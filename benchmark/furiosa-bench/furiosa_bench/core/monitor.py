import shutil
import subprocess
import time
from datetime import datetime
from multiprocessing import Process
from multiprocessing.synchronize import Event
from pathlib import Path

from furiosa_bench.core.detector import HardwareDetector
from furiosa_bench.utils.logger import logger


class HardwareMonitor:
    @staticmethod
    def start_monitor(
        result_dir_path: Path,
        stop_event: Event,
        task_name: str,
        deployment_type: str | None = None,
        devices: list[int] | None = None,
    ) -> Process:
        """Start a background hardware monitoring process for the specified hardware type.

        Selects the appropriate monitor (NPU, GPU, or dummy) based on `deployment_type`,
        falling back to auto-detection when `deployment_type` is None. The monitor process
        writes a CSV log to `result_dir_path / {hardware_type}_monitoring_log.csv` and runs
        until `stop_event` is set.

        Args:
            result_dir_path (Path): Directory where the monitoring CSV log will be written.
            stop_event (Event): Multiprocessing Event used to signal the monitoring process to stop.
            task_name (str): Name of the benchmark task, used in the log file name.
            deployment_type (str | None): Deployment type from config (e.g. "furiosa-llm" for NPU,
                "vllm" for GPU). When provided, determines hardware type directly. Falls back to
                auto-detection if None.
            devices (list[int] | None): Device indices to monitor (e.g. [0] or [0, 1, 2, 3]).
                When None, all available devices are monitored.

        Returns:
            Process: The already-started Process running the hardware monitor in the background.

        Example:
            >>> from multiprocessing import Event
            >>> from pathlib import Path
            >>> stop_event = Event()
            >>> proc = HardwareMonitor.start_monitor(Path('/path/to/results'), stop_event,
            ...     deployment_type="furiosa-llm", devices=[0])
            >>> # ... perform tasks ...
            >>> stop_event.set()  # Stop monitoring
            >>> proc.join()
        """
        # Determine hardware type from deployment config if provided
        if deployment_type == "furiosa-llm":
            hardware_type = "npu"
            target_function = HardwareMonitor._monitor_npu
            logger.info(f"Hardware monitor: NPU (furiosa-llm), devices={devices}")
        elif deployment_type == "vllm":
            hardware_type = "gpu"
            target_function = HardwareMonitor._monitor_gpu
            logger.info(f"Hardware monitor: GPU (vllm), devices={devices}")
        else:
            # Fall back to auto-detection
            hardware_info = HardwareDetector.check_hardware(print_info=False)
            if hardware_info.get("npu"):
                hardware_type = "npu"
                target_function = HardwareMonitor._monitor_npu
                logger.info(f"Hardware monitor: NPU (auto-detected), devices={devices}")
            elif hardware_info.get("gpu"):
                hardware_type = "gpu"
                target_function = HardwareMonitor._monitor_gpu
                logger.info(f"Hardware monitor: GPU (auto-detected), devices={devices}")
            else:
                # No hardware detected - use dummy monitor for dryrun/testing
                logger.warning("No GPU or NPU detected, using dummy monitor")
                target_function = HardwareMonitor._monitor_dummy
                hardware_type = "none"

        result_file_path = result_dir_path / f"{task_name}_{hardware_type}_monitoring_log.csv"

        # Overwrite any existing monitoring log file from a previous run.
        if result_file_path.exists():
            result_file_path.unlink()

        proc = Process(target=target_function, args=(result_file_path, stop_event, 0.5, devices))
        proc.start()
        return proc

    @staticmethod
    def _monitor_npu(
        result_file_path: Path, stop_event: Event, interval: float = 0.5, devices: list[int] | None = None
    ) -> None:
        """Poll Furiosa NPU metrics and append rows to a CSV file until stop_event is set.

        Requires the ``furiosa_smi_py`` package. Returns immediately with a warning if the
        package is not installed. Only rows where average PE utilization > 0 are written.

        Args:
            result_file_path (Path): Path to the CSV file to write (created if absent).
            stop_event (Event): Multiprocessing Event that signals the loop to exit.
            interval (float): Polling interval in seconds. Defaults to 0.5.
            devices (list[int] | None): Device indices to include. When None, all devices are monitored.
        """
        try:
            # Initialize Furiosa SMI and create an observer
            # https://github.com/furiosa-ai/furiosa-smi-py/blob/v2026.1.0-rc1/examples/list_devices.py
            from furiosa_smi_py import create_default_observer, init, list_devices

            init()
            observer = create_default_observer()
        except ImportError:
            logger.warning("furiosa_smi_py is not installed. Please install it to enable Furiosa NPU monitoring.")
            return

        while not result_file_path.parent.exists():
            time.sleep(5)

        try:
            with Path.open(result_file_path, "a") as f:
                f.write("timestamp,device,utilization,power_consumption,temperature\n")
                while not stop_event.is_set():
                    timestamp = datetime.utcnow().isoformat()
                    for device in list_devices():
                        device_index = device.device_info().index()
                        if devices is not None and device_index not in devices:
                            continue
                        device_name = f"rngd{device_index}"
                        power_consumption = device.power_consumption()

                        utilization = observer.get_core_utilization(device)
                        pe_utilization = [pe.pe_usage_percentage() for pe in utilization]
                        avg_utilization = sum(pe_utilization) / len(pe_utilization)
                        temperature = device.device_temperature().soc_peak()
                        if avg_utilization > 0:
                            f.write(f"{timestamp},{device_name},{avg_utilization},{power_consumption},{temperature}\n")
                    f.flush()
                    time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("Furiosa NPU monitoring stopped by user.")

    @staticmethod
    def _monitor_gpu(
        result_file_path: Path, stop_event: Event, interval: float = 0.5, devices: list[int] | None = None
    ) -> None:
        """Poll NVIDIA GPU metrics via nvidia-smi and append rows to a CSV file until stop_event is set.

        Stops and logs a warning if ``nvidia-smi`` is not found on PATH. Only rows where
        GPU utilization > 0 are written.

        Args:
            result_file_path (Path): Path to the CSV file to write (created if absent).
            stop_event (Event): Multiprocessing Event that signals the loop to exit.
            interval (float): Polling interval in seconds. Defaults to 0.5.
            devices (list[int] | None): Device indices to include. When None, all devices are monitored.
        """
        while not result_file_path.parent.exists():
            time.sleep(5)
        try:
            with Path.open(result_file_path, "a") as f:
                f.write("timestamp,device,utilization,power_consumption,temperature\n")
                while not stop_event.is_set():
                    timestamp = datetime.utcnow().isoformat()
                    nvidia_smi_path = shutil.which("nvidia-smi")
                    if nvidia_smi_path:
                        cmd = [
                            nvidia_smi_path,
                            "--query-gpu=name,utilization.gpu,power.draw,temperature.gpu",
                            "--format=csv,noheader,nounits",
                        ]
                        if devices is not None:
                            cmd.append(f"--id={','.join(str(d) for d in devices)}")
                        nvidia_smi = subprocess.Popen(cmd, stdout=subprocess.PIPE)  # noqa: S603
                        output, _ = nvidia_smi.communicate()
                        devices_status = output.decode("utf-8").strip().split("\n")
                        for idx, device_status in enumerate(devices_status):
                            device_index = devices[idx] if devices is not None else idx
                            device_info = device_status.split(",")
                            device_info[0] = device_info[0] + "-" + str(device_index)
                            if int(device_info[1]) > 0:
                                device_status = ",".join(device_info)
                                f.write(f"{timestamp},{device_status}\n")
                        f.flush()
                        time.sleep(interval)
                    else:
                        logger.warning("nvidia-smi not found. Skipping GPU monitoring.")
                        break
        except KeyboardInterrupt:
            logger.info("NVIDIA GPU monitoring stopped by user.")

    @staticmethod
    def _monitor_dummy(
        result_file_path: Path, stop_event: Event, interval: float = 0.5, devices: list[int] | None = None
    ) -> None:
        """No-op monitor used when no GPU or NPU is detected (e.g. dryrun or CI).

        Sleeps in a loop until stop_event is set. Does not create or write any file.

        Args:
            result_file_path (Path): Unused; present for signature compatibility with other monitors.
            stop_event (Event): Multiprocessing Event that signals the loop to exit.
            interval (float): Sleep interval in seconds. Defaults to 0.5.
            devices (list[int] | None): Unused; present for signature compatibility with other monitors.
        """
        while not stop_event.is_set():
            time.sleep(interval)

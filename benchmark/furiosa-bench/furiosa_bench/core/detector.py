import csv
import json
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any

from furiosa_bench.utils.logger import logger


class HardwareDetector:
    """Detects and reports CPU, memory, GPU, and NPU hardware information.

    Note:
        Only homogeneous hardware setups are supported — all accelerators in the system
        are assumed to be of the same type (e.g., all GPUs or all NPUs). Mixed configurations
        are not considered.
    """

    @staticmethod
    def check_hardware(print_info: bool = True) -> dict[str, Any]:
        hardware_info = {
            "cpu": HardwareDetector._detect_cpu(),
            "memory": HardwareDetector._detect_memory(),
            "gpu": HardwareDetector._detect_gpu(),
            "npu": HardwareDetector._detect_furiosa_npu(),
        }
        if print_info:
            HardwareDetector.print_hardware_specs(hardware_info)
        return hardware_info

    @staticmethod
    def _detect_cpu() -> dict[str, Any]:
        return {
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "cores": os.cpu_count(),
        }

    @staticmethod
    def _detect_memory() -> int | None:
        memory = None
        try:
            with Path("/proc/meminfo").open() as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        memory = int(line.split()[1]) * 1024

        except Exception as e:
            logger.warning(f"Memory detection failed: {e}")
        return memory

    @staticmethod
    def _detect_gpu() -> list[dict[str, Any]]:
        gpus: list[dict[str, Any]] = []
        try:
            nvidia_smi_path = shutil.which("nvidia-smi")
            if nvidia_smi_path:
                result = subprocess.run(  # noqa: S603
                    [
                        nvidia_smi_path,
                        "--query-gpu=name,memory.total",
                        "--format=csv,nounits",
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )

                reader = csv.DictReader(result.stdout.strip().split("\n"))

                for row in reader:
                    gpus.append({"name": row["name"].strip(), "memory_mb": int(row[" memory.total [MiB]"])})
                logger.info(f"{len(gpus)} NVIDIA GPU(s) detected")
            else:
                logger.info("nvidia-smi not found. Skipping GPU detection.")
        except Exception as e:
            logger.info(f"NVIDIA GPU detection failed: {e}")
        return gpus

    @staticmethod
    def _detect_furiosa_npu() -> list[dict[str, Any]]:
        npus: list[dict[str, Any]] = []
        try:
            furiosa_smi_path = shutil.which("furiosa-smi")
            if furiosa_smi_path:
                result = subprocess.run(  # noqa: S603
                    [furiosa_smi_path, "status", "--format", "json"], capture_output=True, text=True, check=True
                )
                npu_info = json.loads(result.stdout)
                for line in npu_info:
                    npus.append(
                        {"name": line["arch"], "memory": "48GB"}
                    )  # Placeholder for memory, as rngd does not provide it
                logger.info(f"{len(npus)} Furiosa NPU(s) detected")
            else:
                logger.info("furiosa-smi not found. Skipping Furiosa NPU detection.")
        except Exception as e:
            logger.info(f"Furiosa NPU detection failed: {e}")
        return npus

    @staticmethod
    def check_system_compatibility(hardware_type: str) -> tuple[bool, dict[str, Any]]:
        logger.info(f"Validating hardware: {hardware_type.upper()}")
        detected = HardwareDetector.check_hardware()

        if hardware_type == "gpu" and not detected["gpu"]:
            logger.error("NVIDIA GPU not detected.")
            return False, detected

        if hardware_type == "npu" and not detected["npu"]:
            logger.error("Furiosa NPU not detected.")
            return False, detected

        if not detected["gpu"] and not detected["npu"]:
            logger.warning("No compatible GPU or NPU detected.")
            return False, detected

        return True, detected

    @staticmethod
    def print_hardware_specs(hw_specs: dict[str, Any]) -> None:
        cpu_info = hw_specs["cpu"]
        memory_gb = hw_specs["memory"] // (1024**3) if hw_specs["memory"] else "Unknown"
        gpu_info = hw_specs["gpu"]
        npu_info = hw_specs["npu"]

        logger.info(f"CPU: {cpu_info['architecture']} | Cores: {cpu_info['cores']}")
        logger.info(f"Memory: {memory_gb} GB")

        if gpu_info:
            gpu_name = gpu_info[0]["name"]
            gpu_memory = gpu_info[0]["memory_mb"]
            logger.info(f"GPU: {len(gpu_info)}x {gpu_name} ({gpu_memory} MB)")
        if npu_info:
            npu_name = npu_info[0]["name"]
            npu_memory = npu_info[0]["memory"]
            logger.info(f"NPU: {len(npu_info)}x {npu_name} ({npu_memory})")

import os
import shlex
import signal
import subprocess
import time
from pathlib import Path

import requests
from omegaconf import DictConfig, OmegaConf

from furiosa_bench.manager import ConfigManager
from furiosa_bench.utils.logger import logger


class ServerManager:
    """Manages the lifecycle of an LLM inference server subprocess.

    Typical usage: call ``start()`` to launch the server and wait for it to become
    healthy, then call ``stop()`` when the benchmark is done. In dryrun mode
    (``deployment.type == "dryrun"``), all server operations are no-ops.
    """

    def __init__(
        self,
        config: DictConfig,
        timeout: int = 300,
    ):
        self.config = config
        self.timeout = timeout
        self.server_process: subprocess.Popen[str] | None = None
        self.server_ready = False
        self._server_log_file = None

        output_dir = OmegaConf.select(self.config, "execution.output_dir", default="results")
        self._log_path = Path(output_dir) / "server.log"

        host = OmegaConf.select(self.config, "deployment.host")
        port = OmegaConf.select(self.config, "deployment.port")
        self.base_url = f"http://{host}:{port}"

        health_endpoint = OmegaConf.select(self.config, "endpoints.health")
        model_endpoint = OmegaConf.select(self.config, "endpoints.model")

        self.health_url = f"{self.base_url}{health_endpoint}"
        self.model_url = f"{self.base_url}{model_endpoint}"

        # Check if this is a dryrun deployment (skip server management)
        deployment_name = OmegaConf.select(self.config, "deployment.type", default="")
        self.is_dryrun = deployment_name == "dryrun"

    def start(self) -> None:
        if self.is_dryrun:
            logger.info("Dryrun mode: skipping server startup")
            self.server_ready = True
            return

        if self.server_process and self.server_process.poll() is None:
            logger.warning("Server already running")
            return

        command, env = self._build_command()
        if not command:
            raise ValueError("Failed to build server command.")

        logger.info(f"Starting server: {command}")

        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        self._server_log_file = self._log_path.open("w")
        logger.info(f"Server logs: {self._log_path}")

        self.server_process = subprocess.Popen(  # noqa: S603  # command is generated internally by the benchmark runner
            shlex.split(command),
            env=env,
            text=True,
            stdout=self._server_log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )

        self._wait_for_startup()
        self.server_ready = True
        logger.info("Server is ready")

    def stop(self) -> None:
        if self.is_dryrun:
            logger.info("Dryrun mode: no server to stop")
            self.server_ready = False
            return

        if not self.server_process:
            return

        if self.server_process.poll() is None:
            logger.info("Stopping server process")
            try:
                os.killpg(os.getpgid(self.server_process.pid), signal.SIGTERM)
                self.server_process.wait(timeout=5)
                logger.info("Server process stopped successfully")
            except subprocess.TimeoutExpired:
                os.killpg(os.getpgid(self.server_process.pid), signal.SIGKILL)
                logger.warning("Server process force killed")

        else:
            exit_code = self.server_process.poll()
            logger.info(f"Server already exited with code {exit_code}")

        self.server_process = None
        self.server_ready = False

        if self._server_log_file:
            self._server_log_file.close()
            self._server_log_file = None

    def is_healthy(self) -> bool:
        if self.is_dryrun:
            return True

        if not self.server_process:
            return False
        try:
            health_url = self.health_url
            response = requests.get(health_url, timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def _build_command(self) -> tuple[str, dict[str, str]]:
        env = os.environ.copy()
        env_vars = OmegaConf.select(self.config, "deployment.env_vars")
        if env_vars:
            resolved_env = OmegaConf.to_container(env_vars, resolve=True)
            assert isinstance(resolved_env, dict)
            env.update({str(k): str(v) for k, v in resolved_env.items() if v is not None})

        deployment_type = OmegaConf.select(self.config, "deployment.type")
        devices = OmegaConf.select(self.config, "deployment.devices")

        command = ConfigManager.get_server_command(self.config)

        if devices is not None:
            if deployment_type == "vllm":
                env["CUDA_VISIBLE_DEVICES"] = ",".join(str(d) for d in devices)
                logger.info(f"CUDA_VISIBLE_DEVICES={env['CUDA_VISIBLE_DEVICES']}")
            elif deployment_type == "furiosa-llm":
                npu_devices = ",".join(f"npu:{d}" for d in devices)
                command = f"{command} --devices {npu_devices}"
                logger.info(f"NPU devices: {npu_devices}")

        return command, env

    def _wait_for_startup(
        self,
    ) -> None:
        start = time.time()
        while True:
            if self.server_process and self.server_process.poll() is not None:
                output = ""
                if self._server_log_file:
                    self._server_log_file.flush()
                if self._log_path and self._log_path.exists():
                    output = self._log_path.read_text()
                raise RuntimeError(
                    f"Server process exited unexpectedly with code {self.server_process.returncode}.\n"
                    f"Server log ({self._log_path}):\n{output}"
                )

            try:
                resp = requests.get(self.model_url, timeout=5)
                if resp.status_code == 200:
                    logger.info("Server startup complete")
                    return
            except requests.RequestException as e:
                logger.debug(f"Server not ready yet: {e}")

            if time.time() - start > self.timeout:
                raise RuntimeError(f"Timeout: server did not start within {self.timeout} seconds")

            logger.info("Waiting for server launch. Check after 5 seconds")
            time.sleep(5)

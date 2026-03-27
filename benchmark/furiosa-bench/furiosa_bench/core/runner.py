import os
import shlex
import subprocess
from pathlib import Path
from shutil import copytree

from omegaconf import DictConfig, OmegaConf

from furiosa_bench.utils.logger import logger


class BenchmarkRunner:
    """Runs benchmark using pre-built command from launcher config."""

    def __init__(self, config: DictConfig):
        self.config = config
        output_dir = OmegaConf.select(config, "execution.output_dir", default="results")
        benchmark_dir = OmegaConf.select(config, "execution.workspace", default="benchmark_workspace")
        framework_dir = OmegaConf.select(config, "benchmark.framework_dir")
        task_name = OmegaConf.select(config, "benchmark.task")

        self.output_dir = Path.cwd() / output_dir / task_name
        self.benchmark_dir = Path.cwd() / benchmark_dir / framework_dir
        self.results_file = OmegaConf.select(config, "benchmark.results_file")

    def run(self, debug: bool = False) -> None:
        """Execute the benchmark command."""
        # Get pre-built command from config
        command = OmegaConf.select(self.config, "benchmark.command")
        if not self.benchmark_dir.exists():
            # in case the setup script does not create the benchmark_dir, we create it here to avoid command failure.
            self.benchmark_dir.mkdir(parents=True, exist_ok=True)

        if not command:
            raise ValueError("No benchmark command found in config")

        logger.info(f"Running benchmark command: {command}")

        process = subprocess.Popen(  # noqa: S603  # command is generated internally by the benchmark runner
            shlex.split(command),
            cwd=self.benchmark_dir,
            env=self._get_env(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
        )

        assert process.stdout is not None
        for line in process.stdout:
            logger.info(line.rstrip())

        rc = process.wait()

        if rc != 0:
            raise RuntimeError(f"Benchmark failed with code {rc}")
        # In case the benchmark command does not include evaluation, and only generate the intermediate results,
        # we run evaluation command separately to get the final evaluation results.
        eval_command = OmegaConf.select(self.config, "benchmark.eval_command")
        if eval_command:
            logger.info(f"Running benchmark evaluation command: {eval_command}")
            eval_process = subprocess.Popen(  # noqa: S603  # command is generated internally by the benchmark runner
                shlex.split(eval_command),
                cwd=self.benchmark_dir,
                env=self._get_env(),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
            )

            assert eval_process.stdout is not None
            for line in eval_process.stdout:
                logger.info(line.rstrip())

            eval_rc = eval_process.wait()

            if eval_rc != 0:
                raise RuntimeError(f"Benchmark evaluation failed with code {eval_rc}")
        # make benchmark results to output dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # we set the benchmark command will save results to the benchmark_dir,
        # so we copy them to output_dir to find easily.
        copytree(self.benchmark_dir / self.results_file, self.output_dir, dirs_exist_ok=True)

    def _get_env(self) -> dict[str, str]:
        """Get environment variables for subprocess."""
        env = os.environ.copy()

        # Add env vars from config (filter out None values)
        benchmark_env = OmegaConf.select(self.config, "benchmark.env_vars", default={})
        if benchmark_env:
            resolved_env = OmegaConf.to_container(benchmark_env, resolve=True)
            assert isinstance(resolved_env, dict)
            env.update({str(k): str(v) for k, v in resolved_env.items() if v is not None})
        # Default API key for local server
        if "OPENAI_API_KEY" not in env:
            env["OPENAI_API_KEY"] = "EMPTY"
        return env

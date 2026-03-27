"""Programmatic API for Furiosa Bench."""

import logging
import multiprocessing
import subprocess
from pathlib import Path
from typing import Any

from omegaconf import DictConfig, OmegaConf

logger = logging.getLogger(__name__)


class BenchmarkLauncher:
    """Main launcher class for running evaluations.

    Args:
        config (DictConfig): OmegaConf configuration object
    """

    def __init__(self, config: DictConfig) -> None:
        self.config = config
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate required configuration fields."""
        required_fields = [
            "deployment.type",
            "deployment.model_id",
            "benchmark.task",
            "benchmark.config.use_endpoint_type",
        ]
        for field in required_fields:
            if OmegaConf.select(self.config, field) is None:
                raise ValueError(f"Missing required config field: {field}")

    def _run_framework_setup(self) -> None:
        """Run the framework setup script if configured."""
        skip_setup = OmegaConf.select(self.config, "benchmark.skip_setup", default=False)
        if skip_setup:
            logger.info("Framework setup skipped (--skip-setup)")
            return

        setup_script = OmegaConf.select(self.config, "benchmark.setup_script", default=None)
        framework = OmegaConf.select(self.config, "benchmark.framework", default=None)

        if not setup_script or not framework:
            logger.info("No framework setup required")
            return

        # Use a dedicated directory for framework installations (git clones, etc.)
        setup_dir = Path(OmegaConf.select(self.config, "execution.workspace"))

        setup_dir.mkdir(parents=True, exist_ok=True)

        force_setup = OmegaConf.select(self.config, "benchmark.force_setup", default=False)
        marker_file = setup_dir / f".{framework}.setup_done"

        if marker_file.exists() and not force_setup:
            logger.info(f"Framework '{framework}' already set up (cached). Use --force-setup to re-run.")
            return

        logger.info(f"Running setup for framework '{framework}': {setup_script}")

        result = subprocess.run(  # noqa: S603
            ["bash", setup_script],
            cwd=str(setup_dir),
            capture_output=True,
            text=True,
            timeout=600,
        )

        if result.returncode != 0:
            logger.error(f"Framework setup stdout:\n{result.stdout}")
            logger.error(f"Framework setup stderr:\n{result.stderr}")
            raise RuntimeError(
                f"Framework setup for '{framework}' failed with exit code {result.returncode}. Script: {setup_script}"
            )

        logger.info(f"Framework '{framework}' setup completed successfully")
        if result.stdout:
            logger.info(f"Setup output:\n{result.stdout}")

        # Write marker file on success
        marker_file.write_text(framework)

    def run(self, skip_server_launch: bool = False) -> dict[str, Any]:
        """Run the evaluation.

        Args:
            skip_server_launch (bool): Whether to skip server launch

        Returns:
            dict[str, Any]: Dictionary containing evaluation results
        """

        from furiosa_bench.core.builder import BenchmarkBuilder
        from furiosa_bench.core.executor import BenchmarkExecutor
        from furiosa_bench.core.monitor import HardwareMonitor
        from furiosa_bench.core.server_manager import ServerManager

        name = OmegaConf.select(self.config, "name", default="evaluation")
        logger.info(f"Starting evaluation: {name}")

        # Run framework setup before starting benchmark
        self._run_framework_setup()

        # Initialize server manager
        server_manager = ServerManager(config=self.config)

        # Build benchmark runner (uses full config, not just benchmark section)
        builder = BenchmarkBuilder(config=self.config)
        benchmark = builder.build_benchmark()

        # Get output directory for monitoring
        # We use same output directory for monitoring results with benchmark results,
        # but this can be changed in the future if needed.
        output_dir = OmegaConf.select(self.config, "execution.output_dir", default="results")
        task_name = OmegaConf.select(self.config, "benchmark.task")
        monitor_output_dir = Path(output_dir) / task_name
        monitor_output_dir.mkdir(parents=True, exist_ok=True)

        # Start monitoring
        stop_monitor_event = multiprocessing.Event()
        monitoring_proc = HardwareMonitor.start_monitor(
            result_dir_path=monitor_output_dir,
            stop_event=stop_monitor_event,
            task_name=task_name,
            deployment_type=OmegaConf.select(self.config, "deployment.type"),
            devices=OmegaConf.select(self.config, "deployment.devices", default=None),
        )

        # Execute
        executor = BenchmarkExecutor(debug=False, log_all=True)
        try:
            if skip_server_launch:
                logger.info("Benchmark configured to skip server launch, running benchmark directly")
                executor.run_benchmark(benchmark)
            else:
                executor.execute(benchmark, server_manager)
        finally:
            stop_monitor_event.set()
            monitoring_proc.join()

            logger.info("Evaluation completed")
        return {"status": "success"}

    @classmethod
    def from_yaml(cls, config_path: str, overrides: dict[str, Any] | None = None) -> "BenchmarkLauncher":
        """Create launcher from YAML configuration file.

        Args:
            config_path (str): Path to YAML configuration file
            overrides (dict[str, Any] | None): Optional dictionary of config overrides

        Returns:
            BenchmarkLauncher: Configured BenchmarkLauncher instance
        """
        from furiosa_bench.manager import ConfigManager

        config = ConfigManager.load_config_with_cli_override(config_path, overrides)
        return cls(config)

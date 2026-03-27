"""Integration tests for launcher and evaluator."""

# isort: skip_file
from pathlib import Path
import subprocess
import sys

import pytest
from omegaconf import OmegaConf

from furiosa_bench.core.builder import BenchmarkBuilder
from furiosa_bench.core.runner import BenchmarkRunner
from furiosa_bench.manager import ConfigManager

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestConfigManager:
    """Tests for ConfigManager."""

    def test_load_dryrun_deployment(self) -> None:
        """Test loading dryrun deployment config."""
        config_path = FIXTURES_DIR / "dryrun_experiment.yaml"
        config = ConfigManager.load_config(str(config_path))

        # Check deployment settings are loaded
        assert OmegaConf.select(config, "deployment.name") == "dryrun"
        assert OmegaConf.select(config, "deployment.model_id") == "test-model"

        # Check server command is set from dryrun.yaml
        command = ConfigManager.get_server_command(config)
        assert command is not None
        assert "http.server" in command

    def test_load_config_merges_deployment(self) -> None:
        """Test that experiment config is merged with deployment config."""
        config_path = FIXTURES_DIR / "dryrun_experiment.yaml"
        config = ConfigManager.load_config(str(config_path))

        # Check endpoints from deployment config are present
        assert OmegaConf.select(config, "endpoints.health") == "/health"
        assert OmegaConf.select(config, "endpoints.chat") == "/v1/chat/completions"

    def test_build_benchmark_command_dryrun(self) -> None:
        """Test building benchmark command from dryrun task template."""
        config_path = FIXTURES_DIR / "dryrun_experiment.yaml"
        config = ConfigManager.load_config(str(config_path))

        # Check benchmark command was built
        benchmark_command = OmegaConf.select(config, "benchmark.command")
        assert benchmark_command is not None
        assert "Dryrun benchmark completed successfully" in benchmark_command
        assert "test-model" in benchmark_command  # model_id should be rendered


class TestBenchmarkRunner:
    """Tests for BenchmarkRunner."""

    def _make_config(self, tmp_path: Path, command: str = "echo test") -> OmegaConf:
        return OmegaConf.create(
            {
                "benchmark": {
                    "command": command,
                    "task": "test_task",
                    "framework_dir": ".",
                    "results_file": "results",
                },
                "execution": {
                    "output_dir": str(tmp_path / "output"),
                    "workspace": str(tmp_path / "workspace"),
                },
            }
        )

    def test_runner_executes_command(self, tmp_path: Path) -> None:
        """Test BenchmarkRunner executes a command successfully."""
        workspace = tmp_path / "workspace"
        workspace.mkdir(parents=True)
        (workspace / "results").mkdir()

        config = self._make_config(tmp_path)
        runner = BenchmarkRunner(config)
        runner.run()

        assert (tmp_path / "output" / "test_task").exists()

    def test_runner_creates_benchmark_dir(self, tmp_path: Path) -> None:
        """Test BenchmarkRunner creates benchmark dir if it doesn't exist."""
        config = self._make_config(tmp_path, command="mkdir -p results")

        runner = BenchmarkRunner(config)
        assert not (tmp_path / "workspace").exists()

        runner.run()
        assert (tmp_path / "workspace").exists()

    def test_runner_fails_without_command(self, tmp_path: Path) -> None:
        """Test BenchmarkRunner raises error when no command is provided."""
        config = OmegaConf.create(
            {
                "benchmark": {
                    "task": "test_task",
                    "framework_dir": ".",
                    "results_file": "results",
                },
                "execution": {
                    "output_dir": str(tmp_path / "output"),
                    "workspace": str(tmp_path / "workspace"),
                },
            }
        )

        runner = BenchmarkRunner(config)
        with pytest.raises(ValueError, match="No benchmark command found"):
            runner.run()

    def test_runner_handles_failed_command(self, tmp_path: Path) -> None:
        """Test BenchmarkRunner raises error on failed command."""
        workspace = tmp_path / "workspace"
        workspace.mkdir(parents=True)

        config = self._make_config(tmp_path, command="bash -c 'exit 1'")
        runner = BenchmarkRunner(config)
        with pytest.raises(RuntimeError, match="Benchmark failed with code 1"):
            runner.run()


class TestBenchmarkBuilder:
    """Tests for BenchmarkBuilder."""

    def test_builder_creates_runner(self, tmp_path: Path) -> None:
        """Test BenchmarkBuilder creates a BenchmarkRunner."""
        config = OmegaConf.create(
            {
                "benchmark": {
                    "command": "echo 'test'",
                    "task": "test_task",
                    "framework_dir": ".",
                    "results_file": "results",
                },
                "execution": {
                    "output_dir": str(tmp_path),
                    "workspace": str(tmp_path / "workspace"),
                },
            }
        )

        builder = BenchmarkBuilder(config)
        runner = builder.build_benchmark()

        assert isinstance(runner, BenchmarkRunner)


class TestIntegration:
    """End-to-end integration tests."""

    def test_full_config_loading_pipeline(self) -> None:
        """Test full pipeline: load config and verify resolved values."""
        config_path = FIXTURES_DIR / "dryrun_experiment.yaml"
        config = ConfigManager.load_config(str(config_path))

        # Verify deployment was merged correctly
        assert OmegaConf.select(config, "deployment.model_id") == "test-model"
        assert OmegaConf.select(config, "deployment.name") == "dryrun"

        # Verify server command was rendered
        server_command = ConfigManager.get_server_command(config)
        assert server_command is not None
        assert "http.server" in server_command

        # Verify benchmark command was built
        benchmark_command = OmegaConf.select(config, "benchmark.command")
        assert benchmark_command is not None
        assert "Dryrun benchmark completed successfully" in benchmark_command
        assert "test-model" in benchmark_command


class TestLauncherCLI:
    """Tests for furiosa-bench CLI."""

    def test_cli_help(self) -> None:
        """Test CLI shows help."""
        result = subprocess.run(
            [sys.executable, "-m", "furiosa_bench.cli", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "furiosa-bench-launcher" in result.stdout
        assert "run" in result.stdout
        assert "validate" in result.stdout

    def test_cli_validate_dryrun_config(self) -> None:
        """Test CLI validate command with dryrun config."""
        config_path = FIXTURES_DIR / "dryrun_experiment.yaml"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "furiosa_bench.cli",
                "validate",
                "--config",
                str(config_path),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Configuration is valid" in result.stdout

    def test_cli_run_dry_run_flag(self, tmp_path: Path) -> None:
        """Test CLI run command with --dry-run flag."""
        config_path = FIXTURES_DIR / "dryrun_experiment.yaml"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "furiosa_bench.cli",
                "run",
                "--config",
                str(config_path),
                "--dry-run",
                "--output-dir",
                str(tmp_path),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Configuration (dry-run)" in result.stdout
        assert "dryrun" in result.stdout

    def test_cli_list_benchmarks(self) -> None:
        """Test CLI list benchmarks command."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "furiosa_bench.cli",
                "list",
                "benchmarks",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Available Benchmarks" in result.stdout

    def test_cli_list_backends(self) -> None:
        """Test CLI list backends command."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "furiosa_bench.cli",
                "list",
                "backends",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Available Backends" in result.stdout

    def test_cli_info(self) -> None:
        """Test CLI info command."""
        result = subprocess.run(
            [sys.executable, "-m", "furiosa_bench.cli", "info"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Furiosa Bench Launcher" in result.stdout

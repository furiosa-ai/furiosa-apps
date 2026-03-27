"""Configuration loading, merging, and command rendering for Furiosa Bench.

Loads YAML config files via OmegaConf, merges them with deployment and task defaults,
and renders Jinja2-templated server and benchmark commands into executable strings.
"""

import logging
from pathlib import Path
from typing import Any

from jinja2 import Template
from omegaconf import DictConfig, OmegaConf

logger = logging.getLogger(__name__)

# Base path for metadata files
METADATA_DIR = Path(__file__).parent / "metadata"


class ConfigManager:
    @staticmethod
    def load_config(input_path: str) -> DictConfig:
        input_config = OmegaConf.load(input_path)
        merged = ConfigManager._merge_server_config(input_config)

        # Build server command from deployment config
        server_command = ConfigManager.build_server_command(merged)
        OmegaConf.update(merged, "deployment.command", server_command)

        # Merge benchmark config with task defaults and build benchmark command
        task_name = OmegaConf.select(merged, "benchmark.task")
        merged = ConfigManager._merge_benchmark_config(merged, task_name)

        # Build benchmark command if task is specified
        benchmark_command = ConfigManager.build_benchmark_command(merged, task_name)
        OmegaConf.update(merged, "benchmark.command", benchmark_command)
        # Also build eval command if specified
        if OmegaConf.select(merged, "benchmark.eval_command"):
            eval_command = ConfigManager.build_benchmark_command(merged, task_name, eval_command=True)
            OmegaConf.update(merged, "benchmark.eval_command", eval_command)

        # Resolve framework setup script
        setup_info = ConfigManager.resolve_framework_setup(task_name)
        if setup_info:
            for k, v in setup_info.items():
                logger.info(f"Resolved framework setup info: {k} = {v}")
                OmegaConf.update(merged, f"benchmark.{k}", v)
        return merged

    @staticmethod
    def get_server_command(config: DictConfig) -> str:
        command: str = OmegaConf.select(config, "deployment.command")
        return command

    @staticmethod
    def load_config_with_cli_override(
        input_path: str,
        cli_overrides: dict[str, Any] | None = None,
    ) -> DictConfig:
        config = ConfigManager.load_config(input_path)
        if cli_overrides:
            for key, value in cli_overrides.items():
                if value is not None:
                    OmegaConf.update(config, key, value, merge=True)
                    logger.info(f"Overriding config '{key}' with CLI value: {value}")

        return config

    @staticmethod
    def _load_tasks_config() -> DictConfig:
        """Load tasks.yaml containing Jinja2 templates.

        Note: Jinja2 templates in tasks.yaml must escape '$' as '\\$' to prevent
        OmegaConf from interpreting '${{' as interpolation syntax.
        """
        tasks_file = METADATA_DIR / "benchmark" / "tasks.yaml"
        if not tasks_file.exists():
            logger.warning(f"Tasks file not found: {tasks_file}")
            return OmegaConf.create({})
        result = OmegaConf.load(tasks_file)
        assert isinstance(result, DictConfig)
        return result

    @staticmethod
    def resolve_framework_setup(task_name: str) -> dict[str, str] | None:
        """Resolve the framework setup script path for a given task.

        Args:
            task_name (str): Name of the task to look up.

        Returns:
            dict[str, str] | None: Dict with 'framework' name and absolute 'setup_script' path,
            or None if the task has no framework or no setup script.
        """
        tasks_config = ConfigManager._load_tasks_config()
        tasks = OmegaConf.select(tasks_config, "tasks", default=[])
        frameworks = OmegaConf.select(tasks_config, "frameworks", default={})

        # Find the task's framework
        framework_name = None
        for task in tasks:
            if OmegaConf.is_dict(task):
                for name in task:
                    if name == task_name:
                        framework_name = OmegaConf.select(task, f"{name}.framework", default=None)
                        break
            if framework_name:
                break

        if not framework_name or framework_name == "none":
            return None

        # Look up framework's setup_file
        setup_file = OmegaConf.select(frameworks, f"{framework_name}.setup_file", default=None)
        if not setup_file:
            logger.warning(f"No setup_file defined for framework '{framework_name}'")
            return None

        # Resolve to absolute path relative to metadata/benchmark/
        benchmark_dir = METADATA_DIR / "benchmark"
        setup_script = (benchmark_dir / setup_file).resolve()

        if not setup_script.exists():
            logger.warning(f"Setup script not found: {setup_script}")
            return None

        return {
            "framework": framework_name,
            "setup_script": str(setup_script),
            "framework_dir": OmegaConf.select(frameworks, f"{framework_name}.framework_dir", default="."),
            "results_file": OmegaConf.select(frameworks, f"{framework_name}.results_file"),
        }

    @staticmethod
    def build_server_command(config: DictConfig) -> str:
        """Render server command from Jinja2 template in deployment YAML.

        Args:
            config (DictConfig): The benchmark configuration
        Returns:
            str: Rendered command string
        """

        config_dict = OmegaConf.to_container(config, resolve=True)
        command_template = OmegaConf.select(config, "deployment.command", default="")

        try:
            template = Template(command_template)
            rendered: str = template.render(deployment=config_dict["deployment"])
            # Clean up whitespace
            rendered = " ".join(rendered.split())
            logger.info(f"Built server command: {rendered}")
            return rendered
        except Exception as e:
            logger.error(f"Failed to render server command template: {e}")
            return command_template  # Fallback to original template if rendering fails

    @staticmethod
    def _merge_benchmark_config(input_config: DictConfig, task_name: str) -> dict[str, Any]:
        """Get the default configs for a given task from tasks.yaml.

        Args:
            input_config (DictConfig): The original input config to merge with task
            task_name (str): Name of the task to look up.
        Returns:
            dict[str, Any]: Merged config with the user's input config taking precedence over task defaults
        """
        tasks_config = ConfigManager._load_tasks_config()
        tasks = OmegaConf.select(tasks_config, "tasks")

        # Find the task by name
        task_defaults = None
        for task in tasks:
            if OmegaConf.is_dict(task):
                # Task is a dict with name as key
                for name in task:
                    if name == task_name:
                        task_defaults = OmegaConf.select(task, f"{name}.defaults")
                        break
            if task_defaults:
                break

        if not task_defaults:
            logger.warning(f"Task '{task_name}' not found in tasks.yaml")
            return input_config
        task_defaults_dict = OmegaConf.to_container(task_defaults, resolve=True)
        task_input = OmegaConf.select(input_config, "benchmark", default={})
        task_input = OmegaConf.merge(task_defaults_dict, task_input)
        merged = OmegaConf.merge(input_config, {"benchmark": task_input})
        return merged

    @staticmethod
    def _merge_server_config(input_config: DictConfig) -> DictConfig:
        deployment_name = OmegaConf.select(input_config, "deployment.type")
        # Load deployment config and merge with input config
        deployment_file = METADATA_DIR / "deployment" / f"{deployment_name}.yaml"
        logger.info(f"Loading deployment config from: {deployment_file}")
        deployment_cfg = OmegaConf.load(deployment_file)
        # Deployment config takes precedence over input config for deployment fields
        merged = OmegaConf.merge(deployment_cfg, input_config)
        return merged

    @staticmethod
    def build_benchmark_command(config: DictConfig, task_name: str, eval_command: bool = False) -> str:
        """Render benchmark command from Jinja2 template in tasks.yaml.

        Args:
            config (DictConfig): The merged configuration DictConfig
            task_name (str): Name of the task to build command for
            eval_command (bool): Whether to build the eval_command instead of the main command

        Returns:
            str: Rendered command string, or empty string if task not found

        Raises:
            RuntimeError: If command template rendering fails
        """
        if eval_command:
            command_template = OmegaConf.select(config, "benchmark.eval_command", default="")
        else:
            command_template = OmegaConf.select(config, "benchmark.command", default="")
        # Render the Jinja2 template
        try:
            template = Template(command_template)
            rendered: str = template.render(
                benchmark=config["benchmark"],
                deployment=config["deployment"],
                execution=config["execution"],
            )
            # Clean up whitespace
            rendered = " ".join(rendered.split())
            logger.info(f"Built benchmark command: {rendered}")
            return rendered
        except Exception as e:
            raise RuntimeError("Failed to render benchmark command template:") from e

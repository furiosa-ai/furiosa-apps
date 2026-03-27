"""CLI for Furiosa Evaluator Launcher."""

import argparse
import sys
from importlib.metadata import version as _pkg_version
from pathlib import Path

from furiosa_bench.api import BenchmarkLauncher
from furiosa_bench.manager import ConfigManager


def setup_parser() -> argparse.ArgumentParser:
    """Create the argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="furiosa-bench",
        description="Launch and manage LLM evaluations across different backends",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {_pkg_version('furiosa-bench')}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # 'run' subcommand
    run_parser = subparsers.add_parser("run", help="Run an evaluation")
    run_parser.add_argument(
        "--config",
        "-c",
        type=str,
        required=True,
        help="Path to experiment YAML configuration file",
    )
    run_parser.add_argument(
        "--skip-server-launch",
        action="store_true",
        help="Skip server launch and run benchmark directly (for benchmarks that support this mode)",
    )
    run_parser.add_argument(
        "--model-id",
        type=str,
        help="Override model ID (e.g., furiosa-ai/Qwen2.5-0.5B-Instruct)",
    )
    run_parser.add_argument(
        "--server-model-id",
        type=str,
        help="Override model ID used for server deployment (if different from --model-id)",
    )
    run_parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        help="Override output directory for results",
    )
    run_parser.add_argument(
        "--num-samples",
        type=int,
        help="Override number of samples to evaluate",
    )
    run_parser.add_argument(
        "--backend",
        type=str,
        choices=["vllm", "furiosa-llm"],
        help="Override deployment backend",
    )
    run_parser.add_argument(
        "--log-level",
        type=str,
        default="info",
        choices=["debug", "info", "warning", "error"],
        help="Set logging verbosity",
    )
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print configuration without running",
    )
    run_parser.add_argument(
        "--force-setup",
        action="store_true",
        help="Force re-running framework setup even if cached",
    )
    run_parser.add_argument(
        "--skip-setup",
        action="store_true",
        help="Skip framework setup entirely",
    )

    # 'validate' subcommand
    validate_parser = subparsers.add_parser("validate", help="Validate a configuration file")
    validate_parser.add_argument(
        "--config",
        "-c",
        type=str,
        required=True,
        help="Path to configuration file to validate",
    )

    # 'list' subcommand
    list_parser = subparsers.add_parser("list", help="List available resources")
    list_parser.add_argument(
        "resource",
        choices=["benchmarks", "backends"],
        help="Type of resource to list",
    )

    # 'info' subcommand
    info_parser = subparsers.add_parser("info", help="Show system information")
    info_parser.add_argument(
        "--hardware",
        action="store_true",
        help="Show detected hardware",
    )

    return parser


def cmd_run(args: argparse.Namespace) -> int:
    """Execute the 'run' command."""
    from furiosa_bench.utils.logger import logger, setup_logger

    setup_logger(args.log_level)

    # Build CLI overrides
    cli_overrides = {}
    if args.model_id:
        cli_overrides["deployment.model_id"] = args.model_id
    if args.server_model_id:
        cli_overrides["deployment.serving_model_id"] = args.server_model_id
    if args.output_dir:
        cli_overrides["execution.output_dir"] = args.output_dir
    if args.num_samples:
        cli_overrides["benchmark.task.num_samples"] = args.num_samples
    if args.backend:
        cli_overrides["deployment.type"] = args.backend
    if args.force_setup:
        cli_overrides["benchmark.force_setup"] = True
    if args.skip_setup:
        cli_overrides["benchmark.skip_setup"] = True

    # Load configuration
    try:
        config = ConfigManager.load_config_with_cli_override(
            args.config,
            cli_overrides or None,
        )

    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return 1

    # Dry run - just print config
    if args.dry_run:
        from omegaconf import OmegaConf

        print("=" * 60)
        print("Configuration (dry-run):")
        print("=" * 60)
        print(OmegaConf.to_yaml(config))
        return 0

    # Run evaluation
    try:
        launcher = BenchmarkLauncher(config)
        launcher.run(args.skip_server_launch)
        logger.info(f"Evaluation completed. Results saved to: {config.execution.output_dir}")
        return 0
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        return 1


def cmd_validate(args: argparse.Namespace) -> int:
    """Execute the 'validate' command."""
    from omegaconf import OmegaConf

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Configuration file not found: {config_path}")
        return 1

    try:
        config = ConfigManager.load_config(args.config)
        print(f"✓ Configuration is valid: {config_path}")
        print("\nResolved configuration:")
        print(OmegaConf.to_yaml(config))
        return 0
    except Exception as e:
        print(f"✗ Configuration is invalid: {e}")
        return 1


def cmd_list(args: argparse.Namespace) -> int:
    """Execute the 'list' command."""
    if args.resource == "benchmarks":
        print("Available Benchmarks:")
        print("-" * 40)
        benchmarks = [
            ("lm-eval-harness", "Language model evaluation harness"),
            ("simple-evals", "Simple evaluation suite"),
            ("evalplus", "Code evaluation benchmark"),
            ("mteb", "Massive Text Embedding Benchmark"),
            ("vllm", "vLLM performance benchmark"),
        ]
        for name, desc in benchmarks:
            print(f"  • {name:<20} {desc}")

    elif args.resource == "backends":
        print("Available Backends:")
        print("-" * 40)
        print("  • vllm          NVIDIA GPU inference (vLLM)")
        print("  • furiosa-llm   Furiosa NPU inference")

    return 0


def cmd_info(args: argparse.Namespace) -> int:
    """Execute the 'info' command."""
    if args.hardware:
        # Import from evaluator package
        try:
            from furiosa_bench.core.detector import HardwareDetector

            HardwareDetector.check_hardware(print_info=True)
        except ImportError:
            print("Hardware detection requires furiosa-evaluator package")
            return 1
    else:
        print("Furiosa Bench Launcher")
        print("-" * 40)
        print("Version: 0.0.1")
        print(f"Python: {sys.version}")
    return 0


def main() -> int:
    """Main entry point."""
    parser = setup_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    commands = {
        "run": cmd_run,
        "validate": cmd_validate,
        "list": cmd_list,
        "info": cmd_info,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())

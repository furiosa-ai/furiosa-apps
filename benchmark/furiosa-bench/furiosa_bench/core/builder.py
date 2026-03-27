from omegaconf import DictConfig

from furiosa_bench.core.runner import BenchmarkRunner
from furiosa_bench.utils.logger import logger


class BenchmarkBuilder:
    """Builds a BenchmarkRunner from config.

    Args:
        config (DictConfig): Benchmark configuration.
    """

    def __init__(self, config: DictConfig) -> None:
        self.config = config

    def build_benchmark(self) -> BenchmarkRunner:
        """Create BenchmarkRunner instance from config."""
        logger.info("Building BenchmarkRunner from config")
        return BenchmarkRunner(self.config)

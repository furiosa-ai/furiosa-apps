from furiosa_bench.core.runner import BenchmarkRunner
from furiosa_bench.core.server_manager import ServerManager
from furiosa_bench.utils.logger import logger


class BenchmarkExecutor:
    def __init__(self, debug: bool = False, log_all: bool = False):
        self.debug = debug
        self.log_all = log_all

    def execute(self, benchmark: BenchmarkRunner, server: ServerManager) -> None:
        """Run the benchmarks."""
        try:
            # server start
            logger.info("Starting server")
            server.start()

            # check server is ready
            if not server.is_healthy():
                logger.warning("Server health check failed")

            # benchmark execution
            benchmark.run(self.debug)

            logger.info("Benchmark completed")
        except Exception as e:
            logger.error(f"Benchmark failed: {e}")
            raise
        finally:
            # server stop
            server.stop()

    def run_benchmark(self, benchmark: BenchmarkRunner) -> None:
        """Run the benchmark without server management."""
        try:
            benchmark.run(self.debug)

            logger.info("Benchmark completed")

        except Exception as e:
            logger.error(f"Benchmark failed: {e}")
            raise

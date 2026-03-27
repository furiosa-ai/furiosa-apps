# Contributing to Furiosa Bench

Welcome to the Furiosa Bench project. This guide provides instructions to help you contribute efficiently and effectively.

## TL;DR
This section summarizes the contribution requirements, rather than the detailed process steps.
For a complete step-by-step guide, see [how-to-add-benchmark.md](docs/how-to-guide/how-to-add-benchmark.md).

- Step 1: Create two example configuration files for both GPU and RNGD environments.
   - example/`<new-benchmark>`_`<model>`_`gpu`.yaml
   - example/`<new-benchmark>`_`<model>`_`rngd`.yaml
- Step 2: Add the benchmark metadata (framework and task information) to [tasks.yaml](furiosa-bench/furiosa_bench/metadata/benchmark/tasks.yaml)
- Step 3: If the benchmark requires a new framework, add the corresponding installation scripts under [scripts for installation](furiosa-bench/furiosa_bench/metadata/benchmark/scripts)
- Step 4: Run furiosa-bench using the above configurations and verify that the benchmark scores are consistent between GPU and RNGD.
- Step 5: Add the benchmark information to the Supported Benchmarks table in README.md
- Step 6: Report the results in [reproduced_benchmarks.md](docs/how-to-guide/reproduced_benchmarks.md).

## Reporting Issues
When reporting an issue, please provide:

1. A descriptive title.
2. Steps to reproduce the issue.
3. Expected vs. actual behavior.
4. Screenshots or logs, if applicable.
5. Environment details (OS, Python version, etc.).

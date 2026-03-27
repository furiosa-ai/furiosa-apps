# LLM Serving Benchmark

The benchmark evaluates the inference serving performance of LLMs by measuring latency and throughput under target workloads.

The evaluation focuses on:
- Output Throughput (TPS)
- TTFT (Time to First Token)
- TPOT (Time per Output Token)
- End-to-end latency for generated workloads
- Performance under varying request rates, concurrency, and sequence lengths

## Benchmark Methods

### Task: Online (via vLLM)
The online task submits all `num-prompts` requests at once. Each request uses a predefined input length (`input-tokens`) and target output length (`output-tokens`). The serving framework processes up to `max_concurrency` requests concurrently, and any remaining requests stay in the queue until earlier request finish.

- Evaluation Code: [vLLM benchmark tool](https://docs.vllm.ai/en/latest/benchmarking/cli/#dataset-overview)

To model a **quasi-online serving** scenario, we use `num-prompts = C × 3` with `max_concurrency = C`. In this setup, only `C` requests are served at a time, and the rest remain queued until earlier request complete. This enables evaluation of both active serving performance and queueing behavior. The factor of 3 ensures the queue is never drained before serving performance stabilizes, while keeping total benchmark time bounded.

### Running the Benchmark
The required benchmark framework is automatically installed when the CLI is executed with the task (e.g., online) specified in the configuration file.

Example configuration (my_benchmark.yaml):
```yaml
benchmark:
  # The benchmark task to run
  task: online
```

### Environment setups
The installation script is located at [install_vllm.sh](../../furiosa-bench/furiosa_bench/metadata/benchmark/scripts/install_vllm.sh).
It installs the required evaluation dependencies:
```bash
pip install uv
uv venv .venv
uv pip install --python .venv/bin/python vllm==0.16.0
```

### Run tasks
Benchmark task definitions are located at: [tasks.yaml](../../furiosa-bench/furiosa_bench/metadata/benchmark/tasks.yaml) Example task configuration:
```yaml
- online:
    description: Evaluation for LLM serving performance.
    framework: vllm
    defaults:
      command: >
        ../.venv/bin/vllm bench serve
        --backend vllm
        --model {{deployment.model_id}}
        --base-url http://{{deployment.host}}:{{deployment.port}}/v1
        --endpoint /{{benchmark.config.use_endpoint_type}}
        --dataset-name random
        --random-input-len {{benchmark.config.params.input_tokens}}
        --random-output-len {{benchmark.config.params.output_tokens}}
        --max-concurrency {{benchmark.config.params.concurrency}}
        --num-prompts {{benchmark.config.params.num_prompts}}
        --result-dir results
        --ignore-eos
        --ready-check-timeout-sec 0
        --percentile-metrics ttft,tpot,itl,e2el
        --metric-percentiles 25,50,75,90,95,99
        --save-result
```

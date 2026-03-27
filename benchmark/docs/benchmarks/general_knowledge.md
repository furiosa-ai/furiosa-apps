# General Knowledge Benchmark

The general knowledge benchmark evaluates the breadth and depth of factual knowledge across diverse domains.

The evaluation focuses on:
- General knowledge accuracy (factual correctness across diverse domains)
- End-to-end latency during inference

## Benchmark Methods
### Dataset: MMLU-Pro on lm-eval-harness, (llama3 version)
We evaluate general knowledge performance on the MMLU-Pro dataset using the [lm-eval-harness](https://github.com/EleutherAI/lm-evaluation-harness.git) framework.

MMLU-Pro evaluates LLMs' factual knowledge and reasoning across diverse expert-level domains.

- Paper: [MMLU-Pro: A More Robust and Challenging Multi-Task Language Understanding Benchmark](https://arxiv.org/pdf/2406.01574)
- Original Implementation: [MMLU-Pro(Github)](https://github.com/TIGER-AI-Lab/MMLU-Pro)

- LM-Eval-Harness Implementation: [mmlu_pro_llama variant description on lm-eval-harness(Github)](https://github.com/EleutherAI/lm-evaluation-harness/tree/main/lm_eval/tasks/llama3)

To benchmark a model on the MMLU-Pro dataset, we use the `mmlu_pro_llama` version from lm-eval-harness library following [Llama3 evaluation details](https://github.com/meta-llama/llama-models/blob/main/models/llama3_1/eval_details.md) from [Meta](https://github.com/meta-llama/llama-cookbook/tree/b5f64c0b69d7ff85ec186d964c6c557d55025969/tools/benchmarks/llm_eval_harness/meta_eval_reproduce).

### Running the Benchmark
The required benchmark framework is automatically installed when the CLI is executed with the `mmlu_pro_llama` task specified in the configuration file.

Example configuration (`my_benchmark.yaml`):
```yaml
benchmark:
  # The benchmark task to run
  task: mmlu_pro_llama

```

### Environment setups

The installation script is located at [install_lm_eval_harness.sh](../../packages/furiosa-bench-launcher/furiosa_bench_launcher/metadata/benchmark/scripts/install_lm_eval_harness.sh).
It installs the required evaluation dependencies:
```bash
pip install uv
uv venv .lm_eval_venv
uv pip install --python .lm_eval_venv/bin/python lm_eval[api]==v0.4.11 transformers torch
```

### Run tasks
Benchmark task definitions are located at: [tasks.yaml](../../packages/furiosa-bench-launcher/furiosa_bench_launcher/metadata/benchmark/tasks.yaml)
Example task configuration:

```yaml
- mmlu_pro_llama:
    description: A professional-level knowledge evaluation across diverse domains, which tailors to evaluate generation models.
    framework: lm-eval-harness
    defaults:
      command: >
        ../.lm_eval_venv/bin/python -m lm_eval
        --task {{benchmark.task}}
        --model local-completions
        --model_args "base_url=http://{{deployment.host}}:{{deployment.port}}/v1/{{benchmark.use_endpoint_type}},model={{deployment.model_id}},num_concurrent={{ benchmark.params.concurrency }},timeout={{ benchmark.params.request_timeout }},max_retries={{ benchmark.params.max_retries }}"
        --log_samples --fewshot_as_multiturn --apply_chat_template
        --output_path results
        --use_cache .lm_cache
      config:
        params:
          task: mmlu_pro_llama
          max_retries: 10
          concurrency: 100
          request_timeout: 30
        use_endpoint_type: completions
        debug_args: "--limit 0.001"
```

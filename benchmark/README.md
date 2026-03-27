# Furiosa Benchmark

Furiosa Benchmark is a benchmarking framework for evaluating Large Language Models (LLMs) on Furiosa RNGD. It evaluates three dimensions — performance, accuracy, and power consumption — following the official procedures of each benchmark framework to ensure reproducible and fair comparisons across hardware platforms.

- **Performance**: latency, throughput, scalability
- **Accuracy**: general knowledge, mathematical reasoning, code, retrieval, ranking capabilities
- **Power Consumption**: energy drawn under recommended load configurations

## Workloads

Furiosa Benchmark supports the following benchmark domains. Power consumption is measured across all benchmarks as a cross-cutting concern.

| Domain | Description | Tool | Supported Tasks |
|----------------|-------------|------|----------------------|
| [LLM Serving](/benchmark/docs/benchmarks/llm_serving.md) | Measures end-to-end LLM serving performance in real-world deployment settings, including latency, throughput, and system efficiency under various workload patterns. | vllm | online |
| [General Knowledge](/benchmark/docs/benchmarks/general_knowledge.md) | Evaluates the model's domain-specific and expert-level knowledge across a broad range of subjects, assessing factual correctness, depth of understanding, and reasoning consistency. | lm-eval-harness | MMLU_pro |
| [Mathematical Reasoning](/benchmark/docs/benchmarks/mathematical_reasoning.md) | Assesses mathematical reasoning capabilities ranging from high-school to graduate-level problems, including symbolic reasoning, multi-step logic, and multilingual mathematical tasks. | simple-evals | Math, MGSM |
| [Code Generation](/benchmark/docs/benchmarks/code_generation.md) | Evaluates the model's ability to generate syntactically correct, executable, and functionally valid code (e.g., Python). | Evalplus | HumanEval, MBPP |
| [Retrieval](/benchmark/docs/benchmarks/retrieval.md) | Evaluates Retrieval-Augmented Generation components, particularly embedding models and rerankers, in information retrieval and semantic search tasks. | MTEB | STS22.v2 |

## Installation

```bash
pip install -e .[furiosa-llm] # for RNGD
pip install -e .[vllm] # for GPU
```

## Quick start

### Copy an example configuration

    cp examples/mmlu_pro_llama_qwen2_5_0_5b_instruct_rngd.yaml my_benchmark.yaml

Edit the file to match your target model, backend, and benchmark settings. The following fields are particularly important:
- `execution.workspace` (default: `workspace/`): the working directory where each benchmark framework (e.g., vllm, lm-eval-harness) is installed into its own isolated virtual environment. Frameworks are kept separate from the main Python environment to avoid dependency conflicts between them and `furiosa-llm`.
- `execution.output_dir` (default: `results/`): where benchmark results are saved after the run.

### Run the benchmark
- Scenario 1. Simply run pre-defined YAML file with the following command:
    ```bash
    furiosa-bench run --config my_benchmark.yaml
    ```
- Scenario 2. Run benchmark with overriding settings via CLI
    ```bash
    furiosa-bench run \
    --config examples/mmlu_pro_llama_qwen2_5_0_5b_instruct_rngd.yaml \
    --model furiosa-ai/Qwen3-32B-FP8 \
    --backend furiosa-llm
    ```
- Scenario 3. Running with a Pre-Deployed Server Endpoint

    Use this scenario when the LLM server is already running independently. First, start the server:
    ```bash
    furiosa-llm serve furiosa-ai/Qwen2.5-0.5B-Instruct --max-model-len 8192 --devices 'npu:0'
    ```
    Then run the benchmark with `--skip-server-launch` to skip the built-in server startup:
    ```bash
    furiosa-bench run --config my_benchmark.yaml --skip-server-launch
    ```

## Check the evaluation results
```
{output_dir}/
├── {hardware_type}_monitoring_log.csv   # hardware metrics sampled throughout the run
└── {task_name}/                         # task-specific benchmark outputs
    └── ...                              # framework-dependent result files
```

**Hardware monitoring log** (`{hardware_type}_monitoring_log.csv`): records power draw, utilization, and temperature sampled every 0.5 seconds during the benchmark. The prefix is `npu`, `gpu`, or `none` depending on the detected hardware.

**Task results** (`{task_name}/`): contents vary by framework:
- `vllm`: JSON files with latency percentiles and throughput measurements.
- `lm-eval-harness`: JSON files with per-sample predictions and aggregate accuracy metrics.
- `simple-evals`: JSON files with per-problem scores and summary statistics.
- `evalplus`: JSON files with pass@k scores and per-problem execution results.
- `mteb`: JSON files with per-task scores across the evaluated MTEB tasks.

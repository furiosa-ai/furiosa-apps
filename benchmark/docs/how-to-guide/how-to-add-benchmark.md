# How to Add Benchmarks

Follow the steps below to add a new benchmark configuration.

## Step 0 — Define Benchmark Configuration

Select the target benchmark setup.

- **Model**: `target_model` (e.g., furiosa-ai/Llama-3.3-70B-Instruct)
- **Benchmark**: `target_benchmark` (e.g., llm-serving)
- **Benchmark Tool**: `tool` (e.g., vllm)
- **Task**: `target_task` (e.g., online)

## Step 1 — Update `tasks.yaml`

Check whether the selected **benchmark tool** and **task** are already supported.

- If the **benchmark tool is supported but the task is not**, add a new configuration for `target_task` in `tasks.yaml`.
    ```yaml
    - metadata:
        num_tasks: 9 # update num_tasks

    - `target_task`:
        description: brief task explanation
        framework: `tool`
        defaults: # Default configs merged into examples/<...>.yaml during execution
            command: >
                benchmark command written in Jinja format.
                The command runs inside the downloaded benchmark workspace.
                It should contain base-url info. so benchmarking users can adjust the url with ease.
            config: # default configs
    # example
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
- If both the benchmark tool and the task are not supported
    - Add configurations for both tool and target_task.
    ```yaml
    metadata:
        num_tasks: 9 # update num_tasks
        num_frameworks: 5 # update num_frameworks

    <tool name>:
        description: Benchmark tool description
        url: Original benchmark tool repository
        setup_file: script/install_<tool name>.sh
        framework_dir: Directory where the benchmark is executed
        results_file: Directory where benchmark results are stored this file will be copied to execution.output_dir
    # example
    vllm:
        description: A vllm's serving performance benchmark reference for LLMs.
        url: https://github.com/vllm-project/vllm.git
        setup_file: scripts/install_vllm.sh
        framework_dir: vllm
        results_file: results
    ```
    - Add benchmark setup file, `install_<tool>.sh` , for example
    ```bash
    pip install uv
    uv venv .venv
    uv pip install --python .venv/bin/python vllm==0.16.0
    ```

## Step 2 — Create Benchmark Configuration Files
Create configuration files for both GPU and RNGD.
```bash
# online_llama_3_1_8b_instruct_gpu.yaml
examples/<target_task>_<target_model_slug>_gpu.yaml
# online_llama_3_1_8b_instruct_rngd.yaml
examples/<target_task>_<target_model_slug>_rngd.yaml
```

## Step 3 — Run Benchmarks on GPU and RNGD
Run the benchmark using each backend and compare the results.
```bash
# GPU
pip install -e .[vllm]
furiosa-bench run --config examples/<target_task>_<target_model_slug>_gpu.yaml

# RNGD
pip install -e .[furiosa-llm]
furiosa-bench run --config examples/<target_task>_<target_model_slug>_rngd.yaml
```
Verify that both runs complete successfully and compare the results.

## Step 4 — Update Documentation
Add or update benchmark descriptions in the following files:
- `README.md`
- `docs/benchmarks/<target_benchmark>.md`
- `docs/how-to-guide/reproduced_benchmarks.md`

## Step 5 — Submit a Pull Request
Before creating a PR:
- Ensure benchmarks run successfully on both GPU and RNGD
- Verify that results are correctly reported

Create a PR including:
- Benchmark configuration files
- Updates to `tasks.yaml`
- Documentation updates

## Directory Structure
```
examples/
  <target_task>_<target_model_slug>_gpu.yaml
  <target_task>_<target_model_slug>_rngd.yaml

docs/
  benchmarks/
    <target_benchmark>.md
  how-to-guide/
    reproduced_benchmarks.md

furiosa-bench/furiosa_bench/metadata/benchmark/
  tasks.yaml
  scripts/
    install_<tool>.sh

README.md
```

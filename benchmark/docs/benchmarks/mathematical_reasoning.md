# Mathematical Reasoning Benchmark
The mathematical reasoning benchmark evaluates the ability of LLMs to solve mathematical problems ranging from high school to graduate level.

The evaluation focuses on:
- Mathematical problem-solving accuracy
- End-to-end inference latency

## Benchmark Methods
### Dataset: MGSM, Math (via simple-evals)
We evaluate LLMs' mathematical reasoning ability on the MGSM and MATH datasets using the simple-evals framework.

- Original Implementation: [simple-evals (OpenAI)](https://github.com/openai/simple-evals.git)
- Furiosa Evaluation Code: [simple-evals (Furiosa fork)](https://github.com/furiosa-ai/simple-evals.git)

MGSM evaluates a model's arithmetic reasoning ability on grade-school-level math problems across 11 languages, while MATH evaluates a model's problem-solving ability on competition-level mathematics questions.

- Math Paper: [Measuring Mathematical Problem Solving With the MATH Dataset](https://arxiv.org/abs/2103.03874)
- MGSM Paper: [Language Models are Multilingual Chain-of-Thought Reasoners](https://arxiv.org/abs/2210.03057)

### Running the Benchmark
The required benchmark framework is automatically installed when the CLI is executed with the `mgsm` or `math` task specified in the configuration file.

Example configuration (`my_benchmark.yaml`):
```yaml
benchmark:
  # The benchmark task to run
  task: mgsm # or math

```

### Environment setups
The installation script is located at: [install_simple_evals.sh](https://github.com/furiosa-ai/furiosa-apps/blob/main/furiosa-bench/packages/furiosa-bench-launcher/furiosa_bench_launcher/metadata/benchmark/scripts/install_simple_evals.sh).
It installs the required evaluation dependencies:
```bash
pip install uv

uv venv .simple_evals_venv
uv pip install --python .simple_evals_venv/bin/python setuptools wheel

git clone https://github.com/furiosa-ai/simple-evals.git
git clone https://github.com/openai/human-eval

uv pip install --python .simple_evals_venv/bin/python \
openai blobfile anthropic tabulate pandas jinja2 requests scipy
```

### Run tasks
Benchmark task definitions are located at: [tasks.yaml](https://github.com/furiosa-ai/furiosa-apps/blob/main/furiosa-bench/packages/furiosa-bench-launcher/furiosa_bench_launcher/metadata/benchmark/tasks.yaml)
Example task configuration:

```yaml
- mgsm:
    description: Multilingual Grade School Math (MGSM) evaluation.
    framework: simple-evals
    defaults:
      command: >
        .simple_evals_venv/bin/python
        -m simple-evals.simple_evals
        --eval {{benchmark.task}}
        --model {{deployment.model_id}}
        --base_url http://{{deployment.host}}:{{deployment.port}}/v1
        --custom
      env_vars:
        PYTHONPATH: human-eval
      config:
        use_endpoint_type: completions
        debug_args: "--debug"
- math:
    description: Mathematical reasoning evaluation for language models.
    framework: simple-evals
    defaults:
      command: >
        .simple_evals_venv/bin/python -m simple-evals.simple_evals
        --eval {{benchmark.task}}
        --model {{deployment.model_id}}
        --base_url http://{{deployment.host}}:{{deployment.port}}/v1
        --custom
      env_vars:
        PYTHONPATH: human-eval
      config:
        use_endpoint_type: completions
        debug_args: "--debug"
```

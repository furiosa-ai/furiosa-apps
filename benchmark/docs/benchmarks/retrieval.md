# Retrieval Benchmark
This benchmark evaluates embedding and reranking models used in RAG systems.

The evaluation focuses on:
- Semantic representation quality (accuracy on MTEB)
- End-to-end latency

## Benchmark Methods
### Dataset: MTEB v2 English
When releasing embedding or reranking models, the companies often publish standardized evaluation results using MTEB (Massive Text Embedding Benchmark), a large-scale benchmark suite for evaluating general-purpose semantic representation across diverse text similarity tasks.

- Paper: [MTEB: Massive Text Embedding Benchmark](https://arxiv.org/abs/2210.07316)
- Original Implementation: [MTEB (GitHub)](https://github.com/embeddings-benchmark/mteb)
- Furiosa Evaluation Code: [Qwen3-Embedding (Furiosa fork)](https://github.com/furiosa-ai/Qwen3-Embedding/tree/server-eval)

Our implementation is based on the official evaluation code used in the Qwen3-Embedding release to maintain methodological consistency.


Although MTEB supports multilingual evaluation, we restrict evaluation to English datasets to control scope and reduce evaluation time. The full MTEB suite includes many tasks, and running all of them significantly increases evaluation time. Therefore, we evaluate on 7 representative tasks to balance coverage and practicality.

### Running the Benchmark
The required benchmark framework is automatically installed when the CLI is executed with the `mteb_embedding` or `mteb_reranking` task specified in the configuration file.
Example configuration (`my_benchmark.yaml`):
```yaml
benchmark:
  # The benchmark task to run
  task: mteb_embedding # or mteb_reranking

```

#### Environment setups
The installation script is located at: [install_mteb.sh](furiosa-bench/packages/furiosa-bench-launcher/furiosa_bench_launcher/metadata/benchmark/scripts/install_mteb.sh).
It installs the required evaluation dependencies:
```bash
git clone https://github.com/furiosa-ai/Qwen3-Embedding -b server-eval
cd Qwen3-Embedding/evaluation && pip install -r requirements.txt
```

#### Run tasks
Benchmark task definitions are located at: [tasks.yaml](furiosa-bench/packages/furiosa-bench-launcher/furiosa_bench_launcher/metadata/benchmark/tasks.yaml)
Example task configuration:

```yaml
- mteb_embedding:
    description: Evaluation for embedding models using the MTEB benchmark.
    framework: mteb
    defaults:
      command: >
        bash run_mteb.sh
        {{deployment.model_id}}
        {{deployment.model_id}}
        http://{{deployment.host}}:{{deployment.port}}/v1
      eval_command: >
        python3 summary.py {{benchmark.eval_dir}} "MTEB(eng, v2)"
    config:
      use_endpoint_type: embedding
- mteb_reranking:
    description: Evaluation for reranking models using the MTEB benchmark.
    framework: mteb
    defaults:
      command: >
        bash run_mteb_reranking.sh
        {{deployment.model_id}}
        {{deployment.model_id}}
        http://{{deployment.host}}:{{deployment.port}}/v1
        results_embedding_0.6B_transformers
      eval_command: >
        python3 summary.py {{benchmark.eval_dir}} "MTEB(eng, v2)"
    config:
      use_endpoint_type: score
```

[![RNGD](https://img.shields.io/badge/Powered_by-RNGD-B91C1C?logo=chip&logoColor=white)](https://developer.furiosa.ai/latest/en/)

# Furiosa Reference Applications

`furiosa-apps` provides end-to-end reference implementations built with Furiosa-LLM, covering benchmarks, interactive demos, and integrations with open-source AI platforms.


## Prerequisites
- For Furiosa SDK installation and setup instructions, see [Quick Start with Furiosa-LLM](https://developer.furiosa.ai/latest/en/get_started/furiosa_llm.html).
- Clone this repository and navigate the directory, selecting which reference you want to run.
  ```bash
  # Clone the repository
  git clone https://github.com/furiosa-ai/furiosa-apps.git

  # Navigate to the target reference application
  cd furiosa-apps/<applications>

  # Install Python venv
  python -m venv venv
  source venv/bin/activate
  ```

## Applications

| Name | Description | Primary Use Case |
|------|-------------|-----------------|
| [Benchmark](/benchmark) | A comprehensive evaluation framework for measuring performance and accuracy of LLMs on Furiosa RNGD. | Hardware evaluation and comparison |
| [Chat Playground](/chat-playground) | A full-stack chatbot application with real-time inference metrics, built on Furiosa-LLM. | Interactive LLM inference exploration |
| [Coding Agent](/coding-agent) | A terminal-based AI coding assistant (OpenCode) and a web-based unit-test generator, both powered by Furiosa-LLM. | AI-assisted software development |
| [LLM Assistant](/llm-assistant) | A collection of AI assistant applications: an OpenClaw agent platform integration, a multi-agent weekly news reporter, and a real-time financial sentiment analysis dashboard. | Custom AI Support |
| [RAG](/rag) | An end-to-end RAG pipeline using embedding, reranker, and generation models served via Furiosa-LLM. | Knowledge-grounded question answering |

> These applications are provided for reference purposes only and are not intended for production use.



## Supported models
The pre-compiled models are available at [FuriosaAI models on Hugging Face](https://huggingface.co/furiosa-ai/models).

| Model (HF ID) | Required RNGDs | Max Context Length |
|---|---|---|
| [furiosa-ai/EXAONE-4.0-32B-FP8](https://huggingface.co/furiosa-ai/EXAONE-4.0-32B-FP8) | 4 | 131072 |
| [furiosa-ai/Qwen3-32B-FP8](https://huggingface.co/furiosa-ai/Qwen3-32B-FP8) | 4 | 40960 |
| [furiosa-ai/Llama-3.3-70B-Instruct](https://huggingface.co/furiosa-ai/Llama-3.3-70B-Instruct) | 4 | 131072 |
| [furiosa-ai/Llama-3.1-8B-Instruct](https://huggingface.co/furiosa-ai/Llama-3.1-8B-Instruct) | 1 | 131072 |
| [furiosa-ai/Qwen3-Embedding-8B](https://huggingface.co/furiosa-ai/Qwen3-Embedding-8B) | 1 | 8192 |
| [furiosa-ai/Qwen3-Reranker-8B](https://huggingface.co/furiosa-ai/Qwen3-Reranker-8B) | 1 | 8192 |


## Support
For broader discussions or support of Furiosa SDK and RNGD, we encourage you to participate in the open forum linked below.

- [FuriosaAI Forum](https://forums.furiosa.ai/)


## License
This project is licensed under the Apache License 2.0 — see the [LICENSE](LICENSE) file for details.

# Weekly News Reporter

Weekly News Reporter is an LLM agent that automates the curation, summarization, and compilation of news articles into a formatted weekly report. It uses LangGraph to coordinate three specialized agents in a sequential pipeline.

## How It Works

The pipeline runs three agents in sequence:

1. **NewsSearcher** — Fetches recent AI/ML news articles via the Tavily search API (a pre-saved response is included so the demo runs without an API key).
2. **Summarizer** — Generates a concise 2–3 sentence summary of each article using the LLM, making technical content accessible to general audiences.
3. **Publisher** — Compiles all summaries into a formatted Markdown weekly report with an introduction, main news items, and links for further reading.

## Installation

```bash
furiosa-llm serve furiosa-ai/Llama-3.1-8B-Instruct --devices "npu:0"
```
```bash
pip install -r requirements.txt
```

## Usage

```bash
python app.py
```

Pre-generated sample outputs are available in `app.ipynb`.

## References

This code was adapted from [GenAI_Agents](https://github.com/NirDiamant/GenAI_Agents/blob/main/all_agents_tutorials/ainsight_langgraph.ipynb).

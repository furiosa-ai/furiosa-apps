# Chat Playground with Real-Time Performance Metrics
This playground combines a conversational AI interface with a real-time performance dashboard, highlighting LLM's generation capability and system-level metrics of RNGD.
[![Chat Playground demo](assets/chat_playground.gif)](https://www.youtube.com/watch?v=Eka1A99t2eI)


To quantify these metrics, the dashboard tracks five metrics in real time:
- Tokens Per Second (TPS): generation throughput
- Time to First Token (TTFT): latency until the first output token
- Time Per Output Token (TPOT): token-level latency
- End-to-End Latency (E2E): total response time
- Power per card (W): energy efficiency during inference

## Installation

```bash
pip install -r backend/requirements.txt
```
The frontend is prebuilt and served from `backend/static/`. To rebuild the frontend, run `./build.sh`.

## Usage
Step 1. Start the LLM server with port 8000:
```bash
furiosa-llm serve furiosa-ai/EXAONE-4.0-32B-FP8 \
    --enable-prefix-caching \
    --enable-auto-tool-choice \
    --tool-call-parser hermes \
    --port 8000
```

Step 2. Start the backend server:

```bash
python backend/main.py --model-id furiosa-ai/EXAONE-4.0-32B-FP8
```

Step 3. Open http://localhost:8001 in your browser.

## Note
- The frontend is prebuilt and served from `backend/static/`.
- Frontend source is included for optional UI customization. Rebuild the frontend if you modify the UI.

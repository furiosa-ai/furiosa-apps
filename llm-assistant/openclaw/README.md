# OpenClaw with Furiosa-LLM
OpenClaw is an open-source AI agent platform that lets you build a customized AI assistant in your own workspace.
This guide shows how to use Furiosa-LLM as the backend model for your [OpenClaw](https://github.com/openclaw/openclaw) setup.

<div align="center">
    <img src="assets/openclaw.gif" width="80%">
</div>

## 1. Start the Furiosa-LLM server

```bash
furiosa-llm serve furiosa-ai/EXAONE-4.0-32B-FP8 \
    --enable-prefix-caching \
    --enable-auto-tool-choice \
    --tool-call-parser hermes \
    --port 8000
```
Verify the server is running:
```bash
curl -s http://localhost:8000/v1/models | jq .
```

## 2. Connect OpenClaw to Furiosa-LLM
### Scenario 1: First time OpenClaw setup
1. Install OpenClaw (Linux/Mac):
```bash
# We used OpenClaw 2026.3.24 version.
curl -fsSL https://openclaw.ai/install.sh | bash
```
2. Select QuickStart Mode
3. Select Custom providers in  Model/auth provider
4. Configure the Custom Provider
   - Base URL: http://127.0.0.1:8000/v1
   - API Key: leave it blank (Paste API key now > ENTER)
   - Endpoint Compatibility: OpenAI-compatible
   - Model ID: `furiosa-ai/EXAONE-4.0-32B-FP8`
5. Skip Optional Features
   - Chat channel (Telegram, Whatsapp, etc)
   - Search provider (Brave Search, Exa Search, etc)
   - Skills configuration
   - Enable hooks

### Scenario 2: Existing OpenClaw users
```bash
cd llm-assistant/openclaw
bash setup.sh
```
What the script does
1. Checks that OpenClaw is installed
2. Verifies the RNGD endpoint is reachable
3. Adds the `furiosa-ai` provider to `~/.openclaw/openclaw.json` (existing config is preserved)
4. Sets RNGD as the default model
5. Restarts the gateway

### Custom endpoint (Optional)
If your Furiosa-LLM server is running on a different host:
```bash
FURIOSA_BASE_URL="http://your-server:8000/v1" bash setup.sh
```

## Start and Connect Gateway (Important)
OpenClaw requires a running gateway, which connects the agent to messaging apps (e.g., Telegram, Slack) to interact with users.
```bash
openclaw gateway
```

## Verify
Check gateway
```bash
curl http://127.0.0.1:18789
```
Test via OpenClaw
```
openclaw agent --local --session-id test -m "Hello, what model are you?"
```

## Quick Use via Web Dashboard
You are now ready to interact with your personal agent running on RNGDs.
```bash
# In another terminal, run:
openclaw dashboard
```
Then, open the link on web interface
```bash
http://localhost:18789/#token=<your-auth-token>
```

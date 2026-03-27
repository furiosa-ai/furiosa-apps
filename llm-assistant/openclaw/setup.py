#!/usr/bin/env python3
"""Add Furiosa RNGD as a provider to an existing OpenClaw installation."""

import json
import os
import shutil
import subprocess
import sys
from contextlib import suppress
from pathlib import Path
from urllib.request import Request, urlopen

DEFAULT_BASE_URL = "http://localhost:8000/v1"
DEFAULT_MODEL = "EXAONE-4.0-32B-FP8"
DEFAULT_PROVIDER = "furiosa-ai"


def openclaw_config_path():
    home = Path(os.environ.get("HOME", str(Path.home())))
    return home / ".openclaw" / "openclaw.json"


def check_openclaw():
    """Verify OpenClaw is already installed."""
    path = shutil.which("openclaw")
    if not path:
        print(
            "[fail] openclaw not found. Install it first:\n" "curl -fsSL https://openclaw.ai/install.sh | bash",
            file=sys.stderr,
        )
        return False
    print(f"[ok] openclaw: {path}")
    return True


def check_rngd(base_url: str) -> bool:
    """Check if the RNGD server is reachable."""
    try:
        req = Request(f"{base_url}/models", method="GET")
        with urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
            models = [m["id"] for m in data.get("data", [])]
            if models:
                print(f"[ok] RNGD models: {', '.join(models)}")
                return True
            print("[fail] RNGD returned no models", file=sys.stderr)
            return False
    except Exception as e:
        print(f"[fail] cannot reach RNGD at {base_url}: {e}", file=sys.stderr)
        return False


def add_provider(base_url: str, provider: str, model: str):
    """Merge the furiosa-ai provider into the existing openclaw.json."""
    cfg_path = openclaw_config_path()

    # Load existing config
    cfg = {}
    if cfg_path.exists():
        with suppress(json.JSONDecodeError, OSError):
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))

    # Set default model
    agents = cfg.setdefault("agents", {})
    defaults = agents.setdefault("defaults", {})
    model_cfg = defaults.setdefault("model", {})
    model_ref = f"{provider}/{model}"
    model_cfg["primary"] = model_ref

    # Add provider
    models = cfg.setdefault("models", {})
    models["mode"] = "merge"
    providers = models.setdefault("providers", {})
    providers[provider] = {
        "baseUrl": base_url,
        "apiKey": f"{provider}",
        "api": "openai-completions",
        "models": [
            {
                "id": model,
                "name": f"{model}",
                "reasoning": True,
                "input": ["text"],
                "contextWindow": 131072,
                "maxTokens": 131072,
                "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0},
            }
        ],
    }

    cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    print(f"[ok] updated {cfg_path}")
    print(f"[ok] default model → {model_ref}")


def restart_gateway():
    """Restart the gateway to apply changes."""
    openclaw = shutil.which("openclaw")
    if not openclaw:
        return

    result = subprocess.run([openclaw, "gateway", "status"], capture_output=True, text=True)

    if result.returncode == 0 and "running" in result.stdout.lower():
        print("[..] restarting gateway...")
        subprocess.run([openclaw, "gateway", "restart"], check=False)
    else:
        print("[..] starting gateway...")
        subprocess.run([openclaw, "gateway", "start"], check=False)


def main():
    base_url = os.environ.get("FURIOSA_BASE_URL", DEFAULT_BASE_URL)
    model = os.environ.get("FURIOSA_MODEL", DEFAULT_MODEL)
    provider = os.environ.get("FURIOSA_PROVIDER", DEFAULT_PROVIDER)

    print("[..] OpenClaw + Furiosa RNGD\n")
    print(f"   Endpoint: {base_url}")
    print(f"   Model:    {model}\n")

    if not check_openclaw():
        raise SystemExit(1)

    if not check_rngd(base_url):
        raise SystemExit(1)

    add_provider(base_url, provider, model)
    restart_gateway()

    print("\n[ok] Done! OpenClaw is now using Furiosa LLM.\n")
    print('   Test:     openclaw agent --local --session-id test -m "Hello"')
    print("   Web UI:   openclaw dashboard")
    print("   Revert:   openclaw models set <previous-model>  # see: openclaw models list")


if __name__ == "__main__":
    main()

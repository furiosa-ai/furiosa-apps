#!/usr/bin/env python3
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.request import Request, urlopen

DEFAULT_BASE_URL = "http://localhost:8000/v1"
DEFAULT_MODEL = "furiosa-ai/Qwen3-32B-FP8"
DEFAULT_PROVIDER = "furiosa"


def home():
    return Path(os.environ.get("HOME", str(Path.home())))


def prepend_path(p: Path):
    cur = os.environ.get("PATH", "")
    parts = cur.split(os.pathsep) if cur else []
    sp = str(p)
    if sp and sp not in parts:
        parts.insert(0, sp)
        os.environ["PATH"] = os.pathsep.join(parts)


def ensure_common_bins_on_path():
    h = home()
    prepend_path(h / ".opencode" / "bin")
    prepend_path(h / ".local" / "bin")
    prepend_path(h / "bin")


def install_opencode_if_missing():
    if shutil.which("opencode"):
        return True

    if platform.system().lower().startswith("win"):
        print("[fail] native Windows is not supported; use WSL2 or preinstall opencode.", file=sys.stderr)
        return False

    curl = shutil.which("curl")
    bash = shutil.which("bash")
    if not curl or not bash:
        print("[fail] missing curl/bash; please install opencode manually.", file=sys.stderr)
        return False

    print("[..] opencode not found. installing via https://opencode.ai/install")
    subprocess.run(f"{curl} -fsSL https://opencode.ai/install | {bash}", shell=True, check=True)

    # installer often drops binary into ~/.opencode/bin; make it visible in this process
    ensure_common_bins_on_path()
    return shutil.which("opencode") is not None


def write_opencode_json(path: Path, base_url: str, provider: str, model: str):
    model_cfg = {"name": model}
    if "qwen3" in model.lower():
        model_cfg["limit"] = {"context": 32768, "output": 8192}

    cfg = {
        "$schema": "https://opencode.ai/config.json",
        "provider": {
            provider: {
                "npm": "@ai-sdk/openai-compatible",
                "name": "FuriosaNPU",
                "options": {"baseURL": base_url},
                "models": {model: model_cfg},
            }
        },
        "model": f"{provider}/{model}",
        "small_model": f"{provider}/{model}",
    }
    path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def models_ready(base_url: str) -> bool:
    try:
        req = Request(f"{base_url}/models", method="GET")
        with urlopen(req, timeout=2) as r:
            r.read()
        return True
    except Exception:
        return False


def main():
    base_url = os.environ.get("FURIOSA_BASE_URL", DEFAULT_BASE_URL)
    model = os.environ.get("FURIOSA_MODEL", DEFAULT_MODEL)
    provider = DEFAULT_PROVIDER

    ensure_common_bins_on_path()

    if not install_opencode_if_missing():
        raise SystemExit(1)

    cfg_path = Path.cwd() / "opencode.json"
    write_opencode_json(cfg_path, base_url, provider, model)
    print(f"[ok] wrote {cfg_path}")

    if not models_ready(base_url):
        print(f"[fail] LLM not reachable: {base_url}/models", file=sys.stderr)
        raise SystemExit(1)

    print("[ok] launching opencode")
    subprocess.run(["opencode"], check=True)


if __name__ == "__main__":
    main()

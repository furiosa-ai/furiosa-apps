#!/usr/bin/env bash
set -euo pipefail

export FURIOSA_BASE_URL="http://localhost:8000/v1"
export FURIOSA_MODEL="furiosa-ai/Qwen3-32B-FP8"
export FURIOSA_PROVIDER="furiosa"

exec python3 furiosa-opencode.py

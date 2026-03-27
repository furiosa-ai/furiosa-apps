#!/usr/bin/env bash
set -euo pipefail

FURIOSA_BASE_URL="${FURIOSA_BASE_URL:-http://localhost:8000/v1}"
FURIOSA_MODEL="${FURIOSA_MODEL:-EXAONE-4.0-32B-FP8}"
FURIOSA_PROVIDER="furiosa-ai"

export FURIOSA_BASE_URL FURIOSA_MODEL FURIOSA_PROVIDER
exec python3 "$(dirname "$0")/setup.py"

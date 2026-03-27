pip install uv
uv venv .lm_eval_venv
uv pip install --python .lm_eval_venv/bin/python lm_eval[api]==v0.4.11 transformers torch

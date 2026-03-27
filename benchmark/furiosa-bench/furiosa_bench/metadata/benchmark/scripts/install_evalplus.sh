pip install uv
uv venv .evalplus_venv
uv pip install --python .evalplus_venv/bin/python "evalplus[vllm]" --upgrade

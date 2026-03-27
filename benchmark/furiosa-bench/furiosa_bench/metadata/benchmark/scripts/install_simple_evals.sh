pip install uv

uv venv .simple_evals_venv
uv pip install --python .simple_evals_venv/bin/python setuptools wheel

git clone https://github.com/furiosa-ai/simple-evals.git
git clone https://github.com/openai/human-eval

uv pip install --python .simple_evals_venv/bin/python \
openai blobfile anthropic tabulate pandas jinja2 requests scipy

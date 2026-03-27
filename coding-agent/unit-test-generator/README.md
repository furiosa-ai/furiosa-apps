# LLM-based Code Explanation & Unit Test Generator

This application generates LLM-based code explanations and unittest test cases from user-provided code, allowing users to interact with the code agent via a web interface or CLI.

## Features

- Upload one or more Python `.py` files
- Generate concise code explanations
- Produce Python `unittest` tests for the uploaded code
- Copy to clipboard or download generated tests
- Iteratively refine tests using additional prompts

## Installation

```bash
pip install -r requirements.txt
```

Recommended model for this project:

```bash
furiosa-llm serve furiosa-ai/Llama-3.1-8B-Instruct --devices "npu:0"
```

## Usage
Run the CLI with `python app.py`, or run the web interface with `streamlit run web_app.py` and open the URL shown below.
```bash
# for CLI
python app.py
# for Web Interface
streamlit run web_app.py
```

Then open [http://localhost:8501](http://localhost:8501) in your browser.

1. In the sidebar, set **API Base URL** (default: `http://localhost:8000/v1`) and **API Key** (default: `EMPTY` for a local Furiosa-LLM server).
    > Note: `EMPTY` is a placeholder accepted by a local Furiosa-LLM server that does not require authentication.
2. Upload one or more Python `.py` files using the file uploader.
3. Click **Generate Explanation & Tests** for a one-step process, or use **Generate Explanation** and **Generate Tests** separately.
4. To iteratively improve the generated tests, enter a follow-up prompt in the refinement box and click **Apply Fix**.
5. Use the **Copy** or **Download** button to export the generated test file.

## Examples

The `examples/` folder contains sample modules to try out the demo:

- `examples/calculator.py`: recursive-descent arithmetic parser
- `examples/polynomial.py`: polynomial arithmetic and evaluation

## Project Structure

```
.
├── app.py            # CLI application
├── web_app.py        # Streamlit web interface
├── examples/         # Sample Python modules
│   ├── calculator.py
│   └── polynomial.py
├── README.md         # Project documentation
├── requirements.txt  # Python dependencies
└── pyproject.toml    # Project metadata
```

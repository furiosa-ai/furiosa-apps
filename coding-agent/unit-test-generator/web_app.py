import json
import os
import re

import openai
import streamlit as st
import streamlit.components.v1 as components


def main():
    st.title("LLM-based Code Explanation & Unittest Generator")

    api_key = st.sidebar.text_input("OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
    # Optional custom base URL for the OpenAI API
    base_url = st.sidebar.text_input(
        "OpenAI Base URL",
        value=os.getenv("OPENAI_API_BASE", ""),
        help="Override the OpenAI API base URL (e.g. for Azure OpenAI or on-prem deployments)",
    )
    if base_url:
        openai.base_url = base_url
    # Model to use for completions
    model = st.sidebar.text_input(
        "Model",
        value=os.getenv("OPENAI_MODEL"),
        help="Enter the model name, e.g. 'gpt-3.5-turbo' or 'gpt-4'.",
    )

    if not api_key:
        st.sidebar.error("Please provide your OpenAI API key.")
        st.stop()
    openai.api_key = api_key

    uploaded_files = st.file_uploader("Upload Python files", type="py", accept_multiple_files=True)
    if not uploaded_files:
        st.info("Upload one or more `.py` files to generate explanations and tests.")
        st.stop()

    # Clean up stale session state entries
    file_keys = {f"file_{f.name}" for f in uploaded_files}
    prompt_keys = {f"prompt_{f.name}" for f in uploaded_files}
    for key in list(st.session_state.keys()):
        if key.startswith("file_") and key not in file_keys:
            del st.session_state[key]
        if key.startswith("prompt_") and key not in prompt_keys:
            del st.session_state[key]

    # Initialize session state for each file
    for uploaded in uploaded_files:
        key = f"file_{uploaded.name}"
        if key not in st.session_state:
            try:
                code = uploaded.read().decode("utf-8")
            except Exception:
                code = uploaded.read().decode("latin-1")
            st.session_state[key] = {
                "name": uploaded.name,
                "code": code,
                # Chat message history: list of {role, content}
                "messages": [],
                # Latest parsed explanation and tests
                "explanation": None,
                "tests": None,
            }

    # Per-file UI
    for uploaded in uploaded_files:
        key = f"file_{uploaded.name}"
        state = st.session_state[key]
        # File section: always expanded so results remain visible after generation
        with st.expander(uploaded.name, expanded=True):
            # If neither explanation nor tests exist, generate both in one go
            if (
                state["explanation"] is None
                and state["tests"] is None
                and st.button("Generate Explanation & Tests", key=f"gen_all_{uploaded.name}")
            ):
                # 1) Explanation
                system_prompt_expl = (
                    "You are a helpful assistant. Given Python code, provide a concise explanation "
                    "labeled '## Explanation'."
                )
                expl_messages = [
                    {"role": "system", "content": system_prompt_expl},
                    {"role": "user", "content": f"Here is the Python code:\n\n{state['code']}"},
                ]
                try:
                    with st.spinner("Generating explanation..."):
                        resp_expl = openai.chat.completions.create(
                            model=model,
                            messages=expl_messages,
                        )
                    expl_raw = resp_expl.choices[0].message.content
                    if "</think>" in expl_raw:
                        expl_raw = expl_raw.split("</think>", 1)[1]
                    if expl_raw.lower().startswith("## explanation"):
                        expl_text = "\n".join(expl_raw.splitlines()[1:]).strip()
                    else:
                        expl_text = expl_raw.strip()
                    state["explanation"] = expl_text
                except Exception as e:
                    st.error(f"Error generating explanation: {e}")
                    st.stop()
                # 2) Tests
                system_prompt_tests = (
                    "You are a helpful assistant. Given Python code and its explanation, "
                    "provide Python unittests labeled '## Unittests' using the unittest framework."
                )
                test_messages = [
                    {"role": "system", "content": system_prompt_tests},
                    {"role": "user", "content": f"Here is the Python code:\n\n{state['code']}"},
                    {"role": "user", "content": f"## Explanation\n{state['explanation']}"},
                ]
                try:
                    with st.spinner("Generating tests..."):
                        resp_tests = openai.chat.completions.create(
                            model=model,
                            messages=test_messages,
                        )
                    tests_raw = resp_tests.choices[0].message.content
                    if "</think>" in tests_raw:
                        tests_raw = tests_raw.split("</think>", 1)[1]
                    parts = re.split(r"## Unittests", tests_raw, maxsplit=1)
                    state["tests"] = parts[1].strip() if len(parts) == 2 else tests_raw.strip()
                    state["messages"] = test_messages + [{"role": "assistant", "content": tests_raw}]
                except Exception as e:
                    st.error(f"Error generating tests: {e}")
                    st.stop()
            # Show explanation if available
            if state["explanation"] is not None:
                st.subheader("Explanation")
                st.write(state["explanation"])
            # Allow single-step test generation if only explanation exists
            if (
                state["explanation"] is not None
                and state["tests"] is None
                and st.button("Generate Unittests", key=f"gen_tests_{uploaded.name}")
            ):
                system_prompt_tests = (
                    "You are a helpful assistant. Given Python code and its explanation, "
                    "provide Python unittests labeled '## Unittests' using the unittest framework."
                )
                test_messages = [
                    {"role": "system", "content": system_prompt_tests},
                    {"role": "user", "content": f"Here is the Python code:\n\n{state['code']}"},
                    {"role": "user", "content": f"## Explanation\n{state['explanation']}"},
                ]
                try:
                    with st.spinner("Generating tests..."):
                        resp_tests = openai.chat.completions.create(
                            model=model,
                            messages=test_messages,
                        )
                    tests_raw = resp_tests.choices[0].message.content
                    if "</think>" in tests_raw:
                        tests_raw = tests_raw.split("</think>", 1)[1]
                    parts = re.split(r"## Unittests", tests_raw, maxsplit=1)
                    state["tests"] = parts[1].strip() if len(parts) == 2 else tests_raw.strip()
                    state["messages"] = test_messages + [{"role": "assistant", "content": tests_raw}]
                except Exception as e:
                    st.error(f"Error generating tests: {e}")
            # If tests exist, show tests and any fix bubbles
            if state["tests"] is not None:
                # Display only user messages (fix prompts) in chat bubbles
                for msg in state["messages"][3:]:
                    if msg["role"] == "user":
                        if msg["content"].startswith("Here is the Python code"):
                            continue
                        with st.chat_message("user"):
                            st.markdown(msg["content"])

                # Show the current unittests code block
                st.subheader("Unittests")
                st.code(state["tests"], language="python")

                # Copy and download buttons for tests
                safe_name = re.sub(r"\W", "_", state["name"])
                escaped = json.dumps(state["tests"])
                html_code = f"""
<script>
function copyToClipboard_{safe_name}() {{
  const text = {escaped};
  navigator.clipboard.writeText(text);
}}
</script>
<button onclick="copyToClipboard_{safe_name}()">Copy All</button>
"""
                components.html(html_code, height=50)

                st.download_button(
                    "Download Tests",
                    data=state["tests"],
                    file_name=f"test_{state['name']}",
                    mime="text/x-python",
                )

                # Prompt for test refinements (always shown after current tests)
                prompt_key = f"prompt_{state['name']}"
                clear_key = f"clear_{prompt_key}"
                # If a clear flag is set, reset the prompt
                if st.session_state.get(clear_key, False):
                    st.session_state[prompt_key] = ""
                    del st.session_state[clear_key]
                if prompt_key not in st.session_state:
                    st.session_state[prompt_key] = ""
                prompt = st.text_area(
                    "Additional Prompt to Refine Tests",
                    value=st.session_state[prompt_key],
                    key=prompt_key,
                    height=100,
                )
                if st.button("Apply Fix", key=f"fix_{state['name']}"):
                    if not prompt.strip():
                        st.warning("Please enter a prompt to refine the tests.")
                    else:
                        # Revise only the unittests; explanation remains unchanged
                        system_prompt2 = (
                            "You are an assistant that revises Python unittests based on the user's feedback. "
                            "Only output the updated '## Unittests' section, "
                            "without any additional explanation or sections."
                        )
                        refine_messages = [
                            {"role": "system", "content": system_prompt2},
                            {"role": "user", "content": f"Here is the Python code:\n\n{state['code']}"},
                            {"role": "assistant", "content": f"## Unittests\n{state['tests']}"},
                            {"role": "user", "content": prompt},
                        ]
                        try:
                            with st.spinner("Refining..."):
                                resp = openai.chat.completions.create(
                                    model=model,
                                    messages=refine_messages,
                                )
                            # Raw refine output
                            new_content = resp.choices[0].message.content
                            # Strip reasoning before </think>
                            if "</think>" in new_content:
                                new_content = new_content.split("</think>", 1)[1]
                            parts = re.split(r"## Unittests", new_content, maxsplit=1)
                            tests_part = parts[1].strip() if len(parts) == 2 else new_content.strip()

                            # Append this round to chat history and update tests
                            state["messages"].append({"role": "user", "content": prompt})
                            state["messages"].append({"role": "assistant", "content": new_content})
                            state["tests"] = tests_part
                            # Flag to clear the refine prompt on next run and rerun UI
                            st.session_state[clear_key] = True
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error refining content: {e}")


if __name__ == "__main__":
    # set configs
    os.environ["OPENAI_API_BASE"] = "http://localhost:8000/v1/"
    os.environ["OPENAI_API_KEY"] = "EMPTY"
    os.environ["OPENAI_MODEL"] = "furiosa-ai/Llama-3.1-8B-Instruct"
    main()

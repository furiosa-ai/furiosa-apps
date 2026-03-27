import argparse
import asyncio
import json
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

import furiosa_smi_py
import psutil
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from openai import AsyncOpenAI

parser = argparse.ArgumentParser()
parser.add_argument("--backend-port", type=int, default=8001, help="Port to run the backend server on")
parser.add_argument("--llm-port", type=int, default=8000, help="Port of the LLM server")
parser.add_argument("--model-id", type=str, default="meta-llama/Llama-3.1-8B-Instruct", help="Model ID for tokenizer")
args, _ = parser.parse_known_args()

try:
    from furiosa_llm.tokenizer import get_tokenizer

    tokenizer = get_tokenizer(args.model_id)
except ImportError:
    tokenizer = None

executor = ProcessPoolExecutor(max_workers=1, initializer=furiosa_smi_py.init)


def create_llm_client():
    return AsyncOpenAI(
        base_url=f"http://localhost:{args.llm_port}/v1/",
        api_key="EMPTY",
    )


llm_client = None
request_counter = 0


class ConnectionClosed(RuntimeError):
    pass


@dataclass
class ConnectionState:
    websocket: WebSocket
    send_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    generated_token_count: int = 0
    tps_history: list[int] = field(default_factory=list)
    max_tps_value: int = 0
    tasks: set[asyncio.Task] = field(default_factory=set)


async def to_process(func, *args):
    if not executor:
        return None
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, func, *args)


async def generate_llm_response(topic):
    """Generate a streamed response from the configured LLM server."""
    try:
        messages = [{"role": "user", "content": topic}]

        stream = await llm_client.chat.completions.create(
            model="EMPTY",
            messages=messages,
            temperature=0,
            stream=True,
            stream_options={"include_usage": True},
        )

        async for chunk in stream:
            if not chunk.choices:
                yield {"usage": {"prompt": chunk.usage.prompt_tokens, "total": chunk.usage.total_tokens}}
            elif hasattr(chunk.choices[0].delta, "reasoning_content") and chunk.choices[0].delta.reasoning_content:
                yield {"reasoning": chunk.choices[0].delta.reasoning_content}
            elif chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        raise RuntimeError(f"LLM generation failed: {e}") from e


def get_power_sync():
    devices = furiosa_smi_py.list_devices()
    if not devices:
        raise RuntimeError("No Furiosa devices detected")
    return devices[0].power_consumption()


def get_temp_sync():
    devices = furiosa_smi_py.list_devices()
    if not devices:
        raise RuntimeError("No Furiosa devices detected")
    return devices[0].device_temperature().soc_peak()


async def validate_llm_connection():
    try:
        await llm_client.models.list()
    except Exception as e:
        raise RuntimeError(f"Failed to reach Furiosa-LLM server: {e}") from e


async def send_json(state: ConnectionState, payload: dict):
    try:
        async with state.send_lock:
            await state.websocket.send_text(json.dumps(payload))
    except Exception as e:
        raise ConnectionClosed("Websocket is no longer writable") from e


def track_task(state: ConnectionState, task: asyncio.Task):
    state.tasks.add(task)
    task.add_done_callback(lambda finished_task: state.tasks.discard(finished_task))


async def metrics_loop(state: ConnectionState):
    while True:
        power = round(await to_process(get_power_sync), 1)
        temperature = round(await to_process(get_temp_sync), 1)

        tokens_per_sec = state.generated_token_count
        state.generated_token_count = 0

        if tokens_per_sec > 0:
            state.tps_history.append(tokens_per_sec)
            if len(state.tps_history) > 1000:
                state.tps_history.pop(0)

        if state.tps_history:
            sorted_tps = sorted(state.tps_history, reverse=True)
            percentile_95_index = int(len(sorted_tps) * 0.05)
            state.max_tps_value = sorted_tps[percentile_95_index]

        efficiency = round(tokens_per_sec / power, 2) if power > 0 else 0
        memory_usage = round(psutil.virtual_memory().percent, 1)
        cpu_usage = round(psutil.cpu_percent(), 1)

        info_message = {
            "action": "INFO_UPDATE",
            "power": power,
            "temperature": temperature,
            "tokens_per_sec": tokens_per_sec,
            "max_tps": state.max_tps_value,
            "memory_usage": memory_usage,
            "cpu_usage": cpu_usage,
            "efficiency": efficiency,
        }
        await send_json(state, info_message)
        await asyncio.sleep(1)


async def handle_chat_request(state: ConnectionState, user_message: str):
    """Handle a single chat request for one websocket connection."""
    global request_counter

    request_counter += 1
    request_id = f"msg_{request_counter}"

    create_message = {"action": "CREATE", "request_id": request_id, "user_message": user_message}
    await send_json(state, create_message)

    task = asyncio.create_task(stream_chat_updates(state, request_id, user_message))
    track_task(state, task)


async def stream_chat_updates(state: ConnectionState, request_id: str, user_message: str):
    """Stream LLM token chunks and timing metrics to the owning websocket only."""
    request_start_time = time.time()
    first_token_time = None
    ttft_ms = 0
    all_chunks: list[str] = []
    all_reasoning: list[str] = []

    try:
        last_token_count = 0
        last_token_count_update_time = time.time()
        tokens_total = 0
        tokens_prompt = 0

        async for chunk in generate_llm_response(user_message):
            is_usage = isinstance(chunk, dict) and "usage" in chunk
            is_reasoning = isinstance(chunk, dict) and "reasoning" in chunk

            if is_usage:
                tokens_prompt = chunk["usage"]["prompt"]
                tokens_total = chunk["usage"]["total"]
                continue

            if is_reasoning:
                reasoning_text = chunk["reasoning"]
                all_reasoning.append(reasoning_text)

                if time.time() - last_token_count_update_time > 0.3:
                    current_token_count = 0
                    if tokenizer:
                        current_token_count = len(tokenizer.encode("".join(all_reasoning))) + len(
                            tokenizer.encode("".join(all_chunks))
                        )
                    state.generated_token_count += current_token_count - last_token_count
                    last_token_count = current_token_count
                    last_token_count_update_time = time.time()

                update_message = {"action": "UPDATE", "request_id": request_id, "reasoning_chunk": reasoning_text}
                await send_json(state, update_message)
                continue

            if first_token_time is None:
                first_token_time = time.time()
                ttft_ms = round((first_token_time - request_start_time) * 1000)

            all_chunks.append(chunk)

            if time.time() - last_token_count_update_time > 0.3:
                current_token_count = 0
                if tokenizer:
                    current_token_count = len(tokenizer.encode("".join(all_reasoning))) + len(
                        tokenizer.encode("".join(all_chunks))
                    )
                state.generated_token_count += current_token_count - last_token_count
                last_token_count = current_token_count
                last_token_count_update_time = time.time()

            update_message = {"action": "UPDATE", "request_id": request_id, "chunk": chunk}
            await send_json(state, update_message)

        request_end_time = time.time()
        e2e_ms = round((request_end_time - request_start_time) * 1000)

        total_tokens = 0
        tokens_reasoning = 0
        tokens_response = 0
        if tokenizer and all_chunks:
            tokens_reasoning = len(tokenizer.encode("".join(all_reasoning)))
            tokens_response = len(tokenizer.encode("".join(all_chunks)))
            total_tokens = tokens_reasoning + tokens_response

        state.generated_token_count += total_tokens - last_token_count

        generation_time_ms = e2e_ms - (ttft_ms if first_token_time else 0)
        tpot_ms = round(generation_time_ms / max(total_tokens, 1), 1) if total_tokens > 0 else 0

        timing_message = {
            "action": "TIMING_UPDATE",
            "request_id": request_id,
            "ttft": ttft_ms if first_token_time else 0,
            "e2e_latency": e2e_ms,
            "tpot": tpot_ms,
            "tokens_reasoning": tokens_reasoning,
            "tokens_response": tokens_response,
            "tokens_total": tokens_total,
            "tokens_prompt": tokens_prompt,
        }
        await send_json(state, timing_message)
        await send_json(state, {"action": "COMPLETED", "request_id": request_id})

    except asyncio.CancelledError:
        return
    except ConnectionClosed:
        return
    except Exception as e:
        request_end_time = time.time()
        e2e_ms = round((request_end_time - request_start_time) * 1000)
        ttft_ms = round((first_token_time - request_start_time) * 1000) if first_token_time else 0

        total_tokens = 0
        if tokenizer and all_chunks:
            total_tokens = len(tokenizer.encode("".join(all_chunks)))

        generation_time_ms = e2e_ms - ttft_ms
        tpot_ms = round(generation_time_ms / max(total_tokens, 1), 1) if total_tokens > 0 else 0

        timing_message = {
            "action": "TIMING_UPDATE",
            "request_id": request_id,
            "ttft": ttft_ms,
            "e2e_latency": e2e_ms,
            "tpot": tpot_ms,
        }
        error_message = {"action": "FAILED", "request_id": request_id, "error": str(e)}

        try:
            await send_json(state, timing_message)
            await send_json(state, error_message)
        except ConnectionClosed:
            return


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.websocket("/updates")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    state = ConnectionState(websocket=websocket)
    await send_json(state, {"action": "INIT"})

    metrics_task = asyncio.create_task(metrics_loop(state))
    track_task(state, metrics_task)

    try:
        while True:
            raw_message = await websocket.receive_text()
            try:
                data = json.loads(raw_message)
            except json.JSONDecodeError:
                continue

            if data.get("action") != "SEND_MESSAGE":
                continue

            message = (data.get("message") or "").strip()
            if not message:
                continue

            await handle_chat_request(state, message)

    except WebSocketDisconnect:
        pass
    finally:
        tasks = list(state.tasks)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


@app.get("/api/model_info")
async def get_model_info():
    """Fetch model information from the LLM server."""
    try:
        models = await llm_client.models.list()
        if models.data and len(models.data) > 0:
            return {"model_id": models.data[0].id}
    except Exception as e:
        print(f"Failed to fetch model info: {e}")
    return {"model_id": "Unknown"}


@app.on_event("startup")
async def startup():
    global llm_client

    llm_client = create_llm_client()

    await to_process(get_power_sync)
    await to_process(get_temp_sync)
    await validate_llm_connection()
    print("Backend started - Furiosa hardware and LLM server validated")


static_dir = Path(__file__).parent / "static"
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=args.backend_port, reload=True)

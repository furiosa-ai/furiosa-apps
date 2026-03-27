import argparse
import asyncio
import json
import math
import random
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import furiosa_smi_py
import pandas as pd
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from models.sentiment_analyzer import SentimentAnalyzer

parser = argparse.ArgumentParser()
parser.add_argument("--model-id", type=str, default="meta-llama/Llama-3.1-8B-Instruct", help="Model ID for tokenizer")
args, _ = parser.parse_known_args()

executor = ProcessPoolExecutor(max_workers=1, initializer=furiosa_smi_py.init)


def get_power_sync():
    return furiosa_smi_py.list_devices()[-1].power_consumption()


def get_temp_sync():
    return furiosa_smi_py.list_devices()[-1].device_temperature().soc_peak()


async def to_process(func, *args):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, func, *args)


app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
connected_clients: list[WebSocket] = []
sentiment_analyzer = SentimentAnalyzer(args.model_id)
tweets = []  # All tweets with their current status
all_tweets = []  # Source tweet texts
requests_per_second = 3.0  # Target requests per second
current_index = 0
processing_enabled = False  # User-controlled processing flag
next_tweet_id = 0
analysis_tasks = set()  # Track running analysis tasks


# Load tweet data
def load_tweet_data():
    global all_tweets
    try:
        data_dir = Path("data")
        csv_files = [f for f in data_dir.iterdir() if f.suffix == ".csv"]

        tweet_texts = []
        for csv_file in csv_files:
            df = pd.read_csv(csv_file)
            # Check for different possible column names for tweet text
            text_column = None
            for col in ["Tweet", "text", "content", "message"]:
                if col in df.columns:
                    text_column = col
                    break

            if text_column:
                texts = df[text_column].dropna().tolist()
                # tweet_texts.extend(texts[:100])
                tweet_texts.extend(texts)
                print(f"Loaded {len(texts)} tweets from {csv_file.name} (column: {text_column})")

        all_tweets = tweet_texts
        print(f"Loaded {len(all_tweets)} tweet texts")
    except Exception as e:
        print(f"Error loading tweet data: {e}")


# Generate Poisson-distributed inter-arrival time
def get_next_arrival_time():
    # Lambda = requests_per_second, so mean inter-arrival time = 1/lambda
    mean_interval = 1.0 / requests_per_second
    # Generate exponential random variable (Poisson process)
    return -math.log(1.0 - random.random()) * mean_interval


def cleanup_old_tweets():
    global tweets
    current_time = time.time()
    # Find tweets to remove
    tweets_to_remove = [
        tweet["id"]
        for tweet in tweets
        if tweet["status"] == "completed" and tweet.get("completed_at") and current_time - tweet["completed_at"] >= 5
    ]

    if tweets_to_remove:
        # Remove from array
        tweets = [tweet for tweet in tweets if tweet["id"] not in tweets_to_remove]
        # Notify clients
        send_tweets_removed(tweets_to_remove)


# Send only configuration updates (no tweets)
def send_config_update():
    asyncio.create_task(
        broadcast_message(
            {
                "type": "config_update",
                "data": {"processing_enabled": processing_enabled, "requests_per_second": requests_per_second},
            }
        )
    )


# Send tweet status change
def send_tweet_update(tweet):
    asyncio.create_task(broadcast_message({"type": "tweet_update", "data": tweet}))


# Send multiple tweet removals
def send_tweets_removed(tweet_ids):
    if tweet_ids:
        asyncio.create_task(broadcast_message({"type": "tweets_removed", "data": {"tweet_ids": tweet_ids}}))


# Send full state only on initial connection
def send_initial_state():
    asyncio.create_task(
        broadcast_message(
            {
                "type": "initial_state",
                "data": {
                    "tweets": tweets,
                    "processing_enabled": processing_enabled,
                    "requests_per_second": requests_per_second,
                },
            }
        )
    )


# Continuous background processing task
async def background_processor():
    global next_tweet_id, all_tweets, tweets

    while True:
        # Clean up old completed tweets every cycle
        cleanup_old_tweets()

        # Only process if we have connected clients AND processing is enabled
        if len(connected_clients) == 0 or not processing_enabled:
            await asyncio.sleep(0.5)  # Wait 500ms when idle
            continue

        # Use Poisson distribution for realistic arrival times
        next_arrival = get_next_arrival_time()
        await asyncio.sleep(next_arrival)

        # Create new pending tweet
        if len(all_tweets) > 0:
            tweet_text = random.choice(all_tweets)
            new_tweet = {
                "id": next_tweet_id,
                "text": tweet_text,
                "status": "pending",
                "company": None,
                "sentiment": None,
                "confidence": None,
                "completed_at": None,
            }
            tweets.append(new_tweet)
            next_tweet_id += 1
            send_tweet_update(new_tweet)


# Separate task to spawn parallel tweet analysis tasks
async def tweet_processor():
    while True:
        # Only process if processing is enabled and we have connected clients
        if len(connected_clients) == 0 or not processing_enabled:
            await asyncio.sleep(0.5)
            continue

        # Find pending tweets that haven't been started yet
        pending_tweets = [t for t in tweets if t["status"] == "pending"]

        # Start analysis tasks for pending tweets (parallel processing)
        for tweet in pending_tweets:
            # Mark as queuing to prevent duplicate task creation
            tweet["status"] = "queuing"
            send_tweet_update({"id": tweet["id"], "status": "queuing"})
            # Create individual analysis task for each pending tweet
            task = asyncio.create_task(analyze_tweet_task(tweet))
            analysis_tasks.add(task)
            task.add_done_callback(analysis_tasks.discard)

        await asyncio.sleep(0.1)


# Individual tweet analysis task (runs in parallel)
async def analyze_tweet_task(tweet):
    try:
        # Check if tweet is still queuing (should be after being marked in tweet_processor)
        if tweet["status"] != "queuing":
            return

        tweet["status"] = "processing"
        send_tweet_update({"id": tweet["id"], "status": "processing"})

        # Start LLM analysis
        result = await sentiment_analyzer.analyze(tweet["text"])

        # Update tweet with results
        tweet["status"] = "completed"
        tweet["company"] = result["company"]
        tweet["sentiment"] = result["sentiment"]
        tweet["confidence"] = result["confidence"]
        tweet["completed_at"] = time.time()

        # Send updated tweet status with results
        send_tweet_update(
            {
                "id": tweet["id"],
                "status": "completed",
                "company": tweet["company"],
                "sentiment": tweet["sentiment"],
                "confidence": tweet["confidence"],
                "completed_at": tweet["completed_at"],
            }
        )

        # Send current tweet data
        await broadcast_message({"type": "current_tweet", "data": tweet})

        # Send sentiment data for chart
        await broadcast_message({"type": "sentiment_data", "data": result})

        # NPU metrics are sent separately by npu_metrics_task

    except asyncio.CancelledError:
        # Task was cancelled (stop processing)
        print(f"Tweet {tweet['id']} analysis cancelled")
        tweet["status"] = "completed"  # Mark as completed to remove from pending
        tweet["completed_at"] = time.time()
        raise  # Re-raise to properly cancel
    except Exception as e:
        print(f"Tweet analysis error: {e}")
        # Mark tweet as failed
        tweet["status"] = "completed"  # Still mark as completed to remove from pending
        tweet["completed_at"] = time.time()


async def npu_metrics_task():
    """Separate task to gather and broadcast NPU metrics every second"""
    while True:
        if len(connected_clients) > 0:
            power = await to_process(get_power_sync)
            temperature = await to_process(get_temp_sync)
            # Get token throughput from sentiment analyzer
            tokens_processed = sentiment_analyzer.total_tokens_processed
            sentiment_analyzer.total_tokens_processed = 0  # Reset counter
            throughput = tokens_processed  # tokens per second
            efficiency = throughput / power if power > 0 else 0  # tokens per sec per watt

            await broadcast_message(
                {
                    "type": "npu_metrics",
                    "data": {
                        "throughput": round(throughput, 1),
                        "efficiency": efficiency,
                        "power": round(power, 0),
                        "temperature": round(temperature, 0),
                    },
                }
            )

        await asyncio.sleep(1.0)  # Send metrics every second


@app.on_event("startup")
async def startup_event():
    await sentiment_analyzer.validate_connection()
    await to_process(get_power_sync)
    await to_process(get_temp_sync)
    load_tweet_data()
    # Start all background tasks
    asyncio.create_task(background_processor())
    asyncio.create_task(tweet_processor())
    asyncio.create_task(npu_metrics_task())


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global requests_per_second, processing_enabled, next_tweet_id, tweets

    await websocket.accept()
    connected_clients.append(websocket)

    # Send initial state to new client only
    await websocket.send_text(
        json.dumps(
            {
                "type": "initial_state",
                "data": {
                    "tweets": tweets,
                    "processing_enabled": processing_enabled,
                    "requests_per_second": requests_per_second,
                },
            }
        )
    )

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message["type"] == "set_rps":
                requests_per_second = message.get("rps", 50.0)
                send_config_update()

            elif message["type"] == "start_processing":
                processing_enabled = True
                # Clear existing tweets and reset counter
                tweets.clear()
                next_tweet_id = 0
                send_config_update()

            elif message["type"] == "stop_processing":
                processing_enabled = False
                # Cancel all running analysis tasks
                for task in analysis_tasks.copy():
                    task.cancel()
                analysis_tasks.clear()
                # Clear all tweets when stopping
                tweets.clear()
                # Send immediate clear notification to frontend
                await broadcast_message({"type": "tweets_cleared", "data": {}})
                send_config_update()

    except WebSocketDisconnect:
        connected_clients.remove(websocket)


async def broadcast_message(message):
    if connected_clients:
        for client in connected_clients.copy():
            try:
                await client.send_text(json.dumps(message))
            except Exception:
                connected_clients.remove(client)


@app.get("/api/status")
async def get_status():
    return {
        "tweets_loaded": len(tweets),
        "current_index": current_index,
        "connected_clients": len(connected_clients),
        "requests_per_second": requests_per_second,
        "processing_enabled": processing_enabled,
    }


# Serve static frontend files
@app.get("/")
async def serve_index():
    return FileResponse("static/index.html")


# Mount static files (must be last)
if Path("static").exists():
    app.mount("/", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)

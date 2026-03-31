# Smart Logistics OpenEnv

A real-world logistics environment simulating a parcel robot operating across warehouse zones and loading docks.

## What this project contains

- `smartlogistics/` — OpenEnv-compatible environment implementation with typed models
- `app.py` — FastAPI server exposing `reset`, `step`, and `state` endpoints
- `inference.py` — baseline agent using OpenAI client and deterministic fallback
- `openenv.yaml` — environment metadata and endpoint mapping
- `Dockerfile` — container image for deployment to Hugging Face Spaces or any Docker host

## Environment overview

The environment models a warehouse robot that:
- moves between zones
- picks up packages from origin locations
- delivers packages to destination docks
- manages battery and deadlines

Observations include robot position, battery level, package deadlines, and current carrying state.

Actions support:
- `move`
- `pickup`
- `deliver`
- `recharge`
- `wait`

## Tasks

Three graded tasks are included:
1. `easy` — deliver a small set of packages with relaxed deadlines
2. `medium` — manage delivery deadlines and priority packages
3. `hard` — complete delivery under time, battery, and priority constraints

## Run locally

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the API server:
```bash
uvicorn app:app --host 0.0.0.0 --port 8080
```

3. Call `/reset`, `/step`, and `/state` with JSON body payloads.

## Baseline inference

Set environment variables:
- `API_BASE_URL`
- `MODEL_NAME`
- `HF_TOKEN`

Then run:
```bash
python inference.py
```

If OpenAI variables are not present, the script will run a deterministic heuristic baseline.

## Docker

Build and run:
```bash
docker build -t smartlogistics .
docker run -p 8080:8080 smartlogistics
```

## Hugging Face Spaces

This repository is ready for deployment as a Space using a `Dockerfile` and a FastAPI app.

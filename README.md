# 🌦️ Weather Microframework

![CI/CD Pipeline](https://github.com/MattiaMellone/weather-microfw/actions/workflows/ci.yml/badge.svg)

This project was created as a **personal technical experiment** to evaluate, in practice:

* the usefulness of **uv** as an environment and dependency manager
* integration with common backend components (Django, Celery, Redis, Postgres)
* a simple, reproducible workflow suitable for prototypes and micro‑services

The application itself is intentionally minimal (fetches weather data from a public API and stores it in a database), because the primary goal is to observe **how uv behaves in a real setup**, not to build a complex feature.

---

## 🏛️ Architecture Overview

```
               ┌──────────────────────────┐
               │        Frontend          │
               └──────────────┬───────────┘
                              │ /weather/fetch/
                              ▼
                    ┌──────────────────┐
                    │   Django 5.2 API   │
                    └───────┬──────────┘
                            ▼
                   ┌───────────────────┐
                   │ Typed Service     │
                   │ - Protocol        │
                   │ - TypedDict       │
                   └────────┬──────────┘
                            ▼
           ┌───────────────────────────────────┐
           │ Open-Meteo HTTP Client (httpx)    │
           └───────────────────────────────────┘
                            
                            ▼
                    ┌────────────┐
                    │  Postgres  │  (Docker)
                    └────────────┘

                            ▲
                            │
                     Celery Worker
                     Celery Beat (scheduled tasks)
                     Redis broker (Docker)
```

---

## ⚡ Why uv (and not pip/poetry/etc.)

This repo is designed to show **how uv simplifies the Python toolchain**:

* **Single source of truth**: everything (Django, Celery, mypy, httpx, psycopg2, redis) lives in `pyproject.toml`.
* **Implicit virtualenv**: no `python -m venv`, no manual activation. `uv sync` creates and manages `.venv/` automatically.
* **No pip needed**: uv has its own ultra-fast installer; the venv doesn’t even ship with pip by default.
* **Fast tool bootstrap**: `uv run` and `uvx` let you run tools without global installation.
* **Reproducible**: `pyproject.toml` (+ optional `uv lock`) is enough to rebuild the full environment on any machine.

Typical comparison you can mention live:

| Task                 | Classic (pip/venv)                             | With uv                         |
| -------------------- | ---------------------------------------------- | ------------------------------- |
| Create env           | `python -m venv venv` + activate               | `uv sync`                       |
| Install deps         | `pip install -r requirements.txt`              | `uv add django celery mypy ...` |
| Run manage.py        | `source venv/bin/activate && python manage.py` | `uv run python manage.py`       |
| Add new lib          | `pip install httpx` + update requirements      | `uv add httpx`                  |
| Run tool (e.g. ruff) | `pip install ruff` (global or in venv)         | `uvx ruff check .`              |

---

## 🧱 1. Setup (uv + Docker)

### 1.1 Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

Check:

```bash
uv --version
```

---

### 1.2 Install dependencies (single command)

```bash
uv sync
```

This will:

* create a `.venv/` managed by uv
* install all dependencies from `pyproject.toml`
* make `uv run ...` available as the main entrypoint

---

### 1.3 Start Postgres + Redis

```bash
docker compose up -d
```

Check containers:

```bash
docker compose ps
```

---

## 🧩 2. Run Django (via uv)

You never activate the venv manually; you always go through uv:

```bash
uv run python manage.py migrate
uv run python manage.py runserver
```

This makes it very explicit in CI and docs that **all Python commands go through uv**.

---

## 🎯 3. Weather API Endpoints (local testing)

To test everything **locally**, follow this sequence:

1. Start the base services:

   ```bash
   docker compose up -d
   ```

2. Apply Django migrations:

   ```bash
   uv run python manage.py migrate
   ```

3. Start Django:

   ```bash
   uv run python manage.py runserver
   ```

4. Start Celery (two terminals):

   ```bash
   uv run celery -A microfw worker -l info
   ```

   ```bash
   uv run celery -A microfw beat -l info
   ```

5. Trigger the endpoint that **queues the background job**:

   ```http
   GET /weather/fetch/?city=Bari&lat=41.12&lon=16.87
   ```

   This does *not* fetch the weather directly; Celery performs the async HTTP call.

6. Verify that the async fetch succeeded:

   ```http
   GET /weather/latest/
   ```

---

## 🌐 Async in the project (technical note)

Async usage in this project is **intentionally limited to external I/O** (HTTP calls to Open‑Meteo) and never interacts directly with the Django ORM, which remains fully **synchronous**. This avoids errors such as `SynchronousOnlyOperation` and keeps the architecture stable.

### How the flow works

* Celery uses `asyncio.run()` exclusively to execute the async HTTP client.
* Once the payload is retrieved, the event loop closes.
* Database writes occur in a **pure sync context**, fully compatible with Django ORM.

### Correct task implementation

```python
@shared_task
def fetch_weather_task(city: str, lat: float, lon: float) -> None:
    client = AsyncOpenMeteoClient()

    # Async HTTP call (I/O only)
    payload = asyncio.run(client.get_current(lat=lat, lon=lon))

    # Sync DB write
    store_sample_from_payload(payload, city)
```

### Fetch weather (via Celery)

```http
GET /weather/fetch/?city=Bari&lat=41.12&lon=16.87
```

### Get latest saved sample

```http
GET /weather/latest/
```

The endpoint logic delegates actual weather retrieval to the typed service layer.

---

## 🧵 4. Strongly Typed Service Layer

The interesting part (for architecture & tooling discussions) is `weather/services.py`, which uses:

* `Protocol` → interface for a generic `WeatherClient`
* `TypedDict` → strict shape for the Open-Meteo JSON payload
* a sync `httpx` client
* persistence through Django ORM

Example:

```python
class WeatherClient(Protocol):
    def get_current(self, lat: float, lon: float) -> OpenMeteoResponse: ...


class OpenMeteoResponse(TypedDict):
    latitude: float
    longitude: float
    current_weather: CurrentWeatherPayload
```

The same service is used by:

* the HTTP endpoint (`/weather/fetch/`)
* the Celery task (`weather.tasks.fetch_weather_task`)

So you can talk about **reusability + type safety** in one go.

---

## ⚙️ 5. Celery & Celery Beat (also via uv)

### Start Celery worker

```bash
uv run celery -A microfw worker -l info
```

### Start Celery Beat

```bash
uv run celery -A microfw beat -l info
```

A scheduled job automatically stores Bari weather every 10 minutes:

```python
CELERY_BEAT_SCHEDULE = {
    "fetch_bari_weather_every_10_minutes": {
        "task": "weather.tasks.fetch_weather_task",
        "schedule": 600,
        "args": ("Bari", 41.12, 16.87),
    },
}
```

Again, everything is run through `uv run`, not `python` directly.

---

## 🔍 6. Type Checking (mypy + django-stubs)

Strict mypy configuration is defined in `pyproject.toml` and run through uv:

```bash
uv run mypy
```

Strict mode includes, among others:

* no untyped defs
* no incomplete defs
* no `Any` returns
* missing fields detection
* correct typing for Django models via `django-stubs` plugin

This shows how **tooling (mypy) is also managed through uv** as a first-class dependency.

---

## 🛠️ 7. Project Commands (Quick Reference)

All commands are uv-based, which is the main message of the repo.

### Django

```bash
uv run python manage.py migrate
uv run python manage.py runserver
```

### Celery

```bash
uv run celery -A microfw worker -l info
```

### Celery Beat

```bash
uv run celery -A microfw beat -l info
```

### Type Checking

```bash
uv run mypy
```

### Formatting / Linting (example)

```bash
uvx ruff check --fix
```

---

## 🧪 8. End-to-End Flow (local complete test)

To perform a full end‑to‑end local test:

```bash
git clone <repo>
cd weather-microfw
uv sync
docker compose up -d
uv run python manage.py migrate
uv run python manage.py runserver
```

In two additional terminals:

```bash
uv run celery -A microfw worker -l info
```

```bash
uv run celery -A microfw beat -l info
```

Then:

1. Trigger a manual fetch:

   ```http
   GET http://localhost:8000/weather/fetch/?city=Bari&lat=41.12&lon=16.87
   ```
2. Wait a few seconds for Celery to complete the task.
3. Verify the stored data:

   ```http
   GET http://localhost:8000/weather/latest/
   ```

If you want a **quick demo workflow**:

1. Clone the repo
2. Run `uv sync`
3. Start Docker
4. Apply migrations
5. Start Django
6. Start Celery worker + beat
7. Call the fetch endpoint
8. Call the latest endpoint

Throughout the demo, highlight that **all Python commands are executed via uv**.

---

## ❓ Troubleshooting

### "No module named pip"

uv environments ship without pip by default, because uv is the installer.
If a tool insists on pip (e.g. `mypy --install-types`), you can still:

```bash
uv add pip
```

but in this project everything is managed via `uv add` and `uv sync`.

### Celery typing warnings

Celery has no official type stubs; the mypy config uses overrides to ignore missing imports for Celery while keeping strict mode everywhere else.

---

## 🧠 Design Rationale (Why the project is structured this way)

This section explains **why** the project is structured the way it is.
It provides architectural justification rather than implementation details—useful for understanding the overall design choices.

### 1. Clear separation between async I/O and sync ORM

* The external API client is async because HTTP calls are I/O‑bound.
* Django ORM operations remain sync to ensure stability and avoid edge‑case issues.
* Celery acts as the natural boundary between the two worlds.

This pattern avoids complexity while still providing the performance advantages of async where they matter.

### 2. uv as the single orchestration layer

* All Python operations—Django, Celery, mypy, tooling—are executed through `uv run`.
* No activation of virtualenvs, no pip, no Poetry, no requirements files.
* This keeps developer onboarding extremely short and reduces environment drift.

### 3. Typed service layer for testability & clarity

* Business logic lives outside Django views and tasks.
* Protocols and TypedDicts provide guarantees that the interface and payloads are stable.
* The same service is reused by both HTTP endpoints and Celery tasks.

This mirrors real-world service-oriented designs and improves maintainability.

### 4. Celery as the background execution engine

* Heavy or slow operations are executed outside the request/response cycle.
* The API remains responsive while tasks perform I/O.
* Celery Beat enables periodic ingestion without writing custom schedulers.

This is a simple but effective pattern for microservices and backend tools.

### 5. Minimal surface, but complete workflow

Even though the project is intentionally lightweight, it demonstrates a full chain:

* API layer (Django)
* Async HTTP calls (httpx)
* Typed service layer (Protocol, TypedDict)
* Background worker (Celery)
* Scheduled tasks (Beat)
* Persistent storage (Postgres)
* Managed environment/tooling (uv)

This provides a realistic, end‑to‑end sample while keeping the domain problem intentionally simple.

### 6. Docker for deterministic local services

* Postgres and Redis are isolated and reproducible.
* No need for local installations.
* Makes the environment directly portable to CI pipelines.

---

## 🚀 Summary

This repository is a **modern, uv-first, typed Python microframework** that shows:

* how to structure properly typed services around Django
* how to orchestrate DB + async workers (Postgres, Redis, Celery)
* how to make **uv the central entrypoint** for env management and tooling

It works both as a **demo for technical stakeholders** (architecture, typing, async, orchestration) and as a **template** for future projects.

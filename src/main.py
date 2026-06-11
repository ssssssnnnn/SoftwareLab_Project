from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path

import uvicorn
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from benchmarker import GLOBAL_STATE, run_global_benchmarks


CURRENT_DIR = Path(__file__).parent
STATICS_DIR = CURRENT_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = BackgroundScheduler()

    # Initial startup sync
    scheduler.add_job(
        run_global_benchmarks,
        trigger="date",
        run_date=datetime.now() + timedelta(milliseconds=100),
    )

    # Scheduled hourly sync
    scheduler.add_job(run_global_benchmarks, "interval", hours=1)
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="Package Mirror Performance Monitoring Daemon",
    version="1.0.0",
    lifespan=lifespan,
)


def calculate_summary():
    current_mirrors = GLOBAL_STATE.get("results", [])
    online_mirrors = [m for m in current_mirrors if m["status"] == "Online"]

    fastest_mirror = None
    if online_mirrors:
        fastest_mirror = max(online_mirrors, key=lambda x: x["speed_mbs"])

    avg_latency = (
        sum(m["latency_ms"] for m in online_mirrors) / len(online_mirrors)
        if online_mirrors
        else 0.0
    )

    return {
        "summary": {
            "total_mirrors": len(current_mirrors),
            "online_count": len(online_mirrors),
            "fastest_mirror_name": fastest_mirror["name"] if fastest_mirror else "N/A",
            "fastest_mirror_url": fastest_mirror["url"] if fastest_mirror else "",
            "fastest_mirror_type": fastest_mirror["type"] if fastest_mirror else "",
            "average_latency_ms": round(avg_latency, 2),
        },
        "mirrors": current_mirrors,
    }


@app.get("/api/metrics")
async def get_metrics():
    # Returns the existing memory cache instantly
    return calculate_summary()


# Change the path from /api/refresh to /api/forcerun
@app.post("/api/forcerun")
async def trigger_refresh():
    # Forces the backend to actually re-test the network mirrors right now!
    run_global_benchmarks()
    return calculate_summary()


@app.get("/")
async def root_redirect():
    return RedirectResponse(url="/index.html")


app.mount("/", StaticFiles(directory=STATICS_DIR), name="static")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)

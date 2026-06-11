import json
import logging
import time
from typing import Any, Dict
from pathlib import Path

import httpx

logger = logging.Logger(__name__)


CURRENT_DIR = Path(__file__).parent
MIRRORS_FILE_PATH = CURRENT_DIR / "mirrors.json"

with open(MIRRORS_FILE_PATH) as f:
    MIRRORS_TO_CHECK = json.load(f)
    MIRROR_TYPES = set([mirror["type"] for mirror in MIRRORS_TO_CHECK])

# In-memory storage for saving results
GLOBAL_STATE = {"results": []}


def test_single_mirror(client: httpx.Client, mirror: Dict[str, str]) -> Dict[str, Any]:
    base_url = mirror["url"]
    test_endpoint = f"{base_url.rstrip('/')}{mirror['test_file']}"

    result = {
        "name": mirror["name"],
        "url": base_url,
        "type": mirror["type"],
        "status": "Offline",
        "latency_ms": 0.0,
        "speed_mbs": 0.0,
        "last_checked": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    try:
        start_time = time.perf_counter()
        try:
            response = client.get(base_url, timeout=2.5, follow_redirects=True)
        except httpx.HTTPError:
            response = client.get(base_url, timeout=2.5, follow_redirects=True)

        latency = (time.perf_counter() - start_time) * 1000

        if response.is_success or response.status_code in [301, 302, 403]:
            result["status"] = "Online"
            result["latency_ms"] = round(latency, 2)

            download_start = time.perf_counter()
            try:
                with client.stream("GET", test_endpoint, timeout=2.5) as resp:
                    bytes_downloaded = 0
                    for chunk in resp.iter_bytes(chunk_size=4096):
                        bytes_downloaded += len(chunk)
                        if (
                            bytes_downloaded > 262144
                            or (time.perf_counter() - download_start) > 1.0
                        ):
                            break

                duration = time.perf_counter() - download_start
                if duration > 0 and bytes_downloaded > 0:
                    speed_mbs = (bytes_downloaded / (1024 * 1024)) / duration
                    result["speed_mbs"] = round(speed_mbs, 2)
            except Exception:
                result["speed_mbs"] = 0.0

    except Exception as e:
        logger.warning(f"Connection failed for {mirror['name']}: {e}")
        result["status"] = "Offline"

    return result


def run_global_benchmarks():
    global GLOBAL_STATE
    logger.info("--> Starting global mirrors benchmark execution sync...")

    updated_metrics = []

    with httpx.Client(follow_redirects=True, verify=False) as client:
        for mirror in MIRRORS_TO_CHECK:
            logger.info(f"Testing mirror entity: {mirror['name']} ({mirror['url']})")
            try:
                res = test_single_mirror(client, mirror)
                logger.info(
                    f"Result -> Status: {res['status']}, "
                    f"Latency: {res['latency_ms']}ms, Speed: {res['speed_mbs']}MB/s"
                )
                updated_metrics.append(res)
            except Exception:
                logger.exception(f"Critical exception running {mirror['name']}")
                updated_metrics.append(
                    {
                        "name": mirror["name"],
                        "url": mirror["url"],
                        "type": mirror["type"],
                        "status": "Offline",
                        "latency_ms": 0.0,
                        "speed_mbs": 0.0,
                        "last_checked": time.strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )

        GLOBAL_STATE["results"] = updated_metrics
        logger.info(
            f"--> Benchmark run completed. "
            f"Saved {len(GLOBAL_STATE['results'])} entries to global state."
        )

import time
import httpx
from typing import List, Dict, Any

# Expanded target mirrors to benchmark
MIRRORS_TO_CHECK = [
    # --- PyPI Registries ---
    {"name": "PyPI Global (Upstream)", "url": "https://pypi.org/simple", "type": "PyPI", "test_file": "/pip/"},
    {"name": "PyPI Mirror (Cloudflare)", "url": "https://pypi.cloudflarecdn.com/simple", "type": "PyPI", "test_file": "/pip/"},
    {"name": "PyPI Mirror (Jeiran IR)", "url": "https://mirror.jeiran.ir/pypi/simple", "type": "PyPI", "test_file": "/"},
    {"name": "PyPI Mirror (SUT IR)", "url": "https://mirror.sharif.edu/pypi/simple", "type": "PyPI", "test_file": "/"},
    {"name": "PyPI Mirror (ArvanCloud IR)", "url": "https://pypi.arvancloud.ir/simple", "type": "PyPI", "test_file": "/"},
    {"name": "PyPI Mirror (CDN IR)", "url": "https://mirror.cdn.ir/repository/pypi/simple", "type": "PyPI", "test_file": "/"},

    # --- NPM Registries ---
    {"name": "NPM Global (Upstream)", "url": "https://registry.npmjs.org", "type": "NPM", "test_file": "/express"},
    {"name": "NPM Mirror (Cloudflare)", "url": "https://registry.npmjs.cf", "type": "NPM", "test_file": "/express"},
    {"name": "NPM Mirror (IranServer IR)", "url": "https://npm.iranserver.com", "type": "NPM", "test_file": "/"},
    {"name": "NPM Mirror (ArvanCloud IR)", "url": "https://npm.arvancloud.ir", "type": "NPM", "test_file": "/"},
    {"name": "NPM Mirror (Jeiran IR)", "url": "https://mirror.jeiran.ir/npm", "type": "NPM", "test_file": "/"}
]

# Bulletproof shared memory pointer reference wrapper
GLOBAL_STATE = {
    "results": []
}

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
        "last_checked": time.strftime("%Y-%m-%d %H:%M:%S")
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
                        if bytes_downloaded > 262144 or (time.perf_counter() - download_start) > 1.0:
                            break
                
                duration = time.perf_counter() - download_start
                if duration > 0 and bytes_downloaded > 0:
                    speed_mbs = (bytes_downloaded / (1024 * 1024)) / duration
                    result["speed_mbs"] = round(speed_mbs, 2)
            except Exception:
                result["speed_mbs"] = 0.0
                
    except Exception as err:
        print(f"   [Error] Connection failed for {mirror['name']}: {err}")
        result["status"] = "Offline"

    return result

def run_global_benchmarks():
    global GLOBAL_STATE
    print("--> Starting global mirrors benchmark execution sync...")
    
    updated_metrics = []
    
    with httpx.Client(follow_redirects=True, verify=False) as client:
        for mirror in MIRRORS_TO_CHECK:
            print(f"  Testing mirror entity: {mirror['name']} ({mirror['url']})")
            try:
                res = test_single_mirror(client, mirror)
                print(f"    Result -> Status: {res['status']}, Latency: {res['latency_ms']}ms, Speed: {res['speed_mbs']}MB/s")
                updated_metrics.append(res)
            except Exception as e:
                print(f"  Critical exception running {mirror['name']}: {e}")
                updated_metrics.append({
                    "name": mirror["name"],
                    "url": mirror["url"],
                    "type": mirror["type"],
                    "status": "Offline",
                    "latency_ms": 0.0,
                    "speed_mbs": 0.0,
                    "last_checked": time.strftime("%Y-%m-%d %H:%M:%S")
                })
        
        GLOBAL_STATE["results"] = updated_metrics
        print(f"--> Benchmark run completed. Saved {len(GLOBAL_STATE['results'])} entries to global state.")
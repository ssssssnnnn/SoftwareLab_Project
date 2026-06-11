import pytest
from fastapi.testclient import TestClient

# Adjust imports based on your execution path. 
# Running via `python -m pytest` from the root will resolve these correctly.
from main import app, calculate_summary
from benchmarker import GLOBAL_STATE

@pytest.fixture
def client():
    """Fixture to provide a clean FastAPI TestClient instance."""
    return TestClient(app)

@pytest.fixture(autouse=True)
def clear_global_state():
    """Fixture to automatically reset GLOBAL_STATE before and after each test."""
    GLOBAL_STATE["results"] = []
    yield
    GLOBAL_STATE["results"] = []


# ==============================================================================
# 1. UNIT TESTS FOR PURE LOGIC (calculate_summary)
# ==============================================================================

def test_calculate_summary_with_mixed_mirrors():
    """Verify that calculations work perfectly under normal conditions with mixed states."""
    GLOBAL_STATE["results"] = [
        {"name": "Mirror A", "url": "http://a.com", "type": "NPM", "status": "Online", "latency_ms": 20.0, "speed_mbs": 5.5},
        {"name": "Mirror B", "url": "http://b.com", "type": "NPM", "status": "Online", "latency_ms": 40.0, "speed_mbs": 12.0},  # Fastest
        {"name": "Mirror C", "url": "http://c.com", "type": "PyPI", "status": "Offline", "latency_ms": 0.0, "speed_mbs": 0.0},
    ]

    data = calculate_summary()
    summary = data["summary"]

    assert summary["total_mirrors"] == 3
    assert summary["online_count"] == 2
    assert summary["fastest_mirror_name"] == "Mirror B"
    assert summary["fastest_mirror_url"] == "http://b.com"
    assert summary["fastest_mirror_type"] == "NPM"
    assert summary["average_latency_ms"] == 30.0  # (20 + 40) / 2


def test_calculate_summary_all_offline_edge_case():
    """Critical test: Ensure no ZeroDivisionError occurs and schema falls back gracefully when all mirrors are offline."""
    GLOBAL_STATE["results"] = [
        {"name": "Mirror A", "url": "http://a.com", "type": "NPM", "status": "Offline", "latency_ms": 0.0, "speed_mbs": 0.0},
        {"name": "Mirror B", "url": "http://b.com", "type": "PyPI", "status": "Offline", "latency_ms": 0.0, "speed_mbs": 0.0},
    ]

    # This execution would raise a ZeroDivisionError if not safely handled
    data = calculate_summary()
    summary = data["summary"]

    assert summary["total_mirrors"] == 2
    assert summary["online_count"] == 0
    assert summary["fastest_mirror_name"] == "N/A"
    assert summary["fastest_mirror_url"] == ""
    assert summary["fastest_mirror_type"] == ""
    assert summary["average_latency_ms"] == 0.0


# ==============================================================================
# 2. API INTEGRATION TESTS (JSON Format & Schema Validation)
# ==============================================================================

def test_get_metrics_json_schema_contract(client):
    """Verify HTTP GET /api/metrics returns a 200 and matches the strict expected JSON schema contract."""
    # Seed mock data into global state to test endpoint output structure
    GLOBAL_STATE["results"] = [
        {"name": "Test Mirror", "url": "http://test.com", "type": "PyPI", "status": "Online", "latency_ms": 15.5, "speed_mbs": 8.2, "last_checked": "today"}
    ]

    response = client.get("/api/metrics")
    print("RESPOSE ISSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS", response.json())
    
    assert response.status_code == 200
    
    json_data = response.json()
    
    # Assert top-level keys exist
    assert "summary" in json_data
    assert "mirrors" in json_data
    
    # Assert specific structure of the summary block
    summary = json_data["summary"]
    expected_summary_keys = {
        "total_mirrors", "online_count", "fastest_mirror_name", 
        "fastest_mirror_url", "fastest_mirror_type", "average_latency_ms"
    }
    assert expected_summary_keys.issubset(summary.keys())
    assert isinstance(summary["total_mirrors"], int)
    assert isinstance(summary["average_latency_ms"], float)

    # Assert specific structure of individual mirror elements
    mirrors = json_data["mirrors"]
    assert isinstance(mirrors, list)
    assert len(mirrors) == 1
    
    first_mirror = mirrors[0]
    expected_mirror_keys = {"name", "url", "type", "status", "latency_ms", "speed_mbs", "last_checked"}
    assert expected_mirror_keys.issubset(first_mirror.keys())
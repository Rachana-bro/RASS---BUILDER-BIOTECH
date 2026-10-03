from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_prepare_analysis_demo():
    res = client.post(
        "/api/v1/analysis/prepare",
        json={
            "file_path": "data/demo/sample.fastq",
            "max_reads": 1000,
            "min_quality": 20.0,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "prepared"
    assert data["input"]["processed_reads"] == 5
    assert data["filtering"]["passed_reads"] == 5
    assert len(data["sequences"]) == 5
    first_seq = data["sequences"][0]
    assert first_seq["read_id"] == "READ_001"
    assert first_seq["sequence"] == "ACGTACGTACGTACGTACGT"
    assert first_seq["tokens"] == [1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4]
    assert first_seq["length"] == 20
    assert data["model"]["status"] == "model_not_loaded"
    assert data["model"]["model_name"] == "RASS-DNA-Transformer"


def test_prepare_analysis_file_not_found():
    res = client.post(
        "/api/v1/analysis/prepare",
        json={
            "file_path": "non_existent_file.fastq",
            "max_reads": 100,
            "min_quality": 20.0,
        },
    )
    assert res.status_code == 400

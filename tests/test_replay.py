from fastapi.testclient import TestClient

from app.buffer import _dropped_seqs, get_buffer
from app.main import app

client = TestClient(app)

def test_replay_missing_range():
    # Insert some dummy data into the buffer
    buf = get_buffer("AAPL")
    buf.clear()
    _dropped_seqs["AAPL"] = 0
    
    buf.append({"seq": 100, "symbol": "AAPL", "price": 150.0})
    buf.append({"seq": 101, "symbol": "AAPL", "price": 150.1})
    buf.append({"seq": 102, "symbol": "AAPL", "price": 150.2})
    
    response = client.get("/replay/AAPL?from_seq=100")
    assert response.status_code == 200
    data = response.json()
    assert len(data["ticks"]) == 2
    assert data["ticks"][0]["seq"] == 101
    assert data["ticks"][1]["seq"] == 102

def test_replay_too_old():
    # Simulate a buffer where oldest dropped was 500
    buf = get_buffer("AAPL")
    buf.clear()
    _dropped_seqs["AAPL"] = 500
    buf.append({"seq": 501, "symbol": "AAPL", "price": 150.0})
    
    response = client.get("/replay/AAPL?from_seq=100")
    assert response.status_code == 416
    assert "too old" in response.json()["detail"]

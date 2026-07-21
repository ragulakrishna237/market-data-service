import json
import pytest
from fastapi.testclient import TestClient
from websockets.exceptions import ConnectionClosed

from app.main import app
from app.config import config

client = TestClient(app)

def test_stream_seq_increasing():
    # Make sure we get a few ticks
    with client.websocket_connect("/ws/stream") as websocket:
        last_seq = -1
        ticks = 0
        while ticks < 3:
            data = websocket.receive_text()
            msg = json.loads(data)
            assert "seq" in msg
            assert msg["seq"] > last_seq
            last_seq = msg["seq"]
            ticks += 1

def test_stream_heartbeat_idle():
    # Set interval large so we don't get regular ticks, and short heartbeat
    config.tick_interval_min = 2.0
    config.tick_interval_max = 2.0
    config.heartbeat_interval_s = 0.5
    
    with client.websocket_connect("/ws/stream") as websocket:
        # First message might be a tick or heartbeat
        data = websocket.receive_text()
        msg = json.loads(data)
        
        # Wait for a heartbeat
        got_heartbeat = False
        for _ in range(5):
            data = websocket.receive_text()
            msg = json.loads(data)
            if msg.get("type") == "heartbeat":
                got_heartbeat = True
                break
                
        assert got_heartbeat, "Did not receive a heartbeat during idle"

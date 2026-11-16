import json


def test_stream_seq_increasing(client):
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


def test_stream_heartbeat_idle(client):
    from app.config import config

    config.tick_interval_min = 2.0
    config.tick_interval_max = 2.0
    config.heartbeat_interval_s = 0.2

    with client.websocket_connect("/ws/stream") as websocket:
        got_heartbeat = False
        for _ in range(8):
            msg = json.loads(websocket.receive_text())
            if msg.get("type") == "heartbeat":
                got_heartbeat = True
                break

        assert got_heartbeat, "Did not receive a heartbeat during idle"

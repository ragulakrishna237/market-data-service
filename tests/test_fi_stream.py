import json

from app.fi_quality import enrich_security_master, validate_fi_message
from app.fi_refdata import FI_INSTRUMENTS, FI_REF_DATA
from app.refdata import SYMBOLS


def test_equity_refdata_unchanged(client):
    assert "AAPL" in SYMBOLS
    assert "AAPL" not in FI_REF_DATA
    response = client.get("/refdata")
    assert response.status_code == 200
    assert "AAPL" in response.json()
    assert "UST_10Y" not in response.json()


def test_fi_refdata_and_snapshot(client):
    response = client.get("/fi/refdata")
    assert response.status_code == 200
    body = response.json()
    assert "UST_10Y" in body
    assert body["USD_IRS_10Y"]["asset_class"] == "swap"
    snap = client.get("/fi/snapshot/UST_10Y")
    assert snap.status_code == 200
    data = snap.json()
    assert data["instrument_id"] == "UST_10Y"
    assert "seq" in data
    assert data["reference_data"]["cusip"]


def test_ws_fi_seq_increasing_separate_from_equity(client):
    with client.websocket_connect("/ws/fi") as websocket:
        last_seq = -1
        ticks = 0
        while ticks < 3:
            msg = json.loads(websocket.receive_text())
            if msg.get("type") != "tick":
                continue
            assert msg["instrument_id"] in FI_INSTRUMENTS
            assert "yield" in msg
            assert msg["seq"] > last_seq
            last_seq = msg["seq"]
            ticks += 1


def test_quality_and_security_master_enrichment():
    good = {
        "type": "tick",
        "instrument_id": "UST_10Y",
        "cusip": "91282CJL6",
        "isin": "US91282CJL64",
        "asset_class": "treasury",
        "price": 98.5,
        "yield": 0.043,
        "seq": 1,
        "ts_event": "2099-01-01T00:00:00+00:00",
    }
    assert validate_fi_message(good) == []
    bad = {**good, "price": -1, "yield": 2.5, "seq": 0}
    issues = validate_fi_message(bad, last_seq=1)
    assert "non_positive_price" in issues
    assert "yield_out_of_range" in issues
    assert "sequence_not_increasing" in issues
    master = {}
    enrich_security_master(good, master)
    assert master["UST_10Y"]["cusip"] == "91282CJL6"
    assert master["UST_10Y"]["last_price"] == 98.5

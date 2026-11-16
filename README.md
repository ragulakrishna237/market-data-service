# market-data-service

## Fixed Income Market Data Simulation

Additive FI path. Equity `/ws/stream`, `/snapshot/{symbol}`, and `refdata.yaml` are unchanged.

- `fi_refdata.yaml` — synthetic Treasuries, agency MBS, IRS, caps/floors, swaptions (Security Master fields: CUSIP, ISIN, coupon, maturity).
- `WS /ws/fi` — sequenced FI ticks (`seq`, `ts_event`, `price`, `yield`) on a separate bus so equity clients do not see them.
- `GET /fi/refdata` and `GET /fi/snapshot/{instrument_id}`.
- `examples/fi_consumer.py` — post-receipt pattern: validate sequence/price/yield/staleness, then upsert an in-memory Security Master. Vendor ticks are not the master.

```bash
websocat ws://localhost:8000/ws/fi
python examples/fi_consumer.py
```


[![CI](https://github.com/your-org/market-data-service/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/market-data-service/actions)

## Role in the Architecture
This service acts as **"the vendor"** — a mock external market-data provider for the quant-platform ecosystem. It represents a third-party data feed that the platform consumes but does not control.

It is **stateless by design** and runs in-memory. It can be killed and restarted freely.

## Message Schema

Ticks emitted over WebSocket follow this structure:
```json
{
  "type": "tick",
  "symbol": "AAPL",
  "price": 150.25,
  "size": 100,
  "seq": 1234,
  "ts_event": "2026-07-20T10:00:00.000Z"
}
```

Heartbeats are sent when the market is idle (e.g., every 2s):
```json
{
  "type": "heartbeat",
  "seq": 1234,
  "ts": "2026-07-20T10:00:02.000Z"
}
```

## Running Locally

### Virtual Environment (Windows)
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Virtual Environment (Unix/macOS)
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Example Usage

**Snapshot via curl:**
```bash
curl http://localhost:8000/snapshot/AAPL
```

**Stream via websocat:**
```bash
websocat ws://localhost:8000/ws/stream
```

## Features
- `GET /snapshot/{symbol}`: Returns the last price, reference data, and sequence number for a symbol.
- `WS /ws/stream`: WebSocket endpoint streaming ticks and heartbeats.
- `GET /replay/{symbol}?from_seq=N`: Replay missing ticks from a ring buffer.
- `GET /health`: Health check endpoint.
- `GET /metrics`: Prometheus metrics endpoint.

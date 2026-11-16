import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest

from app.refdata import REF_DATA, SYMBOLS
from app.buffer import replay_from, get_global_last_seq
from app.generator import start_generator, subscribe, unsubscribe, get_current_price
from app.fi_refdata import FI_REF_DATA, FI_INSTRUMENTS
from app.fi_generator import get_fi_snapshot, start_fi_generator, subscribe_fi, unsubscribe_fi

# Metrics
REQUEST_COUNT = Counter("http_requests_total", "Total HTTP Requests", ["method", "endpoint", "http_status"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "HTTP Request Latency", ["method", "endpoint"])
WS_CONNECTIONS = Counter("ws_connections_total", "Total WebSocket Connections")
WS_MESSAGES_SENT = Counter("ws_messages_sent_total", "Total WebSocket Messages Sent")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the tick generator on startup
    gen_task = asyncio.create_task(start_generator())
    fi_task = asyncio.create_task(start_fi_generator())
    yield
    # Clean up on shutdown
    gen_task.cancel()
    fi_task.cancel()

app = FastAPI(title="Market Data Service", lifespan=lifespan)

class SnapshotResponse(BaseModel):
    symbol: str
    last_price: float
    timestamp: str
    last_seq: int
    reference_data: Dict[str, Any]

@app.middleware("http")
async def monitor_requests(request, call_next):
    method = request.method
    endpoint = request.url.path
    
    if endpoint == "/metrics":
        return await call_next(request)
        
    with REQUEST_LATENCY.labels(method=method, endpoint=endpoint).time():
        response = await call_next(request)
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, http_status=response.status_code).inc()
        return response

@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    return generate_latest()

@app.get("/snapshot/{symbol}", response_model=SnapshotResponse)
async def get_snapshot(symbol: str):
    symbol = symbol.upper()
    if symbol not in SYMBOLS:
        raise HTTPException(status_code=404, detail="Symbol not found")
        
    current_price = get_current_price(symbol)
    
    return SnapshotResponse(
        symbol=symbol,
        last_price=round(current_price, 4),
        timestamp=datetime.now(timezone.utc).isoformat(),
        last_seq=get_global_last_seq(),
        reference_data=REF_DATA[symbol]
    )

@app.get("/replay/{symbol}")
async def replay(symbol: str, from_seq: int):
    symbol = symbol.upper()
    if symbol not in SYMBOLS:
        raise HTTPException(status_code=404, detail="Symbol not found")
        
    try:
        ticks = replay_from(symbol, from_seq)
        return {"symbol": symbol, "ticks": ticks}
    except ValueError as e:
        raise HTTPException(status_code=416, detail=str(e))

@app.get("/refdata")
async def get_refdata():
    return REF_DATA

@app.get("/fi/refdata")
async def get_fi_refdata():
    return FI_REF_DATA

@app.get("/fi/snapshot/{instrument_id}")
async def get_fi_snapshot_endpoint(instrument_id: str):
    instrument_id = instrument_id.upper()
    if instrument_id not in FI_INSTRUMENTS:
        raise HTTPException(status_code=404, detail="Instrument not found")
    return get_fi_snapshot(instrument_id)

@app.websocket("/ws/fi")
async def fi_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    WS_CONNECTIONS.inc()
    queue = asyncio.Queue()
    subscribe_fi(queue)
    try:
        while True:
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=1.0)
                await websocket.send_text(json.dumps(msg))
                WS_MESSAGES_SENT.inc()
            except asyncio.TimeoutError:
                continue
    except WebSocketDisconnect:
        print("FI client disconnected")
    except Exception as e:
        print(f"FI WebSocket error: {e}")
    finally:
        unsubscribe_fi(queue)

@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    WS_CONNECTIONS.inc()
    
    queue = asyncio.Queue()
    subscribe(queue)
    
    from app.config import config
    from app.faults import FAULTS_INJECTED
    start_time = asyncio.get_event_loop().time()
    
    try:
        while True:
            if config.fault_disconnect_after_s > 0:
                now = asyncio.get_event_loop().time()
                if now - start_time >= config.fault_disconnect_after_s:
                    FAULTS_INJECTED.labels(type="disconnect").inc()
                    await websocket.close(code=1008)
                    break
                    
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=1.0)
                await websocket.send_text(json.dumps(msg))
                WS_MESSAGES_SENT.inc()
            except asyncio.TimeoutError:
                continue
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        unsubscribe(queue)

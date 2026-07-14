import asyncio
import json
import random
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest

app = FastAPI(title="Market Data Service")

# Metrics
REQUEST_COUNT = Counter("http_requests_total", "Total HTTP Requests", ["method", "endpoint", "http_status"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "HTTP Request Latency", ["method", "endpoint"])
WS_CONNECTIONS = Counter("ws_connections_total", "Total WebSocket Connections")
WS_MESSAGES_SENT = Counter("ws_messages_sent_total", "Total WebSocket Messages Sent")

class SnapshotResponse(BaseModel):
    symbol: str
    last_price: float
    timestamp: str
    reference_data: Dict[str, Any]

# Mock data
MOCK_PRICES = {
    "AAPL": 150.0,
    "GOOGL": 2800.0,
    "MSFT": 300.0,
    "TSLA": 700.0,
}

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
    base_price = MOCK_PRICES.get(symbol, 100.0)
    current_price = base_price * (1 + random.uniform(-0.02, 0.02))
    
    return SnapshotResponse(
        symbol=symbol,
        last_price=round(current_price, 2),
        timestamp=datetime.now(timezone.utc).isoformat(),
        reference_data={
            "exchange": "NASDAQ",
            "currency": "USD",
            "tick_size": 0.01
        }
    )

@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    WS_CONNECTIONS.inc()
    
    sequence_number = 0
    symbols = list(MOCK_PRICES.keys())
    
    try:
        while True:
            sequence_number += 1
            symbol = random.choice(symbols)
            base_price = MOCK_PRICES[symbol]
            current_price = base_price * (1 + random.uniform(-0.01, 0.01))
            
            tick = {
                "sequence": sequence_number,
                "symbol": symbol,
                "price": round(current_price, 2),
                "size": random.randint(1, 100) * 10,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            await websocket.send_text(json.dumps(tick))
            WS_MESSAGES_SENT.inc()
            
            # Simulate tick interval
            await asyncio.sleep(random.uniform(0.1, 1.0))
            
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")

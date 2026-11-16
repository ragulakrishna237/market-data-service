import asyncio
import random
from datetime import datetime, timezone
from typing import Any

from app.buffer import add_tick
from app.config import config
from app.faults import FAULTS_INJECTED, apply_tick_faults
from app.refdata import REF_DATA, SYMBOLS

# We need a way to broadcast ticks to all WS connections
_subscribers = []

def subscribe(queue: asyncio.Queue):
    _subscribers.append(queue)

def unsubscribe(queue: asyncio.Queue):
    if queue in _subscribers:
        _subscribers.remove(queue)

async def _broadcast(msg: dict[str, Any]):
    for q in _subscribers:
        try:
            q.put_nowait(msg)
        except asyncio.QueueFull:
            pass

_current_prices = {sym: data["base_price"] for sym, data in REF_DATA.items()}
_global_seq = 0
_last_tick_time = 0
_start_time = 0

async def start_generator():
    global _global_seq, _last_tick_time, _start_time
    _start_time = asyncio.get_event_loop().time()
    
    # Heartbeat loop
    asyncio.create_task(_heartbeat_loop())
    
    while True:
        now = asyncio.get_event_loop().time()
        
        # FAULT_STALL_AFTER_S
        if config.fault_stall_after_s > 0 and now - _start_time >= config.fault_stall_after_s:
            FAULTS_INJECTED.labels(type="stall").inc()
            await asyncio.sleep(1.0)
            continue
            
        symbol = random.choice(SYMBOLS)
        REF_DATA[symbol]["base_price"]
        tick_size = REF_DATA[symbol]["tick_size"]
        
        # Random walk
        change = random.choice([-tick_size, tick_size, 0])
        _current_prices[symbol] = max(tick_size, _current_prices[symbol] + change)
        
        _global_seq += 1
        
        tick = {
            "type": "tick",
            "symbol": symbol,
            "price": round(_current_prices[symbol], 4),
            "size": random.randint(1, 100) * 10,
            "seq": _global_seq,
            "ts_event": datetime.now(timezone.utc).isoformat()
        }
        
        # Apply fault injection
        tick, seq_increment = apply_tick_faults(tick, _global_seq)
        if seq_increment > 0:
            _global_seq += seq_increment
            tick["seq"] = _global_seq
        
        add_tick(symbol, tick)
        _last_tick_time = asyncio.get_event_loop().time()
        
        await _broadcast(tick)
        
        interval = random.uniform(config.tick_interval_min, config.tick_interval_max)
        await asyncio.sleep(interval)

async def _heartbeat_loop():
    while True:
        await asyncio.sleep(config.heartbeat_interval_s)
        now = asyncio.get_event_loop().time()
        
        # FAULT_STALL_AFTER_S stops heartbeats too
        if config.fault_stall_after_s > 0 and now - _start_time >= config.fault_stall_after_s:
            continue
            
        if now - _last_tick_time >= config.heartbeat_interval_s:
            hb = {
                "type": "heartbeat",
                "seq": _global_seq,
                "ts": datetime.now(timezone.utc).isoformat()
            }
            await _broadcast(hb)

def get_current_price(symbol: str) -> float:
    return _current_prices.get(symbol, REF_DATA.get(symbol, {}).get("base_price", 0.0))

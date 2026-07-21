import random
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Tuple

from prometheus_client import Counter

from app.config import config

FAULTS_INJECTED = Counter("faults_injected_total", "Total faults injected", ["type"])

_ticks_since_start = 0

def apply_tick_faults(tick: Dict[str, Any], global_seq: int) -> Tuple[Dict[str, Any], int]:
    global _ticks_since_start
    _ticks_since_start += 1
    
    modified_tick = tick.copy()
    seq_increment = 0
    
    # FAULT_GAP_EVERY_N: silently skip a sequence number
    if config.fault_gap_every_n > 0 and _ticks_since_start % config.fault_gap_every_n == 0:
        FAULTS_INJECTED.labels(type="gap").inc()
        seq_increment = 1
    
    # FAULT_BAD_TICK_RATE: corrupt tick
    if config.fault_bad_tick_rate > 0 and random.random() < config.fault_bad_tick_rate:
        FAULTS_INJECTED.labels(type="bad_tick").inc()
        if random.random() < 0.5:
            modified_tick["price"] = -1.0
        else:
            modified_tick["price"] = round(modified_tick["price"] * 1.5, 4)
            
    # FAULT_STALE_TS_RATE: tick with ts_event 30s in the past
    if config.fault_stale_ts_rate > 0 and random.random() < config.fault_stale_ts_rate:
        FAULTS_INJECTED.labels(type="stale_ts").inc()
        past_time = datetime.now(timezone.utc) - timedelta(seconds=30)
        modified_tick["ts_event"] = past_time.isoformat()
        
    return modified_tick, seq_increment

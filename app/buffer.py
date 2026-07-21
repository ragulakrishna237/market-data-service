from collections import deque
from typing import Dict, List, Any

# Map symbol -> deque
_buffers: Dict[str, deque] = {}
# Map symbol -> max seq that was dropped
_dropped_seqs: Dict[str, int] = {}

# Global seq track
_global_last_seq = 0

def get_buffer(symbol: str) -> deque:
    if symbol not in _buffers:
        _buffers[symbol] = deque(maxlen=1000)
        _dropped_seqs[symbol] = 0
    return _buffers[symbol]

def add_tick(symbol: str, tick: Dict[str, Any]):
    global _global_last_seq
    buf = get_buffer(symbol)
    if len(buf) == buf.maxlen:
        oldest = buf[0]
        _dropped_seqs[symbol] = oldest["seq"]
    buf.append(tick)
    if tick["seq"] > _global_last_seq:
        _global_last_seq = tick["seq"]

def replay_from(symbol: str, from_seq: int) -> List[Dict[str, Any]]:
    buf = get_buffer(symbol)
    dropped_seq = _dropped_seqs.get(symbol, 0)
    
    if from_seq <= dropped_seq and dropped_seq > 0:
        raise ValueError("from_seq is too old, outside of buffer window")
        
    result = []
    for tick in buf:
        if tick["seq"] > from_seq:
            result.append(tick)
    return result

def get_global_last_seq() -> int:
    return _global_last_seq

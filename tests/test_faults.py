import pytest

from app.config import config
from app.faults import apply_tick_faults


@pytest.fixture(autouse=True)
def reset_faults():
    # Reset config
    config.fault_gap_every_n = 0
    config.fault_bad_tick_rate = 0.0
    config.fault_stale_ts_rate = 0.0
    config.fault_disconnect_after_s = 0
    config.fault_stall_after_s = 0
    
    import app.faults
    app.faults._ticks_since_start = 0

def test_gap_fault():
    config.fault_gap_every_n = 3
    
    base_tick = {"type": "tick", "price": 100.0}
    
    _tick1, inc1 = apply_tick_faults(base_tick.copy(), 100)
    assert inc1 == 0
    
    _tick2, inc2 = apply_tick_faults(base_tick.copy(), 101)
    assert inc2 == 0
    
    _tick3, inc3 = apply_tick_faults(base_tick.copy(), 102)
    assert inc3 == 1  # Gap applied; generator adds this to seq.

def test_bad_tick_fault():
    config.fault_bad_tick_rate = 1.0  # Always bad
    
    base_tick = {"type": "tick", "price": 100.0}
    tick, inc = apply_tick_faults(base_tick.copy(), 100)
    
    assert inc == 0
    assert tick["price"] <= 0.0 or tick["price"] >= 150.0

def test_stale_ts_fault():
    config.fault_stale_ts_rate = 1.0  # Always stale
    
    base_tick = {"type": "tick", "price": 100.0}
    tick, _inc = apply_tick_faults(base_tick.copy(), 100)
    
    assert "ts_event" in tick

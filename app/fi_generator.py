"""Synthetic FI ticks on a separate bus from the equity generator."""

import asyncio
import random
from datetime import datetime, timezone
from typing import Any

from app.buffer import add_tick
from app.config import config
from app.fi_refdata import FI_INSTRUMENTS, FI_REF_DATA

_fi_subscribers: list[asyncio.Queue] = []
_fi_seq = 0
_fi_prices = {sym: data["base_price"] for sym, data in FI_REF_DATA.items()}
_fi_yields = {sym: data["base_yield"] for sym, data in FI_REF_DATA.items()}


def subscribe_fi(queue: asyncio.Queue) -> None:
    _fi_subscribers.append(queue)


def unsubscribe_fi(queue: asyncio.Queue) -> None:
    if queue in _fi_subscribers:
        _fi_subscribers.remove(queue)


async def _broadcast(msg: dict[str, Any]) -> None:
    for queue in _fi_subscribers:
        try:
            queue.put_nowait(msg)
        except asyncio.QueueFull:
            pass


def get_fi_seq() -> int:
    return _fi_seq


def get_fi_snapshot(instrument_id: str) -> dict[str, Any]:
    ref = FI_REF_DATA[instrument_id]
    return {
        "type": "snapshot",
        "instrument_id": instrument_id,
        "cusip": ref["cusip"],
        "isin": ref["isin"],
        "asset_class": ref["asset_class"],
        "price": round(_fi_prices[instrument_id], 6),
        "yield": round(_fi_yields[instrument_id], 6),
        "seq": _fi_seq,
        "ts_event": datetime.now(timezone.utc).isoformat(),
        "reference_data": ref,
    }


async def start_fi_generator() -> None:
    global _fi_seq
    while True:
        instrument_id = random.choice(FI_INSTRUMENTS)
        ref = FI_REF_DATA[instrument_id]
        tick_size = ref["tick_size"]
        change = random.choice([-tick_size, tick_size, 0])
        _fi_prices[instrument_id] = max(tick_size, _fi_prices[instrument_id] + change)
        _fi_yields[instrument_id] = max(0.0001, _fi_yields[instrument_id] + random.choice([-0.0001, 0.0, 0.0001]))
        _fi_seq += 1
        tick = {
            "type": "tick",
            "asset_class": ref["asset_class"],
            "instrument_id": instrument_id,
            "cusip": ref["cusip"],
            "isin": ref["isin"],
            "price": round(_fi_prices[instrument_id], 6),
            "yield": round(_fi_yields[instrument_id], 6),
            "size": random.randint(1, 50) * 100000,
            "seq": _fi_seq,
            "ts_event": datetime.now(timezone.utc).isoformat(),
        }
        add_tick(instrument_id, tick)
        await _broadcast(tick)
        interval = random.uniform(config.tick_interval_min, config.tick_interval_max)
        await asyncio.sleep(interval)

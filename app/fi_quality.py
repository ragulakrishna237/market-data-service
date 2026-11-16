"""Post-receipt quality checks and Security Master enrichment."""

from datetime import datetime, timezone
from typing import Any

from app.fi_refdata import FI_REF_DATA


def validate_fi_message(msg: dict[str, Any], last_seq: int | None = None) -> list[str]:
    issues: list[str] = []
    msg_type = msg.get("type")
    if msg_type not in {"tick", "snapshot", "heartbeat"}:
        issues.append("unknown_type")
        return issues
    if msg_type == "heartbeat":
        if "seq" not in msg:
            issues.append("missing_seq")
        return issues
    for field in ("instrument_id", "seq", "ts_event"):
        if field not in msg:
            issues.append(f"missing_{field}")
    instrument_id = msg.get("instrument_id")
    if instrument_id and instrument_id not in FI_REF_DATA:
        issues.append("unknown_instrument")
    price = msg.get("price")
    yld = msg.get("yield")
    if price is not None and float(price) <= 0:
        issues.append("non_positive_price")
    if yld is not None and not (0 < float(yld) < 1):
        issues.append("yield_out_of_range")
    if last_seq is not None and msg.get("seq") is not None and int(msg["seq"]) <= last_seq:
        issues.append("sequence_not_increasing")
    try:
        ts = datetime.fromisoformat(str(msg.get("ts_event", "")).replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        lag = (datetime.now(timezone.utc) - ts).total_seconds()
        if lag > 30:
            issues.append("stale_ts")
    except ValueError:
        issues.append("bad_ts_event")
    return issues


def enrich_security_master(msg: dict[str, Any], master: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    if msg.get("type") not in {"tick", "snapshot"}:
        return master
    instrument_id = msg["instrument_id"]
    ref = FI_REF_DATA.get(instrument_id, {})
    previous = master.get(instrument_id, {})
    master[instrument_id] = {
        **ref,
        **previous,
        "instrument_id": instrument_id,
        "last_price": msg.get("price"),
        "last_yield": msg.get("yield"),
        "last_seq": msg.get("seq"),
        "last_ts_event": msg.get("ts_event"),
        "cusip": msg.get("cusip") or ref.get("cusip") or previous.get("cusip"),
        "isin": msg.get("isin") or ref.get("isin") or previous.get("isin"),
        "asset_class": msg.get("asset_class") or ref.get("asset_class"),
    }
    return master

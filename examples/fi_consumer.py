"""Connect to /ws/fi, validate ticks, enrich an in-memory Security Master.

Usage (service already running on :8000):

    python examples/fi_consumer.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.fi_quality import enrich_security_master, validate_fi_message


async def consume(url: str = "ws://127.0.0.1:8000/ws/fi", max_messages: int = 20) -> dict:
    import websockets

    master: dict = {}
    last_seq = None
    issues_total = 0
    async with websockets.connect(url) as ws:
        for _ in range(max_messages):
            raw = await ws.recv()
            msg = json.loads(raw)
            issues = validate_fi_message(msg, last_seq=last_seq)
            if issues:
                issues_total += 1
                print({"rejected": issues, "msg": msg})
                continue
            if msg.get("type") in {"tick", "snapshot"}:
                last_seq = msg["seq"]
                enrich_security_master(msg, master)
                print(
                    {
                        "instrument_id": msg["instrument_id"],
                        "price": msg["price"],
                        "yield": msg["yield"],
                        "seq": msg["seq"],
                        "master_size": len(master),
                    }
                )
    out_path = ROOT / "examples" / "fi_security_master.json"
    out_path.write_text(json.dumps(master, indent=2), encoding="utf-8")
    print({"wrote": str(out_path), "issues_total": issues_total})
    return master


def main() -> int:
    asyncio.run(consume())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

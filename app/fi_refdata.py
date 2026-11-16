from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

_FI_PATH = Path(__file__).resolve().parents[1] / "fi_refdata.yaml"


def load_fi_refdata(path: str | None = None) -> Dict[str, Dict[str, Any]]:
    with open(path or _FI_PATH, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data or {}


FI_REF_DATA = load_fi_refdata()
FI_INSTRUMENTS = list(FI_REF_DATA.keys())

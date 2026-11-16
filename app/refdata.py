from typing import Any

import yaml


def load_refdata(path: str = "refdata.yaml") -> dict[str, dict[str, Any]]:
    with open(path, "r") as f:
        return yaml.safe_load(f)

REF_DATA = load_refdata()
SYMBOLS = list(REF_DATA.keys())

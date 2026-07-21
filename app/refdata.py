import yaml
from typing import Dict, Any

def load_refdata(path: str = "refdata.yaml") -> Dict[str, Dict[str, Any]]:
    with open(path, "r") as f:
        return yaml.safe_load(f)

REF_DATA = load_refdata()
SYMBOLS = list(REF_DATA.keys())

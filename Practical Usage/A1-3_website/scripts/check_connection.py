"""Check the configured Codyssey connection without printing credentials."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from api.product_match import match_product  # noqa: E402
from scripts.dev import load_environment  # noqa: E402


if __name__ == "__main__":
    load_environment()
    status, body = match_product({"productName": "리본 파우치", "options": "분홍"})
    print(json.dumps({"status": status, **body}, ensure_ascii=False))
    raise SystemExit(0 if status == 200 else 1)

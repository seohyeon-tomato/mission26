"""Print a credential-free summary of the Codyssey response structure."""

import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from api.product_match import _chat_completion_url, _prompt_messages  # noqa: E402
from scripts.dev import load_environment  # noqa: E402


if __name__ == "__main__":
    load_environment()
    endpoint = _chat_completion_url(os.environ["CODYSSEY_BASE_URL"])
    payload = {
        "model": os.environ["CODYSSEY_MODEL"],
        "messages": _prompt_messages("리본 파우치", "분홍"),
        "max_tokens": 1000,
    }
    request = Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": "Bearer " + os.environ["CODYSSEY_API_KEY"],
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=12) as response:
            body = json.loads(response.read(65537).decode("utf-8"))
            choice = (body.get("choices") or [{}])[0]
            message = choice.get("message") or {}
            content = message.get("content")
            summary = {
                "http_status": response.status,
                "top_level_keys": sorted(body.keys()),
                "choice_keys": sorted(choice.keys()),
                "message_keys": sorted(message.keys()),
                "finish_reason": choice.get("finish_reason"),
                "content_type": type(content).__name__,
                "content_preview": content[:500] if isinstance(content, str) else content,
            }
            print(json.dumps(summary, ensure_ascii=False))
    except HTTPError as error:
        print(json.dumps({"http_status": error.code, "error": "provider rejected request"}))
        raise SystemExit(1)

import json
import socket
import sys
import unittest
from pathlib import Path
from urllib.error import HTTPError, URLError


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from api.product_match import MAX_PRODUCT_NAME_LENGTH, match_product  # noqa: E402


ENVIRONMENT = {
    "CODYSSEY_BASE_URL": "https://qa.example.codyssey/v1",
    "CODYSSEY_API_KEY": "test-key",
    "CODYSSEY_MODEL": "console-model-id",
}


class FakeResponse:
    def __init__(self, body: bytes):
        self.body = body

    def read(self, size: int) -> bytes:
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class ProductMatchTests(unittest.TestCase):
    def test_missing_configuration_returns_503_without_network_call(self):
        called = False

        def sender(request, timeout):
            nonlocal called
            called = True

        status, body = match_product({"productName": "가방"}, environment={}, request_sender=sender)

        self.assertEqual(status, 503)
        self.assertEqual(body["error"]["code"], "api_not_configured")
        self.assertFalse(called)

    def test_validation_rejects_empty_and_too_long_product_names(self):
        for product_name in ("   ", "a" * (MAX_PRODUCT_NAME_LENGTH + 1)):
            status, body = match_product({"productName": product_name}, environment=ENVIRONMENT)
            self.assertEqual(status, 400)
            self.assertEqual(body["error"]["code"], "invalid_input")

    def test_success_uses_single_v1_path_and_parses_fenced_json(self):
        observed = {}
        upstream = {"choices": [{"message": {"content": "```json\n{\"name\":\"빈티지 백\",\"options\":\"초록색\",\"searchQuery\":\"빈티지 초록 가방\"}\n```"}}]}

        def sender(request, timeout):
            observed["url"] = request.full_url
            observed["headers"] = dict(request.header_items())
            observed["payload"] = json.loads(request.data.decode("utf-8"))
            observed["timeout"] = timeout
            return FakeResponse(json.dumps(upstream).encode("utf-8"))

        status, body = match_product({"productName": "가방", "options": "초록"}, environment=ENVIRONMENT, request_sender=sender)

        self.assertEqual(status, 200)
        self.assertEqual(observed["url"], "https://qa.example.codyssey/v1/chat/completions")
        self.assertEqual(observed["headers"]["Authorization"], "Bearer test-key")
        self.assertEqual(observed["payload"]["model"], "console-model-id")
        self.assertEqual(observed["payload"]["max_tokens"], 1000)
        self.assertEqual(observed["payload"]["messages"][0]["role"], "system")
        self.assertEqual(body["candidate"]["searchQuery"], "빈티지 초록 가방")

    def test_base_url_without_v1_adds_the_version_path_once(self):
        observed = {}
        upstream = {"choices": [{"message": {"content": '{"name":"가방","options":"","searchQuery":"가방"}'}}]}

        def sender(request, timeout):
            observed["url"] = request.full_url
            return FakeResponse(json.dumps(upstream).encode("utf-8"))

        environment = {**ENVIRONMENT, "CODYSSEY_BASE_URL": "https://prod.example.codyssey/"}
        status, _ = match_product({"productName": "가방"}, environment=environment, request_sender=sender)

        self.assertEqual(status, 200)
        self.assertEqual(observed["url"], "https://prod.example.codyssey/v1/chat/completions")

    def test_malformed_upstream_response_is_safe(self):
        status, body = match_product(
            {"productName": "가방"},
            environment=ENVIRONMENT,
            request_sender=lambda request, timeout: FakeResponse(b'{"choices":[]}'),
        )

        self.assertEqual(status, 502)
        self.assertEqual(body["error"]["code"], "upstream_invalid_response")

    def test_upstream_http_error_does_not_expose_provider_message(self):
        def sender(request, timeout):
            raise HTTPError(request.full_url, 401, "provider secret detail", {}, None)

        status, body = match_product({"productName": "가방"}, environment=ENVIRONMENT, request_sender=sender)

        self.assertEqual(status, 502)
        self.assertEqual(body["error"]["code"], "upstream_rejected")
        self.assertNotIn("provider secret detail", body["error"]["message"])

    def test_timeout_is_safe(self):
        def sender(request, timeout):
            raise URLError(socket.timeout("network timeout"))

        status, body = match_product({"productName": "가방"}, environment=ENVIRONMENT, request_sender=sender)

        self.assertEqual(status, 504)
        self.assertEqual(body["error"]["code"], "upstream_timeout")


if __name__ == "__main__":
    unittest.main()

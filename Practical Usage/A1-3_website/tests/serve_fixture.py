"""Explicit browser test fixture. Never deployed; no provider requests made."""
import json
import sys
from pathlib import Path
from io import BytesIO
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.dev import LocalHandler, serve
import api.product_match as api

actual_match = api.match_product
calls = 0

def fake_sender(request, timeout):
    global calls
    calls += 1
    print(f'MOCK_API_CALLS={calls}', flush=True)
    product = json.loads(json.loads(request.data)['messages'][1]['content'])
    candidate = {'name': product['productName'], 'options': product['options'], 'searchQuery': (product['productName'] + ' ' + product['options']).strip()}
    return BytesIO(json.dumps({'choices': [{'message': {'content': json.dumps(candidate)}}]}).encode())


def fixture_match(payload):
    return actual_match(payload, environment={'CODYSSEY_BASE_URL': 'https://fixture.invalid', 'CODYSSEY_API_KEY': 'fixture-only', 'CODYSSEY_MODEL': 'fixture'}, request_sender=fake_sender)

api.match_product = fixture_match
class FixtureHandler(LocalHandler):
    fixture = True

if __name__ == '__main__':
    serve(8081, FixtureHandler)

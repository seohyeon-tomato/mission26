"""HTTP 전송만 대체하고 CLI부터 파일 저장까지 실제 함수를 연결한다."""
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import travel_planner as app


class TransportIntegrationTests(unittest.TestCase):
    def test_cli_to_files_with_http_boundary_mock(self):
        recommendation = {'recommended_city': '강릉', 'weather': '계절 경향', 'events': ['확인 필요 후보'], 'reason': '바다를 볼 수 있습니다. 산책하기 좋습니다.'}
        markdown = '# 리포트\n' + '\n'.join('## ' + h + '\n내용' for h in app.HEADINGS) + '\n오전 산책, 오후 관광, 저녁 식사\n'
        def candidate(text):
            return {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': text}]}}]}
        for empty in (False, True):
            with self.subTest(empty=empty), tempfile.TemporaryDirectory() as folder:
                documents = [] if empty else [{'place_name': '모의 식당', 'address_name': '모의 주소', 'x': '128.1', 'y': '37.1'}]
                responses = [candidate(json.dumps(recommendation)), {'documents': documents}, candidate(markdown)]
                streams = [io.BytesIO(json.dumps(r).encode()) for r in responses]
                with patch.object(app, 'BASE', Path(folder)), patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key-g', 'KAKAO_REST_API_KEY': 'test-key-k', 'GEMINI_MODEL': 'gemini-2.5-flash'}, clear=True), patch.object(app, 'urlopen', side_effect=streams) as http:
                    self.assertEqual(app.main(['-date', '2026-10-15']), 0)
                self.assertEqual(http.call_count, 3)
                first, second, third = [c.args[0] for c in http.call_args_list]
                self.assertEqual(first.method, 'POST')
                body = json.loads(first.data)
                self.assertEqual(body['generationConfig']['responseFormat']['text']['mimeType'], 'application/json')
                self.assertEqual(second.method, 'GET')
                self.assertEqual(parse_qs(urlparse(second.full_url).query)['query'], ['강릉 맛집'])
                self.assertEqual(third.method, 'POST')
                raw = json.loads(next(Path(folder).glob('results/*_raw.json')).read_text())
                report = next(Path(folder).glob('results/*_travel_plan.md')).read_text()
                self.assertEqual(raw['recommendation'], recommendation)
                self.assertEqual(len(raw['places']), 0 if empty else 1)
                self.assertIn('데이터 없음' if empty else '모의 식당', report)
                self.assertNotIn('test-key', report)

    def test_recommendation_rejects_missing_and_wrong_types(self):
        for value in ({}, [], {'recommended_city': 1, 'weather': 'x', 'events': [], 'reason': 'x'}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                app.validate_recommendation(json.dumps(value))

    def test_blocked_or_truncated_gemini_is_an_error(self):
        for value in ({'promptFeedback': {'blockReason': 'SAFETY'}}, {'candidates': [{'finishReason': 'MAX_TOKENS'}]}):
            with self.subTest(value=value), patch.object(app, 'request_json', return_value=value), self.assertRaises(app.APIError):
                app.gemini('prompt', 'fake', 'model')

    def test_default_model_uses_current_recommended_flash(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(app, 'BASE', Path(folder)), patch.dict(os.environ, {'GEMINI_API_KEY': 'fake-g', 'KAKAO_REST_API_KEY': 'fake-k'}, clear=True), patch.object(app, 'recommend', side_effect=app.APIError('HTTP_ERROR', 'test')) as recommend:
            self.assertEqual(app.main(['-date', '2026-10-15']), 1)
        self.assertEqual(recommend.call_args.args[2], 'gemini-3.8-flash')


if __name__ == '__main__':
    unittest.main()

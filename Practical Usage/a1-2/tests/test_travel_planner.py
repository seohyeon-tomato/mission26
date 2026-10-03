"""travel_planner의 필수 미션 동작을 실제 API 호출 없이 검증한다."""

import importlib.util
import io
import json
import os
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError


MODULE_PATH = Path(__file__).resolve().parents[1] / "travel_planner.py"
SPEC = importlib.util.spec_from_file_location("travel_planner", MODULE_PATH)
travel_planner = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(travel_planner)


VALID_RECOMMENDATION = {
    "recommended_city": "강릉",
    "weather": "선선한 시기의 일반적인 날씨",
    "events": ["일정 확인이 필요한 지역 행사"],
    "reason": "바다와 지역 문화를 함께 즐길 수 있습니다. 실제 일정은 확인이 필요합니다.",
}

VALID_REPORT = """# 여행 리포트
## 추천 지역
강릉
## 추천 이유
바다와 지역 문화
## 날씨 요약
일반적인 날씨 경향
## 행사/축제
일정 확인이 필요한 행사 후보
## 맛집 추천
- 모델이 만든 가게는 제거되어야 함
## 1일 일정 제안
오전 산책, 오후 전시, 저녁 식사
"""


class CliValidationTests(unittest.TestCase):
    def test_missing_date_prints_usage_and_exits(self):
        stderr = io.StringIO()
        with patch("sys.stderr", stderr), self.assertRaises(SystemExit) as caught:
            travel_planner.main([])

        self.assertEqual(caught.exception.code, 2)
        self.assertIn("usage:", stderr.getvalue())
        self.assertIn("required", stderr.getvalue())

    def test_invalid_or_impossible_date_prints_usage_and_exits(self):
        for value in ("2026/10/03", "2026-02-30"):
            with self.subTest(value=value):
                stderr = io.StringIO()
                with patch("sys.stderr", stderr), self.assertRaises(SystemExit) as caught:
                    travel_planner.main(["--date", value])

                self.assertEqual(caught.exception.code, 2)
                self.assertIn("YYYY-MM-DD", stderr.getvalue())

    def test_missing_keys_exits_before_any_api_step(self):
        with patch.dict(os.environ, {}, clear=True), \
             patch.object(travel_planner, "recommend") as recommend, \
             patch.object(travel_planner, "search_places") as search_places, \
             patch.object(travel_planner, "create_report") as create_report, \
             patch("sys.stdout", new_callable=io.StringIO) as stdout:
            result = travel_planner.main(["--date", "2026-10-03"])

        self.assertEqual(result, 1)
        self.assertIn("API 키 미설정", stdout.getvalue())
        recommend.assert_not_called()
        search_places.assert_not_called()
        create_report.assert_not_called()


class RecommendationRetryTests(unittest.TestCase):
    def test_invalid_json_is_retried_exactly_once_then_succeeds(self):
        errors = []
        valid_text = json.dumps(VALID_RECOMMENDATION, ensure_ascii=False)
        with patch.object(travel_planner, "gemini", side_effect=["not json", valid_text]) as gemini:
            result = travel_planner.recommend("2026-10-03", "secret", "model", errors)

        self.assertEqual(result, VALID_RECOMMENDATION)
        self.assertEqual(gemini.call_count, 2)
        self.assertEqual(errors, [{
            "step": "recommendation",
            "type": "PARSE_ERROR",
            "message": "추천 JSON 검증 실패 (1/2)",
        }])
        self.assertIn("필수 키 4개", gemini.call_args_list[1].args[0])

    def test_invalid_json_stops_after_one_retry(self):
        errors = []
        with patch.object(travel_planner, "gemini", return_value="not json") as gemini:
            with self.assertRaises(travel_planner.APIError) as caught:
                travel_planner.recommend("2026-10-03", "secret", "model", errors)

        self.assertEqual(caught.exception.kind, "PARSE_ERROR")
        self.assertEqual(gemini.call_count, 2)
        self.assertEqual([error["message"] for error in errors], [
            "추천 JSON 검증 실패 (1/2)",
            "추천 JSON 검증 실패 (2/2)",
        ])


class HttpErrorHandlingTests(unittest.TestCase):
    def assert_request_error(self, raised, expected_kind, secret="TOP_SECRET_KEY"):
        with patch.object(travel_planner, "urlopen", side_effect=raised):
            with self.assertRaises(travel_planner.APIError) as caught:
                travel_planner.request_json(
                    f"https://example.test/data?key={secret}",
                    {"Authorization": f"Bearer {secret}"},
                )

        self.assertEqual(caught.exception.kind, expected_kind)
        self.assertNotIn(secret, str(caught.exception))
        self.assertNotIn("example.test", str(caught.exception))

    def test_http_auth_error_is_classified_and_sanitized(self):
        error = HTTPError("https://example.test/?key=TOP_SECRET_KEY", 401, "secret response", {}, None)
        try:
            self.assert_request_error(error, "AUTH_ERROR")
        finally:
            error.close()

    def test_http_quota_error_is_classified_and_sanitized(self):
        error = HTTPError("https://example.test/?key=TOP_SECRET_KEY", 429, "secret response", {}, None)
        try:
            self.assert_request_error(error, "QUOTA_ERROR")
        finally:
            error.close()

    def test_network_errors_are_classified_and_sanitized(self):
        for error in (URLError("TOP_SECRET_KEY"), TimeoutError("TOP_SECRET_KEY"), socket.timeout("TOP_SECRET_KEY")):
            with self.subTest(error=type(error).__name__):
                self.assert_request_error(error, "NETWORK_ERROR")


class PlaceSearchTests(unittest.TestCase):
    def test_empty_result_records_error_without_raising(self):
        errors = []
        with patch.object(travel_planner, "request_json", return_value={"documents": []}):
            places = travel_planner.search_places("강릉", "kakao-secret", errors)

        self.assertEqual(places, [])
        self.assertEqual(errors[0]["type"], "EMPTY_RESULT")

    def test_coordinates_are_saved_as_numbers(self):
        response = {"documents": [{
            "place_name": "테스트 식당",
            "road_address_name": "강원 강릉시 테스트로 1",
            "address_name": "강원 강릉시 테스트동 1",
            "category_name": "음식점 > 한식",
            "place_url": "https://place.example/1",
            "x": "128.8765",
            "y": "37.7564",
        }]}
        with patch.object(travel_planner, "request_json", return_value=response):
            places = travel_planner.search_places("강릉", "kakao-secret", [])

        self.assertEqual(places[0]["x"], 128.8765)
        self.assertEqual(places[0]["y"], 37.7564)
        self.assertIsInstance(places[0]["x"], float)
        self.assertIsInstance(places[0]["y"], float)

    def test_api_failure_returns_empty_places_and_records_error(self):
        errors = []
        failure = travel_planner.APIError("AUTH_ERROR", "HTTP 401: 키/권한을 확인하세요.")
        with patch.object(travel_planner, "request_json", side_effect=failure):
            places = travel_planner.search_places("강릉", "kakao-secret", errors)

        self.assertEqual(places, [])
        self.assertEqual(errors[0]["type"], "AUTH_ERROR")


class ReportTests(unittest.TestCase):
    def test_empty_places_are_rendered_as_data_unavailable(self):
        data = {
            "travel_date": "2026-10-03",
            "recommendation": VALID_RECOMMENDATION,
            "places": [],
            "errors": [{
                "step": "place_search",
                "type": "EMPTY_RESULT",
                "message": "장소 검색 결과 0건",
            }],
        }
        with patch.object(travel_planner, "gemini", return_value=VALID_REPORT):
            report = travel_planner.create_report(data, "gemini-secret", "gemini-test")

        self.assertIn("- 데이터 없음", report)
        self.assertNotIn("모델이 만든 가게", report)
        self.assertIn("place_search: EMPTY_RESULT", report)


class MainFlowTests(unittest.TestCase):
    def setUp(self):
        self.environment = {
            "GEMINI_API_KEY": "gemini-secret",
            "KAKAO_REST_API_KEY": "kakao-secret",
            "GEMINI_MODEL": "gemini-test",
        }

    def test_normal_main_writes_raw_json_and_markdown_under_base(self):
        places = [{
            "name": "테스트 식당",
            "address": "강원 강릉시 테스트로 1",
            "category": "음식점 > 한식",
            "url": "https://place.example/1",
            "x": 128.8765,
            "y": 37.7564,
        }]
        with tempfile.TemporaryDirectory() as directory, \
             patch.dict(os.environ, self.environment, clear=True), \
             patch.object(travel_planner, "BASE", Path(directory)), \
             patch.object(travel_planner, "recommend", return_value=VALID_RECOMMENDATION), \
             patch.object(travel_planner, "search_places", return_value=places), \
             patch.object(travel_planner, "create_report", return_value=VALID_REPORT):
            result = travel_planner.main(["--date", "2026-10-03"])

            raw_files = list((Path(directory) / "results").glob("*_raw.json"))
            report_files = list((Path(directory) / "results").glob("*_travel_plan.md"))
            raw_data = json.loads(raw_files[0].read_text(encoding="utf-8"))
            report = report_files[0].read_text(encoding="utf-8")

        self.assertEqual(result, 0)
        self.assertEqual(len(raw_files), 1)
        self.assertEqual(len(report_files), 1)
        self.assertEqual(raw_data["travel_date"], "2026-10-03")
        self.assertEqual(raw_data["recommendation"], VALID_RECOMMENDATION)
        self.assertEqual(raw_data["places"], places)
        self.assertEqual(raw_data["errors"], [])
        self.assertEqual(report, VALID_REPORT)

    def test_kakao_failure_still_creates_report_with_empty_places(self):
        def failed_search(city, key, errors):
            travel_planner.record(errors, "place_search", "NETWORK_ERROR", "네트워크 오류")
            return []

        with tempfile.TemporaryDirectory() as directory, \
             patch.dict(os.environ, self.environment, clear=True), \
             patch.object(travel_planner, "BASE", Path(directory)), \
             patch.object(travel_planner, "recommend", return_value=VALID_RECOMMENDATION), \
             patch.object(travel_planner, "search_places", side_effect=failed_search), \
             patch.object(travel_planner, "create_report", return_value=VALID_REPORT) as create_report:
            result = travel_planner.main(["--date", "2026-10-03"])
            raw_file = next((Path(directory) / "results").glob("*_raw.json"))
            raw_data = json.loads(raw_file.read_text(encoding="utf-8"))

        self.assertEqual(result, 0)
        create_report.assert_called_once()
        self.assertEqual(create_report.call_args.args[0]["places"], [])
        self.assertEqual(raw_data["errors"][0]["type"], "NETWORK_ERROR")

    def test_final_llm_failure_keeps_raw_json_with_report_error(self):
        report_failure = travel_planner.APIError("QUOTA_ERROR", "HTTP 429: 사용량을 확인하세요.")
        with tempfile.TemporaryDirectory() as directory, \
             patch.dict(os.environ, self.environment, clear=True), \
             patch.object(travel_planner, "BASE", Path(directory)), \
             patch.object(travel_planner, "recommend", return_value=VALID_RECOMMENDATION), \
             patch.object(travel_planner, "search_places", return_value=[]), \
             patch.object(travel_planner, "create_report", side_effect=report_failure):
            result = travel_planner.main(["--date", "2026-10-03"])
            raw_files = list((Path(directory) / "results").glob("*_raw.json"))
            report_files = list((Path(directory) / "results").glob("*_travel_plan.md"))
            raw_data = json.loads(raw_files[0].read_text(encoding="utf-8"))

        self.assertEqual(result, 1)
        self.assertEqual(len(raw_files), 1)
        self.assertEqual(report_files, [])
        self.assertEqual(raw_data["errors"][-1]["step"], "report")
        self.assertEqual(raw_data["errors"][-1]["type"], "QUOTA_ERROR")


class SecurityTests(unittest.TestCase):
    def test_redact_replaces_every_secret(self):
        text = "gemini=gemini-secret kakao=kakao-secret again=gemini-secret"
        result = travel_planner.redact(text, ["gemini-secret", "kakao-secret"])

        self.assertEqual(result.count("[REDACTED]"), 3)
        self.assertNotIn("gemini-secret", result)
        self.assertNotIn("kakao-secret", result)

    def test_save_data_never_writes_secret_values(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "raw.json"
            travel_planner.save_data(
                path,
                {"message": "keys: gemini-secret and kakao-secret"},
                ["gemini-secret", "kakao-secret"],
            )
            saved = path.read_text(encoding="utf-8")

        self.assertNotIn("gemini-secret", saved)
        self.assertNotIn("kakao-secret", saved)
        self.assertEqual(saved.count("[REDACTED]"), 2)


if __name__ == "__main__":
    unittest.main()

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

import travel_planner


VALID_RECOMMENDATION = {
    "recommended_city": "서울",
    "weather": "선선하고 맑습니다.",
    "events": ["전시 관람"],
    "reason": "도심 이동이 편리합니다. 봄 행사를 함께 즐길 수 있습니다.",
}

VALID_MULTI_RECOMMENDATION = {
    "recommended_cities": ["제주", "강릉", "부산"],
    "region_details": [
        {
            "city": "제주",
            "weather": "온화하고 바람이 있습니다.",
            "events": ["유채꽃 행사"],
            "reason": "봄 풍경을 즐기기 좋습니다. 해안 산책을 함께 할 수 있습니다.",
        },
        {
            "city": "강릉",
            "weather": "선선하고 맑습니다.",
            "events": ["해변 문화 행사"],
            "reason": "바다 풍경을 보기 좋습니다. 카페와 전통시장을 함께 둘러볼 수 있습니다.",
        },
        {
            "city": "부산",
            "weather": "따뜻하고 쾌청합니다.",
            "events": ["항구 축제"],
            "reason": "도시와 바다를 함께 즐길 수 있습니다. 대중교통으로 이동하기 편리합니다.",
        },
    ],
}


class TravelPlannerTests(unittest.TestCase):
    def test_call_openai_chat_omits_temperature_for_gpt5_models(self):
        response = {"choices": [{"message": {"content": "{}"}}]}

        with patch.object(travel_planner, "call_json_api", return_value=response) as call:
            travel_planner.call_openai_chat("key", "gpt-5.6-luna", [], temperature=0.2)

        payload = call.call_args.kwargs["payload"]
        self.assertNotIn("temperature", payload)

    def test_validate_recommendation_rejects_empty_events(self):
        recommendation = dict(VALID_RECOMMENDATION, events=[])

        with self.assertRaisesRegex(ValueError, "events must contain 1-3"):
            travel_planner.validate_recommendation(recommendation)

    def test_validate_recommendation_rejects_reason_with_wrong_sentence_count(self):
        recommendation = dict(VALID_RECOMMENDATION, reason="한 문장입니다.")

        with self.assertRaisesRegex(ValueError, "reason must contain 2-4"):
            travel_planner.validate_recommendation(recommendation)

    def test_extract_json_object_parses_multi_region_recommendation(self):
        result = travel_planner.extract_json_object(
            json.dumps(VALID_MULTI_RECOMMENDATION, ensure_ascii=False),
            multi_region=True,
        )

        self.assertEqual(result["recommended_cities"], ["제주", "강릉", "부산"])

    def test_validate_multi_recommendation_rejects_wrong_city_count(self):
        recommendation = dict(VALID_MULTI_RECOMMENDATION)
        recommendation["recommended_cities"] = ["제주"]
        recommendation["region_details"] = [VALID_MULTI_RECOMMENDATION["region_details"][0]]

        with self.assertRaisesRegex(ValueError, "recommended_cities must contain 2-3"):
            travel_planner.validate_multi_recommendation(recommendation)

    def test_search_restaurants_by_city_continues_after_empty_and_error(self):
        class FakeProvider:
            def __init__(self):
                self.calls = []

            def search(self, city, errors):
                self.calls.append(city)
                if city == "강릉":
                    errors.append(
                        {
                            "step": "place_search",
                            "type": "EMPTY_RESULT",
                            "message": "0 results",
                        }
                    )
                    return []
                if city == "부산":
                    raise RuntimeError("temporary provider failure")
                return [{"name": f"{city} 맛집"}]

        provider = FakeProvider()
        errors = []
        restaurants = travel_planner.search_restaurants_by_city(
            provider,
            VALID_MULTI_RECOMMENDATION["recommended_cities"],
            errors,
        )

        self.assertEqual(provider.calls, ["제주", "강릉", "부산"])
        self.assertEqual(restaurants["제주"][0]["name"], "제주 맛집")
        self.assertEqual(restaurants["강릉"], [])
        self.assertEqual(restaurants["부산"], [])
        self.assertEqual(len(errors), 2)
        self.assertEqual(errors[-1]["city"], "부산")

    def test_generate_multi_report_falls_back_with_region_sections(self):
        errors = []
        restaurants_by_city = {"제주": [], "강릉": [], "부산": []}

        with patch.object(travel_planner, "call_openai_chat", return_value="# incomplete report"):
            report = travel_planner.generate_report(
                "key",
                "gpt-5.6-luna",
                "2026-03-15",
                VALID_MULTI_RECOMMENDATION,
                restaurants_by_city,
                errors,
                multi_region=True,
            )

        self.assertIn("## 지역별 추천", report)
        self.assertIn("## 지역별 맛집 추천", report)
        self.assertEqual(errors[0]["type"], "REPORT_GENERATION_FALLBACK")

    def test_load_cached_outputs_reuses_multi_region_cache_and_rejects_single_mode(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            results_dir = base_dir / "results"
            results_dir.mkdir()
            (results_dir / "2026-03-15_raw.json").write_text(
                json.dumps(
                    {
                        "date": "2026-03-15",
                        "mode": "multi",
                        "recommendation": VALID_MULTI_RECOMMENDATION,
                        "restaurants_by_city": {"제주": [], "강릉": [], "부산": []},
                        "errors": [],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (results_dir / "2026-03-15_travel_plan.md").write_text(
                "\n".join(
                    [
                        "## 추천 지역",
                        "## 지역별 추천",
                        "## 날씨 요약",
                        "## 행사/축제",
                        "## 지역별 맛집 추천",
                        "## 1일 일정 제안",
                        "## 오류 요약(errors)",
                    ]
                ),
                encoding="utf-8",
            )

            multi_cached = travel_planner.load_cached_outputs(
                base_dir, "2026-03-15", [], multi_region=True
            )
            single_cached = travel_planner.load_cached_outputs(
                base_dir, "2026-03-15", [], multi_region=False
            )

        self.assertIsNotNone(multi_cached)
        self.assertEqual(multi_cached[1], {"제주": [], "강릉": [], "부산": []})
        self.assertIsNone(single_cached)

    def test_generate_recommendation_does_not_retry_http_error(self):
        errors = []
        http_error = HTTPError(
            "https://api.openai.com/v1/chat/completions",
            401,
            "Unauthorized",
            hdrs=None,
            fp=None,
        )

        with patch.object(travel_planner, "call_openai_chat", side_effect=http_error) as call:
            with self.assertRaises(HTTPError):
                travel_planner.generate_recommendation("key", "gpt-5.6-luna", "2026-03-15", errors)

        self.assertEqual(call.call_count, 1)
        self.assertEqual(errors[0]["type"], "AUTH_ERROR")

    def test_generate_recommendation_retries_invalid_json_once(self):
        errors = []
        responses = ["not json", json.dumps(VALID_RECOMMENDATION, ensure_ascii=False)]

        with patch.object(travel_planner, "call_openai_chat", side_effect=responses) as call:
            result = travel_planner.generate_recommendation(
                "key", "gpt-5.6-luna", "2026-03-15", errors
            )

        self.assertEqual(result, VALID_RECOMMENDATION)
        self.assertEqual(call.call_count, 2)
        self.assertEqual(errors[0]["type"], "JSON_PARSE_RETRY")

    def test_generate_report_falls_back_when_required_section_is_missing(self):
        errors = []

        with patch.object(travel_planner, "call_openai_chat", return_value="# incomplete report"):
            report = travel_planner.generate_report(
                "key", "gpt-5.6-luna", "2026-03-15", VALID_RECOMMENDATION, [], errors
            )

        self.assertIn("## 오류 요약(errors)", report)
        self.assertEqual(errors[0]["type"], "REPORT_GENERATION_FALLBACK")

    def test_normalize_city_name_handles_common_suffixes(self):
        self.assertEqual(travel_planner.normalize_city_name(" 서울특별시 "), "서울")
        self.assertEqual(travel_planner.normalize_city_name("부산시"), "부산")

    def test_kakao_provider_receives_normalized_city(self):
        errors = []
        with patch.object(travel_planner, "call_json_api", return_value={"documents": []}) as call:
            provider = travel_planner.KakaoPlaceSearchProvider("key")
            provider.search("서울시", errors)

        self.assertIn("query=%EC%84%9C%EC%9A%B8+%EB%A7%9B%EC%A7%91", call.call_args.args[0])

    def test_load_cached_outputs_accepts_complete_same_date_result(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            results_dir = base_dir / "results"
            results_dir.mkdir()
            (results_dir / "2026-03-15_raw.json").write_text(
                json.dumps(
                    {
                        "date": "2026-03-15",
                        "recommendation": VALID_RECOMMENDATION,
                        "restaurants": [],
                        "errors": [],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (results_dir / "2026-03-15_travel_plan.md").write_text("# cached", encoding="utf-8")

            cached = travel_planner.load_cached_outputs(base_dir, "2026-03-15", [])

        self.assertIsNotNone(cached)
        self.assertEqual(cached[0], VALID_RECOMMENDATION)

    def test_load_cached_outputs_rebuilds_report_when_cached_sections_are_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            results_dir = base_dir / "results"
            results_dir.mkdir()
            (results_dir / "2026-03-15_raw.json").write_text(
                json.dumps(
                    {
                        "date": "2026-03-15",
                        "recommendation": VALID_RECOMMENDATION,
                        "restaurants": [],
                        "errors": [],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (results_dir / "2026-03-15_travel_plan.md").write_text(
                "# incomplete cached report",
                encoding="utf-8",
            )

            cached = travel_planner.load_cached_outputs(base_dir, "2026-03-15", [])

        self.assertIsNotNone(cached)
        self.assertIsNone(cached[3])

    def test_load_cached_outputs_accepts_raw_json_without_report(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            results_dir = base_dir / "results"
            results_dir.mkdir()
            (results_dir / "2026-03-15_raw.json").write_text(
                json.dumps(
                    {
                        "date": "2026-03-15",
                        "recommendation": VALID_RECOMMENDATION,
                        "restaurants": [],
                        "errors": [],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            cached = travel_planner.load_cached_outputs(base_dir, "2026-03-15", [])

        self.assertIsNotNone(cached)
        self.assertIsNone(cached[3])

    def test_load_cached_outputs_ignores_incomplete_cache(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            results_dir = base_dir / "results"
            results_dir.mkdir()
            (results_dir / "2026-03-15_raw.json").write_text("{}", encoding="utf-8")
            (results_dir / "2026-03-15_travel_plan.md").write_text("# cached", encoding="utf-8")

            cached = travel_planner.load_cached_outputs(base_dir, "2026-03-15", [])

        self.assertIsNone(cached)

    def test_save_outputs_records_write_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            (base_dir / "results").write_text("not a directory", encoding="utf-8")
            errors = []

            paths = travel_planner.save_outputs(
                base_dir,
                "2026-03-15",
                VALID_RECOMMENDATION,
                [],
                errors,
                "# report\n",
            )

        self.assertEqual(paths, (None, None))
        self.assertEqual(errors[0]["type"], "OUTPUT_WRITE_ERROR")

    def test_save_outputs_writes_multi_region_shape(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            restaurants_by_city = {"제주": [], "강릉": [], "부산": []}
            errors = []
            report = travel_planner.build_multi_fallback_report(
                "2026-03-15",
                VALID_MULTI_RECOMMENDATION,
                restaurants_by_city,
                errors,
            )

            raw_path, report_path = travel_planner.save_outputs(
                base_dir,
                "2026-03-15",
                VALID_MULTI_RECOMMENDATION,
                restaurants_by_city,
                errors,
                report,
                multi_region=True,
            )
            raw_data = json.loads(raw_path.read_text(encoding="utf-8"))
            report_saved = report_path.exists()

        self.assertEqual(raw_data["mode"], "multi")
        self.assertEqual(raw_data["restaurants_by_city"], restaurants_by_city)
        self.assertNotIn("restaurants", raw_data)
        self.assertTrue(report_saved)


if __name__ == "__main__":
    unittest.main()

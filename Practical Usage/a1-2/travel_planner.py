import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib import error, parse, request


OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
KAKAO_KEYWORD_SEARCH_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"
REQUIRED_REPORT_HEADINGS = (
    "추천 지역",
    "추천 이유",
    "날씨 요약",
    "행사/축제",
    "맛집 추천",
    "1일 일정 제안",
    "오류 요약(errors)",
)
MULTI_REPORT_HEADINGS = (
    "추천 지역",
    "지역별 추천",
    "날씨 요약",
    "행사/축제",
    "지역별 맛집 추천",
    "1일 일정 제안",
    "오류 요약(errors)",
)
SINGLE_MODE = "single"
MULTI_MODE = "multi"


def load_dotenv(env_path):
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Recommend a Korean travel destination and create a Markdown travel report."
    )
    parser.add_argument(
        "-date",
        "--date",
        required=True,
        help='Travel date in YYYY-MM-DD format. Example: --date "2026-03-15"',
    )
    parser.add_argument(
        "--multi-region",
        action="store_true",
        help="Enable the optional 2-3 city recommendation bonus mode.",
    )
    args = parser.parse_args()

    try:
        datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError:
        parser.error('date must use YYYY-MM-DD format. Example: --date "2026-03-15"')

    return args


def require_env(name, setup_hint):
    value = os.getenv(name)
    if value:
        return value

    print(f"Error: {name} is not set.")
    print(setup_hint)
    sys.exit(1)


def call_json_api(url, method="GET", headers=None, payload=None, timeout=30):
    body = None
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    req = request.Request(url, data=body, method=method, headers=headers or {})
    with request.urlopen(req, timeout=timeout) as response:
        text = response.read().decode("utf-8")
        return json.loads(text)


def call_openai_chat(api_key, model, messages, temperature=0.4):
    payload = {
        "model": model,
        "messages": messages,
    }
    if not model.startswith("gpt-5"):
        payload["temperature"] = temperature
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = call_json_api(
        OPENAI_CHAT_COMPLETIONS_URL,
        method="POST",
        headers=headers,
        payload=payload,
        timeout=60,
    )
    return data["choices"][0]["message"]["content"]


def extract_json_object(text, multi_region=False):
    cleaned = text.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", cleaned, flags=re.DOTALL)
    if fence_match:
        cleaned = fence_match.group(1).strip()

    first = cleaned.find("{")
    last = cleaned.rfind("}")
    if first != -1 and last != -1 and first < last:
        cleaned = cleaned[first : last + 1]

    parsed = json.loads(cleaned)
    if multi_region:
        validate_multi_recommendation(parsed)
    else:
        validate_recommendation(parsed)
    return parsed


def validate_recommendation(data):
    required = {
        "recommended_city": str,
        "weather": str,
        "events": list,
        "reason": str,
    }
    for key, expected_type in required.items():
        if key not in data:
            raise ValueError(f"missing key: {key}")
        if not isinstance(data[key], expected_type):
            raise ValueError(f"{key} must be {expected_type.__name__}")

    validate_events_and_reason(data["events"], data["reason"])


def validate_events_and_reason(events, reason, scope=""):
    prefix = f"{scope} " if scope else ""
    if not all(isinstance(item, str) for item in events):
        raise ValueError(f"{prefix}events must be an array of strings")

    if not 1 <= len(events) <= 3:
        raise ValueError(f"{prefix}events must contain 1-3 items")

    sentence_count = len(re.findall(r"[.!?。！？](?=\s|$)", reason.strip()))
    if not 2 <= sentence_count <= 4:
        raise ValueError(f"{prefix}reason must contain 2-4 sentences")


def validate_multi_recommendation(data):
    if not isinstance(data, dict):
        raise ValueError("multi recommendation must be an object")

    cities = data.get("recommended_cities")
    if not isinstance(cities, list) or not 2 <= len(cities) <= 3:
        raise ValueError("recommended_cities must contain 2-3 items")
    if not all(isinstance(city, str) and city.strip() for city in cities):
        raise ValueError("recommended_cities must be non-empty strings")

    normalized_cities = [normalize_city_name(city) for city in cities]
    if len(set(normalized_cities)) != len(normalized_cities):
        raise ValueError("recommended_cities must not contain duplicates")

    details = data.get("region_details")
    if not isinstance(details, list) or len(details) != len(cities):
        raise ValueError("region_details must describe every recommended city")

    detail_cities = []
    for detail in details:
        if not isinstance(detail, dict):
            raise ValueError("region_details items must be objects")
        for key, expected_type in {
            "city": str,
            "weather": str,
            "events": list,
            "reason": str,
        }.items():
            if key not in detail:
                raise ValueError(f"region_details missing key: {key}")
            if not isinstance(detail[key], expected_type):
                raise ValueError(f"region_details.{key} must be {expected_type.__name__}")
        detail_city = normalize_city_name(detail["city"])
        detail_cities.append(detail_city)
        validate_events_and_reason(detail["events"], detail["reason"], scope=detail_city)

    if len(set(detail_cities)) != len(detail_cities):
        raise ValueError("region_details must not contain duplicate cities")
    if set(detail_cities) != set(normalized_cities):
        raise ValueError("region_details cities must match recommended_cities")


def generate_recommendation(api_key, model, travel_date, errors, multi_region=False):
    system_prompt = (
        "You are a Korean domestic travel recommendation assistant. "
        "Return only a JSON object. Do not wrap it in Markdown."
    )
    if multi_region:
        user_prompt = f"""
Recommend 2 or 3 different Korean cities for a trip on {travel_date}.

Return JSON only with this exact schema:
{{
  "recommended_cities": ["string", "string", "string"],
  "region_details": [
    {{
      "city": "string",
      "weather": "string",
      "events": ["string"],
      "reason": "2-4 Korean sentences"
    }}
  ]
}}

The recommended_cities array must contain exactly 2 or 3 unique cities.
The region_details array must contain one item for every recommended city.
The weather and event information can be a general seasonal estimate.
Do not include API keys, citations, or unverified links.
"""
    else:
        user_prompt = f"""
Recommend one Korean city for a trip on {travel_date}.

Return JSON only with this exact schema:
{{
  "recommended_city": "string",
  "weather": "string",
  "events": ["string", "string"],
  "reason": "2-4 Korean sentences"
}}

The weather and event information can be a general seasonal estimate.
Do not include API keys, citations, or unverified links.
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    try:
        first_response = call_openai_chat(api_key, model, messages, temperature=0.2)
        return extract_json_object(first_response, multi_region=multi_region)
    except error.HTTPError as exc:
        errors.append(classify_http_error("llm_recommendation", exc))
        raise
    except (error.URLError, TimeoutError) as exc:
        errors.append(
            {
                "step": "llm_recommendation",
                "type": "NETWORK_ERROR",
                "message": str(exc),
            }
        )
        raise
    except (ValueError, KeyError, TypeError) as exc:
        errors.append(
            {
                "step": "llm_recommendation",
                "type": "JSON_PARSE_RETRY",
                "message": str(exc),
            }
        )

    repair_messages = messages + [
        {
            "role": "assistant",
            "content": locals().get("first_response", ""),
        },
        {
            "role": "user",
            "content": (
                "The previous answer could not be parsed. "
                + (
                    "Return only valid JSON with recommended_cities and "
                    "region_details for every city."
                    if multi_region
                    else "Return only valid JSON with the required keys: "
                    "recommended_city, weather, events, reason."
                )
            ),
        },
    ]
    try:
        retry_response = call_openai_chat(api_key, model, repair_messages, temperature=0.0)
        return extract_json_object(retry_response, multi_region=multi_region)
    except (ValueError, KeyError, TypeError) as exc:
        errors.append(
            {
                "step": "llm_recommendation",
                "type": "JSON_PARSE_FAILED",
                "message": str(exc),
            }
        )
        raise


def classify_http_error(step, exc):
    status = getattr(exc, "code", None)
    if status in (401, 403):
        error_type = "AUTH_ERROR"
    elif status == 429:
        error_type = "QUOTA_ERROR"
    else:
        error_type = "HTTP_ERROR"

    return {
        "step": step,
        "type": error_type,
        "message": f"HTTP {status}",
    }


def normalize_city_name(city):
    aliases = {
        "서울시": "서울",
        "서울특별시": "서울",
        "부산시": "부산",
        "부산광역시": "부산",
        "대구시": "대구",
        "대구광역시": "대구",
        "인천시": "인천",
        "인천광역시": "인천",
        "광주시": "광주",
        "광주광역시": "광주",
        "대전시": "대전",
        "대전광역시": "대전",
        "울산시": "울산",
        "울산광역시": "울산",
        "세종시": "세종",
        "세종특별자치시": "세종",
        "제주도": "제주",
        "제주특별자치도": "제주",
    }
    cleaned = " ".join(str(city).strip().split())
    return aliases.get(cleaned, cleaned)


class PlaceSearchProvider:
    def search(self, city, errors):
        raise NotImplementedError


class KakaoPlaceSearchProvider(PlaceSearchProvider):
    def __init__(self, kakao_key, size=5):
        self.kakao_key = kakao_key
        self.size = size

    def search(self, city, errors):
        normalized_city = normalize_city_name(city)
        query = f"{normalized_city} 맛집"
        params = parse.urlencode({"query": query, "size": self.size})
        url = f"{KAKAO_KEYWORD_SEARCH_URL}?{params}"
        headers = {"Authorization": f"KakaoAK {self.kakao_key}"}

        try:
            data = call_json_api(url, headers=headers, timeout=30)
        except error.HTTPError as exc:
            errors.append(classify_http_error("place_search", exc))
            return []
        except Exception as exc:
            errors.append(
                {
                    "step": "place_search",
                    "type": "NETWORK_OR_PARSE_ERROR",
                    "message": str(exc),
                }
            )
            return []

        documents = data.get("documents", [])
        if not documents:
            errors.append(
                {
                    "step": "place_search",
                    "type": "EMPTY_RESULT",
                    "message": f"0 results for query={query}",
                }
            )
            return []

        restaurants = []
        for item in documents[: self.size]:
            restaurants.append(
                {
                    "name": item.get("place_name", ""),
                    "address": item.get("road_address_name") or item.get("address_name", ""),
                    "category": item.get("category_name", ""),
                    "url": item.get("place_url", ""),
                    "x": safe_float(item.get("x")),
                    "y": safe_float(item.get("y")),
                }
            )
        return restaurants


def search_kakao_restaurants(kakao_key, city, errors, size=5):
    return KakaoPlaceSearchProvider(kakao_key, size=size).search(city, errors)


def search_restaurants_by_city(provider, cities, errors):
    restaurants_by_city = {}
    for city in cities:
        normalized_city = normalize_city_name(city)
        error_start = len(errors)
        try:
            restaurants_by_city[normalized_city] = provider.search(normalized_city, errors)
        except error.HTTPError as exc:
            error_item = classify_http_error("place_search", exc)
            error_item["city"] = normalized_city
            errors.append(error_item)
            restaurants_by_city[normalized_city] = []
        except Exception as exc:
            errors.append(
                {
                    "step": "place_search",
                    "type": "NETWORK_OR_PARSE_ERROR",
                    "message": str(exc),
                    "city": normalized_city,
                }
            )
            restaurants_by_city[normalized_city] = []

        for item in errors[error_start:]:
            if isinstance(item, dict):
                item.setdefault("city", normalized_city)

    return restaurants_by_city


def safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def build_fallback_report(travel_date, recommendation, restaurants, errors):
    lines = [
        f"# {travel_date} 국내 여행 추천 리포트",
        "",
        "## 추천 지역",
        recommendation["recommended_city"],
        "",
        "## 추천 이유",
        recommendation["reason"],
        "",
        "## 날씨 요약",
        recommendation["weather"],
        "",
        "## 행사/축제",
    ]
    lines.extend([f"- {event}" for event in recommendation["events"]] or ["- 데이터 없음"])
    lines.extend(["", "## 맛집 추천"])
    if restaurants:
        for restaurant in restaurants:
            detail = restaurant["address"] or "주소 정보 없음"
            lines.append(f"- {restaurant['name']} ({detail})")
    else:
        lines.append("- 데이터 없음 (장소 검색 결과 0건 또는 API 오류)")

    lines.extend(
        [
            "",
            "## 1일 일정 제안",
            "- 오전: 추천 지역의 대표 관광지 방문",
            "- 오후: 지역 행사 또는 산책 코스 즐기기",
            "- 저녁: 맛집 방문 후 숙소 이동",
            "",
            "## 오류 요약(errors)",
        ]
    )
    if errors:
        lines.extend([f"- {item['step']}: {item['type']} - {item['message']}" for item in errors])
    else:
        lines.append("- 없음")

    return "\n".join(lines) + "\n"


def build_multi_fallback_report(travel_date, recommendation, restaurants_by_city, errors):
    detail_by_city = {
        normalize_city_name(detail["city"]): detail
        for detail in recommendation["region_details"]
    }
    lines = [
        f"# {travel_date} 국내 복수 지역 여행 추천 리포트",
        "",
        "## 추천 지역",
        ", ".join(recommendation["recommended_cities"]),
        "",
        "## 지역별 추천",
    ]
    for city in recommendation["recommended_cities"]:
        normalized_city = normalize_city_name(city)
        detail = detail_by_city[normalized_city]
        lines.extend(
            [
                f"### {normalized_city}",
                f"- 추천 이유: {detail['reason']}",
            ]
        )

    lines.extend(["", "## 날씨 요약"])
    for city in recommendation["recommended_cities"]:
        detail = detail_by_city[normalize_city_name(city)]
        lines.append(f"- {normalize_city_name(city)}: {detail['weather']}")

    lines.extend(["", "## 행사/축제"])
    for city in recommendation["recommended_cities"]:
        detail = detail_by_city[normalize_city_name(city)]
        lines.append(f"### {normalize_city_name(city)}")
        lines.extend([f"- {event}" for event in detail["events"]] or ["- 데이터 없음"])

    lines.extend(["", "## 지역별 맛집 추천"])
    for city in recommendation["recommended_cities"]:
        normalized_city = normalize_city_name(city)
        restaurants = restaurants_by_city.get(normalized_city, [])
        lines.append(f"### {normalized_city}")
        if restaurants:
            for restaurant in restaurants:
                detail = restaurant.get("address") or "주소 정보 없음"
                lines.append(f"- {restaurant.get('name', '이름 없음')} ({detail})")
        else:
            lines.append("- 데이터 없음 (장소 검색 결과 0건 또는 API 오류)")

    lines.extend(
        [
            "",
            "## 1일 일정 제안",
            "- 오전: 첫 번째 추천 지역의 대표 관광지 방문",
            "- 오후: 두 번째 추천 지역의 행사 또는 산책 코스 확인",
            "- 저녁: 이동 가능한 지역의 맛집 방문",
            "",
            "## 오류 요약(errors)",
        ]
    )
    if errors:
        lines.extend([f"- {item['step']}: {item['type']} - {item['message']}" for item in errors])
    else:
        lines.append("- 없음")

    return "\n".join(lines) + "\n"


def validate_report_sections(report, multi_region=False):
    required_headings = MULTI_REPORT_HEADINGS if multi_region else REQUIRED_REPORT_HEADINGS
    missing = [heading for heading in required_headings if heading not in report]
    if missing:
        raise ValueError(f"report missing required sections: {', '.join(missing)}")


def generate_report(
    api_key,
    model,
    travel_date,
    recommendation,
    restaurants,
    errors,
    multi_region=False,
):
    if multi_region:
        section_text = """
- 추천 지역
- 지역별 추천
- 날씨 요약
- 행사/축제
- 지역별 맛집 추천
- 1일 일정 제안
- 오류 요약(errors)
"""
    else:
        section_text = """
- 추천 지역
- 추천 이유
- 날씨 요약
- 행사/축제
- 맛집 추천
- 1일 일정 제안
- 오류 요약(errors)
"""

    prompt = f"""
Create a Korean Markdown travel report.

Travel date: {travel_date}
Recommendation JSON:
{json.dumps(recommendation, ensure_ascii=False, indent=2)}

Restaurant search results:
{json.dumps(restaurants, ensure_ascii=False, indent=2)}

Errors:
{json.dumps(errors, ensure_ascii=False, indent=2)}

The report must include these sections:
{section_text}

If a city's restaurants are empty, write "데이터 없음" in that city's restaurant section.
Do not include API keys or invented reference links.
"""
    messages = [
        {
            "role": "system",
            "content": "You create concise Korean Markdown travel reports.",
        },
        {"role": "user", "content": prompt},
    ]

    try:
        report = call_openai_chat(api_key, model, messages, temperature=0.5).strip() + "\n"
        validate_report_sections(report, multi_region=multi_region)
        return report
    except Exception as exc:
        errors.append(
            {
                "step": "llm_report",
                "type": "REPORT_GENERATION_FALLBACK",
                "message": str(exc),
            }
        )
        if multi_region:
            return build_multi_fallback_report(
                travel_date,
                recommendation,
                restaurants,
                errors,
            )
        return build_fallback_report(travel_date, recommendation, restaurants, errors)


def validate_restaurants_by_city(restaurants_by_city, cities):
    if not isinstance(restaurants_by_city, dict):
        raise ValueError("restaurants_by_city must be an object")

    expected_cities = {normalize_city_name(city) for city in cities}
    actual_cities = set(restaurants_by_city)
    if actual_cities != expected_cities:
        raise ValueError("restaurants_by_city keys must match recommended_cities")
    if not all(isinstance(items, list) for items in restaurants_by_city.values()):
        raise ValueError("restaurants_by_city values must be arrays")


def load_cached_outputs(base_dir, travel_date, errors, multi_region=False):
    results_dir = base_dir / "results"
    raw_path = results_dir / f"{travel_date}_raw.json"
    report_path = results_dir / f"{travel_date}_travel_plan.md"

    if not raw_path.exists():
        return None

    try:
        raw_data = json.loads(raw_path.read_text(encoding="utf-8"))
        if raw_data.get("date") != travel_date:
            return None
        requested_mode = MULTI_MODE if multi_region else SINGLE_MODE
        cached_mode = raw_data.get("mode", SINGLE_MODE)
        if cached_mode != requested_mode:
            return None
        recommendation = raw_data["recommendation"]
        if multi_region:
            validate_multi_recommendation(recommendation)
            restaurants = raw_data["restaurants_by_city"]
            validate_restaurants_by_city(restaurants, recommendation["recommended_cities"])
        else:
            validate_recommendation(recommendation)
            restaurants = raw_data["restaurants"]
        cached_errors = raw_data["errors"]
        report = None
        if report_path.exists():
            report = report_path.read_text(encoding="utf-8")
            try:
                validate_report_sections(report, multi_region=multi_region)
            except ValueError:
                report = None
        if not isinstance(cached_errors, list):
            return None
        if not multi_region and not isinstance(restaurants, list):
            return None
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(
            {
                "step": "cache_read",
                "type": "CACHE_READ_ERROR",
                "message": str(exc),
            }
        )
        return None
    except (KeyError, TypeError, ValueError):
        return None

    return recommendation, restaurants, cached_errors, report, raw_path, report_path


def save_outputs(
    base_dir,
    travel_date,
    recommendation,
    restaurants,
    errors,
    report,
    multi_region=False,
):
    results_dir = base_dir / "results"
    try:
        results_dir.mkdir(exist_ok=True)
    except OSError as exc:
        errors.append(
            {
                "step": "output_save",
                "type": "OUTPUT_WRITE_ERROR",
                "message": str(exc),
            }
        )
        return None, None

    raw_path = results_dir / f"{travel_date}_raw.json"
    report_path = results_dir / f"{travel_date}_travel_plan.md"

    raw_data = {
        "date": travel_date,
        "mode": MULTI_MODE if multi_region else SINGLE_MODE,
        "recommendation": recommendation,
        "errors": errors,
    }
    if multi_region:
        raw_data["restaurants_by_city"] = restaurants
    else:
        raw_data["restaurants"] = restaurants

    saved_raw_path = None
    saved_report_path = None
    try:
        raw_path.write_text(
            json.dumps(raw_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        saved_raw_path = raw_path
    except OSError as exc:
        errors.append(
            {
                "step": "output_save",
                "type": "OUTPUT_WRITE_ERROR",
                "message": str(exc),
            }
        )

    try:
        report_path.write_text(report, encoding="utf-8")
        saved_report_path = report_path
    except OSError as exc:
        errors.append(
            {
                "step": "output_save",
                "type": "OUTPUT_WRITE_ERROR",
                "message": str(exc),
            }
        )

    return saved_raw_path, saved_report_path


def main():
    base_dir = Path(__file__).resolve().parent
    load_dotenv(base_dir / ".env")
    args = parse_args()
    multi_region = args.multi_region

    errors = []
    cached = load_cached_outputs(base_dir, args.date, errors, multi_region=multi_region)
    if cached:
        recommendation, restaurants, errors, report, raw_path, report_path = cached
        if not report:
            if multi_region:
                report = build_multi_fallback_report(
                    args.date,
                    recommendation,
                    restaurants,
                    errors,
                )
            else:
                report = build_fallback_report(args.date, recommendation, restaurants, errors)
            saved_raw_path, saved_report_path = save_outputs(
                base_dir,
                args.date,
                recommendation,
                restaurants,
                errors,
                report,
                multi_region=multi_region,
            )
            raw_path = saved_raw_path or raw_path
            report_path = saved_report_path or report_path
        print(f"캐시된 결과를 재사용합니다: {report_path}")
        print(f"원본 데이터: {raw_path}")
        return

    openai_key = require_env(
        "OPENAI_API_KEY",
        'Set it in PowerShell: $env:OPENAI_API_KEY="YOUR_KEY"',
    )
    kakao_key = require_env(
        "KAKAO_REST_API_KEY",
        'Set it in PowerShell: $env:KAKAO_REST_API_KEY="YOUR_KEY"',
    )
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    print("[1/3] 1차 추천 생성 중(LLM)...")
    recommendation = generate_recommendation(
        openai_key,
        model,
        args.date,
        errors,
        multi_region=multi_region,
    )
    if multi_region:
        print(f'  - recommended_cities: {json.dumps(recommendation["recommended_cities"], ensure_ascii=False)}')
    else:
        print(f'  - recommended_city: "{recommendation["recommended_city"]}"')

    print("[2/3] 맛집 검색 중(지도/장소 API)...")
    if multi_region:
        provider = KakaoPlaceSearchProvider(kakao_key)
        restaurants = search_restaurants_by_city(
            provider,
            recommendation["recommended_cities"],
            errors,
        )
        for city, city_restaurants in restaurants.items():
            if city_restaurants:
                print(f"  - {city}: 맛집 {len(city_restaurants)}곳 검색 완료")
            else:
                print(f"  - {city}: 맛집 데이터 없음. 다음 지역으로 진행합니다.")
    else:
        restaurants = search_kakao_restaurants(
            kakao_key,
            recommendation["recommended_city"],
            errors,
        )
        if restaurants:
            print(f"  - 맛집 {len(restaurants)}곳 검색 완료")
        else:
            print("  - 맛집 데이터 없음. 리포트 생성을 계속 진행합니다.")

    print("[3/3] 최종 리포트 생성 중(LLM)...")
    report = generate_report(
        openai_key,
        model,
        args.date,
        recommendation,
        restaurants,
        errors,
        multi_region=multi_region,
    )
    raw_path, report_path = save_outputs(
        base_dir,
        args.date,
        recommendation,
        restaurants,
        errors,
        report,
        multi_region=multi_region,
    )
    if raw_path is None or report_path is None:
        print("  - 결과 파일 저장에 실패했습니다. errors를 확인하세요.")
        return

    print("  - 리포트 생성 완료")
    print()
    print(f"완료! {report_path} 를 확인하세요.")
    print(f"원본 데이터: {raw_path}")


if __name__ == "__main__":
    main()

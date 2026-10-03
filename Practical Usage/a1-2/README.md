# 인터넷 정보를 받아와서 여행지 추천해주는 파이썬 프로그램

A1-2 미션 산출물입니다. 사용자가 여행 날짜를 입력하면 LLM API가 국내 추천 지역을 JSON으로 만들고, Kakao Local API가 해당 지역의 맛집을 검색한 뒤, 최종 여행 리포트를 Markdown 파일로 저장합니다. `--multi-region`을 선택하면 2~3개 지역을 각각 검색하는 보너스 모드도 사용할 수 있습니다.

## 제출 정보

- 미션 폴더: `A1-2/`
- 실행 파일: `travel_planner.py`
- 원본 데이터 저장 위치: `results/YYYY-MM-DD_raw.json`
- 최종 리포트 저장 위치: `results/YYYY-MM-DD_travel_plan.md`
- 선택한 API 조합: OpenAI 계열 API + Kakao Local API

## 실행 환경

- Python 3.10 이상
- 터미널 실행
- 웹 UI 없음
- 외부 패키지 설치 없이 Python 표준 라이브러리만 사용

## API 키 설정

API 키는 코드에 직접 쓰지 않습니다. `A1-2/.env` 파일 또는 환경변수로 설정합니다.

`.env.example`을 참고해 `A1-2/.env` 파일을 만듭니다.

```text
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
OPENAI_MODEL=gpt-5.6-luna
KAKAO_REST_API_KEY=YOUR_KAKAO_REST_API_KEY
```

Windows PowerShell에서 현재 터미널 세션에만 설정하려면 아래처럼 입력합니다.

```powershell
$env:OPENAI_API_KEY="YOUR_KEY"
$env:KAKAO_REST_API_KEY="YOUR_KEY"
```

macOS/Linux에서는 아래처럼 입력합니다.

```bash
export OPENAI_API_KEY="YOUR_KEY"
export KAKAO_REST_API_KEY="YOUR_KEY"
```

실제 키 값은 README, 코드, 결과 파일, Git 커밋에 포함하지 않습니다.

## HTTP 메서드 선택 근거

OpenAI 호출은 `POST`를 사용합니다. 모델 이름과 대화 메시지, 응답 형식 요구사항이 요청 본문에 들어가기 때문입니다.

Kakao Local 키워드 검색은 `GET`을 사용합니다. 검색어와 크기 같은 필터가 읽기 전용 쿼리 파라미터에 자연스럽게 들어가기 때문입니다.

이 선택은 HTTP 설계 관점의 설명이며, 보안 보장을 의미하지는 않습니다. 실제 보안은 키를 코드에 두지 않고 `.env` 또는 환경변수로만 관리하는 것으로 확보합니다.

## 프롬프트와 재시도 정책

기본 모드의 1차 추천 LLM 응답은 JSON 전용으로 다룹니다. 요구 키는 아래 4개입니다.

- `recommended_city`
- `weather`
- `events`
- `reason`

미션 기준과 현재 평가 기준에서는 `events`가 1~3개 문자열이어야 하고, `reason`은 2~4문장 범위가 기대됩니다. 현재 구현은 JSON 파싱과 필수 키/타입 검증을 수행하고, JSON 파싱이나 검증에 실패했을 때만 1회 repair retry를 시도합니다.

복수 지역 모드에서는 다음 구조를 사용합니다.

```json
{
  "recommended_cities": ["제주", "강릉", "부산"],
  "region_details": [
    {
      "city": "제주",
      "weather": "온화하고 바람이 있습니다.",
      "events": ["유채꽃 행사"],
      "reason": "봄 풍경을 즐기기 좋습니다. 해안 산책을 함께 할 수 있습니다."
    },
    {
      "city": "강릉",
      "weather": "선선하고 맑습니다.",
      "events": ["해변 문화 행사"],
      "reason": "바다 풍경을 보기 좋습니다. 카페와 전통시장을 함께 둘러볼 수 있습니다."
    },
    {
      "city": "부산",
      "weather": "따뜻하고 쾌청합니다.",
      "events": ["항구 축제"],
      "reason": "도시와 바다를 함께 즐길 수 있습니다. 대중교통으로 이동하기 편리합니다."
    }
  ]
}
```

`recommended_cities`는 2~3개의 중복 없는 도시여야 하며, `region_details`에는 각 도시의 날씨·행사·추천 이유가 하나씩 있어야 합니다.

HTTP 오류, 인증 실패, 쿼터 초과는 JSON으로 다시 해석하지 않습니다. 그런 경우에는 `errors`에 기록하고 다음 단계로 넘어갑니다.

## 실행 방법

작업공간 루트에서 실행:

```bash
cd A1-2
python travel_planner.py --date "2026-03-15"
```

복수 지역 추천 보너스를 실행하려면 선택 옵션을 추가합니다.

```bash
python travel_planner.py --date "2026-03-15" --multi-region
```

미션 원문에 맞춰 `-date` 형식도 지원합니다.

```bash
python travel_planner.py -date "2026-03-15"
```

도움말 확인:

```bash
python travel_planner.py --help
```

문법 검증:

```bash
python -m py_compile travel_planner.py
```

## 실행 흐름

```text
[1/3] 1차 추천 생성 중(LLM)...
  - recommended_city: "제주"
[2/3] 맛집 검색 중(지도/장소 API)...
  - 맛집 5곳 검색 완료
[3/3] 최종 리포트 생성 중(LLM)...
  - 리포트 생성 완료

완료! results/2026-03-15_travel_plan.md 를 확인하세요.
원본 데이터: results/2026-03-15_raw.json
```

## 결과물 확인

실행 후 `results/` 폴더에 아래 파일이 생성됩니다.

| 파일 | 내용 |
| --- | --- |
| `YYYY-MM-DD_raw.json` | 1차 추천 JSON, 맛집 검색 결과, 오류 요약 |
| `YYYY-MM-DD_travel_plan.md` | 최종 국내 여행 추천 리포트 |

원본 JSON에는 최소한 아래 구조가 들어갑니다.

```json
{
  "date": "2026-03-15",
  "recommendation": {
    "recommended_city": "제주",
    "weather": "3월 중순의 일반적 날씨 요약",
    "events": ["행사 후보"],
    "reason": "추천 근거"
  },
  "restaurants": [],
  "errors": []
}
```

복수 지역 모드의 원본 JSON은 `mode: "multi"`, `recommendation.recommended_cities`, `recommendation.region_details`, `restaurants_by_city`, `errors`를 저장합니다.

## 주요 기능

- `argparse` 기반 CLI 실행
- `-date` 또는 `--date` 필수 옵션 지원
- `YYYY-MM-DD` 날짜 형식 검증
- `.env` 또는 환경변수에서 API 키 읽기
- OpenAI 계열 API로 1차 추천 JSON 생성
- `--multi-region` 선택 시 2~3개 지역 추천 JSON 생성
- LLM JSON 파싱 실패 시 최대 1회 재시도
- Kakao Local API로 추천 도시 맛집 검색
- 복수 지역 모드에서 지역별 Kakao 맛집 검색 반복
- 맛집 검색 0건 또는 API 실패 시 리포트 생성 계속 진행
- 최종 Markdown 여행 리포트 생성
- 원본 JSON과 Markdown 파일을 `results/`에 저장
- 오류 목록을 `errors` 배열로 관리

## 오류 기록 형식과 점검 포인트

`errors`에는 아래 구조의 항목이 누적됩니다.

```json
{
  "step": "place_search",
  "type": "AUTH_ERROR",
  "message": "HTTP 403"
}
```

`step`은 어느 단계에서 문제가 났는지, `type`은 오류 분류, `message`는 사람이 읽을 수 있는 요약입니다.
복수 지역 모드의 장소 검색 오류에는 문제가 발생한 `city`도 함께 기록합니다.

401/403이 보이면 아래를 먼저 확인합니다.

- `.env`의 변수 이름이 `OPENAI_API_KEY`, `OPENAI_MODEL`, `KAKAO_REST_API_KEY`인지
- 요청 헤더 형식이 OpenAI는 `Authorization: Bearer ...`, Kakao는 `Authorization: KakaoAK ...`인지
- Kakao REST 키가 해당 앱의 로컬 검색 권한을 갖고 있는지
- OpenAI 계정/프로젝트가 현재 `OPENAI_MODEL`에 접근할 수 있는지

외부 실행 검증에서 OpenAI 추천과 최종 리포트 생성은 성공했습니다. Kakao Local은 처음에 앱의 `OPEN_MAP_AND_LOCAL` 서비스가 비활성화되어 `HTTP 403`을 반환했지만, 해당 서비스를 활성화한 뒤에는 맛집 검색 결과도 정상 확인했습니다. 키 값은 출력하지 않고, 존재 여부와 이름만 확인합니다.

## 요구사항 대응표

| 미션 요구사항 | 반영 내용 |
| --- | --- |
| Python 3.10 이상 | 표준 라이브러리 기반 Python 프로그램 |
| CLI 기반 프로그램 | `travel_planner.py`를 터미널에서 실행 |
| `argparse` 사용 | `parse_args()`에서 인자 처리 |
| 필수 옵션 `-date "YYYY-MM-DD"` | `-date`, `--date` 모두 지원 |
| 날짜 형식 검증 | 형식 오류 시 argparse 사용법 출력 후 종료 |
| LLM API 택1 | OpenAI 계열 API 사용 |
| 지도/장소 API 택1 | Kakao Local 키워드 검색 API 사용 |
| LLM 1차 추천 JSON | 기본 모드는 `recommended_city`, 복수 모드는 `recommended_cities`와 `region_details` 생성 |
| JSON 파싱 가능 출력 | JSON 전용 프롬프트와 파싱 함수 사용 |
| 맛집 N곳 검색 | 추천 도시 + `맛집` 키워드로 최대 5곳 검색, 복수 모드는 지역별 반복 |
| 맛집 0건 처리 | 중단하지 않고 `데이터 없음`으로 리포트 진행 |
| 최종 Markdown 리포트 | 추천 지역, 이유, 날씨, 행사, 맛집, 일정, 오류 요약 포함 |
| API 호출/파싱 오류 처리 | `try-except`와 `errors` 배열 사용 |
| API 키 미설정 처리 | 설정 방법 안내 후 즉시 종료 |
| 지도 API 실패 처리 | 맛집 빈 목록으로 두고 리포트 생성 계속 |
| LLM JSON 파싱 실패 처리 | 최대 1회 재시도 |
| API 키 보안 | `.env`, 환경변수, `.gitignore`, `.env.example` 사용 |
| 결과 저장 | `results/YYYY-MM-DD_raw.json`, `results/YYYY-MM-DD_travel_plan.md` 생성 |

## 오류 처리 정책

- API 키 미설정: 프로그램을 종료하고 설정 방법을 안내합니다.
- LLM JSON 파싱 실패: 한 번만 재요청합니다.
- Kakao Local 인증/네트워크/쿼터 오류: `errors`에 기록하고 맛집은 `데이터 없음`으로 처리합니다.
- 최종 리포트 생성 실패: 프로그램 내부에서 기본 Markdown 리포트를 생성합니다.

## 캐시, 도시 정규화, 검색 추상화

- 같은 날짜의 완전한 `results/YYYY-MM-DD_raw.json`이 있으면 Markdown 유무와 관계없이 현재 실행 모드에 맞는지 확인한 뒤 API를 다시 호출하지 않고 재사용합니다.
- raw JSON은 있지만 Markdown이 없거나 비어 있으면 API를 호출하지 않고 로컬 fallback Markdown을 재생성합니다.
- JSON이 손상됐거나 날짜·필수 키가 다르면 캐시를 무시하고 정상 흐름으로 다시 실행합니다.
- 기존 `mode` 없는 raw JSON은 단일 모드 캐시로 읽고, 복수 모드 캐시는 `mode: "multi"`와 지역별 필드를 모두 요구합니다. 단일/복수 형식이 다르면 서로의 캐시를 재사용하지 않습니다.
- `서울`, `서울시`, `서울특별시`처럼 흔한 도시 표기는 검색 전에 같은 검색어로 정규화합니다.
- 장소 검색은 `PlaceSearchProvider` 인터페이스 뒤에 있으며, 현재 실제 공급자는 `KakaoPlaceSearchProvider` 하나입니다.

캐시는 같은 날짜를 반복 실행할 때 API 비용을 줄이는 보완 기능입니다. 여행 날짜를 바꾸면 별도 결과 파일을 사용합니다.

LLM이 만든 Markdown은 저장 전에 모드별 필수 섹션을 확인합니다. 단일 모드는 `추천 지역`, `추천 이유`, `날씨 요약`, `행사/축제`, `맛집 추천`, `1일 일정 제안`, `오류 요약(errors)`을, 복수 모드는 `추천 지역`, `지역별 추천`, `날씨 요약`, `행사/축제`, `지역별 맛집 추천`, `1일 일정 제안`, `오류 요약(errors)`을 요구합니다. 하나라도 빠지면 해당 모드의 기본 Markdown 리포트로 대체합니다.

## 테스트

외부 API를 호출하지 않는 회귀 테스트는 아래처럼 실행합니다.

```bash
python3 -m unittest discover -s tests -v
```

## API 키 보안 주의

API 키를 코드에 직접 쓰면 GitHub 업로드나 화면 공유 중 외부에 노출될 수 있습니다. 또한 키 교체가 필요할 때 코드를 수정해야 하고, 과금/쿼터가 있는 서비스에서 사고가 날 수 있습니다.

그래서 이 프로그램은 실제 키를 `.env` 또는 환경변수에서만 읽습니다. `.env`와 실행 결과 JSON/Markdown은 `.gitignore`에 등록했습니다.

## 보너스 과제

선택 보너스 중 결과 캐싱과 복수 지역 추천을 구현했습니다. 같은 날짜의 완전한 raw JSON을 현재 모드에 맞게 재사용하고, Markdown이 없거나 필수 섹션이 빠진 경우에는 API를 호출하지 않고 해당 모드의 fallback Markdown을 재생성합니다.

- 복수 지역 추천: 구현 완료 (`--multi-region`)
- 결과 캐싱: 구현 완료

복수 지역 모드에서는 한 지역의 검색 결과가 0건이거나 오류여도 다른 지역 검색을 계속하고, 지역별 목록과 `errors`에 결과를 남깁니다.

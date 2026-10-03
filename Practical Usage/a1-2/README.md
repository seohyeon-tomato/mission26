# 날짜 기반 국내 여행 플래너

여행 날짜를 지정하면 국내 도시를 추천하고, 그 지역의 음식점을 찾아 하루 일정이 담긴 Markdown 보고서를 만듭니다. 프로그램은 터미널에서 실행하며, 결과는 `results/`에 날짜별로 저장합니다.

## 프로젝트 구성

| 경로 | 역할 |
| --- | --- |
| `travel_planner.py` | 날짜 입력, API 연동, 결과 저장을 담당하는 CLI |
| `tests/` | 네트워크 없이 주요 동작을 확인하는 회귀 테스트 |
| `results/` | 실행별 JSON 원본과 여행 보고서 |
| `mission_analysis.md` | 요구사항을 기능과 완료 기준으로 정리한 분석 노트 |

사용하는 서비스는 OpenAI 호환 Chat Completions API와 Kakao Local API입니다. 별도 Python 패키지 없이 표준 라이브러리로 실행합니다.

## 준비하기

Python 3.10 이상을 권장합니다. 저장소의 `.env.example`을 복사해 같은 폴더에 `.env`를 만든 다음, 본인의 키를 넣습니다.

```text
OPENAI_API_KEY=실제_OpenAI_API_키
OPENAI_MODEL=gpt-5.6-luna
KAKAO_REST_API_KEY=실제_Kakao_REST_키
```

`.env`와 실제 결과 파일은 Git에서 제외됩니다. 키 값은 코드, 터미널 캡처, 결과 문서에 붙여 넣지 마세요.

## 실행하기

프로젝트 폴더에서 실행합니다.

```bash
python3 travel_planner.py --date "2026-10-15"
```

`-date` 표기도 사용할 수 있습니다. 여러 도시를 추천받으려면 `--multi-region`을 더합니다.

```bash
python3 travel_planner.py -date "2026-10-15" --multi-region
```

실행이 끝나면 `results/2026-10-15_raw.json`과 `results/2026-10-15_travel_plan.md`를 확인합니다. 같은 날짜와 같은 모드의 완성된 JSON이 있으면 그 결과를 재사용할 수 있습니다.

도움말과 문법은 다음 명령으로 확인할 수 있습니다.

```bash
python3 travel_planner.py --help
python3 -m py_compile travel_planner.py
```

## 처리 순서

1. CLI가 날짜 형식을 검사하고 `.env` 또는 환경변수에서 키를 읽습니다.
2. LLM에 날짜를 전달해 추천 정보를 JSON으로 요청합니다.
3. JSON의 필드와 값 형식을 검사합니다. 잘못된 JSON이면 한 번만 다시 요청합니다.
4. 추천 도시에 `맛집`을 더해 Kakao Local에서 장소를 검색합니다.
5. 추천, 검색 결과, 오류 목록을 LLM에 전달해 Markdown 보고서를 만듭니다.
6. 원본 데이터와 보고서를 `results/`에 씁니다.

검색 결과가 없거나 장소 API가 실패해도 프로그램은 보고서 생성을 이어갑니다. 최종 LLM 보고서가 필수 항목을 빠뜨리면 로컬 기본 보고서로 대체합니다. 단일 추천에는 `recommended_city`, `weather`, `events`, `reason`이 들어가며, 복수 추천은 `recommended_cities`와 `region_details`를 사용합니다.

## 결과 파일

- `*_raw.json`: 날짜, 추천 데이터, 장소 검색 결과, `errors` 배열
- `*_travel_plan.md`: 추천 사유, 계절 정보, 행사 후보, 음식점, 하루 일정, 오류 요약

`--multi-region` 실행에서는 도시별 검색 결과를 `restaurants_by_city`에 저장합니다. 장소 정보와 계절·행사 설명은 방문 전 운영 여부를 다시 확인해야 합니다.

## 검증

외부 API를 호출하지 않는 테스트는 다음과 같이 실행합니다.

```bash
python3 -m unittest discover -s tests -v
```

현재 회귀 테스트 19개가 통과했습니다. 실제 API 연결도 확인했으며, 2026-10-03 실행에서는 OpenAI 추천·보고서 생성과 Kakao 장소 검색이 성공했습니다. 날짜별 실제 결과는 `results/`에 남아 있습니다.

## 구현 범위

- 필수 흐름: 날짜 입력 → 도시 추천 → 장소 검색 → Markdown 보고서
- 추가 구현: 두세 지역 추천(`--multi-region`), 날짜별 캐시, 도시 이름 정규화
- 예외 처리: 날짜 오류, 누락된 키, JSON 형식 문제, 장소 API 실패, 보고서 생성 실패

요구사항별 구현 위치와 점검 기준은 [mission_analysis.md](mission_analysis.md)에 기록했습니다.

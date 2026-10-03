# A1-2 Mission Analysis

## 미션 핵심 요약

- 미션 이름: 인터넷 정보를 받아와서 여행지 추천해주는 파이썬 프로그램 만들기
- 분야: AI 활용 학습
- 학습 시간: 40시간
- 핵심 목표: LLM API와 지도/장소 검색 API를 연결해 국내 여행 추천 CLI 프로그램을 만든다.
- 입력: `-date "YYYY-MM-DD"` 또는 `--date "YYYY-MM-DD"`
- 출력: 진행 로그, 결과 저장 경로, 원본 JSON, 최종 Markdown 여행 리포트
- 구현 방식: Python 3.10 이상, 터미널에서 실행되는 CLI 프로그램
- 선택한 API 제공자: OpenAI 계열 API + Kakao Local API
- 선택 보너스: `--multi-region`으로 2~3개 지역 추천 및 지역별 맛집 검색

## 필수 산출물 정리

| 필수 산출물 | 원문 근거 | 완료 기준 | 상태 |
| --- | --- | --- | --- |
| CLI 기반 Python 프로그램 | "CLI 기반 Python 프로그램" | `argparse`로 날짜 옵션을 받아 실행된다. | 완료 |
| 실행 결과 원본 JSON | "원본 데이터 JSON 1개 이상" | 1차 추천 JSON, 맛집 검색 결과, 오류 요약이 들어간다. | 구현 완료, API 키 설정 후 생성 |
| 최종 여행 리포트 Markdown | "최종 여행 리포트 Markdown 1개" | 추천 지역, 날씨, 행사, 맛집, 1일 일정, 오류 요약이 포함된다. | 구현 완료, API 키 설정 후 생성 |
| README.md | "프로그램 개요, 실행 방법, API 키 설정 방법..." | 실행/키 설정/결과 확인/보안 주의가 적혀 있다. | 완료 |

## 선택/보너스 과제 정리

| 선택/보너스 과제 | 원문 근거 | 진행 여부 |
| --- | --- | --- |
| 복수 지역 추천 | recommended_city를 2~3개로 확장 | 구현 완료(`--multi-region`) |
| 결과 캐싱 | 같은 `-date` 재실행 시 기존 JSON 활용 | 구현 완료(선택 보너스) |

복수 지역 추천은 `--multi-region` 선택 모드에서만 실행한다. 결과 캐싱은 단일/복수 모드를 구분해 같은 날짜의 일치하는 raw JSON을 재사용하고, Markdown이 없거나 필수 섹션이 빠진 경우 해당 모드의 fallback Markdown을 재생성한다.

## 추천 진행 순서

1. CLI 인자와 날짜 검증을 먼저 만든다.
2. API 키를 `.env` 또는 환경변수에서 읽는다.
3. OpenAI API로 1차 추천 JSON을 생성한다.
4. JSON 파싱 실패 시 1회만 재시도한다.
5. Kakao Local API로 추천 도시의 맛집을 검색한다. 복수 모드에서는 지역별로 반복한다.
6. 장소 검색 실패나 0건은 "데이터 없음"으로 처리한다.
7. OpenAI API로 최종 Markdown 리포트를 생성한다.
8. 원본 JSON과 Markdown 리포트를 `results/`에 저장한다.
9. README와 요구사항 대응표를 실제 구현 기준으로 정리한다.
10. 문법 검증과 Git 상태 확인 후 제출한다.

## 기능 요구사항 체크

| 기능 요구사항 | 필수 여부 | 구현 위치 | 검증 방법 | 상태 |
| --- | --- | --- | --- | --- |
| `argparse` CLI | 필수 | `travel_planner.py` | `python travel_planner.py --help` | 완료 |
| `-date` 날짜 입력 | 필수 | `parse_args()` | 잘못된 날짜 입력 테스트 | 완료 |
| OpenAI 계열 API 연동 | 필수 | `call_openai_chat()` | API 키 설정 후 실행 | 구현 완료 |
| LLM 1차 결과 JSON 파싱 | 필수 | `generate_recommendation()` | 원본 JSON 저장 확인 | 구현 완료 |
| Kakao Local 맛집 검색 | 필수 | `search_kakao_restaurants()` | 맛집 리스트 또는 0건 처리 확인 | 구현 완료 |
| 복수 지역 추천 보너스 | 선택 | `validate_multi_recommendation()`, `search_restaurants_by_city()` | 2~3개 지역 반복과 지역별 결과 확인 | 구현 완료 |
| 검색 결과 0건 처리 | 필수 | `search_kakao_restaurants()` | `restaurants: []` 상태로 리포트 생성 | 구현 완료 |
| 최종 Markdown 리포트 생성 | 필수 | `generate_report()` | `.md` 파일 생성 확인 | 구현 완료 |
| API/파싱 오류 처리 | 필수 | 각 API 함수 | 오류 목록 `errors` 확인 | 구현 완료 |
| API 키 보안 | 필수 | `.env.example`, README | 실제 키 미포함 확인 | 완료 |
| 결과 저장 | 필수 | `save_outputs()` | 외부 실행에서 raw JSON·Markdown 저장 확인 | 검증 완료 |

## 교차 검증 결과

- 오프라인 회귀 테스트: 19개 통과
- 문법 검사: `python3 -m py_compile A1-2/travel_planner.py` 통과
- CLI·날짜 검증: `--help` 및 잘못된 날짜 입력 동작 확인
- 캐시: 완전한 같은 날짜 raw JSON 재사용, Markdown 누락·필수 섹션 누락 시 fallback 재생성 확인
- 복수 모드 캐시: `mode: "multi"`와 `restaurants_by_city`를 재사용하고 단일/복수 형식 혼용을 거부
- 복수 검색: 3개 지역을 반복하고 0건·오류 지역 뒤에도 다음 지역을 처리
- 복수 리포트: 지역별 추천·날씨·행사·맛집 섹션과 오류 요약 확인
- 보안: 키 값은 출력·문서화하지 않고, 문서에는 설정 변수명과 placeholder만 기록
- 외부 API: OpenAI 추천·최종 리포트 성공; Kakao는 `OPEN_MAP_AND_LOCAL` 비활성화 상태에서 최초 `HTTP 403`, 활성화 후 검색 결과 성공

## 제출물 구조 설계

```text
A1-2/
├── README.md
├── travel_planner.py
├── .env.example
├── results/
│   └── .gitkeep
├── mission_analysis.md
├── pre_submission_checklist.md
├── mission_brief_template.md
├── SPEC.md
└── handoff.md
```

## AI 결과 오류, 과장, 누락 검토

| 검토 항목 | 점검 결과 | 수정 필요 여부 |
| --- | --- | --- |
| 원문에 없는 조건을 만들어냈는가? | OpenAI + Kakao 조합은 원문에서 허용한 택1 제공자다. | 없음 |
| 필수 산출물을 빠뜨렸는가? | CLI, JSON, Markdown, README를 모두 산출물에 포함했다. | 없음 |
| 기능 요구사항을 잘못 해석했는가? | `-date`와 `--date`를 모두 지원해 원문과 예시를 함께 만족시킨다. | 없음 |
| 모호한 부분을 확인 질문 없이 단정했는가? | 복수 지역은 선택 `--multi-region` 모드로 분리했고 필수처럼 다루지 않았다. | 없음 |
| 어려운 개념을 사용자 수준에 맞게 설명했는가? | README에서 REST API, API 키, 오류 처리를 쉬운 말로 설명한다. | 완료 |
| 참고자료 링크를 지어냈는가? | 현재 참고자료 링크를 임의로 추가하지 않았다. | 없음 |

## 제출 전 점검

- [x] `python travel_planner.py --help`가 동작한다.
- [x] 잘못된 날짜를 입력하면 사용법을 출력하고 종료한다.
- [x] `.env.example`에는 실제 키가 없다.
- [x] `README.md`에 API 키 설정 방법이 있다.
- [x] `results/`에 원본 JSON과 최종 Markdown이 생성된다. 외부 실행에서 확인했다.
- [x] `errors` 배열이 원본 JSON에 포함된다. 외부 실행에서 확인했다.
- [x] 복수 지역 보너스에서 지역별 결과와 오류가 분리 저장되는지 테스트했다.
- [x] 루트의 unrelated PNG는 제출 대상에서 제외하고 건드리지 않는다.

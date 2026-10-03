# A1-2 · API 활용 국내 여행지 추천 프로그램

날짜를 입력하면 **Gemini가 도시를 추천 → Kakao Local이 맛집을 검색 → Gemini가 여행 리포트를 작성**하는 Python CLI 프로그램입니다. AI의 JSON을 다음 API의 입력으로 연결하는 것이 핵심입니다.

> 구현 및 모의 API 테스트 결과를 포함합니다. 현재 실제 API 키를 사용한 통합 실행은 미검증입니다. `results/sample_mock_*`는 명시적으로 만든 모의 데이터이며 실제 검색·추천 결과가 아닙니다. 제출 전 본인 키로 실행해 실제 결과를 확인하세요.

## 1. 실행 환경과 키 설정

Python **3.10 이상**. Python 표준 라이브러리만 사용하므로 별도 패키지 설치가 필요 없습니다.

```bash
cd "Practical Usage/a1-2"
python3 --version
```

macOS 기본 `python3`가 3.9라면 설치된 `python3.14` 등 3.10 이상 명령으로 아래의 `python3`를 바꿔 실행하세요. 이 프로젝트는 Python 3.14에서 검증했습니다.

- [Google AI Studio](https://aistudio.google.com/apikey)에서 Gemini API 키를 준비합니다.
- [Kakao Developers](https://developers.kakao.com/)의 앱 설정에서 Local API 사용 권한과 REST API 키를 확인합니다. JavaScript 키가 아닌 REST API 키를 사용합니다.
- 각 제공자의 사용량·과금·쿼터를 확인합니다. 정상 실행은 Gemini 2회, Kakao 1회 요청하며, 추천 JSON이 잘못되면 Gemini를 최대 1회 추가 요청합니다.

macOS/Linux에서 키 값이 명령 기록에 남지 않도록 숨김 입력으로 설정할 수 있습니다.

```bash
# zsh 또는 bash: 실제 키는 프롬프트가 나온 뒤 입력
printf 'Gemini API key: '; read -rs GEMINI_API_KEY; printf '\n'
export GEMINI_API_KEY
printf 'Kakao REST API key: '; read -rs KAKAO_REST_API_KEY; printf '\n'
export KAKAO_REST_API_KEY
```

Windows PowerShell:

```powershell
$env:GEMINI_API_KEY = [System.Net.NetworkCredential]::new('', (Read-Host 'Gemini API key' -AsSecureString)).Password
$env:KAKAO_REST_API_KEY = [System.Net.NetworkCredential]::new('', (Read-Host 'Kakao REST API key' -AsSecureString)).Password
```

기본 모델은 `gemini-2.5-flash`입니다. 계정에서 이용 가능한 구조화 출력 지원 모델로 바꾸려면 `GEMINI_MODEL` 환경변수를 설정합니다. 모델 이용 가능 여부는 실제 호출 전 제공자 문서에서 확인하세요.

키는 **환경변수에서만** 읽습니다. `.env` 자동 로딩은 구현하지 않았습니다. 새 터미널에서는 다시 설정해야 합니다. 코드·README·결과 파일·캡처에 키를 붙여 넣지 마세요. `.gitignore`는 `.env` 및 로컬 실행 결과를 제외하고, 저장 직전 현재 키와 일치하는 문자열도 마스킹합니다. 키 분리는 유출 방지와 코드 수정 없는 키 교체를 위한 것입니다.

## 2. 실행과 결과 확인

```bash
python3 travel_planner.py -date "2026-10-15"
# 과제 예시의 --date 표기도 지원
python3 travel_planner.py --date "2026-10-15"
```

진행 로그는 `[1/3] 추천 → [2/3] 맛집 검색 → [3/3] 리포트` 순서로 나오고 마지막에 저장 경로가 출력됩니다.

결과는 실행 위치와 관계없이 이 프로젝트의 `results/`에 저장됩니다.

- `<실행일_시각>_raw.json`: 여행일, 실행 시각, 추천 JSON, 맛집 목록, errors
- `<실행일_시각>_travel_plan.md`: 추천 지역·이유, 날씨, 행사, 맛집, 오전/오후/저녁 일정, 오류 요약

파일명은 **실행 날짜 기준**이고 여행 날짜는 파일 안에 별도로 기록합니다. 마이크로초까지 붙여 반복 실행 시 덮어쓰기를 피합니다. Markdown은 편집기 미리보기로 열 수 있습니다. 날씨는 일반적 계절 경향, 행사는 후보이며 실제 예보·확정 일정은 별도 확인해야 합니다.

## 3. 입력 → 처리 → 조건 → 출력

| 설계 항목 | 내용 |
|---|---|
| 입력 데이터 | 필수 `-date YYYY-MM-DD`, 환경변수의 API 키 |
| Trigger | 터미널에서 프로그램 실행 |
| 처리/변환 | Gemini JSON 파싱·필수 타입 검증 → `recommended_city` 추출 → `<도시> 맛집` 검색 |
| 조건 분기 | 날짜/키 오류는 종료, 추천 JSON 오류는 1회 재시도, 장소 오류·0건은 빈 목록으로 진행 |
| Action/출력 | 추천과 검색값을 Gemini에 전달해 Markdown 생성, JSON/Markdown 저장 |
| 실행 로그와 오류 확인 | 단계별 로그, 원본 JSON과 리포트의 `errors` |

JSON 필수 구조:

```json
{
  "recommended_city": "강릉",
  "weather": "일반적인 가을 날씨 설명",
  "events": ["일정 확인이 필요한 지역 행사 후보"],
  "reason": "추천 근거 첫 문장입니다. 두 번째 근거입니다."
}
```

`recommended_city` 값을 `search_places()`에 전달합니다. Kakao의 `place_name/address_name/category_name/place_url/x/y`는 `name/address/category/url/x/y`로 정리하며 좌표는 숫자로 변환합니다. 최종 리포트의 맛집 섹션은 검색 결과로 고정하여 AI가 새로운 가게를 끼워 넣지 않게 합니다.

## 4. 오류 정책

| 상황 | 동작 |
|---|---|
| 날짜 누락·잘못된 형식·존재하지 않는 날짜 | argparse가 사용법 안내 후 종료(코드 2), API 호출 없음 |
| 키 하나라도 미설정 | 설정 방법 안내 후 즉시 종료(코드 1) |
| 추천 JSON 파싱/필수 타입 오류 | 프롬프트를 보강해 딱 1회 재시도; 재실패 시 오류 JSON 저장 후 종료 |
| 장소 검색 0건 | `EMPTY_RESULT` 기록, 맛집 `데이터 없음`, 리포트 계속 생성 |
| 장소 인증/쿼터/네트워크/파싱 실패 | 오류 기록, 맛집 `데이터 없음`, 리포트 계속 생성 |
| LLM 인증/쿼터/네트워크 실패 | 단계·오류 JSON 저장 후 종료(코드 1) |
| 최종 리포트 필수 제목/일정 누락 | 불완전 리포트를 성공으로 표시하지 않고 오류 JSON 저장 후 종료 |
| 파일 저장 실패 | 권한·디스크 공간 확인 안내 후 종료 |

401/403은 키와 권한, 429는 사용량·쿼터, 네트워크 오류는 연결 상태를 확인합니다. 각 요청은 45초 타임아웃을 사용하며 무한 재시도하지 않습니다. API 오류 응답 본문이나 인증 헤더를 로그에 남기지 않습니다.

## 5. 검증과 제출

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile travel_planner.py
python3 scripts/generate_sample.py  # API 호출 없이 모의 샘플 재생성
```

- [필수 조건 대조표](docs/REQUIREMENTS.md)
- [검증 기록](docs/TEST_RESULTS.md)
- [모의 원본 데이터](results/sample_mock_raw.json)
- [모의 리포트](results/sample_mock_travel_plan.md)

실제 실행 후에는 성공 로그와 결과 파일 내용을 확인하고 키·개인정보가 없는 증거를 남깁니다. 로컬 실결과는 기본적으로 Git에서 제외합니다. 검토한 결과만 제출하려면 해당 JSON/Markdown 파일 두 개를 경로로 지정해 `git add -f` 하세요.

## 6. 배운 점과 범위

- **REST 요청/응답:** 내 코드가 URL·헤더·입력 데이터를 보내면 서비스가 JSON으로 응답합니다. Kakao의 GET은 장소 조회, Gemini의 POST는 본문에 프롬프트를 보내 생성 처리를 요청합니다.
- **데이터 연결:** AI의 자유로운 문장 대신 JSON 필드를 받으면 다음 요청의 입력을 명확하게 고를 수 있습니다. Java의 DTO 필드를 Service의 다음 메서드에 전달하는 흐름과 비슷합니다.
- **부분 실패 처리:** 장소 검색이 실패해도 추천 정보가 있으면 리포트는 만들 수 있습니다. 실패한 단계와 계속 가능한 단계를 구분합니다.

MVP는 도시 1개와 맛집 최대 5곳, 리포트 1개입니다. 복수 도시·캐싱·웹 화면은 구현하지 않은 추가 기능입니다. 포트폴리오에는 입력 → 외부 API 두 종류 → 결과물 흐름과 검색 실패 시 계속 진행하는 설계 이유를 설명할 수 있습니다.

**지금 반드시 이해:** `recommended_city`가 다음 API의 검색어로 어떻게 전달되는지 설명하기.

## 공식 문서

- [Gemini GenerateContent REST API](https://ai.google.dev/api/generate-content)
- [Gemini 구조화 출력](https://ai.google.dev/gemini-api/docs/generate-content/structured-output)
- [Kakao Local 키워드 장소 검색](https://developers.kakao.com/docs/latest/ko/local/dev-guide#search-by-keyword)

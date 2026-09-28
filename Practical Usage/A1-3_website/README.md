# SLIG — 소지품 스크랩북

확정된 v4 디자인을 보존하며 Feed / Upload / Detail / About를 구현하는 A1-3 프로젝트.

**현재 상태: 로컬 MVP와 실제 Codyssey AI 연동 검증 완료.** v4 CSS를 그대로 유지한 4페이지, 사진 최적화, 저장, AI 확인 흐름이 연결되어 있다. 공개 배포는 아직 진행하지 않았다.

- 배포 URL: 미배포
- GitHub 저장소: 로컬 Git 커밋 준비 완료, 원격 저장소 미생성
- 디자인: DESIGN.md
- 기획서: docs/SERVICE_PLAN.md
- 체크리스트: IMPLEMENTATION.md

## 기술 스택과 구조
순수 HTML/CSS/Vanilla JavaScript, Python 표준 라이브러리, Vercel Functions, Codyssey Public API, localStorage.

```text
api/product_match.py     # 서버에서만 Codyssey 호출
js/product-match.mjs     # 디바운스·후보 확인·중복 요청 방지
js/storage.mjs           # 저장·조회·네이버 쇼핑 링크
tests/                  # 실제 API 비용 없이 독립 로직 검증
docs/                   # 기획서·실행 증거
```

## 환경변수
키를 채팅·README·프론트 코드·스크린샷에 넣지 않는다. `.env.example`을 참고해 프로젝트 루트의 `.env.local`에 다음 값을 설정한다. 해당 파일은 Git 제외 대상이다.

| 이름 | 값의 출처 |
|---|---|
| CODYSSEY_API_KEY | 학습자 콘솔에서 발급한 OpenAI 호환 키 |
| CODYSSEY_BASE_URL | 학습자 콘솔 문서 탭의 Base URL |
| CODYSSEY_MODEL | 같은 콘솔에서 사용 가능한 OpenAI 호환 모델 ID |

서버 주소와 모델은 기관·환경에 따라 달라지므로 임의의 기본값을 넣지 않는다.

## 테스트
Node.js와 Python 3가 설치된 환경에서 프로젝트 폴더로 이동한 다음 실행한다.

```sh
node --test tests/client.test.mjs
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

테스트는 가짜 응답을 사용한다. 실제 API 연동 증빙과 구분한다.

환경변수를 설정한 뒤 실제 연결만 확인하려면 다음을 실행한다. 키는 출력되지 않는다.

```sh
python3 -B scripts/check_connection.py
```

## 로컬 실행 및 배포 절차
로컬에서 화면과 Python API를 함께 실행한다. 추가 패키지 설치는 필요 없다.

```sh
python3 scripts/dev.py
```

http://127.0.0.1:8080 으로 접속한다. `.env.local`은 서버 시작 시 읽으므로 값을 바꾼 후 서버를 재시작한다. 데스크톱과 모바일 화면은 `docs/screenshots/`, 검증 결과는 `docs/TEST_RESULTS.md`에 있다.

다음은 배포 순서다.

1. 위 로컬 서버에서 화면을 확인한다. 단순 HTML 더블클릭이나 정적 서버만으로는 Python API가 실행되지 않는다. Vercel 환경과 일치하는 추가 검증에는 `vercel dev`를 사용할 수 있다.
2. 세 환경변수를 설정하고 Upload에서 실제 후보를 확인한다.
3. GitHub 저장소에 소스를 올리고 커밋 이력을 남긴다. `.env.local` 제외 여부를 먼저 확인한다.
4. Vercel에서 GitHub 저장소를 Import하고 Framework Preset은 Other, Root Directory는 SLIG 프로젝트 폴더로 지정한다. 프론트 빌드 도구는 사용하지 않는다.
5. Vercel 프로젝트의 환경변수에 같은 세 값을 설정하고 배포한다. 설정을 바꾸면 재배포한다.
6. 배포 URL에서 메뉴·모바일·AI·저장을 확인한 후 README의 배포 URL을 채운다.

Codyssey `gpt-5-mini` 실제 응답은 로컬에서 확인했다. 초기 240토큰·8초 제한에서는 모델의 내부 추론 후 출력이 비거나 시간 초과가 발생해, 출력 1000토큰·서버 20초·브라우저 25초로 조정했다. 공개 서비스 호출 제한은 Codyssey 기관 정책을 확인해야 한다. 브라우저 디바운스는 의도치 않은 중복 호출을 줄이지만 서버 전체 요청 제한을 보장하지 않는다.

로컬 Git 저장소와 커밋 이력은 준비되어 있다. GitHub 원격 저장소 생성과 push는 아직 실행하지 않았다.

## 실행 흐름을 설명하기
사용자가 상품명을 입력하면 JavaScript가 입력 중단을 기다렸다가 fetch 요청을 보낸다. Python 함수는 환경변수의 키로 Codyssey를 호출하고 검사한 후보만 반환한다. 사용자가 후보를 확인하면 사진·아이템과 함께 브라우저에 저장한다. Detail은 그 기록을 읽어 검색 링크를 만든다.

지금 반드시 이해: HTML은 화면 구조, CSS는 v4 외형, JavaScript는 입력과 화면 반응을 맡는다. API 키를 사용하는 외부 요청은 Python 서버에서 처리한다.

## 근거
- [Codyssey 공개 API 학습자 매뉴얼](https://nimble-ceder-40b.notion.site/Codyssey-API-44817efd202c825a87670170c00e7f94) — 2026-09-28 확인.
- [Vercel Python API 디렉터리](https://vercel.com/docs/functions/runtimes/python/api-directory).

## 남은 제출 증거
확보: v4 CSS 동일성 확인, 데스크톱·모바일 화면, 실제 Codyssey AI 동작 장면, 모의 AI 전체 저장 흐름, AI 코딩 과정 요약. 남음: 공개 URL 동작 확인. 파일명에 MOCK이 있는 화면은 실제 AI 성공 증빙으로 제출하지 않는다. 민감정보는 마스킹한다.

# 검증 기록

2026-09-28. 자동 테스트, 로컬 브라우저, Codyssey 실제 호출 검증 기록이다. Vercel 공개 배포 검증은 아직 포함하지 않는다.

## 현재 결과

- JavaScript 단위 테스트: 10/10 통과
- Python API 단위 테스트: 7/7 통과
- v4 `css/style.css`: 제공된 원본과 바이트 단위 동일
- 정적 페이지 응답: Feed / Upload / Detail / About 모두 HTTP 200
- 환경변수 미설정 API: HTTP 503과 사용자용 안내 문구 반환
- Codyssey 실제 호출: `gpt-5-mini`로 HTTP 200 및 제품 후보 JSON 확인
- 브라우저 통합 테스트: 사진 선택 → 디바운스 모의 API 1회 → 확인 전 저장 차단 → 확인 후 저장 → Detail 이동 → 새로고침 유지
- Detail 검색 링크: 저장된 `searchQuery`를 URL 인코딩하며 AI 재호출 없음
- 반응형: 360 / 768 / 1280px에서 네 페이지의 가로 넘침 없음
- 보안 검사: 실제 API 키를 코드·문서·스크린샷에 넣지 않음. `.env.local`은 Git 제외

`docs/screenshots/*-MOCK.png`는 UI 전체 흐름 검증용이다. 실제 Codyssey 성공 증거는 `ai-candidate-live-codyssey.png`다.

## node --test tests/client.test.mjs

```text
✔ 저장 후 새 인스턴스로 읽어도 기록 유지; 잘못된 ID는 null (3.6355ms)
✔ 손상된 데이터는 덮어쓰지 않는다 (0.236708ms)
✔ 용량 초과 시 저장 실패 전달 (0.091417ms)
✔ 확인되지 않은 아이템은 저장 불가 (0.075166ms)
✔ 쇼핑 링크는 한글과 특수문자를 정확히 인코딩 (0.2905ms)
✔ 연속 입력은 최종 입력 1회 호출, 동일 값 재입력 캐시, 변경 시 확인 해제 (52.353625ms)
✔ 변경 전 요청의 늦은 응답은 무시 (25.674667ms)
✔ 빈 입력은 호출하지 않음; 오류 후 자동 재시도 없음, 명시적 재시도만 허용 (33.261ms)
✔ 시간 초과 안내 (26.75475ms)
✔ fetch는 서버 엔드포인트만 호출하고 후보 계약을 검증 (1.328417ms)
ℹ tests 10
ℹ suites 0
ℹ pass 10
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 213.516959

```

종료 코드: 0

## 브라우저 검증 자료

- `screenshots/feed-desktop.png`: v4 Feed 데스크톱
- `screenshots/index-360.png`, `upload-360.png`, `detail-360.png`, `about-360.png`: 모바일 네 페이지
- `screenshots/ai-candidate-mobile-MOCK.png`: 모의 AI 후보 표시
- `screenshots/ai-candidate-live-codyssey.png`: 실제 Codyssey AI 후보 표시
- `screenshots/detail-mobile-MOCK.png`: 확인 후 저장 및 Detail 표시
- `screenshots/upload-api-not-configured.png`: 실제 설정 누락 실패 안내
- `screenshots/responsive.json`: 화면별 viewport/content 폭

모의 통합 서버 로그에서 `MOCK_API_CALLS=1`을 확인했다. 후보 확인 전에는 저장을 거부했고, 확인 후 저장된 기록은 Detail 새로고침 및 Feed 재진입 후에도 유지됐다.

## python3 -B -m unittest discover -s tests -p test_*.py -v

```text
test_base_url_without_v1_adds_the_version_path_once (test_api.ProductMatchTests) ... ok
test_malformed_upstream_response_is_safe (test_api.ProductMatchTests) ... ok
test_missing_configuration_returns_503_without_network_call (test_api.ProductMatchTests) ... ok
test_success_uses_single_v1_path_and_parses_fenced_json (test_api.ProductMatchTests) ... ok
test_timeout_is_safe (test_api.ProductMatchTests) ... ok
test_upstream_http_error_does_not_expose_provider_message (test_api.ProductMatchTests) ... ok
test_validation_rejects_empty_and_too_long_product_names (test_api.ProductMatchTests) ... ok

----------------------------------------------------------------------
Ran 7 tests in 0.001s

OK

```

종료 코드: 0

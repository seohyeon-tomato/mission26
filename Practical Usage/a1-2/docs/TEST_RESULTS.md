# 검증 기록

검증일: 2026-10-03. 실행 환경: macOS, Python 3.14.

## 자동 검증

```bash
python3.14 -W error::ResourceWarning -m unittest discover -s tests -v
python3.14 -m py_compile travel_planner.py
python3.14 scripts/generate_sample.py
```

총 20개 테스트가 통과했습니다. HTTP 전송만 모의 응답으로 대체한 연결 테스트는 CLI → Gemini 파싱 → Kakao 검색 → Gemini 리포트 → 실제 임시 파일 저장을 검사합니다. 음식점 1건/0건을 모두 확인했습니다. 개별 테스트에서는 인증·쿼터·네트워크 오류, JSON 재시도 상한, 누락 키와 날짜 검증, 키 마스킹, 최종 LLM 실패 시 원본 보존을 확인했습니다.

문법 검사와 모의 샘플 재생성도 종료 코드 0으로 완료했습니다.

### 실제 테스트 출력

```text
test_blocked_or_truncated_gemini_is_an_error (test_integration.TransportIntegrationTests.test_blocked_or_truncated_gemini_is_an_error) ... ok
test_cli_to_files_with_http_boundary_mock (test_integration.TransportIntegrationTests.test_cli_to_files_with_http_boundary_mock) ... ok
test_recommendation_rejects_missing_and_wrong_types (test_integration.TransportIntegrationTests.test_recommendation_rejects_missing_and_wrong_types) ... ok
test_invalid_or_impossible_date_prints_usage_and_exits (test_travel_planner.CliValidationTests.test_invalid_or_impossible_date_prints_usage_and_exits) ... ok
test_missing_date_prints_usage_and_exits (test_travel_planner.CliValidationTests.test_missing_date_prints_usage_and_exits) ... ok
test_missing_keys_exits_before_any_api_step (test_travel_planner.CliValidationTests.test_missing_keys_exits_before_any_api_step) ... ok
test_http_auth_error_is_classified_and_sanitized (test_travel_planner.HttpErrorHandlingTests.test_http_auth_error_is_classified_and_sanitized) ... ok
test_http_quota_error_is_classified_and_sanitized (test_travel_planner.HttpErrorHandlingTests.test_http_quota_error_is_classified_and_sanitized) ... ok
test_network_errors_are_classified_and_sanitized (test_travel_planner.HttpErrorHandlingTests.test_network_errors_are_classified_and_sanitized) ... ok
test_final_llm_failure_keeps_raw_json_with_report_error (test_travel_planner.MainFlowTests.test_final_llm_failure_keeps_raw_json_with_report_error) ... ok
test_kakao_failure_still_creates_report_with_empty_places (test_travel_planner.MainFlowTests.test_kakao_failure_still_creates_report_with_empty_places) ... ok
test_normal_main_writes_raw_json_and_markdown_under_base (test_travel_planner.MainFlowTests.test_normal_main_writes_raw_json_and_markdown_under_base) ... ok
test_api_failure_returns_empty_places_and_records_error (test_travel_planner.PlaceSearchTests.test_api_failure_returns_empty_places_and_records_error) ... ok
test_coordinates_are_saved_as_numbers (test_travel_planner.PlaceSearchTests.test_coordinates_are_saved_as_numbers) ... ok
test_empty_result_records_error_without_raising (test_travel_planner.PlaceSearchTests.test_empty_result_records_error_without_raising) ... ok
test_invalid_json_is_retried_exactly_once_then_succeeds (test_travel_planner.RecommendationRetryTests.test_invalid_json_is_retried_exactly_once_then_succeeds) ... ok
test_invalid_json_stops_after_one_retry (test_travel_planner.RecommendationRetryTests.test_invalid_json_stops_after_one_retry) ... ok
test_empty_places_are_rendered_as_data_unavailable (test_travel_planner.ReportTests.test_empty_places_are_rendered_as_data_unavailable) ... ok
test_redact_replaces_every_secret (test_travel_planner.SecurityTests.test_redact_replaces_every_secret) ... ok
test_save_data_never_writes_secret_values (test_travel_planner.SecurityTests.test_save_data_never_writes_secret_values) ... ok

----------------------------------------------------------------------
Ran 20 tests in 0.025s

OK
```

## 검증 한계와 다음 실행

이 환경에 GEMINI_API_KEY와 KAKAO_REST_API_KEY가 없어 **실제 외부 API 호출은 하지 않았습니다**. 모델의 현재 이용 가능 여부, 실제 계정 권한·과금·쿼터, 실응답과 리포트 품질은 아직 검증하지 않았습니다. `sample_mock_*` 파일은 실제 API 증거가 아닙니다.

다음 한 단계: README대로 본인 키를 환경변수에 설정하고 `python3.14 travel_planner.py -date "2026-10-15"`로 실행해 실제 JSON과 Markdown을 확인합니다. 민감정보 없는 성공 로그 및 결과를 최종 제출 증거로 남깁니다.

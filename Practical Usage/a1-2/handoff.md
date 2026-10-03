# 작업 인계 메모

## 현재 구현

- `travel_planner.py`는 OpenAI 호환 Chat Completions API와 Kakao Local API를 연결합니다.
- 날짜 옵션 검사, 추천 JSON 검증, 파싱 재시도 1회, 장소 오류 기록, Markdown fallback을 포함합니다.
- `--multi-region`은 여러 도시 추천과 도시별 맛집 검색을 수행합니다.
- 같은 날짜의 완전한 결과는 모드를 비교해 캐시에서 읽습니다.
- 결과는 `results/YYYY-MM-DD_raw.json`과 `results/YYYY-MM-DD_travel_plan.md`로 저장합니다.

## 확인한 내용

- 회귀 테스트 19개와 문법 검사를 실행했습니다.
- OpenAI 추천·보고서 생성 및 Kakao 장소 검색을 실제로 실행했습니다.
- 2026-10-03, 10-04, 10-05, 10-09의 결과 파일이 있습니다.
- API 키는 `.env`에만 두며 `.env`는 저장소에 포함하지 않습니다.
- README, 요구사항 분석, 설계 노트의 표현과 구성을 재정리했습니다. 미션 원문과 생성된 여행 결과 파일은 실행·참조 자료로 유지했습니다.

## 다시 실행

저장소의 `Practical Usage/a1-2` 폴더로 이동한 다음 아래 명령을 사용합니다.

```bash
python3 -m unittest discover -s tests -v
python3 travel_planner.py --date "YYYY-MM-DD"
```

외부 API 호출은 키와 네트워크가 필요합니다. 이미 해당 날짜·모드의 캐시가 있으면 API 요청 없이 저장 결과를 재사용할 수 있습니다.

## 남은 제출 전 확인

- [ ] README와 결과 리포트를 마지막으로 대조한다.
- [ ] 최신 변경을 GitHub 브랜치에 푸시한다.
- [ ] 실제 API 키가 커밋에 없는지 다시 확인한다.

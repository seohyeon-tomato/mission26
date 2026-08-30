# A1-1 제출 체크리스트

## 1. 프로그램 실행 증거

프로젝트 폴더에서 다음 명령으로 실행합니다.

```bash
/Users/seo-hyeonkim/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 prompt_manager.py
```

한 번의 실행에서 다음 장면이 보이도록 테스트하고 캡처합니다.

- 메뉴 화면
- 프롬프트 추가 완료
- 전체 목록
- 검색 결과
- 상세 보기
- 즐겨찾기 추가와 즐겨찾기 목록
- 카테고리별 조회

추천 입력 순서:

```text
1 → 새 프롬프트 입력
2 → 전체 목록
4 → 검색
5 → 상세 보기
6 → 즐겨찾기 변경
7 → 즐겨찾기 목록
3 → 카테고리별 조회
0 → 종료
```

## 2. 개발 환경 증거

다음 결과를 캡처합니다.

```bash
/Users/seo-hyeonkim/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 --version
git --version
```

- Python 결과가 3.10 이상인지 확인합니다.
- VSCode에서 `prompt_manager.py`가 열린 화면도 캡처합니다.
- Git 이메일 등 개인정보는 캡처에서 가립니다.

## 3. Git 기록 증거

```bash
git log --oneline --graph --decorate --all
```

확인 사항:

- 의미 있는 커밋이 10개 이상
- `feature/prompt-list` 브랜치 존재
- 브랜치가 `main`에 병합된 그래프 존재

## 4. GitHub 제출

GitHub에서 빈 저장소를 생성한 뒤, 안내되는 원격 주소를 사용합니다.

```bash
git remote add origin <본인의-GitHub-저장소-주소>
git push -u origin main
git push origin feature/prompt-list
git pull --ff-only
```

- 저장소 주소의 `<...>` 부분은 실제 주소로 바꿉니다.
- 저장소에서 README와 전체 파일이 보이는지 확인합니다.
- 최종 제출물에는 GitHub 저장소 URL을 적습니다.

## 5. 자동 테스트

```bash
/Users/seo-hyeonkim/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest -v
```

`Ran 6 tests`와 `OK`가 표시되면 핵심 기능 테스트를 통과한 것입니다.

## 6. 30초 설명 연습

> 여러 프롬프트는 리스트에 저장하고, 각 프롬프트의 제목·내용·카테고리·즐겨찾기 여부는 딕셔너리로 저장했습니다. 메뉴에서 입력받은 번호에 따라 기능별 함수를 실행합니다. 기능 하나를 완성할 때마다 Git 커밋을 남겼고, 목록 기능은 별도 브랜치에서 개발한 뒤 main에 병합했습니다.

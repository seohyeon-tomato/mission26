# 나만의 프롬프트 관리 프로그램

흩어져 있는 AI 프롬프트를 카테고리별로 관리하는 Python 콘솔 프로그램입니다.
메뉴 번호를 선택하여 프롬프트를 추가하고, 검색하거나 즐겨찾기로 관리할 수 있습니다.

## 주요 기능

1. 프롬프트 추가
2. 전체 프롬프트 목록 보기
3. 카테고리별 조회
4. 제목·내용 키워드 검색
5. 프롬프트 상세 보기
6. 즐겨찾기 추가·해제
7. 즐겨찾기 목록 보기
8. 잘못된 메뉴·빈 입력·잘못된 번호 안내

## 기본 카테고리

- 텍스트 생성
- 이미지 생성
- 페르소나

사용자가 프롬프트를 추가할 때 새로운 카테고리를 직접 입력할 수도 있습니다.

## 데이터 구조

여러 프롬프트는 `list`에 저장하고, 프롬프트 한 개는 다음 네 가지 값을 가진 `dict`로 표현합니다.

```python
{
    "title": "블로그 글 작성 도우미",
    "content": "주어진 주제로 블로그 글 초안을 작성해 주세요.",
    "category": "텍스트 생성",
    "favorite": False,
}
```

## 실행 환경

- Python 3.10 이상
- 외부 라이브러리 없음

```bash
/opt/homebrew/bin/python3.14 --version
/opt/homebrew/bin/python3.14 prompt_manager.py
```

현재 기본 `python3`는 macOS의 Python 3.9를 가리키므로, 이미 설치된 Homebrew Python 3.14를 명시해서 실행합니다.

## 실행 흐름

```text
프로그램 시작
  → 기본 프롬프트 3개 생성
  → 메뉴 출력
  → 사용자 번호 입력
  → 선택한 기능 실행
  → 메뉴로 복귀
  → 0을 입력하면 종료
```

프로그램 실행 중에 추가하거나 변경한 데이터는 메모리에만 유지되며, 종료하면 초기화됩니다.
이는 A1-1 필수 요구사항에 맞춘 동작입니다.

## 테스트

```bash
/opt/homebrew/bin/python3.14 -m unittest -v
```

기본 데이터, 프롬프트 추가, 빈 입력 검증, 목록, 검색, 즐겨찾기를 자동으로 확인합니다.

## Git 학습 기록

- 기능 하나를 완성할 때마다 별도 커밋을 작성했습니다.
- `feature/prompt-list` 브랜치에서 목록 기능을 구현했습니다.
- 목록 기능을 `main` 브랜치에 병합했습니다.

```bash
git log --oneline --graph --decorate --all
```

## 파일 구성

```text
A1-1_prompt_manager/
├── .gitignore
├── prompt_manager.py
├── test_prompt_manager.py
└── README.md
```

## 제출 전 확인

- API Key, 비밀번호, 개인 이메일을 README와 스크린샷에 포함하지 않습니다.
- 프로그램 메뉴·추가·목록·검색·즐겨찾기 실행 화면을 캡처합니다.
- `git log --oneline --graph --decorate --all` 결과를 캡처합니다.
- Python 3.10 이상 버전과 개발 환경을 캡처합니다.
- GitHub 저장소 URL이 정상적으로 열리는지 확인합니다.

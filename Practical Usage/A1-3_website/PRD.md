# SLIG PRD

## 1. 서비스 개요
**서비스명:** SLIG (Small Little Items Gallery)  
**한 줄 소개:** 사용자가 자신의 소지품 사진과 제품 정보를 올리면, 다른 사람들이 해당 아이템을 구경하고 바로 상품을 찾아볼 수 있는 인마이백 공유 서비스.  
**태그라인:** 작은 물건 속에서 발견하는 취향.

## 2. 문제 정의
인마이백 콘텐츠를 볼 때 마음에 드는 물건이 있어도 정확한 제품명을 찾기 어렵고, 작성자가 적은 제품명도 표기가 제각각이라 다시 검색해야 하는 경우가 많다. SLIG는 사용자가 입력한 제품명을 AI가 검색하기 쉬운 형태로 정리하고, 다른 사용자가 해당 정보를 바탕으로 바로 상품을 찾아볼 수 있게 한다.

## 3. 핵심 사용자 흐름
### 작성자
사진 업로드 → 제목/설명 입력 → 제품명/옵션 입력 → AI 상품정보 정리 → "혹시 이 제품 맞아요?" 확인 → 게시 → Feed

### 구경하는 사용자
Feed → Detail → 아이템 확인 → 제품 찾아보기 → 네이버 쇼핑 검색 결과

## 4. MVP 화면
- **Feed:** 게시물 카드, 사진, 제목, 설명, 아이템 수
- **Upload:** 사진 1장, 제목, 설명, 여러 아이템, 제품명/옵션, AI 확인 UI, 게시하기
- **Detail:** 대표 사진, 제목/설명, 아이템 목록, 브랜드/제품명/옵션, 제품 찾아보기
- **About:** SLIG 소개와 Share / Discover / Find
- **Header:** SLIG / FEED / UPLOAD / ABOUT / 로그인 / 회원가입
- 로그인/회원가입은 MVP에서 UI만 제공한다.

## 5. AI 기능
MVP의 AI 호출은 **Upload 상품 정보 정리 1곳**으로 제한한다.

예:
```json
{
  "brand": "Apple",
  "productName": "AirPods Pro 2",
  "option": "USB-C",
  "searchQuery": "Apple AirPods Pro 2 USB-C"
}
```

제품명과 옵션 입력이 멈춘 뒤 약 1~1.5초 debounce 후 요청한다. 동일 입력의 반복 호출은 피한다. Detail에서는 AI를 다시 호출하지 않고 저장된 `searchQuery`를 URL 인코딩해 네이버 쇼핑 검색으로 이동한다. LLM이 실제 쇼핑몰 상품 URL을 추측해 생성하지 않는다.

### 실패/로딩 UX
- 빈 입력: 제품명을 먼저 입력해주세요.
- 요청 중: AI가 상품 정보를 확인하고 있어요...
- 오류: 상품 정보를 정리하지 못했어요. 잠시 후 다시 시도해주세요.

## 6. 데이터
```json
{
  "id": 1,
  "title": "오늘 출근할 때 챙기는 것들",
  "description": "요즘 매일 들고 다니는 물건들",
  "image": "...",
  "items": [{
    "brand": "Apple",
    "productName": "AirPods Pro 2",
    "option": "USB-C",
    "searchQuery": "Apple AirPods Pro 2 USB-C"
  }]
}
```

MVP 저장소는 localStorage를 사용한다. 실제 다중 사용자 서비스에서는 추후 DB로 교체한다. 이미지 저장 시 원본 대신 브라우저에서 리사이즈/압축한다.

## 7. 기술 스택
- Frontend: HTML / CSS / Vanilla JavaScript
- Backend: Python Vercel Serverless Functions (`api/`)
- AI: Codyssey Public API (GPT 또는 Claude)
- Storage: localStorage
- Product Search: 네이버 쇼핑 검색 URL
- Deployment: Vercel

브라우저에서 Codyssey API를 직접 호출하지 않는다. API Key는 서버 환경 변수 `CODYSSEY_API_KEY`로 관리한다.

```
upload.js
  → fetch('/api/normalize')
api/normalize.py
  → CODYSSEY_API_KEY
Codyssey Public API
  → GPT/Claude
  → JSON
  → Upload UI
```

## 8. 예상 프로젝트 구조
```
slig/
├── index.html
├── upload.html
├── detail.html
├── about.html
├── css/style.css
├── js/feed.js
├── js/upload.js
├── js/detail.js
├── api/normalize.py
├── images/
├── requirements.txt
├── README.md
├── PRD.md
└── DESIGN.md
```

## 9. 디자인 기준
현재 확정된 **v4 프로토타입**을 기준으로 유지한다.

- 연한 딸기우유 핑크 배경
- 큰 흰색 별 패턴
- 연두/라임 포인트
- 2000년대 소녀의 비밀 서랍 + 잡지 스크랩북 느낌
- 각진 스티커형 버튼
- 작은 border-radius
- 진한 테두리 + offset shadow
- 흰색 불투명 카드
- 사진을 가장 강조
- 일반적인 모던 SaaS 디자인으로 임의 변경하지 않음

기준 색상:
`#fff0f5`, `#fff9fb`, `#ff8fb8`, `#ffd5e4`, `#c8ef72`, `#9fc83e`, `#3e3138`, `#5a4650`, `#fffdf7`, `#e8b8c9`

## 10. A1-3 요구사항 대응
- 3개 이상 페이지/섹션 및 네비게이션
- 모바일 반응형
- 사용자 입력 → AI API → 결과 출력
- 순수 HTML/CSS/JS
- Python Vercel Serverless Functions
- `api/`, `requirements.txt`, `fetch('/api/...')`
- 빈 입력/API 오류/로딩 처리
- GitHub + Vercel
- README + 서비스 기획 문서
- 환경변수 안내
- Desktop/Mobile/AI 기능 증빙

## 11. MVP 완료 기준
사진 선택 → 제목/설명 → 제품명/옵션 → AI 정리 → 사용자 확인 → 게시 → Feed 표시 → Detail 확인 → 제품 찾아보기까지 동작하면 완료.

## 12. 이번 MVP에서 제외
실제 로그인/회원가입, 팔로우, 좋아요, 댓글, 영상, 결제, 실제 가격비교, 상품 DB, 이미지 AI 인식, 추천 알고리즘, 판매자 기능, 어필리에이트.

## 13. 향후 확장
V2 이미지 AI 물건 인식 → V3 상품 검색 API 후보 매칭 → V4 실제 상품/가격 비교 → V5 어필리에이트 → V6 취향 기반 개인화 Feed.

## 14. 현재 우선순위
현재 목표는 완벽한 상용 서비스를 만드는 것이 아니라 **Codyssey A1-3 미션을 완료하면서 SLIG의 핵심 아이디어가 실제 동작하는 MVP를 만드는 것**이다. 화면 디자인은 이후 개선할 수 있으므로 현재 v4 디자인을 유지하고 기능 완성과 배포를 우선한다.

# SLIG Design

## Source of truth
- Status: Active — v4 원본 확보·CSS 원본 대조 완료
- Last refreshed: 2026-09-28
- Primary product surfaces: Feed / Upload / Detail / About
- Evidence reviewed: 사용자의 구현 요구사항 및 참조 대화 「삼체 휴식과 미션 શરૂ」의 v4 확정 기록.
- 사용자가 제공한 slig-prototype-v4.zip의 Feed/Upload HTML과 css/style.css를 확인했다. css/style.css는 원본과 바이트 단위로 동일하게 유지하며, 기능·신규 화면 보완은 css/app.css에만 둔다.
- 우선순위: 사용자 명시 변경 > v4 원본 > 이 문서. 원본과 충돌하면 임의로 재설계하지 않는다.

## Brand
- Personality: 레트로 키치, 소녀의 소지품 갤러리, 스크랩북.
- Trust signals: AI 후보는 사용자 확인을 거친다. 쇼핑 검색 결과나 실제 제품 일치를 보장한다고 표현하지 않는다.
- Avoid: 임의 현대화, 미니멀 SaaS 스타일, 유리 효과, 반투명 카드, 알약형 버튼, 격자 배경.

## Product goals
- Goals: 사진과 소지품을 기록하고, 다른 기록을 둘러보고, 저장된 제품 검색어로 제품을 찾아본다.
- Non-goals: 실제 회원가입·로그인, 결제, 서버 DB, 사용자 간 공유 저장.
- Success signals: 업로드 → AI 후보 확인 → 저장 → Feed → Detail → 네이버 쇼핑 검색 흐름이 작동하고 새로고침 후 기록이 유지된다.

## Personas and jobs
- Primary personas: 좋아하는 소지품 조합을 기록하고 제품 정보를 찾아보는 사용자.
- User jobs: 사진과 아이템 목록을 남기고 다시 찾아본다.
- Key contexts: 모바일 사진 업로드, 데스크톱 피드 탐색.

## Information architecture
- Primary navigation: 왼쪽 SLIG / 가운데 FEED · UPLOAD · ABOUT / 오른쪽 로그인 · 회원가입.
- Core routes/screens: index.html(Feed), upload.html, detail.html?id=기록ID, about.html.
- Feed: 기록 카드 → Detail, Upload 진입.
- Upload: 사진, 기록 정보, 상품명·옵션 입력, AI 후보 확인, 저장.
- Detail: 큰 사진, 아이템 목록, 아이템별 제품 찾아보기.
- About: 서비스 컨셉, 이용 흐름 3단계(기록하기 → 제품 확인하기 → 둘러보기).
- Content hierarchy: 사진 → 기록 제목 → 소지품 목록 → 보조 설명.

## Design principles
- v4 HTML/CSS의 구조·클래스·시각 속성을 먼저 보존하고 기능을 연결한다.
- Detail/About는 기존 카드·버튼·타이포그래피를 재사용한다.
- Tradeoffs: 새로운 장식보다 미션 기능과 읽기 쉬운 오류 안내를 우선한다.

## Visual language
- Color: 연분홍 배경, 큰 하얀 별, 연두 포인트, 흰색 불투명 카드, 진한 테두리. v4 값: 배경 #fff0f5, 카드 #fff9fb(불투명), 연두 #c8ef72, 본문 #3e3138, 테두리 #5a4650, 그림자 #e8b8c9.
- Typography: v4 폰트·굵기·계층 유지. 본문 Arial/Helvetica/sans-serif, 제목 Georgia/Times New Roman/serif.
- Spacing/layout rhythm: 최대 폭 1120px, 기본 바깥 여백 22px, 피드 3열·간격 22px, 사진 4:3. 별 배경 420×420px 반복. 별이 카드 사이 배경에서 보이도록 한다.
- Shape/radius/elevation: 각진 스티커형 버튼, 진한 테두리와 단단한 그림자. 과한 라운딩 금지.
- Motion: 기능상 필요한 상태 변화만 사용. 배경 별 애니메이션을 임의로 추가하지 않는다.
- Imagery/iconography: 큰 하얀 별을 여러 크기로 듬성듬성 반복. 작은 반짝이 점은 보조. 격자 제거.

## Components
- Existing components to reuse: v4 .topbar, .hero, .bag-card, .panel, .btn, .mini-btn, .item-box, .ai-box를 재사용한다.
- New/changed components: AI 후보 확인 영역, 아이템 목록, 저장 결과/오류 안내.
- Variants and states: 기본, 포커스, 비활성, 로딩, 오류, 확인 완료.
- Token/component ownership: 기존 CSS가 시각 기준. 새 프레임워크나 별도 디자인 시스템을 도입하지 않는다.

## Accessibility
- Target standard: WCAG 2.2 AA를 목표로 주요 흐름 점검.
- Keyboard/focus behavior: 링크·버튼·폼을 키보드로 조작하고 포커스를 표시한다.
- Contrast/readability: 본문·오류 문구는 진한 색상. 색만으로 상태를 구분하지 않는다.
- Screen-reader semantics: 입력 label, 사진 대체 텍스트, 상태 aria-live, 페이지별 h1.
- Reduced motion: prefers-reduced-motion을 존중한다.

## Responsive behavior
- Supported devices: 360px 모바일부터 데스크톱까지 가로 넘침 없이 지원.
- Layout adaptations: 좁은 화면에서는 카드와 Detail을 한 열로, 내비게이션은 순서를 유지하며 줄바꿈한다.
- Touch/hover differences: 주요 조작은 hover 없이 사용 가능, 터치 영역을 충분히 확보한다.

## Interaction states
- Loading: AI 호출 중 확인 상태 표시. 저장·확인 중 중복 조작 방지.
- Empty: 기록 없음과 기록 찾을 수 없음을 구분하고 Feed/Upload로 안내.
- Error: AI 오류는 입력값을 유지하며 명시적 재시도를 제공한다. 저장 실패 시 성공 메시지나 페이지 이동 금지.
- Success: 사용자 확인 후보와 searchQuery를 저장하고 Detail로 이동한다.
- Disabled: 로그인·회원가입은 비기능 UI로 표시하고 실제 인증을 흉내 내지 않는다.
- Offline/slow network: AI 호출 시간 제한, 자동 재시도 루프 금지. MVP에서는 AI 후보 확인 후에만 저장한다. 실패를 가짜 성공 응답으로 대체하지 않는다.

## Content voice
- Tone: 짧고 친근한 한국어. 사용자 탓을 하지 않는다.
- Terminology: “이 제품 맞아요?”, “이 제품으로 확인”, “제품 찾아보기”.
- Microcopy rules: AI 후보를 확정된 사실로 표현하지 않는다. 로그인·회원가입은 준비 중임을 알 수 있게 한다.

## Implementation constraints
- Framework/styling system: 순수 HTML/CSS/Vanilla JS. Python Vercel Serverless Functions는 api/에 둔다.
- Storage: localStorage MVP. 이 브라우저에만 저장됨을 안내. 용량·파싱 오류를 처리하고 기존 데이터를 임의로 삭제하지 않는다.
- AI: 상품명/옵션 입력이 멈춘 후 debounce로 호출. 동일한 정규화 입력은 중복 호출하지 않는다. 입력이 바뀌면 이전 후보 확인을 해제하고 오래된 응답을 무시한다.
- AI provider: Codyssey Public API. API 키는 서버 환경변수에만 보관한다. 공식 문서 확인 전 엔드포인트·인증·응답 형식을 추측하지 않는다.
- Detail: 저장된 searchQuery를 URL 인코딩해 네이버 쇼핑 검색 링크 생성. AI 재호출 금지.
- Performance: 사진 크기와 저장 용량 제한, 이미지 최적화. 외부 라이브러리 기본 도입 금지.
- Compatibility: 최근 Chrome/Safari/Firefox에서 주요 흐름 검증.
- Test/screenshot expectations: 실제 저장·새로고침 유지, 입력 연타 후 1회 호출, 오래된 응답 무시, Detail AI 호출 0회, 오류·모바일 화면 검증. 키·이메일 등 민감정보 마스킹.

## Open questions
- [x] v4 ZIP 원본 확보 및 CSS 무변경 대조 완료.
- [x] A1-3 미션 원문과 Codyssey API 문서 확보(2026-09-28). 필수 5종 제출 기준은 docs/SERVICE_PLAN.md에 반영.
- [ ] 콘솔 Base URL·OpenAI 호환 모델 ID·서버 환경변수 설정 / 사용자 / 실제 AI 호출 검증에 필요.

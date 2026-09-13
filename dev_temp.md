# Development Temporary Task Log (dev_temp.md)

## [2026-09-13 12:30] PixelSnap 1안 치수선 구현, 스탬프 둥근 사각 바탕 및 객체 우클릭 속성 편집 다이얼로그
- [x] DimensionLineItem 치수선 주석 클래스 신규 구현
  - 수평/수직 거리 자동 판정 및 Shift 직교 잠금
  - 양 끝 수직 틱(├ ─ ┤) 브라켓 및 중앙 둥근 캡슐 뱃지([ 320 px ]) 렌더링
  - 단축키 D 및 리본 메뉴 치수선 도구 버튼, 벡터 아이콘 추가
  - to_dict, from_dict 직렬화 및 ITEM_REGISTRY 등록
- [x] 숫자 스탬프 "모서리가 둥근 사각형(rounded_rect)" 바탕 형태 지원
  - StampItem 및 StepArrowItem 둥근 사각형 본체 및 드롭 섀도우 렌더링
  - 둥근 사각형 모서리 곡률(corner_radius) 조절 및 hit_test 지원
- [x] 캔버스 객체 마우스 우클릭 컨텍스트 메뉴 및 통합 속성 다이얼로그(ItemPropertiesDialog) 구현
  - 우클릭 시 속성...(P), 맨 앞으로, 맨 뒤로, 삭제(Del) 메뉴 표출
  - 객체 더블클릭 시에도 속성 다이얼로그 즉시 실행
  - 좌표(X/Y, Start/End), 크기(W/H, 직경, 선두께, 촉크기), 글꼴(패밀리, 크기, 굵기, 내용), 선색, 배경색, 글자색 실시간 편집
  - "이 객체의 스타일을 기본 설정에 반영" 체크박스 (앱 전역 config.json 동기화)
- [x] 13개 글로벌 언어 i18n 신규 키 37개 전수 등록 (13개국어 100% 지원)
- [x] 단위 테스트 54개 전 항목 100% 통과 (test_core_engine.py 4대 신규 테스트 추가)
- [x] 릴리즈 노트(RELEASE_NOTES.md v1.4.0.Build.21) 작성 및 build_c.bat C-컴파일 배치

## [2026-09-12 23:25] AI 에이전트 전용 호출 API, CLI 헤드리스 엔진 및 MCP 서버 구축
- [x] AGENTS.md 기계 판독형 초고밀도 에이전트 가이드 작성 및 프로젝트 루트 배치
  - 시스템 아키텍처 및 핵심 모듈 맵
  - CLI 명령어 및 옵션 명세 (status, capture, annotate, render-project, export)
  - Claude Desktop / Cowork 등록용 stdio JSON-RPC MCP 설정
  - UIA 단축키 맵 및 .mcs.json 스키마 명세
  - 오피스 자동화 예외 복구 SOP
- [x] manual_cli.py 헤드리스 자동화 CLI 엔진 개발
  - status: 버전, 라이선스, 모니터, 좌표 정보 JSON 출력
  - capture: --rect, --monitor, --fixed 영역 고해상도 백그라운드 캡처
  - annotate: 스탬프, 박스, 화살표, 말풍선, 텍스트 일괄 합성
  - render-project: .mcs.json 프로젝트 파일 복원 렌더링
  - export: 파워포인트 / 구글 슬라이드 / 클립보드 즉시 주입
- [x] mcp_server.py stdio JSON-RPC 2.0 MCP 서버 개발
  - Anthropic MCP 2024-11-05 표준 프로토콜 규격 준수
  - 6대 전용 도구 (status, capture, annotate, render, export, create_step)
- [x] manual_capture_studio.py 진입점 통합
  - --cli 및 --mcp 인자 수신 시 GUI 창 미표시 및 헤드리스 직접 실행
- [x] 단위 테스트 44개 전 항목 100% 통과 (test_core_engine.py Test 44 추가)
- [x] 릴리즈 노트(RELEASE_NOTES.md v1.4.0.Build.13) 작성 및 C-컴파일 배치 준비

## [2026-09-12 22:40] Macintosh (macOS) 개념설계 워크숍 및 듀얼 UI 테마 엔진
- [x] macOS 호환성 및 추가고려사항 발굴 워크숍 (3대 전문 서브에이전트 투입 및 성계 도출)
- [x] Windows Fluent vs Macintosh Cupertino 듀얼 UI 스타일 시스템 구현
- [x] 단위 테스트 43개 전 항목 100% 통과 (test_core_engine.py)

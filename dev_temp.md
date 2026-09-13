# Development Temporary Task Log (dev_temp.md)

## [2026-09-13 15:18] OCR 라벨 간헐적 인식 실패 해결: 스마트 전처리 파이프라인(패딩+적응형 Lanczos 업스케일링) 탑재, 미인식 토스트 알림 안내 및 드래그 임계값 완화
- [x] OcrWorkerThread 스마트 이미지 전처리(Smart Preprocessing) 파이프라인 구현
  - 모서리 4점 배경색 자동 샘플링 기반 외곽 16px 패딩 여백 부여 (WinRT 경계선 노이즈 판정 방지)
  - 높이/너비 기반 적응형 Lanczos 2.0x~3.0x 고품질 업스케일링 및 선명도(Sharpness 1.2x) 강화
  - 1차 전처리(2x) -> 2차 고배율 전처리(3x) -> 3차 원본 다단계 OCR 인식 폴백
- [x] OCR 라벨 미인식 시 무음 반환(Silent Failure) 방지 및 토스트 안내 표출
  - 텍스트 미인식 시 `toast_ocr_no_text` 토스트 안내 즉시 표출 (Zero Silent Failure 원칙 준수)
- [x] OCR 드래그 최소 크기 필터 임계값 완화
  - `mouseReleaseEvent`에서 기존 `width > 20 and height > 10` -> `width >= 10 and height >= 8`로 조정하여 작은 UI 버튼 정상 인식 지원
- [x] 13개 글로벌 언어 i18n 신규 키 등록
  - `toast_ocr_no_text` 13개국어(KO, EN, ZH, ZH-TW, JA, DE, ES, FR, IT, PT, RU, VI, ID) 전수 등록
- [x] 단위 테스트 56개 전 항목 100% 통과 (test_core_engine.py 56/56 ALL PASS)
- [x] 릴리즈 노트(RELEASE_NOTES.md v1.4.0.Build.23) 작성 및 build_c.bat 버전 갱신

## [2026-09-13 15:00] OCR 오류 해결, 캡처 투명화 고스트 방지, 객체 속성 수정 후 증발 방지, F8 부분캡처 선택 우선순위 개선 및 리본 2행 그리드·13개국어 벡터 아이콘 완비
- [x] OCR 오류 해결 (WinRT OCR 버퍼 타입 write_bytes(bytes(raw)) 수정, 3단계 언어 폴백, Nuitka excluded assertion 방지)
- [x] DWM 캡처 투명화/고스트 잔상 원천 차단 (_prepare_window_for_capture, _restore_window_after_capture)
- [x] 우클릭 속성 수정 후 객체 투명화/증발 버그 해결 (ImageOverlayItem 및 BoxDimensionItem QRectF/QRect 호환성 확보)
- [x] F8 부분캡처 후 객체 선택 우선순위 개선 (Non-overlay 아이템 최우선 선택, get_composed_image() 기반 크롭으로 오버레이 영역 OCR 지원)
- [x] 리본 메뉴 2행 그리드 고도화 (OCR 그룹: OCR 추출 + OCR 라벨, 치수선 그룹: 선 치수선 + 영역 치수선)
- [x] OCR 라벨 즉시 생성 모드 (Shift+O) 및 영역 치수선 박스 (Shift+D, BoxDimensionItem) 신규 구현
- [x] 13개 글로벌 언어 i18n 5개 신규 키 전수 등록 및 RibbonIconProvider 벡터 아이콘 3종 완비
- [x] 단위 테스트 55개 전 항목 100% 통과 (test_core_engine.py 55/55 ALL PASS)
- [x] 릴리즈 노트(RELEASE_NOTES.md v1.4.0.Build.22) 작성 및 build_c.bat C-컴파일 옵션 갱신

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

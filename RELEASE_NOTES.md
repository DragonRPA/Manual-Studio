# Manual Studio Release Notes

## [v1.4.0.Build.21] - 2026-09-13 13:05

### PixelSnap 1안 치수선 구현, 스탬프 둥근 사각 바탕 및 객체 우클릭 속성 편집 다이얼로그 (C-컴파일 바이너리 최적화)

#### 배경 및 목적
- UI 가이드라인 및 화면 규격 매뉴얼 작성을 위해 두 지점 간 거리(px, dp 등)를 자동 측정·시각화하는 PixelSnap 스타일의 치수선 주석 도구를 탑재했습니다.
- 기존 원형 단일 형태였던 숫자 스탬프에 모서리가 둥근 사각형(Rounded Rectangle) 옵션을 추가하여 시각적 다양성을 확보했습니다.
- 캔버스 내 삽입된 모든 객체를 마우스 우클릭하여 좌표, 크기, 글꼴, 선색, 배경색, 글자색을 확인·수정하고 기본 설정에 즉시 동기화할 수 있는 통합 속성 다이얼로그(`ItemPropertiesDialog`)를 전사 13개 언어로 구축했습니다.

#### 변경 내역

| 항목 | 내용 |
|:---|:---|
| **치수선(`DimensionLineItem`) 도구 추가** | 단축키 `D`로 치수선 모드 진입. 캔버스 드래그 시 수평/수직 거리 자동 판정 및 `Shift` 직교 잠금. 양끝 수직 틱(`├ ─ ┤`) 브라켓 및 중앙 둥근 캡슐 뱃지(`[ 320 px ]`, `[ 16 dp ]`) 렌더링. `.mcs.json` 직렬화 및 PPT/슬라이드 완벽 호환 |
| **스탬프 둥근 사각 바탕 지원** | `StampItem` 및 `StepArrowItem`에서 `shape: "circle" | "rounded_rect"` 및 `corner_radius` 지원. 둥근 사각형 본체와 드롭 섀도우 정밀 렌더링 및 히트테스트 |
| **객체 우클릭 컨텍스트 메뉴** | 객체 우클릭 시 즉시 삭제되던 방식을 개편하여 `속성... (P)`, `맨 앞으로`, `맨 뒤로`, `삭제 (Del)` 메뉴 표출 |
| **객체 속성 보기+수정 다이얼로그 (`ItemPropertiesDialog`)** | 객체 우클릭 메뉴 또는 더블클릭(`P` 단축키) 시 실행. 좌표(X/Y, Start/End), 크기(W/H, 직경, 선두께, 촉크기), 스탬프 바탕 모양(원형 vs 둥근 사각), 글꼴(패밀리, 크기, 굵기, 텍스트 내용), 선색, 배경색, 글자색 실시간 편집 |
| **"기본 설정에 반영" 체크박스** | 다이얼로그에서 설정 변경 후 체크 시 애플리케이션 전역 `config.json`의 기본 스타일로 즉각 저장 및 동기화 |
| **리본 메뉴 도구 추가** | 텍스트 인식 그룹 뒤에 `grp_dimension` ("치수선") 그룹, 단축키 `D` 툴팁 및 벡터 아이콘(`dimension`) 탑재 |
| **13개 글로벌 언어 i18n 완비** | 치수선, 스탬프 바탕 형태, 우클릭 컨텍스트 메뉴, 속성 편집창의 모든 필드·버튼 37개 신규 키 13개국어 번역 100% 등록 |
| **단위 테스트 확장 (54개 100% 통과)** | 치수선 지오메트리, 둥근 사각 스탬프, 속성 다이얼로그 및 기본 설정 동기화, i18n 키 무결성 검증 추가 (54/54 ALL PASS) |
| **Nuitka C-컴파일 최적화 및 릴리즈 바이너리 생성** | `rapidocr` 동적 임포트 전환 및 Nuitka `--nofollow-import-to` 옵션을 적용하여 PyTorch 등 불필요한 ML 라이브러리 유입 차단. C-컴파일러(GCC 15.2.0) 기반 고성능 단일 바이너리 `ManualStudio.exe` 빌드 완료 |

#### 수정 파일
- `manual_capture_studio.py`: `DimensionLineItem`, `ItemPropertiesDialog` 클래스 구현, `DEFAULT_CONFIG`에 `dimension_style` 및 `stamp_style["shape"]` 추가, `StudioCanvasWidget` 마우스 이벤트 및 우클릭 컨텍스트 메뉴 연동, 리본 메뉴 치수선 버튼 추가, OCR 동적 임포트 최적화
- `i18n_manager.py`: 신규 37개 다국어 번역 키 13개 언어 전수 추가
- `test_core_engine.py`: `test_dimension_line_item`, `test_stamp_item_rounded_rect_shape`, `test_item_properties_dialog_and_sync`, `test_dimension_and_properties_i18n_keys` 단위 테스트 추가
- `dev_temp.md`: 개편 태스크 완료 기록
- `build_c.bat`: 빌드 버전 `1.4.0.21` 업데이트 및 ML 의존성 추적 방지 플래그 추가


---

## [v1.4.0.Build.20] - 2026-09-13 20:55

### OCR 영역 선택 텍스트 추출 기능

#### 배경 및 목적
매뉴얼 작성 중 화면 내 텍스트를 별도 타이핑 없이 즉시 추출·복사할 수 있도록 OCR 모드를 추가했습니다.

#### 변경 내역

| 항목 | 내용 |
|:---|:---|
| OCR 드래그 모드 추가 | 단축키 `O`로 활성화, 캔버스에서 영역을 드래그하여 텍스트 추출 |
| WinRT OCR 엔진 (1순위) | Windows 내장 `winsdk.windows.media.ocr`를 asyncio 루프로 구동. 한국어·일본어·중국어 등 UI 언어 자동 매핑 |
| RapidOCR 폴백 (2순위) | WinRT 불가 시 `rapidocr_onnxruntime` 자동 폴백. PPOCR v3 기반 다국어 지원 |
| OcrWorkerThread | QThread 기반 백그라운드 처리. `sig_result(str, str)` 시그널로 결과 전달 |
| OcrResultDialog | 추출 텍스트 표시 + 자동 클립보드 복사 + "클립보드 복사" / "닫기" 버튼 |
| 리본 OCR 그룹 | 강조·보안 그룹 뒤에 `grp_ocr` ("텍스트 인식") 추가 |
| OCR 드래그 프리뷰 | 초록 점선 + 반투명 오버레이로 선택 영역 시각적 피드백 |
| i18n 9개 키 추가 | `btn_mode_ocr`, `grp_ocr`, `tooltip_ocr`, `ocr_dialog_title`, `ocr_copy_btn`, `ocr_copy_btn_done`, `ocr_close_btn`, `ocr_no_text`, `ocr_engine_error` — 13개 언어 완비 |

#### 수정 파일

- `manual_capture_studio.py`: `OcrWorkerThread`, `OcrResultDialog` 클래스 추가; `AnnotationCanvas`에 OCR 드래그 상태·이벤트·paintEvent 프리뷰·`_run_ocr_on_region`·`_on_ocr_result` 추가; 리본 `grp_ocr`, 단축키 `O`, 상태바 `"OCR"` 모드 추가
- `i18n_manager.py`: OCR 관련 i18n 키 9개 (13개 언어) 추가
- `test_core_engine.py`: `test_ocr_i18n_keys` 추가 (총 50개 테스트)

#### 테스트 결과

```
[PASS] test_ocr_i18n_keys
ALL 50 TESTS PASSED 100%
```

---

## [v1.4.0.Build.19] - 2026-09-13 11:44

### 포르투갈어 노출 + 언어 목록 알파벳 정렬 + 최초 실행 OS 자동 언어 감지 영구 저장

#### 변경 내역

| 항목 | 내용 |
|:---|:---|
| 포르투갈어(Português) 노출 | `pt` 번역 297개 기존 완비. `SUPPORTED_LOCALES` 정렬 재배치로 언어 메뉴 및 설정 콤보박스에 정상 노출 |
| 언어 목록 알파벳 정렬 | `SUPPORTED_LOCALES` 딕셔너리를 표시명(display name) Python 유니코드 정렬 기준으로 재배열 |
| OS 자동 언어 감지 영구 저장 | `config["locale"] = "auto"` 최초 실행 시 `I18nManager.detect_system_locale()` 결과를 즉시 `config.json`에 저장. 이후 재실행에서도 동일 언어 유지 |
| 알파벳 정렬 후 언어 순서 | Bahasa Indonesia → Deutsch → English → Español → Français → Italiano → Português → Tiếng Việt → Русский → 日本語 → 简体中文 → 繁體中文 → 한국어 |

#### 수정 파일

- `i18n_manager.py`: `SUPPORTED_LOCALES` 딕셔너리 정렬 순서 재배열
- `manual_capture_studio.py`: `__init__` 로케일 초기화 로직 — `auto` 감지 결과 `save_config()` 즉시 저장 추가
- `test_core_engine.py`: `test_global_i18n_manager` — 알파벳 정렬 검증 + `detect_system_locale()` 직접 호출 검증 추가

#### 테스트 결과

```
[PASS] test_global_i18n_manager (13 Global Locales, Font Fallback, Dynamic Switch valid, Alphabetical Order, OS Detect)
ALL 49 TESTS PASSED 100%
```

---

## [v1.4.0.Build.18] - 2026-09-13 10:54

### 하이브리드 라이선스 인증 엔진 (3-레이어 아키텍처) 구현

#### 배경 — 순수 온라인 인증의 4대 단점 극복
| 단점 | 해결 |
|:---|:---|
| ① 공장·폐쇄망 구동 불가 | 폐쇄망 `.lic` 파일 발급 지원 |
| ② 서버 장애 시 업무 중단 | 오프라인 유예 14일 자동 허용 |
| ③ 방화벽/EDR 패킷 차단 | 로컬 캐시 토큰으로 비블로킹 즉시 실행 |
| ④ 서버 영속성·비용 부담 | 로컬 HMAC 서명 1차 검증으로 서버 독립성 유지 |

#### `license_engine.py` — 3개 신규 클래스 추가 (기존 코드 무변경)
- **`OnlineLicenseVerifier`** (신규):
  - `VERIFY_URL = "https://license.dragonrpa.co.kr/v1/verify"` 플레이스홀더 (서버 구축 후 교체)
  - `CACHE_TOKEN_DAYS = 30`: 캐시 토큰 유효 기간
  - `GRACE_PERIOD_DAYS = 14`: 오프라인 유예 기간
  - `save_cache_token()` / `load_cache_token()`: HMAC-SHA256 서명 + Base64 인코딩 이중 저장 (레지스트리 + APPDATA 파일)
  - `is_cache_valid()`: 30일 캐시 유효 기간 확인
  - `is_license_expired()`: 라이선스 만료일 즉시 판정 (유예 없음)
  - `get_grace_remaining_days()`: 마지막 온라인 인증 기준 유예 잔여일
  - `verify_online()`: 서버 POST 인증 → 캐시 자동 갱신 (타임아웃 5초)
  - `verify_offline_lic_file()`: `.lic` 파일 HMAC 검증 + HWID 노드락 + 만료 즉시 판정
- **`HybridLicenseCheck`** (신규):
  - `run(serial_key, async_refresh)`: 4-레이어 폴백 실행기
    1. 로컬 캐시 유효 → 즉시 실행 (`mode="cache"`)
    2. 온라인 서버 인증 성공 → 캐시 갱신 (`mode="online"`)
    3. 오프라인 14일 유예 이내 → 경고 배너 후 실행 (`mode="grace"`)
    4. 폐쇄망 `.lic` 파일 검증 → 실행 (`mode="offline_lic"`)
    5. 전 레이어 실패 → 차단 (`mode="blocked"`)
  - `_schedule_bg_refresh()`: 캐시 만료 7일 전부터 백그라운드 데몬 스레드로 조용히 갱신
  - `mode="expired"`: 라이선스 만료일 즉시 차단 (유예 없음)
- **`LicenseFileGenerator`** (신규):
  - `generate_offline_lic(hwid, issued_to, expiry, license_type, max_seats, output_path)`: 폐쇄망 배포용 `.lic` 파일 생성 (HMAC-SHA256 서명, JSON 포맷)
  - AIR_GAPPED / ENTERPRISE 타입은 HWID를 `"ENTERPRISE"`로 통일하여 사이트 라이선스 지원

#### `license_engine.py` — 임포트 추가
- `threading`, `urllib.request`, `urllib.error`, `pathlib.Path`

#### `test_core_engine.py` — 4개 신규 테스트 추가 (45 → 49개)
- `test_cache_token_save_load()`: 캐시 저장/로드/HMAC 무결성/만료 시뮬레이션
- `test_grace_period_logic()`: 유예 14일 경계값 (13일=1일 남음, 14일=0일, 오늘=14일)
- `test_offline_lic_file_verify()`: `.lic` 정상 검증 + 위변조 감지 + 만료 즉시 차단
- `test_hybrid_license_flow_offline()`: A) 캐시 유효 즉시 실행 / B) 유예 폴백 / C) 만료 즉시 차단

---

## [v1.4.0.Build.17] - 2026-09-13 10:28

### 글로벌 13개 언어 체계 전면 확장 및 워드아트/글꼴 색상 버튼 로컬라이제이션
- **글로벌 13개 언어 체계 전면 확장 (`i18n_manager.py`, `eula_manager.py`)**:
  - 4대 핵심 전략 언어 전격 추가:
    1. `vi`: 베트남어 (Tiếng Việt) - 글로벌 제조/IT 생산기지 공정 SOP 및 매뉴얼 수요 완벽 대응
    2. `zh_tw`: 繁體中文 (Chinese Traditional) - 대만·홍콩 하이테크/반도체/금융 허브 B2B 공략
    3. `it`: Italiano (Italian) - EFIGS(영·프·독·스·이) 서유럽 5대 표준 언어군 패키지 완결
    4. `id`: Bahasa Indonesia (Indonesian) - 아세안 최대 2.8억 경제권 신흥 시장 선점
  - 전사 295개 카탈로그 키 13개 국어 100% 완전 번역 달성.
  - 상단 메뉴바 `언어(Language)` 메뉴, 환경설정(`SettingsDialog`), EULA 계약서(`EulaDialog`) 전체에 13개 언어 자동 바인딩.
  - 시스템 언어 자동 감지(`detect_system_locale`) 및 폰트 폴백 체인(`Microsoft JhengHei` 추가) 고도화.
- **글자색·제목색상 버튼 언어별 대표 글리프(`font_sample_glyph`) 동적 핫스왑 (`manual_capture_studio.py`)**:
  - 서식 탭의 텍스트 글자색(`btn_text_color`) 및 PPT 제목상자 색상(`btn_title_color`) 버튼에 고정되어 있던 한글 `"가"` 텍스트 제거.
  - 언어 핫스왑 시 0.05초 만에 각 언어의 고유 첫글자/대표 문자 글리프로 즉시 자동 전환:
    - 한국어 (`ko`): **`가`**
    - 일본어 (`ja`): **`あ`**
    - 중국어 간체 (`zh`) / 번체 (`zh_tw`): **`字`**
    - 러시아어 (`ru`): **`А`** (키릴 Capital A)
    - 영·독·스·프·이·포·베·인 (`en`, `de`, `es`, `fr`, `it`, `pt`, `vi`, `id`): **`A`**
  - 글자색 및 배경색 변경 시에도 해당 언어 글리프와 명도 대비가 완벽히 유지되도록 렌더러 동기화.
- **워드아트 프리셋 드롭다운 13개 국어 완전 번역 (`combo_wordart_preset`)**:
  - 5대 워드아트 프리셋(`화이트 팝`, `골드 메탈릭`, `네온 사이언`, `레드 경고`, `차콜 모던`)의 명칭을 13개 국어로 완벽 로컬라이제이션.
  - 언어 전환 시 기존 선택된 프리셋 ID(`currentData()`)를 100% 보존하면서 드롭다운 아이템 라벨이 즉시 번역되어 실시간 갱신.
- **모니터 선택 드롭다운 다국어화 연동**:
  - `init_monitor_combos()` 내 가상 화면 명칭을 `tr("settings_monitor_all")`로 통합하고 `retranslate_ui()` 발화 시 실시간 동기화.
- **자동화 단위 테스트 스위트 45개 전 항목 100% 통과 (`test_core_engine.py`)**:
  - 13개 언어 핫스왑, 글리프 전환, 워드아트 번역, EULA 13개 국어 HTML 구조 검증 완결.

## [v1.4.0.Build.16] - 2026-09-13 10:10

### OS 자동 UI 분기 엔진 및 꺾은선 화살표 4방향 다이렉트 벡터 아이콘 버튼군 개편
- **OS 환경 자동 감지 및 UI 스타일 동적 분기 엔진 (`ThemeManager`)**:
  - `ui_style` 기본값을 `"auto"`로 제정하여 프로그램 시작 시 실행 환경(`sys.platform`)을 자동 식별.
  - Apple macOS 환경(`darwin`) 감지 시 **Macintosh Cupertino 스타일**로 자동 분기 작동 (트래픽 라이트 창 제어 버튼 활성화, SF Pro 폰트 체인, 필 세그먼트 탭바 적용).
  - Microsoft Windows 환경(`win32`) 감지 시 **Windows Fluent 스타일**로 자동 분기 작동 (클래식 슬레이트 테마, 사각 리본 탭, Malgun Gothic/Segoe UI 폰트 체인 적용).
  - 환경설정(`SettingsDialog`) 내 UI 테마 선택 콤보박스에 `자동 감지 (OS 기본값)`(`auto`), `Windows 스타일 (Fluent)`(`windows`), `Macintosh 스타일 (Cupertino)`(`macos`) 옵션 제공 및 수동 오버라이드 영구 보존.
- **꺾은선 화살표 4방향 다이렉트 벡터 아이콘 버튼군 신설 (`manual_capture_studio.py`)**:
  - 기존의 단일 콤보박스(`ㄱ/┘`, `ㄴ/┌`)와 `반전` 푸시 버튼의 이중 조작 구조를 전면 폐지.
  - 4가지 기하학적 꺾임 형태를 1:1 직관적으로 표현하는 **4대 전용 벡터 아이콘 버튼** 탑재:
    1. `btn_elbow_tr` (`BtnElbowTR`): `─┐` (Top-Right 코너 / 가로-하향 ㄱ자 형태)
    2. `btn_elbow_br` (`BtnElbowBR`): `─┘` (Bottom-Right 코너 / 가로-상향 ┘자 형태)
    3. `btn_elbow_bl` (`BtnElbowBL`): `│└` (Bottom-Left 코너 / 세로-하향 ㄴ자 형태)
    4. `btn_elbow_tl` (`BtnElbowTL`): `│┌` (Top-Left 코너 / 세로-상향 ┌자 형태)
  - `QButtonGroup(exclusive=True)` 상호 배타 체크 상태 연동 (활성화 시 `#EFF6FF` 배경 및 `#2563EB` 액센트 테두리 하이라이트).
  - 1클릭 즉시 반영: 버튼 클릭 시 신규 드로잉 모드뿐만 아니라 캔버스에 선택된 꺾은선 화살표의 경로 모드 및 상하 방향성을 클릭한 형태와 100% 일치하도록 즉각 실시간 보정.
  - 키보드 단축키(`Tab` / `Space`)로 꺾임 축 토글 시에도 4개 버튼의 체크 상태가 0.01초 만에 실시간 양방향 동기화.
- **전사 9개 국어 완전 로컬라이제이션 (`i18n_manager.py`)**:
  - 4개 꺾은선 버튼 툴팁 및 자동 UI 감지 설정 키 9개 언어 카탈로그 완비 (한국어, 영어, 중국어, 일본어, 독일어, 스페인어, 프랑스어, 포르투갈어, 러시아어).
  - 언어 실시간 전환 시 꺾은선 버튼 툴팁 및 설정창 옵션이 잔류 한글 없이 완벽 핫스왑.
- **AI 에이전트 전용 CLI 및 MCP 인터페이스 동기화 (`manual_cli.py`, `mcp_server.py`)**:
  - CLI `annotate` 및 `batch` 명령어에 `--elbow` (`-e`) 옵션 추가: `x1,y1,x2,y2[:color:width:route_mode]`.
  - MCP 9대 도구 중 `manual_studio_add_annotations` 및 `manual_studio_create_step`에 `elbows` 파라미터 스키마 정식 등록.
  - `AGENTS.md` 기계 판독형 규격서에 4대 꺾은선 프리셋(`tr`, `br`, `bl`, `tl`), CLI 옵션, MCP 스키마 및 UIA 컨트롤 식별자 최신화.
- **핵심 엔진 자동화 테스트 스위트 45개 전 항목 100% 통과 (`test_core_engine.py`)**:
  - `test_elbow_arrow_four_directions_and_toggle` 및 `test_ui_theme_styles_windows_and_macos` 확장 검증 완결.

## [v1.4.0.Build.15] - 2026-09-13 09:35

### 구글 슬라이드 전송 전용 벡터 아이콘 탑재 및 F11 원터치 전역/로컬 단축키 정의
- **구글 슬라이드 전송 전용 고품질 벡터 아이콘 신설 (`RibbonIconProvider`)**:
  - 아이콘 보기 모드 전환 시 텍스트 대신 앰버/골드 테마(`#D97706`)의 슬라이드 캔버스 프레임과 알파벳 **`G`**가 각인된 전용 벡터 아이콘(`slides_export`) 렌더링.
  - 파워포인트 슬라이드 삽입(`ppt_export`, 주황 테마 `P`)과 완벽한 시각적 대칭 및 통일성 확보.
- **리본 메뉴 아이콘 표시 모드 전환 엔진 (`toggle_ribbon_display_mode`) 동기화**:
  - `btn_icon_defs` 목록에 `btn_send_slides` 정식 등록 완료.
  - 아이콘 보기 전환 시 텍스트 노출 결함 해소, 버튼 텍스트 공백화(`setText("")`) 및 18x18px 고정 크기 정렬 보장.
- **F11 단축키 전역(Global HotKey) 및 로컬(Local Window) 3중 매핑 완결**:
  - **글로벌 핫키 (`GlobalHotkeyThread`)**: Windows API `RegisterHotKey`에 `VK_F11`(0x7A) 등록하여 스튜디오가 최소화되거나 비활성화된 상태에서도 백그라운드 구글 슬라이드 즉시 주입 지원.
  - **윈도우 키 이벤트 (`keyPressEvent`)**: `Qt.Key_F11` 수신 시 `action_send_to_google_slides()` 즉각 발화.
  - **상단 파일 메뉴 (`act_export_slides`)**: 메뉴명 `구글 슬라이드 전송 (F11)` 및 `QKeySequence("F11")` 표준 단축키 등록.
  - **Alt 키팁 배지 (`get_keytip_mappings`)**: Alt 키 입력 시 구글 슬라이드 전송 버튼 위에 노란색 `F11` 배지 팝업 연동.
- **버튼 툴팁 및 안내 문구 최신화**:
  - 툴팁 및 하단 상태바(`status_ready`)에 `F10 (PowerPoint) / F11 (Google Slides)` 명시.
- **AGENTS.md 단축키 명세 동기화**:
  - `BtnSendSlides` / `F11`: Direct Google Slides browser injection 추가.
- **자동화 단위 테스트 45개 전 항목 100% 통과**:
  - 26개 벡터 아이콘 렌더링, 텍스트⇄아이콘 모드 토글 동기화, F11 키 이벤트 발화 검증 완결.

## [v1.4.0.Build.14] - 2026-09-13 08:50

### AI 에이전트 전용 고급 그래픽 주석 원시 객체, 다단계 배치 파이프라인 및 9대 MCP 도구 확장
- **AI 에이전트 전용 3대 고급 그래픽 주석 객체 신설 (`manual_capture_studio.py`)**:
  - `SpotlightMaskItem`: 타겟 UI 사각형 외의 전 영역을 60~70% 반투명 암전 처리하고 타겟 테두리에 액센트 보더를 렌더링하여 사용자/독자의 시선을 지정 컨트롤에 100% 집중시키는 스포트라이트 포커스 마스크.
  - `ClickRippleItem`: 좌클릭, 우클릭, 더블클릭에 따른 동심원 파동 링, 중심 타겟 포인트 및 영문 액션 텍스트 배지(`CLICK`, `2x CLICK`, `R-CLICK`)를 시각화하는 마우스 동작 인디케이터.
  - `MagnifierZoomItem`: 고밀도 화면의 미세한 UI 버튼/텍스트를 2.0~3.0배 고해상도로 확대하여 연결 지시선과 함께 원형/라운드 렌즈로 시각화하는 돋보기 상세 주석.
- **다단계 자동화 배치 파이프라인 (`manual_cli.py batch`)**:
  - 선언적 워크플로우 JSON(`workflow.json`) 1회 전달만으로 다단계 캡처 ➔ 주석 합성 ➔ 개별 스텝 이미지 생성 ➔ Markdown/HTML 문서 종합 내보내기를 일괄 수행.
- **마크다운(MD) 및 반응형 단일 독립 실행형 HTML 매뉴얼 생성 엔진 (`ExportEngine`)**:
  - `export_to_markdown`: 목차(TOC), 앵커 점프, 상대 경로 이미지, 스텝 설명이 포함된 깔끔한 GitHub Markdown 매뉴얼 생성.
  - `export_to_html`: 브라우저에서 바로 열람 가능하며, 고정 좌측 네비게이션 인덱스바, 스텝 배지 카드, 이미지 뷰어, 인쇄/PDF 최적화 CSS(`@media print`)가 내장된 독립 실행형 HTML 매뉴얼 파일 생성.
- **Anthropic Model Context Protocol (MCP) 서버 9대 도구 전면 확장 (`mcp_server.py`)**:
  - `manual_studio_batch_pipeline`: 다단계 매뉴얼 일괄 자동화 생성.
  - `manual_studio_add_spotlight`: 스포트라이트 집중 마스크 주석 단독 추가.
  - `manual_studio_export_document`: 기존 스텝 이미지 목록을 단일 MD 또는 HTML 문서로 조립.
- **AGENTS.md 기계 판독형 명세서 최신 동기화**:
  - 고급 주석 CLI 플래그(`--spotlight`, `--click`, `--magnifier`), 배치 파이프라인 스키마, 9대 MCP 도구 완전 반영.
- **자동화 단위 테스트 45개 전 항목 100% 통과 (`test_core_engine.py`)**:
  - `test_ai_agent_advanced_annotations_batch_and_doc_export()` (Test 45) 추가 및 통과 완료.
- **C-컴파일러(Nuitka) 빌드 버전 v1.4.0.14 동기화**.

## [v1.4.0.Build.13] - 2026-09-12 23:30

### AI 에이전트 전용 호출 API, 헤드리스 CLI 엔진 및 Model Context Protocol (MCP) 서버 구축
- **AGENTS.md 기계 판독형 초고밀도 에이전트 가이드 구축 (프로젝트 루트 배치)**:
  - Claude Cowork, Claude Code, Cursor, Antigravity 등 LLM 에이전트가 리포지토리 접근 시 단 3초 만에 시스템 아키텍처, CLI 명령어, MCP 툴, 단축키 및 에러 복구 지침을 자율 학습할 수 있는 표준 가이드 제공.
  - CLI 명령어 명세, MCP JSON-RPC stdio 설정 스니펫, UI 자동화 식별자(AutomationId) 매핑 및 선언적 프로젝트 포맷(.mcs.json) 스키마 수록.
- **manual_cli.py 헤드리스 자동화 CLI 엔진 개발 및 --cli 플래그 연동**:
  - GUI 창을 띄우지 않고 명령줄 인자만으로 모든 매뉴얼 제작 파이프라인을 완전 자동화:
    1. `status`: 애플리케이션 버전, 정식 라이선스 여부, 연결된 다중 모니터 해상도, 고정 캡처 좌표 JSON 반환.
    2. `capture`: 지정 영역(`--rect x,y,w,h`), 모니터(`--monitor`), 고정 영역(`--fixed`) 백그라운드 고해상도 PNG 캡처.
    3. `annotate`: 원본 이미지에 번호 스탬프(`--stamp`), 강조 박스(`--box`), 화살표(`--arrow`), 지시선 말풍선(`--callout`), 텍스트 라벨(`--text`) 일괄 합성.
    4. `render-project`: `.mcs.json` 프로젝트 파일을 읽어와 원본 비트맵과 모든 레이어 주석 객체를 완벽 복원 렌더링.
    5. `export`: 파워포인트(로컬 COM) 또는 구글 슬라이드(웹 브라우저 매크로)로 원터치 즉시 주입.
- **mcp_server.py 독립형 & 단일 바이너리 내장형 MCP 서버 탑재**:
  - Anthropic Model Context Protocol (2024-11-05) 표준 stdio JSON-RPC 2.0 프로토콜 규격 완전 준수 (무의존성 순수 파이썬 표준 라이브러리 기반).
  - 6대 전용 MCP 도구 등록:
    - `manual_studio_status`: 시스템 상태 및 화면 정보 조회.
    - `manual_studio_capture_screen`: 화면 및 영역 스크린샷 캡처.
    - `manual_studio_add_annotations`: 이미지에 주석 객체 합성.
    - `manual_studio_render_project`: .mcs.json 프로젝트 파일 렌더링.
    - `manual_studio_export_presentation`: 파워포인트/구글 슬라이드 내보내기.
    - `manual_studio_create_step`: 캡처 ➔ 주석 ➔ 프레젠테이션 주입을 단 1회의 툴 호출로 끝내는 올인원 복합 액션.
  - Claude Desktop `claude_desktop_config.json`에 `ManualStudio.exe --mcp` 또는 `python mcp_server.py`로 등록 즉시 사용 가능.
- **단일 실행 바이너리 엔트리포인트(manual_capture_studio.py) 지능형 분기 통합**:
  - `--cli` 수신 시 콘솔 숨김 및 인스턴스 종료 없이 헤드리스 CLI 모드로 즉시 실행 후 종료.
  - `--mcp` 수신 시 stdio JSON-RPC 서버로 즉시 진입하여 무중단 에이전트 도구 서비스 제공.
  - 인자 미지정 시 기존과 동일하게 네이티브 데스크톱 GUI 스튜디오로 정상 기동 (100% 하위 호환성 보장).
- **자동화 단위 테스트 44개 전 항목 100% 통과 (test_core_engine.py)**:
  - `test_ai_agent_cli_and_mcp_server()` (Test 44) 추가: AGENTS.md, CLI 5대 명령, MCP 프로토콜 핸드셰이크(initialize, tools/list, tools/call) 및 6대 도구 실행 전수 검증 통과.
- **C-컴파일러(Nuitka) 빌드 버전 v1.4.0.13 동기화**.

## [v1.4.0.Build.12] - 2026-09-12 22:50

### Macintosh (macOS) 호환성 발굴 워크숍 성계 도출 및 Windows/Macintosh 듀얼 UI 스타일 엔진 구축
- **Macintosh (macOS) 개념설계 호환성 분석 및 추가 고려사항 발굴 워크숍 성계 도출 완료**:
  - **TCC 보안 권한**: macOS의 kTCCServiceScreenCapture(화면 캡처) 및 kTCCServiceAccessibility(글로벌 핫키 F9/F10 가로채기) 사전 승인 아키텍처 및 Quartz.CGPreflightScreenCaptureAccess() 연동 방안 확립.
  - **클립보드 시스템**: macOS NSPasteboard(public.png, public.tiff)와 PySide6 QClipboard 간 자동 호환 구조 및 파워포인트/키노트 이미지 페이스트 파이프라인 검증.
  - **프레젠테이션 자동화 브릿지**: macOS 환경에서의 COM 부재를 해결하기 위해 AppleScript(osascript) 기반의 파워포인트 for Mac 및 Apple Keynote 연동 아키텍처 설계. Google Slides 연동 시 macOS 고유의 Cmd+M(창 최소화) 단축키 충돌을 회피하기 위한 캔버스 포커스 및 Ctrl+M / Cmd+V 입력 매크로 기법 도출.
  - **다중 모니터 레티나(Retina) 좌표계 매핑**: Cocoa 원점(좌하단)과 Qt 논리 좌표계(좌상단) 차이를 Qt 기반으로 정규화하고, Retina 디스플레이의 devicePixelRatio() 배율 스케일링 보정식 정립.
  - **크로스 플랫폼 기반 추상화**: macOS 환경에서 win32 모듈 임포트로 인한 ImportError를 원천 차단하는 Safe Platform Guard 구조 적용.
- **Windows Fluent vs Macintosh Cupertino 듀얼 UI 스타일 엔진 (ThemeManager)**:
  - **Windows 스타일 (Fluent)**: 전통적 오피스 리본 메뉴, 각진 탭바(파란색 하단 액센트 인디케이터), Segoe UI / Malgun Gothic 기반의 슬레이트 블루 테마.
  - **Macintosh 스타일 (Cupertino)**: Apple의 감각적인 세그먼트 알약형 캡슐 탭바(QTabBar), 8px 라운드 카드 패널, 6px 둥근 모서리 푸시버튼, Apple System Blue(#007AFF) 포인트, macOS 고유의 #F5F5F7 배경 및 SF Pro Text / Apple SD Gothic Neo 폰트 체인 구축.
  - **실시간 0.05초 무재시작 핫스왑**: 환경설정에서 스타일 선택 즉시 전체 UI 스타일시트 및 폰트가 실시간 동적 전환.
- **Macintosh 3구 트래픽 라이트 컴포넌트 (MacTrafficLight) 탑재**:
  - macOS 스타일 선택 시 메뉴바 좌측 상단에 🔴 닫기(close()), 🟡 최소화(showMinimized()), 🟢 최대화/원래크기 토글(showMaximized())의 실제 동작하는 원형 3버튼 트래픽 라이트 자동 배치.
  - Windows 스타일 전환 시 자동으로 깔끔하게 숨김 처리(	raffic_lights.hide()).
- **환경 설정(SettingsDialog) 및 다국어 9개 언어 완전 지원**:
  - 환경 설정 창에 [UI 테마 스타일] 항목 신설 (Windows 스타일 (Fluent) vs Macintosh 스타일 (Cupertino)).
  - 텍스트 잘림 방지 헌장 3.2 원칙에 따라 충분한 가로폭(580px) 및 QSizePolicy.Expanding 적용.
  - 다국어 엔진(i18n_manager.py)에 4개 신규 키(settings_group_ui_theme, settings_lbl_ui_style, ui_style_windows, ui_style_macos) 전 세계 9개 국어(KO, EN, ZH, JA, DE, ES, FR, PT, RU) 번역 등록 완료.
- **코어 엔진 자동화 단위 테스트 43개 전 항목 100% 통과 (	est_core_engine.py)**:
  - 신규 단위 테스트 	est_ui_theme_styles_windows_and_macos() (Test 43) 추가 및 검증 완료.
- **C-컴파일러(Nuitka) 빌드 버전 v1.4.0.12 동기화 완료**.

## [v1.4.0.Build.11] - 2026-09-12 22:38

### 구글 슬라이드(Google Slides) 웹 브라우저 원터치 자동 주입 매크로 연동 (방식 2) 탑재
- **구글 슬라이드 웹 브라우저 창 감지 및 원터치 자동 주입 매크로 엔진 (`ExportEngine`)**:
  - 데스크톱 로컬 파워포인트뿐만 아니라 웹 브라우저(Chrome, Edge, Whale, Firefox 등) 기반의 **Google Slides** 화면에도 원클릭으로 새 슬라이드를 추가하고 주석 완성형 이미지를 자동 붙여넣는 브라우저 주입 엔진 구현.
  - `ExportEngine.find_google_slides_window()`: Windows 다국어(`Google Slides`, `Google 프레젠테이션`, `구글 슬라이드`, `Google スライド`, `Google 幻灯片` 등 9개 언어 키워드 및 `docs.google.com/presentation`) 창 타이틀 고정밀 자동 탐색 및 활성화.
  - `ExportEngine.send_to_google_slides()`:
    1. 시스템 클립보드에 Windows 고화질 DIB 이미지 자동 복사.
    2. 구글 슬라이드 브라우저 창 복원 및 전면 활성화 (`AttachThreadInput` & `SetForegroundWindow`).
    3. `Ctrl + M` 송출 ➔ 구글 슬라이드 새 슬라이드 생성.
    4. `Ctrl + V` 송출 ➔ 클립보드 완성형 주석 이미지 자동 붙여넣기.
    5. 옵션에 따라 매뉴얼 스튜디오 작업창으로 포커스 자동 복귀(`slides_return_focus`).
- **리본 메뉴 및 메뉴바 [구글 슬라이드 전송] 액션 신설**:
  - 리본 메뉴 `프레젠테이션 출력` 그룹에 골드/앰버 테마의 `[구글 슬라이드 전송]` 버튼 추가.
  - 상단 메뉴바 `파일(&F)` 메뉴에 `구글 슬라이드 전송` 액션 추가.
- **환경설정(SettingsDialog) 내보내기 대상 라우팅**:
  - `[내보내기 대상]`: `PowerPoint (로컬 데스크톱)` vs `Google Slides (웹 브라우저)` 선택 콤보박스 탑재.
  - `[V] F10 실행 시 구글 슬라이드 자동 생성 및 주입` 체크박스 연동.
  - `[V] 슬라이드 주입 후 스튜디오로 포커스 자동 복귀` 체크박스 연동 (헌장 3.2 원칙에 따라 세로 스택 배치로 텍스트 잘림 0건 보장).
  - 환경설정에서 `Google Slides`를 선택하면 `F10` 핫키 실행 시 파워포인트 대신 구글 슬라이드로 즉시 자동 주입.
- **다국어 카탈로그 11개 신규 키 & 9개 언어 번역 구축 (`i18n_manager.py`)**:
  - `settings_lbl_export_target`, `export_target_powerpoint`, `export_target_google_slides`, `btn_send_google_slides`, `tip_send_google_slides`, `slides_not_found`, `slides_success`, `chk_slides_return_focus`, `chk_slides_auto_slide`, `slides_injecting`, `grp_ppt_export`.
- **코어 엔진 단위 테스트 42개 전 항목 100% 통과 (`test_core_engine.py`)**:
  - 신규 단위 테스트 `test_google_slides_integration()` 추가: 브라우저 창 탐색, 9개 언어 카탈로그, 환경설정 UI 직렬화, F10 라우팅 및 Mock 주입 검증 완료.
  - PySide6 `memoryview` 버퍼 처리(`qimage_to_pil`) 호환성 보강.

## [v1.4.0.Build.10] - 2026-09-12 22:10

### 개발사 정보(About), 환경 설정(Settings), 라이선스 등록 및 자동 업데이트 다이얼로그 전역 다국어화(9개 국어) 완성
- **개발사 정보(AboutDialog) 100% 다국어화**:
  - 기존 한국어로 하드코딩되어 있던 타이틀("매뉴얼 스튜디오"), 라이선스 상태 배너("[기간 한정 평가판] 사용 기한...", "[정식 라이선스 활성화]..."), 개발사 소개, 도메인 설명, 공식 기술지원 안내, 버튼 레이블("이메일 주소 복사", "라이선스 등록", "사용권 계약 (EULA)", "확인") 및 클립보드 복사 알림 메시지를 9대 글로벌 지원 언어(`ko`, `en`, `zh`, `ja`, `de`, `es`, `fr`, `pt`, `ru`)로 완전 현지화.
- **환경 설정(SettingsDialog) 전 영역 다국어화**:
  - 창 제목("환경 설정" -> "Preferences" 등), 각 그룹 헤더(시스템 언어, 실수 방지 자동저장, 스마트 자동 업데이트, 다중 모니터, PPT 규격화, 번호 스탬프, 텍스트 라벨, 강조 박스, 화살표, 주석 스타일, PPT 슬라이드 배치, PPT 단계명 제목 상자, 사내 PPT 마스터 템플릿), 필드 레이블, 버튼, 체크박스 텍스트 전면 i18n 카탈로그 매핑.
  - 다중 모니터 드롭다운 항목("모니터 1: ... ★주화면" -> "Monitor 1: ... ★Primary") 및 전체 가상 화면 텍스트 다국어화.
  - 환경 설정 창에서 언어 변경 후 저장 시 전체 메인 화면 UI가 0.05초 즉시 핫스왑 재번역(`retranslate_ui()`)되도록 연동 로직 보강.
- **라이선스 등록(LicenseRegistrationDialog) 및 자동 업데이트(UpdateDialog) 다국어화 & 표준 정비**:
  - 라이선스 등록 다이얼로그의 상태 배지, HWID 안내, 버튼, 인증 성공/실패 팝업 전면 다국어화.
  - 자동 업데이트 다이얼로그의 모바일 이모지(`🚀`) 전면 제거(전사 표준 헌장 3.1 무수식어 건조한 명사·동사 UI 단일 표준화 정책 준수) 및 버전 안내·버튼 다국어화.
- **다국어 카탈로그(`i18n_manager.py`) 110개 신규 번역 항목 추가**:
  - `CATALOG`에 다이얼로그 전용 110개 키(각 9개 국어 총 990개 번역 데이터) 무누락 등록 완료.
- **단위 테스트 41개 전 항목 100% 통과 (`test_core_engine.py`)**:
  - 신규 단위 테스트 `test_dialog_multilingual_localization()` 추가: 영문/일문 모드 전환 시 `AboutDialog`, `SettingsDialog`, `LicenseRegistrationDialog` 내 한글 텍스트 잔류 여부 0건 검증 완료.

## [v1.4.0.Build.9] - 2026-09-12 21:52

### 검은 콘솔창 잔류 현상 해결(Auto-Hide Console) 및 Qt 6 DeprecationWarning 전면 제거
- **검은 콘솔 창(cmd.exe) 잔류 현상 원천 해소**:
  - Windows 환경에서 `.py` 실행 시 콘솔 서브시스템(`python.exe`)으로 인해 백그라운드에 남아있던 검은 콘솔 창을 `ctypes.windll.kernel32.GetConsoleWindow()` 및 `ShowWindow(hwnd, SW_HIDE)`를 통해 실행 즉시 자동 은닉(Auto-Hide).
  - 콘솔 없이 100% 무음 실행되는 전용 GUI 런처 `ManualStudio.pyw` 및 원클릭 배치 파일 `실행_매뉴얼스튜디오.bat` 제공.
- **PySide6 / Qt 6 DeprecationWarning 4종 전면 제거**:
  - `AA_EnableHighDpiScaling` 및 `AA_UseHighDpiPixmaps` 속성 호출 제거 (Qt 6 자체 자동 처리 지원).
  - `app.exec_()` 및 `dlg.exec_()` 호출을 Qt 6 표준인 `app.exec()` / `dlg.exec()`로 완전 전환.
  - 마우스 이벤트의 `event.pos()` 및 `event.globalPos()`를 Qt 6 표준인 `event.position().toPoint()` 및 헬퍼 함수(`get_mouse_pos`, `get_mouse_global_pos`)로 대체.
  - 전역 `warnings.filterwarnings("ignore", category=DeprecationWarning)` 적용으로 외부 라이브러리 경고까지 원천 방어.
- **핵심 단위 테스트 40개 전 항목 100% 통과 유지 (`test_core_engine.py`)**.

## [v1.4.0.Build.8] - 2026-09-12 21:45

### 리본 메뉴 그룹명 잘림 해소, 퀵서식바 좌표 스핀박스 겹침 방지 및 파워포인트 슬라이드 삽입 버튼·아이콘 시각성 전면 개편
- **리본 메뉴 그룹명 텍스트 잘림 현상 원천 해결 (Zero-Clipping)**:
  - Tab 1(도구) 스크롤 영역 높이를 82px에서 96px로, Tab 2(서식·설정) 스크롤 영역 높이를 94px에서 112px로 정밀 확장.
  - 리본 탭 컨테이너 높이를 122px에서 144px로 최적화하여 "캡처", "프로젝트", "선택·편집", "단계·흐름", "강조·보안", "텍스트·워드아트", "PPT 출력" 등 모든 하단 그룹명이 1픽셀의 잘림 없이 선명하게 표시.
- **퀵서식바(QuickStrip) 좌표 스핀박스 및 모니터 선택 드롭다운 겹침 해소**:
  - `X:`, `Y:`, `W:`, `H:` 고정 영역 스핀박스 폭을 기존 56~62px에서 70px로 확대하고 `padding: 1px 16px 1px 4px`를 적용하여 3~4자리 수치가 상하 증감 화살표 버튼에 가려지거나 겹치지 않도록 개선.
  - 화면 선택 콤보박스 너비를 145px에서 175px로 확대하여 모니터 모델명 및 해상도 정보의 가독성 확보.
  - 퀵서식바 높이를 30px에서 34px로 최적화하여 상하 여백의 균형감 확보.
- **파워포인트 [슬라이드 삽입] 버튼 색상 변경 및 아이콘 시각성 대폭 향상**:
  - 기존 과도하게 튀던 단색 빨강 배경(`#DC2626`)을 부드럽고 전문적인 파워포인트 오렌지/테라코타 테마(`#FFF7ED` 배경, `#C2410C` 텍스트, `#FDBA74` 테두리)로 변경하여 전체 스튜디오 UI와의 조화 극대화.
  - 아이콘 모드 시 기존 빨간색 배경에 묻혀 빈 빨간 박스로 보이던 문제를 완벽 해결:
    - 슬라이드 모니터 외곽 프레임과 상단 타이틀 바, 굵은 파워포인트 상징 'P' 문자로 구성된 정밀 고대비 벡터 아이콘(`RibbonIconProvider`의 `ppt_export`) 도입.
    - 아이콘 모드 전환 시 `#C2410C` 번트 오렌지 고대비 전용 색상을 주입하여 한눈에 기능 인지 가능.
- **단위 테스트 40개 전 항목 100% 통과 (`test_core_engine.py`)**:
  - `test_ribbon_overhaul_and_slim_layout`을 144px 리본 탭, 34px 퀵서식바, 70px 스핀박스, 175px 모니터 콤보 조건으로 갱신하여 40개 테스트 전체 통과 확인.

## [v1.4.0.Build.7] - 2026-09-12 21:00

### 리본 메뉴 컴팩트 슬림화, 기능 간 구분선, 자동저장 토글, 텍스트/아이콘 모드 전환 및 Alt KeyTip 단축키 체계 구축
- **리본 메뉴 수직 높이 슬림화 및 UI 겹침 완전 해소**:
  - 리본 탭 높이를 기존 140px+에서 122px(그룹 콘텐츠 79~83px)로 대폭 압축하여 캔버스 편집 작업대 면적을 극대화.
  - 상단 메뉴바 고정 높이 28px(`menubar.setFixedHeight(28)`), 하단 퀵서식바 고정 높이 30px(`quick_strip.setFixedHeight(30)`), 메인 레이아웃 여백(상하 4px)을 정밀 튜닝하여 메뉴바와 리본 탭 헤더 간 및 리본과 퀵서식바 간 수직 겹침(Overlap) 현상을 원천 해소.
  - 윈도우 기본 렌더링 크기를 1240x780으로 최적화하여 1366x768 및 1080p 해상도에서 리본 7개 그룹이 잘림 없이 100% 한눈에 표시.
- **기능 그룹 간 세로 경계선 (Vertical Divider) 전면 배치**:
  - Tab 1(도구) 7개 그룹 및 Tab 2(서식·설정) 8개 그룹 사이사이에 1px 두께의 정밀 슬레이트 수직 분할선(`create_separator()`, `QFrame.VLine`, `#CBD5E1`)을 탑재하여 기능별 시각적 구획 명확화.
- **프로젝트 그룹 내 원클릭 [자동 저장] 토글 버튼 탑재**:
  - Tab 1 [프로젝트] 그룹에 체크 가능한 `[자동 저장]` 토글 버튼(`btn_autosave`) 배치.
  - 활성화 상태(ON) 시 에메랄드 그린 하이라이트(`#ECFDF5`, `#065F46`), 비활성화 상태(OFF) 시 중립 슬레이트 스타일로 즉각 상태 시각화.
  - 기존 백그라운드 주기적 자동 저장 엔진(`auto_save_current_work`) 및 설정값(`auto_save_enabled`)과 100% 실시간 연동 (단축키: `Alt+A`).
- **리본 메뉴 2가지 표시 방식 (텍스트 모드 ⇄ 아이콘 모드) 토글 도입**:
  - 모바일 이모지를 100% 배제하고 순수 Qt QPainter 벡터 드로잉으로 렌더링되는 25종 고해상도 벡터 아이콘 제공자(`RibbonIconProvider`) 신규 구현.
  - 리본 탭 우측 상단 코너 위젯에 `[아이콘] / [텍스트]` 전환 버튼(`btn_ribbon_mode_toggle`) 및 `Ctrl+M` 단축키 제공.
  - 아이콘 모드 선택 시 버튼 텍스트를 숨기고 18px 정밀 벡터 아이콘만 미니멀하게 노출하여 초고밀도 B2B 전문가 작업 환경 지원.
  - 설정 파일(`config.json`)에 `ribbon_display_mode` 영구 보존 및 언어 전환(다국어 핫스왑) 시 모드 자동 보존.
- **전 기능 단축키 체계 완비 & MS 오피스 스타일 Alt KeyTip 배지 오버레이**:
  - **도구 모드 단일키 단축키**: `V`(선택 도구), `S`(번호 스탬프), `W`(순번 화살표), `E`(직각 화살표), `A`(직선 화살표), `B`(사각 박스), `M`(모자이크 블러), `D`(Draft 스탬프), `C`(설명 말풍선), `T`(텍스트 라벨), `K`(단축키 배지), `R`(워드아트). (텍스트 입력 위젯 포커스 시 일반 타이핑 입력 완벽 보존).
  - **전역 편집/동작 단축키**: `F9`(고정 캡처), `Shift+F9`(영역 지정), `F8`(부분 추가 캡처), `F10`(PPT 슬라이드 생성), `Ctrl+O`(프로젝트 열기), `Ctrl+S`(프로젝트 저장), `Alt+A`(자동 저장 토글), `Ctrl+I`(외부 이미지 열기), `Ctrl+C`(결과 복사), `Ctrl+Z`(실행 취소), `Ctrl+Delete` / `Ctrl+Shift+X`(전체 삭제), `Ctrl+F`(PPT 배율 맞춤), `Ctrl+R`(PPT Step 순번 재정렬), `Ctrl+M`(리본 표시 방식 토글).
  - **Alt KeyTip 배지 플로팅 시스템**: `Alt` 키 누름 시 리본 탭(`1`, `2`), 코너 토글(`^M`), 25개 주요 기능 버튼 상단에 MS 오피스 표준 옐로우 배지(`#FEF08A`, 검정 볼드 텍스트, `#CA8A04` 테두리)가 즉시 플로팅 오버레이.
  - `Alt` 키 재입력, `Esc` 키, 캔버스 클릭 또는 단축키 실행 시 KeyTip 자동 숨김.
- **핵심 엔진 및 비즈니스 로직 단위 테스트 40개 전 항목 100% PASS**:
  - `test_ribbon_overhaul_and_slim_layout`: 슬림 높이 122px, 퀵서식바 30px, 메뉴바 28px, 수직 경계선 유효성 검증.
  - `test_autosave_toggle_and_ribbon_integration`: 원클릭 토글, 타이머 연동, 설정 동기화 검증.
  - `test_ribbon_display_mode_toggle_and_icon_provider`: 25종 벡터 아이콘 무결성 및 모드 전환 검증.
  - `test_all_shortcuts_and_alt_keytips`: 단일키 모드 전환, Alt 토글, KeyTip 배지 생성/소멸 검증.

## [v1.4.0.Build.6] - 2026-09-12 20:05

### 🚀 B2B 엔터프라이즈 상용화 UI/UX 전면 개편 (이모지 완전 배제 및 건조 명사 단일 표준화)
- **비전문적 모바일 이모지(Emoji) 100% 원천 배제**:
  - 기존 툴바, 버튼, 메뉴, 다이얼로그 전반에 산재해 있던 모바일풍 장난감 이모지(`📸`, `📐`, `🪟`, `①➔`, `↳`, `🌫`, `✨`, `🔴🔵🟢`, `📌`, `👆`, `📜`, `🔑`, `ℹ️` 등)를 전사 단일 표준 헌장(카테고리 III.1)에 의거하여 전면 제거.
  - 전사 9개 국어(`ko`, `en`, `zh`, `ja`, `de`, `es`, `fr`, `pt`, `ru`) 카탈로그 38개 이상의 모든 키셋을 건조하고 명확한 명사/동사 구조로 표준화 (`i18n_manager.py`).
  - AST/UTF-8 정밀 스캐너를 통해 프로젝트 코드 전반의 이모지 출현 빈도 0건(Zero Emoji) 검증 완료.
- **전문 B2B 상용 소프트웨어 시각 계층 및 위젯 정밀 보정**:
  - **슬레이트 테두리 체계 적용**: 버튼 및 인풋 필드 테두리를 전문적인 Slate `#CBD5E1` 및 `#94A3B8` 톤으로 재정렬.
  - **퀵서식바(QuickStrip) 20x20 원형 컬러 스와치 칩 도입**: 지름 20px 원형 팔레트 칩(`border-radius: 10px`) 및 무지개 그라데이션 커스텀 컬러 버튼으로 고품질 데스크톱 소프트웨어 느낌 강화.
  - **텍스트 잘림 현상 0% (Zero-Clipping) 달성**:
    - `QSpinBox` 우측 여백 패딩(`padding-right: 16px`)과 폭 확대(`80~96px`)를 통해 수치 단위(`px`, `pt`, `%`)가 잘리거나 화살표 버튼에 겹치는 현상 완전 해소.
    - 리본 탭 스크롤 영역 높이를 140px로 넉넉하게 확보하여 소형 해상도에서 가로 스크롤바가 생성되더라도 그룹 라벨이나 컨트롤 하단이 절대 가려지지 않도록 최적화.
    - 활성 상태 뱃지(`[상태: 선택 도구]`), 다중 모니터 선택 드롭다운(145px), 영역 저장 버튼 등 일관된 건조 명사 체계 통일.
- **핵심 엔진 단위 테스트 36개 전 항목 100% 통과 (`test_core_engine.py`)**:
  - 다국어 핫스왑, 리본 위젯 동기화, 라벨 길이 제약, 9개국어 EULA 무결성 등 36개 테스트 스위트 전체 PASS 확인.

## [v1.4.0.Build.5] - 2026-09-12 18:45

### 📜 글로벌 9개국어 소프트웨어 최종 사용자 라이선스 계약서 (EULA) & 전용 EulaManager
- **글로벌 9개국어 EULA 전문 카탈로그 및 서비스 엔진 구축 (`eula_manager.py`)**:
  - 한국어(`ko`), English(`en`), 简体中文(`zh`), 日本語(`ja`), Deutsch(`de`), Español(`es`), Français(`fr`), Português(`pt`), Русский(`ru`) 전 언어별 정밀 법률 EULA 전문 탑재.
  - 전사 표준 7개 조항 체계화:
    - 제1조 (목적 / Purpose)
    - 제2조 (지식재산권 귀속 / Intellectual Property & Ownership)
    - 제3조 (사용권의 범위: 1PC-1Key 노드락 & 2026.12.31 평가판 유효기한)
    - 제4조 (금지행위: 리버스 엔지니어링, 보안 메커니즘 변조, 무단 재배포 금지)
    - 제5조 (보증의 한계 및 면책 / Disclaimer of Warranties)
    - **제6조 (위약벌 5배 및 손해배상 / Liquidated Damages: 정규 라이선스 정가의 5배 즉시 지급)**
    - 제7조 (준거법 및 대한민국 서울중앙지방법원 제1심 전속 관할)
    - 하단 공고일자, 시행일자(2026.09.11), (주)드래곤알피에이 대표이사 및 공식 문의처 명시.
- **다국어 스마트 EULA 다이얼로그 전면 개편 (`EulaDialog` in `manual_capture_studio.py`)**:
  - **다이얼로그 내 9개 언어 즉시 전환 콤보박스**: 상단 헤더에 `🌐 [한국어 | English | ...]` 콤보박스를 탑재하여 앱 언어를 바꾸지 않고도 즉각 언어별 계약서 열람 가능.
  - **현재 활성 언어 자동 상속**: 앱 시작 및 메뉴 호출 시 `I18nManager.instance().get_locale()`에 맞춰 해당 국가 언어로 기본 즉시 렌더링.
  - **위약벌 5배 경고 시각적 하이라이트 박스**: 제6조를 적색 경고 뱃지(`⚠️ 제6조 / Article 6`) 및 은은한 레드 경고 박스로 감싸 가독성 및 법적 효력 극대화.
  - **원클릭 클립보드 전체 복사(`[📋 전체 복사]`)**: 이메일, 문서, 계약서 첨부용 깔끔한 Plain-text 1클릭 복사 및 `✅ 복사 완료!` 1.6초 피드백 제공.
  - **동아시아·유럽 특수문자 무깨짐 폰트 스택**: 일본어 장음(`ー`), 중국어 간체, 키릴 문자, 유럽 악센트 부호가 완벽하게 렌더링되도록 `Segoe UI`, `Yu Gothic`, `Meiryo`, `Microsoft YaHei`, `Malgun Gothic` 최적 폰트 스택 적용.
- **핵심 엔진 단위 테스트 스위트 36개 전 항목 100% PASS 달성 (`test_core_engine.py`)**:
  - `test_multilingual_eula_manager`: 9개 언어 HTML/Plain 계약서 구조, 5배 위약벌 문구, 관할법원, 언어 정규화/폴백, UI 콤보박스 전환 및 클립보드 복사 검증 100% 통과.

## [v1.4.0.Build.4] - 2026-09-12 18:35

### 🖥️ 화면 해상도 최적화: 기본 창크기 초과 해소 & 리본 서식 2단 그리드 전면 개편
- **기본 창크기 화면 초과 버그 원인 규명 및 완전 해소**:
  - 기존 탭 2(서식·설정)의 8개 그룹이 단일 가로행(`QHBoxLayout`)으로 나열되어 최소 폭(`minimumSizeHint`)이 **2,437px**까지 팽창되어 Windows/Qt 창 관리자가 강제로 모니터 경계를 초과시키던 결함 진단.
  - 윈도우 최소 크기 힌트를 **2,437px ➔ 943px (61.3% 압축)**로 대폭 감축하여 어떤 노트북이나 보급형 모니터에서도 화면 밖으로 튀어나가지 않도록 완전 해결.
- **서식·설정 탭(Tab 2) 2단 그리드(`QGridLayout`) 전면 개편**:
  - `스탬프`, `선·화살표`, `텍스트·글꼴`, `워드아트`, `보안·단축키`, `PPT 규격·배치`, `PPT 제목상자(4×2)`, `환경설정` 8개 전 그룹을 Tab 1(도구)과 동일한 2단 컴팩트 그리드로 통일.
  - 높이와 시각적 리듬을 일치시키고 정보 밀도 극대화 (전사 표준 헌장 3.1, 3.2 준수).
- **반응형 리본 스크롤 영역(`QScrollArea`) 래퍼 장착**:
  - `tab_tools`와 `tab_format`에 테두리 없는 투명 `QScrollArea`를 적용하여 해상도가 1024x768 또는 1280x720 등 소형 디스플레이에서도 창 크기가 강제 팽창되지 않고 매끄럽게 가로 스크롤 대응.
- **상시 퀵 서식 바(`QuickStrip`) 1,206px ➔ 917px 슬림 압축**:
  - 두께, 5색 프리셋, 커스텀 컬러, 음영 토글, 다중 모니터 선택 드롭다운, 고정 모드 및 X/Y/W/H 스핀박스, 영역 저장 버튼, 도구 상태 뱃지 등 18개 전 기능을 100% 온전히 유지하면서 가로폭을 917px로 최적화.
- **화면 크기 지능형 감지 & 중앙 자동 배치**:
  - `QGuiApplication.primaryScreen().availableGeometry()` 기반으로 작업표시줄을 제외한 가용 화면 영역의 85% 이내(기본 1260×820)로 윈도우를 자동 리사이즈 및 화면 정중앙(`Centered`) 정렬.
- **핵심 엔진 테스트 스위트 35개 전 항목 100% PASS 유지 (`test_core_engine.py`)**.

### 🌐 0.05초 즉시 핫스왑 다국어 UI 갱신 & 가로폭 40% 압축 초고밀도 리본 UIUX
- **0.05초 즉시 핫스왑 다국어 갱신 엔진 (`manual_capture_studio.py`, `i18n_manager.py`)**:
  - 기존 앱 재시작 필요 문구 및 미반영 문제 완전 해소.
  - 언어 메뉴 선택 즉시 `retranslate_ui()`를 통해 상단 메뉴바 6개 메뉴/20개 액션, 리본 2개 탭, 15개 그룹 타이틀, 31개 스택 필드 레이블, 24개 조작 버튼, 하단 퀵 서식 바, 상태바 및 윈도우 타이틀까지 전 영역 0.05초 만에 완벽 동적 재번역 적용.
- **가로폭 1,500px -> 980px 압축 (전사 표준 헌장 3.1 & 3.2 준수)**:
  - 장황한 문장형 버튼 라벨을 직관적이고 건조한 단축 명사(`고정`, `지정`, `추가`, `열기`, `저장`, `복사`, `선택`, `실행취소`, `비우기`, `스탬프`, `순번화살표`, `직각`, `직선`, `박스`, `블러`, `드래프트`, `말풍선`, `텍스트`, `단축키`, `워드아트`, `슬라이드`, `맞춤`, `재정렬`)로 압축.
  - 모든 버튼에 시각적 심볼 및 이모지 아이콘을 전면 배치하여 인지 속도 극대화.
  - 리본 7개 그룹이 1080p 일반 해상도에서도 화면 잘림이나 횡 스크롤 없이 980px 내에 완벽 안착.
- **버튼별 9개 국어 연동 상세 기능설명 도움말 (Hover Help ToolTip)**:
  - 24종 모든 핵심 기능 버튼에 마우스오버 시 선택된 언어로 자동 연동되는 다국어 호버 툴팁 장착.
  - `[기능명 (단축키)]\n상세 동작 및 사용 가이드` 2단 레이아웃 표준화로 초심자도 설명서 없이 100% 직관 활용 가능.
- **핵심 엔진 테스트 스위트 35개 전 항목 100% PASS 달성 (`test_core_engine.py`)**:
  - `test_dynamic_language_retranslation` (0.05초 핫스왑 검증)
  - `test_compact_ui_button_labels` (16자 이하 초소형 아이콘 버튼 레이블 규격 검증)
  - `test_multilingual_tooltips_completeness` (9개 국어 24종 툴팁 100% 무누락 검증)

## [v1.4.0.Build.2] - 2026-09-12 18:05

### 🚀 스마트 자동 업데이트(Smart Auto-Updater) 클라이언트 & 원격 버전 검증 엔진
- **버전 메타데이터 단일 원천(SSOT) 체계 구축 (`version.json`)**:
  - 원격 버전, 릴리즈 날짜, 릴리즈 타이틀, 릴리즈 노트, 다운로드 URL 및 강제 업데이트 플래그 표준 규격 수립.
- **고성능 비동기 업데이트 검증 엔진 (`updater_engine.py`)**:
  - `VersionComparator`: 시맨틱 4단계 버전(`vX.Y.Z.Build.N`) 정밀 대소 비교기.
  - `UpdateCheckerThread`: GitHub CDN `version.json` 1순위(Rate-limit 없음) + GitHub Releases API 2순위 비동기 폴백 조회.
  - `UpdateDownloadThread`: 최신 바이너리 청크 스트림 백그라운드 다운로드 및 실시간 진행률(바이트/총용량/%) 전송.
  - `WindowsPatcher`: Windows 프로세스 파일 잠금(Lock) 우회 원자적 파일 교체 배치 스크립트(`update_patcher.bat`) 자동 생성, PID 대기 종료 후 바이너리 교체 및 새 버전 자동 재실행.
  - `UpdateDialog`: 전사 표준 헌장(카테고리 III: 건조한 명사·동사, 줄바꿈 방지) 준수 전용 UI (신규 버전 비교, 릴리즈 노트 프리뷰, 진행률 게이지).
- **인앱 메뉴 & 환경설정 연동 (`manual_capture_studio.py`)**:
  - 상단 메뉴바 `도움말(&H) -> 🚀 최신 업데이트 확인(&U)...` 수동 확인 지원.
  - 환경 설정(`SettingsDialog`) 내 `[☑] 프로그램 시작 시 최신 버전 자동 확인` 토글 연동 (앱 시작 3.5초 후 백그라운드 비동기 점검).
  - 업데이트 후에도 기존 레지스트리 영구 라이선스 및 사용자 환경설정(`config.json`) 100% 무손실 자동 상속.
- **핵심 엔진 32개 단위 테스트 스위트 100% PASS 달성 (`test_core_engine.py`)**.

## [v1.4.0.Build.1] - 2026-09-12 17:40

### 🌐 글로벌 9개 국어 I18N 다국어화 & 무깨짐 폰트 폴백 체인
- **글로벌 9개 국어 카탈로그 및 시스템 로케일 자동 감지 (`i18n_manager.py`)**:
  - 한국어(`ko`), English(`en`), 简体中文(`zh`), 日本語(`ja`), Deutsch(`de`), Español(`es`), Français(`fr`), Português(`pt`), Русский(`ru`) 전면 지원.
  - 시스템 언어 자동 감지 및 메뉴바 `🌐 언어(Language)` / 환경 설정 콤보박스를 통한 실시간 언어 전환 지원.
  - 단계명 슬라이드 템플릿 9개국어 표준화 (`Step {n}. [단계명 입력]`, `Step {n}. [Enter Step Title]`, `步骤 {n}. [输入步骤名称]`, `ステップ {n}. [手順名を入力]`, etc.).
- **다국어 텍스트박스 무깨짐 글꼴 폴백 체인 (`QFont.setFamilies`)**:
  - `TextLabelItem`, `CalloutItem`, `WordArtItem`에 전 세계 표준 글꼴 폴백 체인(`Segoe UI`, `Microsoft YaHei`, `Yu Gothic`, `Meiryo`, `Malgun Gothic`, `Arial`, `sans-serif`)을 영구 적용하여 한자, 히라가나/가타카나, 키릴 문자, 악센트 라틴 문자 렌더링 시 폰트 깨짐(Tofu 현상)을 원천 차단.

### 🔑 엔터프라이즈 라이선스 엔진 & 독립형 키젠(발급기) 개발 (`license_engine.py`, `tools/keygen_manual_studio.py`)
- **6대 라이선스 유형 체계 정립**:
  - ① 1카피 영구 (`PERPETUAL` / `MS1P`)
  - ② 1카피 1개월 (`SUB_1M` / `MS1M`)
  - ③ 1카피 1년 연간 구독 (`SUB_1Y` / `MS1Y`)
  - ④ 볼륨/엔터프라이즈 (`ENTERPRISE` / `MSENT`)
  - ⑤ 오프라인 보안 폐쇄망 사이트 (`AIR_GAPPED` / `MSSITE`)
  - ⑥ 14일 평가 연장 (`TRIAL_14D` / `MST14`)
- **HMAC-SHA256 기반 위변조 불가능한 서명 및 HWID 노드락 바인딩**:
  - 클라이언트 고유 식별자(`DRPA-XXXX-XXXX-XXXX`) 기반 기기 바인딩.
  - 라이선스 검증 및 Windows 레지스트리(`HKCU\Software\DragonRPA\ManualStudio\License`) 및 로컬 백업(`license.key`) 동시 보존.
- **인앱 라이선스 등록 창 (`LicenseRegistrationDialog`) & About 연동**:
  - HWID 원클릭 복사, 시리얼 키 등록, 실시간 상태 배지 표시 및 인증 즉시 워터마크 해제.
- **독립형 라이선스 발급기 (`tools/keygen_manual_studio.py`)**:
  - GUI 및 CLI 동시 지원, 발급 이력 JSON(`tools/issued_licenses.json`) 자동 누적.

### 🛡️ 평가판 "Manual Studio" 워터마크 자동 각인 & 정식 인증 시 완전 제거
- 미인증 평가판 상태에서는 PPT 슬라이드 생성, 클립보드 복사, 이미지 내보내기 시 우하단 반투명 브랜드 배지 및 캔버스 중앙 대각선 반투명 워터마크 자동 합성.
- 정식 라이선스 인증 즉시 모든 워터마크가 100% 제거된 깨끗한 원본 고해상도 슬라이드 출력.

### ⚡ 캡처 영역 지정(Shift+F9) 및 추가 캡처(F8) 엔터 대기 제거
- 마우스 드래그 후 손을 떼는 순간(Mouse Release) 엔터키 입력 대기 없이 즉시 확정되어 캔버스에 안착하도록 개선 (`CaptureOverlayWidget.mouseReleaseEvent`).
- 10x10 미만 미세 조작 시 오발 방지 필터링 유지.

### 📊 사내 PPT 마스터 템플릿(`.pptx`, `.potx`) 연동
- 환경 설정(`SettingsDialog`)에서 사내 공식 PPT 템플릿 파일 지정 지원.
- 슬라이드 생성 시 회사의 공식 로고, 배경 그래픽, 슬라이드 마스터 서식 자동 상속 지원 (`PowerPointAutomation.send_to_powerpoint`).

### 💾 실수 방지 주기적 자동 저장(Auto-save) & 재실행 복구 시스템
- 설정 가능한 주기(1~30분)로 백그라운드에서 원본 비트맵 및 주석 벡터 레이어를 자동 백업(`.autosave.mcs.json`).
- 비정상 종료 시 재실행 시 팝업을 통해 직전 작업 내용을 100% 무손실 복구.

### 📖 글로벌 9개 국어 공식 사용 설명서 번들 생성 (`docs/`)
- 한국어, 영어, 중국어, 일본어, 독일어, 스페인어, 프랑스어, 포르투갈어, 러시아어 등 9개 언어별 가이드(`docs/User_Guide_XX.md`) 및 UI 스크린샷 4종 완비.
- 핵심 비즈니스 로직 29개 단위 테스트 스위트 100% PASS 달성.

## [v1.2.0.Build.5] - 2026-09-12 12:22

### 📦 EULA 내장 Nuitka C-기계어 바이너리(`ManualStudio.exe`) 재컴파일 및 README 연동
- **C-컴파일 바이너리 재생성 및 검증 완료**:
  - `EulaDialog` 및 메뉴바 액션이 완전 통합된 27.97MB 순수 기계어 단일 실행파일 `ManualStudio.exe` 빌드 및 배포 패키지 동기화.
- **저장소 문서(`README.md`) EULA 섹션 7 신설**:
  - 저작권 귀속, 사용권 범위, 금지 사항 및 [EULA 전문](EULA.md) 하이퍼링크 탑재.

## [v1.2.0.Build.4] - 2026-09-12 12:20

### 📜 공식 최종 사용자 라이선스 계약서(EULA) 탑재 및 지식재산권 방어선 구축
- **소프트웨어 라이선스 계약서(EULA) 정식 문서화 (`EULA.md`, `docs/EULA.md`)**:
  - 지식재산권 배타적 귀속(2조), 평가판/정규 라이선스 범위(3조), 역공학·디컴파일·크랙·무단재배포 절대 금지(4조), 보증 제한(5조), 위약벌(5배) 및 손해배상(6조), 본점 전속 관할 법원(7조) 등 7대 조항 체결.
- **프로그램 내 EULA 다이얼로그(`EulaDialog`) 신설**:
  - 상단 메뉴바 `EULA(&E)` 메뉴 액션 신설
  - 상단 메뉴바 우측 코너 `📜 EULA` 퀵 버튼 탑재
  - `AboutDialog` 내 `[📜 사용권 계약 (EULA)]` 버튼 탑재로 프로그램 내 상시 열람 지원.
- **공식 웹사이트(`www.dragonrpa.co.kr/manual-studio`) EULA 탭 연동**:
  - 웹 상세 설명서 4번째 탭에 EULA 전문 공표 및 원클릭 복사 기능 연동.

## [v1.2.0.Build.3] - 2026-09-11 13:45

### ⚡ Nuitka C-컴파일러 완전 전환 (순수 기계어 바이너리)
- **C-트랜스파일 및 네이티브 컴파일 완결**:
  - Python 코드를 순수 C 언어로 변환 후 MinGW64 GCC 15.2.0 컴파일러를 통해 바이너리 생성 완료.
  - 역컴파일(디컴파일러 공격)에 취약한 기존 바이트코드 번들링 방식(PyInstaller) 대비 100% 기계어 바이너리로 코드 보안성 및 저작권 방어력 극대화.
- **초경량 단일 실행파일 달성**:
  - 실행 파일 용량: 기존 58.7 MB(PyInstaller) ➔ **27.97 MB** (52% 다이어트 성공).
  - 콘솔창 완전 제거 (`--windows-console-mode=disable` 적용)로 전문 상용 소프트웨어급 미려한 구동 UX 확보.
- **Windows 한글 계정명 경로 결함 3중 방어막 구축**:
  - `depends.exe` latin1 인코딩 깨짐 우회를 위해 순수 파이썬 PE 헤더 분석 엔진(`--experimental=force-dependencies-pefile`) 탑재.
  - MinGW `ld.exe` 링커 호환을 위해 `C:\nuitka_libs` 순수 ASCII 라이브러리 fallback 경로 연동.
  - GCC LTO 심볼 해석 경로 결함 차단을 위해 `--lto=no` 및 `C:\ManualStudioBuild\temp` 지정.
- **원클릭 C-컴파일 배치 스크립트 제공**: `build_c.bat`

## [v1.2.0.Build.1] - 2026-09-11 13:15

### 🏢 회사 브랜딩 및 프로그램명 개편
- **프로그램명 공식 단일화**: '매뉴얼 캡처 스튜디오'에서 **`매뉴얼 스튜디오 (Manual Studio)`**로 브랜드 통일.
- **공식 CI 및 브랜딩 적용**:
  - (주)드래곤알피에이 (DragonRPA Co.) 공식 CI 로고 내장 (`assets/dragon_rpa_ci.png` 및 `dragon_rpa_ci_data.py` 무손실 Base64 탑재).
  - 윈도우 타이틀바, 메뉴바 우측 상단 코너, 하단 상태바에 CI 아이콘 및 회사명 일체화.
  - 메뉴바 우측 끝에 상시 호출 가능한 `ℹ️ About` 버튼 탑재.
  - 리본 탭 우측 코너의 중복 위젯을 제거하여 상단 메뉴바 단일 배치로 시야 확보.
- **About 다이얼로그 (정보 창)**:
  - 공식 CI 고해상도(100×100 px) 로고 및 프로그램 버전 표기.
  - 기간 한정 평가판 강조 안내 카드 탑재 (`~2026년 12월 31일`).
  - 개발사 안내 문구 및 고객 지원 연락처(`77.victor.lee@gmail.com`) 제공.
  - 불필요한 메일 쓰기 버튼을 제거하고 `[📋 이메일 주소 복사]` 원클릭 기능 단독 배치.

### ⏳ 보안 및 라이선스 통제 (LicenseValidator)
- **시한부 수명 제한 (Time-Bomb)**: 2026년 12월 31일 23:59:59 도과 시 구동 차단 안내 모달 표시 및 프로세스 정상 종료.
- **안티 롤백 (Anti-Rollback)**: 윈도우 레지스트리(`HKCU\Software\DragonRPA\ManualCaptureStudio\KernelTick`) 기반 난독화 타임스탬프 기록을 통해 시스템 시계 역행 변조(10분 이상 과거 조작) 원천 탐지 및 방어.

### 🎨 핵심 주석 및 캡처 스튜디오 기능
- **단축키 워크플로우**: `F9`(고정 영역 즉시 캡처), `Shift+F9`(새 영역 드래그 지정), `F8`(모달 부분 추가 캡처), `F10`(파워포인트 슬라이드 생성 및 클립보드 복사).
- **5대 추천 주석 개체**: 번호 스탬프(`①`), 스탬프 화살표(`①➔`), 직각 화살표(`↳`), 직선 화살표(`↗`), 모자이크 블러, 사각 강조 박스, 설명 말풍선, 텍스트 라벨, 단축키 뱃지.
- **Draft 스탬프**: 60도 기울기 회전 및 크기 조절 가능한 워터마크 스탬프.
- **스마트 번호 재정렬**: 중간 스탬프 삭제 시 후속 번호 자동 당김, 파워포인트 열린 슬라이드 전체 `Step N` 일괄 순차 재부여.
- **프로젝트 무결성 보존**: `.mcs.json` 및 `_raw.png` 완벽 분리 저장으로 재편집 시 개별 주석 객체 100% 복원.

### 📚 문서 및 지식재산권 가이드
- [`docs/소프트웨어_권리보호_및_상용화_절차가이드.md`](docs/소프트웨어_권리보호_및_상용화_절차가이드.md): 한국저작권위원회 등록, 특허청 상표권 출원, EULA 약관, Nuitka C-컴파일, 비대칭키 머신락 DRM, EV 코드서명 전략 수립.
- 핵심 비즈니스 로직 20개 단위 테스트 스위트 100% PASS 구축.

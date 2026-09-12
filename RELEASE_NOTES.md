# Manual Studio Release Notes

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

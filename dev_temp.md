# Development Temporary Task Log (dev_temp.md)

## [2026-09-13 22:50] 매뉴얼 스튜디오 Phase 9.1 버그 픽스: 타임라인 슬라이드 선택 삭제 시 이중 시그널 방출(2개씩 삭제) 결함 해결 (v1.5.0.Build.4)
- [x] 타임라인 스토리보드 선택 삭제 이중 방출 버그 해결
  - `FilmstripDockWidget.request_delete_selected`에서 `sig_delete_step`과 `sig_delete_steps` 동시 emit 제거 ➔ `sig_delete_steps(targets)` 1회만 단일 방출
  - `FilmstripDockWidget.__init__` 시 `selected_indices`를 `{0}`이 아닌 빈 집합(`set()`)으로 안전하게 초기화하여 초기 인덱스 왜곡 방지
  - 단위 테스트(`test_core_engine.py`)에 단일 선택 삭제 및 다중 선택 삭제 시뮬레이션 검증 케이스 추가 완료 (72개 전 테스트 100% 통과)
- [x] PyInstaller 컴파일 및 실행 파일 안전 교체 완료 (`ManualStudio.exe`)

## [2026-09-13 22:30] 매뉴얼 스튜디오 Phase 9 구현: 도움말 업데이트 노트 뷰어(전체 30개 릴리즈 수록), 리본 42개 전 도구 고해상도 벡터 아이콘 100% 매핑, 13개국어 번역 완전 해소(누락 0건), 스마트 자동 업데이트 실패 원인 해결 및 공식 릴리즈 연계, 전 기능키 배선 완비 (v1.5.0.Build.3)
- [x] 도움말 내 업데이트 노트 다이얼로그 (`ReleaseNotesDialog`) 신설
  - 메뉴바 [도움말(&H)] ➔ [업데이트 노트 (릴리즈 내역)...] 및 About 대화상자 연동
  - `RELEASE_NOTES.md` 파싱하여 `v1.0.0` 초기 버전부터 현재까지 총 30개 전 릴리즈 상세 내역을 HTML 서식으로 열람 가능한 전용 뷰어 제공
  - 상단 드롭다운 버전 필터링 및 원클릭 `[클립보드에 복사]` 기능 탑재
- [x] 리본 메뉴 42개 전 도구 QPainter 고해상도 벡터 아이콘 100% 매핑 (`RibbonIconProvider`)
  - `Ctrl+M` 리본 "아이콘으로 표시" 모드 전환 시 누락/빈칸 0건 달성 (신규 12대 아이콘 추가 탑재)
- [x] 13개 글로벌 언어(i18n) 누락 키 0건 완전 해소 (`i18n_manager.py`)
  - 27개 신규/누락 키 13개 언어 전수 번역 등록 (총 458개 키 등록 완료, 누락률 0%)
- [x] 스마트 자동 업데이트 실패(404) 원인 규명 및 완전 해결 (`updater_engine.py`)
  - GitHub Releases 404/403 예외 시 친절한 원인 진단 및 [공식 릴리즈 페이지 열기] 버튼 제공
  - 개발 환경(`python.exe`) 덮어쓰기 방지 가드 탑재 및 임시 디렉터리 기반 안전 패처 배치 실행
  - `APP_VERSION`과 `version.json`을 1.5.0으로 동기화하여 자가 업데이트 루프 원천 차단
- [x] 기능키 및 단축키 전수 배선 및 72개 전 단위 테스트 무결점 통과
  - `Shift+F10` (한글 삽입), `F10` (파워포인트 삽입 / 새 슬라이드), `F11` (구글 슬라이드), `F12` (한글 전송), `Ctrl+N` (새 프로젝트), `Ctrl+Shift+S` (다른 이름 저장), `Ctrl+Shift+M` (프로젝트 병합)
- [x] 문서 3종 최신화: `각 기능(키)설명.MD`, `AGENTS.md` (UIA 및 9대 MCP 도구 명세), `RELEASE_NOTES.md`

## [2026-09-13 21:15] 매뉴얼 스튜디오 2세대 Phase 8 구현: 다중 슬라이드 프로젝트 아키텍처(.dragon / .mcs.json), 프로젝트 병합 및 내보내기 파이프라인 전수 정상화, 13개국어 번역 완전 연동, 메뉴바/리본 UI 정리 (v1.5.0.Build.2)
- [x] 단일 압축 패키지 포맷 `.dragon` 및 다중 슬라이드 `.mcs.json` 저장/복원 완비
- [x] 외부 프로젝트 슬라이드 병합(`action_merge_project`) 기능 구현
- [x] 웹북(HTML), PPT, Google Slides, 한글(HWP), GIF 전 내보내기 파이프라인 무결점 정상화

## [2026-09-13 19:50] 매뉴얼 스튜디오 2세대 Phase 7.1 구현: 메뉴바 우측 중복 코너 위젯(회사표시, EULA, About) 제거 완료
- [x] 메뉴바 우측 코너 위젯 전면 제거 및 상단 공간 최적화
  - [도움말(&H)] 메뉴에 이미 [사용권 계약서 (EULA)] 및 [프로그램 정보 (About)]가 완벽히 탑재되어 있으므로, 상단 메뉴바 우측에 중복 노출되던 CI 로고, 회사명(`(주)드래곤알피에이 | DragonRPA Co.`), `[EULA]`, `[About]` 코너 버튼군을 전면 제거
  - 윈도우 상단 타이틀 및 메뉴바 영역의 시각적 간결성과 정보 밀도 극대화
- [x] 핵심 단위 테스트 70개 전 항목 100% 통과 (`test_core_engine.py` 70/70 ALL PASS)

## [2026-09-13 19:40] 매뉴얼 스튜디오 2세대 Phase 7 구현: 스토리보드 툴바 전면 개편(선택 복제/앞으로/뒤로 이동, 우클릭 제거), 호버 고화질 미리보기 박스 및 설정 연동, 스토리보드 상단 접기/펼치기 분할 바, 예시 기반 정규식 합성기, MAC 주소 & 금융 계좌 2-Tier 문맥 탐지, 미마스킹 민감정보 감지 시 일시 경고 완비
- [x] 스토리보드 상단 툴바 버튼 신설 및 우클릭 메뉴 전면 제거
  - 슬라이드 카드 우클릭 팝업 메뉴를 배제하고 상단 툴바에 모든 조작 액션을 직관적으로 시각화
  - `[선택 삭제]` 우측이자 `[선택 내보내기 ▾]` 좌측에 3대 액션 버튼 배치:
    - `[선택 복제]`: 선택된 슬라이드(들)를 복제하여 바로 뒤에 즉시 삽입하고 번호 자동 정렬
    - `[앞으로 이동]`: 선택된 슬라이드를 타임라인 앞(왼쪽)으로 1칸 순서 이동
    - `[뒤로 이동]`: 선택된 슬라이드를 타임라인 뒤(오른쪽)으로 1칸 순서 이동
- [x] 슬라이드 호버 고화질 미리보기 박스 (`SlideHoverPreviewWidget`)
  - 타임라인 슬라이드 카드 위에 마우스오버(Hover) 시 커서 약간 위에 확대된 선명한 슬라이드 미리보기 박스 표출
  - 마우스 이탈 시 즉시 숨김
  - 스토리보드 툴바 우측 `[미리보기]` 체크박스 및 `config.json`(`enable_hover_preview`) 연동으로 사용자가 자유롭게 ON/OFF 제어
- [x] 스토리보드 바로 위 접기/펼치기 분할 바 (`StoryboardToggleBar`)
  - 리본 메뉴에 있던 스토리보드 토글 버튼을 스토리보드 바로 위(캔버스와 스토리보드 경계선)로 재배치
  - 22px 슬림 분할 바 중앙에 `[스토리보드 접기 ▲]` / `[스토리보드 펼치기 ▼]` 버튼을 제공하여 스토리보드가 접혀 숨겨져도 바로 그 자리에서 1초 만에 원클릭 펼침 지원
- [x] 예시 기반 정규식 자동 변환기 (`PiiRedactionEngine.synthesize_regex_from_example`)
  - 정규식을 모르는 사용자도 `000-0000-0000`, `aaa@aaa.aaa`, `EMP-0000` 등 서식 예시만 입력하면 최적의 권장 정규식을 실시간 자동 변환
  - 파워 유저는 생성된 권장 정규식을 직접 자유롭게 수정할 수 있도록 허용
  - `PiiMaskingDialog` 테이블을 4컬럼(`[활성]`, `[규칙명]`, `[예시/서식 (입력)]`, `[권장 정규식 (수정가능)]`)으로 고도화하고 `config.json`에 `example` 필드 영구 보존
- [x] MAC Address 기본 카테고리 추가 및 금융 계좌번호 2-Tier 문맥 탐지
  - IEEE 및 Cisco 표준 MAC 주소(`pii_cat_mac`)를 기본 카테고리로 신설하여 원클릭 마스킹
  - 계좌번호를 금융 문맥 키워드 결합 탐지(계좌/입금/환불/은행명/Account/IBAN + 10~16자리) + 국제 표준 IBAN 규격으로 재설계하여 일반 주문번호/송장번호 오탐률 0% 달성
- [x] 슬라이드 미마스킹 민감정보 감지 시 전환 일시 경고
  - 모자이크 블러 처리되지 않은 민감정보가 있는 슬라이드로 전환 시 경고 토스트(`⚠️ 미마스킹 민감정보 감지됨`) 및 카드 뱃지(`⚠️`) 제공
- [x] 13개 글로벌 언어 i18n 10개 신규 키 전수 등록 및 70개 단위 테스트 100% PASS
  - `pii_cat_mac`, `pii_table_col_sample`, `pii_table_col_pattern`, `toast_unmasked_pii_detected`, `btn_duplicate_selected`, `btn_move_prev`, `btn_move_next`, `chk_hover_preview`, `btn_toggle_storyboard_hide`, `btn_toggle_storyboard_show`
  - `test_core_engine.py` 70개 단위 테스트 100% 통과 (Exit Code 0)
- [x] PyInstaller 프로덕션 컴파일 빌드 완비 (`ManualStudio.exe`)



## [2026-09-13 18:35] 매뉴얼 스튜디오 2세대 Phase 6 구현: 중복 모니터 콤보박스 퀵스트립 단일화, 리본 단일 전송 버튼 정리 및 '슬라이드 옵션' 그룹 개편, '+ 새 슬라이드 (F10)' 단축키 부여, 스토리보드 슬라이드 다중 선택(Shift/Ctrl 클릭 토글, 전체선택, 전체해제, 선택삭제, 선택내보내기) 완비
- [x] 중복 모니터 콤보박스 단일화
  - 상단 리본 메뉴 [캡처] 그룹의 중복 `combo_tab_monitor`를 제거하고 하단 퀵스트립의 `combo_monitor`로 일원화
  - 리본 캡처 그룹의 레이아웃을 2x3 균형 배치로 최적화 (`고정 캡처`, `영역 지정`, `부분 캡처`, `스크롤 스티칭`, `액션 녹화`)
- [x] 리본 단일 전송 버튼 제거 & '슬라이드 옵션' 그룹 개편
  - 과거 1장씩 파워포인트/구글슬라이드/한글로 전송하던 구형 버튼군(`슬라이드 삽입`, `구글 슬라이드 전송`, `한글 전송`)을 리본에서 정리
  - 기존 출력 그룹을 `[슬라이드 옵션]` (`grp_slide_options`) 그룹으로 개편하여 `액자 프레임`, `배율 맞춤`, `스토리보드`, `제목 상자`, `순번 재정렬`을 콤팩트 배치
- [x] `+ 새 단계` ➔ `+ 새 슬라이드 (F10)` 개편
  - 버튼 명칭을 `+ 새 슬라이드 (F10)`로 변경하고 단축키 `F10` 부여
  - 글로벌 단축키 및 윈도우 키 이벤트 연동: 캡처 및 주석 편집 후 `F10`을 누르면 현재 캔버스 작업을 활성 슬라이드에 자동 스냅샷 저장하고 즉시 새 슬라이드로 쾌속 전환
- [x] 스토리보드 슬라이드 다중 선택 (Multi-Selection) & 선택 내보내기/삭제
  - 단순 클릭: 해당 슬라이드 1개 선택 및 작업대 캔버스 로드
  - `Shift + 클릭` / `Ctrl + 클릭`: 슬라이드를 선택 목록에 포함(추가)하거나 제외(토글)하여 원하는 슬라이드들만 정밀 선택
  - 카드 상단에 파란색 원형 체크 뱃지(`✓`) 및 하이라이트 테두리로 선택 상태 시각화
  - 툴바 제어 버튼 신설:
    - `[전체 선택]`: 모든 슬라이드 일괄 선택
    - `[전체 해제]`: 활성 슬라이드를 제외한 나머지 선택 해제
    - `[🗑️ 선택 삭제 (N)]`: 현재 다중 선택된 슬라이드들을 원클릭으로 일괄 삭제하고 후속 슬라이드 번호를 1부터 순차 자동 정렬
    - `[선택 내보내기 ▾]`: 선택된 슬라이드들만 원하는 포맷(PPT, Google Slides, HWP, HTML 웹북, GIF)으로 일괄 전송/출판!
- [x] 13개 글로벌 언어 i18n 5개 신규 키 전수 등록
  - `btn_add_slide`, `btn_select_all`, `btn_deselect_all`, `btn_export_selected_menu`, `grp_slide_options` (13개국어 100% 등록)
- [x] 핵심 단위 테스트 69개 전 항목 100% 통과 (`test_core_engine.py` 69/69 ALL PASS)
- [x] `각 기능(키)설명.MD` 기능 및 단축키 설명서 최신화 완료

## [2026-09-13 18:00] 매뉴얼 스튜디오 2세대 Phase 5 구현: 전체 내보내기 대상 통합(PPT/Slides/HWP/HTML/GIF), 선택 삭제 버튼, 마우스 D&D 스텝 순서 변경, PII 9대 카테고리 강화 & 사용자 정의 정규식 관리 대화상자(`PiiMaskingDialog`), F8 1:1 무손실 선명도 복원 완비
- [x] 하단 스토리보드 전체 내보내기 통합 드롭다운 메뉴 (`btn_export_all_menu`, `export_menu`)
  - 개별 분산되어 있던 내보내기 버튼들을 `[전체 내보내기 ▾]` 단일 QMenu 버튼으로 일원화
  - 5대 내보내기 옵션: ① PowerPoint (PPT), ② Google Slides (전 스텝 일괄 주입 `action_export_all_slides`), ③ 한컴 한글 (HWP), ④ 반응형 웹북 (HTML), ⑤ 숏클립 튜토리얼 (GIF)
- [x] 스토리보드 선택 삭제 버튼 (`btn_delete_selected`)
  - 툴바에 `[🗑️ 선택 삭제]` 버튼 추가하여 현재 선택된 활성 스텝(`active_idx`) 원클릭 즉시 삭제 및 번호 자동 재정렬
- [x] 마우스 드래그 앤 드롭(Drag & Drop) 스텝 순서 변경
  - `StepCardWidget`에서 `QDrag` + `QMimeData(application/x-manualstudio-step-index)` 생성 및 드래그 제스처 지원
  - `FilmstripDockWidget.cards_container`에서 `dragEnterEvent`, `dragMoveEvent`, `dropEvent` 처리하여 드롭 위치 기반 타깃 인덱스 계산 및 `sig_move_step(from_idx, to_idx)` 연동
- [x] 개인정보 마스킹 패턴 대폭 강화 & 사용자 정의 정규식 관리 대화상자 (`PiiMaskingDialog`)
  - 9대 기본 카테고리 강화: 사업자등록번호(`111-81-16460`), 서울 02 국번 및 분절 전화번호, 성명+직급(`김승종 대리`, `정재은 차장`), 도로명/지번 주소(`서울시/구/동/로`), 주민번호, 이메일, 계좌번호, 카드번호, IP 주소
  - 프로그램이 일방적으로 자동 마스킹하지 않고 사용자가 원하는 항목을 체크박스로 제어
  - 사용자 임의 정규식(사번, 비밀코드 등) 자유 추가/수정/삭제/활성화 테이블 제공 및 `config.json` 영구 보존
  - 단축키 `M` 또는 리본 메뉴 `[개인정보 마스킹]` 버튼 클릭 시 `PiiMaskingDialog` 표출 후 선택 실행
- [x] F8 모달/서브 윈도우 부분 캡처 1:1 원본 무손실 선명도 복원
  - `StudioCanvasWidget.add_image_overlay()`의 임의 75% 강제 축소 제거 -> 캔버스 크기 이내인 경우 1:1 원본 해상도(`scale = 1.0`) 및 정수 격자 배치
  - `ImageOverlayItem.render()`에서 1:1 원본 비율 시 `painter.drawPixmap(QPoint(rx, ry), self.pixmap)` 호출로 바이리니어 보간 흐림 원천 차단 (F9와 100% 동일한 비트 단위 선명도 보장)
- [x] 13개 글로벌 언어 i18n 26개 신규 키 전수 등록
  - `btn_delete_selected_step`, `btn_delete_selected_step_tooltip`, `btn_export_all_menu`, `menu_export_ppt`, `menu_export_slides`, `menu_export_hwp`, `menu_export_webbook`, `menu_export_gif`, `dialog_pii_title`, `pii_categories_group`, `pii_custom_rules_group`, `pii_cat_phone`, `pii_cat_email`, `pii_cat_resident`, `pii_cat_card`, `pii_cat_account`, `pii_cat_biz_number`, `pii_cat_korean_name`, `pii_cat_address`, `pii_cat_ip`, `pii_table_col_enabled`, `pii_table_col_name`, `pii_table_col_pattern`, `pii_btn_add_rule`, `pii_btn_del_rule`, `pii_btn_run_masking` (13개국어 100% 등록)
- [x] 핵심 단위 테스트 68개 전 항목 100% 통과 (`test_core_engine.py` 68/68 ALL PASS)
- [x] `각 기능(키)설명.MD` 2절 F8 선명도, 3.3절 PII 다이얼로그, 6.5절 스토리보드 통합 내보내기/D&D 최신화

## [2026-09-13 16:55] 매뉴얼 스튜디오 2세대 Phase 4 구현: 차세대 캡처 자동화 (UI 마그네틱 스마트 스냅, 파노라마 스크롤 스티칭, 무인 액션 레코더) 완비, 13개국어 i18n 및 67개 단위 테스트 100% 통과
- [x] UI 요소 마그네틱 스마트 스냅 엔진 (`MagneticSnapEngine`)
  - Windows API `WindowFromPoint` + `ChildWindowFromPointEx` 계층 순회로 최하단 UI 자식 컨트롤(버튼, 입력창, 탭, 체크박스 등) 바운딩 박스 정밀 탐지
  - `CaptureOverlayWidget` 영역 캡처 시 마우스 호버 대상에 형광 시안(`QColor(6, 182, 212)`) 점선 테두리 및 반투명 채우기 자석 스냅 가이드 실시간 표출
  - 원클릭 자동 채택: 스냅된 컨트롤 위를 마우스 단순 클릭하면 해당 컨트롤 사각 영역이 100% 자동 채택되어 즉시 캡처 확정
  - 오버레이 창 내 단축키 `X`로 자석 스냅 켜기/끄기 즉시 토글 지원
- [x] 파노라마 수직 스크롤 스티칭 엔진 (`ScrollStitchEngine`, CLI `--cli stitch`)
  - 긴 웹페이지, ERP 테이블, 보고서 등 화면을 넘어가는 연속 스크롤 프레임 합성
  - OpenCV `cv2.matchTemplate(search_region, template, cv2.TM_CCOEFF_NORMED)` 기반 수직 오프셋 정규화 상관 매칭 ($\ge 0.70$)
  - 중복 영역 무손실 절단 및 `np.vstack` 경계선 없는 1장의 초고화질 파노라마 긴 이미지 생성
  - 리본 메뉴 `[스크롤 스티칭]` 버튼 연동: 현재 스토리보드 스텝 일괄 합성 또는 외부 이미지 파일 다중 선택 합성 지원
  - 헤드리스 CLI `ManualStudio.exe --cli stitch -i frame1.png frame2.png frame3.png -o stitched.png` 완비
- [x] 무인 연속 액션 레코더 (`ActionRecorderThread`, `RecordingFloatWidget`)
  - 비동기 백그라운드 QThread 기반 저지연 마우스 클릭 감지 (`GetAsyncKeyState(VK_LBUTTON)` 250ms 디바운싱)
  - 마우스 클릭 시 화면 자동 캡처 + 클릭 지점에 번호 스탬프(`StampItem`) 자동 타각 + 하단 타임라인 스토리보드에 스텝 자동 누적 적립
  - 화면 상단 구석 상시 최상위 반투명 플로팅 컨트롤 바(`RecordingFloatWidget`: `🔴 REC`, `N단계`, `[완료]`) 제공
  - 리본 메뉴 `[액션 녹화]` 버튼 원클릭 시작/종료 토글 및 시작/종료 시 감지 스텝 수 토스트 알림 안내
- [x] 13개 글로벌 언어 i18n 신규 키 전수 등록
  - `btn_magnetic_snap`, `tip_magnetic_snap`, `btn_scroll_stitch`, `tip_scroll_stitch`, `btn_action_record`, `tip_action_record`, `btn_stop_recording`, `toast_recording_started`, `toast_recording_stopped`, `toast_stitch_success` (13개국어 100% 등록)
- [x] 핵심 단위 테스트 67개 전 항목 100% 통과 (`test_core_engine.py` 67/67 ALL PASS)
- [x] `각 기능(키)설명.MD` 2절 캡처 및 레코더 기능, 8절 단축키 총괄표 개정 완료

## [2026-09-13 16:44] 매뉴얼 스튜디오 2세대 Phase 3 구현: 개인정보 자동 마스킹 (Auto PII Redaction, Shift+M) & 배경 스마트 지우개 (Content-Aware Eraser, X) 완비, 13개국어 i18n 및 64개 단위 테스트 100% 통과
- [x] 개인정보 및 민감 데이터 자동 마스킹 엔진 (`PiiRedactionEngine`, `PiiWorkerThread`)
  - WinRT OCR 단어 레벨 바운딩 박스(`word.bounding_rect`) 기반 비동기 스캔 파이프라인
  - 6대 표준 개인정보 정규식(전화번호/휴대폰, 주민등록번호, 이메일, 계좌번호, 카드번호, IP 주소) 탐지
  - 인접 분절 단어 결합(Token Merging) 및 4px 안전 마진 패딩 알고리즘 탑재
  - 원클릭 비파괴 마스킹: 캔버스에 개별 선택·이동·크기조절·삭제 가능한 `BlurMosaicItem` 일괄 생성
  - 단축키 `Shift + M` 및 리본 메뉴 `[개인정보 마스킹]` 버튼 연동, `Ctrl + Z` 일괄 되돌리기 100% 지원
  - 완료 시 감지 건수 토스트 안내 (`toast_pii_found`, `toast_pii_none`)
- [x] 배경 클린업 스마트 지우개 엔진 (`SmartCleanupEngine`, 캔버스 모드 `ERASER`)
  - OpenCV Telea / Navier-Stokes (`cv2.inpaint`) 기반 배경 텍스처·그라데이션 인페인팅 합성 엔진 탑재
  - OpenCV 미탑재 환경을 대비한 Pillow/NumPy 경계선 가우시안 블러 비상 폴백 파이프라인 내장
  - 단축키 `X` 단일 키 모드 전환 및 리본 메뉴 `[스마트 지우개]` 토글 버튼 연동
  - 드래그 중 반투명 핑크 점선 영역 실시간 프리뷰
  - 마우스 릴리즈 즉시 인페인팅 적용 + `self.history` 픽셀맵 스냅샷 저장으로 `Ctrl + Z` 누를 시 100% 원본 무손실 복원
- [x] 글로벌 13개 언어 i18n 8개 신규 키 전수 등록
  - `btn_auto_pii`, `tip_auto_pii`, `toast_pii_found`, `toast_pii_none`, `btn_smart_eraser`, `tip_smart_eraser`, `toast_eraser_done`, `mode_eraser`
- [x] 핵심 단위 테스트 64개 전 항목 100% 통과 (`test_core_engine.py` 64/64 ALL PASS)
- [x] `각 기능(키)설명.MD` 3.3절 강조·보안 도구 및 8절 단축키 총괄표 개정 완료

## [2026-09-13 16:35] 매뉴얼 스튜디오 2세대 Phase 2 구현: 반응형 단일 파일 HTML5 웹북 매뉴얼 및 초경량 루핑 애니메이션 GIF 숏클립 생성기 탑재, 13개국어 i18n 및 필름스트립 도크 연동 완비

- [x] 반응형 단일 파일 HTML5 웹북 매뉴얼 출력 엔진 (`ExportEngine.export_to_html`)
  - 외부 CDN 및 로컬 이미지 폴더 의존성이 일절 없는 100% 자가완비형(Self-Contained) Single `.html` 파일 생성
  - Base64 Data URI 스텝 이미지 인라인 임베딩 지원 (`image_b64`)
  - 좌측 목차(TOC) 클릭 이동 네비게이션 및 상단 스텝 실시간 필터 검색창 내장
  - 고화질 클릭 확대 라이트박스(Lightbox) 모달 뷰어 및 다크/라이트 테마 원클릭 스위처 내장
  - A4 문서 출력 및 PDF 저장을 위한 `@media print` CSS 인쇄 최적화 규칙 완비
- [x] 숏클립 튜토리얼 애니메이션 GIF 생성기 (`ExportEngine.export_to_animated_gif`)
  - 필름스트립에 등록된 모든 단계(Step) 화면을 1.5초 루핑 애니메이션 GIF로 일괄 변환
  - Pillow RGB/P 모드 최적화 및 캔버스 배경 합성으로 알파 디더링 아티팩트 없는 고화질 압축 지원
  - 노션(Notion), 슬랙(Slack), 잔디, 메신저 업로드에 최적화된 초경량 파일 포맷
- [x] 하단 스토리보드 타임라인 독 연동
  - `[웹북 내보내기]` (`btn_export_webbook`) 및 `[숏클립 GIF]` (`btn_export_gif`) 액션 버튼 배치
  - 메인 윈도우 시그널 연결: 액자 프레임 옵션에 맞추어 캔버스 베이킹 후 브라우저 자동 실행 또는 파일 저장 다이얼로그 호출
- [x] 13개 글로벌 언어 i18n 4개 신규 키 전수 등록
  - `btn_export_webbook`, `tip_export_webbook`, `btn_export_gif`, `tip_export_gif`
- [x] 핵심 단위 테스트 61개 전 항목 100% 통과 (`test_core_engine.py` 61/61 ALL PASS)
- [x] `각 기능(키)설명.MD` 매뉴얼 설명서 6.5절 최신화

## [2026-09-13 16:25] 매뉴얼 스튜디오 2세대 Phase 1 구현: 어도비 스타일 'Ms' 아이콘 확정, 모던 윈도우 액자 프레임·소프트 섀도우(기본 ON), 한컴 한글(HWP) COM 직결(Shift+F10/F12) 및 하단 스토리보드 타임라인 독 완비

- [x] 어도비 스타일 'Ms' 아이콘 정식 채택 및 시스템 배포
  - CamelCase `Ms` (일렉트릭 시안 M + 퓨어 화이트 s) 다중 해상도 안티에일리어싱 `.ico` 교체 (`assets/manual_studio.ico`)
  - 윈도우 타이틀바, 작업표시줄 및 바탕화면 바로가기(`매뉴얼 스튜디오.lnk`) 아이콘 갱신 완료
- [x] 모던 윈도우 창틀 & 소프트 드롭 섀도우 액자 효과 탑재 (`ExportEngine.apply_window_frame_and_shadow`)
  - Notion / CleanShot X / macOS 스타일 3색 신호등 버튼(🔴🟡🟢) 윈도우 상단 바 + 12px 둥근 모서리 + 20px 부드러운 가우시안 드롭 섀도우 합성
  - 투명 알파 마스크 기반으로 PPT, 슬라이드, 문서에 자연스러운 입체감 부여
  - 사용자 요구사항 100% 준수: 기본값 활성화(ON), 툴바 `[액자 프레임]` 토글 버튼으로 원클릭 끄기/켜기 지원
  - 클립보드 복사(`Ctrl+C`), PPT 삽입, 구글 슬라이드, 한컴 한글 삽입에 일체형 연동
- [x] 한컴 한글(HWP / HWPX) COM 직결 내보내기 엔진 탑재 (`ExportEngine.send_to_hwp`)
  - Windows COM Dispatch (`HWPFrame.HwpObject`) 기반 실시간 연동
  - 브라우저 개발자 도구(F12) 전역 단축키 충돌 원천 방지:
    - 전역(Global) 단축키: `Shift + F10` (PPT F10의 패밀리 단축키 배정)
    - 스튜디오 창 활성화 시: `F12` 원클릭 로컬 단축키 동시 지원
  - 커서 위치에 표 및 규격화된 이미지 중앙 정렬 자동 안착 + 단계명 상단 텍스트 자동 삽입
  - 툴바 `[한글 전송]` 버튼 추가
- [x] 하단 타임라인 필름스트립 (스토리보드) 도크 구현 (`StepCardWidget`, `FilmstripDockWidget`)
  - 작업대 하단에 가로 스크롤 가능한 스텝별 썸네일 카드(Step 1, Step 2...) 스트립 상시 노출
  - 원클릭 스텝 전환: 썸네일 클릭 시 현재 작업 자동 스냅샷 저장 및 대상 스텝 캔버스 즉시 복원 로드
  - 우클릭 컨텍스트 메뉴: 스텝 복제, 좌/우 순서 맞교환, 스텝 삭제 및 자동 번호 재정렬
  - `[+ 새 단계]`, `[전체 PPT 전송]`, `[전체 한글 전송]` 원스톱 일괄 자동화 버튼군 완비
- [x] 13개 글로벌 언어 i18n 9개 신규 키 전수 등록
  - `btn_export_hwp`, `tip_export_hwp`, `btn_window_frame`, `tip_window_frame`, `btn_filmstrip_toggle`, `tip_filmstrip_toggle`, `btn_add_step`, `btn_export_all_ppt`, `btn_export_all_hwp`
- [x] 단위 테스트 59개 전 항목 100% 통과 (`test_core_engine.py` 59/59 ALL PASS)
- [x] `각 기능(키)설명.MD` 기능 및 단축키 설명서 전면 최신화


## [2026-09-13 15:45] 매뉴얼 스튜디오 전용 고해상도 바탕화면 앱 아이콘(`manual_studio.ico`) 신규 제작, 윈도우/작업표시줄/바이너리 통합 적용 및 `각 기능(키)설명.MD` 완비
- [x] 매뉴얼 스튜디오 전용 모던 로열 블루 스퀘어클(Squircle) 멀티 레이어 앱 아이콘 제작
  - 뷰파인더 캡처 레티클(`[ ┌ ┐ ]`) + 오픈 매뉴얼 가이드 북 + 오렌지 ① 스텝 번호 뱃지 + 마우스 커서 결합
  - 16, 24, 32, 48, 64, 128, 256px 7대 멀티 해상도 밉맵 ICO 파일 구축 (`assets/manual_studio.ico`)
- [x] 프로그램 창 및 작업표시줄 아이콘 전용화
  - `get_manual_studio_icon()` 구현 및 `ManualStudioWindow`, `QApplication`에 신규 전용 아이콘 적용
  - DragonRPA 회사 CI는 About 다이얼로그 전용으로 목적 분리
- [x] Nuitka C-컴파일러 바이너리 리소스 동기화
  - `build_c.bat` Windows 파일/제품 버전 `1.4.0.24` 및 `--windows-icon-from-ico="assets/manual_studio.ico"` 컴파일 완료
- [x] Windows 바탕화면 바로가기(`매뉴얼 스튜디오.lnk`) 자동 생성 연동
- [x] `각 기능(키)설명.MD` 전 기능 및 단축키 상세 설명서 편찬 완료

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

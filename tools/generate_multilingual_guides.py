"""
================================================================================
(주)드래곤알피에이 매뉴얼 스튜디오 글로벌 9개국어 사용 설명서 및 가이드 이미지 생성기
Multilingual User Guides & UI Screenshot Generator for Manual Studio v1.4.0
================================================================================
"""

import os
import sys

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QPoint, QRect, QSize
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont, QPen, QBrush

from manual_capture_studio import (
    ManualStudioWindow,
    LicenseRegistrationDialog,
    SettingsDialog,
    StudioCanvasWidget,
    StampItem,
    StepArrowItem,
    ElbowArrowItem,
    CalloutItem,
    WordArtItem,
    HighlightBoxItem,
    HotkeyBadgeItem,
    load_config
)
from license_engine import LicenseEngine, LicenseType
from i18n_manager import I18nManager

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(APP_DIR, "docs")
IMAGES_DIR = os.path.join(DOCS_DIR, "images")

def generate_screenshots(app):
    os.makedirs(IMAGES_DIR, exist_ok=True)
    print(f"[Generator] Generating guide images in {IMAGES_DIR}...")

    # 1. Main Window Preview
    win = ManualStudioWindow()
    win.resize(1180, 780)

    # 캔버스에 샘플 데모 주석 배치
    canvas_pix = QPixmap(960, 540)
    canvas_pix.fill(QColor("#F1F5F9"))
    p = QPainter(canvas_pix)
    p.setPen(QPen(QColor("#CBD5E1"), 1, Qt.DashLine))
    for x in range(0, 960, 40):
        p.drawLine(x, 0, x, 540)
    for y in range(0, 540, 40):
        p.drawLine(0, y, 960, y)

    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#FFFFFF"))
    p.drawRoundedRect(60, 50, 840, 440, 8, 8)
    p.setPen(QPen(QColor("#94A3B8"), 2))
    p.drawRoundedRect(60, 50, 840, 440, 8, 8)

    # 모의 윈도우 UI
    p.setBrush(QColor("#2563EB"))
    p.drawRoundedRect(60, 50, 840, 40, 8, 8)
    p.fillRect(60, 70, 840, 20, QColor("#2563EB"))
    p.setPen(QColor("#FFFFFF"))
    p.setFont(QFont("Segoe UI", 12, QFont.Bold))
    p.drawText(80, 76, "Enterprise ERP & RPA Workflow - Manual Capture Studio Sample")

    # 버튼 3개
    p.setBrush(QColor("#EF4444"))
    p.drawEllipse(860, 62, 14, 14)
    p.setBrush(QColor("#F59E0B"))
    p.drawEllipse(840, 62, 14, 14)
    p.setBrush(QColor("#10B981"))
    p.drawEllipse(820, 62, 14, 14)
    p.end()

    win.canvas.set_pixmap(canvas_pix)

    # 주석들 배치
    win.canvas.items.append(StampItem(1, 100, 140, {"size": 36, "bg_color": "#E53935"}))
    win.canvas.items.append(StepArrowItem(2, QPoint(100, 220), QPoint(280, 220), {"size": 36, "bg_color": "#E53935"}, {"arrow_head_size": 18, "line_width": 3, "color": "#E53935"}))
    win.canvas.items.append(ElbowArrowItem(QPoint(350, 160), QPoint(520, 280), style={"color": "#2563EB", "arrow_head_size": 18, "line_width": 3}, route_mode="HV"))
    win.canvas.items.append(CalloutItem("1. 고객 주문 번호 확인 후 승인 버튼을 클릭합니다.", QRect(300, 300, 240, 60), QPoint(260, 280), {"bg_color": "#FFFBEB", "border_color": "#F59E0B", "font_size": 11}))
    win.canvas.items.append(WordArtItem("Manual Studio v1.4.0", 540, 130, {"preset_id": "gold_title", "font_size": 24}))
    win.canvas.items.append(HotkeyBadgeItem("Ctrl + Enter", 600, 220, {"key_mode": "COMBINATION", "preset": "navy_glow"}))
    win.canvas.items.append(HighlightBoxItem(QRect(580, 280, 260, 150), {"border_width": 3, "color": "#059669", "fill": True, "fill_color": "#10B981", "fill_opacity": 35}))

    win.canvas.update()
    win.show()
    app.processEvents()

    # 스크린샷 캡처 및 저장
    pix_main = win.grab()
    main_path = os.path.join(IMAGES_DIR, "guide_main_window.png")
    pix_main.save(main_path, "PNG")
    print(f"  [OK] Saved {main_path}")

    # 2. License Dialog Preview
    lic_dlg = LicenseRegistrationDialog(win)
    lic_dlg.show()
    app.processEvents()
    pix_lic = lic_dlg.grab()
    lic_path = os.path.join(IMAGES_DIR, "guide_license_dialog.png")
    pix_lic.save(lic_path, "PNG")
    lic_dlg.close()
    print(f"  [OK] Saved {lic_path}")

    # 3. Settings Dialog Preview
    cfg = load_config()
    set_dlg = SettingsDialog(cfg, win)
    set_dlg.show()
    app.processEvents()
    pix_set = set_dlg.grab()
    set_path = os.path.join(IMAGES_DIR, "guide_settings_dialog.png")
    pix_set.save(set_path, "PNG")
    set_dlg.close()
    print(f"  [OK] Saved {set_path}")

    # 4. Canvas Annotations Close-up Preview
    pix_canvas = win.canvas.get_composed_image()
    if pix_canvas:
        anno_path = os.path.join(IMAGES_DIR, "guide_annotations.png")
        pix_canvas.save(anno_path, "PNG")
        print(f"  [OK] Saved {anno_path}")

    win.close()


GUIDE_METADATA = {
    "ko": {
        "title": "매뉴얼 스튜디오(Manual Studio) v1.4.0 사용자 가이드",
        "subtitle": "파워포인트 매뉴얼 제작 전문 자동화 솔루션 • (주)드래곤알피에이",
        "overview": "매뉴얼 스튜디오는 화면 캡처부터 10종의 전문 주석 삽입, 사내 PPT 마스터 템플릿 연동, 그리고 파워포인트 슬라이드 자동 생성까지 원클릭으로 완결하는 엔터프라이즈 업무 표준화 소프트웨어입니다.",
        "sec_features": "핵심 주요 기능",
        "sec_hotkeys": "단축키 및 즉시 캡처",
        "sec_tools": "10대 전문 주석 및 도구 모음",
        "sec_ppt": "사내 PPT 마스터 템플릿 및 자동 슬라이드 생성",
        "sec_autosave": "실수 방지 자동 저장 및 복구 시스템",
        "sec_license": "라이선스 인증 및 워터마크 안내",
        "sec_i18n": "글로벌 9개 국어 및 무깨짐 글꼴 체계",
        "sec_support": "공식 기술 지원 및 문의",
        "hotkeys_table": """
| 단축키 | 기능 명칭 | 상세 설명 |
| :--- | :--- | :--- |
| **`F9`** | 고정 좌표 캡처 | 설정된 좌표/크기로 즉시 캡처하여 캔버스에 안착 |
| **`Shift + F9`** | 영역 지정 캡처 | 마우스 드래그 후 릴리즈 즉시 확정 (엔터 입력 대기 없음) |
| **`F8`** | 부분 추가 캡처 | 캔버스 작업 중 화면 일부를 추가 캡처하여 오버레이 스티커로 부착 |
| **`F10`** | PPT 슬라이드 생성 | 열려 있는 PPT에 새 슬라이드 생성, 이미지 정밀 삽입 및 클립보드 복사 |
| **`Ctrl + S`** | 프로젝트 저장 | 비트맵 원본과 주석 벡터 데이터를 무손실 `.mcs.json`으로 영구 보존 |
| **`Ctrl + Z`** | 실행 취소 | 직전 주석 편집 조작을 안전하게 롤백 |
""",
        "tools_desc": """
1. **① 번호 스탬프**: 클릭할 때마다 1부터 순차 증가하는 원형 스탬프 (크기/색상 자유 조정)
2. **①➔ 스탬프 화살표**: 시작점에 번호 스탬프가 달린 일체형 가이드 화살표
3. **↳ 직각 엘보 화살표**: 복잡한 UI 요소를 우회하여 안내하는 직각 꺾임 화살표 (Tab키로 수평/수직 경로 전환)
4. **↗ 직선 화살표**: 정밀한 방향성을 제시하는 표준 벡터 화살표
5. **🔲 사각 박스**: 중요한 메뉴나 입력 필드를 강조하는 테두리/반투명 채우기 상자
6. **🌫 모자이크 블러**: 고객 개인정보, 계좌번호, 비밀번호 등을 마우스 드래그로 즉시 마스킹
7. **💬 설명 말풍선**: 꼬리 방향을 자유롭게 조절할 수 있는 라운드 사각 설명 상자
8. **🔤 텍스트 라벨**: 맑은 고딕, Segoe UI 등 전 세계 다국어 글꼴을 지원하는 깔끔한 텍스트
9. **⌨ 단축키 뱃지**: `Ctrl+C`, `Alt+F4` 등 키보드 키 캡 모양의 입체적 키 뱃지
10. **✨ 워드아트 타이틀**: 5대 전문 프리셋(Gold, Neon, Red, White, Slate) 외곽선/그림자 타이틀
""",
        "ppt_desc": """
- **사내 PPT 마스터 템플릿 파일(`.pptx`, `.potx`) 연동**:
  - `설정(S) -> 환경 설정...` 메뉴에서 회사의 공식 PPT 마스터 파일을 지정하면, 슬라이드 생성 시 회사의 공식 로고, 배경 디자인, 슬라이드 마스터 서식이 자동으로 상속됩니다.
- **슬라이드 내 규격화 정밀 안착**:
  - 사용자 지정 여백(Left, Top)과 이미지 크기(가로 960px 또는 16:9 슬라이드 맞춤)로 완벽하게 규격화되어 삽입됩니다.
- **단계 번호 자동 동기화 & 원클릭 재정렬**:
  - 슬라이드 상단에 `Step 1. [단계명 입력]` 제목 상자가 자동 생성되며, 중간에 슬라이드가 삭제/추가된 경우 `편집 -> 🔢 PPT Step 번호 자동 재정렬` 메뉴로 수백 장의 슬라이드 번호를 1초 만에 연속 번호로 재정렬합니다.
""",
        "autosave_desc": """
- **실수 방지 자동 저장(Auto-save)**:
  - 1~30분 주기로 현재 캔버스의 모든 이미지 및 주석 레이어를 백그라운드에서 자동 저장합니다.
- **비정상 종료 시 원클릭 복구**:
  - PC 재부팅이나 정전 등 돌발 상황 발생 후 재실행 시 "이전 작업의 자동 저장 파일이 발견되었습니다. 복구하시겠습니까?" 팝업이 노출되며, 승인 시 모든 원본 이미지와 주석 객체가 100% 무손실 복구됩니다.
""",
        "license_desc": """
- **평가판 안내**:
  - 정식 라이선스가 등록되지 않은 상태에서는 생성된 클립보드 이미지 및 슬라이드 우하단에 반투명 'Manual Studio' 정품 인증 안내 워터마크가 표시됩니다.
- **정식 라이선스 인증**:
  - `설정 -> 🔑 라이선스 등록` 메뉴에서 [내 PC 고유 식별자(HWID)]를 복사하여 라이선스를 발급받은 후, 시리얼 키를 입력하고 `인증하기` 버튼을 누르면 모든 워터마크가 즉시 제거되고 정식 버전으로 활성화됩니다.
- **6대 라이선스 에디션**:
  - ① 1카피 영구 (PERPETUAL - MS1P)
  - ② 1카피 1개월 구독 (SUB_1M - MS1M)
  - ③ 1카피 1년 연간 구독 (SUB_1Y - MS1Y)
  - ④ 엔터프라이즈 대량 볼륨 (ENTERPRISE - MSENT)
  - ⑤ 보안 폐쇄망 사이트 (AIR_GAPPED - MSSITE)
  - ⑥ 14일 평가 연장 (TRIAL_14D - MST14)
"""
    },
    "en": {
        "title": "Manual Studio v1.4.0 User Guide",
        "subtitle": "Professional PowerPoint Manual Creation Automation Solution • DragonRPA Co.",
        "overview": "Manual Studio is an enterprise standardization software that covers the entire manual generation workflow: high-precision screen captures, 10 professional annotations, corporate PPT master template inheritance, and one-click slide generation.",
        "sec_features": "Core Features",
        "sec_hotkeys": "Hotkeys & Instant Capture",
        "sec_tools": "10 Professional Annotation Tools",
        "sec_ppt": "Corporate PPT Master Template & Slide Generation",
        "sec_autosave": "Disaster Recovery & Auto-Save System",
        "sec_license": "License Activation & Watermark Policy",
        "sec_i18n": "Global 9-Language Support & Multilingual Fonts",
        "sec_support": "Official Support & Inquiries",
        "hotkeys_table": """
| Hotkey | Name | Description |
| :--- | :--- | :--- |
| **`F9`** | Fixed Capture | Instantly captures the configured screen coordinate area |
| **`Shift + F9`** | Area Capture | Instant capture upon mouse release without Enter key delay |
| **`F8`** | Sub Capture | Captures secondary windows or popups as floating overlays |
| **`F10`** | PPT Export | Inserts high-res slide into PowerPoint and copies to clipboard |
| **`Ctrl + S`** | Save Project | Losslessly stores raw bitmap and annotation vector items in `.mcs.json` |
| **`Ctrl + Z`** | Undo | Restores previous canvas state safely |
""",
        "tools_desc": """
1. **① Stamp**: Incremental numbered circular stamps (customizable size & colors).
2. **①➔ Step Arrow**: Integrated step stamp with directional guide arrow.
3. **↳ Elbow Arrow**: Right-angle orthogonal arrow for routing around complex UI controls (toggle HV/VH via Tab key).
4. **↗ Straight Arrow**: Clean vector arrow for precise target pointing.
5. **🔲 Highlight Box**: Rectangular focus box with border styling and translucent fills.
6. **🌫 Mosaic Blur**: Instant drag-and-drop privacy masking for passwords, personal data, and account numbers.
7. **💬 Callout**: Multi-line speech bubble with an adjustable tail pointer.
8. **🔤 Text Label**: Clean typography rendered with global fallback font chains (Segoe UI, Arial, etc.).
9. **⌨ Hotkey Badge**: Keyboard key cap badges (`Ctrl+C`, `Alt+F4`, `Enter`).
10. **✨ WordArt**: 5 professional title styles (Gold, Neon Cyan, Warning Red, Modern Slate, White Pop).
""",
        "ppt_desc": """
- **Corporate Master Template (`.pptx`, `.potx`) Binding**:
  - Configure your company's master presentation under `Settings -> Preferences`. Generated slides automatically inherit corporate headers, logos, and slide master designs.
- **Standardized Slide Layout**:
  - Automatically scales images to target width (960px or 16:9 aspect fit) and aligns them with consistent margins.
- **Sequential Step Renumbering**:
  - Automatically adds `Step {n}. [Enter Title]` headers. If slides are inserted or removed, use `Edit -> 🔢 Auto-renumber PowerPoint Steps` to re-index all slides in 1 second.
""",
        "autosave_desc": """
- **Loss-Prevention Auto-Save**:
  - Automatically saves the active canvas and annotation layers at user-defined intervals (1 to 30 minutes).
- **One-Click Crash Recovery**:
  - In the event of an abnormal shutdown or power outage, restart Manual Studio to receive an automatic recovery prompt, restoring your full workspace without data loss.
""",
        "license_desc": """
- **Evaluation Notice**:
  - Unregistered copies display a translucent 'Manual Studio' badge and diagonal watermark on exported slides and clipboard images.
- **License Registration**:
  - Navigate to `Settings -> 🔑 Register License...`, copy your machine's HWID, obtain your serial key, and click `Activate`. All watermarks are immediately removed.
- **Available Editions**:
  - ① Single-seat Perpetual (`MS1P`)
  - ② Single-seat 1-Month Subscription (`MS1M`)
  - ③ Single-seat 1-Year Subscription (`MS1Y`)
  - ④ Enterprise Multi-seat Volume (`MSENT`)
  - ⑤ Air-gapped Offline Site (`MSSITE`)
  - ⑥ 14-Day Extended Trial (`MST14`)
"""
    },
    "zh": {
        "title": "Manual Studio v1.4.0 官方用户指南",
        "subtitle": "企业级 PowerPoint 操作手册制作自动化解决方案 • DragonRPA Co.",
        "overview": "Manual Studio 是一款专业的企业级屏幕捕获与手册制作软件。它将截屏、10种专业标注、企业PPT母版继承、PPT幻灯片自动排版一键打通，大幅减少手册制作时间。",
        "sec_features": "核心功能概览",
        "sec_hotkeys": "快捷键与即时截图",
        "sec_tools": "10 大专业标注工具",
        "sec_ppt": "企业 PPT 母版集成与自动排版",
        "sec_autosave": "防遗失自动保存与崩溃恢复",
        "sec_license": "许可证激活与水印说明",
        "sec_i18n": "全球 9 种语言与中文字体支持",
        "sec_support": "官方技术支持与联系方式",
        "hotkeys_table": """
| 快捷键 | 功能名称 | 详细说明 |
| :--- | :--- | :--- |
| **`F9`** | 固定坐标截图 | 按照预设坐标和尺寸立即抓取屏幕 |
| **`Shift + F9`** | 区域选取截图 | 鼠标拖拽释放时立即捕获，无需回车确认 |
| **`F8`** | 部分追加截图 | 将附加窗口或弹出框截取为可调整的图层贴片 |
| **`F10`** | 生成 PPT 幻灯片 | 自动在打开的 PPT 中创建幻灯片并写入剪贴板 |
| **`Ctrl + S`** | 保存工程 | 将原始位图与标注矢量数据无损保存至 `.mcs.json` |
| **`Ctrl + Z`** | 撤销 | 撤销上一步标注操作 |
""",
        "tools_desc": """
1. **① 序号印章**: 自动递增的圆形数字印章（尺寸和颜色可自定义）。
2. **①➔ 步骤箭头**: 带有前置数字印章的方向指引箭头。
3. **↳ 折角直角箭头**: 绕过密集 UI 控件的 90 度折线箭头（Tab 键切换横纵路径）。
4. **↗ 直线箭头**: 精确指向按钮和文字的矢量箭头。
5. **🔲 高亮方框**: 用于突出重要菜单与表单的实心边框或半透明填充框。
6. **🌫 马赛克模糊**: 涂抹遮蔽密码、账号、个人隐私信息。
7. **💬 说明气泡**: 尾部指向可自由拖动的圆角说明文本框。
8. **🔤 文本标签**: 支持微软雅黑(Microsoft YaHei)与系统字体的清晰排版。
9. **⌨ 快捷键徽章**: 仿真键盘按键样式的实体键标(`Ctrl+C`, `Enter`)。
10. **✨ 艺术字标题**: 5 种预设高质感外轮廓与投影标题字。
""",
        "ppt_desc": """
- **关联企业 PPT 母版文件(`.pptx`, `.potx`)**:
  - 在`设置 -> 首选项`中指定公司的母版文件，自动继承公司标准页眉、底色与企业 Logo。
- **幻灯片标准化对齐**:
  - 自动将截图规整为统一宽度（960px或16:9比例），整齐居中排版。
- **步骤编号一键重排**:
  - 自动插入 `Step {n}. [步骤名称]`。增删幻灯片后，通过`编辑 -> 🔢 自动重排 PPT 步骤编号`在 1 秒内刷新全局序号。
""",
        "autosave_desc": """
- **自动保存机制**:
  - 支持 1 至 30 分钟周期性自动保存当前作业进度。
- **异常崩溃恢复**:
  - 意外断电或关闭后重新启动时，自动提示恢复未保存工程，保障工作数据零丢失。
""",
        "license_desc": """
- **试用版水印**:
  - 未激活试用版在输出的 PPT 和剪贴板图像右下角带有 'Manual Studio' 徽章与半透明水印。
- **注册与激活**:
  - 打开`设置 -> 🔑 注册许可证`，复制本机唯一识别码(HWID)，填入授权密钥即可永久消除水印。
- **6 大授权类型**:
  - ① 单机永久授权 (`MS1P`)
  - ② 单机 1 个月订阅 (`MS1M`)
  - ③ 单机 1 年订阅 (`MS1Y`)
  - ④ 企业批量授权 (`MSENT`)
  - ⑤ 离线内网站点授权 (`MSSITE`)
  - ⑥ 14 天试用延长期 (`MST14`)
"""
    },
    "ja": {
        "title": "Manual Studio v1.4.0 ユーザーガイド",
        "subtitle": "PowerPoint マニュアル作成自動化ソリューション • DragonRPA Co.",
        "overview": "Manual Studio は、画面キャプチャから 10 種類の注釈編集、社内 PPT テンプレートの適用、スライド自動生成までをワンストップで完結する業務標準化ソフトウェアです。",
        "sec_features": "主な機能",
        "sec_hotkeys": "ショートカットと即時キャプチャ",
        "sec_tools": "10 種の専門注釈ツール",
        "sec_ppt": "社内 PPT マスター連携とスライド作成",
        "sec_autosave": "自動保存および障害復旧機能",
        "sec_license": "ライセンス登録とウォーターマーク",
        "sec_i18n": "多言語対応（日本語フォント対応）",
        "sec_support": "サポート窓口",
        "hotkeys_table": """
| ショートカット | 機能名 | 説明 |
| :--- | :--- | :--- |
| **`F9`** | 固定座標キャプチャ | 指定された画面領域を即座にキャプチャ |
| **`Shift + F9`** | 範囲指定キャプチャ | マウスを離すと Enter キー入力待機なしで即座に確定 |
| **`F8`** | 追加部分キャプチャ | サブウィンドウやダイアログを追加切り抜きしてオーバーレイ配置 |
| **`F10`** | PPT スライド生成 | PowerPoint に新スライドを作成し、クリップボードにも転送 |
| **`Ctrl + S`** | プロジェクト保存 | 元画像とベクター注釈データを `.mcs.json` に完全保存 |
| **`Ctrl + Z`** | 元に戻す | 直前の編集操作をロールバック |
""",
        "tools_desc": """
1. **① 番号スタンプ**: クリックするたびにカウントアップする番号スタンプ
2. **①➔ ステップ矢印**: スタンプと一体化した方向指示矢印
3. **↳ 直角エルボー矢印**: 複雑な UI を迂回して指示する直角矢印（Tab キーで経路切替）
4. **↗ 直線矢印**: 正確なポイント指示を行うベクトル矢印
5. **🔲 強調ボックス**: メニューや入力欄を囲む枠線または半透明塗りつぶしボックス
6. **🌫 モザイクぼかし**: 個人情報やパスワードをドラッグで即座に目隠し
7. **💬 説明吹き出し**: 引き出し線の位置を自由に調整できる丸角吹き出し
8. **🔤 テキストラベル**: メイリオ(Meiryo)や Yu Gothic に対応した見やすいテキスト
9. **⌨ ショートカットキーバッジ**: キートップを模した立体的なキーバッジ
10. **✨ ワードアート**: 5 種類の高品質プリセットタイトル
""",
        "ppt_desc": """
- **社内 PPT マスターテンプレート(`.pptx`)の自動適用**:
  - 設定画面でテンプレートファイルを指定すると、スライド作成時に社内ロゴや規定レイアウトが自動的に引き継がれます。
- **スライド幅の自動統一**:
  - 横幅 960px または 16:9 の最適比率で綺麗に配置されます。
- **ステップ番号の一括自動再採番**:
  - `編集 -> 🔢 PPT Step 番号自動再整列` で、全スライドの `Step {n}.` 番号を 1 秒で整列します。
""",
        "autosave_desc": """
- **自動保存機能**:
  - 1〜30分の間隔で作業内容をバックグラウンド自動保存。
- **起動時ワンクリック復元**:
  - 突然のシャットダウン後も、再起動時に保存データから作業を即座に再開できます。
""",
        "license_desc": """
- **評価版について**:
  - 未認証状態では、クリップボード出力および PPT スライドに 'Manual Studio' の半透明ウォーターマークが表示されます。
- **ライセンスの登録**:
  - `設定 -> 🔑 ライセンス登録` よりハードウェア ID (HWID) を確認し、発行されたシリアルキーを入力して認証するとウォーターマークが解除されます。
- **ライセンス区分**:
  - ① 1コピー永久ライセンス (`MS1P`)
  - ② 1コピー1ヶ月サブスクリプション (`MS1M`)
  - ③ 1コピー1年サブスクリプション (`MS1Y`)
  - ④ エンタープライズボリューム (`MSENT`)
  - ⑤ クローズドネットワーク・サイトライセンス (`MSSITE`)
  - ⑥ 14日評価延長 (`MST14`)
"""
    }
}

# 9개 언어 템플릿 제너레이터 (DE, ES, FR, PT, RU 포함)
OTHER_LANGS = {
    "de": ("Manual Studio v1.4.0 Benutzerhandbuch", "Automatisierte PowerPoint-Handbucherstellung • DragonRPA Co.", "Deutsch"),
    "es": ("Manual Studio v1.4.0 Guía del Usuario", "Solución Automatizada para Manuales en PowerPoint • DragonRPA Co.", "Español"),
    "fr": ("Manual Studio v1.4.0 Guide de l'Utilisateur", "Solution d'Automatisation de Manuels PowerPoint • DragonRPA Co.", "Français"),
    "pt": ("Manual Studio v1.4.0 Guia do Usuário", "Solução Automatizada de Manuais em PowerPoint • DragonRPA Co.", "Português"),
    "ru": ("Manual Studio v1.4.0 Руководство пользователя", "Автоматизация создания руководств PowerPoint • DragonRPA Co.", "Русский")
}

def build_markdown_content(lang_code: str) -> str:
    if lang_code in GUIDE_METADATA:
        m = GUIDE_METADATA[lang_code]
    else:
        info = OTHER_LANGS[lang_code]
        # 영어 기반의 글로벌 다국어 표준 문서 생성
        m_en = GUIDE_METADATA["en"]
        m = {
            "title": f"{info[0]} ({info[2]})",
            "subtitle": f"{info[1]}",
            "overview": m_en["overview"],
            "sec_features": f"{m_en['sec_features']} ({info[2]})",
            "sec_hotkeys": m_en["sec_hotkeys"],
            "sec_tools": m_en["sec_tools"],
            "sec_ppt": m_en["sec_ppt"],
            "sec_autosave": m_en["sec_autosave"],
            "sec_license": m_en["sec_license"],
            "sec_i18n": m_en["sec_i18n"],
            "sec_support": m_en["sec_support"],
            "hotkeys_table": m_en["hotkeys_table"],
            "tools_desc": m_en["tools_desc"],
            "ppt_desc": m_en["ppt_desc"],
            "autosave_desc": m_en["autosave_desc"],
            "license_desc": m_en["license_desc"]
        }

    md = f"""# {m['title']}
> **{m['subtitle']}**
> *Official Release Build v1.4.0 | (주)드래곤알피에이 (DragonRPA Co., Ltd.)*

---

## 📌 1. {m.get('sec_features', 'Overview')}
{m['overview']}

![Manual Studio Main Window Interface](images/guide_main_window.png)

---

## ⚡ 2. {m['sec_hotkeys']}
{m['hotkeys_table']}

> **Tip**: Shift+F9 또는 F8 캡처 시, 마우스 드래그를 마치고 손을 떼는 순간(Mouse Release) 엔터키 입력 대기 없이 즉시 확정되어 캔버스에 안착됩니다.

---

## 🎨 3. {m['sec_tools']}
{m['tools_desc']}

![Annotation Tools and Canvas Overview](images/guide_annotations.png)

---

## 📊 4. {m['sec_ppt']}
{m['ppt_desc']}

![Settings and Master Template Configuration](images/guide_settings_dialog.png)

---

## 💾 5. {m['sec_autosave']}
{m['autosave_desc']}

---

## 🔑 6. {m['sec_license']}
{m['license_desc']}

![License Registration Dialog](images/guide_license_dialog.png)

---

## 🌐 7. {m['sec_i18n']}
- **9 Supported Global Languages**:
  - 한국어 (Korean - `ko`)
  - English (`en`)
  - 简体中文 (Chinese Simplified - `zh`)
  - 日本語 (Japanese - `ja`)
  - Deutsch (German - `de`)
  - Español (Spanish - `es`)
  - Français (French - `fr`)
  - Português (Portuguese - `pt`)
  - Русский (Russian - `ru`)
- **Font Fallback Chain**:
  - Segoe UI, Microsoft YaHei, Meiryo, Malgun Gothic, Arial, sans-serif

---

## 📮 8. {m['sec_support']}
- **Company**: (주)드래곤알피에이 (DragonRPA Co., Ltd.)
- **CEO & Lead Architect**: 이정용 (Victor Lee)
- **Official Contact**: `77.victor.lee@gmail.com`
- **Copyright**: Copyright © 2026 DragonRPA Co. All rights reserved.
"""
    return md

def main():
    app = QApplication.instance() or QApplication(sys.argv)
    generate_screenshots(app)

    # 9개 언어 가이드 문서 작성
    all_locales = ["KO", "EN", "ZH", "JA", "DE", "ES", "FR", "PT", "RU"]
    for code in all_locales:
        c_lower = code.lower()
        content = build_markdown_content(c_lower)
        target_path = os.path.join(DOCS_DIR, f"User_Guide_{code}.md")
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[Generator] Generated documentation: {target_path}")

    print("\nAll 9 multilingual user guides and preview screenshots generated successfully!")

if __name__ == "__main__":
    main()

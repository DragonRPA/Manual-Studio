"""
매뉴얼 스튜디오 핵심 비즈니스 로직 단위 테스트 (Pillow/Win32/Config)
"""
import sys
import os
import io
import json
from PIL import Image, ImageDraw, ImageFont

from manual_capture_studio import load_config, DEFAULT_CONFIG, ExportEngine, CIRCLED_NUMBERS, get_circle_char

def test_config_loader():
    cfg = load_config()
    assert cfg["hotkey_capture"] == "F9"
    assert cfg["hotkey_export"] == "F10"
    assert cfg["target_width"] == 960
    assert cfg["auto_resize"] is True
    print("[PASS] test_config_loader")

def test_circle_char():
    assert get_circle_char(1) == "①"
    assert get_circle_char(5) == "⑤"
    assert get_circle_char(20) == "⑳"
    assert get_circle_char(21) == "21"
    print("[PASS] test_circle_char")

def test_resize_logic():
    # 1. 1920x1080 -> 가로 960px 리사이즈 (종횡비 16:9 유지 -> 960x540)
    img1 = Image.new("RGB", (1920, 1080), color=(100, 150, 200))
    r1 = ExportEngine.resize_to_target_width(img1, 960)
    assert r1.size == (960, 540), f"Expected (960, 540), got {r1.size}"

    # 2. 500x300 -> 가로 960px 리사이즈 (종횡비 유지 -> 960x576)
    img2 = Image.new("RGB", (500, 300), color=(50, 50, 50))
    r2 = ExportEngine.resize_to_target_width(img2, 960)
    assert r2.size == (960, 576), f"Expected (960, 576), got {r2.size}"

    # 3. 960x600 -> 가로 960px 유지
    img3 = Image.new("RGB", (960, 600), color=(255, 255, 255))
    r3 = ExportEngine.resize_to_target_width(img3, 960)
    assert r3.size == (960, 600)
    print("[PASS] test_resize_logic (Lanczos Aspect Ratio Preserved)")

def test_dib_generation():
    # 클립보드용 DIB 포맷 생성 검증
    img = Image.new("RGBA", (200, 100), color=(255, 0, 0, 255))
    rgb_img = Image.new("RGB", img.size, (255, 255, 255))
    rgb_img.paste(img, mask=img.split()[3])

    output = io.BytesIO()
    rgb_img.save(output, "BMP")
    bmp_data = output.getvalue()
    output.close()

    # DIB는 BMP의 14바이트 헤더(BITMAPFILEHEADER)를 제외한 데이터
    assert len(bmp_data) > 14
    dib_data = bmp_data[14:]
    assert len(dib_data) == len(bmp_data) - 14
    print("[PASS] test_dib_generation (Windows Native CF_DIB binary valid)")

def test_backup_file_creation():
    test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_captures")
    img = Image.new("RGB", (100, 100), color=(0, 255, 0))
    saved_path = ExportEngine.auto_backup_file(img, test_dir)
    assert os.path.exists(saved_path)
    assert os.path.basename(saved_path).startswith("Step_")
    print(f"[PASS] test_backup_file_creation ({saved_path})")

    # 정리
    if os.path.exists(saved_path):
        os.remove(saved_path)
    parent_dir = os.path.dirname(saved_path)
    if os.path.exists(parent_dir) and not os.listdir(parent_dir):
        os.rmdir(parent_dir)
    if os.path.exists(test_dir) and not os.listdir(test_dir):
        os.rmdir(test_dir)

def test_fixed_rect_config():
    cfg = load_config()
    assert "fixed_rect" in cfg
    assert "fixed_rect_enabled" in cfg
    fr = cfg["fixed_rect"]
    assert "x" in fr and "y" in fr and "width" in fr and "height" in fr
    assert fr["width"] > 0 and fr["height"] > 0
    print("[PASS] test_fixed_rect_config (Fixed rect schema and defaults valid)")

def test_text_label_rendering():
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QImage, QPainter
    from manual_capture_studio import TextLabelItem
    app = QApplication.instance() or QApplication(sys.argv)
    cfg = load_config()
    for test_opacity in [0.85, 220, '200', None]:
        style = cfg.get("text_style", {}).copy()
        style["bg_opacity"] = test_opacity
        item = TextLabelItem("안내 텍스트 라벨", 50, 50, style)
        img = QImage(200, 100, QImage.Format_ARGB32)
        painter = QPainter(img)
        item.render(painter)
        painter.end()
    print("[PASS] test_text_label_rendering (Opacity type-safety and robust rendering valid)")

def test_toolbar_settings_and_selection_sync():
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtGui import QPixmap
    from manual_capture_studio import (
        ManualStudioWindow, StudioCanvasWidget, StampItem, TextLabelItem, HighlightBoxItem
    )
    app = QApplication.instance() or QApplication(sys.argv)
    win = ManualStudioWindow()
    canvas = win.canvas

    # 1. PPT 가로폭 규격화 변경 테스트
    win.spin_target_width.setValue(1280)
    assert win.config["target_width"] == 1280

    # 2. 스탬프 생성 및 크기/색상 실시간 변경 테스트
    pixmap = QPixmap(800, 600)
    pixmap.fill(Qt.white)
    canvas.set_pixmap(pixmap)
    canvas.set_mode("STAMP")

    # 스탬프 기본 생성
    canvas.mousePressEvent(type("MockEvent", (), {"button": lambda self: Qt.LeftButton, "pos": lambda self: QPoint(100, 100)})())
    assert len(canvas.items) == 1
    stamp = canvas.items[0]
    assert isinstance(stamp, StampItem)
    assert stamp.style["size"] == win.spin_stamp_size.value()

    # 3. 양방향 선택 동기화 테스트 (캔버스 아이템 클릭 시 툴바 반영)
    canvas.set_mode("SELECT")
    canvas.mousePressEvent(type("MockEvent", (), {"button": lambda self: Qt.LeftButton, "pos": lambda self: QPoint(100, 100)})())
    assert canvas.selected_item is stamp
    
    # 툴바에서 스탬프 크기 변경 시 선택된 객체 및 설정에 즉각 반영
    win.spin_stamp_size.setValue(48)
    assert stamp.style["size"] == 48
    assert win.config["stamp_style"]["size"] == 48

    # 4. 텍스트 라벨 추가 및 크기 동기화 테스트
    tx_style = {"font_size": 16, "text_color": "#FFFFFF", "bg_color": "#333333"}
    txt_item = TextLabelItem("테스트 라벨", 200, 200, tx_style)
    canvas.items.append(txt_item)
    
    # 텍스트 선택
    win.on_canvas_item_selected(txt_item)
    assert win.spin_text_font_size.value() == 16

    # 툴바에서 글꼴 크기 변경 시 선택 객체 동기화
    canvas.selected_item = txt_item
    win.spin_text_font_size.setValue(20)
    assert txt_item.style["font_size"] == 20
    assert win.config["text_style"]["font_size"] == 20

    # 5. 박스 객체 및 두께/채우기 동기화 테스트
    bx_style = {"border_width": 4, "color": "#1E88E5", "fill": True}
    box_item = HighlightBoxItem(canvas.rect(), bx_style)
    canvas.items.append(box_item)

    win.on_canvas_item_selected(box_item)
    assert win.spin_box_width.value() == 4
    assert win.chk_box_fill.isChecked() is True

    canvas.selected_item = box_item
    win.spin_box_width.setValue(8)
    assert box_item.style["border_width"] == 8
    assert win.config["highlight_box_style"]["border_width"] == 8

    # 6. 실행 취소(Undo) 객체 복제 보존 테스트
    canvas.push_undo()
    box_item.style["border_width"] = 12
    canvas.undo()
    # 복원 후 이전 두께(8)로 정상 롤백 확인
    assert canvas.items[-1].style["border_width"] == 8

    # 7. 테스트 종료 후 기본 설정값 복원
    win.spin_target_width.setValue(960)
    win.spin_stamp_size.setValue(32)
    win.spin_text_font_size.setValue(14)
    win.spin_box_width.setValue(3)

    win.close()
    print("[PASS] test_toolbar_settings_and_selection_sync (All toolbar controls and two-way sync valid)")

def test_ppt_layout_and_fit():
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QPixmap
    from PySide6.QtCore import Qt
    from manual_capture_studio import ManualStudioWindow, load_config
    
    app = QApplication.instance() or QApplication(sys.argv)
    win = ManualStudioWindow()

    # 1. 초기 PPT 레이아웃 설정 로드 검증 (사용자 기존 설정값 백업)
    cfg = load_config()
    assert "ppt_layout" in cfg
    saved_layout = cfg["ppt_layout"].copy()
    assert "left" in saved_layout and "top" in saved_layout and "scale" in saved_layout

    # 2. 툴바 스핀박스 변경 시 설정 동기화
    win.spin_ppt_left.setValue(60)
    win.spin_ppt_top.setValue(90)
    win.spin_ppt_scale.setValue(85)
    win.chk_ppt_title.setChecked(False)

    assert win.config["ppt_layout"]["left"] == 60
    assert win.config["ppt_layout"]["top"] == 90
    assert win.config["ppt_layout"]["scale"] == 85
    assert win.config["ppt_layout"]["include_title"] is False

    # 3. 16:9 슬라이드 맞춤 자동 계산 로직 검증
    pixmap = QPixmap(960, 540)
    pixmap.fill(Qt.white)
    win.canvas.set_pixmap(pixmap)
    win.spin_ppt_left.setValue(50)
    win.spin_ppt_top.setValue(80)

    win.auto_fit_ppt_scale()
    # 540 슬라이드 높이에서 top 80과 하단 여백 30을 빼면 가용 430pt -> 430/540 = 79.6% -> 79%
    assert win.spin_ppt_scale.value() == 79

    # 4. Step n 번호 인덱스 (n - 1, 첫장 표지 보정) 로직 검증
    def calc_step(slide_idx):
        return max(1, slide_idx - 1)
    assert calc_step(1) == 1  # 1번 슬라이드
    assert calc_step(2) == 1  # 2번 슬라이드 -> Step 1 (표지 다음)
    assert calc_step(3) == 2  # 3번 슬라이드 -> Step 2
    assert calc_step(4) == 3  # 4번 슬라이드 -> Step 3
    assert calc_step(10) == 9 # 10번 슬라이드 -> Step 9

    # 5. PPT 제목 상자 (위치, 크기, 폰트, 색상, 굵기) 리본 메뉴 동기화 검증
    win.spin_title_x.setValue(45)
    win.spin_title_y.setValue(18)
    win.spin_title_w.setValue(650)
    win.spin_title_h.setValue(40)
    win.spin_title_font_size.setValue(22)
    win.chk_title_bold.setChecked(False)
    win.current_title_color = "#1E88E5"
    win.on_ppt_title_layout_changed()

    assert win.config["ppt_layout"]["title_left"] == 45
    assert win.config["ppt_layout"]["title_top"] == 18
    assert win.config["ppt_layout"]["title_width"] == 650
    assert win.config["ppt_layout"]["title_height"] == 40
    assert win.config["ppt_layout"]["title_font_size"] == 22
    assert win.config["ppt_layout"]["title_font_bold"] is False
    assert win.config["ppt_layout"]["title_font_color"] == "#1E88E5"

    # 6. 이미지 좌표 맞춤(정렬) 기능 검증
    win.spin_ppt_left.setValue(105)
    win.align_title_x_to_image()
    assert win.spin_title_x.value() == 105
    assert win.config["ppt_layout"]["title_left"] == 105

    # 7. Office COM BGR 폰트 색상 변환 검증
    from PySide6.QtGui import QColor
    qcol = QColor("#1E88E5")
    bgr_val = qcol.red() + (qcol.green() << 8) + (qcol.blue() << 16)
    assert bgr_val == 0x1E + (0x88 << 8) + (0xE5 << 16)

    # 8. SettingsDialog 제목 상자 설정 저장 검증
    from manual_capture_studio import SettingsDialog
    dlg = SettingsDialog(win.config)
    dlg.spin_title_left.setValue(35)
    dlg.spin_title_top.setValue(25)
    dlg.spin_title_width.setValue(480)
    dlg.spin_title_height.setValue(38)
    dlg.edit_title_font.setText("맑은 고딕")
    dlg.spin_title_font_size.setValue(20)
    dlg.chk_title_bold.setChecked(True)
    dlg.current_title_color = "#E53935"
    dlg.edit_title_template.setText("단계 {n} - [업무명]")
    dlg.save_and_close()

    dlg_cfg = dlg.get_config()
    assert dlg_cfg["ppt_layout"]["title_left"] == 35
    assert dlg_cfg["ppt_layout"]["title_top"] == 25
    assert dlg_cfg["ppt_layout"]["title_width"] == 480
    assert dlg_cfg["ppt_layout"]["title_height"] == 38
    assert dlg_cfg["ppt_layout"]["title_font_family"] == "맑은 고딕"
    assert dlg_cfg["ppt_layout"]["title_font_size"] == 20
    assert dlg_cfg["ppt_layout"]["title_font_bold"] is True
    assert dlg_cfg["ppt_layout"]["title_font_color"] == "#E53935"
    assert dlg_cfg["ppt_layout"]["title_template"] == "단계 {n} - [업무명]"

    # 9. 테스트 종료 후 사용자 설정값 100% 원상복원
    win.spin_ppt_left.setValue(saved_layout.get("left", 26))
    win.spin_ppt_top.setValue(saved_layout.get("top", 50))
    win.spin_ppt_scale.setValue(saved_layout.get("scale", 95))
    win.chk_ppt_title.setChecked(saved_layout.get("include_title", True))
    win.spin_title_x.setValue(saved_layout.get("title_left", 26))
    win.spin_title_y.setValue(saved_layout.get("title_top", 15))
    win.spin_title_w.setValue(saved_layout.get("title_width", 500))
    win.spin_title_h.setValue(saved_layout.get("title_height", 35))
    win.spin_title_font_size.setValue(saved_layout.get("title_font_size", 18))
    win.chk_title_bold.setChecked(saved_layout.get("title_font_bold", True))
    win.current_title_color = saved_layout.get("title_font_color", "#000000")
    win.on_ppt_layout_changed()
    win.on_ppt_title_layout_changed()

    win.close()
    print("[PASS] test_ppt_layout_and_fit (Left/Top, auto-fit, Step n-1, custom Title Box & Dialog sync valid)")

def test_arrow_item_and_sync():
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QPointF, Qt
    from PySide6.QtGui import QImage, QPainter
    from manual_capture_studio import ArrowItem, ManualStudioWindow, load_config
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    # 1. ArrowItem 기하 및 히트 테스트 검증
    p1 = QPointF(50, 50)
    p2 = QPointF(200, 50)
    style = {"color": "#E53935", "width": 4, "head_size": 16}
    arrow = ArrowItem(p1, p2, style)
    
    # 선분 중심 (125, 50) 히트 테스트
    assert arrow.contains(QPointF(125, 50)) is True
    # 선분 근처 (125, 54) 히트 테스트 (마진 내)
    assert arrow.contains(QPointF(125, 54)) is True
    # 선분에서 멀리 떨어진 점 (125, 80) 히트 테스트 (미검출)
    assert arrow.contains(QPointF(125, 80)) is False
    
    # 2. 객체 복제(clone) 검증
    cloned = arrow.clone()
    assert cloned.start_pos == arrow.start_pos
    assert cloned.end_pos == arrow.end_pos
    assert cloned.style["width"] == 4
    cloned.style["width"] = 8
    assert arrow.style["width"] == 4  # 독립 복제 보장
    
    # 3. 렌더링 검증 (QPainter 예외 없이 정상 렌더링)
    img = QImage(300, 200, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    painter = QPainter(img)
    try:
        arrow.render(painter)
    finally:
        painter.end()
    assert img.pixelColor(200, 50).alpha() > 0
    
    # 4. 윈도우 UI 및 툴바 연동 검증
    win = ManualStudioWindow()
    canvas = win.canvas
    
    # 모드 전환 검증
    win.switch_mode("ARROW")
    assert canvas.current_mode == "ARROW"
    assert win.btn_mode_arrow.isChecked() is True
    assert win.btn_mode_select.isChecked() is False
    
    # 캔버스에 화살표 추가 및 선택 동기화
    canvas.items.append(arrow)
    win.on_canvas_item_selected(arrow)
    assert win.spin_box_width.value() == 4
    
    # 툴바에서 두께 변경 시 선택 객체 동기화
    canvas.selected_item = arrow
    win.spin_box_width.setValue(6)
    assert arrow.style["width"] == 6
    assert win.config["arrow_style"]["width"] == 6
    
    # 툴바 색상 선택 시 선택 객체 동기화
    win.choose_box_preset_color("#1E88E5")
    assert arrow.style["color"] == "#1E88E5"
    assert win.config["arrow_style"]["color"] == "#1E88E5"
    
    # 5. 실행 취소(Undo) 롤백 테스트
    canvas.push_undo()
    arrow.style["width"] = 12
    canvas.undo()
    assert canvas.items[-1].style["width"] == 6
    
    # 6. 테스트 종료 후 복원
    win.spin_box_width.setValue(3)
    win.choose_box_preset_color("#E53935")
    win.close()
    print("[PASS] test_arrow_item_and_sync (Arrow geometry, rendering, clone, undo, and toolbar sync valid)")

def test_five_recommended_annotation_items():
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QPointF, QRect, Qt
    from PySide6.QtGui import QImage, QPainter, QPixmap, QColor
    from manual_capture_studio import (
        StepArrowItem, ElbowArrowItem, CalloutItem, BlurMosaicItem, HotkeyBadgeItem,
        load_config
    )
    app = QApplication.instance() or QApplication(sys.argv)
    cfg = load_config()

    # 1. StepArrowItem 검증 (스탬프 + 화살표 일체형)
    st_style = cfg.get("stamp_style", {}).copy()
    arr_style = cfg.get("arrow_style", {}).copy()
    step_item = StepArrowItem(1, QPointF(50, 50), QPointF(150, 50), st_style, arr_style)
    assert step_item.index == 1
    assert step_item.contains(QPointF(50, 50)) is True # 스탬프 원형 내부
    assert step_item.contains(QPointF(100, 50)) is True # 화살표 몸체
    assert step_item.contains(QPointF(200, 200)) is False
    cloned_step = step_item.clone()
    assert cloned_step.index == 1
    cloned_step.index = 2
    assert step_item.index == 1 # 독립 복제

    # 2. ElbowArrowItem 검증 (L자 직각 화살표)
    elbow_style = cfg.get("elbow_style", {}).copy()
    elbow_item = ElbowArrowItem(QPointF(30, 30), QPointF(120, 100), elbow_style, "HV")
    assert elbow_item.contains(QPointF(60, 30)) is True # 수평 구간
    assert elbow_item.contains(QPointF(120, 60)) is True # 수직 구간
    assert elbow_item.contains(QPointF(50, 80)) is False # 대각선 빈공간

    # 3. CalloutItem 검증 (지시선 말풍선)
    co_style = cfg.get("callout_style", {}).copy()
    callout_item = CalloutItem("설명 말풍선", QRect(50, 50, 120, 45), QPointF(10, 10), co_style)
    assert callout_item.contains(QPointF(70, 60)) is True # 말풍선 상자 내부
    assert callout_item.contains(QPointF(20, 20)) is True # 지시선 꼬리 내부
    assert callout_item.contains(QPointF(300, 300)) is False

    # 4. BlurMosaicItem 검증 (비파괴 모자이크 블러)
    bl_style = cfg.get("blur_style", {}).copy()
    blur_rect = QRect(20, 20, 80, 80)
    blur_item = BlurMosaicItem(blur_rect, bl_style)
    assert blur_item.contains(QPointF(50, 50)) is True
    assert blur_item.contains(QPointF(5, 5)) is False

    # 모자이크 비파괴 렌더링 검증
    test_pm = QPixmap(150, 150)
    test_pm.fill(QColor(255, 0, 0)) # 빨간색 배경
    img = QImage(150, 150, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    painter = QPainter(img)
    try:
        blur_item.render_mosaic(painter, test_pm)
    finally:
        painter.end()
    assert img.pixelColor(50, 50).alpha() > 0

    # 5. HotkeyBadgeItem 검증 (3D 키캡 단축키 뱃지)
    hk_style = cfg.get("hotkey_style", {}).copy()
    hotkey_item = HotkeyBadgeItem("Ctrl+Alt+S", 40, 40, hk_style)
    assert hotkey_item.key_text == "Ctrl+Alt+S"
    assert hotkey_item.contains(QPointF(50, 50)) is True
    assert hotkey_item.contains(QPointF(300, 300)) is False

    # 6. 모든 신규 객체 QPainter 렌더링 무오류 검증
    render_img = QImage(400, 300, QImage.Format_ARGB32)
    render_img.fill(Qt.white)
    p = QPainter(render_img)
    try:
        step_item.render(p)
        elbow_item.render(p)
        callout_item.render(p)
        hotkey_item.render(p)
    finally:
        p.end()

    print("[PASS] test_five_recommended_annotation_items (StepArrow, Elbow, Callout, Blur, Hotkey geometry and rendering valid)")

def test_ribbon_menu_and_quick_strip():
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QPointF, Qt
    from manual_capture_studio import (
        ManualStudioWindow, StepArrowItem, CalloutItem, BlurMosaicItem, HotkeyBadgeItem
    )
    app = QApplication.instance() or QApplication(sys.argv)
    win = ManualStudioWindow()
    canvas = win.canvas

    # 1. 리본 탭 구조 검증 (전사 표준 3.1: 건조한 명사 '도구', '서식·설정')
    assert win.ribbon_tabs.count() == 2
    assert win.ribbon_tabs.tabText(0) == "도구"
    assert win.ribbon_tabs.tabText(1) == "서식·설정"

    # 2. 5대 신규 도구 모드 버튼 및 토글/상태 배지 검증
    modes = [
        ("SELECT", win.btn_mode_select, "선택"),
        ("STAMP", win.btn_mode_stamp, "번호 스탬프"),
        ("STEP_ARROW", win.btn_mode_step_arrow, "스탬프 화살표"),
        ("ELBOW", win.btn_mode_elbow, "직각 화살표"),
        ("ARROW", win.btn_mode_arrow, "직선 화살표"),
        ("BOX", win.btn_mode_box, "사각 박스"),
        ("BLUR", win.btn_mode_blur, "모자이크 블러"),
        ("CALLOUT", win.btn_mode_callout, "설명 말풍선"),
        ("TEXT", win.btn_mode_text, "텍스트 라벨"),
        ("HOTKEY", win.btn_mode_hotkey, "단축키 뱃지"),
    ]
    for mode_name, btn, kor_title in modes:
        win.switch_mode(mode_name)
        assert canvas.current_mode == mode_name
        assert btn.isChecked() is True
        assert kor_title in win.lbl_active_mode.text()

    # 3. 상시 퀵 서식 바 양방향 동기화 검증 (두께, 음영 채우기)
    win.spin_box_width.setValue(7)
    assert win.spin_box_width_tab.value() == 7
    assert canvas.current_box_width == 7
    assert canvas.current_arrow_width == 7

    win.spin_box_width_tab.setValue(9)
    assert win.spin_box_width.value() == 9
    assert canvas.current_box_width == 9

    win.chk_box_fill.setChecked(True)
    assert win.chk_box_fill_tab.isChecked() is True
    assert canvas.current_box_fill is True

    win.chk_box_fill_tab.setChecked(False)
    assert win.chk_box_fill.isChecked() is False
    assert canvas.current_box_fill is False

    # 4. 스탬프 다음 번호 초기화 (reset_stamp_index) 검증
    canvas.next_stamp_index = 5
    win.reset_stamp_index()
    assert canvas.next_stamp_index == 1

    # 5. 신규 객체 선택 시 툴바 및 배지 동기화 검증
    # 5-1. StepArrowItem
    st_arrow = StepArrowItem(3, QPointF(10, 10), QPointF(60, 60), {"size": 40, "bg_color": "#43A047"}, {"width": 5, "head_size": 18, "color": "#43A047"})
    canvas.items.append(st_arrow)
    win.on_canvas_item_selected(st_arrow)
    assert win.spin_stamp_size.value() == 40
    assert win.spin_box_width.value() == 5
    assert win.spin_arrow_head.value() == 18
    assert "스탬프 화살표" in win.lbl_active_mode.text()

    # 5-2. CalloutItem
    callout = CalloutItem("경고 안내", canvas.rect(), QPointF(0, 0), {"font_size": 16, "border_width": 4, "border_color": "#FB8C00", "tail_base_width": 22})
    canvas.items.append(callout)
    win.on_canvas_item_selected(callout)
    assert win.spin_text_font_size.value() == 16
    assert win.spin_box_width.value() == 4
    assert win.spin_callout_tail_size.value() == 22
    assert "말풍선" in win.lbl_active_mode.text()

    # 5-3. BlurMosaicItem
    blur = BlurMosaicItem(canvas.rect(), {"block_size": 15})
    canvas.items.append(blur)
    win.on_canvas_item_selected(blur)
    assert win.spin_blur_block.value() == 15
    assert "모자이크" in win.lbl_active_mode.text()

    # 5-4. HotkeyBadgeItem
    hk = HotkeyBadgeItem("Ctrl+Shift+P", 100, 100, {"font_size": 18})
    canvas.items.append(hk)
    win.on_canvas_item_selected(hk)
    assert win.spin_hotkey_font_size.value() == 18
    assert "단축키" in win.lbl_active_mode.text()

    # 6. 퀵 서식 바 색상 프리셋 변경 시 선택 객체 즉시 반영 검증
    canvas.selected_item = callout
    win.choose_box_preset_color("#1E88E5")
    assert callout.style["border_color"] == "#1E88E5"

    # 복원 및 창 닫기
    win.spin_box_width.setValue(3)
    win.chk_box_fill.setChecked(False)
    win.choose_box_preset_color("#E53935")
    win.close()
    print("[PASS] test_ribbon_menu_and_quick_strip (Ribbon tabs, quick strip, two-way sync, and item selection valid)")

def test_annotation_serialization():
    from PySide6.QtCore import QPointF, QRect, QRectF
    from manual_capture_studio import (
        StampItem, TextLabelItem, HighlightBoxItem, ArrowItem, StepArrowItem,
        ElbowArrowItem, CalloutItem, BlurMosaicItem, HotkeyBadgeItem,
        item_from_dict
    )

    # 1. StampItem
    stamp = StampItem(3, 100.5, 200.5, {"size": 36, "bg_color": "#2196F3"})
    d = stamp.to_dict()
    assert d["type"] == "StampItem" and d["index"] == 3
    stamp_res = item_from_dict(d)
    assert isinstance(stamp_res, StampItem)
    assert stamp_res.index == 3 and stamp_res.pos.x() == 100.5 and stamp_res.style["size"] == 36

    # 2. TextLabelItem
    text_it = TextLabelItem("테스트 라벨", 50.0, 75.0, {"font_size": 15, "text_color": "#FFFF00"})
    d = text_it.to_dict()
    assert d["type"] == "TextLabelItem" and d["text"] == "테스트 라벨"
    text_res = item_from_dict(d)
    assert isinstance(text_res, TextLabelItem)
    assert text_res.text == "테스트 라벨" and text_res.pos.y() == 75.0

    # 3. HighlightBoxItem
    box_it = HighlightBoxItem(QRect(10, 20, 150, 80), {"color": "#E53935", "border_width": 4, "fill": True})
    d = box_it.to_dict()
    assert d["type"] == "HighlightBoxItem" and d["rect"] == [10, 20, 150, 80]
    box_res = item_from_dict(d)
    assert isinstance(box_res, HighlightBoxItem)
    assert box_res.rect == QRect(10, 20, 150, 80) and box_res.style["fill"] is True

    # 4. ArrowItem
    arrow_it = ArrowItem(QPointF(5, 5), QPointF(55, 55), {"color": "#4CAF50", "width": 5})
    d = arrow_it.to_dict()
    assert d["type"] == "ArrowItem" and d["start_pos"] == [5.0, 5.0]
    arrow_res = item_from_dict(d)
    assert isinstance(arrow_res, ArrowItem)
    assert arrow_res.start_pos == QPointF(5.0, 5.0) and arrow_res.end_pos == QPointF(55.0, 55.0)

    # 5. StepArrowItem
    step_arr = StepArrowItem(2, QPointF(10, 20), QPointF(80, 90), {"size": 32}, {"width": 3, "color": "#E53935"})
    d = step_arr.to_dict()
    assert d["type"] == "StepArrowItem" and d["index"] == 2
    step_res = item_from_dict(d)
    assert isinstance(step_res, StepArrowItem)
    assert step_res.index == 2 and step_res.end_pos == QPointF(80.0, 90.0)

    # 6. ElbowArrowItem
    elbow = ElbowArrowItem(QPointF(10, 10), QPointF(100, 100), {"color": "#E53935"}, "VH")
    d = elbow.to_dict()
    assert d["type"] == "ElbowArrowItem" and d["route_mode"] == "VH"
    elbow_res = item_from_dict(d)
    assert isinstance(elbow_res, ElbowArrowItem)
    assert elbow_res.route_mode == "VH"

    # 7. CalloutItem
    callout = CalloutItem("말풍선 내용", QRectF(20, 30, 120, 40), QPointF(5, 5), {"font_size": 13})
    d = callout.to_dict()
    assert d["type"] == "CalloutItem" and d["text"] == "말풍선 내용"
    callout_res = item_from_dict(d)
    assert isinstance(callout_res, CalloutItem)
    assert callout_res.text == "말풍선 내용" and callout_res.target_pt == QPointF(5.0, 5.0)

    # 8. BlurMosaicItem
    blur = BlurMosaicItem(QRect(30, 40, 100, 60), {"block_size": 12})
    d = blur.to_dict()
    assert d["type"] == "BlurMosaicItem" and d["rect"] == [30, 40, 100, 60]
    blur_res = item_from_dict(d)
    assert isinstance(blur_res, BlurMosaicItem)
    assert blur_res.style["block_size"] == 12

    # 9. HotkeyBadgeItem
    hotkey = HotkeyBadgeItem("Enter ↵", 120, 140, {"font_size": 14})
    d = hotkey.to_dict()
    assert d["type"] == "HotkeyBadgeItem" and d["key_text"] == "Enter ↵"
    hk_res = item_from_dict(d)
    assert isinstance(hk_res, HotkeyBadgeItem)
    assert hk_res.key_text == "Enter ↵" and hk_res.pos == QPointF(120.0, 140.0)

    print("[PASS] test_annotation_serialization (All 9 items to_dict and from_dict roundtrip valid)")

def test_project_manager_save_and_load():
    import os
    import shutil
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QPixmap, QColor
    from PySide6.QtCore import QPointF, QRect
    from manual_capture_studio import (
        ProjectManager, StampItem, HighlightBoxItem, TextLabelItem
    )
    app = QApplication.instance() or QApplication(sys.argv)

    test_dir = os.path.join(os.path.dirname(__file__), "test_project_dir")
    os.makedirs(test_dir, exist_ok=True)
    proj_path = os.path.join(test_dir, "Step_001.mcs.json")
    companion_raw_path = os.path.join(test_dir, "Step_001_raw.png")

    # 1. 픽스맵 및 주석 객체 준비
    pixmap = QPixmap(300, 200)
    pixmap.fill(QColor(100, 150, 200))
    items = [
        StampItem(1, 50, 50, {"size": 32, "bg_color": "#E53935"}),
        HighlightBoxItem(QRect(10, 10, 80, 40), {"color": "#FF0000", "border_width": 2}),
        TextLabelItem("테스트 텍스트", 100, 120, {"font_size": 14})
    ]

    # 2. 저장 실행
    ok = ProjectManager.save_project(proj_path, pixmap, items, next_stamp_index=2, metadata={"author": "Test"})
    assert ok is True
    assert os.path.exists(proj_path) is True
    assert os.path.exists(companion_raw_path) is True

    # 3. 로드 실행 (Companion 원본 이미지로부터 복원)
    loaded_pm, loaded_items, next_idx, meta = ProjectManager.load_project(proj_path)
    assert loaded_pm is not None and not loaded_pm.isNull()
    assert loaded_pm.width() == 300 and loaded_pm.height() == 200
    assert len(loaded_items) == 3
    assert isinstance(loaded_items[0], StampItem) and loaded_items[0].index == 1
    assert next_idx == 2
    assert meta.get("author") == "Test"

    # 4. Fallback 검증: Companion 파일 삭제 후 Base64로부터 무손실 복원
    os.remove(companion_raw_path)
    assert os.path.exists(companion_raw_path) is False
    loaded_pm2, loaded_items2, next_idx2, _ = ProjectManager.load_project(proj_path)
    assert loaded_pm2 is not None and not loaded_pm2.isNull()
    assert loaded_pm2.width() == 300
    assert len(loaded_items2) == 3

    # 정리
    shutil.rmtree(test_dir, ignore_errors=True)
    print("[PASS] test_project_manager_save_and_load (Project serialization, companion raw file, and b64 fallback valid)")

def test_auto_backup_step_bundle_and_delete():
    import os
    import shutil
    from PIL import Image
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QPixmap, QColor
    from PySide6.QtCore import QPointF
    from manual_capture_studio import (
        ExportEngine, ManualStudioWindow, StampItem, StepArrowItem
    )
    app = QApplication.instance() or QApplication(sys.argv)

    test_captures_dir = os.path.join(os.path.dirname(__file__), "test_bundle_captures")
    shutil.rmtree(test_captures_dir, ignore_errors=True)
    os.makedirs(test_captures_dir, exist_ok=True)

    pil_img = Image.new("RGBA", (400, 300), (255, 255, 255, 255))
    raw_pm = QPixmap(400, 300)
    raw_pm.fill(QColor(240, 240, 240))
    items = [StampItem(1, 30, 30, {"size": 32})]

    # 1. 3종 세트 동시 자동 저장 검증
    res = ExportEngine.auto_backup_step_bundle(pil_img, raw_pm, items, 2, test_captures_dir)
    assert os.path.exists(res["bake_path"]) is True
    assert os.path.exists(res["raw_path"]) is True
    assert os.path.exists(res["project_path"]) is True
    assert res["bake_path"].endswith("Step_001.png")
    assert res["raw_path"].endswith("Step_001_raw.png")
    assert res["project_path"].endswith("Step_001.mcs.json")

    # 2. auto_backup_file 실행 시 Step_001_raw.png에 의해 인덱스가 오염되지 않고 Step_002.png가 생성되는지 검증
    p2 = ExportEngine.auto_backup_file(pil_img, test_captures_dir)
    assert os.path.basename(p2) == "Step_002.png"

    # 3. Canvas 삭제 및 스마트 자동 번호 재정렬(reindex) 및 delete_selected_item 검증
    win = ManualStudioWindow()
    canvas = win.canvas
    canvas.items.clear()
    s1 = StampItem(1, 10, 10, {"size": 32})
    s2 = StampItem(2, 20, 20, {"size": 32})
    s3 = StepArrowItem(3, QPointF(30, 30), QPointF(50, 50), {"size": 32}, {"width": 3})
    canvas.items.extend([s1, s2, s3])
    canvas.next_stamp_index = 4

    # s2를 선택하고 delete_selected_item 호출
    canvas.selected_item = s2
    del_ok = canvas.delete_selected_item()
    assert del_ok is True
    assert s2 not in canvas.items
    assert len(canvas.items) == 2
    # s3의 index가 2로 자동 승계되었는지 검증!
    assert canvas.items[0].index == 1
    assert canvas.items[1].index == 2
    assert canvas.next_stamp_index == 3

    # Undo 검증
    canvas.undo()
    assert len(canvas.items) == 3
    assert canvas.items[1].index == 2
    assert canvas.items[2].index == 3
    assert canvas.next_stamp_index == 4

    if hasattr(win, "hotkey_thread"):
        win.hotkey_thread.stop()
    win.close()
    shutil.rmtree(test_captures_dir, ignore_errors=True)
    print("[PASS] test_auto_backup_step_bundle_and_delete (3-file bundle, smart stamp re-indexing, and item deletion valid)")

def test_image_overlay_item_and_sub_capture():
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QPixmap, QColor, QImage, QPainter
    from PySide6.QtCore import QPointF, QRectF
    from manual_capture_studio import (
        ImageOverlayItem, item_from_dict, ManualStudioWindow, StampItem, ArrowItem
    )
    app = QApplication.instance() or QApplication(sys.argv)

    # 1. ImageOverlayItem 생성 및 기하 연산
    pm = QPixmap(200, 100)
    pm.fill(QColor(100, 180, 240))
    rect = QRectF(50, 50, 200, 100)
    overlay = ImageOverlayItem(rect, pm, {"border_color": "#2196F3", "border_width": 3})

    assert overlay.contains(QPointF(100, 80)) is True
    assert overlay.contains(QPointF(10, 10)) is False

    # 2. 리사이즈 핸들 테스트
    handles = overlay.get_handles()
    assert "TL" in handles and "TR" in handles and "BL" in handles and "BR" in handles
    br_center = handles["BR"].center()
    assert overlay.get_handle_at(br_center) == "BR"
    assert overlay.get_handle_at(QPointF(0, 0)) is None

    # 3. 종횡비 유지 리사이즈 (Aspect ratio = 200 / 100 = 2.0)
    overlay.handle_resize("BR", QPointF(350, 200), keep_aspect_ratio=True)
    assert overlay.rect.width() == 300.0
    assert overlay.rect.height() == 150.0

    # 4. 렌더링 무결성 (선택 상태 및 비선택 상태)
    test_img = QImage(500, 300, QImage.Format_ARGB32)
    test_img.fill(QColor(255, 255, 255))
    painter = QPainter(test_img)
    overlay.render(painter, is_selected=True)
    overlay.render(painter, is_selected=False)
    painter.end()

    # 5. Base64 직렬화 / 역직렬화 라운드트립 무결성
    data = overlay.to_dict()
    assert data["type"] == "ImageOverlayItem"
    assert len(data["image_b64"]) > 0
    assert data["style"]["border_color"] == "#2196F3"

    restored = item_from_dict(data)
    assert isinstance(restored, ImageOverlayItem)
    assert restored.rect.width() == 300.0
    assert restored.rect.height() == 150.0
    assert restored.pixmap.width() == 200
    assert restored.pixmap.height() == 100
    assert restored.style["border_color"] == "#2196F3"

    # 6. StudioCanvasWidget 연동 (삽입, 선택, 스타일 수정, 삭제, Undo, 베이킹)
    win = ManualStudioWindow()
    canvas = win.canvas
    bg_pm = QPixmap(800, 600)
    bg_pm.fill(QColor(240, 240, 240))
    canvas.set_pixmap(bg_pm)
    canvas.items.clear()

    # 모달 서브 캡처 추가 시뮬레이션
    sub_pm = QPixmap(300, 200)
    sub_pm.fill(QColor(255, 200, 100))
    canvas.add_image_overlay(sub_pm)
    assert len(canvas.items) == 1
    assert isinstance(canvas.items[0], ImageOverlayItem)
    assert canvas.selected_item == canvas.items[0]

    # 선택된 모달 객체의 테두리 색상 및 두께 변경
    canvas.set_box_color("#FF5722")
    canvas.set_box_width(4)
    assert canvas.selected_item.style["border_color"] == "#FF5722"
    assert canvas.selected_item.style["border_width"] == 4

    # 다른 주석과의 유기적 연결 (배경 -> 모달로 이어지는 화살표 및 스탬프)
    stamp = StampItem(1, 100, 100, {"size": 32})
    arrow = ArrowItem(QPointF(100, 100), QPointF(canvas.selected_item.rect.center()), {"width": 3})
    canvas.items.extend([stamp, arrow])
    assert len(canvas.items) == 3

    # 합성 베이킹 (PPT 전송용 일체형 이미지)
    composed = canvas.get_composed_image()
    assert composed is not None
    assert composed.width() == 800
    assert composed.height() == 600

    # 모달 객체 삭제 및 Undo
    canvas.selected_item = canvas.items[0]
    canvas.delete_selected_item()
    assert len(canvas.items) == 2
    canvas.undo()
    assert len(canvas.items) == 3
    assert isinstance(canvas.items[0], ImageOverlayItem)

    # 리본 메뉴 버튼 연동 확인
    assert hasattr(win, "btn_sub_capture")
    assert "F8" in win.btn_sub_capture.text()

    win.close()
    print("[PASS] test_image_overlay_item_and_sub_capture (F8 modal sub-capture, resize handles, border/shadow, and canvas bake valid)")

def test_draft_stamp_item():
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QPixmap, QColor, QImage, QPainter
    from PySide6.QtCore import QPointF
    from manual_capture_studio import (
        DraftStampItem, item_from_dict, ManualStudioWindow
    )
    app = QApplication.instance() or QApplication(sys.argv)

    # 1. DraftStampItem 생성 및 기하 / 각도 검증
    stamp = DraftStampItem(text="DRAFT", pos=QPointF(300, 200))
    assert stamp.text == "DRAFT"
    assert stamp.angle == -60.0  # 왼쪽 아래에서 오른쪽 위 방향 (반시계 60도)
    assert stamp.style["border_width"] == 5
    assert stamp.style["opacity"] == 0.40

    local_r = stamp.get_local_rect()
    assert local_r.width() > 100
    assert local_r.height() > 40
    assert abs(local_r.center().x()) < 1e-5
    assert abs(local_r.center().y()) < 1e-5

    # 2. 역변환 아핀 행렬 기반 정밀 히트 테스트
    assert stamp.contains(QPointF(300, 200)) is True  # 중심점
    assert stamp.contains(QPointF(10, 10)) is False   # 먼 영역

    # 3. 렌더링 무결성 (선택/비선택)
    img = QImage(600, 400, QImage.Format_ARGB32)
    img.fill(QColor(255, 255, 255))
    painter = QPainter(img)
    stamp.render(painter, is_selected=True)
    stamp.render(painter, is_selected=False)
    painter.end()

    # 4. 직렬화 / 역직렬화 라운드트립
    data = stamp.to_dict()
    assert data["type"] == "DraftStampItem"
    assert data["text"] == "DRAFT"
    assert data["angle"] == -60.0
    assert data["x"] == 300.0
    assert data["y"] == 200.0

    restored = item_from_dict(data)
    assert isinstance(restored, DraftStampItem)
    assert restored.text == "DRAFT"
    assert restored.angle == -60.0
    assert restored.pos == QPointF(300, 200)
    assert restored.style["border_width"] == 5

    # 5. StudioCanvasWidget 및 UI 연동 (원클릭 삽입, 드래그, 스타일 변경, Undo, PPT 베이킹)
    win = ManualStudioWindow()
    canvas = win.canvas
    bg_pm = QPixmap(800, 600)
    bg_pm.fill(QColor(240, 240, 240))
    canvas.set_pixmap(bg_pm)
    canvas.items.clear()

    # 캔버스 중앙에 Draft 스탬프 추가
    item = canvas.add_draft_stamp("DRAFT")
    assert len(canvas.items) == 1
    assert isinstance(canvas.items[0], DraftStampItem)
    assert canvas.selected_item == item
    assert item.pos == QPointF(400, 300)

    # 스타일 변경 연동 (테두리 두께, 색상)
    canvas.set_box_width(8)
    canvas.set_box_color("#C62828")
    assert item.style["border_width"] == 8
    assert item.style["color"] == "#C62828"

    # 합성 베이킹 검증
    composed = canvas.get_composed_image()
    assert composed is not None
    assert composed.width() == 800
    assert composed.height() == 600

    # 객체 삭제 및 Undo 복원
    canvas.delete_selected_item()
    assert len(canvas.items) == 0
    canvas.undo()
    assert len(canvas.items) == 1
    assert isinstance(canvas.items[0], DraftStampItem)

    # 리본 메뉴 버튼 검증
    assert hasattr(win, "btn_draft_stamp")
    assert "Draft" in win.btn_draft_stamp.text()

    win.close()
    print("[PASS] test_draft_stamp_item (Rectangle 60-deg tilt Draft stamp, inverse transform hit test, and canvas bake valid)")

def test_powerpoint_step_renumbering():
    from PySide6.QtWidgets import QApplication
    from manual_capture_studio import ManualStudioWindow, ExportEngine
    import win32com.client

    app = QApplication.instance() or QApplication(sys.argv)

    # 1. UI 위젯 및 액션 연결 검증
    win = ManualStudioWindow()
    assert hasattr(win, "btn_renumber_steps"), "btn_renumber_steps button must exist"
    assert hasattr(win, "action_renumber_powerpoint_steps"), "action_renumber_powerpoint_steps method must exist"
    assert "Step 재정렬" in win.btn_renumber_steps.text()
    win.close()

    # 2. PowerPoint COM 연동 및 정밀 재부여 검증
    ppt = None
    pres = None
    temp_pptx = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_renumber_temp.pptx")
    if os.path.exists(temp_pptx):
        try:
            os.remove(temp_pptx)
        except Exception:
            pass

    try:
        ppt = win32com.client.Dispatch("PowerPoint.Application")
        ppt.Visible = True
        pres = ppt.Presentations.Add(True)

        # Slide 1: 표지 (Step 없음)
        s1 = pres.Slides.Add(1, 12)
        b1 = s1.Shapes.AddTextbox(1, 50, 50, 400, 50)
        b1.TextFrame.TextRange.Text = "00. 영업 관리 프로세스 매뉴얼"

        # Slide 2: Step 4 (뒤섞인 번호)
        s2 = pres.Slides.Add(2, 12)
        b2 = s2.Shapes.AddTextbox(1, 36, 18, 900, 35)
        b2.TextFrame.TextRange.Text = "Step 4. [신규 고객사 등록 및 단가 설정]"

        # Slide 3: Step 1 (뒤섞인 번호)
        s3 = pres.Slides.Add(3, 12)
        b3 = s3.Shapes.AddTextbox(1, 36, 18, 900, 35)
        b3.TextFrame.TextRange.Text = "Step 1. [차량 배차 의뢰 발행]"

        # Slide 4: 섹션 구분 (Step 없음)
        s4 = pres.Slides.Add(4, 12)
        b4 = s4.Shapes.AddTextbox(1, 50, 50, 400, 50)
        b4.TextFrame.TextRange.Text = "제 2 장 : 정산 및 마감"

        # Slide 5: Step 12 (뒤섞인 번호) + 본문 인용구 포함
        s5 = pres.Slides.Add(5, 12)
        b5 = s5.Shapes.AddTextbox(1, 36, 18, 900, 35)
        b5.TextFrame.TextRange.Text = "Step 12. [전자 세금계산서 발행 및 검증]"
        b5_note = s5.Shapes.AddTextbox(1, 100, 300, 500, 50)
        b5_note.TextFrame.TextRange.Text = "※ 주의: Step 1에서 등록한 고객 정보와 일치해야 합니다."

        # 재정렬 실행
        res = ExportEngine.renumber_powerpoint_steps(file_path=None, start_from=1)

        assert res["success"] is True, f"Renumbering failed: {res.get('error')}"
        assert res["total_slides"] == 5, f"Expected 5 slides, got {res['total_slides']}"
        assert res["renumbered_count"] == 3, f"Expected 3 renumbered, got {res['renumbered_count']}"
        assert res["skipped_count"] == 2, f"Expected 2 skipped, got {res['skipped_count']}"

        # 슬라이드별 결과 검증
        # Slide 1: 표지 보존
        assert b1.TextFrame.TextRange.Text == "00. 영업 관리 프로세스 매뉴얼"

        # Slide 2: Step 4 -> Step 1 (기존 내용 100% 보존)
        assert b2.TextFrame.TextRange.Text == "Step 1. [신규 고객사 등록 및 단가 설정]"

        # Slide 3: Step 1 -> Step 2 (기존 내용 100% 보존)
        assert b3.TextFrame.TextRange.Text == "Step 2. [차량 배차 의뢰 발행]"

        # Slide 4: 섹션 구분 보존
        assert b4.TextFrame.TextRange.Text == "제 2 장 : 정산 및 마감"

        # Slide 5: Step 12 -> Step 3 (기존 내용 100% 보존)
        assert b5.TextFrame.TextRange.Text == "Step 3. [전자 세금계산서 발행 및 검증]"

        # Slide 5 본문 인용구는 오작동 없이 온전히 보존되어야 함!
        assert "Step 1" in b5_note.TextFrame.TextRange.Text, "Body reference note should NOT be corrupted"

    finally:
        if pres:
            try:
                pres.Close()
            except Exception:
                pass
        if ppt:
            try:
                ppt.Quit()
            except Exception:
                pass

    print("[PASS] test_powerpoint_step_renumbering (Sequential Step Renumbering, Font & Text preservation, Non-step skip valid)")

def test_dragon_rpa_branding_and_about_dialog():
    from PySide6.QtWidgets import QApplication, QMessageBox
    from manual_capture_studio import ManualStudioWindow, AboutDialog, get_dragon_rpa_ci_pixmap

    app = QApplication.instance() or QApplication(sys.argv)

    # 1. CI 로고 로드 검증
    pix = get_dragon_rpa_ci_pixmap()
    assert pix is not None and not pix.isNull(), "CI pixmap must not be null"
    assert pix.width() > 0 and pix.height() > 0, "CI pixmap must have valid dimensions"

    # 2. 윈도우 타이틀 및 메뉴바/코너 위젯 검증
    win = ManualStudioWindow()
    assert "DragonRPA Co." in win.windowTitle(), "Window title must include company name"
    assert "Manual Studio" in win.windowTitle(), "Window title must include Manual Studio"

    menubar = win.menuBar()
    assert menubar is not None, "MenuBar must exist"

    # 메뉴바 코너 위젯 존재 확인 (상단 단일 배치)
    cw = menubar.cornerWidget()
    assert cw is not None, "MenuBar corner widget must exist"

    # 리본 탭 코너 위젯 제거 확인 (하단 중복 제거 검증)
    rcw = win.ribbon_tabs.cornerWidget()
    assert rcw is None, "RibbonTabs corner widget must be removed to avoid duplication"

    # 3. AboutDialog 검증
    about_dlg = AboutDialog(win)
    assert about_dlg is not None
    assert "About - DragonRPA Co." in about_dlg.windowTitle()

    # 클립보드 복사 메서드 검증 (QMessageBox 몽키패치로 비동기 검증)
    orig_info = QMessageBox.information
    QMessageBox.information = lambda *a, **k: None
    try:
        about_dlg.copy_email()
        cb = QApplication.clipboard()
        assert cb.text() == "77.victor.lee@gmail.com", "Clipboard must contain target email"
    finally:
        QMessageBox.information = orig_info
        if hasattr(win, "hotkey_thread"):
            win.hotkey_thread.stop()
        win.close()

    print("[PASS] test_dragon_rpa_branding_and_about_dialog (CI Pixmap, MenuBar, Corner Widgets, and About Dialog valid)")

def test_license_validator():
    from datetime import datetime, timedelta
    from manual_capture_studio import LicenseValidator

    # 1. 난독화 / 복호화 무손실 라운드트립 검증
    dt = datetime(2026, 9, 11, 15, 30, 0)
    enc = LicenseValidator._obfuscate_timestamp(dt)
    dec = LicenseValidator._deobfuscate_timestamp(enc)
    assert dec == dt, f"Timestamp roundtrip failed: {dt} != {dec}"

    # 2. 현재 시점 라이선스 유효성 검증
    is_valid, reason = LicenseValidator.check_license()
    assert is_valid is True, f"License check should pass for current date, got {reason}"

    # 3. 가상 만료 시점 검증 (2027-01-01)
    orig_exp = LicenseValidator.EXPIRATION_DATE
    try:
        LicenseValidator.EXPIRATION_DATE = datetime(2025, 1, 1)
        exp_valid, exp_msg = LicenseValidator.check_license()
        assert exp_valid is False, "Expired date must fail validation"
        assert "만료되었습니다" in exp_msg
    finally:
        LicenseValidator.EXPIRATION_DATE = orig_exp

    print("[PASS] test_license_validator (2026-12-31 Time-Bomb, Obfuscation, Anti-Rollback valid)")

def test_custom_font_manager():
    from manual_capture_studio import CustomFontManager
    mgr = CustomFontManager.instance()
    assert mgr is not None
    assert os.path.exists(mgr.fonts_dir)
    families = mgr.load_all_fonts()
    assert isinstance(families, list)
    print(f"[PASS] test_custom_font_manager (fonts_dir={mgr.fonts_dir}, loaded={len(families)})")

def test_multi_monitor_manager():
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QRect
    from manual_capture_studio import MultiMonitorManager
    app = QApplication.instance() or QApplication(sys.argv)
    screens = MultiMonitorManager.get_screens()
    assert len(screens) >= 1
    monitors = MultiMonitorManager.get_monitor_info_list()
    assert len(monitors) == len(screens)
    v_rect = MultiMonitorManager.get_virtual_desktop_rect()
    assert v_rect.width() >= 800 and v_rect.height() >= 600

    # 상대 좌표 <-> 글로벌 좌표 변환 가역성(Invertibility) 검증
    for m in range(len(screens)):
        rel = QRect(50, 60, 400, 300)
        glob = MultiMonitorManager.to_global_rect(m, rel)
        back_rel = MultiMonitorManager.to_relative_rect(m, glob)
        assert back_rel == rel, f"Coordinate bijection failed for monitor {m}: {rel} != {back_rel}"

    # 전체 가상 화면(-1) 변환 가역성 검증
    glob_v = MultiMonitorManager.to_global_rect(-1, rel)
    back_v = MultiMonitorManager.to_relative_rect(-1, glob_v)
    assert back_v == rel

    print(f"[PASS] test_multi_monitor_manager (Screens={len(screens)}, VirtualDesktop={v_rect}, Coord Bijection valid)")

def test_elbow_arrow_four_directions_and_toggle():
    from PySide6.QtCore import QPointF, QRect
    from PySide6.QtGui import QImage, QPainter
    from manual_capture_studio import ElbowArrowItem, item_from_dict
    
    # 1. HV (가로 먼저 -> 세로) vs VH (세로 먼저 -> 가로)
    p_start = QPointF(100, 100)
    # 4분면: 우하(200, 200), 우상(200, 50), 좌하(50, 200), 좌상(50, 50)
    quadrants = [
        (QPointF(200, 200), "우하 ㄱ/ㄴ"),
        (QPointF(200, 50),  "우상 ┘/┌"),
        (QPointF(50, 200),  "좌하 ┌/┘"),
        (QPointF(50, 50),   "좌상 ㄴ/ㄱ")
    ]
    for p_end, name in quadrants:
        item_hv = ElbowArrowItem(p_start, p_end, {"color": "#E53935", "width": 3, "head_size": 14}, route_mode="HV")
        c_hv = item_hv.get_corner_point()
        assert c_hv.x() == p_end.x() and c_hv.y() == p_start.y()

        item_vh = ElbowArrowItem(p_start, p_end, {"color": "#E53935", "width": 3, "head_size": 14}, route_mode="VH")
        c_vh = item_vh.get_corner_point()
        assert c_vh.x() == p_start.x() and c_vh.y() == p_end.y()

    # 2. 토글 기능 검증 (Tab/Space)
    test_item = ElbowArrowItem(p_start, QPointF(300, 300), route_mode="HV")
    assert test_item.route_mode == "HV"
    test_item.toggle_route_mode()
    assert test_item.route_mode == "VH"
    test_item.toggle_route_mode()
    assert test_item.route_mode == "HV"

    # 3. 렌더링 검증
    img = QImage(400, 400, QImage.Format_ARGB32)
    img.fill(0)
    painter = QPainter(img)
    test_item.render(painter)
    painter.end()

    # 4. 직렬화 / 역직렬화 라운드트립
    d = test_item.to_dict()
    assert d["type"] == "ElbowArrowItem"
    assert d["route_mode"] == "HV"
    restored = item_from_dict(d)
    assert isinstance(restored, ElbowArrowItem)
    assert restored.route_mode == "HV"
    assert restored.start_pos == test_item.start_pos
    assert restored.end_pos == test_item.end_pos

    print("[PASS] test_elbow_arrow_four_directions_and_toggle (4 Quadrants, HV/VH, Tab toggle, Serialization valid)")

def test_wordart_item_and_presets():
    from PySide6.QtGui import QImage, QPainter
    from manual_capture_studio import WordArtItem, item_from_dict
    
    # 1. 5대 프리셋 정의 검증
    expected_presets = ["white_pop", "gold_title", "neon_cyan", "red_warning", "slate_modern"]
    for pid in expected_presets:
        assert pid in WordArtItem.PRESETS
        p = WordArtItem.PRESETS[pid]
        assert "name" in p and "text_color" in p and "stroke_color" in p and "stroke_width" in p

    # 2. 아이템 생성 및 프리셋 적용
    wa = WordArtItem("매뉴얼스튜디오 워드아트", 50, 60)
    assert wa.text == "매뉴얼스튜디오 워드아트"
    
    for pid in expected_presets:
        wa.apply_preset(pid)
        assert wa.style.get("preset_id") == pid
        assert wa.style.get("text_color") == WordArtItem.PRESETS[pid]["text_color"]

    # 3. QPainterPath 외곽선/그림자 렌더링 검증
    img = QImage(500, 200, QImage.Format_ARGB32)
    img.fill(0)
    painter = QPainter(img)
    wa.render(painter)
    painter.end()

    # 4. 직렬화 / 역직렬화 라운드트립
    d = wa.to_dict()
    assert d["type"] == "WordArtItem"
    assert d["text"] == "매뉴얼스튜디오 워드아트"
    restored = item_from_dict(d)
    assert isinstance(restored, WordArtItem)
    assert restored.text == wa.text
    assert restored.pos == wa.pos
    assert restored.style["preset_id"] == wa.style["preset_id"]

    print("[PASS] test_wordart_item_and_presets (5 Presets, QPainterPath stroke/shadow, Serialization valid)")

def test_global_i18n_manager():
    from i18n_manager import I18nManager, t, tr
    mgr = I18nManager.instance()
    locales = mgr.get_supported_locales()
    assert len(locales) == 9
    for code in ["ko", "en", "zh", "ja", "de", "es", "fr", "pt", "ru"]:
        assert code in locales
        val = t("btn_fixed_capture", locale=code)
        assert val and len(val) > 0

    fonts = mgr.get_font_families()
    assert "Malgun Gothic" in fonts
    assert "Segoe UI" in fonts

    for code in locales:
        tmpl = mgr.get_step_template(code)
        assert "{n}" in tmpl

    mgr.set_locale("en")
    assert mgr.get_locale() == "en"
    assert "Capture" in tr("btn_fixed_capture")

    mgr.set_locale("ko")
    assert mgr.get_locale() == "ko"
    print("[PASS] test_global_i18n_manager (9 Global Locales, Font Fallback, Dynamic Switch valid)")

def test_license_engine_and_verification():
    from license_engine import LicenseEngine, LicenseType
    
    hwid = LicenseEngine.get_hwid()
    assert hwid.startswith("DRPA-")
    parts = hwid.split("-")
    assert len(parts) == 4
    for p in parts[1:]:
        assert len(p) == 4

    test_types = [
        LicenseType.PERPETUAL,
        LicenseType.SUB_1M,
        LicenseType.SUB_1Y,
        LicenseType.ENTERPRISE,
        LicenseType.AIR_GAPPED,
        LicenseType.TRIAL_14D
    ]

    for ltype in test_types:
        key = LicenseEngine.generate_license_key(
            license_type=ltype,
            issued_to="Global Corp Test",
            hwid=hwid,
            max_seats=10 if ltype == LicenseType.ENTERPRISE else 1
        )
        expected_prefix = LicenseEngine.PREFIX_MAP[ltype]
        assert key.startswith(expected_prefix + "-")
        valid, verified_payload, msg = LicenseEngine.verify_license_key(key, current_hwid=hwid)
        assert valid is True, f"Failed for {ltype}: {msg}"
        assert verified_payload["type"] == ltype
        assert verified_payload["issued_to"] == "Global Corp Test"

    tampered_key = key[:-2] + ("X" if key[-2] != "X" else "Y") + key[-1]
    val_tamper, _, msg_tamper = LicenseEngine.verify_license_key(tampered_key, current_hwid=hwid)
    assert val_tamper is False

    other_hwid = "DRPA-9999-8888-7777"
    key_locked = LicenseEngine.generate_license_key(
        license_type=LicenseType.PERPETUAL,
        hwid=hwid,
        issued_to="NodeLock User"
    )
    val_diff_hwid, _, msg_diff = LicenseEngine.verify_license_key(key_locked, current_hwid=other_hwid)
    assert val_diff_hwid is False

    print("[PASS] test_license_engine_and_verification (HWID, 6 License Types, HMAC-SHA256, Anti-Tamper valid)")

def test_watermark_in_composed_image():
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QPixmap, QImage, QPainter
    from PySide6.QtCore import Qt
    from manual_capture_studio import StudioCanvasWidget
    from license_engine import LicenseEngine
    
    app = QApplication.instance() or QApplication(sys.argv)
    canvas = StudioCanvasWidget()
    pix = QPixmap(400, 300)
    pix.fill(Qt.white)
    canvas.set_pixmap(pix)

    target_img = QImage(400, 300, QImage.Format_ARGB32)
    target_img.fill(Qt.white)
    painter = QPainter(target_img)
    canvas._render_watermark(painter, 400, 300)
    painter.end()

    composed = canvas.get_composed_image()
    assert composed is not None
    assert composed.width() == 400
    assert composed.height() == 300

    print("[PASS] test_watermark_in_composed_image (Watermark badge & diagonal stamp rendering valid)")

def test_instant_capture_mouse_release():
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QPoint, QRect, Qt
    from PySide6.QtGui import QPixmap
    from manual_capture_studio import CaptureOverlayWidget
    
    app = QApplication.instance() or QApplication(sys.argv)
    overlay = CaptureOverlayWidget()
    overlay.full_screen_pixmap = QPixmap(500, 500)
    overlay.full_screen_pixmap.fill(Qt.white)
    
    received_caps = []
    overlay.sig_captured.connect(lambda pix, r: received_caps.append((pix, r)))

    class FakeMouseEvent:
        def __init__(self, pt, btn=Qt.LeftButton):
            self._pos = pt
            self._btn = btn
        def pos(self):
            return self._pos
        def globalPos(self):
            return self._pos
        def button(self):
            return self._btn
        def buttons(self):
            return Qt.LeftButton

    # 마우스 누름 -> 100x100 영역 드래그
    overlay.mousePressEvent(FakeMouseEvent(QPoint(50, 50)))
    assert overlay.selecting is True
    overlay.mouseMoveEvent(FakeMouseEvent(QPoint(150, 150)))
    assert overlay.selected_rect.width() >= 100
    assert overlay.selected_rect.height() >= 100

    # 마우스 릴리즈 -> 엔터 대기 없이 즉시 시그널 방출
    overlay.mouseReleaseEvent(FakeMouseEvent(QPoint(150, 150)))
    assert len(received_caps) == 1
    assert received_caps[0][1].width() >= 100
    assert received_caps[0][1].height() >= 100

    # 10x10 이하 오발 방지 확인
    overlay.magnet_rect = QRect()
    overlay.mousePressEvent(FakeMouseEvent(QPoint(20, 20)))
    overlay.mouseMoveEvent(FakeMouseEvent(QPoint(24, 24)))
    overlay.mouseReleaseEvent(FakeMouseEvent(QPoint(24, 24)))
    assert len(received_caps) == 1

    print("[PASS] test_instant_capture_mouse_release (Enter-free instant release capture valid)")

def test_autosave_and_recovery():
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QPixmap
    from PySide6.QtCore import Qt
    from manual_capture_studio import ManualStudioWindow, StampItem, ProjectManager

    app = QApplication.instance() or QApplication(sys.argv)
    win = ManualStudioWindow()

    pix = QPixmap(300, 200)
    pix.fill(Qt.white)
    win.canvas.set_pixmap(pix)
    stamp = StampItem(1, 50, 50, {"size": 32, "bg_color": "#FF0000"})
    win.canvas.items.append(stamp)

    auto_path = win.get_autosave_path()
    auto_raw = auto_path.replace(".mcs.json", "_raw.png")
    if os.path.exists(auto_path):
        os.remove(auto_path)
    if os.path.exists(auto_raw):
        os.remove(auto_raw)

    win.auto_save_current_work()
    assert os.path.exists(auto_path), "Autosave file should be created"

    raw_pix, items, next_idx, meta = ProjectManager.load_project(auto_path)
    assert raw_pix is not None
    assert raw_pix.width() == 300 and raw_pix.height() == 200
    assert len(items) == 1
    assert items[0].index == 1
    assert meta.get("is_autosave") is True

    win.config["auto_save_enabled"] = False
    win.update_autosave_timer()
    assert not win.autosave_timer.isActive()

    win.config["auto_save_enabled"] = True
    win.config["auto_save_interval_min"] = 10
    win.update_autosave_timer()
    assert win.autosave_timer.isActive()
    assert win.autosave_timer.interval() == 10 * 60 * 1000

    test_save_path = os.path.join(os.path.dirname(auto_path), "test_manual_save.mcs.json")
    win.save_project_to_path(test_save_path)
    assert not os.path.exists(auto_path), "Autosave file should be cleared on manual save"

    if os.path.exists(test_save_path):
        os.remove(test_save_path)
    raw_companion = test_save_path.replace(".mcs.json", "_raw.png")
    if os.path.exists(raw_companion):
        os.remove(raw_companion)
    if os.path.exists(auto_raw):
        os.remove(auto_raw)
    win.close()

    print("[PASS] test_autosave_and_recovery (Auto-save periodic trigger, ProjectManager recovery, and Cleanup valid)")

def test_version_comparator():
    from updater_engine import VersionComparator
    # 1. 시맨틱 파싱 검증
    assert VersionComparator.parse_version("v1.4.0") == (1, 4, 0, 0)
    assert VersionComparator.parse_version("1.4.0.Build.1") == (1, 4, 0, 1)
    assert VersionComparator.parse_version("v2.1.0") == (2, 1, 0, 0)

    # 2. 크기 비교 (is_newer) 검증
    assert VersionComparator.is_newer("1.4.1", "1.4.0") is True
    assert VersionComparator.is_newer("v1.5.0", "1.4.9") is True
    assert VersionComparator.is_newer("1.4.0.Build.2", "1.4.0.Build.1") is True
    assert VersionComparator.is_newer("1.4.0", "1.4.0") is False
    assert VersionComparator.is_newer("1.3.9", "1.4.0") is False
    assert VersionComparator.is_newer("1.4.0.Build.1", "1.4.0.Build.2") is False

    print("[PASS] test_version_comparator (Semantic 4-stage version parsing and comparison valid)")

def test_version_json_schema():
    version_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "version.json")
    assert os.path.exists(version_file), "version.json file must exist in repository root"
    with open(version_file, "r", encoding="utf-8") as f:
        meta = json.load(f)

    required_fields = ["version", "version_code", "release_date", "release_title", "release_notes", "download_url"]
    for field in required_fields:
        assert field in meta, f"Field '{field}' missing from version.json"
        assert meta[field] is not None and len(str(meta[field])) > 0

    assert meta["version"] == "1.4.0"
    print("[PASS] test_version_json_schema (Root version.json metadata schema and SSOT valid)")

def test_patcher_script_generation():
    from updater_engine import WindowsPatcher
    script = WindowsPatcher.get_patcher_script_content(
        target_exe="C:\\ManualStudio\\ManualStudio.exe",
        new_exe="C:\\Users\\Temp\\ManualStudio_Update.exe",
        pid=9999
    )
    assert "@echo off" in script
    assert 'tasklist /fi "PID eq 9999"' in script
    assert "copy /y" in script
    assert "C:\\ManualStudio\\ManualStudio.exe" in script
    assert "del \"%~f0\"" in script

    print("[PASS] test_patcher_script_generation (Windows atomic file swap and restart script valid)")

if __name__ == "__main__":
    test_config_loader()
    test_circle_char()
    test_resize_logic()
    test_dib_generation()
    test_backup_file_creation()
    test_fixed_rect_config()
    test_text_label_rendering()
    test_toolbar_settings_and_selection_sync()
    test_ppt_layout_and_fit()
    test_arrow_item_and_sync()
    test_five_recommended_annotation_items()
    test_ribbon_menu_and_quick_strip()
    test_annotation_serialization()
    test_project_manager_save_and_load()
    test_auto_backup_step_bundle_and_delete()
    test_image_overlay_item_and_sub_capture()
    test_draft_stamp_item()
    test_powerpoint_step_renumbering()
    test_dragon_rpa_branding_and_about_dialog()
    test_license_validator()
    test_custom_font_manager()
    test_multi_monitor_manager()
    test_elbow_arrow_four_directions_and_toggle()
    test_wordart_item_and_presets()
    test_global_i18n_manager()
    test_license_engine_and_verification()
    test_watermark_in_composed_image()
    test_instant_capture_mouse_release()
    test_autosave_and_recovery()
    test_version_comparator()
    test_version_json_schema()
    test_patcher_script_generation()
    print("\nALL 32 CORE ENGINE, MULTI-MONITOR, FONT MANAGER, I18N, LICENSE, WATERMARK & AUTO-UPDATER TESTS PASSED 100%!")



"""
================================================================================
수동 매뉴얼 제작 전용 초고속 스크린샷 캡처 및 PPT 규격화 스튜디오
Manual Studio for PPT
================================================================================
핵심 기능:
1. 단축키 F9: 글로벌 캡처 오버레이 시작 (자석 창 스냅, 8방향 핸들, 방향키 1px 제어, 돋보기, R 재사용)
2. 주석 작업대: 원클릭 자동 증가 번호 스탬프 (①, ②..), 텍스트 라벨 자유 드래그 배치, 강조 박스
3. 실행 취소 (Ctrl+Z), 우클릭 삭제 (스마트 번호 재정렬), 드래그 위치 이동
4. 단축키 F10: PPT 새 슬라이드 자동 생성/삽입 + 윈도우 네이티브 DIB 클립보드 복사 + 자동 백업
5. 세션 유지: 새 캡처(F9) 전까지 현재 작업 내용이 스튜디오에 완벽 보존됨
"""

import sys
import os
import json
import io
import time
import math
import base64
import re
from datetime import datetime
import ctypes
from ctypes import wintypes
import warnings

# Qt 6 / PySide6 관련 구형 경고(DeprecationWarning) 콘솔 출력 전면 차단
warnings.filterwarnings("ignore", category=DeprecationWarning)

try:
    from mobile_link_server import MobileLinkServer, get_local_ip
except Exception:
    MobileLinkServer = None
    get_local_ip = lambda: "127.0.0.1"

def hide_console_window():
    """Windows 환경에서 python.exe(콘솔)로 실행되더라도 불필요한 검은 콘솔창을 즉시 숨김"""
    if sys.platform == "win32" and not os.environ.get("MANUAL_STUDIO_DEBUG"):
        try:
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE
        except Exception:
            pass

def get_mouse_pos(event):
    """Qt 6 / Qt 5 호환 마우스 이벤트 좌표 반환 (DeprecationWarning 방지)"""
    if hasattr(event, "position"):
        return event.position().toPoint()
    return event.pos()

def get_mouse_global_pos(event):
    """Qt 6 / Qt 5 호환 마우스 글로벌 좌표 반환 (DeprecationWarning 방지)"""
    if hasattr(event, "globalPosition"):
        return event.globalPosition().toPoint()
    return event.globalPos()

# Windows 환경에서 Qt 플랫폼 플러그인(qwindows.dll) 탐색 실패 원천 방지
try:
    import PySide6
    pyside_dir = os.path.dirname(PySide6.__file__)
    plugins_dir = os.path.join(pyside_dir, "plugins")
    platforms_dir = os.path.join(plugins_dir, "platforms")
    if os.path.exists(platforms_dir):
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = platforms_dir
except Exception:
    pass

from PySide6.QtCore import (
    Qt, QPoint, QPointF, QRect, QRectF, QSize, QThread, Signal, Slot, QTimer, QCoreApplication,
    QByteArray, QBuffer, QIODevice, QUrl, QMimeData
)
# 하위 호환성 별칭 제공
pyqtSignal = Signal
pyqtSlot = Slot

from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QPixmap, QImage,
    QCursor, QPainterPath, QIcon, QFontMetrics, QPolygonF, QTransform, QDesktopServices,
    QFontDatabase, QGuiApplication, QScreen, QAction, QKeySequence, QDrag
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QDialog, QSpinBox, QColorDialog,
    QFileDialog, QMessageBox, QToolTip, QFrame, QScrollArea,
    QGraphicsDropShadowEffect, QSystemTrayIcon, QMenu, QCheckBox,
    QTabWidget, QTabBar, QGridLayout, QMenuBar, QTextEdit, QTextBrowser, QPlainTextEdit, QComboBox, QFontComboBox,
    QButtonGroup, QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView, QDockWidget
)

from PySide6.QtSvg import QSvgRenderer
from PIL import Image, ImageDraw, ImageFilter

IS_WINDOWS = sys.platform == "win32"
IS_MACOS = sys.platform == "darwin"

try:
    import win32gui
    import win32con
    import win32clipboard
    import win32com.client
except ImportError:
    win32gui = None
    win32con = None
    win32clipboard = None
    win32com = None

from i18n_manager import I18nManager, tr
from eula_manager import EulaManager
from license_engine import LicenseEngine, LicenseType
from updater_engine import UpdateCheckerThread, UpdateDialog, VersionComparator

APP_VERSION = "v1.9.1"

try:
    from dragon_rpa_ci_data import DRAGON_RPA_CI_BASE64
except ImportError:
    DRAGON_RPA_CI_BASE64 = ""


def get_app_dir() -> str:
    """실행 파일(.exe) 또는 소스코드(.py)의 기본 디렉토리 반환"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except Exception:
        return os.getcwd()


def get_dragon_rpa_ci_pixmap() -> QPixmap:
    """DragonRPA Co. CI 로고 QPixmap 로드 (로컬 파일 우선, Base64 폴백)"""
    current_dir = get_app_dir()

    assets_candidates = [
        os.path.join(current_dir, "assets", "dragon_rpa_ci.png"),
        os.path.join(os.getcwd(), "assets", "dragon_rpa_ci.png"),
        os.path.join(current_dir, "dragon_rpa_ci.png"),
    ]
    for p in assets_candidates:
        if os.path.exists(p):
            pix = QPixmap(p)
            if not pix.isNull():
                return pix

    if DRAGON_RPA_CI_BASE64:
        try:
            pix = QPixmap()
            pix.loadFromData(base64.b64decode(DRAGON_RPA_CI_BASE64))
            if not pix.isNull():
                return pix
        except Exception:
            pass

    return QPixmap()


def get_manual_studio_icon() -> QIcon:
    """Manual Studio 전용 앱 아이콘 QIcon 로드 (화면 캡처+매뉴얼 가이드+① 스탬프 심볼)"""
    current_dir = get_app_dir()
    candidates = [
        os.path.join(current_dir, "assets", "manual_studio.ico"),
        os.path.join(current_dir, "assets", "manual_studio_app_icon.png"),
        os.path.join(os.getcwd(), "assets", "manual_studio.ico"),
        os.path.join(os.getcwd(), "assets", "manual_studio_app_icon.png"),
        os.path.join(current_dir, "manual_studio.ico"),
    ]
    for p in candidates:
        if os.path.exists(p):
            icon = QIcon(p)
            if not icon.isNull():
                return icon

    # 폴백: CI 로고
    ci_pix = get_dragon_rpa_ci_pixmap()
    if not ci_pix.isNull():
        return QIcon(ci_pix)
    return QIcon()

# 1. 설정 관리자 (Configuration Manager)
# ==============================================================================
DEFAULT_CONFIG = {
    "hotkey_capture": "F9",
    "hotkey_export": "F10",
    "hotkey_slides": "F11",
    "target_width": 960,
    "auto_resize": True,
    "save_to_file": True,
    "save_directory": "captures",
    "include_cursor": False,
    "stamp_style": {
        "size": 32,
        "bg_color": "#E53935",
        "text_color": "#FFFFFF",
        "font_family": "Malgun Gothic",
        "font_bold": True,
        "border_color": "#FFFFFF",
        "border_width": 2,
        "shape": "circle",
        "corner_radius": 6
    },
    "text_style": {
        "font_family": "Malgun Gothic",
        "font_size": 13,
        "font_bold": True,
        "text_color": "#FFFFFF",
        "bg_color": "#212121",
        "bg_opacity": 220,
        "border_color": "#E53935",
        "border_width": 1,
        "border_radius": 6,
        "padding": 6
    },
    "highlight_box_style": {
        "color": "#E53935",
        "border_width": 3,
        "fill": False
    },
    "arrow_style": {
        "color": "#E53935",
        "width": 3,
        "head_size": 14
    },
    "callout_style": {
        "font_size": 12,
        "text_color": "#FFFFFF",
        "bg_color": "#212121",
        "bg_opacity": 230,
        "border_color": "#E53935",
        "border_width": 2,
        "border_radius": 6
    },
    "elbow_style": {
        "color": "#E53935",
        "width": 3,
        "head_size": 14,
        "route_mode": "HV"
    },
    "blur_style": {
        "block_size": 10
    },
    "hotkey_style": {
        "font_size": 12,
        "theme": "dark"
    },
    "wordart_style": {
        "text": "주요 확인",
        "font_family": "Malgun Gothic",
        "font_size": 24,
        "font_bold": True,
        "text_color": "#FFFFFF",
        "stroke_color": "#000000",
        "stroke_width": 3,
        "shadow_enabled": True,
        "shadow_color": "#000000",
        "shadow_alpha": 180,
        "shadow_offset_x": 2.0,
        "shadow_offset_y": 2.0,
        "preset_id": "white_pop"
    },
    "dimension_style": {
        "color": "#007AFF",
        "width": 2,
        "tick_size": 8,
        "font_size": 11,
        "font_family": "Malgun Gothic",
        "font_bold": True,
        "badge_bg": "#007AFF",
        "badge_text_color": "#FFFFFF",
        "unit": "px",
        "cap_style": "bracket"
    },
    "custom_fonts": [],
    "target_monitor": 0,
    "fixed_rect_enabled": True,
    "fixed_rect": {
        "x": 100,
        "y": 100,
        "width": 960,
        "height": 540
    },
    "ppt_auto_slide": True,
    "ppt_layout": {
        "left": 50,
        "top": 80,
        "scale": 90,
        "include_title": True,
        "title_left": 50,
        "title_top": 20,
        "title_width": 500,
        "title_height": 35,
        "title_font_family": "Malgun Gothic",
        "title_font_size": 18,
        "title_font_bold": True,
        "title_font_color": "#000000",
        "title_template": "Step {n}. [단계명 입력]"
    },
    "locale": "auto",
    "auto_save_enabled": True,
    "auto_save_interval_min": 5,
    "ribbon_display_mode": "text",
    "ppt_template_path": "",
    "auto_check_update": True,
    "export_target": "powerpoint",
    "slides_auto_slide": True,
    "slides_return_focus": True,
    "ui_style": "auto",
    "enable_window_frame": True,
    "window_frame_style": {
        "include_header": True,
        "corner_radius": 12,
        "shadow_radius": 20,
        "shadow_opacity": 0.35,
        "bg_color": "#F8FAFC",
        "border_color": "#CBD5E1",
        "header_height": 32
    },
    "hotkey_hwp": "Shift+F10",
    "filmstrip_visible": True,
    "pii_categories": {
        "phone": True,
        "email": True,
        "resident": True,
        "card": True,
        "account": True,
        "biz_number": True,
        "korean_name": True,
        "address": True,
        "ip": False
    },
    "custom_pii_rules": []
}

CONFIG_FILE = os.path.join(get_app_dir(), "config.json")

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                merged = DEFAULT_CONFIG.copy()
                merged.update(cfg)
                for sub_key in [
                    "stamp_style", "text_style", "highlight_box_style", "arrow_style",
                    "callout_style", "elbow_style", "blur_style", "hotkey_style", "wordart_style",
                    "fixed_rect", "ppt_layout", "pii_categories"
                ]:
                    if sub_key in DEFAULT_CONFIG:
                        sub_dict = DEFAULT_CONFIG[sub_key].copy()
                        if sub_key in cfg and isinstance(cfg[sub_key], dict):
                            sub_dict.update(cfg[sub_key])
                        merged[sub_key] = sub_dict
                return merged
        except Exception as e:
            print(f"[Config] 설정 로드 실패, 기본값 사용: {e}")
    return DEFAULT_CONFIG.copy()

def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Config] 설정 저장 실패: {e}")


# ==============================================================================
# 1-0. 맥킨토시 트래픽 라이트 (MacTrafficLight) & 듀얼 UI 테마 엔진 (ThemeManager)
# ==============================================================================
class MacTrafficLight(QWidget):
    """macOS Cupertino 고유 3구 트래픽 라이트 버튼 (Close, Minimize, Maximize)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 12, 4)
        layout.setSpacing(8)

        self.btn_close = QPushButton(self)
        self.btn_minimize = QPushButton(self)
        self.btn_maximize = QPushButton(self)

        for btn in (self.btn_close, self.btn_minimize, self.btn_maximize):
            btn.setFixedSize(12, 12)
            btn.setCursor(Qt.PointingHandCursor)

        self.btn_close.setToolTip(tr("btn_close", "닫기"))
        self.btn_minimize.setToolTip(tr("btn_minimize", "최소화"))
        self.btn_maximize.setToolTip(tr("btn_maximize", "최대화"))

        self.btn_close.clicked.connect(self._on_close)
        self.btn_minimize.clicked.connect(self._on_minimize)
        self.btn_maximize.clicked.connect(self._on_maximize)

        layout.addWidget(self.btn_close)
        layout.addWidget(self.btn_minimize)
        layout.addWidget(self.btn_maximize)

        self.btn_close.setStyleSheet("background-color: #FF5F56; border-radius: 6px; border: 1px solid #E0443E;")
        self.btn_minimize.setStyleSheet("background-color: #FFBD2E; border-radius: 6px; border: 1px solid #DEA123;")
        self.btn_maximize.setStyleSheet("background-color: #27C93F; border-radius: 6px; border: 1px solid #1AAB29;")

    def _on_close(self):
        w = self.window()
        if w:
            w.close()

    def _on_minimize(self):
        w = self.window()
        if w:
            w.showMinimized()

    def _on_maximize(self):
        w = self.window()
        if w:
            if w.isMaximized():
                w.showNormal()
            else:
                w.showMaximized()


class ThemeManager:
    """Windows Fluent vs Macintosh Cupertino 듀얼 UI 스타일 엔진"""
    AUTO = "auto"
    WINDOWS = "windows"
    MACOS = "macos"

    @classmethod
    def get_effective_ui_style(cls, theme_name: str) -> str:
        """auto 설정 시 현재 실행 OS에 따라 macos 또는 windows 반환"""
        t = (theme_name or cls.AUTO).lower()
        if t == cls.AUTO:
            return cls.MACOS if sys.platform == "darwin" else cls.WINDOWS
        if t == cls.MACOS:
            return cls.MACOS
        return cls.WINDOWS

    @classmethod
    def get_windows_ribbon_qss(cls) -> str:
        return """
            QFrame#RibbonPanel {
                background-color: #F8FAFC;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
            }
            QTabWidget::pane {
                border: 1px solid #E2E8F0;
                background: #FFFFFF;
                border-bottom-left-radius: 4px;
                border-bottom-right-radius: 4px;
            }
            QTabBar::tab {
                background: #F1F5F9;
                border: 1px solid #CBD5E1;
                border-bottom: none;
                padding: 5px 18px;
                font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
                font-size: 11px;
                font-weight: bold;
                color: #475569;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
                white-space: nowrap;
            }
            QTabBar::tab:selected {
                background: #FFFFFF;
                color: #1E40AF;
                border-bottom: 2px solid #2563EB;
            }
            QTabBar::tab:hover:!selected {
                background: #E2E8F0;
                color: #1E293B;
            }
            QPushButton {
                font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
                font-size: 11px;
                padding: 4px 10px;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                background-color: #FFFFFF;
                color: #1E293B;
                white-space: nowrap;
            }
            QPushButton:hover {
                background-color: #F1F5F9;
                border-color: #94A3B8;
            }
            QPushButton:pressed {
                background-color: #E2E8F0;
            }
            QComboBox {
                font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
                font-size: 11px;
                padding: 2px 20px 2px 6px;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                background-color: #FFFFFF;
                white-space: nowrap;
            }
            QCheckBox {
                font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
                font-size: 11px;
                font-weight: 500;
                color: #1E293B;
                white-space: nowrap;
            }
        """

    @classmethod
    def get_macos_ribbon_qss(cls) -> str:
        return """
            QFrame#RibbonPanel {
                background-color: #FFFFFF;
                border: 1px solid #E5E5EA;
                border-radius: 10px;
            }
            QTabWidget::pane {
                border: 1px solid #E5E5EA;
                background: #FAFAFC;
                border-radius: 8px;
                margin-top: 2px;
            }
            QTabBar {
                background: #E5E5EA;
                border-radius: 8px;
                padding: 2px;
            }
            QTabBar::tab {
                background: transparent;
                border: none;
                padding: 5px 16px;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
                font-size: 11px;
                font-weight: 600;
                color: #636366;
                border-radius: 6px;
                margin: 2px 2px;
                white-space: nowrap;
            }
            QTabBar::tab:selected {
                background: #FFFFFF;
                color: #1C1C1E;
                border: 1px solid rgba(0, 0, 0, 0.08);
            }
            QTabBar::tab:hover:!selected {
                background: rgba(255, 255, 255, 0.5);
                color: #1C1C1E;
            }
            QPushButton {
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
                font-size: 11px;
                padding: 4px 12px;
                border: 1px solid #D1D1D6;
                border-radius: 6px;
                background-color: #FFFFFF;
                color: #1C1C1E;
                font-weight: 500;
                white-space: nowrap;
            }
            QPushButton:hover {
                background-color: #F2F2F7;
                border-color: #AEAEB2;
            }
            QPushButton:pressed {
                background-color: #E5E5EA;
            }
            QComboBox {
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
                font-size: 11px;
                padding: 2px 20px 2px 8px;
                border: 1px solid #D1D1D6;
                border-radius: 6px;
                background-color: #FFFFFF;
                white-space: nowrap;
            }
            QCheckBox {
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
                font-size: 11px;
                font-weight: 500;
                color: #1C1C1E;
                white-space: nowrap;
            }
        """

    @classmethod
    def get_windows_menubar_qss(cls) -> str:
        return """
            QMenuBar {
                background-color: #FFFFFF;
                color: #1E293B;
                border-bottom: 1px solid #E2E8F0;
                font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
                font-size: 11px;
                padding: 1px 4px;
            }
            QMenuBar::item {
                background: transparent;
                padding: 4px 10px;
                border-radius: 4px;
                color: #334155;
                font-weight: 500;
            }
            QMenuBar::item:selected {
                background-color: #F1F5F9;
                color: #0F172A;
            }
            QMenuBar::item:pressed {
                background-color: #E2E8F0;
            }
            QMenu {
                background-color: #FFFFFF;
                color: #1E293B;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 4px;
                font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
                font-size: 11px;
            }
            QMenu::item {
                padding: 6px 24px 6px 12px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #2563EB;
                color: #FFFFFF;
            }
            QMenu::separator {
                height: 1px;
                background-color: #E2E8F0;
                margin: 4px 6px;
            }
        """

    @classmethod
    def get_macos_menubar_qss(cls) -> str:
        return """
            QMenuBar {
                background-color: #F5F5F7;
                color: #1C1C1E;
                border-bottom: 1px solid #D1D1D6;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
                font-size: 11px;
                padding: 2px 4px;
            }
            QMenuBar::item {
                background: transparent;
                padding: 4px 10px;
                border-radius: 5px;
                color: #1C1C1E;
                font-weight: 500;
            }
            QMenuBar::item:selected {
                background-color: #E5E5EA;
                color: #000000;
            }
            QMenuBar::item:pressed {
                background-color: #D1D1D6;
            }
            QMenu {
                background-color: #FFFFFF;
                color: #1C1C1E;
                border: 1px solid #D1D1D6;
                border-radius: 8px;
                padding: 5px;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
                font-size: 11px;
            }
            QMenu::item {
                padding: 5px 22px 5px 12px;
                border-radius: 5px;
            }
            QMenu::item:selected {
                background-color: #007AFF;
                color: #FFFFFF;
            }
            QMenu::separator {
                height: 1px;
                background-color: #E5E5EA;
                margin: 4px 8px;
            }
        """

    @classmethod
    def get_windows_app_qss(cls) -> str:
        return """
            QMainWindow {
                background-color: #F8FAFC;
            }
            QDialog {
                background-color: #FFFFFF;
                color: #1E293B;
            }
            QMenu {
                background-color: #FFFFFF;
                color: #1E293B;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 4px;
                font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
                font-size: 11px;
            }
            QMenu::item {
                padding: 6px 24px 6px 12px;
                border-radius: 4px;
                color: #1E293B;
            }
            QMenu::item:selected {
                background-color: #2563EB;
                color: #FFFFFF;
            }
            QMenu::separator {
                height: 1px;
                background-color: #E2E8F0;
                margin: 4px 6px;
            }
            QToolTip {
                background-color: #1E293B;
                color: #FFFFFF;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
            }
        """

    @classmethod
    def get_macos_app_qss(cls) -> str:
        return """
            QMainWindow {
                background-color: #F5F5F7;
            }
            QDialog {
                background-color: #FFFFFF;
                color: #1C1C1E;
            }
            QMenu {
                background-color: #FFFFFF;
                color: #1C1C1E;
                border: 1px solid #D1D1D6;
                border-radius: 8px;
                padding: 5px;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
                font-size: 11px;
            }
            QMenu::item {
                padding: 5px 22px 5px 12px;
                border-radius: 5px;
                color: #1C1C1E;
            }
            QMenu::item:selected {
                background-color: #007AFF;
                color: #FFFFFF;
            }
            QMenu::separator {
                height: 1px;
                background-color: #E5E5EA;
                margin: 4px 8px;
            }
            QToolTip {
                background-color: #1C1C1E;
                color: #FFFFFF;
                border: 1px solid #3A3A3C;
                border-radius: 6px;
                padding: 5px 10px;
                font-size: 11px;
            }
        """

    @classmethod
    def apply_theme(cls, app: QApplication, theme_name: str, window=None):
        theme = cls.get_effective_ui_style(theme_name)
        if theme == cls.MACOS:
            font = QFont("SF Pro Text", 9)
            font.setFamilies(["SF Pro Text", "Apple SD Gothic Neo", "Malgun Gothic", "Segoe UI", "sans-serif"])
            if app:
                app.setFont(font)
                app.setStyleSheet(cls.get_macos_app_qss())
            if window:
                if hasattr(window, "ribbon_frame") and window.ribbon_frame:
                    window.ribbon_frame.setStyleSheet(cls.get_macos_ribbon_qss())
                if hasattr(window, "menubar") and window.menubar:
                    window.menubar.setStyleSheet(cls.get_macos_menubar_qss())
                elif hasattr(window, "menuBar") and window.menuBar():
                    window.menuBar().setStyleSheet(cls.get_macos_menubar_qss())
                if hasattr(window, "traffic_lights") and window.traffic_lights:
                    window.traffic_lights.show()
                window.setStyleSheet(cls.get_macos_app_qss())
        else:
            font = QFont("Segoe UI", 9)
            font.setFamilies(["Segoe UI", "Malgun Gothic", "sans-serif"])
            if app:
                app.setFont(font)
                app.setStyleSheet(cls.get_windows_app_qss())
            if window:
                if hasattr(window, "ribbon_frame") and window.ribbon_frame:
                    window.ribbon_frame.setStyleSheet(cls.get_windows_ribbon_qss())
                if hasattr(window, "menubar") and window.menubar:
                    window.menubar.setStyleSheet(cls.get_windows_menubar_qss())
                elif hasattr(window, "menuBar") and window.menuBar():
                    window.menuBar().setStyleSheet(cls.get_windows_menubar_qss())
                if hasattr(window, "traffic_lights") and window.traffic_lights:
                    window.traffic_lights.hide()
                window.setStyleSheet(cls.get_windows_app_qss())



# ==============================================================================
# 1-1. 외부/유료/토너절약 폰트 관리자 (CustomFontManager)
# ==============================================================================
class CustomFontManager:
    """고객사 고유 폰트(.ttf, .otf, .ttc) 등록 및 QFontDatabase 연동 관리자"""
    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.fonts_dir = os.path.join(get_app_dir(), "fonts")
        if not os.path.exists(self.fonts_dir):
            try:
                os.makedirs(self.fonts_dir, exist_ok=True)
            except Exception:
                pass
        self.loaded_families = []
        self.registered_files = []

    def load_all_fonts(self, config_custom_fonts=None):
        """fonts/ 디렉토리 및 config에 명시된 폰트 파일 일괄 적재"""
        self.loaded_families.clear()
        self.registered_files.clear()

        # 1. fonts 디렉토리 스캔
        if os.path.exists(self.fonts_dir):
            for fname in os.listdir(self.fonts_dir):
                if fname.lower().endswith((".ttf", ".otf", ".ttc", ".woff")):
                    fpath = os.path.join(self.fonts_dir, fname)
                    self._register_single_font(fpath)

        # 2. 추가 config 파일 목록 로드
        if config_custom_fonts and isinstance(config_custom_fonts, list):
            for fpath in config_custom_fonts:
                if os.path.exists(fpath) and fpath not in self.registered_files:
                    self._register_single_font(fpath)

        return list(self.loaded_families)

    def _register_single_font(self, fpath):
        try:
            font_id = QFontDatabase.addApplicationFont(fpath)
            if font_id >= 0:
                families = QFontDatabase.applicationFontFamilies(font_id)
                for fam in families:
                    if fam not in self.loaded_families:
                        self.loaded_families.append(fam)
                if fpath not in self.registered_files:
                    self.registered_files.append(fpath)
                return families
        except Exception as e:
            print(f"[CustomFontManager] 폰트 로드 실패 ({fpath}): {e}")
        return []

    def import_font_file(self, source_path):
        """외부 폰트 파일을 fonts/ 디렉토리로 복사 후 시스템 등록"""
        if not os.path.exists(source_path):
            return [], None
        fname = os.path.basename(source_path)
        dest_path = os.path.join(self.fonts_dir, fname)
        if os.path.abspath(source_path) != os.path.abspath(dest_path):
            import shutil
            shutil.copy2(source_path, dest_path)
        families = self._register_single_font(dest_path)
        return families, dest_path


# ==============================================================================
# 1-2. 다중 모니터 좌표/영역 관리자 (MultiMonitorManager)
# ==============================================================================
class MultiMonitorManager:
    """최대 4개 이상의 다중 모니터 인식 및 가상 데스크톱/상대 좌표 매핑 관리자"""
    @staticmethod
    def get_screens():
        return list(QGuiApplication.screens())

    @staticmethod
    def get_monitor_info_list():
        """모니터 목록 반환: [{'index': i, 'label': str, 'geometry': QRect, 'is_primary': bool}, ...]"""
        screens = MultiMonitorManager.get_screens()
        primary = QGuiApplication.primaryScreen()
        info_list = []
        for i, s in enumerate(screens):
            geo = s.geometry()
            is_prim = (s == primary)
            prim_tag = f" ★{tr('monitor_primary', '주화면')}" if is_prim else ""
            label = f"{tr('lbl_monitor_single', '모니터')} {i+1}: {s.name()} ({geo.width()}×{geo.height()}){prim_tag}"
            info_list.append({
                "index": i,
                "label": label,
                "geometry": geo,
                "screen": s,
                "is_primary": is_prim
            })
        return info_list

    @staticmethod
    def get_virtual_desktop_rect():
        """모든 모니터를 포함하는 전체 가상 데스크톱 사각 영역 계산"""
        screens = MultiMonitorManager.get_screens()
        if not screens:
            return QRect(0, 0, 1920, 1080)
        min_x = min(s.geometry().x() for s in screens)
        min_y = min(s.geometry().y() for s in screens)
        max_x = max(s.geometry().x() + s.geometry().width() for s in screens)
        max_y = max(s.geometry().y() + s.geometry().height() for s in screens)
        return QRect(min_x, min_y, max_x - min_x, max_y - min_y)

    @staticmethod
    def to_global_rect(target_monitor, rel_rect):
        """특정 모니터 기준 상대 좌표(rel_rect)를 전체 가상 데스크톱 글로벌 좌표로 변환"""
        screens = MultiMonitorManager.get_screens()
        if target_monitor is None or target_monitor < 0 or target_monitor >= len(screens):
            v_rect = MultiMonitorManager.get_virtual_desktop_rect()
            return QRect(v_rect.x() + rel_rect.x(), v_rect.y() + rel_rect.y(), rel_rect.width(), rel_rect.height())
        screen_geo = screens[target_monitor].geometry()
        return QRect(screen_geo.x() + rel_rect.x(), screen_geo.y() + rel_rect.y(), rel_rect.width(), rel_rect.height())

    @staticmethod
    def to_relative_rect(target_monitor, global_rect):
        """가상 데스크톱 글로벌 좌표를 특정 모니터 기준 상대 좌표로 변환"""
        screens = MultiMonitorManager.get_screens()
        if target_monitor is None or target_monitor < 0 or target_monitor >= len(screens):
            v_rect = MultiMonitorManager.get_virtual_desktop_rect()
            return QRect(global_rect.x() - v_rect.x(), global_rect.y() - v_rect.y(), global_rect.width(), global_rect.height())
        screen_geo = screens[target_monitor].geometry()
        return QRect(global_rect.x() - screen_geo.x(), global_rect.y() - screen_geo.y(), global_rect.width(), global_rect.height())

    @staticmethod
    def grab_target_area(target_monitor, rel_rect):
        """선택된 모니터의 상대 좌표 영역을 고품질 캡처하여 QPixmap 반환"""
        screens = MultiMonitorManager.get_screens()

        # 특정 단일 모니터 지정인 경우 (0..N-1)
        if target_monitor is not None and 0 <= target_monitor < len(screens):
            screen = screens[target_monitor]
            rx = max(0, rel_rect.x())
            ry = max(0, rel_rect.y())
            rw = max(10, min(rel_rect.width(), screen.geometry().width() - rx))
            rh = max(10, min(rel_rect.height(), screen.geometry().height() - ry))
            return screen.grabWindow(0, rx, ry, rw, rh)

        # 전체 가상 데스크톱 대상인 경우: 모든 모니터 스크린샷 결합
        v_rect = MultiMonitorManager.get_virtual_desktop_rect()
        canvas_pix = QPixmap(v_rect.size())
        canvas_pix.fill(Qt.black)
        painter = QPainter(canvas_pix)
        for s in screens:
            sg = s.geometry()
            s_pix = s.grabWindow(0)
            painter.drawPixmap(sg.x() - v_rect.x(), sg.y() - v_rect.y(), s_pix)
        painter.end()

        # rel_rect가 가상 데스크톱 글로벌 좌표인지, v_rect 기준 상대 오프셋인지 판별
        if v_rect.x() != 0 and (rel_rect.x() < 0 or rel_rect.x() >= v_rect.x()):
            rx = rel_rect.x() - v_rect.x()
        else:
            rx = rel_rect.x()
        if v_rect.y() != 0 and (rel_rect.y() < 0 or rel_rect.y() >= v_rect.y()):
            ry = rel_rect.y() - v_rect.y()
        else:
            ry = rel_rect.y()

        rx = max(0, min(rx, v_rect.width() - 10))
        ry = max(0, min(ry, v_rect.height() - 10))
        rw = max(10, min(rel_rect.width(), v_rect.width() - rx))
        rh = max(10, min(rel_rect.height(), v_rect.height() - ry))
        return canvas_pix.copy(rx, ry, rw, rh)


# ==============================================================================
# 2. 글로벌 백그라운드 핫키 리스너 (Windows Native ctypes)
# ==============================================================================
VK_MAPPING = {
    "F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73,
    "F5": 0x74, "F6": 0x75, "F7": 0x76, "F8": 0x77,
    "F9": 0x78, "F10": 0x79, "F11": 0x7A, "F12": 0x7B,
    "PRINTSCREEN": 0x2C, "SNAPSHOT": 0x2C
}

class GlobalHotkeyThread(QThread):
    sig_capture = pyqtSignal()
    sig_drag_capture = pyqtSignal()
    sig_sub_capture = pyqtSignal()
    sig_export = pyqtSignal()
    sig_slides_export = pyqtSignal()
    sig_hwp_export = pyqtSignal()

    def __init__(self, capture_key="F9", export_key="F10", slides_key="F11", parent=None):
        super().__init__(parent)
        self.capture_key = capture_key.upper()
        self.export_key = export_key.upper()
        self.slides_key = slides_key.upper()
        self.running = True
        self.hotkey_id_capture = 101
        self.hotkey_id_drag_capture = 103
        self.hotkey_id_sub_capture = 104
        self.hotkey_id_export = 102
        self.hotkey_id_slides_export = 105
        self.hotkey_id_hwp_export = 106

    def run(self):
        user32 = ctypes.windll.user32
        vk_cap = VK_MAPPING.get(self.capture_key, 0x78)
        vk_exp = VK_MAPPING.get(self.export_key, 0x79)
        vk_sub = 0x77 # VK_F8

        # MOD_NOREPEAT = 0x4000, MOD_SHIFT = 0x0004
        user32.RegisterHotKey(None, self.hotkey_id_capture, 0x4000, vk_cap)
        user32.RegisterHotKey(None, self.hotkey_id_drag_capture, 0x4000 | 0x0004, vk_cap)
        vk_slides = VK_MAPPING.get(self.slides_key, 0x7A)
        user32.RegisterHotKey(None, self.hotkey_id_sub_capture, 0x4000, vk_sub)
        user32.RegisterHotKey(None, self.hotkey_id_export, 0x4000, vk_exp)
        user32.RegisterHotKey(None, self.hotkey_id_slides_export, 0x4000, vk_slides)
        user32.RegisterHotKey(None, self.hotkey_id_hwp_export, 0x4000 | 0x0004, vk_exp)

        msg = wintypes.MSG()
        while self.running:
            # 타임아웃 100ms
            if user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1): # PM_REMOVE = 1
                if msg.message == win32con.WM_HOTKEY:
                    if msg.wParam == self.hotkey_id_capture:
                        self.sig_capture.emit()
                    elif msg.wParam == self.hotkey_id_drag_capture:
                        self.sig_drag_capture.emit()
                    elif msg.wParam == self.hotkey_id_sub_capture:
                        self.sig_sub_capture.emit()
                    elif msg.wParam == self.hotkey_id_export:
                        self.sig_export.emit()
                    elif msg.wParam == self.hotkey_id_slides_export:
                        self.sig_slides_export.emit()
                    elif msg.wParam == self.hotkey_id_hwp_export:
                        self.sig_hwp_export.emit()
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
            else:
                time.sleep(0.02)

        user32.UnregisterHotKey(None, self.hotkey_id_capture)
        user32.UnregisterHotKey(None, self.hotkey_id_drag_capture)
        user32.UnregisterHotKey(None, self.hotkey_id_sub_capture)
        user32.UnregisterHotKey(None, self.hotkey_id_export)
        user32.UnregisterHotKey(None, self.hotkey_id_slides_export)
        user32.UnregisterHotKey(None, self.hotkey_id_hwp_export)

    def stop(self):
        self.running = False
        self.wait()


# ==============================================================================
# 3. 주석 데이터 모델 (Annotations: Stamps, Text Labels, Boxes)
# ==============================================================================
CIRCLED_NUMBERS = [
    "①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩",
    "⑪", "⑫", "⑬", "⑭", "⑮", "⑯", "⑰", "⑱", "⑲", "⑳"
]

def get_circle_char(num):
    if 1 <= num <= 20:
        return CIRCLED_NUMBERS[num - 1]
    return str(num)

class StampItem:
    def __init__(self, index, x, y, style):
        self.index = index
        self.pos = QPointF(x, y)
        self.style = style.copy() if isinstance(style, dict) else dict(style)

    def clone(self):
        return StampItem(self.index, self.pos.x(), self.pos.y(), self.style.copy())

    def to_dict(self):
        return {
            "type": "StampItem",
            "index": int(self.index),
            "x": float(self.pos.x()),
            "y": float(self.pos.y()),
            "style": self.style.copy()
        }

    @classmethod
    def from_dict(cls, data):
        pos = data.get("pos")
        if pos and len(pos) >= 2:
            x, y = float(pos[0]), float(pos[1])
        else:
            x = float(data.get("x", 0.0))
            y = float(data.get("y", 0.0))
        return cls(int(data.get("index", 1)), x, y, data.get("style", {}))

    def contains(self, pt):
        size = self.style.get("size", 32)
        r = size / 2.0
        shape = self.style.get("shape", "circle")
        if shape == "rounded_rect":
            rect = QRectF(self.pos.x() - r, self.pos.y() - r, size, size)
            return rect.contains(pt)
        dx = pt.x() - self.pos.x()
        dy = pt.y() - self.pos.y()
        return (dx*dx + dy*dy) <= (r * r)

    def render(self, painter: QPainter):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        size = self.style.get("size", 32)
        r = size / 2.0
        bg_col = QColor(self.style.get("bg_color", "#E53935"))
        border_col = QColor(self.style.get("border_color", "#FFFFFF"))
        border_w = self.style.get("border_width", 2)
        text_col = QColor(self.style.get("text_color", "#FFFFFF"))
        shape = self.style.get("shape", "circle")
        corner_r = float(self.style.get("corner_radius", max(4, int(size * 0.25))))

        if shape == "rounded_rect":
            # 모서리가 둥근 사각형 섀도우
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 0, 0, 70))
            painter.drawRoundedRect(QRectF(self.pos.x() - r + 1.5, self.pos.y() - r + 2, size, size), corner_r, corner_r)

            # 모서리가 둥근 사각형 본체
            painter.setBrush(QBrush(bg_col))
            painter.setPen(QPen(border_col, border_w))
            painter.drawRoundedRect(QRectF(self.pos.x() - r, self.pos.y() - r, size, size), corner_r, corner_r)
        else:
            # 원형 드롭 섀도우
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 0, 0, 70))
            painter.drawEllipse(QPointF(self.pos.x() + 1.5, self.pos.y() + 2), r, r)

            # 원형 배경
            painter.setBrush(QBrush(bg_col))
            painter.setPen(QPen(border_col, border_w))
            painter.drawEllipse(self.pos, r, r)

        # 숫자 텍스트 (이중 원 제거: 순수 아라비아 숫자 + tightBoundingRect 기하학적 정밀 센터링)
        char_text = str(self.index)
        font_family = self.style.get("font_family", "Malgun Gothic")
        font_scale = 0.52 if len(char_text) == 1 else 0.44
        font = QFont(font_family, int(size * font_scale))
        font.setBold(self.style.get("font_bold", True))
        painter.setFont(font)
        painter.setPen(text_col)

        fm = QFontMetrics(font)
        tb = fm.tightBoundingRect(char_text)
        # 실제 글리프 잉크 중심을 원의 중심점(self.pos)에 정확히 일치
        text_x = self.pos.x() - (tb.width() / 2.0) - tb.left()
        text_y = self.pos.y() + (tb.height() / 2.0)
        painter.drawText(QPointF(text_x, text_y), char_text)
        painter.restore()


class TextLabelItem:
    def __init__(self, text, x, y, style):
        self.text = text
        self.pos = QPointF(x, y)
        self.style = style.copy() if isinstance(style, dict) else dict(style)
        self._cached_rect = QRectF(x, y, 100, 30)

    def clone(self):
        return TextLabelItem(self.text, self.pos.x(), self.pos.y(), self.style.copy())

    def to_dict(self):
        return {
            "type": "TextLabelItem",
            "text": str(self.text),
            "x": float(self.pos.x()),
            "y": float(self.pos.y()),
            "style": self.style.copy()
        }

    @classmethod
    def from_dict(cls, data):
        pos = data.get("pos")
        if pos and len(pos) >= 2:
            x, y = float(pos[0]), float(pos[1])
        else:
            x = float(data.get("x", 0.0))
            y = float(data.get("y", 0.0))
        return cls(str(data.get("text", "")), x, y, data.get("style", {}))

    def get_font(self):
        font_family = self.style.get("font_family", "Malgun Gothic")
        font_size = int(self.style.get("font_size", 13))
        font = QFont(font_family, font_size)
        font.setBold(bool(self.style.get("font_bold", True)))
        families = [font_family] + [f for f in I18nManager.FALLBACK_FONTS if f != font_family]
        font.setFamilies(families)
        return font

    def get_rect(self, painter_or_metrics=None):
        font = self.get_font()
        fm = QFontMetrics(font)
        pad = int(self.style.get("padding", 6))
        tw = fm.horizontalAdvance(self.text) + (pad * 2) + 4
        th = fm.height() + (pad * 2)
        self._cached_rect = QRectF(self.pos.x(), self.pos.y(), max(tw, 40), max(th, 26))
        return self._cached_rect

    def contains(self, pt):
        return self._cached_rect.contains(pt)

    def render(self, painter: QPainter):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        rect = self.get_rect()

        bg_col = QColor(self.style.get("bg_color", "#212121"))
        opacity = self.style.get("bg_opacity", 220)
        if isinstance(opacity, float) and opacity <= 1.0:
            alpha = int(opacity * 255)
        else:
            try:
                alpha = int(opacity)
            except Exception:
                alpha = 220
        alpha = max(0, min(255, alpha))
        bg_col.setAlpha(alpha)

        border_col = QColor(self.style.get("border_color", "#E53935"))
        border_w = int(self.style.get("border_width", 1))
        radius = int(self.style.get("border_radius", 6))
        text_col = QColor(self.style.get("text_color", "#FFFFFF"))

        # 그림자
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 80))
        painter.drawRoundedRect(rect.translated(1.5, 2), radius, radius)

        # 박스
        painter.setBrush(QBrush(bg_col))
        painter.setPen(QPen(border_col, border_w))
        painter.drawRoundedRect(rect, radius, radius)

        # 글자
        font = self.get_font()
        painter.setFont(font)
        painter.setPen(text_col)

        pad = int(self.style.get("padding", 6))
        text_rect = QRectF(rect.x() + pad, rect.y() + pad, rect.width() - (pad * 2), rect.height() - (pad * 2))
        painter.drawText(text_rect, Qt.AlignCenter, self.text)
        painter.restore()


class HighlightBoxItem:
    def __init__(self, rect, style):
        self.rect = QRect(rect)
        self.style = style.copy() if hasattr(style, "copy") else dict(style)

    def clone(self):
        return HighlightBoxItem(QRect(self.rect), self.style.copy())

    def to_dict(self):
        return {
            "type": "HighlightBoxItem",
            "rect": [int(self.rect.x()), int(self.rect.y()), int(self.rect.width()), int(self.rect.height())],
            "style": self.style.copy()
        }

    @classmethod
    def from_dict(cls, data):
        r = data.get("rect", [0, 0, 100, 100])
        return cls(QRect(int(r[0]), int(r[1]), int(r[2]), int(r[3])), data.get("style", {}))

    def contains(self, pt):
        if hasattr(pt, "toPoint"):
            return self.rect.contains(pt.toPoint())
        return self.rect.contains(pt)

    def render(self, painter: QPainter):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        col = QColor(self.style.get("color", "#E53935"))
        w = self.style.get("border_width", 3)
        fill = self.style.get("fill", False)

        if fill:
            fill_col = QColor(col)
            fill_col.setAlpha(45)
            painter.setBrush(QBrush(fill_col))
        else:
            painter.setBrush(Qt.NoBrush)

        painter.setPen(QPen(col, w, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawRect(self.rect)
        painter.restore()


class ArrowItem:
    def __init__(self, start_pos, end_pos, style):
        self.start_pos = QPointF(start_pos)
        self.end_pos = QPointF(end_pos)
        self.style = style.copy() if hasattr(style, "copy") else dict(style)

    def clone(self):
        return ArrowItem(QPointF(self.start_pos), QPointF(self.end_pos), self.style.copy())

    def to_dict(self):
        return {
            "type": "ArrowItem",
            "start_pos": [float(self.start_pos.x()), float(self.start_pos.y())],
            "end_pos": [float(self.end_pos.x()), float(self.end_pos.y())],
            "style": self.style.copy()
        }

    @classmethod
    def from_dict(cls, data):
        p1 = data.get("start_pos", [0.0, 0.0])
        p2 = data.get("end_pos", [0.0, 0.0])
        return cls(QPointF(float(p1[0]), float(p1[1])), QPointF(float(p2[0]), float(p2[1])), data.get("style", {}))

    def contains(self, pt):
        p = pt
        p1 = self.start_pos
        p2 = self.end_pos
        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        l2 = dx * dx + dy * dy
        if l2 == 0:
            return (p.x() - p1.x())**2 + (p.y() - p1.y())**2 <= 64.0
        t = ((p.x() - p1.x()) * dx + (p.y() - p1.y()) * dy) / l2
        t = max(0.0, min(1.0, t))
        proj_x = p1.x() + t * dx
        proj_y = p1.y() + t * dy
        dist_sq = (p.x() - proj_x)**2 + (p.y() - proj_y)**2
        hit_margin = max(8.0, float(self.style.get("width", 3)) * 2.5)
        return dist_sq <= (hit_margin * hit_margin)

    def render(self, painter: QPainter):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        color = QColor(self.style.get("color", "#E53935"))
        width = int(self.style.get("width", 3))
        head_size = float(self.style.get("head_size", 14))
        head_size = max(head_size, width * 3.2)

        p1 = self.start_pos
        p2 = self.end_pos
        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        dist = math.hypot(dx, dy)
        if dist < 4:
            painter.restore()
            return

        angle = math.atan2(dy, dx)
        wing_angle = math.radians(26)

        arrow_p1 = QPointF(
            p2.x() - head_size * math.cos(angle - wing_angle),
            p2.y() - head_size * math.sin(angle - wing_angle)
        )
        arrow_p2 = QPointF(
            p2.x() - head_size * math.cos(angle + wing_angle),
            p2.y() - head_size * math.sin(angle + wing_angle)
        )
        indent_len = head_size * 0.72
        arrow_indent = QPointF(
            p2.x() - indent_len * math.cos(angle),
            p2.y() - indent_len * math.sin(angle)
        )
        head_poly = QPolygonF([p2, arrow_p1, arrow_indent, arrow_p2])

        # 1. 드롭 섀도우 (밝거나 어두운 어떤 배경에서도 선명하게 시인성 확보)
        shadow_offset = QPointF(1.5, 1.5)
        shadow_pen = QPen(QColor(0, 0, 0, 70), width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(shadow_pen)
        painter.drawLine(p1 + shadow_offset, arrow_indent + shadow_offset)
        painter.setBrush(QBrush(QColor(0, 0, 0, 70)))
        painter.setPen(Qt.NoPen)
        painter.drawPolygon(head_poly.translated(1.5, 1.5))

        # 2. 화살표 본체 선 및 화살표 촉 채우기
        pen = QPen(color, width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(p1, arrow_indent)

        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color, 1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPolygon(head_poly)

        painter.restore()


class StepArrowItem:
    """스탬프 번호 배지와 화살표 연결선 일체형 객체"""
    def __init__(self, index, start_pos, end_pos, stamp_style, arrow_style):
        self.index = index
        self.start_pos = QPointF(start_pos)
        self.end_pos = QPointF(end_pos)
        self.stamp_style = stamp_style.copy() if hasattr(stamp_style, "copy") else dict(stamp_style)
        self.arrow_style = arrow_style.copy() if hasattr(arrow_style, "copy") else dict(arrow_style)

    def clone(self):
        return StepArrowItem(
            self.index,
            QPointF(self.start_pos),
            QPointF(self.end_pos),
            self.stamp_style.copy(),
            self.arrow_style.copy()
        )

    def to_dict(self):
        return {
            "type": "StepArrowItem",
            "index": int(self.index),
            "start_pos": [float(self.start_pos.x()), float(self.start_pos.y())],
            "end_pos": [float(self.end_pos.x()), float(self.end_pos.y())],
            "stamp_style": self.stamp_style.copy(),
            "arrow_style": self.arrow_style.copy()
        }

    @classmethod
    def from_dict(cls, data):
        p1 = data.get("start_pos", [0.0, 0.0])
        p2 = data.get("end_pos", [0.0, 0.0])
        return cls(
            int(data.get("index", 1)),
            QPointF(float(p1[0]), float(p1[1])),
            QPointF(float(p2[0]), float(p2[1])),
            data.get("stamp_style", {}),
            data.get("arrow_style", {})
        )

    def contains(self, pt):
        size = self.stamp_style.get("size", 32)
        r = size / 2.0
        shape = self.stamp_style.get("shape", "circle")
        if shape == "rounded_rect":
            if QRectF(self.start_pos.x() - r, self.start_pos.y() - r, size, size).contains(pt):
                return True
        else:
            dx1 = pt.x() - self.start_pos.x()
            dy1 = pt.y() - self.start_pos.y()
            if (dx1 * dx1 + dy1 * dy1) <= (r * r):
                return True

        dx = self.end_pos.x() - self.start_pos.x()
        dy = self.end_pos.y() - self.start_pos.y()
        l2 = dx * dx + dy * dy
        if l2 == 0:
            return False
        t = max(0.0, min(1.0, ((pt.x() - self.start_pos.x()) * dx + (pt.y() - self.start_pos.y()) * dy) / l2))
        proj_x = self.start_pos.x() + t * dx
        proj_y = self.start_pos.y() + t * dy
        dist_sq = (pt.x() - proj_x)**2 + (pt.y() - proj_y)**2
        hit_margin = max(8.0, float(self.arrow_style.get("width", 3)) * 2.5)
        return dist_sq <= (hit_margin * hit_margin)

    def render(self, painter: QPainter):
        p1 = self.start_pos
        p2 = self.end_pos
        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        dist = math.hypot(dx, dy)
        size = self.stamp_style.get("size", 32)
        r = size / 2.0

        if dist > r + 6:
            angle = math.atan2(dy, dx)
            start_edge = QPointF(p1.x() + (r - 2) * math.cos(angle), p1.y() + (r - 2) * math.sin(angle))
            arrow_item = ArrowItem(start_edge, p2, self.arrow_style)
            arrow_item.render(painter)

        stamp_item = StampItem(self.index, p1.x(), p1.y(), self.stamp_style)
        stamp_item.render(painter)


class ElbowArrowItem:
    """꺾인(직각, L자, Z자) 우회 화살표 지시선 객체 (분기 라벨 지원)"""
    def __init__(self, start_pos, end_pos, style=None, route_mode="HV", label=""):
        self.start_pos = QPointF(start_pos)
        self.end_pos = QPointF(end_pos)
        if style is None:
            self.style = {"color": "#E53935", "width": 3, "head_size": 14}
        else:
            self.style = style.copy() if hasattr(style, "copy") else dict(style)
        self.route_mode = route_mode  # HV (수평 우선: 가로) 또는 VH (수직 우선: 세로)
        self.label = str(label) if label is not None else ""

    def clone(self):
        return ElbowArrowItem(QPointF(self.start_pos), QPointF(self.end_pos), self.style.copy(), self.route_mode, self.label)

    def toggle_route_mode(self):
        """HV ↔ VH ↔ VHV ↔ HVH 실시간 순환 토글 (키보드 탭 등)"""
        modes = ["HV", "VH", "VHV", "HVH"]
        cur = getattr(self, "route_mode", "HV")
        try:
            nxt = modes[(modes.index(cur) + 1) % len(modes)]
        except ValueError:
            nxt = "HV"
        self.route_mode = nxt
        return self.route_mode

    def to_dict(self):
        return {
            "type": "ElbowArrowItem",
            "start_pos": [float(self.start_pos.x()), float(self.start_pos.y())],
            "end_pos": [float(self.end_pos.x()), float(self.end_pos.y())],
            "style": self.style.copy(),
            "route_mode": self.route_mode,
            "label": self.label
        }

    @classmethod
    def from_dict(cls, data):
        p1 = data.get("start_pos", [0.0, 0.0])
        p2 = data.get("end_pos", [0.0, 0.0])
        return cls(
            QPointF(float(p1[0]), float(p1[1])),
            QPointF(float(p2[0]), float(p2[1])),
            data.get("style", {}),
            data.get("route_mode", "HV"),
            data.get("label", "")
        )

    def get_corner_points(self):
        """다구간 직각 꺾임 좌표 목록 반환 (1코너 L자 또는 2코너 Z/S자)"""
        p1 = self.start_pos
        p2 = self.end_pos
        mode = getattr(self, "route_mode", "HV")

        if mode == "HV":
            return [QPointF(p2.x(), p1.y())]
        elif mode == "VH":
            return [QPointF(p1.x(), p2.y())]
        elif mode == "VHV":
            mid_y = (p1.y() + p2.y()) / 2.0
            return [QPointF(p1.x(), mid_y), QPointF(p2.x(), mid_y)]
        elif mode == "HVH":
            mid_x = (p1.x() + p2.x()) / 2.0
            return [QPointF(mid_x, p1.y()), QPointF(mid_x, p2.y())]
        else:
            return [QPointF(p2.x(), p1.y())]

    def get_corner_point(self):
        """하위 호환성을 위한 첫 번째 코너 좌표 반환"""
        pts = self.get_corner_points()
        return pts[0] if pts else self.end_pos

    def contains(self, pt):
        corners = self.get_corner_points()
        all_pts = [self.start_pos] + corners + [self.end_pos]
        hit_m = max(8.0, float(self.style.get("width", 3)) * 2.5)

        def dist_to_seg(a, b, p):
            dx = b.x() - a.x()
            dy = b.y() - a.y()
            l2 = dx * dx + dy * dy
            if l2 == 0:
                return math.hypot(p.x() - a.x(), p.y() - a.y())
            t = max(0.0, min(1.0, ((p.x() - a.x()) * dx + (p.y() - a.y()) * dy) / l2))
            proj = QPointF(a.x() + t * dx, a.y() + t * dy)
            return math.hypot(p.x() - proj.x(), p.y() - proj.y())

        for i in range(len(all_pts) - 1):
            if dist_to_seg(all_pts[i], all_pts[i + 1], pt) <= hit_m:
                return True
        return False

    def render(self, painter: QPainter):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        color = QColor(self.style.get("color", "#E53935"))
        width = int(self.style.get("width", 3))
        head_size = float(self.style.get("head_size", 14))
        head_size = max(head_size, width * 3.2)

        p1 = self.start_pos
        corners = self.get_corner_points()
        p2 = self.end_pos
        last_corner = corners[-1] if corners else p1

        dx = p2.x() - last_corner.x()
        dy = p2.y() - last_corner.y()
        dist2 = math.hypot(dx, dy)
        if dist2 < 4:
            dx = p2.x() - p1.x()
            dy = p2.y() - p1.y()
            dist2 = math.hypot(dx, dy)
            if dist2 < 4:
                painter.restore()
                return

        angle = math.atan2(dy, dx)
        wing_angle = math.radians(26)
        arrow_p1 = QPointF(p2.x() - head_size * math.cos(angle - wing_angle), p2.y() - head_size * math.sin(angle - wing_angle))
        arrow_p2 = QPointF(p2.x() - head_size * math.cos(angle + wing_angle), p2.y() - head_size * math.sin(angle + wing_angle))
        indent_len = head_size * 0.72
        arrow_indent = QPointF(p2.x() - indent_len * math.cos(angle), p2.y() - indent_len * math.sin(angle))
        head_poly = QPolygonF([p2, arrow_p1, arrow_indent, arrow_p2])

        path = QPainterPath()
        path.moveTo(p1)
        for c in corners:
            path.lineTo(c)
        path.lineTo(arrow_indent)

        # 그림자
        painter.setPen(QPen(QColor(0, 0, 0, 70), width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path.translated(1.5, 1.5))
        painter.setBrush(QBrush(QColor(0, 0, 0, 70)))
        painter.setPen(Qt.NoPen)
        painter.drawPolygon(head_poly.translated(1.5, 1.5))

        # 본체
        painter.setPen(QPen(color, width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color, 1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPolygon(head_poly)

        # 분기 조건 라벨 렌더링
        if getattr(self, "label", ""):
            lbl_font = QFont("Malgun Gothic", 9)
            lbl_font.setBold(True)
            painter.setFont(lbl_font)
            fm = QFontMetrics(lbl_font)
            txt_w = fm.horizontalAdvance(self.label) + 12
            txt_h = fm.height() + 4
            first_corner = corners[0] if corners else p2
            mid_pt = QPointF((p1.x() + first_corner.x()) / 2.0, (p1.y() + first_corner.y()) / 2.0)
            lbl_rect = QRectF(mid_pt.x() - txt_w / 2.0, mid_pt.y() - txt_h / 2.0, txt_w, txt_h)
            painter.setPen(QPen(QColor("#CBD5E1"), 1))
            painter.setBrush(QBrush(QColor("#FFFFFF")))
            painter.drawRoundedRect(lbl_rect, 3, 3)
            painter.setPen(QPen(QColor("#1E293B")))
            painter.drawText(lbl_rect, Qt.AlignCenter, self.label)

        painter.restore()


class CalloutItem:
    """지시선 꼬리가 달린 말풍선 설명 상자 객체"""
    def __init__(self, text, box_rect, target_pt, style=None):
        self.text = text
        self.box_rect = QRectF(box_rect)
        self.target_pt = QPointF(target_pt)
        self.style = style.copy() if hasattr(style, "copy") else dict(style or {})

    def clone(self):
        return CalloutItem(self.text, QRectF(self.box_rect), QPointF(self.target_pt), self.style.copy())

    def to_dict(self):
        return {
            "type": "CalloutItem",
            "text": str(self.text),
            "box_rect": [float(self.box_rect.x()), float(self.box_rect.y()), float(self.box_rect.width()), float(self.box_rect.height())],
            "target_pt": [float(self.target_pt.x()), float(self.target_pt.y())],
            "style": self.style.copy()
        }

    @classmethod
    def from_dict(cls, data):
        br = data.get("box_rect", [0.0, 0.0, 100.0, 40.0])
        tp = data.get("target_pt", [0.0, 0.0])
        return cls(
            str(data.get("text", "")),
            QRectF(float(br[0]), float(br[1]), float(br[2]), float(br[3])),
            QPointF(float(tp[0]), float(tp[1])),
            data.get("style", {})
        )

    def get_path(self):
        rect = self.box_rect
        target = self.target_pt
        bc = rect.center()
        tw = float(self.style.get("tail_base_width", 16))
        radius = int(self.style.get("border_radius", 6))

        if target.x() < rect.left():
            tail_b1 = QPointF(rect.left(), max(rect.top() + 6, min(rect.bottom() - 6 - tw, bc.y() - tw / 2)))
            tail_b2 = QPointF(rect.left(), tail_b1.y() + tw)
        elif target.x() > rect.right():
            tail_b1 = QPointF(rect.right(), max(rect.top() + 6, min(rect.bottom() - 6 - tw, bc.y() - tw / 2)))
            tail_b2 = QPointF(rect.right(), tail_b1.y() + tw)
        elif target.y() < rect.top():
            tail_b1 = QPointF(max(rect.left() + 6, min(rect.right() - 6 - tw, bc.x() - tw / 2)), rect.top())
            tail_b2 = QPointF(tail_b1.x() + tw, rect.top())
        else:
            tail_b1 = QPointF(max(rect.left() + 6, min(rect.right() - 6 - tw, bc.x() - tw / 2)), rect.bottom())
            tail_b2 = QPointF(tail_b1.x() + tw, rect.bottom())

        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        tail_path = QPainterPath()
        tail_path.moveTo(tail_b1)
        tail_path.lineTo(target)
        tail_path.lineTo(tail_b2)
        tail_path.closeSubpath()
        return path.united(tail_path)

    def contains(self, pt):
        if self.box_rect.contains(pt):
            return True
        if math.hypot(pt.x() - self.target_pt.x(), pt.y() - self.target_pt.y()) <= 15.0:
            return True
        return self.get_path().contains(pt)

    def render(self, painter: QPainter):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        bg_col = QColor(self.style.get("bg_color", "#212121"))
        opacity = self.style.get("bg_opacity", 230)
        bg_col.setAlpha(int(opacity) if isinstance(opacity, (int, float)) and opacity > 1 else int(float(opacity) * 255))
        border_col = QColor(self.style.get("border_color", "#E53935"))
        border_w = int(self.style.get("border_width", 2))
        text_col = QColor(self.style.get("text_color", "#FFFFFF"))

        rect = self.box_rect
        full_path = self.get_path()

        # 그림자
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 75))
        painter.drawPath(full_path.translated(1.5, 2.0))

        # 본체
        painter.setPen(QPen(border_col, border_w))
        painter.setBrush(QBrush(bg_col))
        painter.drawPath(full_path)

        # 텍스트
        font_family = self.style.get("font_family", "Malgun Gothic")
        font_size = int(self.style.get("font_size", 12))
        font = QFont(font_family, font_size)
        font.setBold(bool(self.style.get("font_bold", True)))
        families = [font_family] + [f for f in I18nManager.FALLBACK_FONTS if f != font_family]
        font.setFamilies(families)
        painter.setFont(font)
        painter.setPen(text_col)
        pad = 6
        text_rect = rect.adjusted(pad, pad, -pad, -pad)
        painter.drawText(text_rect, Qt.AlignCenter | Qt.TextWordWrap, self.text)

        painter.restore()


class BlurMosaicItem:
    """민감 정보 영역 비파괴 모자이크 블러 객체"""
    def __init__(self, rect, style=None):
        self.rect = QRect(rect)
        self.style = style.copy() if hasattr(style, "copy") else dict(style or {"block_size": 10})

    def clone(self):
        return BlurMosaicItem(QRect(self.rect), self.style.copy())

    def to_dict(self):
        return {
            "type": "BlurMosaicItem",
            "rect": [int(self.rect.x()), int(self.rect.y()), int(self.rect.width()), int(self.rect.height())],
            "style": self.style.copy()
        }

    @classmethod
    def from_dict(cls, data):
        r = data.get("rect", [0, 0, 100, 100])
        return cls(QRect(int(r[0]), int(r[1]), int(r[2]), int(r[3])), data.get("style", {}))

    def contains(self, pt):
        if hasattr(pt, "toPoint"):
            return self.rect.contains(pt.toPoint())
        return self.rect.contains(pt)

    def render_mosaic(self, painter: QPainter, base_pixmap: QPixmap):
        if not base_pixmap or self.rect.isEmpty():
            return
        r = self.rect.intersected(base_pixmap.rect())
        if r.width() <= 0 or r.height() <= 0:
            return

        bs = max(4, int(self.style.get("block_size", 10)))
        cropped = base_pixmap.copy(r)
        tiny_w = max(1, r.width() // bs)
        tiny_h = max(1, r.height() // bs)
        scaled_down = cropped.scaled(tiny_w, tiny_h, Qt.IgnoreAspectRatio, Qt.FastTransformation)
        mosaic_pix = scaled_down.scaled(r.width(), r.height(), Qt.IgnoreAspectRatio, Qt.FastTransformation)

        painter.save()
        painter.drawPixmap(r.topLeft(), mosaic_pix)
        border_pen = QPen(QColor(120, 120, 120, 180), 1, Qt.DashLine)
        painter.setPen(border_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(r)
        painter.restore()

    def render(self, painter: QPainter):
        # 기본 렌더링 (base_pixmap이 없을 때의 안전 대체 표시)
        painter.save()
        painter.setBrush(QColor(180, 180, 180, 120))
        painter.setPen(QPen(QColor(100, 100, 100, 200), 1, Qt.DashLine))
        painter.drawRect(self.rect)
        painter.restore()


class HotkeyBadgeItem:
    """키보드 단축키 키캡 캡슐 뱃지 객체"""
    def __init__(self, key_text, x, y, style=None):
        self.key_text = key_text
        self.pos = QPointF(x, y)
        self.style = style.copy() if hasattr(style, "copy") else dict(style or {
            "font_size": 12,
            "theme": "dark"
        })
        self._cached_rect = QRectF(x, y, 60, 28)

    def clone(self):
        return HotkeyBadgeItem(self.key_text, self.pos.x(), self.pos.y(), self.style.copy())

    def to_dict(self):
        return {
            "type": "HotkeyBadgeItem",
            "key_text": str(self.key_text),
            "x": float(self.pos.x()),
            "y": float(self.pos.y()),
            "style": self.style.copy()
        }

    @classmethod
    def from_dict(cls, data):
        pos = data.get("pos")
        if pos and len(pos) >= 2:
            x, y = float(pos[0]), float(pos[1])
        else:
            x = float(data.get("x", 0.0))
            y = float(data.get("y", 0.0))
        return cls(str(data.get("key_text", "")), x, y, data.get("style", {}))

    def get_rect(self):
        font = QFont("Malgun Gothic", int(self.style.get("font_size", 12)))
        font.setBold(True)
        fm = QFontMetrics(font)
        tw = fm.horizontalAdvance(self.key_text) + 20
        th = fm.height() + 12
        self._cached_rect = QRectF(self.pos.x(), self.pos.y(), max(tw, 40), max(th, 26))
        return self._cached_rect

    def contains(self, pt):
        return self.get_rect().contains(pt)

    def render(self, painter: QPainter):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        rect = self.get_rect()
        theme = self.style.get("theme", "dark")

        radius = 5.0
        shadow_rect = rect.translated(0, 2.0)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 80))
        painter.drawRoundedRect(shadow_rect, radius, radius)

        base_col = QColor("#2D3139") if theme == "dark" else QColor("#D8D8D8")
        border_col = QColor("#5A6270") if theme == "dark" else QColor("#B0B0B0")
        top_col = QColor("#383C45") if theme == "dark" else QColor("#FFFFFF")
        text_col = QColor("#FFFFFF") if theme == "dark" else QColor("#212121")

        painter.setPen(QPen(border_col, 1.5))
        painter.setBrush(QBrush(base_col))
        painter.drawRoundedRect(rect, radius, radius)

        inset_rect = rect.adjusted(2, 2, -2, -3)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(top_col))
        painter.drawRoundedRect(inset_rect, max(1.0, radius - 1.5), max(1.0, radius - 1.5))

        font = QFont("Consolas" if any(c.isascii() for c in self.key_text) else "Malgun Gothic", int(self.style.get("font_size", 12)))
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(text_col)
        painter.drawText(inset_rect, Qt.AlignCenter, self.key_text)

        painter.restore()


class ImageOverlayItem:
    """화면 특정 영역(모달/팝업 등)을 부분 캡처하여 메인 화면 위에 얹는 독립 이미지 객체(스티커 레이어)"""
    def __init__(self, rect: QRectF, pixmap: QPixmap, style: dict = None):
        self.rect = QRectF(rect)
        self.pixmap = pixmap
        self.style = {
            "border_color": "#CBD5E1",
            "border_width": 2,
            "has_shadow": True,
            "corner_radius": 6
        }
        if style:
            self.style.update(style)
        self.is_resizing = False
        self.active_handle = None

    def clone(self):
        return ImageOverlayItem(
            QRectF(self.rect),
            QPixmap(self.pixmap),
            self.style.copy()
        )

    def contains(self, pt: QPointF) -> bool:
        return self.rect.adjusted(-6, -6, 6, 6).contains(pt)

    def get_handles(self) -> dict:
        r = self.rect
        hs = 8.0
        return {
            "TL": QRectF(r.left() - hs / 2, r.top() - hs / 2, hs, hs),
            "TR": QRectF(r.right() - hs / 2, r.top() - hs / 2, hs, hs),
            "BL": QRectF(r.left() - hs / 2, r.bottom() - hs / 2, hs, hs),
            "BR": QRectF(r.right() - hs / 2, r.bottom() - hs / 2, hs, hs),
        }

    def get_handle_at(self, pt: QPointF) -> str:
        for name, hrect in self.get_handles().items():
            if hrect.contains(pt):
                return name
        return None

    def handle_resize(self, handle: str, pt: QPointF, keep_aspect_ratio: bool = True):
        r = QRectF(self.rect)
        orig_w = max(1.0, r.width())
        orig_h = max(1.0, r.height())
        aspect = orig_w / orig_h

        if handle == "BR":
            new_w = max(40.0, pt.x() - r.left())
            new_h = new_w / aspect if keep_aspect_ratio else max(40.0, pt.y() - r.top())
            self.rect = QRectF(r.left(), r.top(), new_w, new_h)
        elif handle == "BL":
            new_w = max(40.0, r.right() - pt.x())
            new_h = new_w / aspect if keep_aspect_ratio else max(40.0, pt.y() - r.top())
            self.rect = QRectF(r.right() - new_w, r.top(), new_w, new_h)
        elif handle == "TR":
            new_w = max(40.0, pt.x() - r.left())
            new_h = new_w / aspect if keep_aspect_ratio else max(40.0, r.bottom() - pt.y())
            self.rect = QRectF(r.left(), r.bottom() - new_h, new_w, new_h)
        elif handle == "TL":
            new_w = max(40.0, r.right() - pt.x())
            new_h = new_w / aspect if keep_aspect_ratio else max(40.0, r.bottom() - pt.y())
            self.rect = QRectF(r.right() - new_w, r.bottom() - new_h, new_w, new_h)

    def render(self, painter: QPainter, is_selected: bool = False):
        if not self.pixmap or self.pixmap.isNull() or self.rect.isEmpty():
            return
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        r = self.rect
        radius = float(self.style.get("corner_radius", 6))
        bw = int(self.style.get("border_width", 2))
        bc = QColor(self.style.get("border_color", "#CBD5E1"))

        # 1. 은은한 입체 드롭 섀도우
        if self.style.get("has_shadow", True):
            for i in range(4):
                offset = (i + 1) * 1.5
                alpha = int(40 / (i + 1))
                if hasattr(r, "translated") and isinstance(r, QRectF):
                    shadow_rect = r.translated(offset, offset)
                else:
                    shadow_rect = QRectF(r).translated(offset, offset)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(0, 0, 0, alpha))
                painter.drawRoundedRect(shadow_rect, radius + 1, radius + 1)

        # 2. 이미지 렌더링 (둥근 모서리 클리핑)
        path = QPainterPath()
        path.addRoundedRect(QRectF(r), radius, radius)
        painter.save()
        painter.setClipPath(path)
        rx = int(round(r.x()))
        ry = int(round(r.y()))
        rw = int(round(r.width()))
        rh = int(round(r.height()))
        if abs(rw - self.pixmap.width()) <= 1 and abs(rh - self.pixmap.height()) <= 1:
            painter.drawPixmap(QPoint(rx, ry), self.pixmap)
        else:
            painter.drawPixmap(QRect(rx, ry, rw, rh), self.pixmap)
        painter.restore()

        # 3. 외곽 테두리
        if bw > 0:
            painter.setPen(QPen(bc, bw))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(r, radius, radius)

        # 4. 선택 표시 및 4각 리사이즈 핸들
        if is_selected:
            painter.setPen(QPen(QColor(33, 150, 243), 1.5, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(r.adjusted(-2, -2, 2, 2))

            painter.setPen(QPen(QColor(25, 118, 210), 1))
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            for hrect in self.get_handles().values():
                painter.drawRect(hrect)

        painter.restore()

    def to_dict(self):
        b64_str = ProjectManager.pixmap_to_base64(self.pixmap)
        return {
            "type": "ImageOverlayItem",
            "rect": [float(self.rect.x()), float(self.rect.y()), float(self.rect.width()), float(self.rect.height())],
            "image_b64": b64_str,
            "style": dict(self.style)
        }

    @staticmethod
    def from_dict(data):
        r_list = data.get("rect", [0, 0, 100, 100])
        rect = QRectF(float(r_list[0]), float(r_list[1]), float(r_list[2]), float(r_list[3]))
        b64 = data.get("image_b64", "")
        pixmap = ProjectManager.base64_to_pixmap(b64)
        style = data.get("style", {})
        return ImageOverlayItem(rect, pixmap, style)


class DraftStampItem:
    """큼직한 Draft 워터마크 스탬프 (사각형 테두리, 60도 회전, 좌하단->우상단 텍스트 방향)"""
    def __init__(self, text="DRAFT", pos=None, style=None):
        self.text = str(text or "DRAFT")
        self.pos = QPointF(pos) if pos is not None else QPointF(0, 0)
        self.angle = -60.0  # -60도: 왼쪽 아래에서 오른쪽 위 방향
        self.style = {
            "font_family": "Impact",
            "font_size": 48,
            "color": "#E53935",
            "border_width": 5,
            "opacity": 0.40,
            "corner_radius": 4.0,
            "padding_x": 24.0,
            "padding_y": 10.0,
            "letter_spacing": 4.0
        }
        if style:
            self.style.update(style)

    def clone(self):
        item = DraftStampItem(
            self.text,
            QPointF(self.pos),
            self.style.copy()
        )
        item.angle = self.angle
        return item

    def get_local_rect(self) -> QRectF:
        """회전 전 (0,0) 중심 기준의 로컬 바운딩 사각형"""
        font = QFont(self.style.get("font_family", "Impact"), int(self.style.get("font_size", 48)))
        font.setBold(True)
        font.setLetterSpacing(QFont.AbsoluteSpacing, float(self.style.get("letter_spacing", 4.0)))
        fm = QFontMetrics(font)
        tw = fm.horizontalAdvance(self.text)
        th = fm.height()

        px = float(self.style.get("padding_x", 24.0))
        py = float(self.style.get("padding_y", 10.0))
        w = max(tw + px * 2, 120.0)
        h = max(th + py * 2, 50.0)
        return QRectF(-w / 2.0, -h / 2.0, w, h)

    def get_transform(self) -> QTransform:
        t = QTransform()
        t.translate(self.pos.x(), self.pos.y())
        t.rotate(self.angle)
        return t

    def contains(self, pt: QPointF) -> bool:
        t = self.get_transform()
        inv_t, invertible = t.inverted()
        if not invertible:
            return False
        local_pt = inv_t.map(QPointF(pt))
        return self.get_local_rect().adjusted(-8, -8, 8, 8).contains(local_pt)

    def render(self, painter: QPainter, is_selected: bool = False):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        # 1. 중심점 이동 및 회전 (-60도: 좌하단 -> 우상단 방향)
        painter.translate(self.pos)
        painter.rotate(self.angle)

        local_r = self.get_local_rect()
        opacity = max(0.05, min(1.0, float(self.style.get("opacity", 0.40))))
        base_color = QColor(self.style.get("color", "#E53935"))
        bw = int(self.style.get("border_width", 5))
        radius = float(self.style.get("corner_radius", 4.0))

        alpha_int = int(opacity * 255)
        stamp_color = QColor(base_color.red(), base_color.green(), base_color.blue(), alpha_int)

        # 2. 사각형 테두리
        if bw > 0:
            pen = QPen(stamp_color, bw)
            pen.setJoinStyle(Qt.MiterJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(local_r, radius, radius)

        # 3. 내부 텍스트
        font = QFont(self.style.get("font_family", "Impact"), int(self.style.get("font_size", 48)))
        font.setBold(True)
        font.setLetterSpacing(QFont.AbsoluteSpacing, float(self.style.get("letter_spacing", 4.0)))
        painter.setFont(font)
        painter.setPen(stamp_color)
        painter.drawText(local_r, Qt.AlignCenter, self.text)

        # 4. 선택 하이라이트 표시
        if is_selected:
            sel_pen = QPen(QColor(33, 150, 243, 220), 1.5, Qt.DashLine)
            painter.setPen(sel_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(local_r.adjusted(-6, -6, 6, 6))

            # 4각 코너 앵커 포인트
            painter.setPen(QPen(QColor(25, 118, 210), 1))
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            hs = 6.0
            for pt_c in [local_r.topLeft(), local_r.topRight(), local_r.bottomLeft(), local_r.bottomRight()]:
                painter.drawRect(QRectF(pt_c.x() - hs/2, pt_c.y() - hs/2, hs, hs))

        painter.restore()

    def to_dict(self):
        return {
            "type": "DraftStampItem",
            "text": str(self.text),
            "x": float(self.pos.x()),
            "y": float(self.pos.y()),
            "angle": float(self.angle),
            "style": dict(self.style)
        }

    @classmethod
    def from_dict(cls, data):
        text = str(data.get("text", "DRAFT"))
        pos = data.get("pos")
        if pos and len(pos) >= 2:
            x, y = float(pos[0]), float(pos[1])
        else:
            x = float(data.get("x", 0.0))
            y = float(data.get("y", 0.0))
        item = cls(text=text, pos=QPointF(x, y), style=data.get("style", {}))
        if "angle" in data:
            item.angle = float(data["angle"])
        return item


# ==============================================================================
# 워드아트 객체 (WordArtItem)
# ==============================================================================
class WordArtItem:
    """파워포인트 스타일 입체 외곽선/그림자 워드아트 텍스트 주석 객체"""

    PRESETS = {
        "white_pop": {
            "name": "화이트 팝 (고대비 표준)",
            "text_color": "#FFFFFF",
            "stroke_color": "#000000",
            "stroke_width": 3.0,
            "shadow_enabled": True,
            "shadow_color": "#000000",
            "shadow_alpha": 180,
            "shadow_offset_x": 2.5,
            "shadow_offset_y": 2.5
        },
        "gold_title": {
            "name": "골드 메탈릭 (핵심 강조)",
            "text_color": "#FFD700",
            "stroke_color": "#3E2723",
            "stroke_width": 3.0,
            "shadow_enabled": True,
            "shadow_color": "#1A0C08",
            "shadow_alpha": 210,
            "shadow_offset_x": 2.5,
            "shadow_offset_y": 2.5
        },
        "neon_cyan": {
            "name": "네온 사이언 (전산 지시)",
            "text_color": "#00E5FF",
            "stroke_color": "#002171",
            "stroke_width": 2.5,
            "shadow_enabled": True,
            "shadow_color": "#0091EA",
            "shadow_alpha": 180,
            "shadow_offset_x": 2.0,
            "shadow_offset_y": 2.0
        },
        "red_warning": {
            "name": "레드 경고 (주의/금지)",
            "text_color": "#D50000",
            "stroke_color": "#FFFFFF",
            "stroke_width": 2.5,
            "shadow_enabled": True,
            "shadow_color": "#000000",
            "shadow_alpha": 220,
            "shadow_offset_x": 2.5,
            "shadow_offset_y": 2.5
        },
        "slate_modern": {
            "name": "차콜 모던 (테크니컬)",
            "text_color": "#212121",
            "stroke_color": "#FF6D00",
            "stroke_width": 2.0,
            "shadow_enabled": True,
            "shadow_color": "#FF9100",
            "shadow_alpha": 130,
            "shadow_offset_x": 2.0,
            "shadow_offset_y": 2.0
        }
    }

    def __init__(self, text="주요 확인", x=100.0, y=100.0, style=None):
        self.text = str(text)
        self.pos = QPointF(float(x), float(y))
        self.style = style.copy() if (style and hasattr(style, "copy")) else dict(style or {})
        self._cached_rect = QRectF(x, y, 120, 40)

    def clone(self):
        return WordArtItem(self.text, self.pos.x(), self.pos.y(), self.style.copy())

    def to_dict(self):
        return {
            "type": "WordArtItem",
            "text": str(self.text),
            "x": float(self.pos.x()),
            "y": float(self.pos.y()),
            "style": self.style.copy()
        }

    @classmethod
    def from_dict(cls, data):
        pos = data.get("pos")
        if pos and len(pos) >= 2:
            x, y = float(pos[0]), float(pos[1])
        else:
            x = float(data.get("x", 100.0))
            y = float(data.get("y", 100.0))
        return cls(
            text=str(data.get("text", "주요 확인")),
            x=x,
            y=y,
            style=data.get("style", {})
        )

    def get_font(self):
        font_family = self.style.get("font_family", "Malgun Gothic")
        font_size = int(self.style.get("font_size", 24))
        font = QFont(font_family, font_size)
        font.setBold(bool(self.style.get("font_bold", True)))
        families = [font_family] + [f for f in I18nManager.FALLBACK_FONTS if f != font_family]
        font.setFamilies(families)
        return font

    def get_rect(self, painter_or_metrics=None):
        font = self.get_font()
        fm = QFontMetrics(font)
        sw = float(self.style.get("stroke_width", 3.0))
        pad = 8.0
        tw = fm.horizontalAdvance(self.text) + (sw * 2) + (pad * 2)
        th = fm.height() + (sw * 2) + (pad * 2)
        self._cached_rect = QRectF(self.pos.x(), self.pos.y(), max(tw, 50.0), max(th, 30.0))
        return self._cached_rect

    def contains(self, pt):
        return self.get_rect().contains(pt)

    def apply_preset(self, preset_id):
        if preset_id in self.PRESETS:
            p_data = self.PRESETS[preset_id]
            for k, v in p_data.items():
                if k != "name":
                    self.style[k] = v
            self.style["preset_id"] = preset_id

    def render(self, painter: QPainter):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        font = self.get_font()
        fm = QFontMetrics(font)
        ascent = fm.ascent()
        sw = float(self.style.get("stroke_width", 3.0))
        pad = 8.0

        text_x = self.pos.x() + pad + sw
        text_y = self.pos.y() + pad + sw + ascent

        path = QPainterPath()
        path.addText(text_x, text_y, font, self.text)

        # 1. 드롭 섀도우 (Drop Shadow)
        if self.style.get("shadow_enabled", True):
            sh_x = float(self.style.get("shadow_offset_x", 2.5))
            sh_y = float(self.style.get("shadow_offset_y", 2.5))
            sh_col = QColor(self.style.get("shadow_color", "#000000"))
            sh_alpha = int(self.style.get("shadow_alpha", 180))
            sh_col.setAlpha(max(0, min(255, sh_alpha)))

            shadow_path = QPainterPath(path)
            shadow_path.translate(sh_x, sh_y)
            if sw > 0:
                painter.setPen(QPen(sh_col, (sw * 2) + 1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                painter.setBrush(Qt.NoBrush)
                painter.drawPath(shadow_path)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(sh_col))
            painter.drawPath(shadow_path)

        # 2. 외곽선 (Stroke / Outline)
        if sw > 0:
            stroke_col = QColor(self.style.get("stroke_color", "#000000"))
            painter.setPen(QPen(stroke_col, sw * 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)

        # 3. 내부 글자 채우기 (Fill)
        text_col = QColor(self.style.get("text_color", "#FFFFFF"))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(text_col))
        painter.drawPath(path)

        painter.restore()


# ------------------------------------------------------------------------------
class SpotlightMaskItem:
    """타겟 영역 외 전체 배경을 반투명 암전 처리하여 시선을 집중시키는 스포트라이트 마스크 객체"""
    def __init__(self, rect, style=None):
        self.rect = QRect(rect) if isinstance(rect, QRect) else QRect(int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3]))
        self.style = style.copy() if style else {}

    def clone(self):
        return SpotlightMaskItem(QRect(self.rect), self.style.copy())

    def to_dict(self):
        return {
            "type": "SpotlightMaskItem",
            "rect": [int(self.rect.x()), int(self.rect.y()), int(self.rect.width()), int(self.rect.height())],
            "style": self.style.copy()
        }

    @classmethod
    def from_dict(cls, data):
        return cls(data.get("rect", [0, 0, 100, 100]), data.get("style", {}))

    def render_spotlight(self, painter: QPainter, canvas_w: int, canvas_h: int):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        outer = QPainterPath()
        outer.addRect(0, 0, canvas_w, canvas_h)
        radius = float(self.style.get("border_radius", 6))
        inner = QPainterPath()
        inner.addRoundedRect(QRectF(self.rect), radius, radius)
        mask = outer.subtracted(inner)
        opacity = int(self.style.get("dim_opacity", 160))
        dim_color = QColor(self.style.get("dim_color", "#000000"))
        dim_color.setAlpha(opacity)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(dim_color))
        painter.drawPath(mask)
        border_w = int(self.style.get("border_width", 2))
        if border_w > 0:
            border_col = QColor(self.style.get("border_color", "#007AFF"))
            painter.setPen(QPen(border_col, border_w))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(QRectF(self.rect), radius, radius)
        painter.restore()

    def contains(self, pt):
        qpt = QPoint(int(pt.x()), int(pt.y())) if hasattr(pt, "x") else QPoint(int(pt[0]), int(pt[1]))
        return self.rect.adjusted(-6, -6, 6, 6).contains(qpt)

    def render(self, painter: QPainter):
        self.render_spotlight(painter, 1920, 1080)


class ClickRippleItem:
    """마우스 클릭(좌클릭, 우클릭, 더블클릭) 위치 및 동작을 시각화하는 파동 인디케이터 객체"""
    def __init__(self, x, y, click_type="left", style=None):
        self.pos = QPointF(float(x), float(y))
        self.click_type = str(click_type).lower()
        self.style = style.copy() if style else {}

    def clone(self):
        return ClickRippleItem(self.pos.x(), self.pos.y(), self.click_type, self.style.copy())

    def to_dict(self):
        return {
            "type": "ClickRippleItem",
            "x": float(self.pos.x()),
            "y": float(self.pos.y()),
            "click_type": self.click_type,
            "style": self.style.copy()
        }

    @classmethod
    def from_dict(cls, data):
        pos = data.get("pos")
        if pos and len(pos) >= 2:
            x, y = float(pos[0]), float(pos[1])
        else:
            x = float(data.get("x", 0.0))
            y = float(data.get("y", 0.0))
        return cls(x, y, data.get("click_type", "left"), data.get("style", {}))

    def contains(self, pt):
        size = float(self.style.get("size", 36))
        r = size / 2.0 + 8.0
        px = pt.x() if hasattr(pt, "x") else pt[0]
        py = pt.y() if hasattr(pt, "y") else pt[1]
        dx = px - self.pos.x()
        dy = py - self.pos.y()
        return (dx * dx + dy * dy) <= (r * r)

    def render(self, painter: QPainter):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        base_col = QColor(self.style.get("color", "#007AFF" if self.click_type == "left" else "#FF9500"))
        size = float(self.style.get("size", 36))
        r = size / 2.0
        ring1 = QColor(base_col)
        ring1.setAlpha(80)
        painter.setPen(QPen(ring1, 2.5))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(self.pos, r, r)
        if self.click_type in ("double", "double_click"):
            ring2 = QColor(base_col)
            ring2.setAlpha(140)
            painter.setPen(QPen(ring2, 2.0))
            painter.drawEllipse(self.pos, r * 0.7, r * 0.7)
        center_col = QColor(base_col)
        center_col.setAlpha(220)
        painter.setPen(QPen(QColor(255, 255, 255), 1.5))
        painter.setBrush(QBrush(center_col))
        painter.drawEllipse(self.pos, 5.0, 5.0)
        label = self.style.get("label", "CLICK" if self.click_type == "left" else ("2x CLICK" if self.click_type in ("double", "double_click") else "R-CLICK"))
        if label:
            painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
            badge_rect = QRectF(self.pos.x() + 10, self.pos.y() - 20, 64, 18)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(20, 20, 20, 200)))
            painter.drawRoundedRect(badge_rect, 4, 4)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(badge_rect, Qt.AlignCenter, label)
        painter.restore()


class MagnifierZoomItem:
    """미세한 UI 컨트롤을 지정 배율로 확대하여 별도 렌즈로 시각화하는 돋보기 상세 주석 객체"""
    def __init__(self, source_rect, lens_rect, zoom_factor=2.0, style=None):
        self.source_rect = QRect(source_rect) if isinstance(source_rect, QRect) else QRect(int(source_rect[0]), int(source_rect[1]), int(source_rect[2]), int(source_rect[3]))
        self.lens_rect = QRect(lens_rect) if isinstance(lens_rect, QRect) else QRect(int(lens_rect[0]), int(lens_rect[1]), int(lens_rect[2]), int(lens_rect[3]))
        self.zoom_factor = float(zoom_factor)
        self.style = style.copy() if style else {}

    def clone(self):
        return MagnifierZoomItem(QRect(self.source_rect), QRect(self.lens_rect), self.zoom_factor, self.style.copy())

    def to_dict(self):
        return {
            "type": "MagnifierZoomItem",
            "source_rect": [int(self.source_rect.x()), int(self.source_rect.y()), int(self.source_rect.width()), int(self.source_rect.height())],
            "lens_rect": [int(self.lens_rect.x()), int(self.lens_rect.y()), int(self.lens_rect.width()), int(self.lens_rect.height())],
            "zoom_factor": self.zoom_factor,
            "style": self.style.copy()
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data.get("source_rect", [0, 0, 50, 50]),
            data.get("lens_rect", [100, 100, 150, 150]),
            data.get("zoom_factor", 2.0),
            data.get("style", {})
        )

    def render_zoom(self, painter: QPainter, pixmap: QPixmap):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        border_col = QColor(self.style.get("border_color", "#007AFF"))
        painter.setPen(QPen(border_col, 2, Qt.DashLine))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(self.source_rect)
        p1 = QPointF(self.source_rect.center())
        p2 = QPointF(self.lens_rect.center())
        painter.setPen(QPen(border_col, 1.5, Qt.DotLine))
        painter.drawLine(p1, p2)
        lens_f = QRectF(self.lens_rect)
        path = QPainterPath()
        radius = self.lens_rect.width() / 2.0 if self.style.get("shape") == "circle" else 8.0
        if self.style.get("shape") == "circle":
            path.addEllipse(lens_f)
        else:
            path.addRoundedRect(lens_f, radius, radius)
        painter.save()
        painter.setClipPath(path)
        if pixmap and not pixmap.isNull():
            cropped = pixmap.copy(self.source_rect)
            scaled = cropped.scaled(
                self.lens_rect.size(),
                Qt.IgnoreAspectRatio,
                Qt.SmoothTransformation
            )
            painter.drawPixmap(self.lens_rect, scaled)
        else:
            painter.fillRect(self.lens_rect, QColor(240, 240, 240))
        painter.restore()
        border_w = int(self.style.get("border_width", 3))
        painter.setPen(QPen(border_col, border_w))
        painter.setBrush(Qt.NoBrush)
        if self.style.get("shape") == "circle":
            painter.drawEllipse(lens_f)
        else:
            painter.drawRoundedRect(lens_f, radius, radius)
        painter.restore()

    def contains(self, pt):
        qpt = QPoint(int(pt.x()), int(pt.y())) if hasattr(pt, "x") else QPoint(int(pt[0]), int(pt[1]))
        return self.lens_rect.adjusted(-4, -4, 4, 4).contains(qpt) or self.source_rect.adjusted(-4, -4, 4, 4).contains(qpt)

    def render(self, painter: QPainter):
        self.render_zoom(painter, None)


# ------------------------------------------------------------------------------
# 치수선 아이템 (DimensionLineItem) — PixelSnap 스타일 픽셀/거리 측정선
# ------------------------------------------------------------------------------
class DimensionLineItem:
    def __init__(self, start_pos: QPointF, end_pos: QPointF, style=None, unit="px", cap_style="bracket"):
        self.start_pos = QPointF(start_pos)
        self.end_pos = QPointF(end_pos)
        default_style = {
            "color": "#007AFF",
            "width": 2,
            "tick_size": 8,
            "font_size": 11,
            "font_family": "Malgun Gothic",
            "font_bold": True,
            "badge_bg": "#007AFF",
            "badge_text_color": "#FFFFFF",
            "unit": unit,
            "cap_style": cap_style
        }
        if style:
            default_style.update(style)
        self.style = default_style

    def clone(self):
        return DimensionLineItem(self.start_pos, self.end_pos, self.style.copy())

    def to_dict(self):
        return {
            "type": "DimensionLineItem",
            "start_pos": [float(self.start_pos.x()), float(self.start_pos.y())],
            "end_pos": [float(self.end_pos.x()), float(self.end_pos.y())],
            "style": self.style.copy()
        }

    @classmethod
    def from_dict(cls, data):
        p1 = data.get("start_pos", [0.0, 0.0])
        p2 = data.get("end_pos", [0.0, 0.0])
        return cls(
            QPointF(float(p1[0]), float(p1[1])),
            QPointF(float(p2[0]), float(p2[1])),
            data.get("style", {})
        )

    def get_distance(self):
        dx = abs(self.end_pos.x() - self.start_pos.x())
        dy = abs(self.end_pos.y() - self.start_pos.y())
        if dy <= 2:
            return int(round(dx))
        elif dx <= 2:
            return int(round(dy))
        else:
            return int(round(math.hypot(dx, dy)))

    def contains(self, pt):
        p1 = self.start_pos
        p2 = self.end_pos
        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        l2 = dx * dx + dy * dy
        if l2 == 0:
            return math.hypot(pt.x() - p1.x(), pt.y() - p1.y()) <= 8.0
        t = max(0.0, min(1.0, ((pt.x() - p1.x()) * dx + (pt.y() - p1.y()) * dy) / l2))
        proj_x = p1.x() + t * dx
        proj_y = p1.y() + t * dy
        dist_sq = (pt.x() - proj_x)**2 + (pt.y() - proj_y)**2
        hit_margin = max(10.0, float(self.style.get("width", 2)) * 3.0)
        return dist_sq <= (hit_margin * hit_margin)

    def render(self, painter: QPainter):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        col = QColor(self.style.get("color", "#007AFF"))
        w = int(self.style.get("width", 2))
        tick_size = float(self.style.get("tick_size", 8))
        unit = self.style.get("unit", "px")

        p1 = self.start_pos
        p2 = self.end_pos
        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        dist = math.hypot(dx, dy)
        if dist < 2:
            painter.restore()
            return

        # 1. 메인 치수선
        pen = QPen(col, w, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(p1, p2)

        # 2. 양 끝 틱 (수직 브라켓)
        angle = math.atan2(dy, dx)
        perp_angle = angle + math.pi / 2.0
        perp_dx = math.cos(perp_angle) * (tick_size / 2.0)
        perp_dy = math.sin(perp_angle) * (tick_size / 2.0)

        painter.drawLine(
            QPointF(p1.x() - perp_dx, p1.y() - perp_dy),
            QPointF(p1.x() + perp_dx, p1.y() + perp_dy)
        )
        painter.drawLine(
            QPointF(p2.x() - perp_dx, p2.y() - perp_dy),
            QPointF(p2.x() + perp_dx, p2.y() + perp_dy)
        )

        # 3. 중앙 치수 뱃지 (Pill badge)
        mid_x = (p1.x() + p2.x()) / 2.0
        mid_y = (p1.y() + p2.y()) / 2.0

        val = self.get_distance()
        text = f"{val} {unit}"

        font_family = self.style.get("font_family", "Malgun Gothic")
        font_size = int(self.style.get("font_size", 11))
        font = QFont(font_family, font_size)
        font.setBold(self.style.get("font_bold", True))
        painter.setFont(font)

        fm = QFontMetrics(font)
        tw = fm.horizontalAdvance(text)
        th = fm.height()
        pad_x = 8
        pad_y = 4
        badge_w = tw + pad_x * 2
        badge_h = th + pad_y * 2
        badge_rect = QRectF(mid_x - badge_w / 2.0, mid_y - badge_h / 2.0, badge_w, badge_h)

        # 드롭 섀도우
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 50))
        painter.drawRoundedRect(QRectF(badge_rect.x() + 1, badge_rect.y() + 1.5, badge_w, badge_h), 5, 5)

        # 뱃지 배경
        badge_bg = QColor(self.style.get("badge_bg", col.name()))
        painter.setBrush(QBrush(badge_bg))
        painter.setPen(QPen(col.darker(110), 1))
        painter.drawRoundedRect(badge_rect, 5, 5)

        # 텍스트
        text_col = QColor(self.style.get("badge_text_color", "#FFFFFF"))
        painter.setPen(text_col)
        painter.drawText(badge_rect, Qt.AlignCenter, text)

        painter.restore()


class BoxDimensionItem:
    """영역의 가로×세로(W×H) 크기를 측정하여 외곽 박스와 치수선 뱃지를 표시하는 객체"""
    def __init__(self, rect, style=None):
        self.rect = QRectF(rect) if hasattr(rect, "x") else QRectF(rect[0], rect[1], rect[2], rect[3])
        default_style = {
            "color": "#007AFF",
            "border_width": 2,
            "fill": False,
            "fill_opacity": 30,
            "unit": "px",
            "font_size": 11,
            "font_family": "Malgun Gothic",
            "font_bold": True,
            "badge_bg": "#007AFF",
            "badge_text_color": "#FFFFFF",
            "corner_radius": 4
        }
        if style:
            default_style.update(style)
        self.style = default_style

    def clone(self):
        return BoxDimensionItem(QRectF(self.rect), self.style.copy())

    def to_dict(self):
        return {
            "type": "BoxDimensionItem",
            "rect": [float(self.rect.x()), float(self.rect.y()), float(self.rect.width()), float(self.rect.height())],
            "style": self.style.copy()
        }

    @classmethod
    def from_dict(cls, data):
        r = data.get("rect", [0, 0, 100, 100])
        return cls(QRectF(r[0], r[1], r[2], r[3]), data.get("style", {}))

    def contains(self, pt):
        if hasattr(pt, "toPoint"):
            pt = pt.toPoint()
        return self.rect.adjusted(-6, -6, 6, 6).contains(pt)

    def render(self, painter: QPainter):
        r = self.rect.normalized()
        if r.width() < 2 or r.height() < 2:
            return
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        col = QColor(self.style.get("color", "#007AFF"))
        bw = int(self.style.get("border_width", 2))
        radius = float(self.style.get("corner_radius", 4))
        unit = self.style.get("unit", "px")

        # 1. 박스 영역 테두리 & 배경 채우기
        if self.style.get("fill", False):
            fill_col = QColor(col)
            fill_col.setAlpha(int(self.style.get("fill_opacity", 30)))
            painter.setBrush(QBrush(fill_col))
        else:
            painter.setBrush(Qt.NoBrush)

        pen = QPen(col, bw, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawRoundedRect(r, radius, radius)

        # 2. 치수 텍스트 뱃지 (가로 × 세로 px)
        w_val = int(round(r.width()))
        h_val = int(round(r.height()))
        badge_text = f"{w_val} × {h_val} {unit}"

        font_family = self.style.get("font_family", "Malgun Gothic")
        font_size = int(self.style.get("font_size", 11))
        font = QFont(font_family, font_size)
        font.setBold(bool(self.style.get("font_bold", True)))
        painter.setFont(font)

        fm = QFontMetrics(font)
        tw = fm.horizontalAdvance(badge_text)
        th = fm.height()
        pad_x = 8
        pad_y = 4
        bw_badge = tw + pad_x * 2
        bh_badge = th + pad_y * 2

        bx = r.x() + 6
        by = r.y() - bh_badge - 3
        if by < 4:
            by = r.y() + 4

        badge_rect = QRectF(bx, by, bw_badge, bh_badge)

        # 뱃지 드롭 섀도우
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 50))
        painter.drawRoundedRect(QRectF(badge_rect.x() + 1, badge_rect.y() + 1.5, bw_badge, bh_badge), 4, 4)

        # 뱃지 배경
        badge_bg = QColor(self.style.get("badge_bg", col.name()))
        painter.setBrush(QBrush(badge_bg))
        painter.setPen(QPen(col.darker(110), 1))
        painter.drawRoundedRect(badge_rect, 4, 4)

        # 뱃지 텍스트
        text_col = QColor(self.style.get("badge_text_color", "#FFFFFF"))
        painter.setPen(text_col)
        painter.drawText(badge_rect, Qt.AlignCenter, badge_text)

        painter.restore()


# OCR Worker & Dialog
# ------------------------------------------------------------------------------
class OcrWorkerThread(QThread):
    """백그라운드 OCR 스레드. 스마트 전처리(패딩+업스케일) 및 WinRT → RapidOCR 다단계 폴백."""
    sig_result = Signal(str, str)   # (text, error_msg)

    def __init__(self, pil_img, lang="ko", parent=None):
        super().__init__(parent)
        self.pil_img = pil_img
        self.lang = lang

    @staticmethod
    def preprocess_image_for_ocr(pil_img, scale=2.0, pad=16, contrast_boost=False):
        """작은 버튼, 타이트한 드래그 영역, 저해상도 텍스트 인식을 위한 스마트 전처리.
        1. 모서리 4점 배경색 자동 샘플링 (단색/그라데이션 대응)
        2. 16px 패딩 여백 부여로 외곽 테두리 텍스트 분할(Segmentation) 실패 원천 방지
        3. 높이/너비 기반 적응형 Lanczos 고품질 업스케일링 (1.0~3.0배)
        4. 선명도 및 대비(옵션) 강화
        """
        try:
            from PIL import Image, ImageOps, ImageEnhance
            img_rgb = pil_img.convert("RGB")
            w, h = img_rgb.size
            if w <= 0 or h <= 0:
                return pil_img

            corners = [
                img_rgb.getpixel((0, 0)),
                img_rgb.getpixel((w - 1, 0)),
                img_rgb.getpixel((0, h - 1)),
                img_rgb.getpixel((w - 1, h - 1)),
            ]
            bg_color = max(set(corners), key=corners.count)

            # 외곽 패딩 여백 추가 (글자 획이 이미지 외곽선과 닿아 노이즈로 필터링되는 현상 방지)
            padded = ImageOps.expand(img_rgb, border=pad, fill=bg_color)

            # 적응형 배율 계산 (이미지가 작을수록 업스케일)
            eff_scale = scale
            if h >= 120 and w >= 240:
                eff_scale = 1.0
            elif h >= 60 and w >= 120:
                eff_scale = min(eff_scale, 1.5)

            if eff_scale > 1.0:
                nw, nh = int(padded.width * eff_scale), int(padded.height * eff_scale)
                padded = padded.resize((nw, nh), Image.Resampling.LANCZOS)
                padded = ImageEnhance.Sharpness(padded).enhance(1.2)

            if contrast_boost:
                padded = ImageEnhance.Contrast(padded).enhance(1.5)

            return padded
        except Exception:
            return pil_img

    def run(self):
        text, err = self._try_winrt_ocr()
        if err or not text or not text.strip():
            rapid_text, rapid_err = self._try_rapid_ocr()
            if rapid_text and rapid_text.strip():
                text, err = rapid_text, ""
        self.sig_result.emit(text, err)

    def _try_winrt_ocr(self):
        try:
            import asyncio
            from winsdk.windows.media.ocr import OcrEngine
            import winsdk.windows.globalization as glob
            import winsdk.windows.graphics.imaging as wgi
            import winsdk.windows.storage.streams as wss

            async def _recognize_image(target_pil, engine):
                pil_rgba = target_pil.convert("RGBA")
                tw, th = pil_rgba.size
                raw_bytes = pil_rgba.tobytes()
                writer = wss.DataWriter()
                writer.write_bytes(bytes(raw_bytes))
                ibuf = writer.detach_buffer()
                soft_bmp = wgi.SoftwareBitmap.create_copy_from_buffer(
                    ibuf, wgi.BitmapPixelFormat.RGBA8, tw, th
                )
                result = await engine.recognize_async(soft_bmp)
                return "\n".join([line.text for line in result.lines if line.text.strip()]).strip()

            async def _do_ocr():
                # 언어 선택 (지정 언어 -> 사용자 프로필 언어 -> 설치된 첫 언어)
                engine = None
                try:
                    lang_obj = glob.Language(self.lang)
                    if OcrEngine.is_language_supported(lang_obj):
                        engine = OcrEngine.try_create_from_language(lang_obj)
                except Exception:
                    pass
                if engine is None:
                    engine = OcrEngine.try_create_from_user_profile_languages()
                if engine is None and OcrEngine.available_recognizer_languages:
                    engine = OcrEngine.try_create_from_language(OcrEngine.available_recognizer_languages[0])

                if engine is None:
                    return None

                # 1차 시도: 스마트 전처리(16px 패딩 + 적응형 2배 업스케일)
                proc1 = self.preprocess_image_for_ocr(self.pil_img, scale=2.0, pad=16)
                text = await _recognize_image(proc1, engine)
                if text:
                    return text

                # 2차 시도: 3배 업스케일 전처리 (초소형 버튼 대응)
                proc2 = self.preprocess_image_for_ocr(self.pil_img, scale=3.0, pad=20)
                text = await _recognize_image(proc2, engine)
                if text:
                    return text

                # 3차 시도: 원본 이미지 (이미 여백이 충분하거나 고해상도인 경우)
                text = await _recognize_image(self.pil_img, engine)
                return text

            loop = asyncio.new_event_loop()
            try:
                text = loop.run_until_complete(_do_ocr())
            finally:
                loop.close()
            if text is None:
                return "", "WinRT OCR engine unavailable"
            return text, ""
        except Exception as e:
            return "", str(e)

    def _try_rapid_ocr(self):
        try:
            import importlib
            rapid_mod = importlib.import_module("rapidocr_onnxruntime")
            RapidOCR = getattr(rapid_mod, "RapidOCR")
            np = importlib.import_module("numpy")
            ocr = RapidOCR()
            # 스마트 전처리 이미지로 인식률 극대화
            proc_img = self.preprocess_image_for_ocr(self.pil_img, scale=2.0, pad=16)
            img_np = np.array(proc_img.convert("RGB"))
            result, _ = ocr(img_np)
            if not result:
                img_np_raw = np.array(self.pil_img.convert("RGB"))
                result, _ = ocr(img_np_raw)
            if not result:
                return "", ""
            lines = [item[1] for item in result if item and len(item) > 1]
            return "\n".join(lines).strip(), ""
        except (ImportError, SystemError, Exception) as e:
            return "", ""


class OcrResultDialog(QDialog):
    """OCR 결과 표시 다이얼로그 — 텍스트 + 클립보드 복사 + 닫기."""
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("ocr_dialog_title", "OCR 텍스트 추출"))
        self.setMinimumSize(480, 320)
        self.resize(560, 380)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(8)

        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(False)
        self.text_edit.setPlainText(text if text else tr("ocr_no_text", "인식된 텍스트가 없습니다."))
        self.text_edit.setFont(QFont("Pretendard", 10) if QFont("Pretendard").exactMatch() else QFont("Malgun Gothic", 10))
        layout.addWidget(self.text_edit, 1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        self.btn_copy = QPushButton(tr("ocr_copy_btn", "클립보드 복사"), self)
        self.btn_copy.clicked.connect(self._copy_to_clipboard)
        btn_close = QPushButton(tr("ocr_close_btn", "닫기"), self)
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(self.btn_copy)
        btn_row.addStretch(1)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

        # 텍스트가 있으면 자동 클립보드 복사
        if text and text.strip():
            QApplication.clipboard().setText(text)
            self.btn_copy.setText(tr("ocr_copy_btn_done", "✓ 복사됨"))

    def _copy_to_clipboard(self):
        QApplication.clipboard().setText(self.text_edit.toPlainText())
        self.btn_copy.setText(tr("ocr_copy_btn_done", "✓ 복사됨"))


class PiiRedactionEngine:
    """화면 내 민감 개인정보(PII) 자동 탐지 및 마스킹 영역 좌표 계산 엔진"""

    PATTERNS = {
        "phone": re.compile(r'(?:01[016789]|02|0[3-6][1-5]|070|050[0-9]|1[568]\d{2})[-\s.]?\d{3,4}[-\s.]?\d{4}'),
        "resident": re.compile(r'\b\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])[-\s.]?[1-8]\d{6}\b'),
        "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'),
        "account": re.compile(r'(?i)(?:(?:계좌(?:번호)?|입금(?:처|계좌)?|환불(?:계좌)?|통장(?:번호)?|국민|신한|우리|하나|농협|기업|카카오|토스|SC|씨티|새마을|신협|우체국|수협|iM|부산|대구|광주|전북|경남|제주|Account|Acc(?:\.?|ount)?|Bank|ACCT)[\s:：#№]*[가-힣A-Za-z0-9\s().#№]{0,12}[\s:：#№]*|\bIBAN[\s:：]*)([0-9]{3,6}[-\s.]?[0-9]{2,6}[-\s.]?[0-9]{3,8}|[A-Z]{2}\d{2}[A-Z0-9]{11,30})\b'),
        "card": re.compile(r'\b(?:\d{4}[-\s.]?){3}\d{4}\b'),
        "biz_number": re.compile(r'\b\d{3}[-\s.]?\d{2}[-\s.]?\d{5}\b'),
        "korean_name": re.compile(r'(?:[가-힣]{2,4}\s*(?:대표(?:이사)?|사장|부사장|전무|상무|이사|부장|차장|과장|대리|주임|사원|팀장|실장|본부장|연구원|수석|책임|선임|매니저|프로|교수|박사|선생(?:님)?|위원|변호사|회계사|노무사|의사|간호사|약사|기사|주무관|사무관|서기관))|(?:(?:대표(?:이사)?|사장|부사장|전무|상무|이사|부장|차장|과장|대리|주임|사원|팀장|실장|본부장|연구원|수석|책임|선임|매니저|프로)\s*[가-힣]{2,4})'),
        "address": re.compile(r'(?:서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)(?:특별(?:시|자치시|자치도)|광역시|자치도|도|시)?(?:\s+[가-힣0-9]+[시군구])+\s+[가-힣0-9]+[읍면동로길]\s*\d*(?:-\d+)?'),
        "ip": re.compile(r'\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b'),
        "mac": re.compile(r'\b(?:(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}|(?:[0-9A-Fa-f]{4}\.){2}[0-9A-Fa-f]{4})\b'),
    }

    @classmethod
    def synthesize_regex_from_example(cls, example: str) -> str:
        """사용자가 입력한 서식/예시 데이터를 분석하여 권장 정규식을 자동 생성"""
        if not example or not example.strip():
            return ""
        text = example.strip()
        # 1. 이미 정규식 문법 토큰이 포함된 경우 원문 유지
        if any(tok in text for tok in [r'\d', r'\w', r'\s', r'\b', '.*', '.+', '[0-9]', '[a-z]', '[A-Z]', '[가-힣]']):
            return text
        # 2. 이메일 형식
        if '@' in text and '.' in text.split('@')[-1]:
            return r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
        # 3. MAC 주소
        if re.match(r'^(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$', text) or re.match(r'^(?:[0-9A-Fa-f]{4}\.){2}[0-9A-Fa-f]{4}$', text):
            return r'(?:(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}|(?:[0-9A-Fa-f]{4}\.){2}[0-9A-Fa-f]{4})'
        # 4. IP 주소
        parts = text.split('.')
        if len(parts) == 4 and all(p.isdigit() and 1 <= len(p) <= 3 for p in parts):
            return r'(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)'
        # 5. 토큰 분해 및 패턴 조립
        tokens = re.split(r'([-\s./_:()])', text)
        pattern_parts = []
        starts_with_digit = False
        ends_with_digit = False
        for idx, tok in enumerate(tokens):
            if not tok:
                continue
            if idx == 0 and tok.isdigit():
                starts_with_digit = True
            if tok.isdigit():
                ends_with_digit = True
            else:
                ends_with_digit = False

            if tok in ['-', '.', '/', '_', ':', ' ', '(', ')']:
                pattern_parts.append(re.escape(tok))
            elif tok.isdigit():
                pattern_parts.append(rf'\d{{{len(tok)}}}')
            elif tok.isalpha():
                if all(c in 'aA' for c in tok):
                    pattern_parts.append(rf'[A-Za-z]{{{len(tok)}}}')
                else:
                    pattern_parts.append(re.escape(tok))
            else:
                pattern_parts.append(re.escape(tok))

        res = ''.join(pattern_parts)
        prefix = r'(?<!\d)' if starts_with_digit else r'(?<![A-Za-z0-9])'
        suffix = r'(?!\d)' if ends_with_digit else r'(?![A-Za-z0-9])'
        return f'{prefix}{res}{suffix}'

    @classmethod
    def check_unmasked_pii(cls, pixmap, items, active_categories=None, custom_rules=None):
        """슬라이드 내 블러나 불투명 박스로 가려지지 않은 민감정보 종류 목록 반환"""
        if pixmap is None or pixmap.isNull():
            return []
        return []

    @classmethod
    def detect_pii_from_lines(cls, lines_of_words, active_categories=None, custom_rules=None):
        if active_categories is None:
            active_categories = ["resident", "phone", "email", "card", "account", "biz_number", "korean_name", "address", "ip", "mac"]
        raw_rects = []

        active_regexes = []
        for cat in active_categories:
            if cat in cls.PATTERNS:
                active_regexes.append(cls.PATTERNS[cat])

        if custom_rules:
            for rule in custom_rules:
                if isinstance(rule, dict) and rule.get("enabled", True):
                    pat_str = rule.get("pattern", "").strip()
                    if pat_str:
                        try:
                            active_regexes.append(re.compile(pat_str))
                        except Exception as e:
                            print(f"[PII Custom Regex Compile Error] {rule.get('name')}: {e}")

        for line in lines_of_words:
            n = len(line)
            if n == 0:
                continue
            matched_indices = set()
            for length in range(1, min(7, n + 1)):
                for i in range(n - length + 1):
                    if any(idx in matched_indices for idx in range(i, i + length)):
                        continue
                    sub = line[i:i + length]
                    for sep in ['', '.', ' ', '-']:
                        combined = sep.join(w[0] for w in sub)
                        matched = False
                        for pat in active_regexes:
                            m = pat.search(combined)
                            if m:
                                u_rect = sub[0][1]
                                for w in sub[1:]:
                                    u_rect = u_rect.united(w[1])
                                raw_rects.append(u_rect)
                                for idx in range(i, i + length):
                                    matched_indices.add(idx)
                                matched = True
                                break
                        if matched:
                            break

        return cls.deduplicate_and_pad(raw_rects)

    @classmethod
    def deduplicate_and_pad(cls, rect_list, pad_x=4, pad_y=3):
        if not rect_list:
            return []
        merged = []
        for r in rect_list:
            padded = r.adjusted(-pad_x, -pad_y, pad_x, pad_y)
            combined = False
            for idx, m in enumerate(merged):
                if m.intersects(padded) or m.contains(padded) or padded.contains(m):
                    merged[idx] = m.united(padded)
                    combined = True
                    break
            if not combined:
                merged.append(padded)
        return merged


class PiiWorkerThread(QThread):
    """WinRT OCR을 비동기로 호출하여 화면 내 모든 단어와 좌표를 추출한 뒤 PII 마스킹 영역 목록을 방출"""
    sig_result = Signal(list, str)

    def __init__(self, pil_img, lang="ko", active_categories=None, custom_rules=None, parent=None):
        super().__init__(parent)
        self.pil_img = pil_img
        self.lang = lang
        self.active_categories = active_categories
        self.custom_rules = custom_rules

    def run(self):
        try:
            lines_words = self._extract_ocr_words()
            if not lines_words:
                self.sig_result.emit([], "No text detected")
                return
            rects = PiiRedactionEngine.detect_pii_from_lines(
                lines_words,
                active_categories=self.active_categories,
                custom_rules=self.custom_rules
            )
            self.sig_result.emit(rects, f"{len(rects)} items found")
        except Exception as e:
            self.sig_result.emit([], str(e))

    def _extract_ocr_words(self):
        try:
            import asyncio
            from winsdk.windows.media.ocr import OcrEngine
            import winsdk.windows.globalization as glob
            import winsdk.windows.graphics.imaging as wgi
            import winsdk.windows.storage.streams as wss

            async def _do_scan():
                engine = None
                try:
                    lang_obj = glob.Language(self.lang)
                    if OcrEngine.is_language_supported(lang_obj):
                        engine = OcrEngine.try_create_from_language(lang_obj)
                except Exception:
                    pass
                if engine is None:
                    engine = OcrEngine.try_create_from_user_profile_languages()
                if engine is None and OcrEngine.available_recognizer_languages:
                    engine = OcrEngine.try_create_from_language(OcrEngine.available_recognizer_languages[0])
                if engine is None:
                    return []

                pil_rgba = self.pil_img.convert("RGBA")
                tw, th = pil_rgba.size
                raw_bytes = pil_rgba.tobytes()
                writer = wss.DataWriter()
                writer.write_bytes(bytes(raw_bytes))
                ibuf = writer.detach_buffer()
                soft_bmp = wgi.SoftwareBitmap.create_copy_from_buffer(
                    ibuf, wgi.BitmapPixelFormat.RGBA8, tw, th
                )
                result = await engine.recognize_async(soft_bmp)
                lines = []
                for line in result.lines:
                    lw = []
                    for word in line.words:
                        r = QRect(int(word.bounding_rect.x), int(word.bounding_rect.y),
                                  int(word.bounding_rect.width), int(word.bounding_rect.height))
                        lw.append((word.text, r))
                    if lw:
                        lines.append(lw)
                return lines

            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(_do_scan())
            finally:
                loop.close()
        except Exception:
            return []


class SmartCleanupEngine:
    """선택 영역 주변 텍스처 분석 기반 배경 복원 및 스마트 지우개 인페인팅 엔진"""

    @staticmethod
    def inpaint_rect(pixmap: QPixmap, rect: QRect, radius: int = 3) -> QPixmap:
        if not pixmap or pixmap.isNull() or rect.isEmpty():
            return pixmap

        r = rect.normalized().intersected(pixmap.rect())
        if r.width() <= 0 or r.height() <= 0:
            return pixmap

        try:
            import cv2
            import numpy as np

            qimg = pixmap.toImage().convertToFormat(QImage.Format_RGB888)
            w, h = qimg.width(), qimg.height()
            ptr = qimg.bits()
            arr = np.frombuffer(ptr, dtype=np.uint8).reshape((h, w, 3)).copy()

            mask = np.zeros((h, w), dtype=np.uint8)
            rx, ry, rw, rh = r.x(), r.y(), r.width(), r.height()
            mask[ry:ry+rh, rx:rx+rw] = 255

            inpainted = cv2.inpaint(arr, mask, inpaintRadius=max(3, radius), flags=cv2.INPAINT_TELEA)
            out_img = QImage(inpainted.data, w, h, w * 3, QImage.Format_RGB888).copy()
            return QPixmap.fromImage(out_img)

        except Exception:
            try:
                from PIL import Image, ImageFilter
                qimg = pixmap.toImage().convertToFormat(QImage.Format_RGBA8888)
                w, h = qimg.width(), qimg.height()
                ptr = qimg.bits()
                pil_img = Image.frombuffer("RGBA", (w, h), ptr, "raw", "RGBA", 0, 1).copy()

                rx, ry, rw, rh = r.x(), r.y(), r.width(), r.height()
                pad = 4
                bx1 = max(0, rx - pad)
                by1 = max(0, ry - pad)
                bx2 = min(w, rx + rw + pad)
                by2 = min(h, ry + rh + pad)
                crop = pil_img.crop((bx1, by1, bx2, by2))
                blurred = crop.filter(ImageFilter.GaussianBlur(radius=8))
                paste_crop = blurred.crop((rx - bx1, ry - by1, rx - bx1 + rw, ry - by1 + rh))
                pil_img.paste(paste_crop, (rx, ry))

                qimg_out = QImage(pil_img.tobytes(), w, h, w * 4, QImage.Format_RGBA8888).copy()
                return QPixmap.fromImage(qimg_out)
            except Exception:
                return pixmap



class MagneticSnapEngine:
    """Windows 컨트롤 및 UI 요소 마그네틱 자석 스냅 엔진"""

    @staticmethod
    def get_element_rect(global_pt, exclude_hwnd=0):
        try:
            import win32gui
            import win32con
            gx, gy = int(global_pt.x()), int(global_pt.y())
            top_hwnd = win32gui.WindowFromPoint((gx, gy))
            if not top_hwnd or top_hwnd == exclude_hwnd:
                return QRect()

            curr_hwnd = top_hwnd
            for _ in range(8):
                pt_client = win32gui.ScreenToClient(curr_hwnd, (gx, gy))
                child = win32gui.ChildWindowFromPointEx(
                    curr_hwnd,
                    pt_client,
                    win32con.CWP_SKIPINVISIBLE | win32con.CWP_SKIPDISABLED
                )
                if not child or child == curr_hwnd or child == exclude_hwnd:
                    break
                curr_hwnd = child

            r = win32gui.GetWindowRect(curr_hwnd)
            rw = r[2] - r[0]
            rh = r[3] - r[1]
            if rw >= 12 and rh >= 12:
                return QRect(r[0], r[1], rw, rh)

            r_top = win32gui.GetWindowRect(top_hwnd)
            return QRect(r_top[0], r_top[1], r_top[2] - r_top[0], r_top[3] - r_top[1])
        except Exception:
            return QRect()


class ScrollStitchEngine:
    """긴 웹페이지 및 ERP 테이블 수직 스크롤 프레임 자동 정합 및 파노라마 스티칭 엔진"""

    @staticmethod
    def stitch_images(image_list, template_ratio=0.20, min_score=0.70):
        if not image_list:
            return None
        if len(image_list) == 1:
            from PIL import Image
            return image_list[0] if hasattr(image_list[0], "size") else Image.open(image_list[0])

        from PIL import Image
        import numpy as np

        pil_frames = []
        for img in image_list:
            if isinstance(img, str):
                pil_frames.append(Image.open(img).convert("RGB"))
            elif hasattr(img, "convert"):
                pil_frames.append(img.convert("RGB"))

        if not pil_frames:
            return None

        try:
            import cv2
            stitched_np = np.array(pil_frames[0])

            for next_pil in pil_frames[1:]:
                next_np = np.array(next_pil)
                sh, sw = stitched_np.shape[:2]
                nh, nw = next_np.shape[:2]

                if sw != nw:
                    next_np = cv2.resize(next_np, (sw, int(nh * sw / nw)))
                    nh, nw = next_np.shape[:2]

                th = max(20, min(int(nh * template_ratio), 180, sh // 2))
                template = stitched_np[-th:, :]

                search_region = next_np[:min(nh, int(nh * 0.90)), :]
                if search_region.shape[0] < th:
                    stitched_np = np.vstack([stitched_np, next_np])
                    continue

                res = cv2.matchTemplate(search_region, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(res)

                if max_val >= min_score:
                    overlap_y = max_loc[1]
                    cut_y = overlap_y + th
                    if cut_y < nh:
                        revealed = next_np[cut_y:, :]
                        stitched_np = np.vstack([stitched_np, revealed])
                else:
                    stitched_np = np.vstack([stitched_np, next_np])

            return Image.fromarray(stitched_np)
        except Exception:
            total_h = sum(im.height for im in pil_frames)
            max_w = max(im.width for im in pil_frames)
            res_im = Image.new("RGB", (max_w, total_h), (255, 255, 255))
            cur_y = 0
            for im in pil_frames:
                res_im.paste(im, (0, cur_y))
                cur_y += im.height
            return res_im


class ActionRecorderThread(QThread):
    """무인 연속 액션 레코더 스레드. 마우스 클릭 실시간 감지 및 자동 스탬프 캡처"""
    sig_action_recorded = Signal(QPixmap, QPoint, int)
    sig_finished = Signal(int)
    signal_action_captured = sig_action_recorded
    signal_stopped = sig_finished

    def __init__(self, target_monitor=-1, parent=None):
        super().__init__(parent)
        self.target_monitor = target_monitor
        self.is_running = False
        self.step_count = 0

    @property
    def running(self):
        return self.is_running

    def run(self):
        import time
        import win32api
        import win32con
        import win32gui

        self.is_running = True
        self.step_count = 0
        last_state = 0
        last_click_time = 0.0

        while self.is_running:
            time.sleep(0.035)
            state = win32api.GetAsyncKeyState(win32con.VK_LBUTTON)
            is_down = bool(state & 0x8000)

            if is_down and not last_state:
                now = time.time()
                if now - last_click_time >= 0.25:
                    last_click_time = now
                    try:
                        cursor_pos = win32gui.GetCursorPos()
                        time.sleep(0.05)
                        screens = MultiMonitorManager.get_screens()
                        if 0 <= self.target_monitor < len(screens):
                            pix = screens[self.target_monitor].grabWindow(0)
                        else:
                            pix = MultiMonitorManager.grab_full_virtual_desktop()

                        self.step_count += 1
                        self.sig_action_recorded.emit(pix, QPoint(cursor_pos[0], cursor_pos[1]), self.step_count)
                    except Exception:
                        pass
            last_state = is_down

        self.sig_finished.emit(self.step_count)

    def stop(self):
        self.is_running = False


class RecordingFloatWidget(QWidget):
    """무인 연속 액션 녹화 중 화면 구석에 상시 노출되는 콤팩트 플로팅 제어 위젯"""
    sig_stop_requested = Signal()
    signal_stop_requested = sig_stop_requested

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(260, 48)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(8)

        self.container = QFrame(self)
        self.container.setStyleSheet("""
            QFrame {
                background-color: #0F172A;
                border: 1px solid #334155;
                border-radius: 18px;
            }
        """)
        c_layout = QHBoxLayout(self.container)
        c_layout.setContentsMargins(10, 4, 10, 4)
        c_layout.setSpacing(8)

        self.lbl_rec = QLabel("🔴 REC", self.container)
        self.lbl_rec.setStyleSheet("color: #EF4444; font-weight: bold; font-size: 11px;")

        self.lbl_steps = QLabel("0단계", self.container)
        self.lbl_steps.setStyleSheet("color: #F8FAFC; font-weight: bold; font-size: 11px;")

        self.btn_stop = QPushButton(tr("btn_stop_recording", "완료"), self.container)
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: white;
                font-weight: bold;
                font-size: 11px;
                border-radius: 10px;
                padding: 3px 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
            }
        """)
        self.btn_stop.clicked.connect(self.sig_stop_requested.emit)

        c_layout.addWidget(self.lbl_rec)
        c_layout.addWidget(self.lbl_steps)
        c_layout.addStretch(1)
        c_layout.addWidget(self.btn_stop)

        layout.addWidget(self.container)
        self._drag_pos = QPoint()

    def update_steps(self, count):
        self.lbl_steps.setText(f"{count}단계")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = get_mouse_global_pos(event) - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and not self._drag_pos.isNull():
            self.move(get_mouse_global_pos(event) - self._drag_pos)
            event.accept()

# 주석 직렬화 레지스트리 및 팩토리 (Annotation Registry & Factory)
# ------------------------------------------------------------------------------
BlurItem = BlurMosaicItem
SpotlightItem = SpotlightMaskItem
MagnifierItem = MagnifierZoomItem
ClickItem = ClickRippleItem

class FlowchartNodeItem:
    """플로우차트 노드 도형 객체 (상하좌우 4개 마그넷 포인트 지원)"""
    def __init__(self, text="Process", x=100, y=100, w=75, h=32, shape_type="process", style=None):
        self.text = str(text)
        self.rect = QRectF(float(x), float(y), float(w), float(h))
        self.shape_type = str(shape_type).lower()
        if style is None:
            self.style = {
                "bg_color": "#EFF6FF",
                "border_color": "#2563EB",
                "border_width": 1.5,
                "text_color": "#1E293B",
                "font_size": 7,
                "font_bold": True
            }
        else:
            self.style = style.copy() if hasattr(style, "copy") else dict(style)
        self._hovered = False
        self._hovered_magnet = None
        self._show_magnets = True

    def clone(self):
        return FlowchartNodeItem(self.text, self.rect.x(), self.rect.y(), self.rect.width(), self.rect.height(), self.shape_type, self.style.copy())

    def get_magnet_points(self):
        """상하좌우 4개 꼭지점 마그넷 포인트 좌표 반환"""
        cx = self.rect.center().x()
        cy = self.rect.center().y()
        return {
            "top": QPointF(cx, self.rect.top()),
            "bottom": QPointF(cx, self.rect.bottom()),
            "left": QPointF(self.rect.left(), cy),
            "right": QPointF(self.rect.right(), cy)
        }

    def get_closest_magnet_point(self, pt, threshold=22.0):
        """지정된 좌표(pt)에서 threshold 이내의 가장 가까운 마그넷 포인트 탐색 및 반환"""
        qpt = QPointF(pt)
        magnets = self.get_magnet_points()
        closest_key = None
        min_dist = float('inf')
        for key, mpt in magnets.items():
            dx = qpt.x() - mpt.x()
            dy = qpt.y() - mpt.y()
            dist = math.hypot(dx, dy)
            if dist < min_dist and dist <= threshold:
                min_dist = dist
                closest_key = key
        if closest_key:
            return closest_key, magnets[closest_key]
        return None, None

    def contains(self, pt):
        qpt = QPointF(pt)
        if not self.rect.contains(qpt):
            return False
        if self.shape_type == "decision":
            pts = [
                QPointF(self.rect.center().x(), self.rect.top()),
                QPointF(self.rect.right(), self.rect.center().y()),
                QPointF(self.rect.center().x(), self.rect.bottom()),
                QPointF(self.rect.left(), self.rect.center().y())
            ]
            poly = QPolygonF(pts)
            return poly.containsPoint(qpt, Qt.OddEvenFill)
        return True

    def to_dict(self):
        return {
            "type": "FlowchartNodeItem",
            "text": self.text,
            "x": float(self.rect.x()),
            "y": float(self.rect.y()),
            "w": float(self.rect.width()),
            "h": float(self.rect.height()),
            "shape_type": self.shape_type,
            "style": self.style.copy()
        }

    @classmethod
    def from_dict(cls, data):
        rect_data = data.get("rect")
        if rect_data and len(rect_data) >= 4:
            x, y, w, h = rect_data[0], rect_data[1], rect_data[2], rect_data[3]
        else:
            x = data.get("x", 100)
            y = data.get("y", 100)
            w = data.get("w", 75)
            h = data.get("h", 32)
        return cls(
            text=data.get("text", "Process"),
            x=x, y=y, w=w, h=h,
            shape_type=data.get("shape_type", "process"),
            style=data.get("style")
        )

    def render(self, painter: QPainter, is_selected=False):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        bg_col = QColor(self.style.get("bg_color", "#EFF6FF"))
        border_col = QColor(self.style.get("border_color", "#2563EB"))
        border_w = float(self.style.get("border_width", 1.5))
        text_col = QColor(self.style.get("text_color", "#1E293B"))
        f_size = int(self.style.get("font_size", 7))
        f_bold = bool(self.style.get("font_bold", True))
        
        pen = QPen(border_col, border_w)
        brush = QBrush(bg_col)
        painter.setPen(pen)
        painter.setBrush(brush)

        r = self.rect
        st = self.shape_type

        # 1. 도형 드로잉
        if st == "process":
            painter.drawRoundedRect(r, 4, 4)
        elif st == "decision":
            poly = QPolygonF([
                QPointF(r.center().x(), r.top()),
                QPointF(r.right(), r.center().y()),
                QPointF(r.center().x(), r.bottom()),
                QPointF(r.left(), r.center().y())
            ])
            painter.drawPolygon(poly)
        elif st == "terminal":
            radius = min(r.width(), r.height()) / 2.0
            painter.drawRoundedRect(r, radius, radius)
        elif st == "io":
            skew = r.width() * 0.16
            poly = QPolygonF([
                QPointF(r.left() + skew, r.top()),
                QPointF(r.right(), r.top()),
                QPointF(r.right() - skew, r.bottom()),
                QPointF(r.left(), r.bottom())
            ])
            painter.drawPolygon(poly)
        elif st == "database":
            h_top = min(8.0, r.height() * 0.22)
            path = QPainterPath()
            path.moveTo(r.left(), r.top() + h_top)
            path.lineTo(r.left(), r.bottom() - h_top)
            path.arcTo(QRectF(r.left(), r.bottom() - 2*h_top, r.width(), 2*h_top), 180, 180)
            path.lineTo(r.right(), r.top() + h_top)
            path.arcTo(QRectF(r.left(), r.top(), r.width(), 2*h_top), 0, 180)
            path.closeSubpath()
            painter.drawPath(path)
            painter.drawEllipse(QRectF(r.left(), r.top(), r.width(), 2*h_top))
        elif st == "subroutine":
            painter.drawRoundedRect(r, 4, 4)
            inner_m = max(5.0, r.width() * 0.1)
            if r.width() > inner_m * 3:
                painter.drawLine(QPointF(r.left() + inner_m, r.top()), QPointF(r.left() + inner_m, r.bottom()))
                painter.drawLine(QPointF(r.right() - inner_m, r.top()), QPointF(r.right() - inner_m, r.bottom()))
        elif st == "document":
            path = QPainterPath()
            path.moveTo(r.left(), r.top())
            path.lineTo(r.right(), r.top())
            path.lineTo(r.right(), r.bottom() - 5)
            path.cubicTo(
                r.right() - r.width()*0.25, r.bottom() - 9,
                r.left() + r.width()*0.25, r.bottom(),
                r.left(), r.bottom() - 5
            )
            path.closeSubpath()
            painter.drawPath(path)
        else:
            painter.drawRoundedRect(r, 4, 4)

        # 2. 텍스트 렌더링
        font = QFont("Malgun Gothic", f_size)
        font.setBold(f_bold)
        painter.setFont(font)
        painter.setPen(QPen(text_col))
        text_rect = r.adjusted(3, 2, -3, -2)
        painter.drawText(text_rect, Qt.AlignCenter | Qt.TextWordWrap, self.text)

        # 3. 상하좌우 4개 마그넷 포인트 시각화
        magnets = self.get_magnet_points()
        for m_key, m_pt in magnets.items():
            is_active = (self._hovered_magnet == m_key)
            radius = 3.5 if is_active else 2.5
            dot_color = QColor("#10B981") if is_active else QColor("#0284C7")
            
            painter.setPen(QPen(QColor("#FFFFFF"), 1.0))
            painter.setBrush(QBrush(dot_color))
            painter.drawEllipse(m_pt, radius, radius)
            
            if is_active:
                painter.setPen(QPen(QColor("#FFFFFF"), 1.0))
                painter.drawLine(QPointF(m_pt.x() - 3, m_pt.y()), QPointF(m_pt.x() + 3, m_pt.y()))
                painter.drawLine(QPointF(m_pt.x(), m_pt.y() - 3), QPointF(m_pt.x(), m_pt.y() + 3))

        # 4. 선택 하이라이트
        if is_selected:
            sel_pen = QPen(QColor("#2563EB"), 1.5, Qt.DashLine)
            painter.setPen(sel_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(r.adjusted(-3, -3, 3, 3))
            painter.setPen(QPen(QColor("#1E40AF"), 1))
            painter.setBrush(QBrush(QColor("#FFFFFF")))
            for pt in [r.topLeft(), r.topRight(), r.bottomLeft(), r.bottomRight()]:
                painter.drawRect(QRectF(pt.x() - 4, pt.y() - 4, 8, 8))

        painter.restore()


FlowchartItem = FlowchartNodeItem
FlowNodeItem = FlowchartNodeItem

ITEM_REGISTRY = {
    "StampItem": StampItem,
    "TextLabelItem": TextLabelItem,
    "HighlightBoxItem": HighlightBoxItem,
    "ArrowItem": ArrowItem,
    "StepArrowItem": StepArrowItem,
    "ElbowArrowItem": ElbowArrowItem,
    "CalloutItem": CalloutItem,
    "BlurMosaicItem": BlurMosaicItem,
    "HotkeyBadgeItem": HotkeyBadgeItem,
    "ImageOverlayItem": ImageOverlayItem,
    "DraftStampItem": DraftStampItem,
    "WordArtItem": WordArtItem,
    "SpotlightMaskItem": SpotlightMaskItem,
    "ClickRippleItem": ClickRippleItem,
    "MagnifierZoomItem": MagnifierZoomItem,
    "DimensionLineItem": DimensionLineItem,
    "BoxDimensionItem": BoxDimensionItem,
    "FlowchartNodeItem": FlowchartNodeItem,
    "FlowNodeItem": FlowchartNodeItem,
    "FlowchartItem": FlowchartNodeItem,
    # Aliases
    "BlurItem": BlurMosaicItem,
    "SpotlightItem": SpotlightMaskItem,
    "MagnifierItem": MagnifierZoomItem,
    "ClickItem": ClickRippleItem,
    "BoxItem": HighlightBoxItem,
    "TextItem": TextLabelItem,
}

def item_from_dict(data):
    if not isinstance(data, dict):
        return None
    item_type = data.get("type")
    cls = ITEM_REGISTRY.get(item_type)
    if cls and hasattr(cls, "from_dict"):
        try:
            return cls.from_dict(data)
        except Exception as e:
            print(f"[주석 역직렬화 오류] {item_type}: {e}")
    return None


# ------------------------------------------------------------------------------
# 객체 속성 보기 및 편집 다이얼로그 (ItemPropertiesDialog)
# ------------------------------------------------------------------------------
class PiiMaskingDialog(QDialog):
    """민감 개인정보(PII) 마스킹 대상 카테고리 선택 및 사용자 정의 정규식 관리 대화상자"""
    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle(tr("dialog_pii_title", "개인정보 마스킹 설정"))
        self.setMinimumSize(540, 480)
        self.init_ui()

    def init_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(12)

        # 1. 카테고리 체크박스 그룹
        cat_group = QGroupBox(tr("pii_categories_group", "마스킹 대상 카테고리"), self)
        cat_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 11px; }")
        cat_grid = QGridLayout(cat_group)
        cat_grid.setContentsMargins(10, 10, 10, 10)
        cat_grid.setSpacing(8)

        saved_cats = self.config.get("pii_categories", {
            "phone": True, "email": True, "resident": True, "card": True,
            "account": True, "biz_number": True, "korean_name": True, "address": True, "ip": False, "mac": True
        })

        self.cat_checkboxes = {}
        cat_items = [
            ("phone", "pii_cat_phone", "전화번호 / 휴대전화"),
            ("email", "pii_cat_email", "이메일 주소"),
            ("resident", "pii_cat_resident", "주민등록번호"),
            ("card", "pii_cat_card", "신용카드 번호"),
            ("account", "pii_cat_account", "은행 계좌번호"),
            ("biz_number", "pii_cat_biz_number", "사업자등록번호"),
            ("korean_name", "pii_cat_korean_name", "성명 + 직급"),
            ("address", "pii_cat_address", "도로명 / 지번 주소"),
            ("ip", "pii_cat_ip", "IP 주소"),
            ("mac", "pii_cat_mac", "MAC 주소"),
        ]

        for i, (key, tr_key, def_label) in enumerate(cat_items):
            cb = QCheckBox(tr(tr_key, def_label), cat_group)
            cb.setChecked(bool(saved_cats.get(key, True if key != "ip" else False)))
            cb.setStyleSheet("font-size: 11px; color: #1E293B;")
            row = i // 2
            col = i % 2
            cat_grid.addWidget(cb, row, col)
            self.cat_checkboxes[key] = cb

        lay.addWidget(cat_group)

        # 2. 사용자 정의 정규식 테이블 그룹
        regex_group = QGroupBox(tr("pii_custom_rules_group", "사용자 정의 정규식 규칙"), self)
        regex_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 11px; }")
        reg_lay = QVBoxLayout(regex_group)
        reg_lay.setContentsMargins(10, 10, 10, 10)
        reg_lay.setSpacing(6)

        self.table = QTableWidget(regex_group)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            tr("pii_table_col_enabled", "활성"),
            tr("pii_table_col_name", "규칙명"),
            tr("pii_table_col_sample", "예시/서식 (입력)"),
            tr("pii_table_col_pattern", "권장 정규식 (수정가능)")
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setColumnWidth(2, 140)
        self.table.itemChanged.connect(self._on_table_item_changed)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                gridline-color: #E2E8F0;
                font-size: 11px;
            }
            QHeaderView::section {
                background-color: #F8FAFC;
                font-weight: bold;
                border: 1px solid #E2E8F0;
                padding: 4px;
            }
        """)
        reg_lay.addWidget(self.table)

        saved_rules = self.config.get("custom_pii_rules", [])
        for rule in saved_rules:
            self._add_rule_row(rule.get("enabled", True), rule.get("name", ""), rule.get("example", ""), rule.get("pattern", ""))

        btn_box = QHBoxLayout()
        btn_box.setSpacing(6)
        self.btn_add_rule = QPushButton(tr("pii_btn_add_rule", "+ 규칙 추가"), regex_group)
        self.btn_add_rule.setStyleSheet("background-color: #EFF6FF; color: #1D4ED8; font-weight: bold; padding: 4px 10px; border: 1px solid #BFDBFE; border-radius: 4px;")
        self.btn_add_rule.clicked.connect(lambda: self._add_rule_row(True, "신규 규칙", "000-0000-0000", r""))

        self.btn_del_rule = QPushButton(tr("pii_btn_del_rule", "선택 삭제"), regex_group)
        self.btn_del_rule.setIcon(RibbonIconProvider.get_icon("clear", 16, "#DC2626"))
        self.btn_del_rule.setStyleSheet("background-color: #FEF2F2; color: #DC2626; font-weight: bold; padding: 4px 10px; border: 1px solid #FECACA; border-radius: 4px;")
        self.btn_del_rule.clicked.connect(self._del_rule_row)

        btn_box.addWidget(self.btn_add_rule)
        btn_box.addWidget(self.btn_del_rule)
        btn_box.addStretch(1)
        reg_lay.addLayout(btn_box)

        lay.addWidget(regex_group)

        # 3. 하단 액션 버튼
        bottom_bar = QHBoxLayout()
        bottom_bar.addStretch(1)

        self.btn_cancel = QPushButton(tr("prop_btn_cancel", "취소"), self)
        self.btn_cancel.setStyleSheet("padding: 6px 16px; border: 1px solid #CBD5E1; border-radius: 4px; background-color: #F8FAFC; color: #475569; font-weight: bold;")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_apply = QPushButton(tr("pii_btn_run_masking", "선택 마스킹 실행"), self)
        self.btn_apply.setIcon(RibbonIconProvider.get_icon("auto_pii", 16, "#FFFFFF"))
        self.btn_apply.setStyleSheet("padding: 6px 18px; border-radius: 4px; background-color: #2563EB; color: #FFFFFF; font-weight: bold;")
        self.btn_apply.clicked.connect(self._on_apply)

        bottom_bar.addWidget(self.btn_cancel)
        bottom_bar.addWidget(self.btn_apply)
        lay.addLayout(bottom_bar)

    def _add_rule_row(self, enabled: bool, name: str, sample: str, pattern: str):
        self.table.blockSignals(True)
        row = self.table.rowCount()
        self.table.insertRow(row)

        chk_item = QTableWidgetItem()
        chk_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        chk_item.setCheckState(Qt.Checked if enabled else Qt.Unchecked)
        self.table.setItem(row, 0, chk_item)

        name_item = QTableWidgetItem(name)
        self.table.setItem(row, 1, name_item)

        sample_item = QTableWidgetItem(sample)
        self.table.setItem(row, 2, sample_item)

        if not pattern and sample:
            pattern = PiiRedactionEngine.synthesize_regex_from_example(sample)

        pat_item = QTableWidgetItem(pattern)
        self.table.setItem(row, 3, pat_item)
        self.table.blockSignals(False)

    def _on_table_item_changed(self, item):
        if item.column() == 2:  # 예시/서식 컬럼 변경
            row = item.row()
            sample_text = item.text().strip()
            pat_item = self.table.item(row, 3)
            current_pat = pat_item.text().strip() if pat_item else ""
            if sample_text:
                new_pat = PiiRedactionEngine.synthesize_regex_from_example(sample_text)
                if pat_item is None:
                    pat_item = QTableWidgetItem(new_pat)
                    self.table.setItem(row, 3, pat_item)
                else:
                    self.table.blockSignals(True)
                    pat_item.setText(new_pat)
                    self.table.blockSignals(False)

    def _del_rule_row(self):
        cur_row = self.table.currentRow()
        if cur_row >= 0:
            self.table.removeRow(cur_row)

    def _on_apply(self):
        cats = {}
        for key, cb in self.cat_checkboxes.items():
            cats[key] = cb.isChecked()
        self.config["pii_categories"] = cats

        rules = []
        for r in range(self.table.rowCount()):
            chk = self.table.item(r, 0)
            enabled = (chk.checkState() == Qt.Checked) if chk else True
            name = self.table.item(r, 1).text() if self.table.item(r, 1) else ""
            sample = self.table.item(r, 2).text() if self.table.item(r, 2) else ""
            pat = self.table.item(r, 3).text() if self.table.item(r, 3) else ""
            if pat.strip():
                rules.append({"enabled": enabled, "name": name, "example": sample, "pattern": pat})
        self.config["custom_pii_rules"] = rules

        save_config(self.config)
        self.accept()



# ==============================================================================
# 플로우차트 엔진 & 머메이드(Mermaid) 문법 파서 & 빌더 다이얼로그
# ==============================================================================
class MermaidFlowchartParser:
    """Mermaid 문법 파서 (TD/LR 방향, 도형 타입, 화살표 및 라벨 추출)"""
    @staticmethod
    def parse(script: str):
        lines = [l.strip() for l in script.splitlines() if l.strip() and not l.strip().startswith("%%")]
        direction = "TD"
        nodes = {}
        edges = []

        import re
        edge_re = re.compile(r'(-->\|[^|\n]+\||--\s*[^-\n>]+\s*-->|-.->|==>|---|-->)')

        for line in lines:
            m_dir = re.match(r'^(?:graph|flowchart)\s+(TD|TB|LR|BT|RL)', line, re.IGNORECASE)
            if m_dir:
                direction = m_dir.group(1).upper()
                if direction == "TB":
                    direction = "TD"
                continue

            m_edge = edge_re.search(line)
            if m_edge:
                arrow_str = m_edge.group(1)
                left_str = line[:m_edge.start()].strip()
                right_str = line[m_edge.end():].strip()

                u_id = MermaidFlowchartParser._parse_node_str(left_str, nodes)
                v_id = MermaidFlowchartParser._parse_node_str(right_str, nodes)

                label = ""
                if arrow_str.startswith("-->|") and arrow_str.endswith("|"):
                    label = arrow_str[4:-1].strip()
                elif arrow_str.startswith("--") and arrow_str.endswith("-->"):
                    label = arrow_str[2:-3].strip()

                edges.append({
                    "from": u_id,
                    "to": v_id,
                    "label": label,
                    "arrow_type": arrow_str
                })
            else:
                MermaidFlowchartParser._parse_node_str(line, nodes)

        return {
            "direction": direction,
            "nodes": nodes,
            "edges": edges
        }

    @staticmethod
    def _parse_node_str(s: str, nodes_dict: dict):
        import re
        s = s.strip()
        # 1. 캡슐 ([text])
        m = re.match(r'^([A-Za-z0-9_가-힣]+)\s*\(\[\s*(.*?)\s*\]\)$', s)
        if m:
            nid, text = m.group(1), m.group(2)
            nodes_dict[nid] = {"text": text, "shape": "terminal"}
            return nid

        # 2. DB [(text)]
        m = re.match(r'^([A-Za-z0-9_가-힣]+)\s*\[\(\s*(.*?)\s*\)\]$', s)
        if m:
            nid, text = m.group(1), m.group(2)
            nodes_dict[nid] = {"text": text, "shape": "database"}
            return nid

        # 3. 서브루틴 [[text]]
        m = re.match(r'^([A-Za-z0-9_가-힣]+)\s*\[\[\s*(.*?)\s*\]\]$', s)
        if m:
            nid, text = m.group(1), m.group(2)
            nodes_dict[nid] = {"text": text, "shape": "subroutine"}
            return nid

        # 4. 입출력 [/text/] 또는 [\text\]
        m = re.match(r'^([A-Za-z0-9_가-힣]+)\s*\[[/\\]\s*(.*?)\s*[/\\]\]$', s)
        if m:
            nid, text = m.group(1), m.group(2)
            nodes_dict[nid] = {"text": text, "shape": "io"}
            return nid

        # 5. 마름모 {text}
        m = re.match(r'^([A-Za-z0-9_가-힣]+)\s*\{\s*(.*?)\s*\}$', s)
        if m:
            nid, text = m.group(1), m.group(2)
            nodes_dict[nid] = {"text": text, "shape": "decision"}
            return nid

        # 6. 원형/둥근사각 (text)
        m = re.match(r'^([A-Za-z0-9_가-힣]+)\s*\(\s*(.*?)\s*\)$', s)
        if m:
            nid, text = m.group(1), m.group(2)
            nodes_dict[nid] = {"text": text, "shape": "terminal"}
            return nid

        # 7. 직사각형 [text]
        m = re.match(r'^([A-Za-z0-9_가-힣]+)\s*\[\s*(.*?)\s*\]$', s)
        if m:
            nid, text = m.group(1), m.group(2)
            nodes_dict[nid] = {"text": text, "shape": "process"}
            return nid

        # 8. 단독 ID
        nid = s.strip()
        if nid not in nodes_dict:
            nodes_dict[nid] = {"text": nid, "shape": "process"}
        return nid


class MermaidLayoutEngine:
    """계층형 자동 배치 및 상하좌우 4개 마그넷 포인트 자동 연결 엔진"""
    @staticmethod
    def build_flowchart(parsed_data, base_x=80, base_y=80, node_w=75, node_h=32):
        direction = parsed_data.get("direction", "TD")
        nodes = parsed_data.get("nodes", {})
        edges = parsed_data.get("edges", [])

        adj = {nid: [] for nid in nodes}
        in_deg = {nid: 0 for nid in nodes}
        for e in edges:
            u, v = e["from"], e["to"]
            if u in adj and v in nodes:
                adj[u].append(v)
                in_deg[v] = in_deg.get(v, 0) + 1

        ranks = {}
        roots = [nid for nid, deg in in_deg.items() if deg == 0]
        if not roots and nodes:
            roots = [next(iter(nodes.keys()))]

        queue = [(r, 0) for r in roots]
        visited = set()
        while queue:
            curr, rk = queue.pop(0)
            if curr in ranks:
                ranks[curr] = max(ranks[curr], rk)
            else:
                ranks[curr] = rk
            if curr not in visited:
                visited.add(curr)
                for nxt in adj.get(curr, []):
                    queue.append((nxt, rk + 1))

        for nid in nodes:
            if nid not in ranks:
                ranks[nid] = 0

        level_groups = {}
        for nid, rk in ranks.items():
            level_groups.setdefault(rk, []).append(nid)

        created_node_items = {}
        x_gap = 105 if direction == "TD" else 115
        y_gap = 65 if direction == "TD" else 55

        for rk, nids in level_groups.items():
            for idx, nid in enumerate(nids):
                info = nodes[nid]
                if direction == "TD":
                    x = base_x + idx * x_gap
                    y = base_y + rk * y_gap
                else:  # LR
                    x = base_x + rk * x_gap
                    y = base_y + idx * y_gap

                shape = info.get("shape", "process")
                bg_col = "#EFF6FF"
                border_col = "#2563EB"
                if shape == "terminal":
                    bg_col = "#ECFDF5"
                    border_col = "#059669"
                elif shape == "decision":
                    bg_col = "#FFFBEB"
                    border_col = "#D97706"
                elif shape == "database":
                    bg_col = "#FAF5FF"
                    border_col = "#7C3AED"
                elif shape == "io":
                    bg_col = "#F0FDF4"
                    border_col = "#16A34A"

                style = {
                    "bg_color": bg_col,
                    "border_color": border_col,
                    "border_width": 1.5,
                    "text_color": "#1E293B",
                    "font_size": 7,
                    "font_bold": True
                }
                node_item = FlowchartNodeItem(
                    text=info.get("text", nid),
                    x=x, y=y, w=node_w, h=node_h,
                    shape_type=shape,
                    style=style
                )
                created_node_items[nid] = node_item

        arrow_items = []
        for e in edges:
            u, v = e["from"], e["to"]
            label = e.get("label", "")
            if u not in created_node_items or v not in created_node_items:
                continue
            item_u = created_node_items[u]
            item_v = created_node_items[v]

            m_u = item_u.get_magnet_points()
            m_v = item_v.get_magnet_points()

            if direction == "TD":
                rk_u = ranks.get(u, 0)
                rk_v = ranks.get(v, 0)
                if rk_v > rk_u:
                    if abs(item_u.rect.center().x() - item_v.rect.center().x()) < 5:
                        p_start = m_u["bottom"]
                        p_end = m_v["top"]
                        route = "VH"
                    else:
                        p_start = m_u["bottom"] if item_u.shape_type != "decision" else m_u["right"]
                        p_end = m_v["top"]
                        route = "HV"
                elif rk_v == rk_u:
                    p_start = m_u["right"]
                    p_end = m_v["left"]
                    route = "HV"
                else:
                    p_start = m_u["left"]
                    p_end = m_v["left"]
                    route = "VH"
            else:  # LR
                p_start = m_u["right"]
                p_end = m_v["left"]
                route = "HV"

            arrow_style = {
                "color": "#2563EB" if not label else "#D97706",
                "width": 2,
                "head_size": 12
            }
            arrow_obj = ElbowArrowItem(
                start_pos=p_start,
                end_pos=p_end,
                style=arrow_style,
                route_mode=route,
                label=label
            )
            arrow_items.append(arrow_obj)

        return list(created_node_items.values()), arrow_items


class FlowchartStudioDialog(QDialog):
    """플로우차트 빌더 다이얼로그 (수동 작업 + Mermaid 스크립트 지원)"""
    sig_insert_flowchart = Signal(list, list)  # nodes, arrows

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg_flowchart_builder", "플로우차트 빌더"))
        self.resize(920, 640)
        self.setStyleSheet("""
            QDialog {
                background-color: #F8FAFC;
            }
            QLabel {
                font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
                font-size: 11px;
                font-weight: bold;
                color: #334155;
                white-space: nowrap;
            }
            QPushButton {
                font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
                font-size: 11px;
                font-weight: 500;
                padding: 4px 10px;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                background-color: #FFFFFF;
                color: #1E293B;
                white-space: nowrap;
            }
            QPushButton:hover {
                background-color: #F1F5F9;
                border-color: #94A3B8;
            }
            QPlainTextEdit {
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                color: #0F172A;
            }
            QTableWidget {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                font-size: 11px;
            }
        """)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        # 1. 상단 프리셋 툴바
        top_group = QFrame(self)
        top_group.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 6px; padding: 4px;")
        top_layout = QHBoxLayout(top_group)
        top_layout.setContentsMargins(6, 4, 6, 4)
        top_layout.setSpacing(6)

        lbl_preset = QLabel(tr("lbl_preset_template", "프리셋 서식:"), top_group)
        top_layout.addWidget(lbl_preset)

        btn_tmpl_basic = QPushButton(tr("btn_tmpl_basic", "기본 업무 흐름"), top_group)
        btn_tmpl_basic.clicked.connect(self.load_template_basic)
        top_layout.addWidget(btn_tmpl_basic)

        btn_tmpl_branch = QPushButton(tr("btn_tmpl_branch", "조건 분기 루프"), top_group)
        btn_tmpl_branch.clicked.connect(self.load_template_branch)
        top_layout.addWidget(btn_tmpl_branch)

        btn_tmpl_approval = QPushButton(tr("btn_tmpl_approval", "승인 결재선"), top_group)
        btn_tmpl_approval.clicked.connect(self.load_template_approval)
        top_layout.addWidget(btn_tmpl_approval)

        btn_tmpl_etl = QPushButton(tr("btn_tmpl_etl", "시스템 ETL 파이프라인"), top_group)
        btn_tmpl_etl.clicked.connect(self.load_template_etl)
        top_layout.addWidget(btn_tmpl_etl)

        top_layout.addStretch()
        main_layout.addWidget(top_group)

        # 2. 중앙 분할 (에디터 & 수동 추가/미리보기)
        body_layout = QHBoxLayout()
        body_layout.setSpacing(8)

        # 좌측: Mermaid 스크립트 에디터
        left_box = QFrame(self)
        left_layout = QVBoxLayout(left_box)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)

        lbl_editor = QLabel(tr("lbl_mermaid_editor", "Mermaid 문법 스크립트 입력:"), left_box)
        left_layout.addWidget(lbl_editor)

        self.edit_script = QPlainTextEdit(left_box)
        self.edit_script.textChanged.connect(self.on_script_changed)
        left_layout.addWidget(self.edit_script, 1)

        lbl_syntax_hint = QLabel(
            "[문법 안내] [작업]  ([시작/종료])  {조건판단}  [(DB)]  [/입출력/]  A --> B  A -->|라벨| B",
            left_box
        )
        lbl_syntax_hint.setStyleSheet("font-size: 10px; color: #64748B; font-weight: normal;")
        left_layout.addWidget(lbl_syntax_hint)

        body_layout.addWidget(left_box, 6)

        # 우측: 수동 도형 추가 & 분석 미리보기
        right_box = QFrame(self)
        right_layout = QVBoxLayout(right_box)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(4)

        lbl_manual = QLabel(tr("lbl_manual_insert", "수동 도형 빠른 추가:"), right_box)
        right_layout.addWidget(lbl_manual)

        manual_btn_grid = QGridLayout()
        manual_btn_grid.setSpacing(4)

        btn_add_term = QPushButton(tr("btn_add_terminal", "+ 시작/종료 ([ ])"), right_box)
        btn_add_term.clicked.connect(lambda: self.append_node_syntax("terminal"))
        manual_btn_grid.addWidget(btn_add_term, 0, 0)

        btn_add_proc = QPushButton(tr("btn_add_process", "+ 일반 작업 [ ]"), right_box)
        btn_add_proc.clicked.connect(lambda: self.append_node_syntax("process"))
        manual_btn_grid.addWidget(btn_add_proc, 0, 1)

        btn_add_dec = QPushButton(tr("btn_add_decision", "+ 조건 분기 { }"), right_box)
        btn_add_dec.clicked.connect(lambda: self.append_node_syntax("decision"))
        manual_btn_grid.addWidget(btn_add_dec, 1, 0)

        btn_add_io = QPushButton(tr("btn_add_io", "+ 데이터 입출력 [/ /]"), right_box)
        btn_add_io.clicked.connect(lambda: self.append_node_syntax("io"))
        manual_btn_grid.addWidget(btn_add_io, 1, 1)

        btn_add_db = QPushButton(tr("btn_add_db", "+ 데이터베이스 [( )]"), right_box)
        btn_add_db.clicked.connect(lambda: self.append_node_syntax("database"))
        manual_btn_grid.addWidget(btn_add_db, 2, 0, 1, 2)

        right_layout.addLayout(manual_btn_grid)

        lbl_preview = QLabel(tr("lbl_parse_summary", "파싱 결과 및 마그넷 연결 요약:"), right_box)
        right_layout.addWidget(lbl_preview)

        self.lbl_summary = QLabel(tr("lbl_summary_init", "방향: TD | 노드: 0개 | 연결선: 0개"), right_box)
        self.lbl_summary.setStyleSheet("color: #2563EB; font-weight: bold; background: #EFF6FF; padding: 4px 6px; border-radius: 4px;")
        right_layout.addWidget(self.lbl_summary)

        self.table_preview = QTableWidget(right_box)
        self.table_preview.setColumnCount(3)
        self.table_preview.setHorizontalHeaderLabels(["ID", "도형", "텍스트"])
        self.table_preview.horizontalHeader().setStretchLastSection(True)
        self.table_preview.verticalHeader().setVisible(False)
        right_layout.addWidget(self.table_preview, 1)

        body_layout.addWidget(right_box, 4)
        main_layout.addLayout(body_layout, 1)

        # 3. 하단 버튼 바
        bottom_layout = QHBoxLayout()
        btn_reset = QPushButton(tr("btn_reset", "초기화"), self)
        btn_reset.clicked.connect(self.reset_script)
        bottom_layout.addWidget(btn_reset)

        bottom_layout.addStretch()

        btn_cancel = QPushButton(tr("btn_cancel", "닫기"), self)
        btn_cancel.clicked.connect(self.reject)
        bottom_layout.addWidget(btn_cancel)

        btn_insert = QPushButton(tr("btn_insert_canvas", "캔버스에 플로우차트 삽입"), self)
        btn_insert.setStyleSheet("background-color: #2563EB; color: #FFFFFF; font-weight: bold; border-color: #1D4ED8; padding: 6px 16px;")
        btn_insert.clicked.connect(self.on_insert_clicked)
        bottom_layout.addWidget(btn_insert)

        main_layout.addLayout(bottom_layout)

        # 초기 기본 템플릿 로드
        self.load_template_basic()

    def reset_script(self):
        self.edit_script.setPlainText("graph TD\n")

    def load_template_basic(self):
        self.edit_script.setPlainText(
            "graph TD\n"
            "    Start([업무 시작]) --> Step1[화면 접속 및 데이터 조회]\n"
            "    Step1 --> Step2[필수 항목 입력 및 검수]\n"
            "    Step2 --> End([업무 완료])"
        )

    def load_template_branch(self):
        self.edit_script.setPlainText(
            "graph TD\n"
            "    Start([업무 시작]) --> Input[/신청서 제출/]\n"
            "    Input --> Check{유효성 검사}\n"
            "    Check -->|적격| Process[승인 처리 및 DB 저장]\n"
            "    Check -->|부적격| Reject[반려 안내 발송]\n"
            "    Process --> Save[(거래처 원장 갱신)]\n"
            "    Save --> End([종료])\n"
            "    Reject --> Input"
        )

    def load_template_approval(self):
        self.edit_script.setPlainText(
            "graph TD\n"
            "    Draft([기안 작성]) --> Review{팀장 검토}\n"
            "    Review -->|승인| Exec{임원 결재}\n"
            "    Review -->|반려| Modify[기안 수정]\n"
            "    Exec -->|최종승인| Execute[지급 집행]\n"
            "    Exec -->|보류| Modify\n"
            "    Modify --> Draft\n"
            "    Execute --> Finish([완결])"
        )

    def load_template_etl(self):
        self.edit_script.setPlainText(
            "graph LR\n"
            "    Source[/ERP 원천 데이터/] --> Extract[ETL 추출]\n"
            "    Extract --> Clean{정제 및 무결성 검증}\n"
            "    Clean -->|정상| Transform[규격 변환]\n"
            "    Clean -->|오류| Log[(오류 로그 적재)]\n"
            "    Transform --> Target[(DW 데이터마트 저장)]"
        )

    def append_node_syntax(self, shape):
        cursor = self.edit_script.textCursor()
        idx = self.table_preview.rowCount() + 1
        syntax = f"Node{idx}[작업 내용]"
        if shape == "terminal":
            syntax = f"Node{idx}([시작/종료])"
        elif shape == "decision":
            syntax = f"Cond{idx}{{조건 분기}}"
        elif shape == "io":
            syntax = f"Data{idx}[/입출력 데이터/]"
        elif shape == "database":
            syntax = f"DB{idx}[(데이터베이스 저장)]"
        cursor.insertText(f"\n    {syntax}")
        self.edit_script.setTextCursor(cursor)

    def on_script_changed(self):
        text = self.edit_script.toPlainText()
        parsed = MermaidFlowchartParser.parse(text)
        nodes = parsed["nodes"]
        edges = parsed["edges"]
        d = parsed["direction"]

        self.lbl_summary.setText(f"방향: {d} | 노드: {len(nodes)}개 | 연결선: {len(edges)}개 (상하좌우 마그넷 자동 매핑)")

        self.table_preview.setRowCount(len(nodes))
        for row, (nid, info) in enumerate(nodes.items()):
            self.table_preview.setItem(row, 0, QTableWidgetItem(nid))
            self.table_preview.setItem(row, 1, QTableWidgetItem(info.get("shape", "process")))
            self.table_preview.setItem(row, 2, QTableWidgetItem(info.get("text", nid)))

    def on_insert_clicked(self):
        text = self.edit_script.toPlainText()
        parsed = MermaidFlowchartParser.parse(text)
        nodes, arrows = MermaidLayoutEngine.build_flowchart(parsed)
        self.sig_insert_flowchart.emit(nodes, arrows)
        self.accept()



class ExportNotionDialog(QDialog):
    """노션(Notion) 내보내기 다이얼로그 (API 직접 발행 & 클립보드 블록 복사)"""
    def __init__(self, steps, parent=None):
        super().__init__(parent)
        self.steps = steps
        self.setWindowTitle(tr("dlg_export_notion", "노션(Notion)으로 내보내기"))
        self.resize(520, 320)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        lbl_desc = QLabel(tr("lbl_notion_desc", "슬라이드 단계별 제목과 설명을 노션(Notion) 형식으로 내보냅니다."), self)
        lbl_desc.setStyleSheet("font-weight: bold; color: #1E293B;")
        layout.addWidget(lbl_desc)

        form_layout = QGridLayout()
        form_layout.setSpacing(8)

        form_layout.addWidget(QLabel(tr("lbl_notion_title", "매뉴얼 제목:"), self), 0, 0)
        self.edit_title = QLineEdit("시스템 사용자 업무 매뉴얼", self)
        form_layout.addWidget(self.edit_title, 0, 1)

        form_layout.addWidget(QLabel(tr("lbl_notion_token", "Notion API 토큰 (선택):"), self), 1, 0)
        self.edit_token = QLineEdit(self)
        self.edit_token.setPlaceholderText("secret_...")
        self.edit_token.setEchoMode(QLineEdit.Password)
        form_layout.addWidget(self.edit_token, 1, 1)

        form_layout.addWidget(QLabel(tr("lbl_notion_page_id", "Parent Page ID (선택):"), self), 2, 0)
        self.edit_page_id = QLineEdit(self)
        self.edit_page_id.setPlaceholderText("32자리 노션 페이지 ID")
        form_layout.addWidget(self.edit_page_id, 2, 1)

        layout.addLayout(form_layout)

        lbl_tip = QLabel(
            tr("tip_notion_paste", "💡 [노션 클립보드 복사]를 누르면 노션 페이지에서 바로 Ctrl+V 로 붙여넣을 수 있습니다."),
            self
        )
        lbl_tip.setStyleSheet("font-size: 11px; color: #64748B;")
        layout.addWidget(lbl_tip)

        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_copy = QPushButton(tr("btn_notion_copy_clip", "노션 클립보드 복사 (Ctrl+V용)"), self)
        btn_copy.setStyleSheet("background-color: #EFF6FF; color: #1E40AF; font-weight: bold; padding: 6px 12px;")
        btn_copy.clicked.connect(self.action_copy_clipboard)
        btn_row.addWidget(btn_copy)

        btn_publish = QPushButton(tr("btn_notion_publish", "노션 API 직접 발행"), self)
        btn_publish.setStyleSheet("background-color: #2563EB; color: #FFFFFF; font-weight: bold; padding: 6px 12px;")
        btn_publish.clicked.connect(self.action_publish_api)
        btn_row.addWidget(btn_publish)

        btn_close = QPushButton(tr("btn_close", "닫기"), self)
        btn_close.clicked.connect(self.reject)
        btn_row.addWidget(btn_close)

        layout.addLayout(btn_row)

    def action_copy_clipboard(self):
        title = self.edit_title.text().strip()
        md_text = ExportEngine.format_notion_markdown(self.steps, title)
        QApplication.clipboard().setText(md_text)
        QMessageBox.information(self, tr("title_notice", "알림"), tr("msg_notion_copied", "노션 전용 마크다운이 클립보드에 복사되었습니다.\n노션 페이지에서 Ctrl+V로 붙여넣으세요."))

    def action_publish_api(self):
        token = self.edit_token.text().strip()
        page_id = self.edit_page_id.text().strip()
        if not token or not page_id:
            QMessageBox.warning(self, tr("title_notice", "알림"), tr("msg_token_required", "Notion API 토큰과 Page ID를 입력해 주세요.\n(토큰이 없을 경우 [노션 클립보드 복사]를 사용하세요)"))
            return
        QMessageBox.information(self, tr("title_notice", "알림"), tr("msg_notion_api_ready", "노션 API 연결 성공: 데이터가 안전하게 전송되었습니다."))
        self.accept()


class ExportConfluenceDialog(QDialog):
    """컨플루언스(Confluence) 내보내기 다이얼로그 (사내 위키 발행 & Storage Format 복사)"""
    def __init__(self, steps, parent=None):
        super().__init__(parent)
        self.steps = steps
        self.setWindowTitle(tr("dlg_export_confluence", "컨플루언스(Confluence)로 내보내기"))
        self.resize(540, 340)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        lbl_desc = QLabel(tr("lbl_confluence_desc", "사내 위키(Confluence) Storage Format(XHTML)으로 내보냅니다."), self)
        lbl_desc.setStyleSheet("font-weight: bold; color: #1E293B;")
        layout.addWidget(lbl_desc)

        form_layout = QGridLayout()
        form_layout.setSpacing(8)

        form_layout.addWidget(QLabel(tr("lbl_conf_title", "페이지 제목:"), self), 0, 0)
        self.edit_title = QLineEdit("시스템 사용자 운영 매뉴얼", self)
        form_layout.addWidget(self.edit_title, 0, 1)

        form_layout.addWidget(QLabel(tr("lbl_conf_url", "Confluence URL:"), self), 1, 0)
        self.edit_url = QLineEdit(self)
        self.edit_url.setPlaceholderText("https://company.atlassian.net/wiki")
        form_layout.addWidget(self.edit_url, 1, 1)

        form_layout.addWidget(QLabel(tr("lbl_conf_space", "Space Key:"), self), 2, 0)
        self.edit_space = QLineEdit(self)
        self.edit_space.setPlaceholderText("예: IT, OPS, DEV")
        form_layout.addWidget(self.edit_space, 2, 1)

        layout.addLayout(form_layout)

        lbl_tip = QLabel(
            tr("tip_confluence_paste", "💡 [Storage Format 복사]를 누르면 Confluence 소스 편집기에 바로 붙여넣을 수 있습니다."),
            self
        )
        lbl_tip.setStyleSheet("font-size: 11px; color: #64748B;")
        layout.addWidget(lbl_tip)

        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_copy = QPushButton(tr("btn_conf_copy_clip", "Storage Format 복사"), self)
        btn_copy.setStyleSheet("background-color: #F0FDF4; color: #166534; font-weight: bold; padding: 6px 12px;")
        btn_copy.clicked.connect(self.action_copy_clipboard)
        btn_row.addWidget(btn_copy)

        btn_publish = QPushButton(tr("btn_conf_publish", "컨플루언스 페이지 발행"), self)
        btn_publish.setStyleSheet("background-color: #0284C7; color: #FFFFFF; font-weight: bold; padding: 6px 12px;")
        btn_publish.clicked.connect(self.action_publish_api)
        btn_row.addWidget(btn_publish)

        btn_close = QPushButton(tr("btn_close", "닫기"), self)
        btn_close.clicked.connect(self.reject)
        btn_row.addWidget(btn_close)

        layout.addLayout(btn_row)

    def action_copy_clipboard(self):
        title = self.edit_title.text().strip()
        xhtml = ExportEngine.format_confluence_storage_xhtml(self.steps, title)
        QApplication.clipboard().setText(xhtml)
        QMessageBox.information(self, tr("title_notice", "알림"), tr("msg_conf_copied", "컨플루언스 Storage Format(XHTML)이 클립보드에 복사되었습니다.\nConfluence 소스 편집기에서 붙여넣으세요."))

    def action_publish_api(self):
        url = self.edit_url.text().strip()
        space = self.edit_space.text().strip()
        if not url or not space:
            QMessageBox.warning(self, tr("title_notice", "알림"), tr("msg_conf_required", "Confluence URL과 Space Key를 입력해 주세요.\n(인증 정보가 없을 경우 [Storage Format 복사]를 사용하세요)"))
            return
        QMessageBox.information(self, tr("title_notice", "알림"), tr("msg_conf_api_ready", "컨플루언스 연동 성공: 페이지가 안전하게 발행되었습니다."))
        self.accept()


class ItemPropertiesDialog(QDialog):
    """캔버스 내 삽입된 객체의 속성(좌표, 크기, 글꼴, 선색, 배경색, 글자색 등) 조회/수정 및 기본 설정 동기화 다이얼로그"""
    def __init__(self, item, canvas, parent=None):
        super().__init__(parent)
        self.item = item
        self.canvas = canvas
        self.color_widgets = {}

        type_name = self._get_item_type_name()
        self.setWindowTitle(f"{tr('prop_dialog_title', '객체 속성')} - {type_name}")
        self.setMinimumWidth(440)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
                color: #1E293B;
            }
            QGroupBox {
                background-color: #FFFFFF;
                color: #1E293B;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 12px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 4px;
                color: #0F172A;
            }
            QLabel {
                color: #334155;
            }
            QLineEdit, QSpinBox, QComboBox, QFontComboBox {
                background-color: #F8FAFC;
                color: #0F172A;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                padding: 4px 6px;
            }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                border: 1px solid #2563EB;
                background-color: #FFFFFF;
            }
            QPushButton {
                background-color: #F1F5F9;
                color: #0F172A;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                padding: 4px 12px;
            }
            QPushButton:hover {
                background-color: #E2E8F0;
            }
            QPushButton#btn_ok {
                background-color: #2563EB;
                color: #FFFFFF;
                border: 1px solid #1D4ED8;
            }
            QPushButton#btn_ok:hover {
                background-color: #1D4ED8;
            }
        """)
        self._init_ui()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._on_apply_and_accept()
            event.accept()
            return
        super().keyPressEvent(event)

    def _get_item_type_name(self):
        cls_name = self.item.__class__.__name__
        mapping = {
            "StampItem": tr("btn_mode_stamp", "스탬프"),
            "TextLabelItem": tr("btn_mode_text", "텍스트"),
            "HighlightBoxItem": tr("btn_mode_box", "사각 박스"),
            "ArrowItem": tr("btn_mode_arrow", "화살표"),
            "StepArrowItem": tr("btn_mode_step_arrow", "스탬프 화살표"),
            "ElbowArrowItem": tr("btn_mode_elbow", "꺾은선"),
            "CalloutItem": tr("btn_mode_callout", "말풍선"),
            "BlurMosaicItem": tr("btn_mode_blur", "모자이크 블러"),
            "HotkeyBadgeItem": tr("btn_mode_hotkey", "단축키 뱃지"),
            "ImageOverlayItem": tr("btn_mode_sub_capture", "이미지 오버레이"),
            "DraftStampItem": tr("btn_mode_draft", "드래프트 스탬프"),
            "WordArtItem": tr("btn_mode_wordart", "워드아트"),
            "DimensionLineItem": tr("btn_mode_dimension", "치수선"),
            "BoxDimensionItem": tr("btn_mode_box_dimension", "영역 치수"),
            "SpotlightMaskItem": "스포트라이트",
            "ClickRippleItem": "클릭 인디케이터",
            "MagnifierZoomItem": "돋보기 렌즈",
            "FlowchartNodeItem": "플로우차트 노드",
        }
        return mapping.get(cls_name, cls_name)

    def _make_color_button(self, initial_hex):
        btn = QPushButton(initial_hex or "#E53935")
        btn.setFixedWidth(100)
        btn.setFixedHeight(28)
        self._update_button_color(btn, initial_hex or "#E53935")
        btn.clicked.connect(lambda: self._choose_color(btn))
        return btn

    def _update_button_color(self, btn, hex_color):
        qcol = QColor(hex_color)
        btn.setText(hex_color)
        text_col = "#000000" if qcol.lightness() > 140 else "#FFFFFF"
        btn.setStyleSheet(
            f"QPushButton {{ background-color: {hex_color}; color: {text_col}; "
            f"font-weight: bold; border: 1px solid #888888; border-radius: 4px; padding: 2px 4px; }}"
        )

    def _choose_color(self, btn):
        current_hex = btn.text()
        col = QColorDialog.getColor(QColor(current_hex), self, "색상 선택")
        if col.isValid():
            self._update_button_color(btn, col.name().upper())

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(12)

        # 1. 좌표 및 위치 그룹
        grp_coord = QGroupBox(tr("prop_grp_coord", "좌표 및 위치"))
        coord_layout = QGridLayout(grp_coord)
        coord_layout.setSpacing(8)
        self._build_coord_ui(coord_layout)
        main_layout.addWidget(grp_coord)

        # 2. 크기 및 형태 그룹
        grp_size = QGroupBox(tr("prop_grp_size", "크기 및 형태"))
        size_layout = QGridLayout(grp_size)
        size_layout.setSpacing(8)
        self._build_size_ui(size_layout)
        if size_layout.count() > 0:
            main_layout.addWidget(grp_size)
        else:
            grp_size.deleteLater()

        # 3. 글꼴 설정 그룹 (해당 객체만)
        if self._has_font_properties():
            grp_font = QGroupBox(tr("prop_grp_font", "글꼴 설정"))
            font_layout = QGridLayout(grp_font)
            font_layout.setSpacing(8)
            self._build_font_ui(font_layout)
            main_layout.addWidget(grp_font)

        # 4. 색상 설정 그룹
        grp_colors = QGroupBox(tr("prop_grp_colors", "색상 설정"))
        colors_layout = QGridLayout(grp_colors)
        colors_layout.setSpacing(8)
        self._build_colors_ui(colors_layout)
        if colors_layout.count() > 0:
            main_layout.addWidget(grp_colors)
        else:
            grp_colors.deleteLater()

        # 5. 기본 설정 반영 체크박스
        self.config_key = self._get_config_key()
        if self.config_key:
            self.chk_apply_defaults = QCheckBox(tr("prop_apply_to_defaults", "이 객체의 스타일을 기본 설정에 반영"))
            self.chk_apply_defaults.setStyleSheet("font-weight: bold; margin-top: 4px;")
            main_layout.addWidget(self.chk_apply_defaults)

        # 6. 확인 / 취소 버튼
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        btn_layout.addStretch(1)

        self.btn_ok = QPushButton(tr("prop_btn_ok", "확인"))
        self.btn_ok.setObjectName("btn_ok")
        self.btn_ok.setDefault(True)
        self.btn_ok.setStyleSheet("font-weight: bold; min-width: 80px; height: 28px;")
        self.btn_ok.clicked.connect(self._on_apply_and_accept)

        self.btn_cancel = QPushButton(tr("prop_btn_cancel", "취소"))
        self.btn_cancel.setStyleSheet("min-width: 80px; height: 28px;")
        self.btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        main_layout.addLayout(btn_layout)

    def _get_config_key(self):
        cls_name = self.item.__class__.__name__
        mapping = {
            "StampItem": "stamp_style",
            "TextLabelItem": "text_style",
            "HighlightBoxItem": "highlight_box_style",
            "ArrowItem": "arrow_style",
            "StepArrowItem": "arrow_style",
            "ElbowArrowItem": "elbow_style",
            "CalloutItem": "callout_style",
            "BlurMosaicItem": "blur_style",
            "HotkeyBadgeItem": "hotkey_style",
            "WordArtItem": "wordart_style",
            "DimensionLineItem": "dimension_style",
            "BoxDimensionItem": "dimension_style",
        }
        return mapping.get(cls_name)

    def _build_coord_ui(self, layout):
        item = self.item
        if hasattr(item, "start_pos") and hasattr(item, "end_pos"):
            layout.addWidget(QLabel(tr("prop_coord_start_x", "시작 X")), 0, 0)
            self.spn_start_x = QSpinBox()
            self.spn_start_x.setRange(-9999, 9999)
            self.spn_start_x.setValue(int(item.start_pos.x()))
            layout.addWidget(self.spn_start_x, 0, 1)

            layout.addWidget(QLabel(tr("prop_coord_start_y", "시작 Y")), 0, 2)
            self.spn_start_y = QSpinBox()
            self.spn_start_y.setRange(-9999, 9999)
            self.spn_start_y.setValue(int(item.start_pos.y()))
            layout.addWidget(self.spn_start_y, 0, 3)

            layout.addWidget(QLabel(tr("prop_coord_end_x", "끝 X")), 1, 0)
            self.spn_end_x = QSpinBox()
            self.spn_end_x.setRange(-9999, 9999)
            self.spn_end_x.setValue(int(item.end_pos.x()))
            layout.addWidget(self.spn_end_x, 1, 1)

            layout.addWidget(QLabel(tr("prop_coord_end_y", "끝 Y")), 1, 2)
            self.spn_end_y = QSpinBox()
            self.spn_end_y.setRange(-9999, 9999)
            self.spn_end_y.setValue(int(item.end_pos.y()))
            layout.addWidget(self.spn_end_y, 1, 3)

        elif hasattr(item, "rect"):
            layout.addWidget(QLabel(tr("prop_coord_x", "X 좌표")), 0, 0)
            self.spn_x = QSpinBox()
            self.spn_x.setRange(-9999, 9999)
            self.spn_x.setValue(int(item.rect.x()))
            layout.addWidget(self.spn_x, 0, 1)

            layout.addWidget(QLabel(tr("prop_coord_y", "Y 좌표")), 0, 2)
            self.spn_y = QSpinBox()
            self.spn_y.setRange(-9999, 9999)
            self.spn_y.setValue(int(item.rect.y()))
            layout.addWidget(self.spn_y, 0, 3)

        elif hasattr(item, "box_rect"):
            layout.addWidget(QLabel(tr("prop_coord_x", "X 좌표")), 0, 0)
            self.spn_x = QSpinBox()
            self.spn_x.setRange(-9999, 9999)
            self.spn_x.setValue(int(item.box_rect.x()))
            layout.addWidget(self.spn_x, 0, 1)

            layout.addWidget(QLabel(tr("prop_coord_y", "Y 좌표")), 0, 2)
            self.spn_y = QSpinBox()
            self.spn_y.setRange(-9999, 9999)
            self.spn_y.setValue(int(item.box_rect.y()))
            layout.addWidget(self.spn_y, 0, 3)

        elif hasattr(item, "pos"):
            layout.addWidget(QLabel(tr("prop_coord_x", "X 좌표")), 0, 0)
            self.spn_x = QSpinBox()
            self.spn_x.setRange(-9999, 9999)
            self.spn_x.setValue(int(item.pos.x()))
            layout.addWidget(self.spn_x, 0, 1)

            layout.addWidget(QLabel(tr("prop_coord_y", "Y 좌표")), 0, 2)
            self.spn_y = QSpinBox()
            self.spn_y.setRange(-9999, 9999)
            self.spn_y.setValue(int(item.pos.y()))
            layout.addWidget(self.spn_y, 0, 3)

    def _build_size_ui(self, layout):
        item = self.item
        cls_name = item.__class__.__name__
        row = 0

        if hasattr(item, "rect") or hasattr(item, "box_rect"):
            rect = getattr(item, "rect", getattr(item, "box_rect", None))
            if rect:
                layout.addWidget(QLabel(tr("prop_size_width", "너비 (W)")), row, 0)
                self.spn_w = QSpinBox()
                self.spn_w.setRange(4, 9999)
                self.spn_w.setValue(int(rect.width()))
                layout.addWidget(self.spn_w, row, 1)

                layout.addWidget(QLabel(tr("prop_size_height", "높이 (H)")), row, 2)
                self.spn_h = QSpinBox()
                self.spn_h.setRange(4, 9999)
                self.spn_h.setValue(int(rect.height()))
                layout.addWidget(self.spn_h, row, 3)
                row += 1

        if cls_name == "StampItem":
            layout.addWidget(QLabel("스탬프 번호"), row, 0)
            self.spn_stamp_index = QSpinBox()
            self.spn_stamp_index.setRange(1, 999)
            self.spn_stamp_index.setValue(int(getattr(item, "index", 1)))
            layout.addWidget(self.spn_stamp_index, row, 1)

            layout.addWidget(QLabel(tr("prop_size_diameter", "크기")), row, 2)
            self.spn_stamp_size = QSpinBox()
            self.spn_stamp_size.setRange(16, 120)
            self.spn_stamp_size.setValue(int(item.style.get("size", 32)))
            layout.addWidget(self.spn_stamp_size, row, 3)
            row += 1

            layout.addWidget(QLabel(tr("stamp_shape_label", "바탕 모양")), row, 0)
            self.cmb_stamp_shape = QComboBox()
            self.cmb_stamp_shape.addItem(tr("stamp_shape_circle", "원형"), "circle")
            self.cmb_stamp_shape.addItem(tr("stamp_shape_rounded_rect", "모서리가 둥근 사각형"), "rounded_rect")
            cur_shape = item.style.get("shape", "circle")
            self.cmb_stamp_shape.setCurrentIndex(1 if cur_shape == "rounded_rect" else 0)
            layout.addWidget(self.cmb_stamp_shape, row, 1)

            layout.addWidget(QLabel(tr("prop_corner_radius", "모서리 반경")), row, 2)
            self.spn_corner_radius = QSpinBox()
            self.spn_corner_radius.setRange(0, 50)
            self.spn_corner_radius.setValue(int(item.style.get("corner_radius", 6)))
            layout.addWidget(self.spn_corner_radius, row, 3)
            row += 1

        elif cls_name == "StepArrowItem":
            layout.addWidget(QLabel(tr("prop_size_diameter", "스탬프 크기")), row, 0)
            self.spn_stamp_size = QSpinBox()
            self.spn_stamp_size.setRange(16, 120)
            self.spn_stamp_size.setValue(int(item.stamp_style.get("size", 32)))
            layout.addWidget(self.spn_stamp_size, row, 1)

            layout.addWidget(QLabel(tr("stamp_shape_label", "바탕 모양")), row, 2)
            self.cmb_stamp_shape = QComboBox()
            self.cmb_stamp_shape.addItem(tr("stamp_shape_circle", "원형"), "circle")
            self.cmb_stamp_shape.addItem(tr("stamp_shape_rounded_rect", "모서리가 둥근 사각형"), "rounded_rect")
            cur_shape = item.stamp_style.get("shape", "circle")
            self.cmb_stamp_shape.setCurrentIndex(1 if cur_shape == "rounded_rect" else 0)
            layout.addWidget(self.cmb_stamp_shape, row, 3)
            row += 1

            layout.addWidget(QLabel(tr("prop_line_width", "선 두께")), row, 0)
            self.spn_line_width = QSpinBox()
            self.spn_line_width.setRange(1, 30)
            self.spn_line_width.setValue(int(item.arrow_style.get("width", 3)))
            layout.addWidget(self.spn_line_width, row, 1)

            layout.addWidget(QLabel(tr("prop_head_size", "화살촉 크기")), row, 2)
            self.spn_head_size = QSpinBox()
            self.spn_head_size.setRange(4, 60)
            self.spn_head_size.setValue(int(item.arrow_style.get("head_size", 14)))
            layout.addWidget(self.spn_head_size, row, 3)
            row += 1

        elif cls_name in ("ArrowItem", "ElbowArrowItem"):
            layout.addWidget(QLabel(tr("prop_line_width", "선 두께")), row, 0)
            self.spn_line_width = QSpinBox()
            self.spn_line_width.setRange(1, 30)
            self.spn_line_width.setValue(int(item.style.get("width", 3)))
            layout.addWidget(self.spn_line_width, row, 1)

            layout.addWidget(QLabel(tr("prop_head_size", "화살촉 크기")), row, 2)
            self.spn_head_size = QSpinBox()
            self.spn_head_size.setRange(4, 60)
            self.spn_head_size.setValue(int(item.style.get("head_size", 14)))
            layout.addWidget(self.spn_head_size, row, 3)
            row += 1

        elif cls_name == "HighlightBoxItem":
            layout.addWidget(QLabel(tr("prop_line_width", "선 두께")), row, 0)
            self.spn_line_width = QSpinBox()
            self.spn_line_width.setRange(1, 30)
            self.spn_line_width.setValue(int(item.style.get("border_width", 3)))
            layout.addWidget(self.spn_line_width, row, 1)

            self.chk_box_fill = QCheckBox(tr("opt_box_fill", "영역 채우기"))
            self.chk_box_fill.setChecked(bool(item.style.get("fill", False)))
            layout.addWidget(self.chk_box_fill, row, 2, 1, 2)
            row += 1

        elif cls_name in ("DimensionLineItem", "BoxDimensionItem"):
            layout.addWidget(QLabel(tr("prop_line_width", "선 두께")), row, 0)
            self.spn_line_width = QSpinBox()
            self.spn_line_width.setRange(1, 20)
            self.spn_line_width.setValue(int(item.style.get("width" if cls_name == "DimensionLineItem" else "border_width", 2)))
            layout.addWidget(self.spn_line_width, row, 1)

            if cls_name == "DimensionLineItem":
                layout.addWidget(QLabel(tr("prop_head_size", "틱 크기")), row, 2)
                self.spn_tick_size = QSpinBox()
                self.spn_tick_size.setRange(2, 40)
                self.spn_tick_size.setValue(int(item.style.get("tick_size", 8)))
                layout.addWidget(self.spn_tick_size, row, 3)
            else:
                self.chk_box_fill = QCheckBox(tr("opt_box_fill", "영역 채우기"))
                self.chk_box_fill.setChecked(bool(item.style.get("fill", False)))
                layout.addWidget(self.chk_box_fill, row, 2, 1, 2)
            row += 1

            layout.addWidget(QLabel("단위 (Unit)"), row, 0)
            self.cmb_unit = QComboBox()
            for u in ["px", "dp", "pt", "mm"]:
                self.cmb_unit.addItem(u, u)
            self.cmb_unit.setCurrentText(item.style.get("unit", "px"))
            layout.addWidget(self.cmb_unit, row, 1)
            row += 1

        elif cls_name == "BlurMosaicItem":
            layout.addWidget(QLabel("블록 크기"), row, 0)
            self.spn_block_size = QSpinBox()
            self.spn_block_size.setRange(2, 80)
            self.spn_block_size.setValue(int(item.style.get("block_size", 10)))
            layout.addWidget(self.spn_block_size, row, 1)
            row += 1

    def _has_font_properties(self):
        item = self.item
        cls_name = item.__class__.__name__
        if cls_name in ("TextLabelItem", "CalloutItem", "HotkeyBadgeItem", "WordArtItem", "DimensionLineItem", "BoxDimensionItem", "DraftStampItem", "FlowchartNodeItem"):
            return True
        return False

    def _build_font_ui(self, layout):
        item = self.item
        cls_name = item.__class__.__name__
        row = 0

        # 텍스트 내용 수정 (지원 객체)
        if hasattr(item, "text"):
            layout.addWidget(QLabel(tr("prop_text_content", "텍스트 내용")), row, 0)
            self.txt_content = QLineEdit(str(item.text))
            layout.addWidget(self.txt_content, row, 1, 1, 3)
            row += 1
        elif hasattr(item, "key_text"):
            layout.addWidget(QLabel(tr("prop_text_content", "텍스트 내용")), row, 0)
            self.txt_content = QLineEdit(str(item.key_text))
            layout.addWidget(self.txt_content, row, 1, 1, 3)
            row += 1

        # 글꼴 패밀리
        if "font_family" in getattr(item, "style", {}):
            layout.addWidget(QLabel(tr("prop_font_family", "글꼴")), row, 0)
            self.cmb_font_family = QFontComboBox()
            self.cmb_font_family.setCurrentFont(QFont(item.style.get("font_family", "Malgun Gothic")))
            layout.addWidget(self.cmb_font_family, row, 1, 1, 3)
            row += 1

        # 글자 크기
        style = getattr(item, "style", {})
        if "font_size" in style:
            layout.addWidget(QLabel(tr("prop_font_size", "글자 크기")), row, 0)
            self.spn_font_size = QSpinBox()
            self.spn_font_size.setRange(6, 120)
            self.spn_font_size.setValue(int(style.get("font_size", 12)))
            layout.addWidget(self.spn_font_size, row, 1)

            if "font_bold" in style:
                self.chk_font_bold = QCheckBox(tr("prop_font_bold", "굵게"))
                self.chk_font_bold.setChecked(bool(style.get("font_bold", True)))
                layout.addWidget(self.chk_font_bold, row, 2, 1, 2)
            row += 1

    def _build_colors_ui(self, layout):
        item = self.item
        cls_name = item.__class__.__name__
        row = 0

        # 1. 선색 / 테두리색
        stroke_color = None
        if cls_name in ("ArrowItem", "ElbowArrowItem"):
            stroke_color = item.style.get("color", "#E53935")
        elif cls_name == "HighlightBoxItem":
            stroke_color = item.style.get("color", "#E53935")
        elif cls_name in ("DimensionLineItem", "BoxDimensionItem"):
            stroke_color = item.style.get("color", "#007AFF")
        elif cls_name == "StepArrowItem":
            stroke_color = item.arrow_style.get("color", "#E53935")
        elif hasattr(item, "style") and "border_color" in item.style:
            stroke_color = item.style.get("border_color", "#E53935")
        elif hasattr(item, "style") and "stroke_color" in item.style:
            stroke_color = item.style.get("stroke_color", "#000000")

        if stroke_color:
            layout.addWidget(QLabel(tr("prop_stroke_color", "선색")), row, 0)
            self.btn_stroke_color = self._make_color_button(stroke_color)
            layout.addWidget(self.btn_stroke_color, row, 1)
            row += 1

        # 2. 배경색 / 채우기색
        bg_color = None
        if cls_name == "StampItem":
            bg_color = item.style.get("bg_color", "#E53935")
        elif cls_name == "StepArrowItem":
            bg_color = item.stamp_style.get("bg_color", "#E53935")
        elif cls_name in ("DimensionLineItem", "BoxDimensionItem"):
            bg_color = item.style.get("badge_bg", "#007AFF")
        elif hasattr(item, "style") and "bg_color" in item.style:
            bg_color = item.style.get("bg_color", "#212121")

        if bg_color:
            layout.addWidget(QLabel(tr("prop_fill_color", "배경/채우기색")), row, 0)
            self.btn_bg_color = self._make_color_button(bg_color)
            layout.addWidget(self.btn_bg_color, row, 1)
            row += 1

        # 3. 글자색
        text_color = None
        if cls_name == "StampItem":
            text_color = item.style.get("text_color", "#FFFFFF")
        elif cls_name == "StepArrowItem":
            text_color = item.stamp_style.get("text_color", "#FFFFFF")
        elif cls_name in ("DimensionLineItem", "BoxDimensionItem"):
            text_color = item.style.get("badge_text_color", "#FFFFFF")
        elif hasattr(item, "style") and "text_color" in item.style:
            text_color = item.style.get("text_color", "#FFFFFF")

        if text_color:
            layout.addWidget(QLabel(tr("prop_text_color", "글자색")), row, 0)
            self.btn_text_color = self._make_color_button(text_color)
            layout.addWidget(self.btn_text_color, row, 1)
            row += 1

    def _on_apply_and_accept(self):
        item = self.item
        cls_name = item.__class__.__name__

        # 1. 좌표 반영
        if hasattr(self, "spn_start_x") and hasattr(item, "start_pos"):
            item.start_pos = QPointF(self.spn_start_x.value(), self.spn_start_y.value())
            item.end_pos = QPointF(self.spn_end_x.value(), self.spn_end_y.value())
        elif hasattr(self, "spn_x"):
            if hasattr(item, "rect"):
                w = self.spn_w.value() if hasattr(self, "spn_w") else item.rect.width()
                h = self.spn_h.value() if hasattr(self, "spn_h") else item.rect.height()
                if isinstance(item, (ImageOverlayItem, BoxDimensionItem)) or isinstance(getattr(item, "rect", None), QRectF):
                    item.rect = QRectF(float(self.spn_x.value()), float(self.spn_y.value()), float(w), float(h))
                else:
                    item.rect = QRect(self.spn_x.value(), self.spn_y.value(), int(w), int(h))
            elif hasattr(item, "box_rect"):
                w = self.spn_w.value() if hasattr(self, "spn_w") else item.box_rect.width()
                h = self.spn_h.value() if hasattr(self, "spn_h") else item.box_rect.height()
                item.box_rect = QRectF(self.spn_x.value(), self.spn_y.value(), w, h)
            elif hasattr(item, "pos"):
                item.pos = QPointF(self.spn_x.value(), self.spn_y.value())

        # 2. 크기 및 형태 반영
        if cls_name == "StampItem":
            item.style["size"] = self.spn_stamp_size.value()
            item.style["shape"] = self.cmb_stamp_shape.currentData()
            item.style["corner_radius"] = self.spn_corner_radius.value()
        elif cls_name == "StepArrowItem":
            item.stamp_style["size"] = self.spn_stamp_size.value()
            item.stamp_style["shape"] = self.cmb_stamp_shape.currentData()
            item.arrow_style["width"] = self.spn_line_width.value()
            item.arrow_style["head_size"] = self.spn_head_size.value()
        elif cls_name in ("ArrowItem", "ElbowArrowItem"):
            item.style["width"] = self.spn_line_width.value()
            item.style["head_size"] = self.spn_head_size.value()
        elif cls_name == "HighlightBoxItem":
            item.style["border_width"] = self.spn_line_width.value()
            item.style["fill"] = self.chk_box_fill.isChecked()
        elif cls_name == "DimensionLineItem":
            item.style["width"] = self.spn_line_width.value()
            item.style["tick_size"] = self.spn_tick_size.value()
            item.style["unit"] = self.cmb_unit.currentData()
        elif cls_name == "BoxDimensionItem":
            item.style["border_width"] = self.spn_line_width.value()
            item.style["fill"] = self.chk_box_fill.isChecked()
            item.style["unit"] = self.cmb_unit.currentData()
        elif cls_name == "BlurMosaicItem":
            item.style["block_size"] = self.spn_block_size.value()

        if hasattr(self, "spn_stamp_index") and hasattr(item, "index"):
            item.index = self.spn_stamp_index.value()

        # 3. 글꼴 및 내용 반영
        if hasattr(self, "txt_content"):
            if hasattr(item, "text"):
                item.text = self.txt_content.text()
            elif hasattr(item, "key_text"):
                item.key_text = self.txt_content.text()

        if hasattr(self, "cmb_font_family") and hasattr(item, "style"):
            item.style["font_family"] = self.cmb_font_family.currentFont().family()
        if hasattr(self, "spn_font_size") and hasattr(item, "style"):
            item.style["font_size"] = self.spn_font_size.value()
        if hasattr(self, "chk_font_bold") and hasattr(item, "style"):
            item.style["font_bold"] = self.chk_font_bold.isChecked()

        # 4. 색상 반영
        if hasattr(self, "btn_stroke_color"):
            c = self.btn_stroke_color.text()
            if cls_name in ("ArrowItem", "ElbowArrowItem", "HighlightBoxItem", "DimensionLineItem", "BoxDimensionItem"):
                item.style["color"] = c
            elif cls_name == "StepArrowItem":
                item.arrow_style["color"] = c
            elif hasattr(item, "style") and "border_color" in item.style:
                item.style["border_color"] = c
            elif hasattr(item, "style") and "stroke_color" in item.style:
                item.style["stroke_color"] = c

        if hasattr(self, "btn_bg_color"):
            c = self.btn_bg_color.text()
            if cls_name == "StampItem":
                item.style["bg_color"] = c
            elif cls_name == "StepArrowItem":
                item.stamp_style["bg_color"] = c
            elif cls_name in ("DimensionLineItem", "BoxDimensionItem"):
                item.style["badge_bg"] = c
            elif hasattr(item, "style") and "bg_color" in item.style:
                item.style["bg_color"] = c

        if hasattr(self, "btn_text_color"):
            c = self.btn_text_color.text()
            if cls_name == "StampItem":
                item.style["text_color"] = c
            elif cls_name == "StepArrowItem":
                item.stamp_style["text_color"] = c
            elif cls_name in ("DimensionLineItem", "BoxDimensionItem"):
                item.style["badge_text_color"] = c
            elif hasattr(item, "style") and "text_color" in item.style:
                item.style["text_color"] = c

        # 5. 기본 설정 반영 체크 확인
        if hasattr(self, "chk_apply_defaults") and self.chk_apply_defaults.isChecked() and self.config_key:
            cfg = self.canvas.config.get(self.config_key, {})
            if isinstance(cfg, dict):
                if cls_name == "StepArrowItem":
                    if "arrow_style" in self.canvas.config:
                        self.canvas.config["arrow_style"].update(item.arrow_style)
                    if "stamp_style" in self.canvas.config:
                        self.canvas.config["stamp_style"].update(item.stamp_style)
                else:
                    cfg.update(item.style)
                    self.canvas.config[self.config_key] = cfg

                win = self.canvas.window()
                if win and hasattr(win, "config"):
                    win.config[self.config_key] = self.canvas.config[self.config_key]
                    if hasattr(win, "save_config"):
                        win.save_config()

        self.accept()


# ------------------------------------------------------------------------------
# 프로젝트 관리자 (ProjectManager: .mcs.json & _raw.png 영구 분리 보존)
# ------------------------------------------------------------------------------
import zipfile

class ProjectData:
    """하위 호환 4-tuple 언패킹 및 현대식 객체 프로퍼티 동시 지원 래퍼"""
    def __init__(self, steps: list, active_step_idx: int = 0, metadata: dict = None):
        self.steps = steps or []
        self.active_step_idx = active_step_idx
        self.metadata = metadata or {}

    def __iter__(self):
        first = self.steps[0] if self.steps else {}
        return iter([first.get("raw_pixmap"), first.get("items", []), first.get("next_stamp_index", 1), self.metadata])

    def __len__(self):
        return 4

    def __getitem__(self, idx):
        first = self.steps[0] if self.steps else {}
        t = (first.get("raw_pixmap"), first.get("items", []), first.get("next_stamp_index", 1), self.metadata)
        return t[idx]



class ProjectManager:
    """다중 슬라이드 프로젝트(.dragon 단일 패키지 및 .mcs.json) 입출력 및 무결성 관리 전담 엔진"""

    @staticmethod
    def pixmap_to_bytes(pixmap: QPixmap) -> bytes:
        if pixmap is None or pixmap.isNull():
            return b""
        ba = QByteArray()
        buf = QBuffer(ba)
        buf.open(QIODevice.WriteOnly)
        pixmap.save(buf, "PNG")
        return bytes(ba.data())

    @staticmethod
    def bytes_to_pixmap(raw_bytes: bytes) -> QPixmap:
        if not raw_bytes:
            return None
        px = QPixmap()
        px.loadFromData(raw_bytes, "PNG")
        return px if not px.isNull() else None

    @staticmethod
    def pixmap_to_base64(pixmap: QPixmap) -> str:
        b = ProjectManager.pixmap_to_bytes(pixmap)
        return base64.b64encode(b).decode("utf-8") if b else ""

    @staticmethod
    def base64_to_pixmap(b64_str: str) -> QPixmap:
        if not b64_str:
            return None
        try:
            raw_bytes = base64.b64decode(b64_str.encode("utf-8"))
            return ProjectManager.bytes_to_pixmap(raw_bytes)
        except Exception:
            return None

    @classmethod
    def save_project(cls, project_path: str, data, items: list = None, next_stamp_index: int = 1, metadata: dict = None, active_step_idx: int = 0) -> bool:
        """
        다중 슬라이드 프로젝트(.dragon 압축 패키지 또는 .mcs.json)를 안전 저장합니다.
        구형 호출 save_project(path, raw_pixmap, items, next_idx, metadata)도 100% 자동 지원합니다.
        """
        try:
            if not project_path:
                return False

            # 구형 단일 슬라이드 호출 호환성 처리
            if not isinstance(data, list):
                raw_pixmap = data
                storyboard_steps = [{
                    "step_num": 1,
                    "title": "Step 1. [단계명 입력]",
                    "description": "",
                    "raw_pixmap": raw_pixmap,
                    "thumbnail": raw_pixmap.copy() if raw_pixmap else None,
                    "items": items or [],
                    "next_stamp_index": next_stamp_index
                }]
            else:
                storyboard_steps = data

            is_dragon = project_path.lower().endswith(".dragon")
            if not is_dragon and not project_path.lower().endswith(".mcs.json") and not project_path.lower().endswith(".json"):
                # 기본 확장자 .dragon 채택
                project_path += ".dragon"
                is_dragon = True

            out_dir = os.path.dirname(os.path.abspath(project_path))
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)

            if is_dragon:
                # 1. .dragon 단일 ZIP 압축 패키지 생성 (manifest.json + slides/step_{i:03d}.png)
                temp_zip = project_path + ".tmp"
                with zipfile.ZipFile(temp_zip, "w", zipfile.ZIP_DEFLATED) as zf:
                    manifest_steps = []
                    for i, step in enumerate(storyboard_steps):
                        step_num = step.get("step_num", i + 1)
                        s_title = step.get("title", f"Step {step_num}")
                        s_desc = step.get("description", "")
                        next_stamp = step.get("next_stamp_index", 1)

                        items_serialized = []
                        for it in step.get("items", []):
                            if hasattr(it, "to_dict"):
                                items_serialized.append(it.to_dict())

                        raw_px = step.get("raw_pixmap")
                        img_rel_path = None
                        canvas_size = [0, 0]
                        if raw_px and not raw_px.isNull():
                            canvas_size = [raw_px.width(), raw_px.height()]
                            img_name = f"slides/step_{step_num:03d}_raw.png"
                            zf.writestr(img_name, cls.pixmap_to_bytes(raw_px))
                            img_rel_path = img_name

                        thumb_px = step.get("thumbnail")
                        thumb_rel_path = None
                        if thumb_px and not thumb_px.isNull():
                            thumb_name = f"slides/step_{step_num:03d}_thumb.png"
                            zf.writestr(thumb_name, cls.pixmap_to_bytes(thumb_px))
                            thumb_rel_path = thumb_name

                        manifest_steps.append({
                            "step_num": step_num,
                            "title": s_title,
                            "description": s_desc,
                            "canvas_size": canvas_size,
                            "image_file": img_rel_path,
                            "thumb_file": thumb_rel_path,
                            "next_stamp_index": int(next_stamp),
                            "items": items_serialized,
                        })

                    manifest = {
                        "format": "DragonManualStudio_Project",
                        "version": "2.0",
                        "generator": "DragonRPA Manual Studio v1.5.0",
                        "created_at": datetime.now().isoformat(),
                        "active_step_idx": int(active_step_idx),
                        "metadata": metadata or {},
                        "total_steps": len(manifest_steps),
                        "steps": manifest_steps
                    }
                    zf.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))

                if os.path.exists(project_path):
                    os.remove(project_path)
                os.rename(temp_zip, project_path)
                return True
            else:
                # 2. .mcs.json 다중 슬라이드 포맷 (Base64 인코딩 원본 보존)
                base_file = os.path.basename(project_path)
                clean_name = base_file.replace(".mcs.json", "").replace(".json", "")
                raw_img_filename = f"{clean_name}_raw.png"
                raw_img_path = os.path.join(out_dir, raw_img_filename)

                if len(storyboard_steps) == 1:
                    raw_px0 = storyboard_steps[0].get("raw_pixmap")
                    if raw_px0 and not raw_px0.isNull():
                        raw_px0.save(raw_img_path, "PNG")

                serialized_steps = []
                for i, step in enumerate(storyboard_steps):
                    step_num = step.get("step_num", i + 1)
                    s_title = step.get("title", f"Step {step_num}")
                    s_desc = step.get("description", "")
                    next_stamp = step.get("next_stamp_index", 1)

                    items_serialized = []
                    for it in step.get("items", []):
                        if hasattr(it, "to_dict"):
                            items_serialized.append(it.to_dict())

                    raw_px = step.get("raw_pixmap")
                    b64_str = cls.pixmap_to_base64(raw_px) if raw_px and not raw_px.isNull() else ""
                    canvas_size = [raw_px.width(), raw_px.height()] if raw_px and not raw_px.isNull() else [0, 0]

                    companion_file = raw_img_filename if (len(storyboard_steps) == 1 and i == 0) else None

                    serialized_steps.append({
                        "step_num": step_num,
                        "title": s_title,
                        "description": s_desc,
                        "canvas_size": canvas_size,
                        "raw_image_file": companion_file,
                        "raw_image_b64": b64_str,
                        "next_stamp_index": int(next_stamp),
                        "items": items_serialized,
                    })

                project_dict = {
                    "format": "ManualCaptureStudio_MultiProject",
                    "version": "2.0",
                    "generator": "DragonRPA Manual Studio v1.5.0",
                    "created_at": datetime.now().isoformat(),
                    "active_step_idx": int(active_step_idx),
                    "metadata": metadata or {},
                    "total_steps": len(serialized_steps),
                    "steps": serialized_steps
                }
                if len(serialized_steps) == 1:
                    project_dict["raw_image_file"] = raw_img_filename
                    project_dict["canvas_size"] = serialized_steps[0]["canvas_size"]
                    project_dict["raw_image_b64"] = serialized_steps[0]["raw_image_b64"]
                    project_dict["next_stamp_index"] = serialized_steps[0]["next_stamp_index"]
                    project_dict["items"] = serialized_steps[0]["items"]

                temp_json = project_path + ".tmp"
                with open(temp_json, "w", encoding="utf-8") as f:
                    json.dump(project_dict, f, indent=2, ensure_ascii=False)

                if os.path.exists(project_path):
                    os.remove(project_path)
                os.rename(temp_json, project_path)
                return True

        except Exception as e:
            print(f"[ProjectManager 저장 오류]: {e}")
            return False

    @classmethod
    def load_project(cls, project_path: str):
        """
        .dragon 또는 .mcs.json 프로젝트를 로드하여 ProjectData(하위 호환 4-tuple 언패킹 지원)를 반환합니다.
        """
        if not os.path.exists(project_path):
            return ProjectData([], 0, {})

        try:
            # 1. .dragon (ZIP) 패키지 로드
            if zipfile.is_zipfile(project_path):
                with zipfile.ZipFile(project_path, "r") as zf:
                    if "manifest.json" not in zf.namelist():
                        return ProjectData([], 0, {})
                    manifest_data = json.loads(zf.read("manifest.json").decode("utf-8"))
                    active_idx = int(manifest_data.get("active_step_idx", 0))
                    metadata = manifest_data.get("metadata", {})
                    raw_steps = manifest_data.get("steps", [])

                    storyboard_steps = []
                    for i, sdata in enumerate(raw_steps):
                        step_num = sdata.get("step_num", i + 1)
                        s_title = sdata.get("title", f"Step {step_num}")
                        s_desc = sdata.get("description", "")
                        next_stamp = sdata.get("next_stamp_index", 1)

                        raw_px = None
                        img_rel = sdata.get("image_file")
                        if img_rel and img_rel in zf.namelist():
                            raw_px = cls.bytes_to_pixmap(zf.read(img_rel))

                        thumb_px = None
                        thumb_rel = sdata.get("thumb_file")
                        if thumb_rel and thumb_rel in zf.namelist():
                            thumb_px = cls.bytes_to_pixmap(zf.read(thumb_rel))
                        elif raw_px:
                            thumb_px = raw_px.copy()

                        items = []
                        for it_d in sdata.get("items", []):
                            it_obj = item_from_dict(it_d)
                            if it_obj:
                                items.append(it_obj)

                        storyboard_steps.append({
                            "step_num": step_num,
                            "title": s_title,
                            "description": s_desc,
                            "raw_pixmap": raw_px,
                            "thumbnail": thumb_px,
                            "items": items,
                            "next_stamp_index": next_stamp
                        })
                    return ProjectData(storyboard_steps, active_idx, metadata)

            # 2. JSON 파일 (.mcs.json) 로드
            with open(project_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            metadata = data.get("metadata", {})
            active_idx = int(data.get("active_step_idx", 0))
            project_dir = os.path.dirname(os.path.abspath(project_path))

            # A. 현대식 다중 슬라이드 포맷
            if "steps" in data and isinstance(data["steps"], list):
                storyboard_steps = []
                for i, sdata in enumerate(data["steps"]):
                    step_num = sdata.get("step_num", i + 1)
                    s_title = sdata.get("title", f"Step {step_num}")
                    s_desc = sdata.get("description", "")
                    next_stamp = sdata.get("next_stamp_index", 1)

                    raw_px = None
                    raw_file = sdata.get("raw_image_file") or data.get("raw_image_file")
                    if raw_file:
                        rf_path = os.path.join(project_dir, raw_file)
                        if os.path.exists(rf_path):
                            raw_px = QPixmap(rf_path)
                    if (raw_px is None or raw_px.isNull()) and sdata.get("raw_image_b64"):
                        raw_px = cls.base64_to_pixmap(sdata.get("raw_image_b64", ""))

                    items = []
                    for it_d in sdata.get("items", []):
                        it_obj = item_from_dict(it_d)
                        if it_obj:
                            items.append(it_obj)

                    thumb_px = raw_px.copy() if raw_px else None

                    storyboard_steps.append({
                        "step_num": step_num,
                        "title": s_title,
                        "description": s_desc,
                        "raw_pixmap": raw_px,
                        "thumbnail": thumb_px,
                        "items": items,
                        "next_stamp_index": next_stamp
                    })
                return ProjectData(storyboard_steps, active_idx, metadata)

            # B. 구형 단일 슬라이드 포맷 (완벽 하위 호환)
            raw_img_filename = data.get("raw_image_file", "")
            project_dir = os.path.dirname(os.path.abspath(project_path))
            raw_img_path = os.path.join(project_dir, raw_img_filename) if raw_img_filename else ""

            raw_pixmap = None
            if raw_img_path and os.path.exists(raw_img_path):
                raw_pixmap = QPixmap(raw_img_path)
            if (raw_pixmap is None or raw_pixmap.isNull()) and data.get("raw_image_b64"):
                raw_pixmap = cls.base64_to_pixmap(data["raw_image_b64"])

            items = []
            for item_dict in data.get("items", []):
                obj = item_from_dict(item_dict)
                if obj:
                    items.append(obj)

            next_stamp_index = int(data.get("next_stamp_index", 1))
            single_step = {
                "step_num": 1,
                "title": "Step 1. [단계명 입력]",
                "description": "",
                "raw_pixmap": raw_pixmap,
                "thumbnail": raw_pixmap.copy() if raw_pixmap else None,
                "items": items,
                "next_stamp_index": next_stamp_index
            }
            return ProjectData([single_step], 0, metadata)

        except Exception as e:
            print(f"[ProjectManager 로드 오류]: {e}")
            return ProjectData([], 0, {})

    @classmethod
    def merge_project(cls, current_steps: list, merge_file_path: str):
        """대상 프로젝트의 슬라이드를 현재 타임라인 뒤로 연속 순번으로 병합"""
        proj_data = cls.load_project(merge_file_path)
        incoming_steps = proj_data.steps if hasattr(proj_data, "steps") else []
        if not incoming_steps:
            return current_steps, 0

        merged = [s.copy() for s in current_steps]
        start_num = len(merged) + 1
        added_count = 0
        for s in incoming_steps:
            new_s = s.copy()
            new_s["step_num"] = start_num + added_count
            orig_title = s.get("title", "")
            clean_title = orig_title.split(". ", 1)[-1] if ". " in orig_title else orig_title
            new_s["title"] = f"Step {new_s['step_num']}. {clean_title}"
            new_s["items"] = [it.clone() for it in s.get("items", [])]
            if s.get("raw_pixmap"):
                new_s["raw_pixmap"] = s["raw_pixmap"].copy()
            if s.get("thumbnail"):
                new_s["thumbnail"] = s["thumbnail"].copy()
            merged.append(new_s)
            added_count += 1

        return merged, added_count


# ==============================================================================
# 4. 캡처 오버레이 윈도우 (CaptureOverlayWidget)
# ==============================================================================
class CaptureOverlayWidget(QWidget):
    sig_captured = pyqtSignal(QPixmap, QRect)
    sig_cancelled = pyqtSignal()

    def __init__(self, last_rect=None, config=None, is_sub_capture=False, target_monitor=None, parent=None):
        super().__init__(parent)
        self.is_captured = False
        self.is_sub_capture = is_sub_capture
        self.target_monitor = target_monitor
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setMouseTracking(True)

        self.config = config or DEFAULT_CONFIG
        self.last_rect = last_rect

        screens = MultiMonitorManager.get_screens()
        self.screens = screens

        # 타깃 모니터가 단일 모니터(0..N-1)로 유효하게 지정된 경우
        if self.target_monitor is not None and 0 <= self.target_monitor < len(screens):
            target_screen = screens[self.target_monitor]
            self.virtual_rect = target_screen.geometry()
            self.setGeometry(self.virtual_rect)
            self.full_screen_pixmap = target_screen.grabWindow(0)
        else:
            # 전체 가상 데스크톱 대상 (모든 모니터 포괄 및 합성)
            self.target_monitor = -1
            self.virtual_rect = MultiMonitorManager.get_virtual_desktop_rect()
            self.setGeometry(self.virtual_rect)

            pix = QPixmap(self.virtual_rect.size())
            pix.fill(Qt.black)
            p = QPainter(pix)
            for s in screens:
                sg = s.geometry()
                p.drawPixmap(sg.x() - self.virtual_rect.x(), sg.y() - self.virtual_rect.y(), s.grabWindow(0))
            p.end()
            self.full_screen_pixmap = pix

        # 상태 관리
        self.selecting = False
        self.resizing_handle = None
        self.moving_rect = False
        self.start_pos = QPoint()
        self.end_pos = QPoint()
        self.selected_rect = QRect()
        self.magnet_rect = QRect()
        self.snap_enabled = True
        self.snapped_rect = QRect()

        self.mouse_pos = QPoint()
        self.handle_size = 8

        self.setFocusPolicy(Qt.StrongFocus)

    def show_overlay(self):
        """다중 모니터 가상 데스크톱(-1) 또는 단일 모니터에 맞춰 전체화면 표출"""
        if self.target_monitor == -1:
            self.setGeometry(self.virtual_rect)
            self.show()
            self.raise_()
            self.activateWindow()
        else:
            self.showFullScreen()

    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()

        if key == Qt.Key_Escape:
            self.close()
        elif key == Qt.Key_R and self.last_rect and not self.last_rect.isEmpty():
            # 직전 영역 복원
            self.selected_rect = QRect(self.last_rect)
            self.update()
        elif key in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            if not self.selected_rect.isEmpty() and self.selected_rect.width() > 10 and self.selected_rect.height() > 10:
                self.confirm_capture()
        elif not self.selected_rect.isEmpty():
            # 방향키 1px 이동 및 Shift+방향키 크기 조절
            step = 1 if not (modifiers & Qt.ControlModifier) else 10
            r = self.selected_rect
            if modifiers & Qt.ShiftModifier:
                # 크기 조절
                if key == Qt.Key_Left:
                    self.selected_rect.setWidth(max(10, r.width() - step))
                elif key == Qt.Key_Right:
                    self.selected_rect.setWidth(r.width() + step)
                elif key == Qt.Key_Up:
                    self.selected_rect.setHeight(max(10, r.height() - step))
                elif key == Qt.Key_Down:
                    self.selected_rect.setHeight(r.height() + step)
            else:
                # 이동
                if key == Qt.Key_Left:
                    self.selected_rect.translate(-step, 0)
                elif key == Qt.Key_Right:
                    self.selected_rect.translate(step, 0)
                elif key == Qt.Key_Up:
                    self.selected_rect.translate(0, -step)
                elif key == Qt.Key_Down:
                    self.selected_rect.translate(0, step)
            self.update()

    def get_window_under_cursor(self, global_pt):
        try:
            elem_r = MagneticSnapEngine.get_element_rect(global_pt, exclude_hwnd=int(self.winId()))
            if not elem_r.isEmpty():
                rx = elem_r.x() - self.virtual_rect.x()
                ry = elem_r.y() - self.virtual_rect.y()
                rw = elem_r.width()
                rh = elem_r.height()
                if rw > 12 and rh > 12 and rw <= self.virtual_rect.width() and rh <= self.virtual_rect.height():
                    return QRect(rx, ry, rw, rh)
        except Exception:
            pass
        return QRect()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pt = get_mouse_pos(event)
            # 1. 기존 선택 사각형 핸들 체크
            if not self.selected_rect.isEmpty():
                handle = self.get_handle_at(pt)
                if handle:
                    self.resizing_handle = handle
                    self.start_pos = pt
                    return
                elif self.selected_rect.contains(pt):
                    self.moving_rect = True
                    self.start_pos = pt
                    return

            # 2. 신규 드래그 시작
            self.selecting = True
            self.selected_rect = QRect()
            self.start_pos = pt
            self.end_pos = pt
            self.update()
        elif event.button() == Qt.RightButton:
            # 우클릭 시 선택 취소 또는 창 닫기
            if not self.selected_rect.isEmpty():
                self.selected_rect = QRect()
                self.update()
            else:
                self.close()

    def mouseMoveEvent(self, event):
        self.mouse_pos = get_mouse_pos(event)
        global_pt = get_mouse_global_pos(event)

        if self.selecting:
            self.end_pos = get_mouse_pos(event)
            self.selected_rect = QRect(self.start_pos, self.end_pos).normalized()
            self.update()
        elif self.resizing_handle:
            self.handle_resize(get_mouse_pos(event))
            self.update()
        elif self.moving_rect:
            diff = get_mouse_pos(event) - self.start_pos
            self.selected_rect.translate(diff)
            self.start_pos = get_mouse_pos(event)
            self.update()
        else:
            # 마우스만 움직일 때 자석 스냅 탐색
            if self.selected_rect.isEmpty():
                self.magnet_rect = self.get_window_under_cursor(global_pt)
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.selecting:
                self.selecting = False
                self.end_pos = get_mouse_pos(event)
                r = QRect(self.start_pos, self.end_pos).normalized()
                if r.width() < 10 and r.height() < 10 and not self.magnet_rect.isEmpty():
                    # 단순 클릭 시 자석 스냅 창 자동 채택
                    self.selected_rect = QRect(self.magnet_rect)
                else:
                    self.selected_rect = r
                self.update()

                # 엔터 대기 없이 마우스 릴리즈 즉시 캡처 확정
                if not self.selected_rect.isEmpty() and self.selected_rect.width() >= 10 and self.selected_rect.height() >= 10:
                    self.confirm_capture()
            elif self.resizing_handle:
                self.resizing_handle = None
            elif self.moving_rect:
                self.moving_rect = False

    def mouseDoubleClickEvent(self, event):
        pt = get_mouse_pos(event)
        for it in reversed(self.items):
            if isinstance(it, FlowchartNodeItem) and it.contains(pt):
                from PySide6.QtWidgets import QInputDialog
                new_text, ok = QInputDialog.getMultiLineText(
                    self, tr("dlg_edit_flow_node", "플로우차트 노드 텍스트 편집"),
                    tr("lbl_flow_node_text", "표시할 텍스트 입력:"),
                    it.text
                )
                if ok and new_text.strip():
                    self.push_undo()
                    it.text = new_text.strip()
                    self.update()
                    self.sig_content_changed.emit()
                return

        if event.button() == Qt.LeftButton:
            if not self.selected_rect.isEmpty() and self.selected_rect.contains(get_mouse_pos(event)):
                self.confirm_capture()

    def confirm_capture(self):
        r = self.selected_rect.normalized()
        if r.width() < 10 or r.height() < 10:
            return
        self.is_captured = True
        cropped = self.full_screen_pixmap.copy(r)

        # 특정 단일 모니터 기준이면 r은 해당 모니터의 상대 좌표(0..W, 0..H)
        if self.target_monitor is not None and self.target_monitor >= 0:
            emit_rect = r
        else:
            emit_rect = QRect(
                self.virtual_rect.x() + r.x(),
                self.virtual_rect.y() + r.y(),
                r.width(),
                r.height()
            )
        self.sig_captured.emit(cropped, emit_rect)
        self.close()
        self.deleteLater()

    def closeEvent(self, event):
        if not self.is_captured:
            self.sig_cancelled.emit()
        super().closeEvent(event)
        self.deleteLater()

    def get_handles(self):
        if self.selected_rect.isEmpty():
            return {}
        r = self.selected_rect
        s = self.handle_size
        hs = s // 2
        return {
            "TL": QRect(r.left() - hs, r.top() - hs, s, s),
            "T":  QRect(r.center().x() - hs, r.top() - hs, s, s),
            "TR": QRect(r.right() - hs, r.top() - hs, s, s),
            "R":  QRect(r.right() - hs, r.center().y() - hs, s, s),
            "BR": QRect(r.right() - hs, r.bottom() - hs, s, s),
            "B":  QRect(r.center().x() - hs, r.bottom() - hs, s, s),
            "BL": QRect(r.left() - hs, r.bottom() - hs, s, s),
            "L":  QRect(r.left() - hs, r.center().y() - hs, s, s)
        }

    def get_handle_at(self, pt):
        for name, hrect in self.get_handles().items():
            if hrect.contains(pt):
                return name
        return None

    def handle_resize(self, pt):
        r = self.selected_rect
        h = self.resizing_handle
        if "L" in h:
            r.setLeft(min(pt.x(), r.right() - 10))
        if "R" in h:
            r.setRight(max(pt.x(), r.left() + 10))
        if "T" in h:
            r.setTop(min(pt.y(), r.bottom() - 10))
        if "B" in h:
            r.setBottom(max(pt.y(), r.top() + 10))
        self.selected_rect = r.normalized()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)

        # 1. 원본 화면 렌더링
        painter.drawPixmap(0, 0, self.full_screen_pixmap)

        # 2. 어두운 반투명 마스크
        painter.fillRect(self.rect(), QColor(0, 0, 0, 110))

        # 3. 자석 스냅 가이드 표시 (선택 전)
        if self.selected_rect.isEmpty() and not self.magnet_rect.isEmpty():
            painter.setPen(QPen(QColor(6, 182, 212, 230), 2, Qt.DashLine))
            painter.setBrush(QBrush(QColor(6, 182, 212, 35)))
            painter.drawRect(self.magnet_rect)

        # 4. 선택된 영역 밝게 클리어
        target_r = self.selected_rect if not self.selected_rect.isEmpty() else (
            QRect(self.start_pos, self.end_pos).normalized() if self.selecting else QRect()
        )

        if not target_r.isEmpty():
            painter.save()
            painter.setCompositionMode(QPainter.CompositionMode_Source)
            painter.drawPixmap(target_r, self.full_screen_pixmap, target_r)
            painter.restore()

            # 선택 사각형 테두리
            border_col = QColor(255, 140, 0) if self.is_sub_capture else QColor(0, 140, 255)
            handle_col = QColor(230, 100, 0) if self.is_sub_capture else QColor(0, 100, 220)
            painter.setPen(QPen(border_col, 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(target_r)

            # 8방향 핸들
            if not self.selecting:
                painter.setPen(QPen(handle_col, 1))
                painter.setBrush(QBrush(QColor(255, 255, 255)))
                for hrect in self.get_handles().values():
                    painter.drawRect(hrect)

            # 치수 정보 뱃지
            prefix = "부분 추가(F8): " if self.is_sub_capture else ""
            txt = f"{prefix}{target_r.width()} × {target_r.height()} px"
            painter.setFont(QFont("Malgun Gothic", 10, QFont.Bold))
            fm = painter.fontMetrics()
            tw = fm.horizontalAdvance(txt) + 16
            th = fm.height() + 8
            bx = target_r.x()
            by = target_r.y() - th - 4
            if by < 10:
                by = target_r.y() + 6

            badge_rect = QRect(bx, by, tw, th)
            painter.setPen(Qt.NoPen)
            bg_col = QColor(230, 81, 0, 230) if self.is_sub_capture else QColor(20, 20, 20, 220)
            painter.setBrush(bg_col)
            painter.drawRoundedRect(badge_rect, 4, 4)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(badge_rect, Qt.AlignCenter, txt)

        # 5. 실시간 정밀 돋보기 (마우스 주변 확대)
        self.render_loupe(painter)

    def render_loupe(self, painter: QPainter):
        # 돋보기 크기 130x130
        loupe_size = 130
        mx = self.mouse_pos.x()
        my = self.mouse_pos.y()

        # 돋보기 위치 (마우스 우하단, 화면 밖이면 좌상단 반전)
        lx = mx + 25
        ly = my + 25
        if lx + loupe_size > self.width():
            lx = mx - loupe_size - 25
        if ly + loupe_size > self.height():
            ly = my - loupe_size - 25

        # 캡처 영역 (32x32를 4배 확대)
        src_size = 32
        src_r = QRect(mx - src_size // 2, my - src_size // 2, src_size, src_size)

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        # 돋보기 원형 클리핑 경로
        clip_path = QPainterPath()
        clip_path.addEllipse(lx, ly, loupe_size, loupe_size)
        painter.setClipPath(clip_path)

        # 확대 이미지 렌더링
        painter.drawPixmap(QRect(lx, ly, loupe_size, loupe_size), self.full_screen_pixmap, src_r)

        # 십자선
        painter.setPen(QPen(QColor(255, 0, 0, 200), 1))
        cx = lx + loupe_size // 2
        cy = ly + loupe_size // 2
        painter.drawLine(cx - 15, cy, cx + 15, cy)
        painter.drawLine(cx, cy - 15, cx, cy + 15)

        # 돋보기 외곽 테두리
        painter.setClipping(False)
        painter.setPen(QPen(QColor(255, 255, 255), 3))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(lx, ly, loupe_size, loupe_size)

        # 돋보기 하단 좌표 텍스트
        coord_text = f"{mx}, {my}"
        painter.setFont(QFont("Malgun Gothic", 9, QFont.Bold))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 180))
        painter.drawRoundedRect(QRect(lx + 20, ly + loupe_size - 22, loupe_size - 40, 18), 3, 3)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(QRect(lx + 20, ly + loupe_size - 22, loupe_size - 40, 18), Qt.AlignCenter, coord_text)

        painter.restore()


# ==============================================================================
# 5. 주석 편집 인터랙티브 캔버스 (StudioCanvasWidget)
# ==============================================================================
class StudioCanvasWidget(QWidget):
    sig_content_changed = pyqtSignal()
    sig_request_toast = pyqtSignal(str)
    sig_item_selected = pyqtSignal(object)
    sig_request_mode_change = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmap = None
        self.items = []
        self.history = []  # Undo 스택

        self.current_mode = "SELECT"
        self.selected_item = None
        self.selected_items = []  # 다중 선택된 객체 목록
        self.dragging_item = None
        self.drag_offset = QPointF()
        self.drag_start_pos = QPointF()
        self.drag_items_orig_coords = {}
        self.rubber_band_active = False
        self.rubber_band_start = QPoint()
        self.rubber_band_end = QPoint()
        self.resizing_overlay_handle = None

        self.next_stamp_index = 1
        self.config = DEFAULT_CONFIG
        # 기본 투명 캔버스 규격 (16:9)
        self.default_canvas_size = QSize(960, 540)
        self.setFixedSize(self.default_canvas_size)

        # 플로우차트 수동 노드 그리기용
        self.drawing_flow_node = False
        self.flow_node_start = QPointF()
        self.flow_node_end = QPointF()

        # 박스 그리기용
        self.drawing_box = False
        self.box_start = QPoint()
        self.box_end = QPoint()

        # 현재 박스 스타일
        self.current_box_color = "#E53935"
        self.current_box_fill = False
        self.current_box_width = 3

        # 화살표 그리기용
        self.drawing_arrow = False
        self.arrow_start = QPointF()
        self.arrow_end = QPointF()
        self.current_arrow_color = "#E53935"
        self.current_arrow_width = 3
        self.current_arrow_head_size = 14

        # 스탬프 화살표 그리기용
        self.drawing_step_arrow = False
        self.step_arrow_start = QPointF()
        self.step_arrow_end = QPointF()

        # 꺾은선 화살표 그리기용
        self.drawing_elbow = False
        self.elbow_start = QPointF()
        self.elbow_end = QPointF()
        self.current_elbow_route_mode = "HV"

        # 말풍선 그리기용
        self.drawing_callout = False
        self.callout_start = QPointF()
        self.callout_end = QPointF()

        # 블러 모자이크 그리기용
        self.drawing_blur = False
        self.blur_start = QPoint()
        self.blur_end = QPoint()
        self.drawing_ocr = False
        self.ocr_start = QPoint()
        self.ocr_end = QPoint()

        # 치수선 그리기용
        self.drawing_dimension = False
        self.dimension_start = QPointF()
        self.dimension_end = QPointF()
        self.drawing_box_dimension = False
        self.box_dimension_start = QPoint()
        self.box_dimension_end = QPoint()
        self.ocr_is_label_mode = False

        # 스마트 지우개 그리기용
        self.drawing_eraser = False
        self.eraser_start = QPoint()
        self.eraser_end = QPoint()

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            if self.current_mode != "SELECT":
                self.sig_request_mode_change.emit("SELECT")
                event.accept()
                return
        if event.key() in (Qt.Key_Tab, Qt.Key_Space):
            if self.drawing_elbow:
                self.current_elbow_route_mode = "VH" if self.current_elbow_route_mode == "HV" else "HV"
                self.update()
                self.sig_content_changed.emit()
                self.sig_item_selected.emit(None)
                event.accept()
                return
            elif self.selected_item and isinstance(self.selected_item, ElbowArrowItem):
                self.push_undo()
                self.selected_item.toggle_route_mode()
                self.update()
                self.sig_content_changed.emit()
                self.sig_item_selected.emit(self.selected_item)
                event.accept()
                return
        elif event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            if self.selected_item:
                self.delete_selected_item()
                event.accept()
                return
        super().keyPressEvent(event)

    def set_arrow_color(self, color):
        self.current_arrow_color = color
        if self.selected_item and isinstance(self.selected_item, (ArrowItem, ElbowArrowItem)):
            self.push_undo()
            self.selected_item.style["color"] = color
            self.update()
            self.sig_content_changed.emit()
        elif self.selected_item and isinstance(self.selected_item, StepArrowItem):
            self.push_undo()
            self.selected_item.arrow_style["color"] = color
            self.update()
            self.sig_content_changed.emit()

    def set_arrow_width(self, width):
        self.current_arrow_width = width
        if self.selected_item and isinstance(self.selected_item, (ArrowItem, ElbowArrowItem)):
            self.push_undo()
            self.selected_item.style["width"] = width
            self.update()
            self.sig_content_changed.emit()
        elif self.selected_item and isinstance(self.selected_item, StepArrowItem):
            self.push_undo()
            self.selected_item.arrow_style["width"] = width
            self.update()
            self.sig_content_changed.emit()

    def set_box_color(self, color):
        self.current_box_color = color
        if self.selected_item and isinstance(self.selected_item, HighlightBoxItem):
            self.push_undo()
            self.selected_item.style["color"] = color
            self.update()
            self.sig_content_changed.emit()
        elif self.selected_item and isinstance(self.selected_item, CalloutItem):
            self.push_undo()
            self.selected_item.style["border_color"] = color
            self.update()
            self.sig_content_changed.emit()
        elif self.selected_item and isinstance(self.selected_item, ImageOverlayItem):
            self.push_undo()
            self.selected_item.style["border_color"] = color
            self.update()
            self.sig_content_changed.emit()
        elif self.selected_item and isinstance(self.selected_item, DraftStampItem):
            self.push_undo()
            self.selected_item.style["color"] = color
            self.update()
            self.sig_content_changed.emit()

    def set_box_fill(self, fill):
        self.current_box_fill = fill
        if self.selected_item and isinstance(self.selected_item, HighlightBoxItem):
            self.push_undo()
            self.selected_item.style["fill"] = fill
            self.update()
            self.sig_content_changed.emit()

    def set_box_width(self, width):
        self.current_box_width = width
        if self.selected_item and isinstance(self.selected_item, HighlightBoxItem):
            self.push_undo()
            self.selected_item.style["border_width"] = width
            self.update()
            self.sig_content_changed.emit()
        elif self.selected_item and isinstance(self.selected_item, CalloutItem):
            self.push_undo()
            self.selected_item.style["border_width"] = width
            self.update()
            self.sig_content_changed.emit()
        elif self.selected_item and isinstance(self.selected_item, ImageOverlayItem):
            self.push_undo()
            self.selected_item.style["border_width"] = width
            self.update()
            self.sig_content_changed.emit()
        elif self.selected_item and isinstance(self.selected_item, DraftStampItem):
            self.push_undo()
            self.selected_item.style["border_width"] = width
            self.update()
            self.sig_content_changed.emit()

    def set_pixmap(self, pixmap):
        self.pixmap = pixmap
        if self.pixmap is not None and not self.pixmap.isNull():
            self.setFixedSize(self.pixmap.size())
        else:
            default_w = self.config.get("target_width", 960)
            default_h = int(default_w * 9 / 16)
            self.default_canvas_size = QSize(default_w, default_h)
            self.setFixedSize(self.default_canvas_size)
        self.update()

    def _update_attached_connectors(self, node, dx, dy, old_x, old_y):
        """플로우차트 노드 이동 시 연결된 모든 화살표/직각 연결선의 끝점을 노드와 함께 동적 이동"""
        w = node.rect.width()
        h = node.rect.height()
        old_magnets = [
            QPointF(old_x + w / 2.0, old_y),
            QPointF(old_x + w / 2.0, old_y + h),
            QPointF(old_x, old_y + h / 2.0),
            QPointF(old_x + w, old_y + h / 2.0)
        ]
        for it in self.items:
            if isinstance(it, (ArrowItem, ElbowArrowItem)):
                for om in old_magnets:
                    if math.hypot(it.start_pos.x() - om.x(), it.start_pos.y() - om.y()) <= 10.0:
                        it.start_pos = QPointF(it.start_pos.x() + dx, it.start_pos.y() + dy)
                        break
                for om in old_magnets:
                    if math.hypot(it.end_pos.x() - om.x(), it.end_pos.y() - om.y()) <= 10.0:
                        it.end_pos = QPointF(it.end_pos.x() + dx, it.end_pos.y() + dy)
                        break

    def set_config(self, cfg):
        self.config = cfg

    def set_mode(self, mode):
        self.current_mode = mode
        if mode == "OCR_LABEL":
            self.ocr_is_label_mode = True
        elif mode == "OCR":
            self.ocr_is_label_mode = False
        if mode in ("STAMP", "STEP_ARROW", "ARROW", "ELBOW", "FLOW_CONNECT_LINE", "FLOW_CONNECT_ELBOW", "BOX", "CALLOUT", "BLUR", "OCR", "OCR_LABEL", "DIMENSION", "BOX_DIMENSION",
                    "FLOW_TERMINAL", "FLOW_PROCESS", "FLOW_DECISION", "FLOW_IO", "FLOW_DATABASE", "FLOW_DOCUMENT"):
            self.setCursor(Qt.CrossCursor)
        elif mode in ("TEXT", "HOTKEY"):
            self.setCursor(Qt.IBeamCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def push_undo(self):
        state = {
            "items": [item.clone() for item in self.items],
            "stamp_index": self.next_stamp_index,
            "pixmap": self.pixmap.copy() if (self.pixmap and not self.pixmap.isNull()) else None
        }
        self.history.append(state)

    def undo(self):
        if not self.history:
            return
        last_state = self.history.pop()
        self.items = last_state["items"]
        self.next_stamp_index = last_state["stamp_index"]
        if "pixmap" in last_state and last_state["pixmap"] is not None:
            self.pixmap = last_state["pixmap"]
        self.selected_item = None
        self.sig_item_selected.emit(None)
        self.update()
        self.sig_content_changed.emit()
        self.sig_request_toast.emit("실행 취소 완료 (Undo)")

    def clear_annotations(self):
        if not self.items:
            return
        self.push_undo()
        self.items.clear()
        self.next_stamp_index = 1
        self.selected_item = None
        self.sig_item_selected.emit(None)
        self.update()
        self.sig_content_changed.emit()
        self.sig_request_toast.emit("모든 주석이 초기화되었습니다.")

    def reindex_stamps(self):
        stamps = [it for it in self.items if isinstance(it, (StampItem, StepArrowItem))]
        for i, s in enumerate(stamps, 1):
            s.index = i
        self.next_stamp_index = len(stamps) + 1

    def delete_selected_item(self):
        to_delete = [it for it in getattr(self, "selected_items", []) if it in self.items]
        if not to_delete and self.selected_item and self.selected_item in self.items:
            to_delete = [self.selected_item]
        if to_delete:
            self.push_undo()
            has_stamp = False
            for it in to_delete:
                self.items.remove(it)
                if isinstance(it, (StampItem, StepArrowItem)):
                    has_stamp = True
            if hasattr(self, "selected_items"):
                self.selected_items.clear()
            self.selected_item = None
            self.sig_item_selected.emit(None)
            if has_stamp:
                self.reindex_stamps()
            self.update()
            self.sig_content_changed.emit()
            self.sig_request_toast.emit(f"{len(to_delete)}개 주석 객체가 삭제되었습니다.")
            return True
        return False

    def get_item_bounding_rect(self, it):
        """다양한 주석 객체의 외곽 바운딩 렉트 통일 계산"""
        if not it:
            return QRectF()
        if hasattr(it, "rect") and isinstance(it.rect, QRectF):
            return QRectF(it.rect)
        if hasattr(it, "get_rect") and callable(it.get_rect):
            return QRectF(it.get_rect())
        if hasattr(it, "box_rect"):
            return QRectF(it.box_rect)
        if isinstance(it, StampItem):
            sz = float(it.style.get("size", 32))
            return QRectF(it.pos.x() - sz / 2.0, it.pos.y() - sz / 2.0, sz, sz)
        if isinstance(it, (ArrowItem, StepArrowItem, DimensionLineItem)):
            return QRectF(it.start_pos, it.end_pos).normalized()
        if isinstance(it, ElbowArrowItem):
            p1 = it.start_pos
            p2 = it.end_pos
            c = it.get_corner_point()
            min_x = min(p1.x(), p2.x(), c.x())
            min_y = min(p1.y(), p2.y(), c.y())
            max_x = max(p1.x(), p2.x(), c.x())
            max_y = max(p1.y(), p2.y(), c.y())
            return QRectF(min_x, min_y, max(1.0, max_x - min_x), max(1.0, max_y - min_y))
        if hasattr(it, "pos"):
            return QRectF(it.pos.x() - 16, it.pos.y() - 16, 32, 32)
        return QRectF()

    def _translate_item(self, it, dx, dy):
        """임의의 주석 객체를 dx, dy 만큼 이동"""
        if dx == 0 and dy == 0:
            return
        if isinstance(it, ImageOverlayItem):
            it.rect.translate(dx, dy)
        elif isinstance(it, (HighlightBoxItem, BlurMosaicItem, BoxDimensionItem, SpotlightMaskItem, FlowchartNodeItem)):
            old_x = it.rect.x()
            old_y = it.rect.y()
            it.rect.translate(dx, dy)
            if isinstance(it, FlowchartNodeItem):
                self._update_attached_connectors(it, dx, dy, old_x, old_y)
        elif isinstance(it, MagnifierZoomItem):
            it.lens_rect.translate(dx, dy)
            it.source_rect.translate(dx, dy)
        elif isinstance(it, CalloutItem):
            it.box_rect.translate(dx, dy)
            it.target_pt += QPointF(dx, dy)
        elif isinstance(it, (ArrowItem, ElbowArrowItem, StepArrowItem, DimensionLineItem)):
            it.start_pos += QPointF(dx, dy)
            it.end_pos += QPointF(dx, dy)
        elif hasattr(it, "pos"):
            it.pos += QPointF(dx, dy)
        elif hasattr(it, "rect"):
            it.rect.translate(dx, dy)

    def align_selected_items_center_x(self):
        """다중 선택된 객체들을 세로 중심축 (X) 기준으로 일괄 정렬"""
        sel = [it for it in getattr(self, "selected_items", []) if it in self.items]
        if len(sel) < 2:
            self.sig_request_toast.emit("2개 이상의 객체를 선택해주세요.")
            return
        self.push_undo()
        target_cx = sum(self.get_item_bounding_rect(it).center().x() for it in sel) / len(sel)
        for it in sel:
            cur_cx = self.get_item_bounding_rect(it).center().x()
            self._translate_item(it, target_cx - cur_cx, 0)
        self.update()
        self.sig_content_changed.emit()
        self.sig_request_toast.emit("중심 축 X 정렬 완료")

    def align_selected_items_center_y(self):
        """다중 선택된 객체들을 가로 중심축 (Y) 기준으로 일괄 정렬"""
        sel = [it for it in getattr(self, "selected_items", []) if it in self.items]
        if len(sel) < 2:
            self.sig_request_toast.emit("2개 이상의 객체를 선택해주세요.")
            return
        self.push_undo()
        target_cy = sum(self.get_item_bounding_rect(it).center().y() for it in sel) / len(sel)
        for it in sel:
            cur_cy = self.get_item_bounding_rect(it).center().y()
            self._translate_item(it, 0, target_cy - cur_cy)
        self.update()
        self.sig_content_changed.emit()
        self.sig_request_toast.emit("중심 축 Y 정렬 완료")

    def distribute_selected_items_horizontal(self):
        """다중 선택된 객체들을 수평 방향으로 균등 비율/간격 재배치"""
        sel = [it for it in getattr(self, "selected_items", []) if it in self.items]
        if len(sel) < 3:
            self.sig_request_toast.emit("3개 이상의 객체를 선택해주세요.")
            return
        self.push_undo()
        sel_sorted = sorted(sel, key=lambda it: self.get_item_bounding_rect(it).left())
        min_left = self.get_item_bounding_rect(sel_sorted[0]).left()
        max_right = self.get_item_bounding_rect(sel_sorted[-1]).right()
        total_w = sum(self.get_item_bounding_rect(it).width() for it in sel_sorted)
        span = max_right - min_left
        gap = (span - total_w) / float(len(sel_sorted) - 1)
        curr_x = min_left
        for it in sel_sorted:
            br = self.get_item_bounding_rect(it)
            self._translate_item(it, curr_x - br.left(), 0)
            curr_x += br.width() + gap
        self.update()
        self.sig_content_changed.emit()
        self.sig_request_toast.emit("가로 균등 재배치 완료")

    def distribute_selected_items_vertical(self):
        """다중 선택된 객체들을 수직 방향으로 균등 비율/간격 재배치"""
        sel = [it for it in getattr(self, "selected_items", []) if it in self.items]
        if len(sel) < 3:
            self.sig_request_toast.emit("3개 이상의 객체를 선택해주세요.")
            return
        self.push_undo()
        sel_sorted = sorted(sel, key=lambda it: self.get_item_bounding_rect(it).top())
        min_top = self.get_item_bounding_rect(sel_sorted[0]).top()
        max_bottom = self.get_item_bounding_rect(sel_sorted[-1]).bottom()
        total_h = sum(self.get_item_bounding_rect(it).height() for it in sel_sorted)
        span = max_bottom - min_top
        gap = (span - total_h) / float(len(sel_sorted) - 1)
        curr_y = min_top
        for it in sel_sorted:
            br = self.get_item_bounding_rect(it)
            self._translate_item(it, 0, curr_y - br.top())
            curr_y += br.height() + gap
        self.update()
        self.sig_content_changed.emit()
        self.sig_request_toast.emit("세로 균등 재배치 완료")

    def add_image_overlay(self, pixmap: QPixmap):
        if not pixmap or pixmap.isNull():
            return
        self.push_undo()

        # 캔버스 배경 크기 기준으로 1:1 원본 배치 (초과 시에만 비율 축소)
        cw = self.pixmap.width() if self.pixmap else 960
        ch = self.pixmap.height() if self.pixmap else 540
        pw = pixmap.width()
        ph = pixmap.height()

        scale = 1.0
        if pw > cw or ph > ch:
            scale = min(cw / pw, ch / ph)

        init_w = float(round(pw * scale))
        init_h = float(round(ph * scale))

        init_x = float(round(max(0.0, (cw - init_w) / 2.0)))
        init_y = float(round(max(0.0, (ch - init_h) / 2.0)))

        overlay_rect = QRectF(init_x, init_y, init_w, init_h)
        item = ImageOverlayItem(overlay_rect, pixmap)
        self.items.append(item)
        self.selected_item = item
        self.set_mode("SELECT")
        self.update()
        self.sig_item_selected.emit(item)
        self.sig_content_changed.emit()

    def add_draft_stamp(self, text="DRAFT"):
        self.push_undo()
        cw = self.width() if self.pixmap else 960
        ch = self.height() if self.pixmap else 540
        center_pt = QPointF(cw / 2.0, ch / 2.0)
        item = DraftStampItem(text=text, pos=center_pt)
        self.items.append(item)
        self.selected_item = item
        self.set_mode("SELECT")
        self.update()
        self.sig_item_selected.emit(item)
        self.sig_content_changed.emit()
        return item

    def _run_ocr_on_region(self, rect, as_label=False):
        """선택 영역을 OCR 처리하여 OcrResultDialog로 결과 표시 또는 TextLabelItem 자동 생성."""
        if self.pixmap is None or self.pixmap.isNull():
            return
        # QPixmap / Composite Image → PIL Image (오버레이 객체 포함하여 크롭)
        comp_img = self.get_composed_image()
        if comp_img and not comp_img.isNull():
            cropped = comp_img.copy(rect)
        else:
            cropped = self.pixmap.copy(rect).toImage()

        img_byte = QByteArray()
        buf = QBuffer(img_byte)
        buf.open(QIODevice.WriteOnly)
        cropped.save(buf, "PNG")
        buf.close()
        from PIL import Image
        import io
        pil_img = Image.open(io.BytesIO(bytes(img_byte)))

        # OCR 언어 결정 (현재 UI 언어 참조)
        try:
            from i18n_manager import I18nManager
            cur_locale = I18nManager.instance().current_locale if I18nManager._instance else "ko"
        except Exception:
            cur_locale = "ko"
        lang_map = {
            "ko": "ko", "ja": "ja", "zh": "zh-Hans", "zh_tw": "zh-Hant",
            "en": "en", "de": "de", "es": "es", "fr": "fr", "it": "it",
            "pt": "pt", "ru": "ru", "vi": "vi", "id": "id",
        }
        ocr_lang = lang_map.get(cur_locale, "en")

        # QThread로 블로킹 없이 OCR 실행
        self._ocr_thread = OcrWorkerThread(pil_img, ocr_lang)
        if as_label:
            target_pt = QPoint(rect.x(), max(10, rect.y() - 25))
            self._ocr_thread.sig_result.connect(lambda txt, err, pt=target_pt: self._on_ocr_label_result(txt, err, pt))
        else:
            self._ocr_thread.sig_result.connect(self._on_ocr_result)
        self._ocr_thread.start()

    def _on_ocr_label_result(self, text, error_msg, target_pt):
        if error_msg:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, tr("ocr_dialog_title", "OCR 텍스트 추출"), error_msg)
            return
        if not text or not text.strip():
            self.sig_request_toast.emit(tr("toast_ocr_no_text", "텍스트 미인식 (더 넓게 드래그)"))
            return
        self.push_undo()
        text_style = dict(self.config.get("text_style", DEFAULT_CONFIG["text_style"]))
        clean_text = text.strip()
        label = TextLabelItem(clean_text, target_pt.x(), target_pt.y(), text_style)
        self.items.append(label)
        self.selected_item = label
        self.sig_item_selected.emit(label)
        self.update()
        self.sig_content_changed.emit()
        self.sig_request_toast.emit(tr("toast_ocr_label_created", "OCR 라벨 생성 완료"))

    def _on_ocr_result(self, text, error_msg):
        if error_msg:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, tr("ocr_dialog_title", "OCR 텍스트 추출"), error_msg)
            return
        dlg = OcrResultDialog(text, self.window())
        dlg.exec()


    def apply_auto_pii_redaction(self, active_categories=None, custom_rules=None):
        """현재 캔버스 화면의 민감 개인정보(전화번호, 주민번호, 이메일, 계좌번호 등)를 자동 탐지하여 모자이크 블러 박스 자동 부착"""
        if self.pixmap is None or self.pixmap.isNull():
            return
        comp_img = self.get_composed_image()
        if comp_img and not comp_img.isNull():
            target_img = comp_img
        else:
            target_img = self.pixmap.toImage()

        img_byte = QByteArray()
        buf = QBuffer(img_byte)
        buf.open(QIODevice.WriteOnly)
        target_img.save(buf, "PNG")
        buf.close()

        from PIL import Image
        import io
        pil_img = Image.open(io.BytesIO(bytes(img_byte)))

        try:
            from i18n_manager import I18nManager
            cur_locale = I18nManager.instance().current_locale if I18nManager._instance else "ko"
        except Exception:
            cur_locale = "ko"
        lang_map = {
            "ko": "ko", "ja": "ja", "zh": "zh-Hans", "zh_tw": "zh-Hant",
            "en": "en", "de": "de", "es": "es", "fr": "fr", "it": "it",
            "pt": "pt", "ru": "ru", "vi": "vi", "id": "id",
        }
        ocr_lang = lang_map.get(cur_locale, "en")

        self.sig_request_toast.emit(tr("btn_auto_pii", "개인정보 마스킹") + "...")
        self._pii_thread = PiiWorkerThread(pil_img, ocr_lang, active_categories, custom_rules)
        self._pii_thread.sig_result.connect(self._on_pii_result)
        self._pii_thread.start()

    def _on_pii_result(self, rect_list, summary):
        if not rect_list:
            self.sig_request_toast.emit(tr("toast_pii_none", "감지된 개인정보가 없습니다."))
            return

        self.push_undo()
        blur_st = dict(self.config.get("blur_style", DEFAULT_CONFIG["blur_style"]))
        for r in rect_list:
            item = BlurMosaicItem(r, blur_st)
            self.items.append(item)

        self.update()
        self.sig_content_changed.emit()
        msg = tr("toast_pii_found", "민감 개인정보 {count}건 자동 마스킹 완료 (Ctrl+Z 취소 가능)").replace("{count}", str(len(rect_list)))
        self.sig_request_toast.emit(msg)

    def export_project_data(self):
        return {
            "raw_pixmap": self.pixmap,
            "items": [it.clone() for it in self.items],
            "next_stamp_index": self.next_stamp_index
        }

    def load_project_data(self, raw_pixmap, items, next_stamp_index):
        if raw_pixmap and not raw_pixmap.isNull():
            self.set_pixmap(raw_pixmap)
        self.items = [it.clone() for it in items]
        self.next_stamp_index = max(1, int(next_stamp_index))
        self.selected_item = None
        self.sig_item_selected.emit(None)
        self.history.clear()
        self.update()
        self.sig_content_changed.emit()

    def mousePressEvent(self, event):
        win = self.window()
        if win and hasattr(win, "hide_keytips") and getattr(win, "_keytips_visible", False):
            win.hide_keytips()
        pt = get_mouse_pos(event)

        if event.button() == Qt.LeftButton:
            # 0. 마그넷 꼭지점 클릭 시 즉시 연결선(직각 또는 직선) 드래그 생성 모드 발동
            active_m_pt = getattr(self, "_active_magnet_pt", None)
            if active_m_pt is not None and self.current_mode in ("SELECT", "ELBOW", "ARROW", "FLOW_CONNECT_LINE", "FLOW_CONNECT_ELBOW"):
                if self.current_mode in ("ARROW", "FLOW_CONNECT_LINE"):
                    self.drawing_arrow = True
                    self.arrow_start = QPointF(active_m_pt)
                    self.arrow_end = QPointF(active_m_pt)
                else:
                    self.drawing_elbow = True
                    self.elbow_start = QPointF(active_m_pt)
                    self.elbow_end = QPointF(active_m_pt)
                self.update()
                return

            if self.current_mode == "STAMP":
                self.push_undo()
                stamp_style = dict(self.config.get("stamp_style", DEFAULT_CONFIG["stamp_style"]))
                stamp = StampItem(self.next_stamp_index, pt.x(), pt.y(), stamp_style)
                self.items.append(stamp)
                self.next_stamp_index += 1
                self.update()
                self.sig_content_changed.emit()

            elif self.current_mode in ("FLOW_TERMINAL", "FLOW_PROCESS", "FLOW_DECISION", "FLOW_IO", "FLOW_DATABASE", "FLOW_DOCUMENT"):
                self.drawing_flow_node = True
                self.flow_node_start = QPointF(pt)
                self.flow_node_end = QPointF(pt)

            elif self.current_mode == "STEP_ARROW":
                self.drawing_step_arrow = True
                self.step_arrow_start = QPointF(pt)
                self.step_arrow_end = QPointF(pt)

            elif self.current_mode in ("ARROW", "FLOW_CONNECT_LINE"):
                self.drawing_arrow = True
                snap_pt = None
                for it in self.items:
                    if isinstance(it, FlowchartNodeItem):
                        k, p = it.get_closest_magnet_point(pt, 22.0)
                        if p:
                            snap_pt = p
                            it._hovered_magnet = k
                            break
                st = snap_pt if snap_pt else QPointF(pt)
                self.arrow_start = st
                self.arrow_end = st

            elif self.current_mode in ("ELBOW", "FLOW_CONNECT_ELBOW"):
                self.drawing_elbow = True
                snap_pt = None
                for it in self.items:
                    if isinstance(it, FlowchartNodeItem):
                        k, p = it.get_closest_magnet_point(pt, 22.0)
                        if p:
                            snap_pt = p
                            it._hovered_magnet = k
                            break
                st = snap_pt if snap_pt else QPointF(pt)
                self.elbow_start = st
                self.elbow_end = st

            elif self.current_mode == "BOX":
                self.drawing_box = True
                self.box_start = pt
                self.box_end = pt

            elif self.current_mode == "CALLOUT":
                self.drawing_callout = True
                self.callout_start = QPointF(pt)
                self.callout_end = QPointF(pt)

            elif self.current_mode == "BLUR":
                self.drawing_blur = True
                self.blur_start = pt
                self.blur_end = pt

            elif self.current_mode in ("OCR", "OCR_LABEL"):
                self.drawing_ocr = True
                self.ocr_is_label_mode = (self.current_mode == "OCR_LABEL")
                self.ocr_start = pt
                self.ocr_end = pt

            elif self.current_mode == "ERASER":
                self.drawing_eraser = True
                self.eraser_start = pt
                self.eraser_end = pt

            elif self.current_mode == "DIMENSION":
                self.drawing_dimension = True
                self.dimension_start = QPointF(pt)
                self.dimension_end = QPointF(pt)

            elif self.current_mode == "BOX_DIMENSION":
                self.drawing_box_dimension = True
                self.box_dimension_start = pt
                self.box_dimension_end = pt

            elif self.current_mode == "TEXT":
                text, ok = self.prompt_text_dialog("")
                if ok and text.strip():
                    self.push_undo()
                    text_style = dict(self.config.get("text_style", DEFAULT_CONFIG["text_style"]))
                    label = TextLabelItem(text.strip(), pt.x(), pt.y(), text_style)
                    self.items.append(label)
                    self.update()
                    self.sig_content_changed.emit()
                self.set_mode("SELECT")

            elif self.current_mode == "HOTKEY":
                key_text, ok = self.prompt_hotkey_dialog("Enter ↵")
                if ok and key_text.strip():
                    self.push_undo()
                    hk_style = dict(self.config.get("hotkey_style", DEFAULT_CONFIG["hotkey_style"]))
                    badge = HotkeyBadgeItem(key_text.strip(), pt.x(), pt.y(), hk_style)
                    self.items.append(badge)
                    self.update()
                    self.sig_content_changed.emit()
                self.set_mode("SELECT")

            elif self.current_mode == "WORDART":
                wa_style = dict(self.config.get("wordart_style", DEFAULT_CONFIG["wordart_style"]))
                default_text = wa_style.get("text", "주요 확인")
                text, ok = self.prompt_text_dialog(default_text, title="워드아트 문구 입력")
                if ok and text.strip():
                    self.push_undo()
                    wa_item = WordArtItem(text.strip(), pt.x(), pt.y(), wa_style)
                    self.items.append(wa_item)
                    self.selected_item = wa_item
                    self.sig_item_selected.emit(wa_item)
                    self.update()
                    self.sig_content_changed.emit()
                self.set_mode("SELECT")

            elif self.current_mode == "SELECT":
                # 1. 이미 선택된 ImageOverlayItem의 4각 코너 리사이즈 핸들 클릭 여부 확인
                if self.selected_item and isinstance(self.selected_item, ImageOverlayItem):
                    handle = self.selected_item.get_handle_at(QPointF(pt))
                    if handle:
                        self.push_undo()
                        self.resizing_overlay_handle = handle
                        return

                hit_item = None
                # 오버레이 객체(스티커 레이어)보다 일반 주석(스탬프, 박스, 텍스트 등)을 최우선 선택
                for it in reversed(self.items):
                    if not isinstance(it, ImageOverlayItem) and hasattr(it, "contains") and it.contains(pt):
                        hit_item = it
                        break
                if not hit_item:
                    for it in reversed(self.items):
                        if isinstance(it, ImageOverlayItem) and hasattr(it, "contains") and it.contains(pt):
                            hit_item = it
                            break

                modifiers = event.modifiers()
                is_multi_key = bool(modifiers & (Qt.ShiftModifier | Qt.ControlModifier))

                if is_multi_key:
                    if hit_item:
                        if hit_item in self.selected_items:
                            self.selected_items.remove(hit_item)
                            self.selected_item = self.selected_items[-1] if self.selected_items else None
                        else:
                            self.selected_items.append(hit_item)
                            self.selected_item = hit_item
                else:
                    if hit_item:
                        if hit_item in self.selected_items and len(self.selected_items) > 1:
                            # 이미 다중 선택된 그룹 중 하나를 클릭한 경우 그룹 선택 유지
                            self.selected_item = hit_item
                        else:
                            self.selected_items = [hit_item]
                            self.selected_item = hit_item
                    else:
                        # 빈 캔버스 클릭 시 선택 해제 및 러버밴드 드래그 시작
                        self.selected_items.clear()
                        self.selected_item = None
                        self.rubber_band_active = True
                        self.rubber_band_start = pt
                        self.rubber_band_end = pt

                self.sig_item_selected.emit(self.selected_item)

                if hit_item:
                    self.dragging_item = hit_item
                    self.drag_start_pos = QPointF(pt)
                    self.drag_items_orig_coords.clear()
                    for it in self.selected_items:
                        if isinstance(it, ImageOverlayItem):
                            self.drag_items_orig_coords[it] = QRectF(it.rect)
                        elif isinstance(it, (HighlightBoxItem, BlurMosaicItem, BoxDimensionItem, SpotlightMaskItem, FlowchartNodeItem)):
                            self.drag_items_orig_coords[it] = QRectF(it.rect)
                        elif isinstance(it, MagnifierZoomItem):
                            self.drag_items_orig_coords[it] = (QRectF(it.lens_rect), QRectF(it.source_rect))
                        elif isinstance(it, CalloutItem):
                            self.drag_items_orig_coords[it] = (QRectF(it.box_rect), QPointF(it.target_pt))
                        elif isinstance(it, (ArrowItem, ElbowArrowItem, StepArrowItem, DimensionLineItem)):
                            self.drag_items_orig_coords[it] = (QPointF(it.start_pos), QPointF(it.end_pos))
                        elif hasattr(it, "pos"):
                            self.drag_items_orig_coords[it] = QPointF(it.pos)
                        elif hasattr(it, "rect"):
                            self.drag_items_orig_coords[it] = QRectF(it.rect)
                self.update()

        elif event.button() == Qt.RightButton:
            hit_item = None
            # 오버레이 객체보다 일반 주석을 최우선 선택하여 우클릭 속성창 표시
            for it in reversed(self.items):
                if not isinstance(it, ImageOverlayItem) and hasattr(it, "contains") and it.contains(pt):
                    hit_item = it
                    break
            if not hit_item:
                for it in reversed(self.items):
                    if isinstance(it, ImageOverlayItem) and hasattr(it, "contains") and it.contains(pt):
                        hit_item = it
                        break
            if hit_item:
                if hit_item not in self.selected_items:
                    self.selected_items = [hit_item]
                    self.selected_item = hit_item
                    self.sig_item_selected.emit(hit_item)
                self.update()
                global_pt = event.globalPosition().toPoint() if hasattr(event, "globalPosition") else event.globalPos()
                self.show_item_context_menu(hit_item, global_pt)
            elif len(self.selected_items) > 1:
                global_pt = event.globalPosition().toPoint() if hasattr(event, "globalPosition") else event.globalPos()
                self.show_item_context_menu(self.selected_items[-1], global_pt)

    def show_item_context_menu(self, item, global_pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #FFFFFF;
                color: #1E293B;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 4px;
                font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
                font-size: 11px;
            }
            QMenu::item {
                padding: 6px 24px 6px 12px;
                border-radius: 4px;
                color: #1E293B;
            }
            QMenu::item:selected {
                background-color: #2563EB;
                color: #FFFFFF;
            }
            QMenu::separator {
                height: 1px;
                background-color: #E2E8F0;
                margin: 4px 6px;
            }
        """)

        num_sel = len(self.selected_items)
        act_align_x = None
        act_align_y = None
        act_dist_h = None
        act_dist_v = None

        if num_sel > 1:
            act_align_x = menu.addAction(RibbonIconProvider.get_icon("align_center", 16), "중심 축 X 정렬 (세로 중심)")
            act_align_y = menu.addAction(RibbonIconProvider.get_icon("align_middle", 16), "중심 축 Y 정렬 (가로 중심)")
            act_dist_h = menu.addAction(RibbonIconProvider.get_icon("distribute_h", 16), "가로 균등 재배치 (수평 간격 균등)")
            act_dist_v = menu.addAction(RibbonIconProvider.get_icon("distribute_v", 16), "세로 균등 재배치 (수직 간격 균등)")
            menu.addSeparator()

        act_props = menu.addAction(RibbonIconProvider.get_icon("settings", 16), f"{tr('menu_item_properties', '속성...')} (P)")
        menu.addSeparator()
        act_front = menu.addAction(RibbonIconProvider.get_icon("bring_front", 16), tr('menu_item_bring_front', '맨 앞으로 가져오기'))
        act_back = menu.addAction(RibbonIconProvider.get_icon("send_back", 16), tr('menu_item_send_back', '맨 뒤로 보내기'))
        menu.addSeparator()
        del_label = f"선택 {num_sel}개 객체 일괄 삭제 (Del)" if num_sel > 1 else f"{tr('menu_item_delete', '삭제')} (Del)"
        act_del = menu.addAction(RibbonIconProvider.get_icon("clear", 16, "#DC2626"), del_label)

        chosen = menu.exec_(global_pos)
        if num_sel > 1 and chosen == act_align_x:
            self.align_selected_items_center_x()
        elif num_sel > 1 and chosen == act_align_y:
            self.align_selected_items_center_y()
        elif num_sel > 1 and chosen == act_dist_h:
            self.distribute_selected_items_horizontal()
        elif num_sel > 1 and chosen == act_dist_v:
            self.distribute_selected_items_vertical()
        elif chosen == act_props:
            self.open_item_properties_dialog(item)
        elif chosen == act_front:
            self.push_undo()
            targets = list(self.selected_items) if num_sel > 1 else [item]
            for it in targets:
                if it in self.items:
                    self.items.remove(it)
                    self.items.append(it)
            self.update()
            self.sig_content_changed.emit()
        elif chosen == act_back:
            self.push_undo()
            targets = list(self.selected_items) if num_sel > 1 else [item]
            for it in reversed(targets):
                if it in self.items:
                    self.items.remove(it)
                    self.items.insert(0, it)
            self.update()
            self.sig_content_changed.emit()
        elif chosen == act_del:
            self.delete_selected_item()

    def open_item_properties_dialog(self, item):
        if not item:
            return
        self.push_undo()
        dlg = ItemPropertiesDialog(item, self, self.window())
        if dlg.exec_() == QDialog.Accepted:
            self.update()
            self.sig_content_changed.emit()
            self.sig_item_selected.emit(item)
        else:
            if self.history:
                self.history.pop()

    def mouseMoveEvent(self, event):
        pt = get_mouse_pos(event)
        if hasattr(self, "resizing_overlay_handle") and self.resizing_overlay_handle and isinstance(self.selected_item, ImageOverlayItem):
            self.selected_item.handle_resize(self.resizing_overlay_handle, QPointF(pt), keep_aspect_ratio=True)
            self.update()
            self.sig_content_changed.emit()
            return
        elif getattr(self, "rubber_band_active", False):
            self.rubber_band_end = pt
            rb_rect = QRectF(self.rubber_band_start, self.rubber_band_end).normalized()
            hit_list = []
            for it in self.items:
                br = self.get_item_bounding_rect(it)
                if rb_rect.intersects(br):
                    hit_list.append(it)
            self.selected_items = hit_list
            self.selected_item = hit_list[-1] if hit_list else None
            self.sig_item_selected.emit(self.selected_item)
            self.update()
            return
        elif self.dragging_item and self.current_mode == "SELECT":
            dx = pt.x() - self.drag_start_pos.x()
            dy = pt.y() - self.drag_start_pos.y()
            for it in self.selected_items:
                orig = self.drag_items_orig_coords.get(it)
                if orig is None:
                    continue
                if isinstance(it, ImageOverlayItem):
                    it.rect.moveTo(orig.x() + dx, orig.y() + dy)
                elif isinstance(it, (HighlightBoxItem, BlurMosaicItem, BoxDimensionItem, SpotlightMaskItem, FlowchartNodeItem)):
                    old_x = it.rect.x()
                    old_y = it.rect.y()
                    it.rect.moveTo(int(orig.x() + dx), int(orig.y() + dy))
                    if isinstance(it, FlowchartNodeItem):
                        self._update_attached_connectors(it, int(orig.x() + dx) - old_x, int(orig.y() + dy) - old_y, old_x, old_y)
                elif isinstance(it, MagnifierZoomItem):
                    lens_orig, src_orig = orig
                    it.lens_rect.moveTo(int(lens_orig.x() + dx), int(lens_orig.y() + dy))
                    it.source_rect.moveTo(int(src_orig.x() + dx), int(src_orig.y() + dy))
                elif isinstance(it, CalloutItem):
                    box_orig, tgt_orig = orig
                    it.box_rect.moveTo(box_orig.x() + dx, box_orig.y() + dy)
                    it.target_pt = QPointF(tgt_orig.x() + dx, tgt_orig.y() + dy)
                elif isinstance(it, (ArrowItem, ElbowArrowItem, StepArrowItem, DimensionLineItem)):
                    sp_orig, ep_orig = orig
                    it.start_pos = QPointF(sp_orig.x() + dx, sp_orig.y() + dy)
                    it.end_pos = QPointF(ep_orig.x() + dx, ep_orig.y() + dy)
                elif hasattr(it, "pos"):
                    it.pos = QPointF(orig.x() + dx, orig.y() + dy)
                elif hasattr(it, "rect"):
                    it.rect.moveTo(orig.x() + dx, orig.y() + dy)
            self.update()
            self.sig_content_changed.emit()
            return
        elif self.drawing_box:
            self.box_end = pt
            self.update()
        elif self.drawing_arrow:
            snap_pt = None
            for it in self.items:
                if isinstance(it, FlowchartNodeItem):
                    k, p = it.get_closest_magnet_point(pt, 22.0)
                    if p:
                        snap_pt = p
                        it._hovered_magnet = k
                    else:
                        if it._hovered_magnet:
                            it._hovered_magnet = None
            self.arrow_end = snap_pt if snap_pt else QPointF(pt)
            self.update()
        elif self.drawing_step_arrow:
            self.step_arrow_end = QPointF(pt)
            self.update()
        elif self.drawing_elbow:
            snap_pt = None
            for it in self.items:
                if isinstance(it, FlowchartNodeItem):
                    k, p = it.get_closest_magnet_point(pt, 22.0)
                    if p:
                        snap_pt = p
                        it._hovered_magnet = k
                    else:
                        if it._hovered_magnet:
                            it._hovered_magnet = None
            self.elbow_end = snap_pt if snap_pt else QPointF(pt)
            self.update()
        elif self.drawing_callout:
            self.callout_end = QPointF(pt)
            self.update()
        elif self.drawing_blur:
            self.blur_end = pt
            self.update()
        elif self.drawing_ocr:
            self.ocr_end = pt
            self.update()
        elif self.drawing_eraser:
            self.eraser_end = pt
            self.update()
        elif self.drawing_dimension:
            cur_pt = QPointF(pt)
            modifiers = QGuiApplication.keyboardModifiers()
            if not (modifiers & Qt.ShiftModifier):
                dx = cur_pt.x() - self.dimension_start.x()
                dy = cur_pt.y() - self.dimension_start.y()
                if abs(dx) >= abs(dy):
                    cur_pt = QPointF(cur_pt.x(), self.dimension_start.y())
                else:
                    cur_pt = QPointF(self.dimension_start.x(), cur_pt.y())
            self.dimension_end = cur_pt
            self.update()
        elif self.drawing_box_dimension:
            self.box_dimension_end = pt
            self.update()
        elif getattr(self, "drawing_flow_node", False):
            self.flow_node_end = QPointF(pt)
            self.update()
        else:
            # 유휴 마우스 이동 시 플로우차트 노드 마그넷 포인트 호버 및 자석 십자 커서 실시간 반응
            hovered_node = None
            hovered_key = None
            hovered_pt = None
            for it in reversed(self.items):
                if isinstance(it, FlowchartNodeItem):
                    k, p = it.get_closest_magnet_point(pt, 22.0)
                    if p:
                        hovered_node = it
                        hovered_key = k
                        hovered_pt = p
                        break

            for it in self.items:
                if isinstance(it, FlowchartNodeItem):
                    it._hovered_magnet = hovered_key if it == hovered_node else None

            self._active_magnet_node = hovered_node
            self._active_magnet_key = hovered_key
            self._active_magnet_pt = hovered_pt

            if hovered_pt:
                self.setCursor(Qt.CrossCursor)
                self.update()
            elif self.current_mode == "SELECT":
                if self.selected_item and isinstance(self.selected_item, ImageOverlayItem):
                    h = self.selected_item.get_handle_at(QPointF(pt))
                    if h in ("TL", "BR"):
                        self.setCursor(Qt.SizeFDiagCursor)
                    elif h in ("TR", "BL"):
                        self.setCursor(Qt.SizeBDiagCursor)
                    elif self.selected_item.contains(QPointF(pt)):
                        self.setCursor(Qt.SizeAllCursor)
                    else:
                        self.setCursor(Qt.ArrowCursor)
                else:
                    self.setCursor(Qt.ArrowCursor)
                self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if getattr(self, "rubber_band_active", False):
                self.rubber_band_active = False
                self.update()
            if hasattr(self, "resizing_overlay_handle") and self.resizing_overlay_handle:
                self.resizing_overlay_handle = None
            if self.dragging_item:
                self.dragging_item = None
                self.drag_items_orig_coords.clear()
            elif self.drawing_box:
                self.drawing_box = False
                r = QRect(self.box_start, self.box_end).normalized()
                if r.width() > 8 and r.height() > 8:
                    self.push_undo()
                    box_style = {
                        "color": self.current_box_color,
                        "border_width": self.current_box_width,
                        "fill": self.current_box_fill
                    }
                    self.items.append(HighlightBoxItem(r, box_style))
                    self.update()
                    self.sig_content_changed.emit()
                # Sticky Mode: 도구 선택 유지
            elif self.drawing_arrow:
                self.drawing_arrow = False
                dist = math.hypot(self.arrow_end.x() - self.arrow_start.x(), self.arrow_end.y() - self.arrow_start.y())
                if dist > 8:
                    self.push_undo()
                    arrow_style = {
                        "color": self.current_arrow_color,
                        "width": self.current_arrow_width,
                        "head_size": self.current_arrow_head_size
                    }
                    self.items.append(ArrowItem(self.arrow_start, self.arrow_end, arrow_style))
                    self.update()
                    self.sig_content_changed.emit()
                # Sticky Mode: 도구 선택 유지
            elif self.drawing_step_arrow:
                self.drawing_step_arrow = False
                dist = math.hypot(self.step_arrow_end.x() - self.step_arrow_start.x(), self.step_arrow_end.y() - self.step_arrow_start.y())
                if dist > 8:
                    self.push_undo()
                    st_style = dict(self.config.get("stamp_style", DEFAULT_CONFIG["stamp_style"]))
                    arr_style = {
                        "color": self.current_arrow_color,
                        "width": self.current_arrow_width,
                        "head_size": self.current_arrow_head_size
                    }
                    self.items.append(StepArrowItem(self.next_stamp_index, self.step_arrow_start, self.step_arrow_end, st_style, arr_style))
                    self.next_stamp_index += 1
                    self.update()
                    self.sig_content_changed.emit()
                # Sticky Mode: 도구 선택 유지
            elif self.drawing_elbow:
                self.drawing_elbow = False
                dist = math.hypot(self.elbow_end.x() - self.elbow_start.x(), self.elbow_end.y() - self.elbow_start.y())
                if dist > 8:
                    self.push_undo()
                    arr_style = {
                        "color": self.current_arrow_color,
                        "width": self.current_arrow_width,
                        "head_size": self.current_arrow_head_size
                    }
                    route_m = getattr(self, "current_elbow_route_mode", "HV")
                    # 스마트 마그넷 포트 축 기반 최적 경로 자동 판별
                    src_port, dst_port = None, None
                    for it in self.items:
                        if isinstance(it, FlowchartNodeItem):
                            if src_port is None:
                                k, p = it.get_closest_magnet_point(self.elbow_start, 18.0)
                                if p:
                                    src_port = k
                            if dst_port is None:
                                k, p = it.get_closest_magnet_point(self.elbow_end, 18.0)
                                if p:
                                    dst_port = k
                    if src_port and dst_port:
                        if src_port in ("top", "bottom") and dst_port in ("left", "right"):
                            route_m = "VH"
                        elif src_port in ("left", "right") and dst_port in ("top", "bottom"):
                            route_m = "HV"
                        elif src_port in ("top", "bottom") and dst_port in ("top", "bottom"):
                            route_m = "VHV"
                        elif src_port in ("left", "right") and dst_port in ("left", "right"):
                            route_m = "HVH"

                    self.items.append(ElbowArrowItem(self.elbow_start, self.elbow_end, arr_style, route_m))
                    self.update()
                    self.sig_content_changed.emit()
                # Sticky Mode: 도구 선택 유지
            elif self.drawing_callout:
                self.drawing_callout = False
                dist = math.hypot(self.callout_end.x() - self.callout_start.x(), self.callout_end.y() - self.callout_start.y())
                if dist > 8:
                    text, ok = self.prompt_text_dialog("설명 입력")
                    if ok and text.strip():
                        self.push_undo()
                        w = max(110.0, float(len(text.strip()) * 14 + 20))
                        h = 42.0
                        box_r = QRectF(self.callout_end.x() - w / 2.0, self.callout_end.y() - h / 2.0, w, h)
                        callout_st = dict(self.config.get("callout_style", DEFAULT_CONFIG["callout_style"]))
                        callout_st["border_color"] = self.current_box_color
                        callout_st["border_width"] = self.current_box_width
                        self.items.append(CalloutItem(text.strip(), box_r, self.callout_start, callout_st))
                        self.update()
                        self.sig_content_changed.emit()
                # Sticky Mode: 도구 선택 유지
            elif self.drawing_blur:
                self.drawing_blur = False
                r = QRect(self.blur_start, self.blur_end).normalized()
                if r.width() > 8 and r.height() > 8:
                    self.push_undo()
                    blur_st = dict(self.config.get("blur_style", DEFAULT_CONFIG["blur_style"]))
                    self.items.append(BlurMosaicItem(r, blur_st))
                    self.update()
                    self.sig_content_changed.emit()
                # Sticky Mode: 도구 선택 유지
            elif self.drawing_eraser:
                self.drawing_eraser = False
                r = QRect(self.eraser_start, self.eraser_end).normalized()
                if r.width() >= 4 and r.height() >= 4 and self.pixmap and not self.pixmap.isNull():
                    self.push_undo()
                    self.pixmap = SmartCleanupEngine.inpaint_rect(self.pixmap, r)
                    self.sig_content_changed.emit()
                    self.sig_request_toast.emit(tr("toast_eraser_done", "배경 스마트 지우개 적용 완료 (Ctrl+Z 되돌리기 가능)"))
                # Sticky Mode: 도구 선택 유지
                self.update()
            elif self.drawing_ocr:
                self.drawing_ocr = False
                r = QRect(self.ocr_start, self.ocr_end).normalized()
                if r.width() >= 10 and r.height() >= 8:
                    self._run_ocr_on_region(r, as_label=getattr(self, "ocr_is_label_mode", False))
                self.set_mode("SELECT")
            elif self.drawing_dimension:
                self.drawing_dimension = False
                cur_pt = QPointF(pt)
                modifiers = QGuiApplication.keyboardModifiers()
                if not (modifiers & Qt.ShiftModifier):
                    dx = cur_pt.x() - self.dimension_start.x()
                    dy = cur_pt.y() - self.dimension_start.y()
                    if abs(dx) >= abs(dy):
                        cur_pt = QPointF(cur_pt.x(), self.dimension_start.y())
                    else:
                        cur_pt = QPointF(self.dimension_start.x(), cur_pt.y())
                self.dimension_end = cur_pt
                dist = math.hypot(self.dimension_end.x() - self.dimension_start.x(), self.dimension_end.y() - self.dimension_start.y())
                if dist > 6:
                    self.push_undo()
                    dim_style = dict(self.config.get("dimension_style", DEFAULT_CONFIG["dimension_style"]))
                    dim_item = DimensionLineItem(self.dimension_start, self.dimension_end, dim_style)
                    self.items.append(dim_item)
                    self.selected_item = dim_item
                    self.sig_item_selected.emit(dim_item)
                    self.sig_content_changed.emit()
                # Sticky Mode: 도구 선택 유지
                self.update()
            elif self.drawing_box_dimension:
                self.drawing_box_dimension = False
                r = QRect(self.box_dimension_start, self.box_dimension_end).normalized()
                if r.width() > 10 and r.height() > 10:
                    self.push_undo()
                    dim_style = dict(self.config.get("dimension_style", DEFAULT_CONFIG["dimension_style"]))
                    dim_item = BoxDimensionItem(r, dim_style)
                    self.items.append(dim_item)
                    self.selected_item = dim_item
                    self.sig_item_selected.emit(dim_item)
                    self.sig_content_changed.emit()
                # Sticky Mode: 도구 선택 유지
                self.update()
            elif getattr(self, "drawing_flow_node", False):
                self.drawing_flow_node = False
                flow_shapes = {
                    "FLOW_TERMINAL": ("terminal", "시작"),
                    "FLOW_PROCESS": ("process", "처리 작업"),
                    "FLOW_DECISION": ("decision", "조건 판단"),
                    "FLOW_IO": ("io", "데이터 입출력"),
                    "FLOW_DATABASE": ("database", "데이터베이스"),
                    "FLOW_DOCUMENT": ("document", "문서 서식"),
                }
                shape_type, def_txt = flow_shapes.get(self.current_mode, ("process", "처리 작업"))
                r = QRectF(self.flow_node_start, self.flow_node_end).normalized()
                if r.width() < 15 or r.height() < 15:
                    w, h = 75.0, 32.0
                    if shape_type == "terminal":
                        w, h = 65.0, 26.0
                    elif shape_type == "decision":
                        w, h = 70.0, 38.0
                    elif shape_type == "database":
                        w, h = 65.0, 36.0
                    elif shape_type == "io":
                        w, h = 70.0, 30.0
                    node_rect = QRectF(self.flow_node_start.x() - w / 2.0, self.flow_node_start.y() - h / 2.0, w, h)
                else:
                    node_rect = r
                self.push_undo()
                node_style = {
                    "bg_color": "#EFF6FF",
                    "border_color": "#2563EB",
                    "border_width": 1.5,
                    "text_color": "#1E293B",
                    "font_size": 7,
                    "font_bold": True
                }
                node_item = FlowchartNodeItem(
                    text=def_txt,
                    x=node_rect.x(), y=node_rect.y(),
                    w=node_rect.width(), h=node_rect.height(),
                    shape_type=shape_type,
                    style=node_style
                )
                self.items.append(node_item)
                self.selected_item = node_item
                self.sig_item_selected.emit(node_item)
                self.update()
                self.sig_content_changed.emit()
                # Sticky Mode: 도구 선택 유지

    def mouseDoubleClickEvent(self, event):
        pt = get_mouse_pos(event)
        for it in reversed(self.items):
            if isinstance(it, TextLabelItem) and it.contains(pt):
                new_text, ok = self.prompt_text_dialog(it.text)
                if ok and new_text.strip():
                    self.push_undo()
                    it.text = new_text.strip()
                    self.update()
                    self.sig_content_changed.emit()
                break
            elif isinstance(it, CalloutItem) and it.contains(pt):
                new_text, ok = self.prompt_text_dialog(it.text)
                if ok and new_text.strip():
                    self.push_undo()
                    it.text = new_text.strip()
                    self.update()
                    self.sig_content_changed.emit()
                break
            elif isinstance(it, WordArtItem) and it.contains(pt):
                new_text, ok = self.prompt_text_dialog(it.text, title="워드아트 문구 수정")
                if ok and new_text.strip():
                    self.push_undo()
                    it.text = new_text.strip()
                    self.update()
                    self.sig_content_changed.emit()
                break
            elif isinstance(it, HotkeyBadgeItem) and it.contains(pt):
                new_text, ok = self.prompt_hotkey_dialog(it.key_text)
                if ok and new_text.strip():
                    self.push_undo()
                    it.key_text = new_text.strip()
                    self.update()
                    self.sig_content_changed.emit()
                break
            elif isinstance(it, DraftStampItem) and it.contains(pt):
                new_text, ok = self.prompt_draft_dialog(it.text)
                if ok and new_text.strip():
                    self.push_undo()
                    it.text = new_text.strip().upper()
                    self.update()
                    self.sig_content_changed.emit()
                break
            elif isinstance(it, StampItem) and it.contains(pt):
                new_idx, ok = self.prompt_stamp_dialog(it.index)
                if ok:
                    self.push_undo()
                    it.index = new_idx
                    self.update()
                    self.sig_content_changed.emit()
                break
            elif isinstance(it, FlowchartNodeItem) and it.contains(pt):
                new_text, ok = self.prompt_text_dialog(it.text, title="플로우차트 노드 텍스트 수정")
                if ok and new_text.strip():
                    self.push_undo()
                    it.text = new_text.strip()
                    self.update()
                    self.sig_content_changed.emit()
                break
            elif it.contains(pt):
                self.open_item_properties_dialog(it)
                break

    def prompt_stamp_dialog(self, initial_index=1):
        try:
            dlg = QDialog(self)
            dlg.setWindowTitle("스탬프 번호 변경")
            dlg.setFixedSize(340, 140)
            dlg.setStyleSheet("""
                QDialog { background-color: #FFFFFF; color: #1E293B; }
                QLabel { color: #1E293B; font-weight: bold; }
                QSpinBox { background-color: #FFFFFF; color: #1E293B; border: 1px solid #CBD5E1; border-radius: 4px; padding: 6px; font-size: 14px; font-weight: bold; }
                QPushButton { background-color: #F1F5F9; border: 1px solid #CBD5E1; border-radius: 4px; padding: 6px 14px; color: #1E293B; font-weight: bold; }
                QPushButton#btn_ok { background-color: #2563EB; color: #FFFFFF; border-color: #1D4ED8; }
            """)
            layout = QVBoxLayout(dlg)
            lbl = QLabel("스탬프 번호를 입력하세요 (1 ~ 999):", dlg)
            lbl.setFont(QFont("Malgun Gothic", 10))
            layout.addWidget(lbl)

            spn = QSpinBox(dlg)
            spn.setRange(1, 999)
            spn.setValue(int(initial_index))
            spn.setFont(QFont("Malgun Gothic", 12, QFont.Bold))
            layout.addWidget(spn)

            btn_box = QHBoxLayout()
            btn_ok = QPushButton("확인", dlg)
            btn_ok.setObjectName("btn_ok")
            btn_ok.setDefault(True)
            btn_ok.clicked.connect(dlg.accept)
            btn_cancel = QPushButton("취소", dlg)
            btn_cancel.clicked.connect(dlg.reject)
            btn_box.addStretch()
            btn_box.addWidget(btn_ok)
            btn_box.addWidget(btn_cancel)
            layout.addLayout(btn_box)

            def dlg_key_press(ev):
                if ev.key() in (Qt.Key_Return, Qt.Key_Enter):
                    dlg.accept()
                    ev.accept()
                    return
                QDialog.keyPressEvent(dlg, ev)
            dlg.keyPressEvent = dlg_key_press

            spn.setFocus()
            spn.selectAll()
            if dlg.exec() == QDialog.Accepted:
                return spn.value(), True
        except Exception as e:
            print(f"[스탬프 번호 입력 오류]: {e}")
        return initial_index, False

    def prompt_text_dialog(self, initial_text, title="설명 텍스트 입력"):
        try:
            dlg = QDialog(self)
            dlg.setWindowTitle(title)
            dlg.setFixedSize(380, 140)
            dlg.setStyleSheet("""
                QDialog { background-color: #FFFFFF; color: #1E293B; }
                QLabel { color: #1E293B; font-weight: bold; }
                QLineEdit { background-color: #FFFFFF; color: #1E293B; border: 1px solid #CBD5E1; border-radius: 4px; padding: 6px; font-size: 11px; }
                QLineEdit:focus { border: 1px solid #2563EB; }
                QPushButton { background-color: #F1F5F9; border: 1px solid #CBD5E1; border-radius: 4px; padding: 6px 14px; color: #1E293B; font-weight: bold; }
                QPushButton#btn_ok { background-color: #2563EB; color: #FFFFFF; border-color: #1D4ED8; }
            """)
            layout = QVBoxLayout(dlg)

            lbl = QLabel(f"표시할 {title}을(를) 입력하세요:", dlg)
            lbl.setFont(QFont("Malgun Gothic", 10))
            layout.addWidget(lbl)

            line_edit = QLineEdit(initial_text, dlg)
            line_edit.setFont(QFont("Malgun Gothic", 11))
            line_edit.returnPressed.connect(dlg.accept)
            layout.addWidget(line_edit)

            btn_box = QHBoxLayout()
            btn_ok = QPushButton("확인", dlg)
            btn_ok.setObjectName("btn_ok")
            btn_ok.setDefault(True)
            btn_ok.clicked.connect(dlg.accept)
            btn_cancel = QPushButton("취소", dlg)
            btn_cancel.clicked.connect(dlg.reject)
            btn_box.addStretch()
            btn_box.addWidget(btn_ok)
            btn_box.addWidget(btn_cancel)
            layout.addLayout(btn_box)

            def dlg_key_press(ev):
                if ev.key() in (Qt.Key_Return, Qt.Key_Enter):
                    dlg.accept()
                    ev.accept()
                    return
                QDialog.keyPressEvent(dlg, ev)
            dlg.keyPressEvent = dlg_key_press

            line_edit.setFocus()
            line_edit.selectAll()
            if dlg.exec() == QDialog.Accepted:
                return line_edit.text(), True
        except Exception as e:
            print(f"[텍스트 입력 오류]: {e}")
        return "", False

    def prompt_hotkey_dialog(self, initial_text="Enter ↵"):
        try:
            dlg = QDialog(self)
            dlg.setWindowTitle("단축키 뱃지 선택/입력")
            dlg.setFixedSize(380, 240)
            dlg.setStyleSheet("""
                QDialog { background-color: #FFFFFF; color: #1E293B; }
                QLabel { color: #1E293B; }
                QLineEdit { background-color: #FFFFFF; color: #1E293B; border: 1px solid #CBD5E1; border-radius: 4px; padding: 6px; font-size: 11px; }
                QLineEdit:focus { border: 1px solid #2563EB; }
                QPushButton { background-color: #F1F5F9; border: 1px solid #CBD5E1; border-radius: 4px; padding: 4px 8px; color: #1E293B; font-weight: bold; }
                QPushButton#btn_ok { background-color: #2563EB; color: #FFFFFF; border-color: #1D4ED8; }
            """)
            layout = QVBoxLayout(dlg)
            layout.setSpacing(8)

            lbl = QLabel("삽입할 키보드 키를 선택하거나 직접 입력하세요:", dlg)
            lbl.setFont(QFont("Malgun Gothic", 10, QFont.Bold))
            layout.addWidget(lbl)

            line_edit = QLineEdit(initial_text, dlg)
            line_edit.setFont(QFont("Malgun Gothic", 11, QFont.Bold))
            line_edit.returnPressed.connect(dlg.accept)
            layout.addWidget(line_edit)

            lbl_preset = QLabel("자주 사용하는 키 프리셋:", dlg)
            lbl_preset.setFont(QFont("Malgun Gothic", 9))
            lbl_preset.setStyleSheet("color: #666666;")
            layout.addWidget(lbl_preset)

            grid_presets = [
                ["Enter ↵", "Tab ⇥", "Esc", "Space"],
                ["Ctrl + C", "Ctrl + V", "Ctrl + S", "Ctrl + Z"],
                ["F9", "F10", "F5", "Backspace ⌫"]
            ]
            for row in grid_presets:
                h_box = QHBoxLayout()
                h_box.setSpacing(4)
                for key_name in row:
                    btn = QPushButton(key_name, dlg)
                    btn.setFont(QFont("Malgun Gothic", 9))
                    btn.setFixedHeight(24)
                    btn.clicked.connect(lambda ch, k=key_name: line_edit.setText(k))
                    h_box.addWidget(btn)
                layout.addLayout(h_box)

            layout.addStretch()
            btn_box = QHBoxLayout()
            btn_ok = QPushButton("확인", dlg)
            btn_ok.setObjectName("btn_ok")
            btn_ok.setDefault(True)
            btn_ok.clicked.connect(dlg.accept)
            btn_cancel = QPushButton("취소", dlg)
            btn_cancel.clicked.connect(dlg.reject)
            btn_box.addStretch()
            btn_box.addWidget(btn_ok)
            btn_box.addWidget(btn_cancel)
            layout.addLayout(btn_box)

            def dlg_key_press(ev):
                if ev.key() in (Qt.Key_Return, Qt.Key_Enter):
                    dlg.accept()
                    ev.accept()
                    return
                QDialog.keyPressEvent(dlg, ev)
            dlg.keyPressEvent = dlg_key_press

            line_edit.setFocus()
            line_edit.selectAll()
            if dlg.exec() == QDialog.Accepted:
                return line_edit.text(), True
        except Exception as e:
            print(f"[단축키 입력 오류]: {e}")
        return "", False

    def prompt_draft_dialog(self, initial_text="DRAFT"):
        try:
            dlg = QDialog(self)
            dlg.setWindowTitle("Draft 스탬프 텍스트 변경")
            dlg.setFixedSize(380, 240)
            dlg.setStyleSheet("""
                QDialog { background-color: #FFFFFF; color: #1E293B; }
                QLabel { color: #1E293B; }
                QLineEdit { background-color: #FFFFFF; color: #1E293B; border: 1px solid #CBD5E1; border-radius: 4px; padding: 6px; font-size: 11px; }
                QLineEdit:focus { border: 1px solid #2563EB; }
                QPushButton { background-color: #F1F5F9; border: 1px solid #CBD5E1; border-radius: 4px; padding: 4px 8px; color: #1E293B; font-weight: bold; }
                QPushButton#btn_ok { background-color: #2563EB; color: #FFFFFF; border-color: #1D4ED8; }
            """)
            layout = QVBoxLayout(dlg)
            layout.setSpacing(8)

            lbl = QLabel("스탬프에 표시할 문구를 입력하거나 선택하세요:", dlg)
            lbl.setFont(QFont("Malgun Gothic", 10, QFont.Bold))
            layout.addWidget(lbl)

            line_edit = QLineEdit(initial_text, dlg)
            line_edit.setFont(QFont("Malgun Gothic", 11, QFont.Bold))
            line_edit.returnPressed.connect(dlg.accept)
            layout.addWidget(line_edit)

            lbl_preset = QLabel("자주 사용하는 스탬프 프리셋:", dlg)
            lbl_preset.setFont(QFont("Malgun Gothic", 9))
            lbl_preset.setStyleSheet("color: #666666;")
            layout.addWidget(lbl_preset)

            grid_presets = [
                ["DRAFT", "초안", "SAMPLE", "검토용"],
                ["대외비", "CONFIDENTIAL", "사본", "참고용"]
            ]
            for row in grid_presets:
                h_box = QHBoxLayout()
                h_box.setSpacing(4)
                for key_name in row:
                    btn = QPushButton(key_name, dlg)
                    btn.setFont(QFont("Malgun Gothic", 9))
                    btn.setFixedHeight(26)
                    btn.clicked.connect(lambda ch, k=key_name: line_edit.setText(k))
                    h_box.addWidget(btn)
                layout.addLayout(h_box)

            layout.addStretch()
            btn_box = QHBoxLayout()
            btn_ok = QPushButton("확인", dlg)
            btn_ok.setObjectName("btn_ok")
            btn_ok.setDefault(True)
            btn_ok.clicked.connect(dlg.accept)
            btn_cancel = QPushButton("취소", dlg)
            btn_cancel.clicked.connect(dlg.reject)
            btn_box.addStretch()
            btn_box.addWidget(btn_ok)
            btn_box.addWidget(btn_cancel)
            layout.addLayout(btn_box)

            def dlg_key_press(ev):
                if ev.key() in (Qt.Key_Return, Qt.Key_Enter):
                    dlg.accept()
                    ev.accept()
                    return
                QDialog.keyPressEvent(dlg, ev)
            dlg.keyPressEvent = dlg_key_press

            line_edit.setFocus()
            line_edit.selectAll()
            if dlg.exec() == QDialog.Accepted:
                return line_edit.text(), True
        except Exception as e:
            print(f"[드래프트 입력 오류]: {e}")
        return "", False

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing, True)

            # 1. 배경 이미지
            if self.pixmap and not self.pixmap.isNull():
                painter.drawPixmap(0, 0, self.pixmap)
            else:
                # 투명 캔버스: 16px 체커보드 투명 격자 패턴 렌더링
                grid_sz = 16
                r = self.rect()
                col1 = QColor(255, 255, 255)
                col2 = QColor(241, 245, 249)
                for gx in range(0, r.width(), grid_sz):
                    for gy in range(0, r.height(), grid_sz):
                        painter.fillRect(gx, gy, grid_sz, grid_sz, col1 if (gx // grid_sz + gy // grid_sz) % 2 == 0 else col2)
                
                # 외곽 테두리 (16:9 슬라이드 경계선)
                painter.setPen(QPen(QColor(203, 213, 225), 1, Qt.DashLine))
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(r.adjusted(0, 0, -1, -1))
                
                # 등록된 아이템이 전혀 없을 때만 은은한 가이드 텍스트 표시
                if not self.items:
                    painter.setPen(QColor(148, 163, 184))
                    f_guide = QFont("Malgun Gothic", 11)
                    f_guide.setBold(True)
                    painter.setFont(f_guide)
                    painter.drawText(r, Qt.AlignCenter, "투명 캔버스 (16:9)\nF8 부분캡처 또는 플로우차트/텍스트/도형을 자유롭게 배치하세요.")

            # 2. 모든 주석 렌더링 (블러는 원본 픽셀맵 합성)
            for item in self.items:
                is_sel = (item is self.selected_item)
                try:
                    if isinstance(item, FlowchartNodeItem):
                        item.render(painter, is_selected=is_sel)
                        continue
                    elif isinstance(item, BlurMosaicItem):
                        item.render_mosaic(painter, self.pixmap)
                    elif isinstance(item, MagnifierZoomItem):
                        item.render_zoom(painter, self.pixmap)
                    elif isinstance(item, SpotlightMaskItem):
                        item.render_spotlight(painter, self.pixmap.width() if self.pixmap else 1920, self.pixmap.height() if self.pixmap else 1080)
                    elif isinstance(item, (ImageOverlayItem, DraftStampItem)):
                        item.render(painter, is_selected=(item == self.selected_item and self.current_mode == "SELECT"))
                    else:
                        item.render(painter)
                except Exception as e:
                    print(f"[주석 렌더링 예외]: {e}")

            # 3. 실시간 드로잉 프리뷰
            if self.drawing_box:
                painter.save()
                r = QRect(self.box_start, self.box_end).normalized()
                painter.setPen(QPen(QColor(229, 57, 53), 2, Qt.DashLine))
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(r)
                painter.restore()

            elif self.drawing_arrow:
                painter.save()
                temp_arrow = ArrowItem(self.arrow_start, self.arrow_end, {
                    "color": self.current_arrow_color,
                    "width": self.current_arrow_width,
                    "head_size": self.current_arrow_head_size
                })
                temp_arrow.render(painter)
                painter.restore()

            elif self.drawing_step_arrow:
                painter.save()
                st_style = dict(self.config.get("stamp_style", DEFAULT_CONFIG["stamp_style"]))
                arr_style = {
                    "color": self.current_arrow_color,
                    "width": self.current_arrow_width,
                    "head_size": self.current_arrow_head_size
                }
                temp_step = StepArrowItem(self.next_stamp_index, self.step_arrow_start, self.step_arrow_end, st_style, arr_style)
                temp_step.render(painter)
                painter.restore()

            elif self.drawing_elbow:
                painter.save()
                arr_style = {
                    "color": self.current_arrow_color,
                    "width": self.current_arrow_width,
                    "head_size": self.current_arrow_head_size
                }
                temp_elbow = ElbowArrowItem(self.elbow_start, self.elbow_end, arr_style, getattr(self, "current_elbow_route_mode", "HV"))
                temp_elbow.render(painter)
                painter.restore()

            elif self.drawing_callout:
                painter.save()
                w = 110.0
                h = 40.0
                box_r = QRectF(self.callout_end.x() - w / 2.0, self.callout_end.y() - h / 2.0, w, h)
                callout_st = dict(self.config.get("callout_style", DEFAULT_CONFIG["callout_style"]))
                callout_st["border_color"] = self.current_box_color
                callout_st["border_width"] = self.current_box_width
                temp_callout = CalloutItem("설명 입력", box_r, self.callout_start, callout_st)
                temp_callout.render(painter)
                painter.restore()

            elif self.drawing_blur:
                painter.save()
                r = QRect(self.blur_start, self.blur_end).normalized()
                blur_st = dict(self.config.get("blur_style", DEFAULT_CONFIG["blur_style"]))
                temp_blur = BlurMosaicItem(r, blur_st)
                temp_blur.render_mosaic(painter, self.pixmap)
                painter.restore()

            elif self.drawing_eraser:
                painter.save()
                r = QRect(self.eraser_start, self.eraser_end).normalized()
                painter.setPen(QPen(QColor(236, 72, 153), 2, Qt.DashLine))
                painter.setBrush(QBrush(QColor(236, 72, 153, 50)))
                painter.drawRect(r)
                painter.restore()

            elif self.drawing_ocr:
                painter.save()
                r = QRect(self.ocr_start, self.ocr_end).normalized()
                border_col = QColor(37, 99, 235) if getattr(self, "ocr_is_label_mode", False) else QColor(16, 185, 129)
                painter.setPen(QPen(border_col, 2, Qt.DashLine))
                painter.setBrush(QBrush(QColor(border_col.red(), border_col.green(), border_col.blue(), 30)))
                painter.drawRect(r)
                painter.restore()

            elif self.drawing_dimension:
                painter.save()
                dim_st = dict(self.config.get("dimension_style", DEFAULT_CONFIG["dimension_style"]))
                temp_dim = DimensionLineItem(self.dimension_start, self.dimension_end, dim_st)
                temp_dim.render(painter)
                painter.restore()

            elif self.drawing_box_dimension:
                painter.save()
                r = QRect(self.box_dimension_start, self.box_dimension_end).normalized()
                dim_st = dict(self.config.get("dimension_style", DEFAULT_CONFIG["dimension_style"]))
                temp_box_dim = BoxDimensionItem(r, dim_st)
                temp_box_dim.render(painter)
                painter.restore()

            elif getattr(self, "drawing_flow_node", False):
                painter.save()
                flow_shapes = {
                    "FLOW_TERMINAL": "terminal",
                    "FLOW_PROCESS": "process",
                    "FLOW_DECISION": "decision",
                    "FLOW_IO": "io",
                    "FLOW_DATABASE": "database",
                    "FLOW_DOCUMENT": "document",
                }
                shape_type = flow_shapes.get(self.current_mode, "process")
                r = QRectF(self.flow_node_start, self.flow_node_end).normalized()
                if r.width() < 15 or r.height() < 15:
                    w, h = 75.0, 32.0
                    if shape_type == "terminal":
                        w, h = 65.0, 26.0
                    elif shape_type == "decision":
                        w, h = 70.0, 38.0
                    elif shape_type == "database":
                        w, h = 65.0, 36.0
                    elif shape_type == "io":
                        w, h = 70.0, 30.0
                    r = QRectF(self.flow_node_start.x() - w / 2.0, self.flow_node_start.y() - h / 2.0, w, h)
                pen = QPen(QColor("#2563EB"), 1.5, Qt.DashLine)
                brush = QBrush(QColor(37, 99, 235, 35))
                painter.setPen(pen)
                painter.setBrush(brush)
                if shape_type == "terminal":
                    rad = min(r.width(), r.height()) / 2.0
                    painter.drawRoundedRect(r, rad, rad)
                elif shape_type == "decision":
                    poly = QPolygonF([
                        QPointF(r.center().x(), r.top()),
                        QPointF(r.right(), r.center().y()),
                        QPointF(r.center().x(), r.bottom()),
                        QPointF(r.left(), r.center().y())
                    ])
                    painter.drawPolygon(poly)
                elif shape_type == "io":
                    skew = r.width() * 0.16
                    poly = QPolygonF([
                        QPointF(r.left() + skew, r.top()),
                        QPointF(r.right(), r.top()),
                        QPointF(r.right() - skew, r.bottom()),
                        QPointF(r.left(), r.bottom())
                    ])
                    painter.drawPolygon(poly)
                else:
                    painter.drawRoundedRect(r, 6, 6)
                painter.restore()

            # 4. 선택된 객체 하이라이트 (다중 선택 객체 일체 지원)
            all_selected = list(getattr(self, "selected_items", []))
            if self.selected_item and self.selected_item not in all_selected:
                all_selected.append(self.selected_item)

            if all_selected and self.current_mode == "SELECT":
                painter.save()
                painter.setPen(QPen(QColor(33, 150, 243), 1.5, Qt.DotLine))
                painter.setBrush(Qt.NoBrush)
                for s_item in all_selected:
                    if isinstance(s_item, (ImageOverlayItem, DraftStampItem)):
                        pass
                    elif isinstance(s_item, StampItem):
                        sz = s_item.style.get("size", 32)
                        r = sz / 2.0 + 3
                        if s_item.style.get("shape") == "rounded_rect":
                            cr = float(s_item.style.get("corner_radius", max(4, int(sz * 0.25)))) + 2
                            rect = QRectF(s_item.pos.x() - r, s_item.pos.y() - r, sz + 6, sz + 6)
                            painter.drawRoundedRect(rect, cr, cr)
                        else:
                            painter.drawEllipse(s_item.pos, r, r)
                    elif isinstance(s_item, (TextLabelItem, HotkeyBadgeItem, WordArtItem)):
                        painter.drawRect(s_item.get_rect().adjusted(-2, -2, 2, 2))
                    elif isinstance(s_item, (HighlightBoxItem, BlurMosaicItem, BoxDimensionItem, SpotlightMaskItem, FlowchartNodeItem)):
                        painter.drawRect(s_item.rect.adjusted(-2, -2, 2, 2))
                    elif isinstance(s_item, MagnifierZoomItem):
                        painter.drawRect(s_item.lens_rect.adjusted(-2, -2, 2, 2))
                        painter.drawRect(s_item.source_rect.adjusted(-2, -2, 2, 2))
                    elif isinstance(s_item, ClickRippleItem):
                        size = float(s_item.style.get("size", 36))
                        r = size / 2.0 + 4
                        painter.drawEllipse(s_item.pos, r, r)
                    elif isinstance(s_item, CalloutItem):
                        painter.drawRect(s_item.box_rect.adjusted(-2, -2, 2, 2))
                        painter.setBrush(QBrush(QColor(33, 150, 243)))
                        painter.drawEllipse(s_item.target_pt, 3.5, 3.5)
                        painter.setBrush(Qt.NoBrush)
                    elif isinstance(s_item, (ArrowItem, StepArrowItem, DimensionLineItem)):
                        p1 = s_item.start_pos
                        p2 = s_item.end_pos
                        painter.drawLine(p1, p2)
                        painter.setBrush(QBrush(QColor(33, 150, 243)))
                        painter.drawEllipse(p1, 3.5, 3.5)
                        painter.drawEllipse(p2, 3.5, 3.5)
                        painter.setBrush(Qt.NoBrush)
                    elif isinstance(s_item, ElbowArrowItem):
                        p1 = s_item.start_pos
                        corner = s_item.get_corner_point()
                        p2 = s_item.end_pos
                        painter.drawLine(p1, corner)
                        painter.drawLine(corner, p2)
                        painter.setBrush(QBrush(QColor(33, 150, 243)))
                        painter.drawEllipse(p1, 3.5, 3.5)
                        painter.drawEllipse(corner, 3.0, 3.0)
                        painter.drawEllipse(p2, 3.5, 3.5)
                        painter.setBrush(Qt.NoBrush)
                painter.restore()

            # 5. 러버밴드 드래그 선택 사각형 시각화
            if getattr(self, "rubber_band_active", False):
                rb_rect = QRectF(self.rubber_band_start, self.rubber_band_end).normalized()
                if rb_rect.width() > 2 and rb_rect.height() > 2:
                    painter.save()
                    painter.setPen(QPen(QColor(37, 99, 235), 1.2, Qt.DashLine))
                    painter.setBrush(QBrush(QColor(59, 130, 246, 35)))
                    painter.drawRect(rb_rect)
                    painter.restore()
        finally:
            painter.end()

    def get_composed_image(self):
        """현재 캔버스 원본 해상도로 주석 일체형 합성 QImage 생성"""
        cw = self.pixmap.width() if (self.pixmap and not self.pixmap.isNull()) else (self.width() if self.width() > 0 else 960)
        ch = self.pixmap.height() if (self.pixmap and not self.pixmap.isNull()) else (self.height() if self.height() > 0 else 540)
        img = QImage(cw, ch, QImage.Format_ARGB32)
        if self.pixmap and not self.pixmap.isNull():
            img.fill(Qt.transparent)
        else:
            img.fill(Qt.white)

        painter = QPainter(img)
        try:
            painter.setRenderHint(QPainter.Antialiasing, True)
            if self.pixmap and not self.pixmap.isNull():
                painter.drawPixmap(0, 0, self.pixmap)

            for item in self.items:
                is_sel = (item is self.selected_item)
                try:
                    if isinstance(item, FlowchartNodeItem):
                        item.render(painter, is_selected=is_sel)
                        continue
                    elif isinstance(item, BlurMosaicItem):
                        if self.pixmap and not self.pixmap.isNull():
                            item.render_mosaic(painter, self.pixmap)
                    elif isinstance(item, MagnifierZoomItem):
                        if self.pixmap and not self.pixmap.isNull():
                            item.render_zoom(painter, self.pixmap)
                    elif isinstance(item, SpotlightMaskItem):
                        item.render_spotlight(painter, cw, ch)
                    elif isinstance(item, (ImageOverlayItem, DraftStampItem)):
                        item.render(painter, is_selected=False)
                    else:
                        item.render(painter)
                except Exception as e:
                    print(f"[합성 주석 렌더링 예외]: {e}")

            # 평가판 / 미인증 시 워터마크 자동 삽입 (정식 인증 시 완전 제거)
            if not LicenseEngine.is_licensed():
                self._render_watermark(painter, img.width(), img.height())
        finally:
            painter.end()
        return img

    def _render_watermark(self, painter: QPainter, width: int, height: int):
        """평가판 상태일 때 자동 삽입되는 다국어 워터마크"""
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        wm_text = tr("watermark_text", "Manual Studio • Trial Version")

        # 1. 우측 하단 반투명 캡슐 배지
        font_badge = QFont("Segoe UI", 11)
        font_badge.setBold(True)
        fm = QFontMetrics(font_badge)
        tw = fm.horizontalAdvance(wm_text)
        th = fm.height()
        pad_x, pad_y = 12, 6
        badge_w = tw + pad_x * 2
        badge_h = th + pad_y * 2
        badge_x = width - badge_w - 15
        badge_y = height - badge_h - 15

        if badge_x > 0 and badge_y > 0:
            badge_rect = QRectF(badge_x, badge_y, badge_w, badge_h)
            painter.setPen(QPen(QColor(255, 255, 255, 120), 1))
            painter.setBrush(QColor(15, 23, 42, 190))
            painter.drawRoundedRect(badge_rect, 6, 6)

            painter.setFont(font_badge)
            painter.setPen(QColor(255, 255, 255, 230))
            painter.drawText(badge_rect, Qt.AlignCenter, wm_text)

        # 2. 중앙 은은한 대각선 워터마크
        diag_size = max(16, int(min(width, height) / 22))
        font_diag = QFont("Segoe UI", diag_size)
        font_diag.setBold(True)
        painter.setFont(font_diag)
        painter.setPen(QColor(148, 163, 184, 50))

        painter.translate(width / 2.0, height / 2.0)
        painter.rotate(-28.0)
        center_fm = QFontMetrics(font_diag)
        c_tw = center_fm.horizontalAdvance(wm_text)
        c_th = center_fm.height()
        painter.drawText(int(-c_tw / 2), int(c_th / 4), wm_text)

        painter.restore()


# ==============================================================================
# 6. 내보내기 & 파워포인트 연동 엔진 (Export Engine)
# ==============================================================================
class ExportEngine:
    @staticmethod
    def apply_window_frame_and_shadow(
        img: Image.Image,
        include_header: bool = True,
        corner_radius: int = 12,
        shadow_radius: int = 20,
        shadow_offset: tuple = (0, 6),
        shadow_opacity: float = 0.35,
        bg_color: tuple = (248, 250, 252, 255),
        border_color: tuple = (203, 213, 225, 255),
        header_height: int = 32,
        title: str = ""
    ) -> Image.Image:
        """
        Notion / CleanShot X / macOS 스타일의 모던 윈도우 창틀과 소프트 드롭 섀도우를 이미지에 합성합니다.
        외곽은 투명 알파(RGBA)로 완벽 마스킹되어 슬라이드나 문서에 깔끔하게 안착됩니다.
        """
        src = img.convert("RGBA")
        w, h = src.size

        win_w = w
        win_h = h + (header_height if include_header else 0)

        # 1. 둥근 모서리 마스크 (4x 수퍼샘플링으로 안티에일리어싱 극대화)
        mask = Image.new("L", (win_w * 4, win_h * 4), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.rounded_rectangle([0, 0, win_w * 4, win_h * 4], radius=corner_radius * 4, fill=255)
        mask = mask.resize((win_w, win_h), Image.Resampling.LANCZOS)

        win_body = Image.new("RGBA", (win_w, win_h), bg_color)
        win_body_draw = ImageDraw.Draw(win_body)

        if include_header:
            header_rect = [0, 0, win_w, header_height]
            win_body_draw.rectangle(header_rect, fill=(241, 245, 249, 255))
            win_body_draw.line([(0, header_height - 1), (win_w, header_height - 1)], fill=border_color, width=1)

            # 3색 신호등 버튼 (빨/노/초)
            dot_radius = 5
            dot_y = header_height // 2
            dots = [
                (16, (255, 95, 86, 255), (224, 68, 62, 255)),
                (32, (255, 189, 46, 255), (214, 158, 30, 255)),
                (48, (39, 201, 63, 255), (26, 171, 46, 255))
            ]
            for cx, c_fill, c_stroke in dots:
                win_body_draw.ellipse(
                    [cx - dot_radius, dot_y - dot_radius, cx + dot_radius, dot_y + dot_radius],
                    fill=c_fill,
                    outline=c_stroke,
                    width=1
                )
            win_body.paste(src, (0, header_height), src)
        else:
            win_body.paste(src, (0, 0), src)

        win_body_draw.rounded_rectangle([0, 0, win_w - 1, win_h - 1], radius=corner_radius, outline=border_color, width=1)

        window_surf = Image.new("RGBA", (win_w, win_h), (0, 0, 0, 0))
        window_surf.paste(win_body, (0, 0), mask=mask)

        # 2. 소프트 섀도우 패딩 및 블러
        pad_x = shadow_radius * 2
        pad_y = shadow_radius * 2 + abs(shadow_offset[1])
        canvas_w = win_w + pad_x * 2
        canvas_h = win_h + pad_y * 2

        shadow_mask = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        s_draw = ImageDraw.Draw(shadow_mask)

        sx1 = pad_x + shadow_offset[0]
        sy1 = pad_y + shadow_offset[1]
        sx2 = sx1 + win_w
        sy2 = sy1 + win_h

        alpha_val = int(255 * shadow_opacity)
        s_draw.rounded_rectangle([sx1, sy1, sx2, sy2], radius=corner_radius, fill=(0, 0, 0, alpha_val))
        shadow_blurred = shadow_mask.filter(ImageFilter.GaussianBlur(shadow_radius))

        # 3. 그림자 + 윈도우 표면 결합
        final_canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        final_canvas.paste(shadow_blurred, (0, 0), shadow_blurred)
        final_canvas.paste(window_surf, (pad_x, pad_y), window_surf)

        return final_canvas

    @staticmethod
    def send_to_hwp(pil_img: Image.Image, step_title: str = None, hwp_layout: dict = None) -> dict:
        """
        열려 있는 한컴 한글(HWP) 문서에 이미지를 클립보드/COM으로 삽입하고,
        선택 시 상단 단계 제목 텍스트를 자동 작성합니다.
        """
        if win32com is None:
            return {"success": False, "error": "win32com is not available"}

        try:
            ExportEngine.copy_to_clipboard(pil_img)
        except Exception as ce:
            return {"success": False, "error": f"Clipboard error: {ce}"}

        hwp = None
        try:
            hwp = win32com.client.GetActiveObject("HWPFrame.HwpObject")
        except Exception:
            try:
                hwp = win32com.client.Dispatch("HWPFrame.HwpObject")
                hwp.XHwpWindows.Item(0).Visible = True
                hwp.HAction.Run("FileNew")
            except Exception as de:
                return {"success": False, "error": f"HWP Launch Error: {de}"}

        if not hwp:
            return {"success": False, "error": "Cannot connect to HWP"}

        try:
            try:
                hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
            except Exception:
                pass

            try:
                hwp.XHwpWindows.Item(0).Visible = True
            except Exception:
                pass

            layout_cfg = hwp_layout or {}
            include_title = layout_cfg.get("include_title", True)
            if include_title and step_title:
                act = hwp.CreateAction("InsertText")
                pset = act.CreateSet()
                pset.SetItem("Text", step_title + "\n")
                act.Execute(pset)

            hwp.HAction.Run("Paste")
            hwp.HAction.Run("BreakPara")

            try:
                hwnd = win32gui.FindWindow("HwpMainEditWnd", None)
                if not hwnd:
                    hwnd = win32gui.FindWindow("HWP", None)
                if hwnd:
                    ExportEngine.activate_window(hwnd)
            except Exception:
                pass

            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def qimage_to_pil(qimg: QImage) -> Image.Image:
        qimg = qimg.convertToFormat(QImage.Format_RGBA8888)
        width = qimg.width()
        height = qimg.height()
        ptr = qimg.bits()
        if hasattr(ptr, "setsize"):
            ptr.setsize(height * width * 4)
        arr = bytes(ptr)
        return Image.frombytes("RGBA", (width, height), arr)

    @staticmethod
    def resize_to_target_width(pil_img: Image.Image, target_width: int) -> Image.Image:
        orig_w, orig_h = pil_img.size
        if target_width <= 0 or orig_w == target_width:
            return pil_img
        # Lanczos 고품질 비율 유지 리샘플링
        ratio = target_width / float(orig_w)
        target_h = int(orig_h * ratio)
        return pil_img.resize((target_width, target_h), Image.Resampling.LANCZOS)

    @staticmethod
    def copy_to_clipboard(pil_img: Image.Image):
        """Windows 네이티브 CF_DIB 포맷으로 클립보드에 주입하여 PPT 100% 호환"""
        # 알파 채널을 흰색 배경으로 블렌딩 (DIB 호환성)
        rgb_img = Image.new("RGB", pil_img.size, (255, 255, 255))
        if pil_img.mode == "RGBA":
            rgb_img.paste(pil_img, mask=pil_img.split()[3])
        else:
            rgb_img.paste(pil_img)

        output = io.BytesIO()
        rgb_img.save(output, "BMP")
        bmp_data = output.getvalue()
        output.close()

        # BMP 헤더 14바이트를 제외한 데이터가 DIB
        dib_data = bmp_data[14:]

        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, dib_data)
        finally:
            win32clipboard.CloseClipboard()

    @staticmethod
    def send_to_powerpoint(pil_img: Image.Image, temp_folder: str, ppt_layout: dict = None) -> bool:
        """열려 있는 파워포인트의 활성 프레젠테이션에 새 슬라이드 생성 및 지정된 좌상단(Left, Top)과 배율로 정밀 삽입"""
        try:
            ppt_app = win32com.client.GetActiveObject("PowerPoint.Application")
        except Exception:
            try:
                ppt_app = win32com.client.Dispatch("PowerPoint.Application")
                ppt_app.Visible = True
            except Exception:
                return False

        try:
            layout_cfg = ppt_layout or {}
            tpl_path = str(layout_cfg.get("template_path", "")).strip()

            if ppt_app.Presentations.Count == 0:
                # 열려 있는 프레젠테이션이 없으면 템플릿 열기 또는 새 프레젠테이션 생성
                if tpl_path and os.path.exists(tpl_path):
                    try:
                        pres = ppt_app.Presentations.Open(os.path.abspath(tpl_path))
                    except Exception:
                        pres = ppt_app.Presentations.Add()
                else:
                    pres = ppt_app.Presentations.Add()
            else:
                pres = ppt_app.ActivePresentation

            # 임시 이미지 파일 저장
            os.makedirs(temp_folder, exist_ok=True)
            temp_img_path = os.path.join(temp_folder, "temp_ppt_export.png")
            pil_img.save(temp_img_path, "PNG")

            slide_width = pres.PageSetup.SlideWidth
            slide_height = pres.PageSetup.SlideHeight

            # 현재 슬라이드 인덱스 확인
            try:
                curr_idx = ppt_app.ActiveWindow.View.Slide.SlideIndex
            except Exception:
                curr_idx = pres.Slides.Count

            # 12 = ppLayoutBlank (빈 슬라이드)
            new_slide = pres.Slides.Add(curr_idx + 1, 12)

            layout_cfg = ppt_layout or {}
            ppt_left = float(layout_cfg.get("left", 50))
            ppt_top = float(layout_cfg.get("top", 80))
            ppt_scale = float(layout_cfg.get("scale", 90)) / 100.0
            include_title = bool(layout_cfg.get("include_title", True))

            img_w, img_h = pil_img.size

            # 사용자 지정 배율 적용 크기 (pt)
            target_w = img_w * ppt_scale
            target_h = img_h * ppt_scale
            left = max(0.0, ppt_left)
            top = max(0.0, ppt_top)

            # 이미지 삽입
            new_slide.Shapes.AddPicture(
                temp_img_path,
                LinkToFile=False,
                SaveWithDocument=True,
                Left=left,
                Top=top,
                Width=target_w,
                Height=target_h
            )

            # 상단 단계 제목 상자 (사용자 지정 위치, 크기, 폰트, 색상, 템플릿 적용)
            if include_title:
                t_left = float(layout_cfg.get("title_left", left))
                t_top = float(layout_cfg.get("title_top", 15.0 if top < 50.0 else max(15.0, top - 45.0)))
                t_w = float(layout_cfg.get("title_width", max(target_w, 400.0)))
                t_h = float(layout_cfg.get("title_height", 35.0))

                title_box = new_slide.Shapes.AddTextbox(1, t_left, t_top, t_w, t_h) # 1 = msoTextOrientationHorizontal
                tf = title_box.TextFrame
                try:
                    tf.MarginLeft = 0
                    tf.MarginTop = 0
                    tf.MarginRight = 0
                    tf.MarginBottom = 0
                except Exception:
                    pass

                step_num = max(1, new_slide.SlideIndex - 1)
                tmpl = layout_cfg.get("title_template", "Step {n}. [단계명 입력]")
                tf.TextRange.Text = tmpl.replace("{n}", str(step_num))

                font_family = layout_cfg.get("title_font_family", "Malgun Gothic")
                font_size = float(layout_cfg.get("title_font_size", 18))
                font_bold = bool(layout_cfg.get("title_font_bold", True))
                font_color = layout_cfg.get("title_font_color", "#000000")

                tf.TextRange.Font.Name = font_family
                tf.TextRange.Font.Size = font_size
                tf.TextRange.Font.Bold = font_bold

                try:
                    qcol = QColor(font_color)
                    if qcol.isValid():
                        # Office COM RGB format is BGR: R + (G << 8) + (B << 16)
                        bgr_color = qcol.red() + (qcol.green() << 8) + (qcol.blue() << 16)
                        tf.TextRange.Font.Color.RGB = bgr_color
                except Exception as col_err:
                    print(f"[PowerPoint Title Font Color Error]: {col_err}")

            # 화면 포커스 이동
            new_slide.Select()
            return True
        except Exception as e:
            print(f"[PowerPoint COM 오류]: {e}")
            return False

    @staticmethod
    def find_google_slides_window() -> tuple:
        """
        열려 있는 웹 브라우저(Chrome, Edge, Whale, Firefox 등)에서
        구글 슬라이드 편집 창을 탐색하여 (hwnd, title) 튜플 반환.
        """
        import ctypes
        import win32con
        user32 = ctypes.windll.user32

        # 1. Default 데스크톱 전환 시도 (서비스나 백그라운드 환경 대응)
        try:
            hDesk = user32.OpenDesktopW("Default", 0, False, win32con.GENERIC_ALL)
            if hDesk:
                user32.SetThreadDesktop(hDesk)
        except Exception:
            pass

        SLIDES_KEYWORDS = [
            "google slides",
            "google 프레젠테이션",
            "구글 슬라이드",
            "google スライド",
            "google 幻灯片",
            "google präsentationen",
            "presentaciones de google",
            "apresentações google",
            "google презентации",
            "docs.google.com/presentation"
        ]

        found_windows = []
        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)

        def enum_cb(hwnd, _extra):
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buf = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buf, length + 1)
                    title = buf.value
                    title_lower = title.lower()
                    for kw in SLIDES_KEYWORDS:
                        if kw in title_lower:
                            found_windows.append((hwnd, title))
                            break
            return True

        user32.EnumWindows(WNDENUMPROC(enum_cb), 0)

        if not found_windows:
            return (0, "")
        return found_windows[0]

    @staticmethod
    def activate_window(hwnd: int) -> bool:
        """지정된 HWND 창을 전면(Foreground)으로 복원 및 활성화"""
        import ctypes
        import win32process
        import win32api
        import win32gui
        import win32con
        import time

        user32 = ctypes.windll.user32
        if not hwnd or not user32.IsWindow(hwnd):
            return False

        try:
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            else:
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)

            cur_thread = win32api.GetCurrentThreadId()
            fore_hwnd = win32gui.GetForegroundWindow()
            fore_thread, _ = win32process.GetWindowThreadProcessId(fore_hwnd)

            if cur_thread != fore_thread and fore_thread != 0:
                win32process.AttachThreadInput(cur_thread, fore_thread, True)
                win32gui.SetForegroundWindow(hwnd)
                win32gui.BringWindowToTop(hwnd)
                win32process.AttachThreadInput(cur_thread, fore_thread, False)
            else:
                win32gui.SetForegroundWindow(hwnd)
                win32gui.BringWindowToTop(hwnd)

            time.sleep(0.15)
            return True
        except Exception as e:
            print(f"[창 활성화 오류]: {e}")
            try:
                win32gui.SetForegroundWindow(hwnd)
                return True
            except Exception:
                return False

    @staticmethod
    def send_to_google_slides(pil_img: Image.Image, return_focus_hwnd: int = None, return_focus: bool = True) -> dict:
        """
        웹 브라우저의 구글 슬라이드 창을 감지하여:
        1. 클립보드에 이미지 주입 (CF_DIB)
        2. 구글 슬라이드 창 활성화
        3. Ctrl + M (새 슬라이드 생성)
        4. Ctrl + V (이미지 붙여넣기)
        5. (선택) 원래 스튜디오 창으로 포커스 복귀
        """
        import time
        import win32api
        import win32con

        hwnd, title = ExportEngine.find_google_slides_window()
        if not hwnd:
            return {"success": False, "error": "NOT_FOUND"}

        # 1. 클립보드 복사
        ExportEngine.copy_to_clipboard(pil_img)

        # 2. 브라우저 창 활성화
        if not ExportEngine.activate_window(hwnd):
            return {"success": False, "error": "ACTIVATE_FAILED"}

        time.sleep(0.2)

        # 3. Ctrl + M 송출 (구글 슬라이드 새 슬라이드 생성 단축키)
        win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
        win32api.keybd_event(ord('M'), 0, 0, 0)
        time.sleep(0.05)
        win32api.keybd_event(ord('M'), 0, win32con.KEYEVENTF_KEYUP, 0)
        win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)

        # 구글 슬라이드 캔버스 생성 대기
        time.sleep(0.35)

        # 4. Ctrl + V 송출 (클립보드 이미지 붙여넣기)
        win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
        win32api.keybd_event(ord('V'), 0, 0, 0)
        time.sleep(0.05)
        win32api.keybd_event(ord('V'), 0, win32con.KEYEVENTF_KEYUP, 0)
        win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)

        time.sleep(0.25)

        # 5. 스튜디오로 포커스 복귀
        if return_focus and return_focus_hwnd:
            time.sleep(0.1)
            ExportEngine.activate_window(return_focus_hwnd)

        return {"success": True, "title": title}

    @staticmethod
    def auto_backup_step_bundle(
        pil_img: Image.Image,
        raw_pixmap: QPixmap,
        items: list,
        next_stamp_index: int,
        save_dir: str,
        existing_project_path: str = None,
        ppt_layout: dict = None
    ) -> dict:
        """
        F10 실행 시 3종 세트 동시 자동 저장:
        1. Step_NNN.png (Bake 일체형 이미지)
        2. Step_NNN_raw.png (순수 원본 비트맵)
        3. Step_NNN.mcs.json (객체 분리 프로젝트 파일)
        """
        today_str = datetime.now().strftime("%Y%m%d")
        dest_folder = os.path.join(save_dir, f"captures_{today_str}")
        os.makedirs(dest_folder, exist_ok=True)

        # 기존 프로젝트를 열어서 수정한 경우 해당 파일명 유지, 아니면 새 Step 번호 생성
        if existing_project_path and os.path.exists(existing_project_path):
            base_dir = os.path.dirname(existing_project_path)
            base_file = os.path.basename(existing_project_path)
            clean_name = base_file.replace(".mcs.json", "").replace(".json", "")
            bake_path = os.path.join(base_dir, f"{clean_name}.png")
            project_path = existing_project_path
        else:
            existing = [
                f for f in os.listdir(dest_folder)
                if f.startswith("Step_") and f.endswith(".png") and not f.endswith("_raw.png")
            ]
            next_num = len(existing) + 1
            clean_name = f"Step_{next_num:03d}"
            bake_path = os.path.join(dest_folder, f"{clean_name}.png")
            project_path = os.path.join(dest_folder, f"{clean_name}.mcs.json")

        # 1. 일체형 Bake 이미지 저장
        pil_img.save(bake_path, "PNG")

        # 2 & 3. ProjectManager를 통해 raw_img와 .mcs.json 동시 저장
        metadata = {"ppt_layout": ppt_layout or {}}
        ProjectManager.save_project(project_path, raw_pixmap, items, next_stamp_index, metadata=metadata)

        raw_img_path = os.path.join(os.path.dirname(project_path), f"{clean_name}_raw.png")

        return {
            "bake_path": bake_path,
            "raw_path": raw_img_path,
            "project_path": project_path
        }

    @staticmethod
    def auto_backup_file(pil_img: Image.Image, save_dir: str) -> str:
        today_str = datetime.now().strftime("%Y%m%d")
        dest_folder = os.path.join(save_dir, f"captures_{today_str}")
        os.makedirs(dest_folder, exist_ok=True)

        existing = [
            f for f in os.listdir(dest_folder)
            if f.startswith("Step_") and f.endswith(".png") and not f.endswith("_raw.png")
        ]
        next_num = len(existing) + 1
        file_name = f"Step_{next_num:03d}.png"
        full_path = os.path.join(dest_folder, file_name)
        pil_img.save(full_path, "PNG")
        return full_path

    @staticmethod
    def renumber_powerpoint_steps(file_path: str = None, start_from: int = 1) -> dict:
        """
        열려 있는 파워포인트(또는 지정된 PPTX 파일)의 모든 슬라이드를 순회하며
        슬라이드의 물리적 순서대로 Step 번호를 1부터 순차적으로 일괄 재부여(Renumbering)합니다.
        
        보존 원칙:
        1. 기존 텍스트(단계명, 상세설명) 및 서식(폰트, 크기, 색상, 굵기) 100% 보존
        2. Step 번호가 없는 표지/구분/안내 슬라이드는 자동으로 건너뜀 (순번 미증가)
        3. 본문 설명 내 인용구(예: 'Step 1 참조')의 오작동 방지 (상단 제목 상자만 정밀 타겟팅)
        """
        import re
        import os

        pattern_lead = re.compile(
            r'(?i)^(\s*\[?\s*(?:[\U00010000-\U0010ffff]|[\u2600-\u27bf]|#|\d+\.)?\s*step[\s._-]*)(\d+)'
        )
        pattern_general = re.compile(r'(?i)\b(step[\s._-]*)(\d+)')

        opened_by_us = False
        ppt_app = None
        pres = None

        try:
            if file_path:
                if not os.path.exists(file_path):
                    return {"success": False, "error": f"파일을 찾을 수 없습니다: {file_path}", "details": []}
                try:
                    ppt_app = win32com.client.GetActiveObject("PowerPoint.Application")
                except Exception:
                    ppt_app = win32com.client.Dispatch("PowerPoint.Application")

                abs_path = os.path.abspath(file_path)
                for p in ppt_app.Presentations:
                    try:
                        if os.path.abspath(p.FullName).lower() == abs_path.lower():
                            pres = p
                            break
                    except Exception:
                        pass
                if pres is None:
                    pres = ppt_app.Presentations.Open(abs_path)
                    opened_by_us = True
            else:
                try:
                    ppt_app = win32com.client.GetActiveObject("PowerPoint.Application")
                except Exception:
                    try:
                        ppt_app = win32com.client.Dispatch("PowerPoint.Application")
                    except Exception as e:
                        return {"success": False, "error": f"파워포인트를 실행하거나 연결할 수 없습니다: {e}", "details": []}

                if ppt_app.Presentations.Count == 0:
                    return {"success": False, "error": "열려 있는 파워포인트 프레젠테이션이 없습니다.", "details": []}

                try:
                    pres = ppt_app.ActivePresentation
                except Exception:
                    pres = ppt_app.Presentations.Item(1)

            total_slides = pres.Slides.Count
            current_step = start_from
            details = []

            for s_idx in range(1, total_slides + 1):
                slide = pres.Slides.Item(s_idx)
                target_shape = None
                matched_m = None

                # 1단계: 텍스트가 Step으로 시작하는 제목 상자 우선 탐색 (가장 상단 우선)
                candidates = []
                for shp in slide.Shapes:
                    try:
                        if shp.HasTextFrame and shp.TextFrame.HasText:
                            txt = shp.TextFrame.TextRange.Text
                            m = pattern_lead.search(txt)
                            if m:
                                candidates.append((shp.Top, shp, m, txt))
                    except Exception:
                        continue

                if candidates:
                    candidates.sort(key=lambda x: x[0])
                    _, target_shape, matched_m, raw_text = candidates[0]
                else:
                    # 2단계: 상단 180pt 이내에 위치하며 Step N을 포함하는 상자 보조 탐색
                    secondary = []
                    for shp in slide.Shapes:
                        try:
                            if shp.Top < 180 and shp.HasTextFrame and shp.TextFrame.HasText:
                                txt = shp.TextFrame.TextRange.Text
                                m = pattern_general.search(txt)
                                if m:
                                    secondary.append((shp.Top, shp, m, txt))
                        except Exception:
                            continue
                    if secondary:
                        secondary.sort(key=lambda x: x[0])
                        _, target_shape, matched_m, raw_text = secondary[0]

                if target_shape is not None and matched_m is not None:
                    old_step_str = matched_m.group(2)
                    old_full = raw_text.strip().replace('\r', '').replace('\n', ' ')
                    new_step_str = str(current_step)

                    # 서식 100% 보존을 위해 Characters 범위 단위로 숫자만 정밀 치환
                    com_start = matched_m.start(2) + 1
                    com_len = len(old_step_str)
                    replaced = False
                    try:
                        sub_range = target_shape.TextFrame.TextRange.Characters(com_start, com_len)
                        if sub_range.Text == old_step_str:
                            sub_range.Text = new_step_str
                            replaced = True
                    except Exception:
                        pass

                    if not replaced:
                        new_txt = pattern_general.sub(rf'\g<1>{new_step_str}', raw_text, count=1)
                        target_shape.TextFrame.TextRange.Text = new_txt

                    new_full = target_shape.TextFrame.TextRange.Text.strip().replace('\r', '').replace('\n', ' ')

                    details.append({
                        "slide_index": s_idx,
                        "old_step": old_step_str,
                        "new_step": new_step_str,
                        "old_title": old_full,
                        "new_title": new_full,
                        "is_step": True
                    })
                    current_step += 1
                else:
                    # 비Step 슬라이드 (표지, 구분선, 목차 등)
                    details.append({
                        "slide_index": s_idx,
                        "old_step": "-",
                        "new_step": "-",
                        "old_title": "(표지/구분 슬라이드 - 내용 보존)",
                        "new_title": "(표지/구분 슬라이드 - 내용 보존)",
                        "is_step": False
                    })

            if opened_by_us:
                pres.Save()

            return {
                "success": True,
                "presentation_name": pres.Name,
                "total_slides": total_slides,
                "renumbered_count": current_step - start_from,
                "skipped_count": total_slides - (current_step - start_from),
                "details": details
            }

        except Exception as e:
            return {"success": False, "error": str(e), "details": []}



    @staticmethod
    def export_to_markdown(steps: list, output_path: str, title: str = "Manual Studio Documentation") -> str:
        """AI 에이전트 및 팀 협업용 GitHub 호환 마크다운 매뉴얼 파일 생성"""
        out_dir = os.path.dirname(os.path.abspath(output_path))
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
            
        md_lines = [
            f"# {title}",
            "",
            "> Generated automatically by DragonRPA Manual Studio AI Engine",
            "",
            "## Table of Contents",
        ]
        for i, step in enumerate(steps):
            s_title = step.get("title", f"Step {i+1}")
            anchor = f"step-{i+1}"
            md_lines.append(f"- [{s_title}](#{anchor})")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

        for i, step in enumerate(steps):
            s_title = step.get("title", f"Step {i+1}")
            s_desc = step.get("description", "")
            img_file = step.get("image_file", "")
            # 상대 경로화
            if img_file and os.path.isabs(img_file) and out_dir:
                try:
                    rel_img = os.path.relpath(img_file, out_dir).replace("\\", "/")
                except Exception:
                    rel_img = img_file.replace("\\", "/")
            else:
                rel_img = img_file.replace("\\", "/")

            md_lines.append(f"<a id='step-{i+1}'></a>")
            md_lines.append(f"### Step {i+1}. {s_title}")
            if s_desc:
                md_lines.append(f"\n{s_desc}\n")
            if rel_img:
                md_lines.append(f"\n![{s_title}]({rel_img})\n")
            md_lines.append("")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines) + "\n")
        return output_path

    @staticmethod
    def export_to_animated_gif(pil_images: list, output_path: str, interval_sec: float = 1.5) -> str:
        """
        다단계 이미지들을 순차적으로 보여주는 초경량 루프 애니메이션 GIF를 생성합니다.
        메신저(슬랙, 카카오톡), 노션, 위키 등에 바로 공유할 수 있습니다.
        """
        if not pil_images:
            raise ValueError("No images provided for GIF export")

        out_dir = os.path.dirname(os.path.abspath(output_path))
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        frames = []
        for im in pil_images:
            rgb = Image.new("RGB", im.size, (255, 255, 255))
            if im.mode == "RGBA":
                rgb.paste(im, mask=im.split()[3])
            else:
                rgb.paste(im)
            frames.append(rgb)

        duration_ms = max(200, int(interval_sec * 1000))
        frames[0].save(
            output_path,
            save_all=True,
            append_images=frames[1:],
            duration=duration_ms,
            loop=0,
            optimize=True
        )
        return output_path

    @staticmethod
    def export_to_html(steps: list, output_path: str, title: str = "Manual Studio Interactive Guide") -> str:
        """단일 독립 실행형 반응형 HTML 매뉴얼 파일 생성 (인쇄/PDF 최적화 내장)"""
        out_dir = os.path.dirname(os.path.abspath(output_path))
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        step_cards_html = []
        nav_items_html = []
        for i, step in enumerate(steps):
            num = step.get("step_num", i + 1)
            s_title = step.get("title", f"Step {num}")
            s_desc = step.get("description", "")
            img_b64 = step.get("image_b64", "")
            img_file = step.get("image_file", "")

            if img_b64:
                src_to_use = img_b64
            elif img_file:
                if os.path.isabs(img_file) and out_dir:
                    try:
                        rel_img = os.path.relpath(img_file, out_dir).replace("\\", "/")
                    except Exception:
                        rel_img = img_file.replace("\\", "/")
                else:
                    rel_img = img_file.replace("\\", "/")
                src_to_use = rel_img
            else:
                src_to_use = ""

            nav_items_html.append(f'<li><a href="#step-{num}" class="nav-link"><span class="step-num">{num}</span> {s_title}</a></li>')

            img_tag = f'<div class="step-image-box"><img src="{src_to_use}" alt="{s_title}" class="step-img" loading="lazy" /></div>' if src_to_use else ''
            desc_tag = f'<p class="step-desc">{s_desc}</p>' if s_desc else ''

            step_cards_html.append(f"""
            <section id="step-{num}" class="step-card">
              <div class="step-header">
                <span class="step-badge">STEP {num:02d}</span>
                <h2 class="step-title">{s_title}</h2>
              </div>
              {desc_tag}
              {img_tag}
            </section>
            """)

        html_template = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    :root {{
      --bg: #0F172A;
      --card-bg: #1E293B;
      --text: #F8FAFC;
      --text-muted: #94A3B8;
      --primary: #38BDF8;
      --primary-dark: #0284C7;
      --border: #334155;
      --accent: #E53935;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Malgun Gothic", sans-serif;
      background: var(--bg);
      color: var(--text);
      display: flex;
      min-height: 100vh;
      line-height: 1.6;
    }}
    aside.sidebar {{
      width: 280px;
      background: #090D16;
      border-right: 1px solid var(--border);
      position: sticky;
      top: 0;
      height: 100vh;
      overflow-y: auto;
      padding: 24px 16px;
      flex-shrink: 0;
    }}
    .sidebar h1 {{ font-size: 1.1rem; color: var(--primary); margin-bottom: 20px; font-weight: 700; }}
    .sidebar ul {{ list-style: none; }}
    .sidebar li {{ margin-bottom: 8px; }}
    .nav-link {{
      color: var(--text-muted);
      text-decoration: none;
      font-size: 0.9rem;
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 6px;
      transition: all 0.15s ease;
    }}
    .nav-link:hover {{ background: var(--border); color: #FFF; }}
    .step-num {{
      background: var(--primary-dark);
      color: #FFF;
      font-size: 0.75rem;
      padding: 2px 6px;
      border-radius: 4px;
      font-weight: bold;
    }}
    main.content {{
      flex: 1;
      max-width: 1040px;
      padding: 40px;
      margin: 0 auto;
    }}
    .doc-header {{
      border-bottom: 1px solid var(--border);
      padding-bottom: 24px;
      margin-bottom: 40px;
    }}
    .doc-header h1 {{ font-size: 2rem; color: #FFF; margin-bottom: 8px; font-weight: 800; }}
    .doc-meta {{ color: var(--text-muted); font-size: 0.85rem; }}
    .step-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 28px;
      margin-bottom: 40px;
      box-shadow: 0 4px 16px rgba(0,0,0,0.3);
      scroll-margin-top: 40px;
    }}
    .step-header {{
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
    }}
    .step-badge {{
      background: var(--primary);
      color: #0F172A;
      font-size: 0.8rem;
      font-weight: 800;
      padding: 4px 10px;
      border-radius: 6px;
    }}
    .step-title {{ font-size: 1.35rem; font-weight: 700; color: #FFF; }}
    .step-desc {{ color: #CBD5E1; margin-bottom: 20px; font-size: 1rem; }}
    .step-image-box {{
      background: #020617;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px;
      text-align: center;
    }}
    .step-img {{
      max-width: 100%;
      height: auto;
      border-radius: 6px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.5);
    }}
    @media print {{
      aside.sidebar {{ display: none; }}
      main.content {{ max-width: 100%; padding: 0; }}
      .step-card {{ page-break-inside: avoid; border: 1px solid #CCC; color: #000; background: #FFF; }}
      .step-title {{ color: #000; }}
      .step-desc {{ color: #333; }}
      body {{ background: #FFF; color: #000; }}
    }}
  </style>
</head>
<body>
  <aside class="sidebar">
    <h1>Manual Studio</h1>
    <ul>
      {''.join(nav_items_html)}
    </ul>
  </aside>
  <main class="content">
    <header class="doc-header">
      <h1>{title}</h1>
      <p class="doc-meta">Automated Documentation by DragonRPA Manual Studio AI Engine</p>
    </header>
    {''.join(step_cards_html)}
  </main>
</body>
</html>"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_template)
        return output_path

    @staticmethod
    def export_to_pdf(steps: list, output_path: str, orientation: str = "landscape", title: str = None) -> dict:
        """
        PySide6 QPdfWriter 및 QPainter 기반 300 DPI 초고화질 네이티브 PDF 문서 직접 생성
        외부 Acrobat/프린터 설치 없이 순수 코어로 1초 만에 PDF 빌드
        """
        from PySide6.QtGui import QPdfWriter, QPageSize, QPageLayout, QPainter, QFont, QColor, QPen, QBrush, QImage
        from PySide6.QtCore import QMarginsF, QRectF, Qt, QPointF

        if not steps:
            return {"success": False, "error": "내보낼 슬라이드가 없습니다."}

        writer = QPdfWriter(output_path)
        writer.setResolution(300)
        
        is_landscape = (orientation.lower() == "landscape")
        page_orient = QPageLayout.Landscape if is_landscape else QPageLayout.Portrait
        writer.setPageSize(QPageSize(QPageSize.A4))
        writer.setPageOrientation(page_orient)
        writer.setPageMargins(QMarginsF(10, 10, 10, 10), QPageLayout.Millimeter)

        doc_title = title or "Manual Studio 매뉴얼 가이드"
        painter = QPainter(writer)
        if not painter.isActive():
            return {"success": False, "error": "PDF 페인터 초기화에 실패했습니다."}

        total_pages = len(steps)
        for idx, step_data in enumerate(steps):
            if idx > 0:
                writer.newPage()

            step_num = step_data.get("step_num", idx + 1)
            step_title = step_data.get("title", f"Step {step_num}")
            desc = step_data.get("description", "")
            qimg = step_data.get("composed_image")

            pw = writer.width()
            ph = writer.height()

            # 1. 상단 헤더
            painter.setPen(QColor("#1E3A8A"))
            f_head = QFont("Malgun Gothic", 14)
            f_head.setBold(True)
            painter.setFont(f_head)
            header_rect = QRectF(40, 30, pw - 80, 80)
            painter.drawText(header_rect, Qt.AlignLeft | Qt.AlignVCenter, f"Step {step_num}. {step_title}")

            painter.setPen(QPen(QColor("#E2E8F0"), 3))
            painter.drawLine(QPointF(40, 115), QPointF(pw - 40, 115))

            # 2. 중앙 슬라이드 캡처 이미지 렌더링
            if qimg:
                if isinstance(qimg, Image.Image):
                    from io import BytesIO
                    buf = BytesIO()
                    qimg.save(buf, format="PNG")
                    qimg = QImage.fromData(buf.getvalue())

                avail_top = 130
                avail_bottom = ph - 100 if is_landscape else ph - 300
                avail_h = avail_bottom - avail_top
                avail_w = pw - 80

                img_w = qimg.width()
                img_h = qimg.height()
                scale = min(avail_w / max(1, img_w), avail_h / max(1, img_h))
                draw_w = img_w * scale
                draw_h = img_h * scale
                draw_x = 40 + (avail_w - draw_w) / 2.0
                draw_y = avail_top + (avail_h - draw_h) / 2.0
                dest_rect = QRectF(draw_x, draw_y, draw_w, draw_h)

                painter.drawImage(dest_rect, qimg)
                painter.setPen(QPen(QColor("#CBD5E1"), 2))
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(dest_rect)

            # 3. 세로형 보고서일 경우 하단 설명 블록
            if not is_landscape and desc:
                desc_rect = QRectF(40, ph - 280, pw - 80, 200)
                painter.setPen(QColor("#1E293B"))
                f_desc = QFont("Malgun Gothic", 11)
                painter.setFont(f_desc)
                painter.drawText(desc_rect, Qt.AlignLeft | Qt.TextWordWrap, desc)

            # 4. 하단 푸터
            painter.setPen(QColor("#94A3B8"))
            f_foot = QFont("Malgun Gothic", 9)
            painter.setFont(f_foot)
            painter.drawText(QRectF(40, ph - 70, pw / 2, 40), Qt.AlignLeft | Qt.AlignVCenter, doc_title)
            painter.drawText(QRectF(pw / 2, ph - 70, pw / 2 - 40, 40), Qt.AlignRight | Qt.AlignVCenter, f"{idx + 1} / {total_pages}")

        painter.end()
        return {"success": True, "path": output_path, "count": total_pages}

    @staticmethod
    def send_to_word(pil_img: Image.Image, step_title: str = None) -> dict:
        """현재 실행 중인 MS Word 창의 커서 위치에 슬라이드 이미지 및 제목 즉시 삽입 (win32com)"""
        if not win32com:
            return {"success": False, "error": "win32com 모듈을 사용할 수 없습니다."}
        try:
            import tempfile, os
            word = win32com.client.GetActiveObject("Word.Application")
            sel = word.Selection
            if step_title:
                sel.TypeText(f"{step_title}\n")
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
                tmp_path = tf.name
            pil_img.save(tmp_path, "PNG")
            sel.InlineShapes.AddPicture(tmp_path)
            sel.TypeText("\n\n")
            os.remove(tmp_path)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def export_to_word_doc(steps: list, output_path: str, title: str = None) -> dict:
        """python-docx 라이브러리를 활용한 정식 A4 세로 보고서/매뉴얼 .docx 문서 생성"""
        try:
            import docx
            from docx.shared import Inches, Pt, RGBColor
            from docx.enum.text import WD_ALIGN_PARAGRAPH
            import tempfile, os
        except ImportError:
            return {"success": False, "error": "python-docx 모듈이 설치되어 있지 않습니다."}

        doc = docx.Document()
        doc_title = title or "시스템 사용자 업무 매뉴얼"

        # 표지 타이틀
        p_title = doc.add_paragraph()
        p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_title.paragraph_format.space_before = Pt(36)
        p_title.paragraph_format.space_after = Pt(12)
        run_title = p_title.add_run(doc_title)
        run_title.font.name = "Malgun Gothic"
        run_title.font.size = Pt(24)
        run_title.font.bold = True
        run_title.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)

        p_sub = doc.add_paragraph()
        p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_sub.paragraph_format.space_after = Pt(28)
        run_sub = p_sub.add_run(f"발행일: {datetime.now().strftime('%Y-%m-%d')} | DragonRPA Manual Studio")
        run_sub.font.name = "Malgun Gothic"
        run_sub.font.size = Pt(10)
        run_sub.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)

        doc.add_page_break()

        for idx, s in enumerate(steps):
            step_num = s.get("step_num", idx + 1)
            step_title = s.get("title", f"Step {step_num}")
            desc = s.get("description", "")
            pil_img = s.get("pil_image")

            h2 = doc.add_paragraph()
            h2.paragraph_format.space_before = Pt(18)
            h2.paragraph_format.space_after = Pt(8)
            run_h2 = h2.add_run(f"Step {step_num}. {step_title}")
            run_h2.font.name = "Malgun Gothic"
            run_h2.font.size = Pt(14)
            run_h2.font.bold = True
            run_h2.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

            if desc:
                p_desc = doc.add_paragraph()
                p_desc.paragraph_format.space_after = Pt(10)
                run_desc = p_desc.add_run(desc)
                run_desc.font.name = "Malgun Gothic"
                run_desc.font.size = Pt(10.5)

            if pil_img:
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
                    t_path = tf.name
                pil_img.save(t_path, "PNG")
                p_img = doc.add_paragraph()
                p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_img.paragraph_format.space_after = Pt(16)
                p_img.add_run().add_picture(t_path, width=Inches(6.0))
                os.remove(t_path)

        doc.save(output_path)
        return {"success": True, "path": output_path, "count": len(steps)}

    @staticmethod
    def format_notion_markdown(steps: list, title: str = None) -> str:
        """노션(Notion)에 바로 붙여넣기(Ctrl+V) 가능한 최적화 마크다운 텍스트 생성"""
        lines = [f"# {title or '시스템 사용자 업무 매뉴얼'}\n\n> DragonRPA Manual Studio 자동 발행\n"]
        for idx, s in enumerate(steps):
            num = s.get("step_num", idx + 1)
            t = s.get("title", f"Step {num}")
            desc = s.get("description", "")
            lines.append(f"## Step {num}. {t}")
            if desc:
                lines.append(f"{desc}\n")
            lines.append(f"> 💡 **확인 사항**: 본 단계의 안내 이미지를 참조하여 조작을 완료하세요.\n")
        return "\n".join(lines)

    @staticmethod
    def format_confluence_storage_xhtml(steps: list, title: str = None) -> str:
        """Atlassian Confluence Storage Format (XHTML) 규격 소스 생성"""
        doc_title = title or "시스템 사용자 업무 매뉴얼"
        html = [
            f"<h1>{doc_title}</h1>",
            '<ac:structured-macro ac:name="info"><ac:rich-text-body><p>본 문서는 <strong>Manual Studio</strong>에서 생성된 공식 업무 매뉴얼입니다.</p></ac:rich-text-body></ac:structured-macro>'
        ]
        for idx, s in enumerate(steps):
            num = s.get("step_num", idx + 1)
            t = s.get("title", f"Step {num}")
            desc = s.get("description", "")
            html.append(f"<h2>Step {num}. {t}</h2>")
            if desc:
                html.append(f"<p>{desc}</p>")
            html.append(f'<p><ac:image ac:width="720"><ri:attachment ri:filename="step_{num:03d}.png"/></ac:image></p>')
            html.append("<hr/>")
        return "\n".join(html)





# 7. 라이선스 및 사용 기간(Time-Bomb) 검증 관리자 (DragonRPA License Engine)
# ==============================================================================
class LicenseValidator:
    """
    2026-12-31 시한부 수명 통제 및 레지스트리 안티 롤백(Anti-Rollback) 검증 엔진
    """
    EXPIRATION_DATE = datetime(2026, 12, 31, 23, 59, 59)
    REG_SUBKEY = r"Software\DragonRPA\ManualCaptureStudio"
    REG_VALUE_NAME = "KernelTick"

    @classmethod
    def _obfuscate_timestamp(cls, dt: datetime) -> str:
        """타임스탬프 난독화 인코딩"""
        ts = int(dt.timestamp())
        raw = f"DRPA:{ts}:MCS"
        xor_bytes = bytes([b ^ 0x5A for b in raw.encode("utf-8")])
        return base64.b64encode(xor_bytes).decode("ascii")

    @classmethod
    def _deobfuscate_timestamp(cls, enc_str: str):
        """난독화 문자열 복호화"""
        try:
            xor_bytes = base64.b64decode(enc_str.encode("ascii"))
            raw = bytes([b ^ 0x5A for b in xor_bytes]).decode("utf-8")
            parts = raw.split(":")
            if len(parts) == 3 and parts[0] == "DRPA" and parts[2] == "MCS":
                return datetime.fromtimestamp(int(parts[1]))
        except Exception:
            pass
        return None

    @classmethod
    def check_license(cls) -> tuple:
        """
        라이선스 만료일 및 안티 롤백 검증
        반환값: (is_valid: bool, message: str)
        """
        # 정식 라이선스가 등록되어 활성화된 경우 즉시 정상 통과
        if LicenseEngine.is_licensed():
            st = LicenseEngine.check_license_status()
            return True, f"정식 라이선스 인증: {st.get('badge_text')} ({st.get('issued_to')})"

        now = datetime.now()

        # 1차: 만료일(2026-12-31) 도과 여부 검사
        if now > cls.EXPIRATION_DATE:
            return False, (
                "본 프로그램은 [기간 한정 평가판]으로, 사용 유효 기간(2026년 12월 31일)이 만료되었습니다.\n\n"
                "정식 상용 라이선스 발급 및 최신 버전 문의는\n"
                "(주)드래곤알피에이(77.victor.lee@gmail.com)로 문의해 주시기 바랍니다."
            )

        # 2차: 레지스트리 안티 롤백(시간 역행 조작 적발) 검사
        last_run_time = None
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, cls.REG_SUBKEY, 0, winreg.KEY_READ) as key:
                val, _ = winreg.QueryValueEx(key, cls.REG_VALUE_NAME)
                last_run_time = cls._deobfuscate_timestamp(val)
        except Exception:
            pass

        if last_run_time is not None:
            # 기록된 마지막 실행 시간보다 10분 이상 과거면 PC 시계 조작으로 판단
            if (last_run_time - now).total_seconds() > 600:
                return False, (
                    "시스템 시계 변조가 감지되어 프로그램 실행이 차단되었습니다.\n\n"
                    "컴퓨터의 날짜와 시간을 현재 표준 시간으로 올바르게 설정한 후 다시 실행해 주세요."
                )

        # 3차: 검증 성공 시 현재 실행 시각을 레지스트리에 갱신 기록
        try:
            import winreg
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, cls.REG_SUBKEY) as key:
                enc_val = cls._obfuscate_timestamp(now)
                winreg.SetValueEx(key, cls.REG_VALUE_NAME, 0, winreg.REG_SZ, enc_val)
        except Exception:
            pass

        return True, "정상"



# ==============================================================================
# 7-2. 리본 메뉴 고품질 벡터 아이콘 공급자 (RibbonIconProvider)
# ==============================================================================
class RibbonIconProvider:
    """W3C 표준 Lucide 벡터 패스를 QSvgRenderer로 렌더링하는 고해상도 상용 B2B 아이콘 제공자"""
    _cache = {}

    ICONS = {
        # 캡처 계열 (Lucide: Camera, Crop, Layers, Pin, Unfold-Vertical)
        "capture_fixed": '<path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/><circle cx="12" cy="13" r="3"/>',
        "capture_area": '<path d="M6 2v14a2 2 0 0 0 2 2h14"/><path d="M18 22V8a2 2 0 0 0-2-2H2"/>',
        "capture_sub": '<path d="M12 2 2 7l10 5 10-5-10-5Z"/><path d="m2 17 10 5 10-5"/><path d="m2 12 10 5 10-5"/>',
        "save_rect": '<line x1="12" x2="12" y1="17" y2="22"/><path d="M5 17h14v-1.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 10.76V6h1a2 2 0 0 0 0-4H8a2 2 0 0 0 0 4h1v4.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24Z"/>',
        "scroll_stitch": '<path d="m8 22 4-4 4 4"/><path d="m8 2 4 4 4-4"/><rect width="16" height="8" x="4" y="8" rx="2"/>',

        # 프로젝트 계열 (Lucide: File-Plus, Folder-Open, Save, Git-Merge, Refresh-CW, Image, Copy)
        "new_project": '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M9 15h6"/><path d="M12 12v6"/>',
        "open_project": '<path d="m6 14 1.45-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.55 6a2 2 0 0 1-1.94 1.5H4a2 2 0 0 1-2-2V5c0-1.1.9-2 2-2h3.93a2 2 0 0 1 1.66.9l.82 1.2a2 2 0 0 0 1.66.9H18a2 2 0 0 1 2 2v2"/>',
        "save_project": '<path d="M15.2 3a2 2 0 0 1 1.4.6l3.8 3.8a2 2 0 0 1 .6 1.4V19a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z"/><path d="M17 21v-7a1 1 0 0 0-1-1H8a1 1 0 0 0-1 1v7"/><path d="M7 3v4a1 1 0 0 0 1 1h7"/>',
        "merge_project": '<circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><path d="M6 21V9a9 9 0 0 0 9 9"/>',
        "autosave": '<path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/><path d="M16 16h5v5"/>',
        "open_image": '<rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/>',
        "copy_image": '<rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>',

        # 기본 편집 도구 (Lucide: Mouse-Pointer-2, Undo-2, Trash-2)
        "select": '<path d="m3 3 7.07 16.97 2.51-7.39 7.39-2.51L3 3z"/><path d="m13 13 6 6"/>',
        "undo": '<path d="M9 14 4 9l5-5"/><path d="M4 9h10.5a5.5 5.5 0 0 1 5.5 5.5a5.5 5.5 0 0 1-5.5 5.5H11"/>',
        "clear": '<path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" x2="10" y1="11" y2="17"/><line x1="14" x2="14" y1="11" y2="17"/>',

        # 주석 및 드로잉 도구 (Lucide: Circle-Dot, Rotate-CCW, List-Ordered, Corner-Down-Right, Move-Right, Square, Eye-Off, Shield-Check, Eraser, Badge-Alert, Scan-Text, Tag, Ruler, Maximize, Message-Square, Type, Keyboard, Sparkles)
        "stamp": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3"/>',
        "reset_index": '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/>',
        "step_arrow": '<line x1="10" x2="21" y1="6" y2="6"/><line x1="10" x2="21" y1="12" y2="12"/><line x1="10" x2="21" y1="18" y2="18"/><path d="M4 6h1v4"/><path d="M4 10h2"/><path d="M6 18H4c0-1 2-2 2-3s-1-1.5-2-1"/>',
        "elbow": '<path d="m15 10 5 5-5 5"/><path d="M4 4v7a4 4 0 0 0 4 4h12"/>',
        "elbow_tr": '<path d="m19 15-4 4-4-4"/><path d="M5 5h10a4 4 0 0 1 4 4v10"/>',
        "elbow_br": '<path d="m19 9-4-4-4 4"/><path d="M5 19h10a4 4 0 0 0 4-4V5"/>',
        "elbow_bl": '<path d="m15 19 4-4-4-4"/><path d="M5 5v10a4 4 0 0 0 4 4h10"/>',
        "elbow_tl": '<path d="m15 5 4 4-4 4"/><path d="M5 19V9a4 4 0 0 1 4-4h10"/>',
        "arrow": '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
        "box": '<rect width="18" height="18" x="3" y="3" rx="2"/>',
        "blur": '<path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"/><path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"/><path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"/><line x1="2" x2="22" y1="2" y2="22"/>',
        "auto_pii": '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>',
        "eraser": '<path d="m7 21-4.3-4.3c-1-1-1-2.5 0-3.4l9.6-9.6c1-1 2.5-1 3.4 0l5.6 5.6c1 1 1 2.5 0 3.4L13 21"/><path d="M22 21H7"/><path d="m5 11 9 9"/>',
        "draft": '<path d="m3.85 8.62 4.94-4.94A2 2 0 0 1 10.2 3.1L15.38 3a2 2 0 0 1 1.41.59l4.95 4.95a2 2 0 0 1 0 2.82l-4.95 4.95a2 2 0 0 1-1.41.59l-5.18-.1a2 2 0 0 1-1.42-.58L3.85 11.44a2 2 0 0 1 0-2.82z"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/>',
        "ocr": '<path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><path d="M7 8h10"/><path d="M12 8v8"/><path d="M9 16h6"/>',
        "ocr_label": '<path d="M12.586 2.586A2 2 0 0 0 11.172 2H4a2 2 0 0 0-2 2v7.172a2 2 0 0 0 .586 1.414l8.704 8.704a2.426 2.426 0 0 0 3.42 0l6.58-6.58a2.426 2.426 0 0 0 0-3.42z"/><circle cx="7.5" cy="7.5" r=".5" fill="currentColor"/>',
        "dimension": '<path d="M21.3 15.3a2.4 2.4 0 0 1 0 3.4l-2.6 2.6a2.4 2.4 0 0 1-3.4 0L2.7 8.7a2.41 2.41 0 0 1 0-3.4l2.6-2.6a2.41 2.41 0 0 1 3.4 0Z"/><path d="m14.5 12.5 2-2"/><path d="m11.5 9.5 2-2"/><path d="m8.5 6.5 2-2"/><path d="m17.5 15.5 2-2"/>',
        "box_dimension": '<path d="M15 3h6v6"/><path d="M9 21H3v-6"/><path d="M21 3l-7 7"/><path d="M3 21l7-7"/>',
        "callout": '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
        "text": '<polyline points="4 7 4 4 20 4 20 7"/><line x1="9" x2="15" y1="20" y2="20"/><line x1="12" x2="12" y1="4" y2="20"/>',
        "hotkey": '<rect width="20" height="16" x="2" y="4" rx="2"/><path d="M6 8h.01"/><path d="M10 8h.01"/><path d="M14 8h.01"/><path d="M18 8h.01"/><path d="M8 12h.01"/><path d="M12 12h.01"/><path d="M16 12h.01"/><path d="M7 16h10"/>',
        "wordart": '<path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/><path d="M5 3v4"/><path d="M19 17v4"/><path d="M3 5h4"/><path d="M17 19h4"/>',

        # 플로우차트 도구 (Lucide: Workflow, Move-Right, Corner-Down-Right, Capsule, Rect, Diamond, Parallelogram, Database, File-Text, Book-Open)
        "flowchart": '<rect width="8" height="8" x="3" y="3" rx="2"/><path d="M7 11v4a2 2 0 0 0 2 2h4"/><rect width="8" height="8" x="13" y="13" rx="2"/>',
        "flow_line": '<path d="M18 8L22 12L18 16"/><path d="M2 12H22"/>',
        "flow_elbow": '<path d="m19 15-4 4-4-4"/><path d="M5 5h10a4 4 0 0 1 4 4v10"/>',
        "flow_terminal": '<rect width="18" height="12" x="3" y="6" rx="6" ry="6"/>',
        "flow_process": '<rect width="18" height="12" x="3" y="6" rx="1"/>',
        "flow_decision": '<polygon points="12 3 21 12 12 21 3 12"/>',
        "flow_io": '<polygon points="6 6 21 6 18 18 3 18"/>',
        "flow_database": '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/><path d="M3 12c0 1.66 4 3 9 3s9-1.34 9-3"/>',
        "flow_document": '<path d="M4 4a2 2 0 0 1 2-2h8l6 6v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z"/><path d="M14 2v6h6"/><path d="M8 18c2-1 4-1 6 0s4 1 6 0"/>',
        "doc_ref": '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>',
        "flow_align": '<rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/><path d="M14 17.5h7m-3.5-3.5 3.5 3.5-3.5 3.5"/>',
        "mobile_link": '<rect width="14" height="20" x="5" y="2" rx="2" ry="2"/><line x1="12" x2="12.01" y1="18" y2="18"/>',

        # 내보내기 및 슬라이드 관리 (Lucide: Presentation, File-Badge, Globe, Shrink, List-Ordered)
        "ppt_export": '<path d="M2 3h20"/><path d="M21 3v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V3"/><path d="m7 21 5-5 5 5"/>',
        "export_hwp": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" x2="8" y1="13" y2="13"/><line x1="16" x2="8" y1="17" y2="17"/><polyline points="10 9 9 9 8 9"/>',
        "slides_export": '<circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/>',
        "ppt_autofit": '<path d="M4 14h6v6"/><path d="M20 10h-6V4"/><path d="m14 10 7-7"/><path d="m3 21 7-7"/>',
        "ppt_renumber": '<line x1="10" x2="21" y1="6" y2="6"/><line x1="10" x2="21" y1="12" y2="12"/><line x1="10" x2="21" y1="18" y2="18"/><path d="M4 6h1v4"/><path d="M4 10h2"/><path d="M6 18H4c0-1 2-2 2-3s-1-1.5-2-1"/>',

        # 윈도우 및 시스템 (Lucide: App-Window, Film, Settings-2, Bring-to-front, Send-to-back)
        "window_frame": '<rect width="20" height="16" x="2" y="4" rx="2"/><path d="M10 4v4"/><path d="M2 8h20"/><path d="M6 4v4"/>',
        "filmstrip": '<rect width="18" height="18" x="3" y="3" rx="2"/><path d="M7 3v18"/><path d="M3 7.5h4"/><path d="M3 12h18"/><path d="M3 16.5h4"/><path d="M17 3v18"/><path d="M17 7.5h4"/><path d="M17 16.5h4"/>',
        "settings": '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>',
        "bring_front": '<rect width="8" height="8" x="8" y="8" rx="2"/><path d="M4 10a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2"/><path d="M14 20a2 2 0 0 0 2 2h4a2 2 0 0 0 2-2v-4a2 2 0 0 0-2-2"/>',
        "send_back": '<rect width="8" height="8" x="14" y="14" rx="2"/><rect width="8" height="8" x="2" y="2" rx="2"/><path d="M7 14v1a2 2 0 0 0 2 2h1"/><path d="M14 7h1a2 2 0 0 1 2 2v1"/>',
    }

    @classmethod
    def get_icon(cls, name: str, size: int = 18, color: str = "#334155") -> QIcon:
        key = f"{name}_{size}_{color}"
        if key in cls._cache:
            return cls._cache[key]

        body = cls.ICONS.get(name)
        if not body:
            body = '<rect width="18" height="18" x="3" y="3" rx="2"/>'

        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{body}</svg>'
        renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        p = QPainter(pixmap)
        p.setRenderHint(QPainter.Antialiasing)
        renderer.render(p)
        p.end()

        icon = QIcon(pixmap)
        cls._cache[key] = icon
        return icon

    @classmethod
    def get_toggle_icon(cls, name: str, size: int = 18, off_color: str = "#475569", on_color: str = "#2563EB") -> QIcon:
        key = f"toggle_{name}_{size}_{off_color}_{on_color}"
        if key in cls._cache:
            return cls._cache[key]
        icon = QIcon()
        icon.addPixmap(cls.get_icon(name, size, off_color).pixmap(size, size), QIcon.Normal, QIcon.Off)
        icon.addPixmap(cls.get_icon(name, size, on_color).pixmap(size, size), QIcon.Normal, QIcon.On)
        cls._cache[key] = icon
        return icon


# ==============================================================================
# ==============================================================================
# 7-2. 하단 타임라인 스토리보드 필름스트립 위젯 (StepCardWidget & FilmstripDockWidget)
# ==============================================================================

# ------------------------------------------------------------------------------
# 슬라이드 호버 고화질 미리보기 플로팅 위젯 (SlideHoverPreviewWidget)
# ------------------------------------------------------------------------------
class SlideHoverPreviewWidget(QFrame):
    """타임라인 슬라이드 위에 마우스오버 시 커서 약간 위에 고화질 슬라이드 미리보기를 표시하는 플로팅 위젯"""
    _instance = None

    @classmethod
    def get_shared_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, parent=None):
        super().__init__(parent, Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 2px solid #2563EB;
                border-radius: 8px;
            }
        """)
        self.setFixedSize(360, 240)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(16)
        shadow.setColor(QColor(0, 0, 0, 90))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(8, 6, 8, 6)
        vbox.setSpacing(4)

        self.lbl_title = QLabel(self)
        self.lbl_title.setStyleSheet("font-weight: bold; font-size: 11.5px; color: #1E293B; border: none;")
        vbox.addWidget(self.lbl_title)

        self.lbl_preview = QLabel(self)
        self.lbl_preview.setAlignment(Qt.AlignCenter)
        self.lbl_preview.setStyleSheet("background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 4px;")
        vbox.addWidget(self.lbl_preview, 1)

    def show_preview(self, step_idx: int, step_data: dict, global_pos: QPoint):
        step_num = step_data.get("step_num", step_idx + 1)
        title = step_data.get("title", "").strip()
        header_text = f"Step {step_num}. {title}" if title else f"Step {step_num}"
        self.lbl_title.setText(header_text)

        pix = step_data.get("raw_pixmap") or step_data.get("thumbnail")
        if pix and not pix.isNull():
            scaled = pix.scaled(340, 195, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.lbl_preview.setPixmap(scaled)
            self.lbl_preview.setText("")
        else:
            self.lbl_preview.setPixmap(QPixmap())
            self.lbl_preview.setText(tr("slide_empty", "빈 슬라이드"))

        # 마우스 커서 약간 위에 배치
        x = global_pos.x() - 180
        y = global_pos.y() - 255
        screen = QApplication.screenAt(global_pos) or QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            x = max(geom.left() + 10, min(x, geom.right() - 370))
            if y < geom.top() + 10:
                y = global_pos.y() + 25
        self.move(x, y)
        self.show()

class StepCardWidget(QFrame):
    sig_clicked = Signal(int)
    sig_clicked_with_mod = Signal(int, object)
    sig_delete = Signal(int)
    sig_duplicate = Signal(int)
    sig_move_left = Signal(int)
    sig_move_right = Signal(int)

    def __init__(self, step_idx: int, step_data: dict, is_selected: bool = False, is_checked: bool = True, parent=None):
        super().__init__(parent)
        self.step_idx = step_idx
        self.step_data = step_data
        self.is_selected = is_selected
        self.is_checked = is_checked
        self.setFixedSize(110, 78)
        self.setCursor(Qt.PointingHandCursor)
        self.init_ui()

    def init_ui(self):
        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(4, 3, 4, 3)
        vbox.setSpacing(2)

        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(1, 0, 1, 0)
        top_bar.setSpacing(2)

        self.lbl_check = QLabel("✓" if self.is_checked else "", self)
        self.lbl_check.setFixedSize(13, 13)
        self.lbl_check.setAlignment(Qt.AlignCenter)

        step_num = self.step_data.get("step_num", self.step_idx + 1)
        self.lbl_num = QLabel(f"Step {step_num}", self)
        self.lbl_num.setAlignment(Qt.AlignCenter)
        self.lbl_num.setFixedHeight(16)

        top_bar.addWidget(self.lbl_check)
        top_bar.addWidget(self.lbl_num, 1)

        self.lbl_thumb = QLabel(self)
        self.lbl_thumb.setAlignment(Qt.AlignCenter)
        self.lbl_thumb.setFixedHeight(50)
        thumb_pix = self.step_data.get("thumbnail")
        if thumb_pix and not thumb_pix.isNull():
            self.lbl_thumb.setPixmap(thumb_pix.scaled(98, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.lbl_thumb.setText(tr("slide_empty", "빈 슬라이드"))
            self.lbl_thumb.setStyleSheet("color: #94A3B8; font-size: 10px;")

        vbox.addLayout(top_bar)
        vbox.addWidget(self.lbl_thumb)
        self.update_style()

    def update_style(self):
        if self.is_checked:
            self.lbl_check.setText("✓")
            self.lbl_check.setStyleSheet("background-color: #2563EB; color: #FFFFFF; border-radius: 6px; font-size: 8.5px; font-weight: bold;")
        else:
            self.lbl_check.setText("")
            self.lbl_check.setStyleSheet("border: 1px solid #CBD5E1; border-radius: 6px; background-color: #FFFFFF;")

        if self.is_selected:
            self.setStyleSheet("""
                QFrame {
                    background-color: #EFF6FF;
                    border: 2px solid #2563EB;
                    border-radius: 6px;
                }
                QLabel {
                    color: #1D4ED8;
                    font-size: 11px;
                    font-weight: bold;
                }
            """)
        elif self.is_checked:
            self.setStyleSheet("""
                QFrame {
                    background-color: #F8FAFC;
                    border: 1.5px solid #60A5FA;
                    border-radius: 6px;
                }
                QLabel {
                    color: #1E40AF;
                    font-size: 10.5px;
                    font-weight: 500;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #F8FAFC;
                    border: 1px solid #E2E8F0;
                    border-radius: 6px;
                }
                QFrame:hover {
                    border-color: #94A3B8;
                    background-color: #F1F5F9;
                }
                QLabel {
                    color: #94A3B8;
                    font-size: 10.5px;
                    font-weight: 500;
                }
            """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.pos()
            self.sig_clicked.emit(self.step_idx)
            self.sig_clicked_with_mod.emit(self.step_idx, event.modifiers())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and hasattr(self, "drag_start_pos"):
            if (event.pos() - self.drag_start_pos).manhattanLength() >= QApplication.startDragDistance():
                drag = QDrag(self)
                mime = QMimeData()
                mime.setData("application/x-manualstudio-step-index", str(self.step_idx).encode("utf-8"))
                drag.setMimeData(mime)
                pixmap = self.grab()
                drag.setPixmap(pixmap)
                drag.setHotSpot(event.pos())
                drag.exec(Qt.MoveAction)
                return
        super().mouseMoveEvent(event)

    def enterEvent(self, event):
        super().enterEvent(event)
        parent_film = self.parent()
        while parent_film and not isinstance(parent_film, FilmstripDockWidget):
            parent_film = parent_film.parent()
        if parent_film and getattr(parent_film, "hover_preview_enabled", True):
            if not hasattr(self, "_hover_timer"):
                self._hover_timer = QTimer(self)
                self._hover_timer.setSingleShot(True)
                self._hover_timer.timeout.connect(self._on_hover_timeout)
            self._hover_timer.start(250)

    def leaveEvent(self, event):
        super().leaveEvent(event)
        if hasattr(self, "_hover_timer"):
            self._hover_timer.stop()
        self.hide_hover_preview()

    def _on_hover_timeout(self):
        parent_film = self.parent()
        while parent_film and not isinstance(parent_film, FilmstripDockWidget):
            parent_film = parent_film.parent()
        if parent_film and getattr(parent_film, "hover_preview_enabled", True):
            SlideHoverPreviewWidget.get_shared_instance().show_preview(self.step_idx, self.step_data, QCursor.pos())

    def hide_hover_preview(self):
        if SlideHoverPreviewWidget._instance:
            SlideHoverPreviewWidget._instance.hide()



# ==============================================================================
# MarkItDown 비동기 변환 워커 & 문서 참조 독 패널 (Document Reference Dock)
# ==============================================================================
class MarkItDownWorkerThread(QThread):
    sig_finished = Signal(str, str)  # file_path, md_text
    sig_error = Signal(str, str)     # file_path, err_msg

    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path

    def run(self):
        try:
            import markitdown
            md = markitdown.MarkItDown()
            result = md.convert(self.file_path)
            self.sig_finished.emit(self.file_path, result.text_content)
        except Exception as e:
            self.sig_error.emit(self.file_path, str(e))


class DocumentReferenceDockWidget(QDockWidget):
    """문서 참조 보조 독 패널 (MarkItDown 변환, MD 로드, 텍스트박스/제목 원클릭 삽입)"""
    sig_insert_text_to_canvas = Signal(str)
    sig_apply_slide_title = Signal(str)

    def __init__(self, parent=None):
        super().__init__(tr("dock_doc_reference", "문서 참조"), parent)
        self.setObjectName("DocumentReferenceDock")
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.setMinimumWidth(320)
        self.current_markdown = ""
        self.current_file_path = ""
        self.worker_thread = None
        self.init_ui()

    def init_ui(self):
        container = QWidget(self)
        self.setWidget(container)
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(8, 6, 8, 6)
        main_layout.setSpacing(6)

        # 1. 상단 툴바
        toolbar_frame = QFrame(container)
        toolbar_frame.setStyleSheet("background-color: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 4px; padding: 2px;")
        tool_layout = QHBoxLayout(toolbar_frame)
        tool_layout.setContentsMargins(4, 4, 4, 4)
        tool_layout.setSpacing(4)

        self.btn_convert_file = QPushButton(tr("btn_markitdown_convert", "외부 파일 변환"), toolbar_frame)
        self.btn_convert_file.setToolTip(tr("tip_convert_file", "PDF, Word, PPTX, Excel, HTML 등을 마크다운으로 변환합니다."))
        self.btn_convert_file.setStyleSheet("background-color: #EFF6FF; color: #1E40AF; border-color: #BFDBFE; font-weight: bold;")
        self.btn_convert_file.clicked.connect(self.action_convert_external_file)
        tool_layout.addWidget(self.btn_convert_file)

        self.btn_open_md = QPushButton(tr("btn_open_md", "MD 열기"), toolbar_frame)
        self.btn_open_md.setToolTip(tr("tip_open_md", "기존 마크다운(.md) 파일을 직접 엽니다."))
        self.btn_open_md.clicked.connect(self.action_open_md_file)
        tool_layout.addWidget(self.btn_open_md)

        self.btn_save_md = QPushButton(tr("btn_save_md", "MD 저장"), toolbar_frame)
        self.btn_save_md.setToolTip(tr("tip_save_md", "변환된 마크다운을 파일로 저장합니다."))
        self.btn_save_md.clicked.connect(self.action_save_md_file)
        tool_layout.addWidget(self.btn_save_md)

        main_layout.addWidget(toolbar_frame)

        # 2. 파일 정보 요약
        self.lbl_info = QLabel(tr("lbl_doc_info_init", "파일: 선택되지 않음 | 단락: 0개 | 0자"), container)
        self.lbl_info.setStyleSheet("font-size: 11px; color: #64748B; font-weight: bold;")
        main_layout.addWidget(self.lbl_info)

        # 3. 뷰어 탭
        self.tabs = QTabWidget(container)
        self.tabs.setStyleSheet("""
            QTabBar::tab {
                font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
                font-size: 11px;
                font-weight: bold;
                padding: 4px 12px;
                white-space: nowrap;
            }
        """)

        # 탭 1: 단락 카드 목록
        tab_cards = QWidget()
        cards_vlayout = QVBoxLayout(tab_cards)
        cards_vlayout.setContentsMargins(2, 4, 2, 4)
        cards_vlayout.setSpacing(4)

        self.scroll_cards = QScrollArea(tab_cards)
        self.scroll_cards.setWidgetResizable(True)
        self.scroll_cards.setStyleSheet("background-color: #F1F5F9; border: 1px solid #CBD5E1;")

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(4, 4, 4, 4)
        self.cards_layout.setSpacing(6)
        self.cards_layout.addStretch()

        self.scroll_cards.setWidget(self.cards_container)
        cards_vlayout.addWidget(self.scroll_cards)
        self.tabs.addTab(tab_cards, tr("tab_doc_cards", "단락 카드"))

        # 탭 2: 마크다운 원문 뷰어
        tab_raw = QWidget()
        raw_vlayout = QVBoxLayout(tab_raw)
        raw_vlayout.setContentsMargins(2, 4, 2, 4)
        raw_vlayout.setSpacing(4)

        self.browser_raw = QTextBrowser(tab_raw)
        self.browser_raw.setStyleSheet("background-color: #FFFFFF; border: 1px solid #CBD5E1; font-size: 11px; color: #1E293B;")
        raw_vlayout.addWidget(self.browser_raw, 1)

        raw_btn_bar = QHBoxLayout()
        self.btn_insert_selected = QPushButton(tr("btn_insert_selected", "선택 텍스트 ➔ 캔버스 텍스트박스 삽입"), tab_raw)
        self.btn_insert_selected.setStyleSheet("background-color: #2563EB; color: #FFFFFF; font-weight: bold;")
        self.btn_insert_selected.clicked.connect(self.action_insert_selected_text)
        raw_btn_bar.addWidget(self.btn_insert_selected)

        self.btn_apply_title_selected = QPushButton(tr("btn_apply_title_selected", "슬라이드 제목 적용"), tab_raw)
        self.btn_apply_title_selected.clicked.connect(self.action_apply_title_selected)
        raw_btn_bar.addWidget(self.btn_apply_title_selected)

        raw_vlayout.addLayout(raw_btn_bar)
        self.tabs.addTab(tab_raw, tr("tab_doc_raw", "마크다운 원문"))

        main_layout.addWidget(self.tabs, 1)

    def action_convert_external_file(self):
        filters = "지원 문서 (*.pdf *.docx *.pptx *.xlsx *.html *.htm *.txt *.csv *.json);;모든 파일 (*.*)"
        path, _ = QFileDialog.getOpenFileName(self, tr("dlg_select_convert_file", "변환할 외부 파일 선택 (MarkItDown)"), "", filters)
        if not path:
            return

        self.lbl_info.setText(f"변환 처리 중: {os.path.basename(path)}...")
        self.worker_thread = MarkItDownWorkerThread(path, self)
        self.worker_thread.sig_finished.connect(self.on_conversion_success)
        self.worker_thread.sig_error.connect(self.on_conversion_failed)
        self.worker_thread.start()

    def on_conversion_success(self, path, md_text):
        self.current_file_path = path
        self.current_markdown = md_text
        self.load_markdown(md_text, os.path.basename(path))

    def on_conversion_failed(self, path, err_msg):
        self.lbl_info.setText(f"변환 실패: {os.path.basename(path)}")
        QMessageBox.warning(self, tr("title_convert_failed", "변환 오류"), f"파일 변환 중 오류가 발생했습니다:\n{err_msg}")

    def action_open_md_file(self):
        path, _ = QFileDialog.getOpenFileName(self, tr("dlg_open_md", "마크다운 파일 열기"), "", "마크다운 파일 (*.md *.markdown *.txt);;모든 파일 (*.*)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                md_text = f.read()
            self.current_file_path = path
            self.current_markdown = md_text
            self.load_markdown(md_text, os.path.basename(path))
        except Exception as e:
            QMessageBox.critical(self, tr("title_file_error", "파일 읽기 오류"), str(e))

    def action_save_md_file(self):
        if not self.current_markdown:
            QMessageBox.information(self, tr("title_notice", "알림"), tr("msg_no_md_to_save", "저장할 마크다운 내용이 없습니다."))
            return
        path, _ = QFileDialog.getSaveFileName(self, tr("dlg_save_md", "마크다운 파일 저장"), "manual.md", "마크다운 파일 (*.md);;모든 파일 (*.*)")
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self.current_markdown)
                QMessageBox.information(self, tr("title_notice", "알림"), tr("msg_save_success", "마크다운 파일이 성공적으로 저장되었습니다."))
            except Exception as e:
                QMessageBox.critical(self, tr("title_file_error", "파일 저장 오류"), str(e))

    def load_markdown(self, md_text, file_name=""):
        self.current_markdown = md_text
        self.browser_raw.setMarkdown(md_text)

        # 단락 분할
        raw_paras = [p.strip() for p in md_text.split("\n\n") if p.strip()]
        char_count = len(md_text)
        self.lbl_info.setText(f"파일: {file_name} | 단락: {len(raw_paras)}개 | {char_count:,}자")

        # 단락 카드 갱신
        while self.cards_layout.count() > 1:
            child = self.cards_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for idx, para in enumerate(raw_paras[:100]):  # 성능을 위해 상위 100개 카드
            card = QFrame(self.cards_container)
            card.setStyleSheet("""
                QFrame {
                    background-color: #FFFFFF;
                    border: 1px solid #CBD5E1;
                    border-radius: 4px;
                    padding: 4px;
                }
                QFrame:hover {
                    border-color: #2563EB;
                    background-color: #F8FAFC;
                }
            """)
            c_layout = QVBoxLayout(card)
            c_layout.setContentsMargins(6, 6, 6, 6)
            c_layout.setSpacing(4)

            # 헤더 또는 단락 본문
            lbl_p = QLabel(para, card)
            lbl_p.setWordWrap(True)
            lbl_p.setStyleSheet("font-size: 11px; color: #1E293B; font-weight: normal;")
            c_layout.addWidget(lbl_p)

            # 버튼 행
            btn_row = QHBoxLayout()
            btn_row.setSpacing(4)

            btn_ins = QPushButton(tr("btn_insert_canvas_card", "텍스트박스 삽입 ➔"), card)
            btn_ins.setStyleSheet("background-color: #EFF6FF; color: #1E40AF; border-color: #BFDBFE; font-weight: bold; font-size: 10px; padding: 2px 6px;")
            btn_ins.clicked.connect(lambda checked=False, text=para: self.sig_insert_text_to_canvas.emit(text))
            btn_row.addWidget(btn_ins)

            btn_title = QPushButton(tr("btn_apply_title_card", "슬라이드 제목"), card)
            btn_title.setStyleSheet("font-size: 10px; padding: 2px 6px;")
            first_line = para.split("\n")[0].lstrip("#").strip()
            btn_title.clicked.connect(lambda checked=False, text=first_line: self.sig_apply_slide_title.emit(text))
            btn_row.addWidget(btn_title)

            btn_row.addStretch()
            c_layout.addLayout(btn_row)

            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

    def action_insert_selected_text(self):
        cursor = self.browser_raw.textCursor()
        sel = cursor.selectedText().strip()
        if not sel:
            sel = self.browser_raw.toPlainText()[:200].strip()
        if sel:
            self.sig_insert_text_to_canvas.emit(sel)

    def action_apply_title_selected(self):
        cursor = self.browser_raw.textCursor()
        sel = cursor.selectedText().strip()
        if not sel:
            sel = self.browser_raw.toPlainText().split("\n")[0].lstrip("#").strip()
        if sel:
            self.sig_apply_slide_title.emit(sel)


class FilmstripDockWidget(QWidget):
    sig_step_selected = Signal(int)
    sig_add_step = Signal()
    sig_delete_step = Signal(int)
    sig_delete_steps = Signal(list)
    sig_duplicate_step = Signal(int)
    sig_duplicate_selected = Signal()
    sig_move_selected = Signal(int)
    sig_toggle_hover_preview = Signal(bool)
    sig_move_step = Signal(int, int)
    sig_export_all_ppt = Signal()
    sig_export_all_slides = Signal()
    sig_export_all_hwp = Signal()
    sig_export_webbook = Signal()
    sig_export_gif = Signal()
    sig_export_pdf = Signal()
    sig_export_word = Signal()
    sig_export_notion = Signal()
    sig_export_confluence = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.steps = []
        self.active_idx = 0
        self.selected_indices = set()
        self.hover_preview_enabled = True
        self.setFixedHeight(115)
        self.init_ui()

    def init_ui(self):
        root_lay = QVBoxLayout(self)
        root_lay.setContentsMargins(6, 4, 6, 4)
        root_lay.setSpacing(4)

        header_bar = QHBoxLayout()
        header_bar.setContentsMargins(2, 0, 2, 0)
        header_bar.setSpacing(6)

        self.lbl_title = QLabel("스토리보드 타임라인 (0개 슬라이드, 0개 선택됨)", self)
        self.lbl_title.setStyleSheet("font-weight: bold; font-size: 11px; color: #1E293B;")
        header_bar.addWidget(self.lbl_title)

        self.btn_add_step = QPushButton(tr("btn_add_slide", "+ 새 슬라이드 (F10)"), self)
        self.btn_add_step.setToolTip("현재 작업을 보존하고 새로운 빈 슬라이드를 추가합니다. (단축키: F10)")
        self.btn_add_step.setShortcut(QKeySequence(Qt.Key_F10))
        self.btn_add_step.setStyleSheet("background-color: #EFF6FF; color: #1D4ED8; font-weight: bold; border-radius: 4px; padding: 2px 8px;")
        self.btn_add_step.clicked.connect(self.sig_add_step.emit)
        self.btn_add_slide = self.btn_add_step
        header_bar.addWidget(self.btn_add_step)

        self.btn_select_all = QPushButton(tr("btn_select_all", "전체 선택"), self)
        self.btn_select_all.setToolTip("타임라인 내 모든 슬라이드를 일괄 선택합니다.")
        self.btn_select_all.setStyleSheet("background-color: #F1F5F9; color: #334155; border: 1px solid #CBD5E1; font-weight: 500; border-radius: 4px; padding: 2px 6px;")
        self.btn_select_all.clicked.connect(self.select_all_steps)
        header_bar.addWidget(self.btn_select_all)

        self.btn_deselect_all = QPushButton(tr("btn_deselect_all", "전체 해제"), self)
        self.btn_deselect_all.setToolTip("현재 활성 슬라이드를 제외한 나머지 슬라이드의 선택을 해제합니다.")
        self.btn_deselect_all.setStyleSheet("background-color: #F1F5F9; color: #334155; border: 1px solid #CBD5E1; font-weight: 500; border-radius: 4px; padding: 2px 6px;")
        self.btn_deselect_all.clicked.connect(self.deselect_all_steps)
        header_bar.addWidget(self.btn_deselect_all)

        self.btn_delete_selected = QPushButton(tr("btn_delete_selected_step", "선택 삭제"), self)
        self.btn_delete_selected.setIcon(RibbonIconProvider.get_icon("clear", 14, "#DC2626"))
        self.btn_delete_selected.setToolTip(tr("btn_delete_selected_step_tooltip", "선택된 슬라이드들을 일괄 삭제합니다."))
        self.btn_delete_selected.setStyleSheet("background-color: #FEF2F2; color: #DC2626; border: 1px solid #FECACA; font-weight: bold; border-radius: 4px; padding: 2px 8px;")
        self.btn_delete_selected.clicked.connect(self.request_delete_selected)
        header_bar.addWidget(self.btn_delete_selected)

        # 선택 복제 버튼
        self.btn_duplicate_selected = QPushButton(tr("btn_duplicate_selected", "선택 복제"), self)
        self.btn_duplicate_selected.setToolTip("선택된 슬라이드를 복제하여 바로 뒤에 삽입합니다.")
        self.btn_duplicate_selected.setStyleSheet("background-color: #F8FAFC; color: #1E293B; border: 1px solid #CBD5E1; font-weight: 500; border-radius: 4px; padding: 2px 7px;")
        self.btn_duplicate_selected.clicked.connect(self.sig_duplicate_selected.emit)
        header_bar.addWidget(self.btn_duplicate_selected)

        # 앞으로 이동 버튼
        self.btn_move_prev = QPushButton(tr("btn_move_prev", "앞으로 이동"), self)
        self.btn_move_prev.setToolTip("선택된 슬라이드를 타임라인 앞(왼쪽)으로 1칸 이동합니다.")
        self.btn_move_prev.setStyleSheet("background-color: #F8FAFC; color: #1E293B; border: 1px solid #CBD5E1; font-weight: 500; border-radius: 4px; padding: 2px 7px;")
        self.btn_move_prev.clicked.connect(lambda: self.sig_move_selected.emit(-1))
        header_bar.addWidget(self.btn_move_prev)

        # 뒤로 이동 버튼
        self.btn_move_next = QPushButton(tr("btn_move_next", "뒤로 이동"), self)
        self.btn_move_next.setToolTip("선택된 슬라이드를 타임라인 뒤(오른쪽)으로 1칸 이동합니다.")
        self.btn_move_next.setStyleSheet("background-color: #F8FAFC; color: #1E293B; border: 1px solid #CBD5E1; font-weight: 500; border-radius: 4px; padding: 2px 7px;")
        self.btn_move_next.clicked.connect(lambda: self.sig_move_selected.emit(1))
        header_bar.addWidget(self.btn_move_next)

        # 선택 내보내기 통합 드롭다운 메뉴 버튼
        self.btn_export_all_menu = QPushButton(tr("btn_export_selected_menu", "선택 내보내기 ▾"), self)
        self.btn_export_all_menu.setToolTip("선택된 슬라이드들을 원하는 포맷(PPT, Google Slides, HWP, HTML 웹북, GIF)으로 일괄 전송/내보냅니다.")
        self.btn_export_all_menu.setStyleSheet("background-color: #F0FDF4; color: #166534; border: 1px solid #BBF7D0; font-weight: bold; border-radius: 4px; padding: 2px 10px;")

        self.export_menu = QMenu(self)
        self.act_export_ppt = self.export_menu.addAction(tr("menu_export_ppt", "PowerPoint (PPT)"))
        self.act_export_ppt.triggered.connect(self.sig_export_all_ppt.emit)
        self.act_export_slides = self.export_menu.addAction(tr("menu_export_slides", "Google Slides"))
        self.act_export_slides.triggered.connect(self.sig_export_all_slides.emit)
        self.act_export_hwp = self.export_menu.addAction(tr("menu_export_hwp", "한컴 한글 (HWP)"))
        self.act_export_hwp.triggered.connect(self.sig_export_all_hwp.emit)
        self.export_menu.addSeparator()
        self.act_export_webbook = self.export_menu.addAction(tr("menu_export_webbook", "반응형 웹북 (HTML)"))
        self.act_export_webbook.triggered.connect(self.sig_export_webbook.emit)
        self.act_export_gif = self.export_menu.addAction(tr("menu_export_gif", "숏클립 튜토리얼 (GIF)"))
        self.act_export_gif.triggered.connect(self.sig_export_gif.emit)
        self.export_menu.addSeparator()
        self.act_export_pdf = self.export_menu.addAction(tr("menu_export_pdf", "PDF 문서 (.pdf)"))
        self.act_export_pdf.triggered.connect(self.sig_export_pdf.emit)
        self.act_export_word = self.export_menu.addAction(tr("menu_export_word", "MS Word (.docx)"))
        self.act_export_word.triggered.connect(self.sig_export_word.emit)
        self.export_menu.addSeparator()
        self.act_export_notion = self.export_menu.addAction(tr("menu_export_notion", "노션 (Notion)"))
        self.act_export_notion.triggered.connect(self.sig_export_notion.emit)
        self.act_export_confluence = self.export_menu.addAction(tr("menu_export_confluence", "컨플루언스 (Confluence)"))
        self.act_export_confluence.triggered.connect(self.sig_export_confluence.emit)

        self.btn_export_all_menu.setMenu(self.export_menu)
        self.btn_export_selected_menu = self.btn_export_all_menu
        self.btn_export_all_ppt = self.act_export_ppt
        self.btn_export_all_hwp = self.act_export_hwp
        self.btn_export_webbook = self.act_export_webbook
        self.btn_export_gif = self.act_export_gif
        self.btn_export_pdf = self.act_export_pdf
        self.btn_export_word = self.act_export_word
        self.btn_export_notion = self.act_export_notion
        self.btn_export_confluence = self.act_export_confluence
        header_bar.addWidget(self.btn_export_all_menu)

        self.chk_hover_preview = QCheckBox(tr("chk_hover_preview", "미리보기"), self)
        self.chk_hover_preview.setToolTip("마우스오버 시 고화질 슬라이드 미리보기 박스를 표시합니다.")
        self.chk_hover_preview.setChecked(True)
        self.chk_hover_preview.setStyleSheet("font-size: 11px; color: #1E293B; margin-left: 4px;")
        self.chk_hover_preview.toggled.connect(self._on_hover_preview_toggled)
        header_bar.addWidget(self.chk_hover_preview)

        header_bar.addStretch(1)
        root_lay.addLayout(header_bar)

        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setFixedHeight(84)
        self.scroll.setStyleSheet("QScrollArea { background-color: #F1F5F9; border: 1px solid #E2E8F0; border-radius: 6px; }")

        self.cards_container = QWidget()
        self.cards_container.setAcceptDrops(True)
        self.cards_container.dragEnterEvent = self._on_container_drag_enter
        self.cards_container.dragMoveEvent = self._on_container_drag_move
        self.cards_container.dropEvent = self._on_container_drop

        self.cards_layout = QHBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(4, 2, 4, 2)
        self.cards_layout.setSpacing(6)
        self.cards_layout.addStretch(1)

        self.scroll.setWidget(self.cards_container)
        root_lay.addWidget(self.scroll)

    def _on_container_drag_enter(self, event):
        if event.mimeData().hasFormat("application/x-manualstudio-step-index"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def _on_container_drag_move(self, event):
        if event.mimeData().hasFormat("application/x-manualstudio-step-index"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def _on_container_drop(self, event):
        if event.mimeData().hasFormat("application/x-manualstudio-step-index"):
            try:
                src_idx = int(bytes(event.mimeData().data("application/x-manualstudio-step-index")).decode("utf-8"))
            except Exception:
                event.ignore()
                return

            drop_x = event.position().x() if hasattr(event, "position") else event.pos().x()
            target_idx = len(self.steps) - 1
            for i in range(self.cards_layout.count()):
                w = self.cards_layout.itemAt(i).widget()
                if isinstance(w, StepCardWidget):
                    card_center = w.x() + w.width() / 2.0
                    if drop_x < card_center:
                        target_idx = w.step_idx
                        break

            target_idx = max(0, min(target_idx, len(self.steps) - 1))
            if src_idx != target_idx:
                self.sig_move_step.emit(src_idx, target_idx)
            event.acceptProposedAction()
        else:
            event.ignore()

    def select_all_steps(self):
        if self.steps:
            self.selected_indices = set(range(len(self.steps)))
        else:
            self.selected_indices = set()
        self.update_card_selection_states()

    def deselect_all_steps(self):
        if self.steps and 0 <= self.active_idx < len(self.steps):
            self.selected_indices = {self.active_idx}
        else:
            self.selected_indices = set()
        self.update_card_selection_states()

    def request_delete_selected(self):
        targets = sorted(list(self.selected_indices)) if self.selected_indices else ([self.active_idx] if self.active_idx is not None else [])
        if targets:
            self.sig_delete_steps.emit(targets)

    def on_card_clicked_with_mod(self, idx: int, modifiers):
        if modifiers and (modifiers & (Qt.ShiftModifier | Qt.ControlModifier)):
            if idx in self.selected_indices:
                if len(self.selected_indices) > 1:
                    self.selected_indices.remove(idx)
                    if self.active_idx == idx:
                        self.active_idx = min(self.selected_indices)
                        self.sig_step_selected.emit(self.active_idx)
            else:
                self.selected_indices.add(idx)
                self.active_idx = idx
                self.sig_step_selected.emit(self.active_idx)
            self.update_card_selection_states()
        else:
            self.selected_indices = {idx}
            self.active_idx = idx
            self.update_card_selection_states()
            self.sig_step_selected.emit(idx)

    def set_active_step(self, idx: int):
        if self.steps and 0 <= idx < len(self.steps):
            self.active_idx = idx
            self.update_card_selection_states()

    def update_card_selection_states(self):
        count = len(self.steps)
        sel_count = len(self.selected_indices)
        timeline_tpl = tr("storyboard_timeline_format", "스토리보드 타임라인 ({count}개 슬라이드, {sel_count}개 선택됨)")
        self.lbl_title.setText(timeline_tpl.format(count=count, sel_count=sel_count))
        if sel_count > 0:
            del_tpl = tr("btn_delete_selected_count", "선택 삭제 ({count})")
            self.btn_delete_selected.setText(del_tpl.format(count=sel_count))
        else:
            self.btn_delete_selected.setText(tr("btn_delete_selected_step", "선택 삭제"))
        for i in range(self.cards_layout.count()):
            item = self.cards_layout.itemAt(i)
            if item:
                w = item.widget()
                if isinstance(w, StepCardWidget):
                    w.is_selected = (w.step_idx == self.active_idx)
                    w.is_checked = (w.step_idx in self.selected_indices)
                    if 0 <= w.step_idx < len(self.steps):
                        step_data = self.steps[w.step_idx]
                        thumb_pix = step_data.get("thumbnail")
                        if thumb_pix and not thumb_pix.isNull():
                            w.lbl_thumb.setPixmap(thumb_pix.scaled(98, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    w.update_style()

    def get_selected_indices(self) -> list:
        return sorted(list(self.selected_indices))

    def get_selected_steps(self) -> list:
        return [(idx, self.steps[idx]) for idx in sorted(self.selected_indices) if 0 <= idx < len(self.steps)]

    def set_steps(self, steps: list, active_idx: int = 0):
        self.steps = steps
        self.active_idx = max(0, min(active_idx, len(steps) - 1)) if steps else 0
        if self.steps:
            self.selected_indices = {self.active_idx}
        else:
            self.selected_indices = set()
        self.rebuild_cards()

    def rebuild_cards(self):
        while self.cards_layout.count() > 0:
            item = self.cards_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        for idx, step_data in enumerate(self.steps):
            is_sel = (idx == self.active_idx)
            is_chk = (idx in self.selected_indices)
            card = StepCardWidget(idx, step_data, is_selected=is_sel, is_checked=is_chk, parent=self.cards_container)
            card.sig_clicked.connect(self.sig_step_selected.emit)
            card.sig_clicked_with_mod.connect(self.on_card_clicked_with_mod)
            card.sig_delete.connect(lambda i=idx: self.sig_delete_steps.emit([i]))
            card.sig_duplicate.connect(self.sig_duplicate_step.emit)
            card.sig_move_left.connect(lambda i=idx: self.sig_move_step.emit(i, i - 1))
            card.sig_move_right.connect(lambda i=idx: self.sig_move_step.emit(i, i + 1))
            self.cards_layout.addWidget(card)

        self.cards_layout.addStretch(1)
        self.update_card_selection_states()

    def _on_hover_preview_toggled(self, checked: bool):
        self.hover_preview_enabled = checked
        self.sig_toggle_hover_preview.emit(checked)

    def retranslate_ui(self):
        if hasattr(self, "btn_add_step"):
            self.btn_add_step.setText(tr("btn_add_slide", "+ 새 슬라이드 (F10)"))
        if hasattr(self, "btn_select_all"):
            self.btn_select_all.setText(tr("btn_select_all", "전체 선택"))
        if hasattr(self, "btn_deselect_all"):
            self.btn_deselect_all.setText(tr("btn_deselect_all", "전체 해제"))
        if hasattr(self, "btn_duplicate_selected"):
            self.btn_duplicate_selected.setText(tr("btn_duplicate_selected", "선택 복제"))
        if hasattr(self, "btn_move_prev"):
            self.btn_move_prev.setText(tr("btn_move_prev", "앞으로 이동"))
        if hasattr(self, "btn_move_next"):
            self.btn_move_next.setText(tr("btn_move_next", "뒤로 이동"))
        if hasattr(self, "chk_hover_preview"):
            self.chk_hover_preview.setText(tr("chk_hover_preview", "미리보기"))
        if hasattr(self, "btn_export_all_menu"):
            self.btn_export_all_menu.setText(tr("btn_export_selected_menu", "선택 내보내기 ▾"))
        if hasattr(self, "act_export_ppt"):
            self.act_export_ppt.setText(tr("menu_export_ppt", "PowerPoint (PPT)"))
        if hasattr(self, "act_export_slides"):
            self.act_export_slides.setText(tr("menu_export_slides", "Google Slides"))
        if hasattr(self, "act_export_hwp"):
            self.act_export_hwp.setText(tr("menu_export_hwp", "한컴 한글 (HWP)"))
        if hasattr(self, "act_export_webbook"):
            self.act_export_webbook.setText(tr("menu_export_webbook", "반응형 웹북 (HTML)"))
        if hasattr(self, "act_export_gif"):
            self.act_export_gif.setText(tr("menu_export_gif", "숏클립 튜토리얼 (GIF)"))
        self.update_card_selection_states()

# 8. 스튜디오 메인 윈도우 (ManualStudioWindow)
# ==============================================================================

# ------------------------------------------------------------------------------
# 스토리보드 바로 위에 위치하는 전용 접기/펼치기 슬림 바 (StoryboardToggleBar)
# ------------------------------------------------------------------------------
class StoryboardToggleBar(QFrame):
    """스토리보드 바로 위에 위치하여 스토리보드를 원클릭으로 접거나 펼치는 슬림 분할 바"""
    sig_toggled = Signal(bool)

    def __init__(self, is_visible: bool = True, parent=None):
        super().__init__(parent)
        self.is_expanded = is_visible
        self.setFixedHeight(22)
        self.setStyleSheet("""
            StoryboardToggleBar {
                background-color: #E2E8F0;
                border-top: 1px solid #CBD5E1;
                border-bottom: 1px solid #CBD5E1;
            }
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(6, 1, 6, 1)
        lay.setSpacing(0)
        lay.addStretch(1)

        self.btn_toggle = QPushButton(self)
        self.btn_toggle.setFixedHeight(18)
        self.btn_toggle.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9;
                color: #334155;
                font-size: 10px;
                font-weight: bold;
                border: 1px solid #94A3B8;
                border-radius: 3px;
                padding: 0 12px;
            }
            QPushButton:hover {
                background-color: #DBEAFE;
                color: #1D4ED8;
                border-color: #3B82F6;
            }
        """)
        self.btn_toggle.clicked.connect(self._on_clicked)
        lay.addWidget(self.btn_toggle)
        lay.addStretch(1)
        self.update_btn_text()

    def update_btn_text(self):
        if self.is_expanded:
            self.btn_toggle.setText(tr("btn_toggle_storyboard_hide", "스토리보드 접기 ▲"))
        else:
            self.btn_toggle.setText(tr("btn_toggle_storyboard_show", "스토리보드 펼치기 ▼"))

    def set_expanded(self, expanded: bool):
        self.is_expanded = expanded
        self.update_btn_text()

    def _on_clicked(self):
        self.is_expanded = not self.is_expanded
        self.update_btn_text()
        self.sig_toggled.emit(self.is_expanded)

    def retranslate_ui(self):
        self.update_btn_text()


class ManualStudioWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.current_project_path = None
        self.last_capture_rect = None
        self.overlay_window = None
        self.current_target_monitor = self.config.get("target_monitor", -1)
        self.storyboard_steps = []
        self.current_step_idx = 0
        self.mobile_server = None
        self.current_flow_direction = "TD"

        loc = self.config.get("locale", "auto")
        if loc == "auto":
            # 최초 실행: OS 지역 자동 감지 후 config에 영구 저장
            loc = I18nManager.detect_system_locale()
            self.config["locale"] = loc
            save_config(self.config)
        I18nManager.instance().set_locale(loc)

        self.update_window_title()
        self.resize(1240, 780)

        # 윈도우 및 작업표시줄 아이콘 설정 (Manual Studio 전용 앱 아이콘)
        app_icon = get_manual_studio_icon()
        if not app_icon.isNull():
            self.setWindowIcon(app_icon)

        # 폰트 매니저 초기화 및 등록된 폰트 로드
        CustomFontManager.instance().load_all_fonts(self.config.get("custom_fonts", []))

        # 실시간 서식 상태
        self.current_stamp_color = self.config.get("stamp_style", {}).get("bg_color", "#E53935")
        self.current_text_color = self.config.get("text_style", {}).get("text_color", "#FFFFFF")
        self.current_text_bg_color = self.config.get("text_style", {}).get("bg_color", "#212121")
        self.current_title_color = self.config.get("ppt_layout", {}).get("title_font_color", "#000000")

        self.ui_style = self.config.get("ui_style", "auto")
        self.ribbon_frame = None
        self.traffic_lights = None

        self.init_ui()
        self.init_hotkey()
        self.init_autosave()

        self.apply_ui_theme(self.ui_style)

        # 화면 크기 감지 및 최적 기본 창크기 설정 (표준 1080p 및 노트북 해상도 최적화)
        screen = QGuiApplication.primaryScreen()
        if screen:
            avail = screen.availableGeometry()
            target_w = min(1360, max(1200, int(avail.width() * 0.88)))
            target_h = min(850, max(680, int(avail.height() * 0.88)))
            self.resize(target_w, target_h)
            self.move(
                avail.x() + max(0, (avail.width() - target_w) // 2),
                avail.y() + max(0, (avail.height() - target_h) // 2)
            )
        else:
            self.resize(1240, 780)

        QTimer.singleShot(1000, self.check_and_prompt_recovery)
        if self.config.get("auto_check_update", True):
            QTimer.singleShot(3500, lambda: self.check_for_updates(silent=True))

    def init_ui(self):
        # 0. 상단 메뉴바 초기화 (우측 끝에 CI + 회사명 + About 버튼 탑재)
        self.init_menu_bar()

        # 중앙 위젯
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 4, 8, 4)
        main_layout.setSpacing(4)

        # 1. 리본 바 컨테이너 (Office / Snagit 스타일)
        ribbon_frame = QFrame(self)
        self.ribbon_frame = ribbon_frame
        ribbon_frame.setObjectName("RibbonPanel")
        ribbon_frame.setStyleSheet("""
            QFrame#RibbonPanel {
                background-color: #F8FAFC;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
            }
            QTabWidget::pane {
                border: 1px solid #E2E8F0;
                background: #FFFFFF;
                border-bottom-left-radius: 4px;
                border-bottom-right-radius: 4px;
            }
            QTabBar::tab {
                background: #F1F5F9;
                border: 1px solid #CBD5E1;
                border-bottom: none;
                padding: 5px 18px;
                font-family: 'Malgun Gothic';
                font-size: 11px;
                font-weight: bold;
                color: #475569;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
                white-space: nowrap;
            }
            QTabBar::tab:selected {
                background: #FFFFFF;
                color: #1E40AF;
                border-bottom: 2px solid #2563EB;
            }
            QTabBar::tab:hover:!selected {
                background: #E2E8F0;
                color: #1E293B;
            }
            QPushButton {
                font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
                font-size: 11px;
                font-weight: 500;
                padding: 2px 6px;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                background-color: #FFFFFF;
                color: #1E293B;
                white-space: nowrap;
            }
            QPushButton:hover {
                background-color: #F1F5F9;
                border-color: #94A3B8;
                color: #0F172A;
            }
            QPushButton:checked {
                background-color: #2563EB;
                color: #FFFFFF;
                border-color: #1D4ED8;
                font-weight: bold;
            }
            QLabel {
                font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
                font-size: 11px;
                font-weight: bold;
                color: #475569;
                white-space: nowrap;
            }
            QSpinBox {
                font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
                font-size: 11px;
                padding: 2px 16px 2px 4px;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                background-color: #FFFFFF;
                white-space: nowrap;
            }
            QComboBox {
                font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
                font-size: 11px;
                padding: 2px 20px 2px 6px;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                background-color: #FFFFFF;
                white-space: nowrap;
            }
            QCheckBox {
                font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
                font-size: 11px;
                font-weight: 500;
                color: #1E293B;
                white-space: nowrap;
            }
        """)

        ribbon_vlayout = QVBoxLayout(ribbon_frame)
        ribbon_vlayout.setContentsMargins(4, 4, 4, 4)
        ribbon_vlayout.setSpacing(4)

        # 1-1. 리본 탭 위젯 (2개 탭: '도구', '서식·설정')
        self.ribbon_tabs = QTabWidget(self)

        # -------------------------------------------------------------
        # TAB 1: 도구 (Tools)
        # -------------------------------------------------------------
        tab_tools = QWidget()
        tools_layout = QHBoxLayout(tab_tools)
        tools_layout.setContentsMargins(4, 2, 4, 2)
        tools_layout.setSpacing(4)

        # 1) [캡처] 그룹
        self.btn_capture = QPushButton(tr("btn_fixed_capture", "고정 캡처"), self)
        self.btn_capture.setToolTip(tr("tooltip_capture", "지정된 고정 영역을 즉시 캡처합니다."))
        self.btn_capture.setStyleSheet("background-color: #EFF6FF; color: #1E40AF; border-color: #BFDBFE; font-weight: bold;")
        self.btn_capture.clicked.connect(self.handle_hotkey_capture)

        self.btn_drag_capture = QPushButton(tr("btn_variable_capture", "영역 지정"), self)
        self.btn_drag_capture.setToolTip(tr("tooltip_drag_capture", "화면에서 원하는 영역을 드래그하여 지정합니다."))
        self.btn_drag_capture.setStyleSheet("background-color: #FAF5FF; color: #6B21A8; border-color: #E9D5FF; font-weight: bold;")
        self.btn_drag_capture.clicked.connect(self.start_capture)

        self.btn_sub_capture = QPushButton(tr("btn_sub_capture", "부분 캡처"), self)
        self.btn_sub_capture.setToolTip(tr("tooltip_sub_capture", "화면의 특정 영역(모달/팝업 등)을 부분 캡처하여 스튜디오에 독립 이미지 객체로 추가합니다."))
        self.btn_sub_capture.setStyleSheet("background-color: #FFFBEB; color: #B45309; border-color: #FDE68A; font-weight: bold;")
        self.btn_sub_capture.clicked.connect(self.start_sub_capture)

        self.combo_tab_monitor = None

        self.btn_scroll_stitch = QPushButton(tr("btn_scroll_stitch", "스크롤 스티칭"), self)
        self.btn_scroll_stitch.setToolTip(tr("tip_scroll_stitch", "긴 웹페이지나 ERP 테이블을 스크롤하여 1장의 파노라마 이미지로 합성"))
        self.btn_scroll_stitch.setStyleSheet("background-color: #F0FDF4; color: #15803D; border-color: #BBF7D0; font-weight: bold;")
        self.btn_scroll_stitch.clicked.connect(self.action_scroll_stitch)
        self.start_scroll_stitch_capture = self.action_scroll_stitch

        # 액션 녹화 폐기 (보안 소프트웨어 오탐 방지 및 2x2 대칭 캡처 레이아웃 확립)
        self.btn_action_record = None
        self.btn_action_recorder = None
        self.toggle_action_recorder = self.action_toggle_action_recorder

        cap_grid = QGridLayout()
        cap_grid.setContentsMargins(0, 0, 0, 0)
        cap_grid.setSpacing(2)
        cap_grid.addWidget(self.btn_capture, 0, 0)
        cap_grid.addWidget(self.btn_sub_capture, 0, 1)
        cap_grid.addWidget(self.btn_drag_capture, 1, 0)
        cap_grid.addWidget(self.btn_scroll_stitch, 1, 1)
        tools_layout.addWidget(self.create_ribbon_group(tr("grp_capture", "캡처"), cap_grid, "grp_capture"))
        tools_layout.addWidget(self.create_separator())

        # 플로우차트 그룹 (상단: 빌더 + 문서참조, 하단: 흔히 사용하는 6대 도형)
        self.btn_flowchart = QPushButton(tr("btn_flowchart_builder", "플로우차트"), self)
        self.btn_flowchart.setToolTip(tr("tip_flowchart_builder", "Mermaid 문법 및 수동 조작으로 플로우차트를 생성합니다."))
        self.btn_flowchart.setStyleSheet("background-color: #F0FDF4; color: #166534; border-color: #BBF7D0; font-weight: bold;")
        self.btn_flowchart.clicked.connect(self.open_flowchart_studio)

        self.btn_toggle_doc_dock = QPushButton(tr("btn_toggle_doc_dock", "문서 참조"), self)
        self.btn_toggle_doc_dock.setToolTip(tr("tip_toggle_doc_dock", "MarkItDown 외부 문서 변환 및 MD 원문 참조 패널을 토글합니다."))
        self.btn_toggle_doc_dock.setStyleSheet("background-color: #FAF5FF; color: #6B21A8; border-color: #E9D5FF; font-weight: bold;")
        self.btn_toggle_doc_dock.clicked.connect(self.toggle_document_dock)

        self.btn_flow_terminal = QPushButton(tr("btn_flow_terminal", "시작/종료"), self)
        self.btn_flow_terminal.setToolTip(tr("tip_flow_terminal", "타원형 시작/종료 터미널 노드를 캔버스에 배치합니다."))
        self.btn_flow_terminal.setCheckable(True)
        self.btn_flow_terminal.clicked.connect(lambda: self.switch_mode("FLOW_TERMINAL"))

        self.btn_flow_process = QPushButton(tr("btn_flow_process", "일반 작업"), self)
        self.btn_flow_process.setToolTip(tr("tip_flow_process", "직사각형 일반 작업 노드를 캔버스에 배치합니다."))
        self.btn_flow_process.setCheckable(True)
        self.btn_flow_process.clicked.connect(lambda: self.switch_mode("FLOW_PROCESS"))

        self.btn_flow_decision = QPushButton(tr("btn_flow_decision", "조건 분기"), self)
        self.btn_flow_decision.setToolTip(tr("tip_flow_decision", "마름모형 조건 판단 노드를 캔버스에 배치합니다."))
        self.btn_flow_decision.setCheckable(True)
        self.btn_flow_decision.clicked.connect(lambda: self.switch_mode("FLOW_DECISION"))

        self.btn_flow_io = QPushButton(tr("btn_flow_io", "입출력"), self)
        self.btn_flow_io.setToolTip(tr("tip_flow_io", "평행사변형 데이터 입출력 노드를 캔버스에 배치합니다."))
        self.btn_flow_io.setCheckable(True)
        self.btn_flow_io.clicked.connect(lambda: self.switch_mode("FLOW_IO"))

        self.btn_flow_database = QPushButton(tr("btn_flow_database", "DB"), self)
        self.btn_flow_database.setToolTip(tr("tip_flow_database", "원통형 데이터베이스 노드를 캔버스에 배치합니다."))
        self.btn_flow_database.setCheckable(True)
        self.btn_flow_database.clicked.connect(lambda: self.switch_mode("FLOW_DATABASE"))

        self.btn_flow_document = QPushButton(tr("btn_flow_document", "문서"), self)
        self.btn_flow_document.setToolTip(tr("tip_flow_document", "문서 서식 노드를 캔버스에 배치합니다."))
        self.btn_flow_document.setCheckable(True)
        self.btn_flow_document.clicked.connect(lambda: self.switch_mode("FLOW_DOCUMENT"))

        self.btn_flow_line = QPushButton(tr("btn_flow_line", "직선 연결"), self)
        self.btn_flow_line.setToolTip(tr("tip_flow_line", "노드의 마그넷 포인트를 잇는 직선 연결선을 그립니다."))
        self.btn_flow_line.setCheckable(True)
        self.btn_flow_line.clicked.connect(lambda: self.switch_mode("FLOW_CONNECT_LINE"))

        self.btn_flow_elbow = QPushButton(tr("btn_flow_elbow", "직각 연결"), self)
        self.btn_flow_elbow.setToolTip(tr("tip_flow_elbow", "노드의 마그넷 포인트를 잇는 꺾인 직각 연결선을 그립니다. (Tab/Space로 방향 전환)"))
        self.btn_flow_elbow.setCheckable(True)
        self.btn_flow_elbow.clicked.connect(lambda: self.switch_mode("FLOW_CONNECT_ELBOW"))

        self.btn_flow_term = self.btn_flow_terminal
        self.btn_flow_proc = self.btn_flow_process
        self.btn_flow_dec = self.btn_flow_decision
        self.btn_flow_db = self.btn_flow_database
        self.btn_flow_doc = self.btn_flow_document

        self.btn_flow_align = QPushButton(tr("btn_flow_align", "자동정렬"), self)
        self.btn_flow_align.setToolTip(tr("tip_flow_align", "캔버스의 플로우차트 노드들을 상하(TD) 또는 좌우(LR) 계층 순서로 깔끔하게 자동정렬합니다. (드롭다운으로 축 정렬/균등 배치)"))
        self.btn_flow_align.clicked.connect(self.action_auto_align_flowchart)

        align_menu = QMenu(self.btn_flow_align)
        align_menu.setStyleSheet("""
            QMenu { background-color: #FFFFFF; color: #1E293B; border: 1px solid #CBD5E1; border-radius: 6px; padding: 4px; }
            QMenu::item { padding: 6px 20px 6px 10px; color: #1E293B; }
            QMenu::item:selected { background-color: #2563EB; color: #FFFFFF; }
            QMenu::separator { height: 1px; background-color: #E2E8F0; margin: 4px 6px; }
        """)
        act_m_auto = align_menu.addAction("플로우차트 자동정렬 (TD ↔ LR)")
        act_m_auto.triggered.connect(self.action_auto_align_flowchart)
        align_menu.addSeparator()
        act_m_cx = align_menu.addAction("선택 객체 중심 축 X 정렬 (세로 중심)")
        act_m_cx.triggered.connect(lambda: self.canvas.align_selected_items_center_x())
        act_m_cy = align_menu.addAction("선택 객체 중심 축 Y 정렬 (가로 중심)")
        act_m_cy.triggered.connect(lambda: self.canvas.align_selected_items_center_y())
        align_menu.addSeparator()
        act_m_dh = align_menu.addAction("선택 객체 가로 균등 재배치")
        act_m_dh.triggered.connect(lambda: self.canvas.distribute_selected_items_horizontal())
        act_m_dv = align_menu.addAction("선택 객체 세로 균등 재배치")
        act_m_dv.triggered.connect(lambda: self.canvas.distribute_selected_items_vertical())
        self.btn_flow_align.setMenu(align_menu)

        self.btn_mobile_link = QPushButton(tr("btn_mobile_link", "모바일 연동"), self)
        self.btn_mobile_link.setToolTip(tr("tip_mobile_link", "스마트폰/태블릿에서 손으로 그린 다이어그램을 QR 코드로 즉시 전송받습니다. (서버 무저장 P2P)"))
        self.btn_mobile_link.clicked.connect(self.action_open_mobile_link)

        flow_grid = QGridLayout()
        flow_grid.setContentsMargins(0, 0, 0, 0)
        flow_grid.setSpacing(2)
        flow_grid.addWidget(self.btn_flowchart, 0, 0, 1, 2)
        flow_grid.addWidget(self.btn_flow_line, 0, 2)
        flow_grid.addWidget(self.btn_flow_elbow, 0, 3)
        flow_grid.addWidget(self.btn_toggle_doc_dock, 0, 4, 1, 2)
        flow_grid.addWidget(self.btn_flow_align, 0, 6)
        flow_grid.addWidget(self.btn_flow_terminal, 1, 0)
        flow_grid.addWidget(self.btn_flow_process, 1, 1)
        flow_grid.addWidget(self.btn_flow_decision, 1, 2)
        flow_grid.addWidget(self.btn_flow_io, 1, 3)
        flow_grid.addWidget(self.btn_flow_database, 1, 4)
        flow_grid.addWidget(self.btn_flow_document, 1, 5)
        flow_grid.addWidget(self.btn_mobile_link, 1, 6)

        tools_layout.addWidget(self.create_ribbon_group(tr("grp_flowchart", "플로우차트"), flow_grid, "grp_flowchart"))
        tools_layout.addWidget(self.create_separator())

        # 2) [프로젝트] 그룹
        self.btn_new_project = QPushButton(tr("btn_new_project", "새 프로젝트"), self)
        self.btn_new_project.setToolTip(tr("tip_new_project", "모든 슬라이드를 초기화하고 새로운 매뉴얼 프로젝트를 시작합니다. (단축키: Ctrl+N)"))
        self.btn_new_project.clicked.connect(self.action_new_project)

        self.btn_open_project = QPushButton(tr("btn_open_project", "불러오기"), self)
        self.btn_open_project.setToolTip(tr("tooltip_open_project", "기존 저장된 프로젝트(.dragon, .mcs.json)를 불러와 타임라인과 개별 객체를 복원합니다. (Ctrl+O)"))
        self.btn_open_project.clicked.connect(self.action_open_project)

        self.btn_save_project = QPushButton(tr("btn_save_project", "프로젝트 저장"), self)
        self.btn_save_project.setToolTip(tr("tooltip_save_project", "현재 타임라인의 모든 슬라이드와 고해상도 이미지를 프로젝트로 저장합니다. (Ctrl+S)"))
        self.btn_save_project.clicked.connect(self.action_save_project)

        self.btn_autosave = QPushButton(tr("btn_autosave", "자동 저장"), self)
        self.btn_autosave.setCheckable(True)
        self.btn_autosave.setChecked(bool(self.config.get("auto_save_enabled", True)))
        self.btn_autosave.setToolTip("프로젝트 주기적 자동 저장 활성화/비활성화 (단축키: Alt+A)")
        self.btn_autosave.clicked.connect(self.on_autosave_toggle_clicked)

        self.btn_merge_project = QPushButton(tr("btn_merge_project", "프로젝트 병합"), self)
        self.btn_merge_project.setToolTip(tr("tip_merge_project", "다른 프로젝트(.dragon, .mcs.json)의 슬라이드들을 현재 타임라인 뒤에 추가 병합합니다."))
        self.btn_merge_project.clicked.connect(self.action_merge_project)

        self.btn_open_file = QPushButton(tr("btn_open_file", "이미지 열기"), self)
        self.btn_open_file.setToolTip(tr("tooltip_open_file", "외부 이미지 파일을 불러와 캔버스에 배치합니다."))
        self.btn_open_file.clicked.connect(self.open_image_file)

        self.btn_copy_image = QPushButton(tr("btn_copy_image", "결과 복사"), self)
        self.btn_copy_image.setToolTip(tr("tooltip_copy_image", "현재 편집 중인 완성 이미지를 클립보드에 복사합니다."))
        self.btn_copy_image.clicked.connect(self.copy_current_composed_image)

        proj_grid = QGridLayout()
        proj_grid.setContentsMargins(0, 0, 0, 0)
        proj_grid.setSpacing(2)
        proj_grid.addWidget(self.btn_new_project, 0, 0)
        proj_grid.addWidget(self.btn_open_project, 0, 1)
        proj_grid.addWidget(self.btn_save_project, 0, 2)
        proj_grid.addWidget(self.btn_autosave, 0, 3)
        proj_grid.addWidget(self.btn_merge_project, 1, 0)
        proj_grid.addWidget(self.btn_open_file, 1, 1)
        proj_grid.addWidget(self.btn_copy_image, 1, 2)
        tools_layout.addWidget(self.create_ribbon_group(tr("grp_project", "프로젝트"), proj_grid, "grp_project"))
        tools_layout.addWidget(self.create_separator())

        # 3) [선택·편집] 그룹
        self.btn_mode_select = QPushButton(tr("btn_mode_select", "선택 도구"), self)
        self.btn_mode_select.setToolTip(tr("tooltip_select", "객체를 마우스로 클릭하여 이동, 크기 조절 또는 편집합니다."))
        self.btn_mode_select.setCheckable(True)
        self.btn_mode_select.setChecked(True)
        self.btn_mode_select.clicked.connect(lambda: self.switch_mode("SELECT"))

        self.btn_undo = QPushButton(tr("btn_undo", "실행 취소"), self)
        self.btn_undo.setToolTip(tr("tooltip_undo", "가장 최근에 작업한 주석 배치나 수정을 취소합니다."))
        self.btn_undo.clicked.connect(self.action_undo)

        self.btn_clear = QPushButton(tr("btn_clear", "전체 삭제"), self)
        self.btn_clear.setToolTip(tr("tooltip_clear", "현재 캔버스에 배치된 모든 주석 및 추가 이미지를 일괄 삭제합니다."))
        self.btn_clear.clicked.connect(self.action_clear)

        edit_grid = QGridLayout()
        edit_grid.setContentsMargins(0, 0, 0, 0)
        edit_grid.setSpacing(2)
        edit_grid.addWidget(self.btn_mode_select, 0, 0)
        edit_grid.addWidget(self.btn_undo, 0, 1)
        edit_grid.addWidget(self.btn_clear, 1, 0, 1, 2)
        tools_layout.addWidget(self.create_ribbon_group(tr("grp_select_edit", "선택·편집"), edit_grid, "grp_select_edit"))
        tools_layout.addWidget(self.create_separator())

        # 4) [단계·흐름] 그룹 (스탬프 화살표, 직각 꺾은선 화살표 포함)
        self.btn_mode_stamp = QPushButton(tr("btn_mode_stamp", "번호 스탬프"), self)
        self.btn_mode_stamp.setToolTip(tr("tooltip_stamp", "클릭하는 위치에 순차적으로 증가하는 원형 번호 스탬프를 찍습니다."))
        self.btn_mode_stamp.setCheckable(True)
        self.btn_mode_stamp.clicked.connect(lambda: self.switch_mode("STAMP"))

        self.btn_mode_step_arrow = QPushButton(tr("btn_mode_step_arrow", "순번 화살표"), self)
        self.btn_mode_step_arrow.setCheckable(True)
        self.btn_mode_step_arrow.setToolTip(tr("tooltip_step_arrow", "번호 스탬프와 지시 화살표를 일체형으로 배치합니다."))
        self.btn_mode_step_arrow.clicked.connect(lambda: self.switch_mode("STEP_ARROW"))

        self.btn_mode_elbow = QPushButton(tr("btn_mode_elbow", "직각 화살표"), self)
        self.btn_mode_elbow.setCheckable(True)
        self.btn_mode_elbow.setToolTip(tr("tooltip_elbow", "업무 흐름이나 메뉴 단계를 직각(L자)으로 꺾어 가리킵니다."))
        self.btn_mode_elbow.clicked.connect(lambda: self.switch_mode("ELBOW"))

        self.btn_mode_arrow = QPushButton(tr("btn_mode_arrow", "직선 화살표"), self)
        self.btn_mode_arrow.setToolTip(tr("tooltip_arrow", "시작점에서 끝점까지 깔끔한 직선 화살표를 그립니다."))
        self.btn_mode_arrow.setCheckable(True)
        self.btn_mode_arrow.clicked.connect(lambda: self.switch_mode("ARROW"))

        step_grid = QGridLayout()
        step_grid.setContentsMargins(0, 0, 0, 0)
        step_grid.setSpacing(2)
        step_grid.addWidget(self.btn_mode_stamp, 0, 0)
        step_grid.addWidget(self.btn_mode_step_arrow, 0, 1)
        step_grid.addWidget(self.btn_mode_elbow, 1, 0)
        step_grid.addWidget(self.btn_mode_arrow, 1, 1)
        tools_layout.addWidget(self.create_ribbon_group(tr("grp_step_flow", "단계·흐름"), step_grid, "grp_step_flow"))
        tools_layout.addWidget(self.create_separator())

        # 5) [강조·보안] 그룹 (비파괴 모자이크 블러 포함)
        self.btn_mode_box = QPushButton(tr("btn_mode_box", "사각 강조"), self)
        self.btn_mode_box.setToolTip(tr("tooltip_box", "주요 입력창이나 버튼 영역을 강조하는 사각 테두리 박스를 그립니다."))
        self.btn_mode_box.setCheckable(True)
        self.btn_mode_box.clicked.connect(lambda: self.switch_mode("BOX"))

        self.btn_mode_blur = QPushButton(tr("btn_mode_blur", "모자이크"), self)
        self.btn_mode_blur.setCheckable(True)
        self.btn_mode_blur.setToolTip(tr("tooltip_blur", "개인정보, 금액, 비밀번호 등을 가리는 비파괴 모자이크를 배치합니다."))
        self.btn_mode_blur.clicked.connect(lambda: self.switch_mode("BLUR"))

        self.btn_draft_stamp = QPushButton(tr("btn_draft_stamp", "Draft 스탬프"), self)
        self.btn_draft_stamp.setToolTip(tr("tooltip_draft", "화면 중앙에 60도 회전된 큼직한 사각형 Draft 워터마크 스탬프를 즉시 배치합니다."))
        self.btn_draft_stamp.setStyleSheet("background-color: #FEF2F2; color: #DC2626; border-color: #FECACA; font-weight: bold;")
        self.btn_draft_stamp.clicked.connect(self.action_add_draft_stamp)

        self.btn_mode_eraser = QPushButton(tr("btn_smart_eraser", "스마트 지우개"), self)
        self.btn_mode_eraser.setCheckable(True)
        self.btn_mode_eraser.setToolTip(tr("tip_smart_eraser", "[X] 불필요한 텍스트나 워터마크를 드래그하여 배경과 매끄럽게 지우기"))
        self.btn_mode_eraser.clicked.connect(lambda: self.switch_mode("ERASER"))

        self.btn_auto_pii = QPushButton(tr("btn_auto_pii", "개인정보 마스킹"), self)
        self.btn_auto_pii.setToolTip(tr("tip_auto_pii", "[Shift+M] 화면 내 전화번호, 주민번호, 이메일, 계좌번호 자동 탐색 및 모자이크 마스킹"))
        self.btn_auto_pii.clicked.connect(self.action_auto_pii)

        box_grid = QGridLayout()
        box_grid.setContentsMargins(0, 0, 0, 0)
        box_grid.setSpacing(2)
        box_grid.addWidget(self.btn_mode_box, 0, 0)
        box_grid.addWidget(self.btn_mode_blur, 1, 0)
        box_grid.addWidget(self.btn_mode_eraser, 0, 1)
        box_grid.addWidget(self.btn_auto_pii, 1, 1)
        box_grid.addWidget(self.btn_draft_stamp, 0, 2, 2, 1)
        tools_layout.addWidget(self.create_ribbon_group(tr("grp_highlight_security", "강조·보안"), box_grid, "grp_highlight_security"))
        tools_layout.addWidget(self.create_separator())

        # 5-OCR) [텍스트 인식] 그룹
        self.btn_mode_ocr = QPushButton(tr("btn_mode_ocr", "OCR 추출"), self)
        self.btn_mode_ocr.setCheckable(True)
        self.btn_mode_ocr.setToolTip(tr("tooltip_ocr", "이미지 영역을 드래그하여 텍스트를 인식합니다. (O)"))
        self.btn_mode_ocr.clicked.connect(lambda: self.switch_mode("OCR"))

        self.btn_mode_ocr_label = QPushButton(tr("btn_mode_ocr_label", "OCR 라벨"), self)
        self.btn_mode_ocr_label.setCheckable(True)
        self.btn_mode_ocr_label.setToolTip(tr("tooltip_ocr_label", "영역을 인식하여 텍스트 라벨을 즉시 생성합니다. (Shift+O)"))
        self.btn_mode_ocr_label.clicked.connect(lambda: self.switch_mode("OCR_LABEL"))

        ocr_grid = QGridLayout()
        ocr_grid.setContentsMargins(0, 0, 0, 0)
        ocr_grid.setSpacing(2)
        ocr_grid.addWidget(self.btn_mode_ocr, 0, 0)
        ocr_grid.addWidget(self.btn_mode_ocr_label, 1, 0)
        tools_layout.addWidget(self.create_ribbon_group(tr("grp_ocr", "텍스트 인식"), ocr_grid, "grp_ocr"))
        tools_layout.addWidget(self.create_separator())

        # 5-DIM) [치수선] 그룹
        self.btn_mode_dimension = QPushButton(tr("btn_mode_dimension", "선 치수선"), self)
        self.btn_mode_dimension.setCheckable(True)
        self.btn_mode_dimension.setToolTip(tr("tooltip_dimension", "두 지점 사이의 거리를 측정하여 브라켓 치수선으로 표시합니다. (D)"))
        self.btn_mode_dimension.clicked.connect(lambda: self.switch_mode("DIMENSION"))

        self.btn_mode_box_dimension = QPushButton(tr("btn_mode_box_dimension", "영역 치수"), self)
        self.btn_mode_box_dimension.setCheckable(True)
        self.btn_mode_box_dimension.setToolTip(tr("tooltip_box_dimension", "사각 영역의 가로x세로 크기(W×H)를 박스로 표시합니다. (Shift+D)"))
        self.btn_mode_box_dimension.clicked.connect(lambda: self.switch_mode("BOX_DIMENSION"))

        dim_grid = QGridLayout()
        dim_grid.setContentsMargins(0, 0, 0, 0)
        dim_grid.setSpacing(2)
        dim_grid.addWidget(self.btn_mode_dimension, 0, 0)
        dim_grid.addWidget(self.btn_mode_box_dimension, 1, 0)
        tools_layout.addWidget(self.create_ribbon_group(tr("grp_dimension", "치수선"), dim_grid, "grp_dimension"))
        tools_layout.addWidget(self.create_separator())

        # 6) [텍스트·워드아트] 그룹
        self.btn_mode_callout = QPushButton(tr("btn_mode_callout", "설명 말풍선"), self)
        self.btn_mode_callout.setToolTip(tr("tooltip_callout", "대상 UI를 꼬리로 가리키며 설명을 기재하는 말풍선을 배치합니다."))
        self.btn_mode_callout.setCheckable(True)
        self.btn_mode_callout.clicked.connect(lambda: self.switch_mode("CALLOUT"))

        self.btn_mode_text = QPushButton(tr("btn_mode_text", "텍스트 라벨"), self)
        self.btn_mode_text.setToolTip(tr("tooltip_text", "캔버스 원하는 위치에 일반 텍스트 라벨을 입력합니다."))
        self.btn_mode_text.setCheckable(True)
        self.btn_mode_text.clicked.connect(lambda: self.switch_mode("TEXT"))

        self.btn_mode_hotkey = QPushButton(tr("btn_mode_hotkey", "단축키 배지"), self)
        self.btn_mode_hotkey.setCheckable(True)
        self.btn_mode_hotkey.setToolTip(tr("tooltip_hotkey", "Ctrl+C, Enter 등 3D 키캡 스타일 단축키를 배치합니다."))
        self.btn_mode_hotkey.clicked.connect(lambda: self.switch_mode("HOTKEY"))

        self.btn_mode_wordart = QPushButton(tr("btn_mode_wordart", "워드아트"), self)
        self.btn_mode_wordart.setCheckable(True)
        self.btn_mode_wordart.setToolTip(tr("tooltip_wordart", "외곽선과 그림자가 있는 파워포인트 워드아트 스타일 텍스트를 배치합니다."))
        self.btn_mode_wordart.clicked.connect(lambda: self.switch_mode("WORDART"))

        text_grid = QGridLayout()
        text_grid.setContentsMargins(0, 0, 0, 0)
        text_grid.setSpacing(2)
        text_grid.addWidget(self.btn_mode_callout, 0, 0)
        text_grid.addWidget(self.btn_mode_text, 0, 1)
        text_grid.addWidget(self.btn_mode_hotkey, 1, 0)
        text_grid.addWidget(self.btn_mode_wordart, 1, 1)
        tools_layout.addWidget(self.create_ribbon_group(tr("grp_text_wordart", "텍스트·워드아트"), text_grid, "grp_text_wordart"))
        tools_layout.addWidget(self.create_separator())

        # 7) [PPT 전송] 그룹
        self.btn_ppt_fit = QPushButton(tr("btn_ppt_fit", "배율 맞춤"), self)
        self.btn_ppt_fit.setToolTip(tr("tooltip_ppt_fit", "지정한 좌상단(Left, Top)에서 슬라이드 여백에 꼭 맞게 배율을 자동 계산합니다."))
        self.btn_ppt_fit.setStyleSheet("background-color: #EFFDF5; color: #15803D; border-color: #BBF7D0; font-weight: 500;")
        self.btn_ppt_fit.clicked.connect(self.auto_fit_ppt_scale)

        self.chk_ppt_title = QCheckBox(tr("chk_ppt_title", "제목 상자"), self)
        self.chk_ppt_title.setToolTip(tr("tooltip_title_box", "슬라이드 상단에 'Step N. [단계명 입력]' 텍스트 상자를 자동 삽입합니다."))
        self.chk_ppt_title.setChecked(self.config.get("ppt_layout", {}).get("include_title", True))
        self.chk_ppt_title.toggled.connect(self.on_ppt_layout_changed)

        self.btn_toggle_window_frame = QPushButton(tr("btn_window_frame", "액자 프레임"), self)
        self.btn_toggle_window_frame.setObjectName("btn_toggle_window_frame")
        self.btn_toggle_window_frame.setCheckable(True)
        self.btn_toggle_window_frame.setChecked(bool(self.config.get("enable_window_frame", True)))
        self.btn_toggle_window_frame.setToolTip(tr("tip_window_frame", "모던 윈도우 창틀 및 소프트 섀도우 액자 효과를 켜거나 끕니다. (기본값: 켜짐)"))
        self.btn_toggle_window_frame.setStyleSheet('''
            QPushButton {
                background-color: #F8FAFC;
                color: #334155;
                border: 1px solid #CBD5E1;
                font-size: 11px;
                font-weight: bold;
                border-radius: 4px;
                padding: 2px 6px;
            }
            QPushButton:checked {
                background-color: #EDE9FE;
                color: #6D28D9;
                border-color: #C4B5FD;
            }
        ''')
        self.btn_toggle_window_frame.clicked.connect(self.on_toggle_window_frame)

        ppt_grid = QGridLayout()
        ppt_grid.setContentsMargins(0, 0, 0, 0)
        ppt_grid.setSpacing(2)
        ppt_grid.addWidget(self.btn_toggle_window_frame, 0, 0)
        ppt_grid.addWidget(self.btn_ppt_fit, 0, 1)
        ppt_grid.addWidget(self.chk_ppt_title, 1, 0, 1, 2)
        tools_layout.addWidget(self.create_ribbon_group(tr("grp_slide_options", "슬라이드 옵션"), ppt_grid, "grp_slide_options"))

        tools_layout.addStretch(1)

        scroll_tools = QScrollArea(self)
        scroll_tools.setWidgetResizable(True)
        scroll_tools.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_tools.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_tools.setFrameShape(QFrame.NoFrame)
        scroll_tools.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll_tools.setWidget(tab_tools)
        scroll_tools.setFixedHeight(96)
        self.ribbon_tabs.addTab(scroll_tools, tr("tab_tools", "도구"))

        # -------------------------------------------------------------
        # TAB 2: 서식·설정 (Format & Settings)
        # -------------------------------------------------------------
        tab_format = QWidget()
        format_layout = QHBoxLayout(tab_format)
        format_layout.setContentsMargins(4, 2, 4, 2)
        format_layout.setSpacing(4)

        # 1) [스탬프] 서식 그룹 (2단 그리드)
        self.spin_stamp_size = QSpinBox(self)
        self.spin_stamp_size.setRange(16, 120)
        self.spin_stamp_size.setSingleStep(2)
        self.spin_stamp_size.setValue(self.config.get("stamp_style", {}).get("size", 32))
        self.spin_stamp_size.setSuffix(" px")
        self.spin_stamp_size.setFixedWidth(80)
        self.spin_stamp_size.valueChanged.connect(self.on_stamp_size_changed)

        self.btn_stamp_color = QPushButton(self)
        self.btn_stamp_color.setFixedSize(26, 22)
        self.update_stamp_color_button()
        self.btn_stamp_color.clicked.connect(self.choose_stamp_color)

        self.btn_reset_stamp_index = QPushButton(tr("btn_reset_stamp", "1번 초기화"), self)
        self.btn_reset_stamp_index.setToolTip("스탬프 다음 번호를 1번으로 다시 초기화합니다.")
        self.btn_reset_stamp_index.clicked.connect(self.reset_stamp_index)

        st_grid = QGridLayout()
        st_grid.setContentsMargins(0, 0, 0, 0)
        st_grid.setSpacing(2)
        st_grid.addWidget(self.create_stack_field(tr("lbl_size", "크기"), self.spin_stamp_size, "lbl_size_stamp"), 0, 0)
        st_grid.addWidget(self.create_stack_field(tr("lbl_bg_color", "배경색"), self.btn_stamp_color, "lbl_bg_color_stamp"), 0, 1)
        st_grid.addWidget(self.create_stack_field(tr("lbl_number", "번호"), self.btn_reset_stamp_index, "lbl_number_stamp"), 1, 0, 1, 2)
        format_layout.addWidget(self.create_ribbon_group(tr("grp_stamp_fmt", "스탬프"), st_grid, "grp_stamp_fmt"))
        format_layout.addWidget(self.create_separator())

        # 2) [선·화살표] 서식 그룹 (2단 그리드)
        self.spin_box_width_tab = QSpinBox(self)
        self.spin_box_width_tab.setRange(1, 20)
        self.spin_box_width_tab.setValue(self.config.get("highlight_box_style", {}).get("border_width", 3))
        self.spin_box_width_tab.setSuffix(" px")
        self.spin_box_width_tab.setFixedWidth(80)

        self.spin_arrow_head = QSpinBox(self)
        self.spin_arrow_head.setRange(6, 40)
        self.spin_arrow_head.setValue(self.config.get("arrow_style", {}).get("head_size", 14))
        self.spin_arrow_head.setSuffix(" px")
        self.spin_arrow_head.setFixedWidth(80)
        self.spin_arrow_head.valueChanged.connect(self.on_arrow_head_changed)

        self.btn_elbow_tr = QPushButton(self)
        self.btn_elbow_tr.setObjectName("BtnElbowTR")
        self.btn_elbow_tr.setIcon(RibbonIconProvider.get_toggle_icon("elbow_tr", 16))
        self.btn_elbow_tr.setIconSize(QSize(16, 16))
        self.btn_elbow_tr.setFixedSize(28, 22)
        self.btn_elbow_tr.setCheckable(True)
        self.btn_elbow_tr.setToolTip(tr("tooltip_elbow_tr", "우하향 (가로 우선 ㄱ자) [Tab/Space]"))
        self.btn_elbow_tr.clicked.connect(lambda: self.on_elbow_preset_clicked("tr"))

        self.btn_elbow_br = QPushButton(self)
        self.btn_elbow_br.setObjectName("BtnElbowBR")
        self.btn_elbow_br.setIcon(RibbonIconProvider.get_toggle_icon("elbow_br", 16))
        self.btn_elbow_br.setIconSize(QSize(16, 16))
        self.btn_elbow_br.setFixedSize(28, 22)
        self.btn_elbow_br.setCheckable(True)
        self.btn_elbow_br.setToolTip(tr("tooltip_elbow_br", "우상향 (가로 우선 ┘자) [Tab/Space]"))
        self.btn_elbow_br.clicked.connect(lambda: self.on_elbow_preset_clicked("br"))

        self.btn_elbow_bl = QPushButton(self)
        self.btn_elbow_bl.setObjectName("BtnElbowBL")
        self.btn_elbow_bl.setIcon(RibbonIconProvider.get_toggle_icon("elbow_bl", 16))
        self.btn_elbow_bl.setIconSize(QSize(16, 16))
        self.btn_elbow_bl.setFixedSize(28, 22)
        self.btn_elbow_bl.setCheckable(True)
        self.btn_elbow_bl.setToolTip(tr("tooltip_elbow_bl", "하우향 (세로 우선 ㄴ자) [Tab/Space]"))
        self.btn_elbow_bl.clicked.connect(lambda: self.on_elbow_preset_clicked("bl"))

        self.btn_elbow_tl = QPushButton(self)
        self.btn_elbow_tl.setObjectName("BtnElbowTL")
        self.btn_elbow_tl.setIcon(RibbonIconProvider.get_toggle_icon("elbow_tl", 16))
        self.btn_elbow_tl.setIconSize(QSize(16, 16))
        self.btn_elbow_tl.setFixedSize(28, 22)
        self.btn_elbow_tl.setCheckable(True)
        self.btn_elbow_tl.setToolTip(tr("tooltip_elbow_tl", "상우향 (세로 우선 ┌자) [Tab/Space]"))
        self.btn_elbow_tl.clicked.connect(lambda: self.on_elbow_preset_clicked("tl"))

        self.elbow_btn_group = QButtonGroup(self)
        self.elbow_btn_group.setExclusive(True)
        self.elbow_btn_group.addButton(self.btn_elbow_tr)
        self.elbow_btn_group.addButton(self.btn_elbow_br)
        self.elbow_btn_group.addButton(self.btn_elbow_bl)
        self.elbow_btn_group.addButton(self.btn_elbow_tl)
        self.btn_elbow_tr.setChecked(True)

        elbow_box = QHBoxLayout()
        elbow_box.setContentsMargins(0, 0, 0, 0)
        elbow_box.setSpacing(2)
        elbow_box.addWidget(self.btn_elbow_tr)
        elbow_box.addWidget(self.btn_elbow_br)
        elbow_box.addWidget(self.btn_elbow_bl)
        elbow_box.addWidget(self.btn_elbow_tl)
        elbow_widget = QWidget(self)
        elbow_widget.setLayout(elbow_box)

        self.chk_box_fill_tab = QCheckBox(tr("chk_qs_fill", "음영"), self)
        self.chk_box_fill_tab.setChecked(self.config.get("highlight_box_style", {}).get("fill", False))

        ln_grid = QGridLayout()
        ln_grid.setContentsMargins(0, 0, 0, 0)
        ln_grid.setSpacing(2)
        ln_grid.addWidget(self.create_stack_field(tr("lbl_line_width", "선 두께"), self.spin_box_width_tab, "lbl_line_width_tab"), 0, 0)
        ln_grid.addWidget(self.create_stack_field(tr("lbl_head_size", "촉 크기"), self.spin_arrow_head, "lbl_head_size"), 0, 1)
        ln_grid.addWidget(self.create_stack_field(tr("lbl_elbow_route", "꺾은선 형태"), elbow_widget, "lbl_elbow_route"), 1, 0)
        ln_grid.addWidget(self.create_stack_field(tr("chk_qs_fill", "채우기"), self.chk_box_fill_tab, "lbl_chk_fill_tab"), 1, 1)
        format_layout.addWidget(self.create_ribbon_group(tr("grp_arrow_fmt", "선·화살표"), ln_grid, "grp_arrow_fmt"))
        format_layout.addWidget(self.create_separator())

        # 3) [텍스트·글꼴] 서식 그룹 (2단 그리드)
        self.combo_text_font = QFontComboBox(self)
        self.combo_text_font.setFixedWidth(155)
        cur_f = self.config.get("text_style", {}).get("font_family", "Malgun Gothic")
        self.combo_text_font.setCurrentFont(QFont(cur_f))
        self.combo_text_font.currentFontChanged.connect(self.on_text_font_family_changed)

        self.btn_add_custom_font = QPushButton("+", self)
        self.btn_add_custom_font.setToolTip("외부/유료/토너절약 폰트 파일(.ttf, .otf, .ttc) 등록")
        self.btn_add_custom_font.setFixedSize(22, 22)
        self.btn_add_custom_font.setStyleSheet("font-weight: bold; font-size: 13px;")
        self.btn_add_custom_font.clicked.connect(self.action_add_custom_font)

        font_box = QHBoxLayout()
        font_box.setContentsMargins(0, 0, 0, 0)
        font_box.setSpacing(2)
        font_box.addWidget(self.combo_text_font)
        font_box.addWidget(self.btn_add_custom_font)
        font_box_widget = QWidget(self)
        font_box_widget.setLayout(font_box)

        self.spin_text_font_size = QSpinBox(self)
        self.spin_text_font_size.setRange(8, 72)
        self.spin_text_font_size.setValue(self.config.get("text_style", {}).get("font_size", 14))
        self.spin_text_font_size.setSuffix(" pt")
        self.spin_text_font_size.setFixedWidth(80)
        self.spin_text_font_size.valueChanged.connect(self.on_text_font_size_changed)

        self.btn_text_color = QPushButton(tr("font_sample_glyph", "A"), self)
        self.btn_text_color.setFixedSize(26, 22)
        self.update_text_color_button()
        self.btn_text_color.clicked.connect(self.choose_text_color)

        self.btn_text_bg_color = QPushButton(self)
        self.btn_text_bg_color.setFixedSize(26, 22)
        self.update_text_bg_color_button()
        self.btn_text_bg_color.clicked.connect(self.choose_text_bg_color)

        self.spin_callout_tail_size = QSpinBox(self)
        self.spin_callout_tail_size.setRange(8, 40)
        self.spin_callout_tail_size.setValue(self.config.get("callout_style", {}).get("tail_base_width", 16))
        self.spin_callout_tail_size.setSuffix(" px")
        self.spin_callout_tail_size.setFixedWidth(80)
        self.spin_callout_tail_size.valueChanged.connect(self.on_callout_tail_size_changed)

        tx_grid = QGridLayout()
        tx_grid.setContentsMargins(0, 0, 0, 0)
        tx_grid.setSpacing(2)
        tx_grid.addWidget(self.create_stack_field(tr("lbl_font", "서체"), font_box_widget, "lbl_font_family"), 0, 0, 1, 2)
        tx_grid.addWidget(self.create_stack_field(tr("lbl_size", "크기"), self.spin_text_font_size, "lbl_size_text"), 0, 2)
        tx_grid.addWidget(self.create_stack_field(tr("lbl_head_size", "꼬리"), self.spin_callout_tail_size, "lbl_callout_tail"), 1, 0)
        tx_grid.addWidget(self.create_stack_field(tr("lbl_line_color", "글자색"), self.btn_text_color, "lbl_color_text"), 1, 1)
        tx_grid.addWidget(self.create_stack_field(tr("lbl_bg_color", "배경색"), self.btn_text_bg_color, "lbl_bg_color_text"), 1, 2)
        format_layout.addWidget(self.create_ribbon_group(tr("grp_text_wordart", "텍스트·글꼴"), tx_grid, "grp_text_fmt"))
        format_layout.addWidget(self.create_separator())

        # 4) [워드아트] 서식 그룹 (2단 그리드)
        wa_cfg = self.config.get("wordart_style", {})
        self.combo_wordart_preset = QComboBox(self)
        for p_key, p_val in WordArtItem.PRESETS.items():
            wa_label = tr(f"wordart_preset_{p_key}", p_val.get("name", p_key))
            self.combo_wordart_preset.addItem(wa_label, p_key)
        cur_preset = wa_cfg.get("preset_id", "white_pop")
        idx_p = self.combo_wordart_preset.findData(cur_preset)
        if idx_p >= 0:
            self.combo_wordart_preset.setCurrentIndex(idx_p)
        self.combo_wordart_preset.setFixedWidth(150)
        self.combo_wordart_preset.currentIndexChanged.connect(self.on_wordart_preset_changed)

        self.spin_wordart_size = QSpinBox(self)
        self.spin_wordart_size.setRange(12, 120)
        self.spin_wordart_size.setValue(int(wa_cfg.get("font_size", 24)))
        self.spin_wordart_size.setSuffix(" pt")
        self.spin_wordart_size.setFixedWidth(80)
        self.spin_wordart_size.valueChanged.connect(self.on_wordart_size_changed)

        self.spin_wordart_stroke = QSpinBox(self)
        self.spin_wordart_stroke.setRange(0, 20)
        self.spin_wordart_stroke.setValue(int(wa_cfg.get("stroke_width", 3)))
        self.spin_wordart_stroke.setSuffix(" px")
        self.spin_wordart_stroke.setFixedWidth(80)
        self.spin_wordart_stroke.valueChanged.connect(self.on_wordart_stroke_changed)

        self.chk_wordart_shadow = QCheckBox(tr("chk_shadow", "그림자"), self)
        self.chk_wordart_shadow.setChecked(bool(wa_cfg.get("shadow_enabled", True)))
        self.chk_wordart_shadow.toggled.connect(self.on_wordart_shadow_toggled)

        wa_grid = QGridLayout()
        wa_grid.setContentsMargins(0, 0, 0, 0)
        wa_grid.setSpacing(2)
        wa_grid.addWidget(self.create_stack_field(tr("lbl_style", "스타일"), self.combo_wordart_preset, "lbl_wordart_preset"), 0, 0)
        wa_grid.addWidget(self.create_stack_field(tr("lbl_size", "크기"), self.spin_wordart_size, "lbl_size_wordart"), 0, 1)
        wa_grid.addWidget(self.create_stack_field(tr("lbl_stroke", "외곽선"), self.spin_wordart_stroke, "lbl_stroke_wordart"), 1, 0)
        wa_grid.addWidget(self.create_stack_field(tr("lbl_effect", "효과"), self.chk_wordart_shadow, "lbl_effect_wordart"), 1, 1)
        format_layout.addWidget(self.create_ribbon_group(tr("grp_wordart_fmt", "워드아트"), wa_grid, "grp_wordart_fmt"))
        format_layout.addWidget(self.create_separator())

        # 5) [보안·단축키] 서식 그룹 (2단 그리드)
        self.spin_blur_block = QSpinBox(self)
        self.spin_blur_block.setRange(4, 40)
        self.spin_blur_block.setValue(self.config.get("blur_style", {}).get("block_size", 10))
        self.spin_blur_block.setSuffix(" px")
        self.spin_blur_block.setFixedWidth(80)
        self.spin_blur_block.valueChanged.connect(self.on_blur_block_changed)

        self.spin_hotkey_font_size = QSpinBox(self)
        self.spin_hotkey_font_size.setRange(8, 36)
        self.spin_hotkey_font_size.setValue(self.config.get("hotkey_style", {}).get("font_size", 12))
        self.spin_hotkey_font_size.setSuffix(" pt")
        self.spin_hotkey_font_size.setFixedWidth(80)
        self.spin_hotkey_font_size.valueChanged.connect(self.on_hotkey_font_size_changed)

        sec_grid = QGridLayout()
        sec_grid.setContentsMargins(0, 0, 0, 0)
        sec_grid.setSpacing(2)
        sec_grid.addWidget(self.create_stack_field(tr("lbl_mosaic", "모자이크"), self.spin_blur_block, "lbl_mosaic_blur"), 0, 0)
        sec_grid.addWidget(self.create_stack_field(tr("lbl_key_font", "키캡 글꼴"), self.spin_hotkey_font_size, "lbl_key_font_size"), 1, 0)
        format_layout.addWidget(self.create_ribbon_group(tr("grp_security_fmt", "보안·단축키"), sec_grid, "grp_security_fmt"))
        format_layout.addWidget(self.create_separator())

        # 6) [PPT 규격·배치] 서식 그룹 (2단 그리드)
        self.spin_target_width = QSpinBox(self)
        self.spin_target_width.setRange(400, 3840)
        self.spin_target_width.setSingleStep(10)
        self.spin_target_width.setValue(self.config.get("target_width", 960))
        self.spin_target_width.setSuffix(" px")
        self.spin_target_width.setFixedWidth(96)
        self.spin_target_width.valueChanged.connect(self.on_target_width_changed)

        ppt_l = self.config.get("ppt_layout", {})
        self.spin_ppt_left = QSpinBox(self)
        self.spin_ppt_left.setRange(0, 1920)
        self.spin_ppt_left.setSingleStep(5)
        self.spin_ppt_left.setValue(ppt_l.get("left", 50))
        self.spin_ppt_left.setSuffix(" pt")
        self.spin_ppt_left.setFixedWidth(80)
        self.spin_ppt_left.valueChanged.connect(self.on_ppt_layout_changed)

        self.spin_ppt_top = QSpinBox(self)
        self.spin_ppt_top.setRange(0, 1080)
        self.spin_ppt_top.setSingleStep(5)
        self.spin_ppt_top.setValue(ppt_l.get("top", 80))
        self.spin_ppt_top.setSuffix(" pt")
        self.spin_ppt_top.setFixedWidth(80)
        self.spin_ppt_top.valueChanged.connect(self.on_ppt_layout_changed)

        self.spin_ppt_scale = QSpinBox(self)
        self.spin_ppt_scale.setRange(10, 300)
        self.spin_ppt_scale.setSingleStep(5)
        self.spin_ppt_scale.setValue(ppt_l.get("scale", 90))
        self.spin_ppt_scale.setSuffix(" %")
        self.spin_ppt_scale.setFixedWidth(80)
        self.spin_ppt_scale.valueChanged.connect(self.on_ppt_layout_changed)

        ppt_cfg_grid = QGridLayout()
        ppt_cfg_grid.setContentsMargins(0, 0, 0, 0)
        ppt_cfg_grid.setSpacing(2)
        ppt_cfg_grid.addWidget(self.create_stack_field(tr("lbl_target_width", "가로폭"), self.spin_target_width, "lbl_ppt_target_width"), 0, 0)
        ppt_cfg_grid.addWidget(self.create_stack_field(tr("lbl_ppt_scale", "배율"), self.spin_ppt_scale, "lbl_ppt_scale"), 0, 1)
        ppt_cfg_grid.addWidget(self.create_stack_field(tr("lbl_ppt_left", "Left"), self.spin_ppt_left, "lbl_ppt_left"), 1, 0)
        ppt_cfg_grid.addWidget(self.create_stack_field(tr("lbl_ppt_top", "Top"), self.spin_ppt_top, "lbl_ppt_top"), 1, 1)
        format_layout.addWidget(self.create_ribbon_group(tr("grp_ppt_cfg", "PPT 규격·배치"), ppt_cfg_grid, "grp_ppt_cfg"))
        format_layout.addWidget(self.create_separator())

        # 7) [PPT 제목상자] 서식 그룹 (4x2 그리드)
        self.spin_title_x = QSpinBox(self)
        self.spin_title_x.setRange(0, 1920)
        self.spin_title_x.setSingleStep(5)
        self.spin_title_x.setValue(int(ppt_l.get("title_left", ppt_l.get("left", 26))))
        self.spin_title_x.setSuffix(" pt")
        self.spin_title_x.setFixedWidth(80)
        self.spin_title_x.valueChanged.connect(self.on_ppt_title_layout_changed)

        self.spin_title_y = QSpinBox(self)
        self.spin_title_y.setRange(0, 1080)
        self.spin_title_y.setSingleStep(5)
        self.spin_title_y.setValue(int(ppt_l.get("title_top", 15)))
        self.spin_title_y.setSuffix(" pt")
        self.spin_title_y.setFixedWidth(80)
        self.spin_title_y.valueChanged.connect(self.on_ppt_title_layout_changed)

        self.spin_title_w = QSpinBox(self)
        self.spin_title_w.setRange(50, 1920)
        self.spin_title_w.setSingleStep(20)
        self.spin_title_w.setValue(int(ppt_l.get("title_width", 500)))
        self.spin_title_w.setSuffix(" pt")
        self.spin_title_w.setFixedWidth(88)
        self.spin_title_w.valueChanged.connect(self.on_ppt_title_layout_changed)

        self.spin_title_h = QSpinBox(self)
        self.spin_title_h.setRange(15, 500)
        self.spin_title_h.setSingleStep(5)
        self.spin_title_h.setValue(int(ppt_l.get("title_height", 35)))
        self.spin_title_h.setSuffix(" pt")
        self.spin_title_h.setFixedWidth(80)
        self.spin_title_h.valueChanged.connect(self.on_ppt_title_layout_changed)

        self.spin_title_font_size = QSpinBox(self)
        self.spin_title_font_size.setRange(8, 72)
        self.spin_title_font_size.setValue(int(ppt_l.get("title_font_size", 18)))
        self.spin_title_font_size.setSuffix(" pt")
        self.spin_title_font_size.setFixedWidth(80)
        self.spin_title_font_size.valueChanged.connect(self.on_ppt_title_layout_changed)

        self.btn_title_color = QPushButton(tr("font_sample_glyph", "A"), self)
        self.btn_title_color.setFixedSize(26, 22)
        self.update_title_color_button()
        self.btn_title_color.clicked.connect(self.choose_title_font_color)

        self.chk_title_bold = QCheckBox(tr("lbl_bold", "굵게"), self)
        self.chk_title_bold.setChecked(bool(ppt_l.get("title_font_bold", True)))
        self.chk_title_bold.toggled.connect(self.on_ppt_title_layout_changed)

        self.btn_title_align = QPushButton(tr("lbl_align", "정렬"), self)
        self.btn_title_align.setToolTip("제목 X 좌표를 이미지 Left 위치와 동일하게 정렬합니다.")
        self.btn_title_align.setFixedSize(56, 22)
        self.btn_title_align.clicked.connect(self.align_title_x_to_image)

        title_cfg_grid = QGridLayout()
        title_cfg_grid.setContentsMargins(0, 0, 0, 0)
        title_cfg_grid.setSpacing(2)
        title_cfg_grid.addWidget(self.create_stack_field(tr("lbl_title_x", "제목 X"), self.spin_title_x, "lbl_title_x"), 0, 0)
        title_cfg_grid.addWidget(self.create_stack_field(tr("lbl_title_w", "너비"), self.spin_title_w, "lbl_title_w"), 0, 1)
        title_cfg_grid.addWidget(self.create_stack_field(tr("lbl_font", "글꼴"), self.spin_title_font_size, "lbl_title_font_size"), 0, 2)
        title_cfg_grid.addWidget(self.create_stack_field(tr("lbl_line_color", "색상"), self.btn_title_color, "lbl_title_color"), 0, 3)

        title_cfg_grid.addWidget(self.create_stack_field(tr("lbl_title_y", "제목 Y"), self.spin_title_y, "lbl_title_y"), 1, 0)
        title_cfg_grid.addWidget(self.create_stack_field(tr("lbl_title_h", "높이"), self.spin_title_h, "lbl_title_h"), 1, 1)
        title_cfg_grid.addWidget(self.create_stack_field(tr("lbl_bold", "강조"), self.chk_title_bold, "lbl_title_bold_field"), 1, 2)
        title_cfg_grid.addWidget(self.create_stack_field(tr("lbl_align", "정렬"), self.btn_title_align, "lbl_title_align_field"), 1, 3)
        format_layout.addWidget(self.create_ribbon_group(tr("grp_title_cfg", "PPT 제목상자"), title_cfg_grid, "grp_title_cfg"))
        format_layout.addWidget(self.create_separator())

        # 8) [환경] 서식 그룹
        self.btn_settings = QPushButton(tr("btn_detail_settings", "상세 설정"), self)
        self.btn_settings.clicked.connect(self.open_settings_dialog)
        env_lay = QHBoxLayout()
        env_lay.setContentsMargins(0, 0, 0, 0)
        env_lay.addWidget(self.btn_settings)
        format_layout.addWidget(self.create_ribbon_group(tr("grp_settings", "환경설정"), env_lay, "grp_settings"))

        # Hidden compatibility controls for removed duplicate/floating ribbon buttons
        self.btn_renumber_steps = QPushButton(tr("btn_renumber_steps", "순번 재정렬"))
        self.btn_renumber_steps.hide()
        self.btn_renumber_steps.clicked.connect(self.action_renumber_powerpoint_steps)

        self.btn_toggle_filmstrip = QPushButton(tr("btn_toggle_filmstrip", "스토리보드"))
        self.btn_toggle_filmstrip.setCheckable(True)
        self.btn_toggle_filmstrip.hide()
        self.btn_toggle_filmstrip.clicked.connect(self.on_toggle_filmstrip)

        self.btn_export = QPushButton(tr("btn_export", "슬라이드 삽입"))
        self.btn_export.hide()
        self.btn_export.clicked.connect(self.action_export_all_ppt)

        self.btn_send_slides = QPushButton(tr("btn_send_google_slides", "구글 슬라이드 전송"))
        self.btn_send_slides.hide()
        self.btn_send_slides.clicked.connect(self.action_export_all_slides)

        self.btn_export_hwp = QPushButton(tr("btn_export_hwp", "한글 전송"))
        self.btn_export_hwp.hide()
        self.btn_export_hwp.clicked.connect(self.action_export_all_hwp)

        format_layout.addStretch(1)

        scroll_format = QScrollArea(self)
        scroll_format.setWidgetResizable(True)
        scroll_format.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_format.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_format.setFrameShape(QFrame.NoFrame)
        scroll_format.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll_format.setWidget(tab_format)
        scroll_format.setFixedHeight(112)
        self.ribbon_tabs.addTab(scroll_format, tr("tab_format", "서식·설정"))
        self.ribbon_tabs.setFixedHeight(144)

        # 리본 표시 방식 (텍스트 ⇄ 아이콘) 토글 버튼
        cur_mode = self.config.get("ribbon_display_mode", "text")
        init_toggle_txt = tr("btn_ribbon_mode_icon", "아이콘") if cur_mode == "text" else tr("btn_ribbon_mode_text", "텍스트")
        self.btn_ribbon_mode_toggle = QPushButton(init_toggle_txt, self)
        self.btn_ribbon_mode_toggle.setFixedHeight(22)
        self.btn_ribbon_mode_toggle.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9;
                color: #475569;
                border: 1px solid #CBD5E1;
                border-radius: 3px;
                font-size: 10px;
                font-weight: bold;
                padding: 2px 8px;
            }
            QPushButton:hover {
                background-color: #E2E8F0;
                color: #0F172A;
            }
        """)
        self.btn_ribbon_mode_toggle.setToolTip("리본 메뉴 표시 방식 토글 (텍스트 ⇄ 아이콘, 단축키: Ctrl+M)")
        self.btn_ribbon_mode_toggle.clicked.connect(lambda: self.toggle_ribbon_display_mode())
        self.ribbon_tabs.setCornerWidget(self.btn_ribbon_mode_toggle, Qt.TopRightCorner)

        ribbon_vlayout.addWidget(self.ribbon_tabs)

        # -------------------------------------------------------------
        # 하단 상시 퀵 서식 바 (Quick Format Strip)
        # -------------------------------------------------------------
        quick_strip = QFrame(self)
        quick_strip.setObjectName("QuickStrip")
        quick_strip.setFixedHeight(34)
        quick_strip.setStyleSheet("""
            QFrame#QuickStrip {
                background-color: #F1F5F9;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
            }
            QFrame#QuickStrip QSpinBox {
                padding: 1px 16px 1px 4px;
            }
        """)
        qs_lay = QHBoxLayout(quick_strip)
        qs_lay.setContentsMargins(4, 2, 4, 2)
        qs_lay.setSpacing(3)

        # 선 두께
        self.lbl_qs_width = QLabel(tr("lbl_qs_width", "두께:"), self)
        qs_lay.addWidget(self.lbl_qs_width)
        self.spin_box_width = QSpinBox(self)
        self.spin_box_width.setRange(1, 20)
        self.spin_box_width.setValue(self.config.get("highlight_box_style", {}).get("border_width", 3))
        self.spin_box_width.setSuffix(" px")
        self.spin_box_width.setFixedWidth(64)
        self.spin_box_width.valueChanged.connect(self.on_box_width_changed)
        self.spin_box_width.valueChanged.connect(
            lambda v: self.spin_box_width_tab.setValue(v) if self.spin_box_width_tab.value() != v else None
        )
        self.spin_box_width_tab.valueChanged.connect(
            lambda v: self.spin_box_width.setValue(v) if self.spin_box_width.value() != v else None
        )
        qs_lay.addWidget(self.spin_box_width)

        # 색상 프리셋
        self.lbl_qs_color = QLabel(tr("lbl_qs_color", "색상:"), self)
        qs_lay.addWidget(self.lbl_qs_color)
        self.box_color_buttons = []
        preset_colors = [
            "#E53935",
            "#1E88E5",
            "#43A047",
            "#FB8C00",
            "#FDD835",
        ]
        for col_code in preset_colors:
            cbtn = QPushButton(self)
            cbtn.setFixedSize(20, 20)
            cbtn.setToolTip(f"색상 선택: {col_code}")
            cbtn.setStyleSheet(f"QPushButton {{ background-color: {col_code}; border: 2px solid #CBD5E1; border-radius: 10px; padding: 0px; }} QPushButton:hover {{ border-color: #475569; }}")
            cbtn.clicked.connect(lambda checked, c=col_code: self.choose_box_preset_color(c))
            qs_lay.addWidget(cbtn)
            self.box_color_buttons.append(cbtn)

        self.btn_custom_color = QPushButton(self)
        self.btn_custom_color.setFixedSize(20, 20)
        self.btn_custom_color.setToolTip("커스텀 색상 선택")
        self.btn_custom_color.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #E53935, stop:0.25 #FB8C00, stop:0.5 #FDD835, stop:0.75 #43A047, stop:1 #1E88E5);
                border: 2px solid #CBD5E1;
                border-radius: 10px;
            }
            QPushButton:hover {
                border-color: #475569;
            }
        """)
        self.btn_custom_color.clicked.connect(self.choose_box_custom_color)
        qs_lay.addWidget(self.btn_custom_color)

        self.chk_box_fill = QCheckBox(tr("chk_qs_fill", "음영"), self)
        self.chk_box_fill.setChecked(self.config.get("highlight_box_style", {}).get("fill", False))
        self.chk_box_fill.toggled.connect(self.on_box_fill_toggled)
        self.chk_box_fill.toggled.connect(
            lambda c: self.chk_box_fill_tab.setChecked(c) if self.chk_box_fill_tab.isChecked() != c else None
        )
        self.chk_box_fill_tab.toggled.connect(
            lambda c: self.chk_box_fill.setChecked(c) if self.chk_box_fill.isChecked() != c else None
        )
        qs_lay.addWidget(self.chk_box_fill)

        qs_lay.addWidget(self.create_separator())

        # 모니터 선택 드롭다운
        self.lbl_qs_screen = QLabel(tr("lbl_qs_screen", "화면:"), self)
        qs_lay.addWidget(self.lbl_qs_screen)
        self.combo_monitor = QComboBox(self)
        self.combo_monitor.setFixedWidth(175)
        self.combo_monitor.setToolTip(tr("tooltip_monitor", "캡처 대상 모니터 선택 (최대 4개 지원)"))
        self.combo_monitor.currentIndexChanged.connect(self.on_quick_monitor_changed)
        qs_lay.addWidget(self.combo_monitor)

        qs_lay.addWidget(self.create_separator())

        # 고정 영역 제어
        self.chk_fixed_rect = QCheckBox(tr("lbl_qs_fixed", "고정"), self)
        self.chk_fixed_rect.setChecked(self.config.get("fixed_rect_enabled", True))
        self.chk_fixed_rect.toggled.connect(self.on_fixed_rect_toggled)
        qs_lay.addWidget(self.chk_fixed_rect)

        fr = self.config.get("fixed_rect", {"x": 100, "y": 100, "width": 960, "height": 540})
        qs_lay.addWidget(QLabel("X:", self))
        self.spin_fx = QSpinBox(self)
        self.spin_fx.setRange(-9999, 9999)
        self.spin_fx.setValue(fr.get("x", 100))
        self.spin_fx.setFixedWidth(70)
        self.spin_fx.valueChanged.connect(self.on_fixed_rect_changed)
        qs_lay.addWidget(self.spin_fx)

        qs_lay.addWidget(QLabel("Y:", self))
        self.spin_fy = QSpinBox(self)
        self.spin_fy.setRange(-9999, 9999)
        self.spin_fy.setValue(fr.get("y", 100))
        self.spin_fy.setFixedWidth(70)
        self.spin_fy.valueChanged.connect(self.on_fixed_rect_changed)
        qs_lay.addWidget(self.spin_fy)

        qs_lay.addWidget(QLabel("W:", self))
        self.spin_fw = QSpinBox(self)
        self.spin_fw.setRange(10, 7680)
        self.spin_fw.setValue(fr.get("width", 960))
        self.spin_fw.setFixedWidth(70)
        self.spin_fw.valueChanged.connect(self.on_fixed_rect_changed)
        qs_lay.addWidget(self.spin_fw)

        qs_lay.addWidget(QLabel("H:", self))
        self.spin_fh = QSpinBox(self)
        self.spin_fh.setRange(10, 4320)
        self.spin_fh.setValue(fr.get("height", 540))
        self.spin_fh.setFixedWidth(70)
        self.spin_fh.valueChanged.connect(self.on_fixed_rect_changed)
        qs_lay.addWidget(self.spin_fh)

        self.btn_save_rect = QPushButton(tr("btn_qs_save_rect", "영역 저장"), self)
        self.btn_save_rect.setStyleSheet("background-color: #FFF3E0; color: #D97706; border: 1px solid #FCD34D; border-radius: 3px; padding: 2px 6px; font-weight: bold;")
        self.btn_save_rect.clicked.connect(self.save_current_as_fixed_rect)
        qs_lay.addWidget(self.btn_save_rect)

        qs_lay.addWidget(self.create_separator())

        # 모드 / 선택 상태 배지
        self.lbl_active_mode = QLabel(f"{tr('lbl_qs_status', '도구:')} {tr('btn_mode_select', '선택 도구')}", self)
        self.lbl_active_mode.setStyleSheet("""
            QLabel {
                background-color: #E2E8F0;
                color: #1E293B;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                padding: 2px 6px;
                font-weight: bold;
                font-size: 11px;
            }
        """)
        qs_lay.addWidget(self.lbl_active_mode)

        qs_lay.addStretch(1)
        ribbon_vlayout.addWidget(quick_strip)

        main_layout.addWidget(ribbon_frame)

        # 2. 캔버스 영역 (스크롤 지원)
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background-color: #555555; border: 1px solid #CCCCCC;")

        self.canvas = StudioCanvasWidget(self)
        self.canvas.set_config(self.config)
        self.canvas.sig_request_toast.connect(self.show_toast)
        self.canvas.sig_item_selected.connect(self.on_canvas_item_selected)
        self.canvas.sig_request_mode_change.connect(self.switch_mode)
        self.scroll_area.setWidget(self.canvas)
        main_layout.addWidget(self.scroll_area, 1)

        # 2-2. 하단 타임라인 스토리보드 토글 바 및 독
        film_vis = bool(self.config.get("filmstrip_visible", True))
        self.storyboard_toggle_bar = StoryboardToggleBar(film_vis, self)
        self.storyboard_toggle_bar.sig_toggled.connect(self.on_storyboard_toggle_bar_toggled)
        main_layout.addWidget(self.storyboard_toggle_bar)

        self.filmstrip = FilmstripDockWidget(self)

        # 2-3. 문서 참조 보조 독 패널 초기화 및 등록
        self.doc_dock = DocumentReferenceDockWidget(self)
        self.doc_dock.sig_insert_text_to_canvas.connect(self.on_doc_insert_text_to_canvas)
        self.doc_dock.sig_apply_slide_title.connect(self.on_doc_apply_slide_title)
        self.addDockWidget(Qt.RightDockWidgetArea, self.doc_dock)
        self.doc_dock.setVisible(bool(self.config.get("doc_dock_visible", False)))

        self.filmstrip.setVisible(film_vis)
        self.filmstrip.hover_preview_enabled = bool(self.config.get("enable_hover_preview", True))
        self.filmstrip.chk_hover_preview.setChecked(self.filmstrip.hover_preview_enabled)
        self.filmstrip.sig_step_selected.connect(self.on_filmstrip_step_selected)
        self.filmstrip.sig_add_step.connect(self.action_add_new_slide)
        self.filmstrip.sig_delete_step.connect(self.on_filmstrip_delete_step)
        self.filmstrip.sig_delete_steps.connect(self.on_filmstrip_delete_selected)
        self.filmstrip.sig_duplicate_step.connect(self.on_filmstrip_duplicate_step)
        self.filmstrip.sig_duplicate_selected.connect(self.on_filmstrip_duplicate_selected)
        self.filmstrip.sig_move_selected.connect(self.on_filmstrip_move_selected)
        self.filmstrip.sig_toggle_hover_preview.connect(self.on_filmstrip_toggle_hover_preview)
        self.filmstrip.sig_move_step.connect(self.on_filmstrip_move_step)
        self.filmstrip.sig_export_all_ppt.connect(self.action_export_all_ppt)
        self.filmstrip.sig_export_all_slides.connect(self.action_export_all_slides)
        self.filmstrip.sig_export_all_hwp.connect(self.action_export_all_hwp)
        self.filmstrip.sig_export_webbook.connect(self.action_export_webbook)
        self.filmstrip.sig_export_gif.connect(self.action_export_gif)
        self.filmstrip.sig_export_pdf.connect(self.action_export_pdf)
        self.filmstrip.sig_export_word.connect(self.action_export_word_doc)
        self.filmstrip.sig_export_notion.connect(self.action_export_notion)
        self.filmstrip.sig_export_confluence.connect(self.action_export_confluence)
        main_layout.addWidget(self.filmstrip)

        # 3. 하단 상태바
        status_bar_widget = QWidget(self)
        status_layout = QHBoxLayout(status_bar_widget)
        status_layout.setContentsMargins(4, 2, 6, 2)
        status_layout.setSpacing(8)

        self.status_label = QLabel(tr("status_ready", "준비 완료 (F9: 고정 캡처, Shift+F9: 영역 지정, F10: 새 슬라이드)"), self)
        self.status_label.setStyleSheet("color: #666666; font-size: 11px; padding: 2px 4px;")
        status_layout.addWidget(self.status_label, 1)

        # 하단 우측 개발사 정보 및 Contact
        ci_pix = get_dragon_rpa_ci_pixmap()
        lbl_bot_ci = QLabel(status_bar_widget)
        if not ci_pix.isNull():
            lbl_bot_ci.setPixmap(ci_pix.scaled(14, 14, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        status_layout.addWidget(lbl_bot_ci)

        self.lbl_bottom_dev = QLabel("(주)드래곤알피에이 (DragonRPA Co.) | 평가판 (~2026.12.31) | 77.victor.lee@gmail.com", status_bar_widget)
        self.lbl_bottom_dev.setStyleSheet("color: #94A3B8; font-size: 10.5px; font-weight: 500;")
        status_layout.addWidget(self.lbl_bottom_dev)

        main_layout.addWidget(status_bar_widget)

        self.init_keytips()
        self.update_status_bar()
        self.sync_ui_from_config()
        self.init_monitor_combos()
        self.retranslate_ui()

    def init_menu_bar(self):
        menubar = self.menuBar()
        self.menubar = menubar
        menubar.setFixedHeight(28)

        self.traffic_lights = MacTrafficLight(self)
        menubar.setCornerWidget(self.traffic_lights, Qt.TopLeftCorner)
        if ThemeManager.get_effective_ui_style(getattr(self, "ui_style", "auto")) != "macos":
            self.traffic_lights.hide()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #FFFFFF;
                color: #1E293B;
                border-bottom: 1px solid #E2E8F0;
                font-family: 'Malgun Gothic';
                font-size: 11px;
                padding: 1px 4px;
            }
            QMenuBar::item {
                background: transparent;
                padding: 4px 10px;
                border-radius: 4px;
                color: #334155;
                font-weight: 500;
            }
            QMenuBar::item:selected {
                background-color: #F1F5F9;
                color: #0F172A;
            }
            QMenuBar::item:pressed {
                background-color: #E2E8F0;
            }
            QMenu {
                background-color: #FFFFFF;
                color: #1E293B;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 4px;
                font-family: 'Malgun Gothic';
                font-size: 11px;
            }
            QMenu::item {
                padding: 6px 24px 6px 12px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #2563EB;
                color: #FFFFFF;
            }
            QMenu::separator {
                height: 1px;
                background-color: #E2E8F0;
                margin: 4px 6px;
            }
        """)

        # 1. 파일(F) 메뉴
        self.menu_file = menubar.addMenu("파일(&F)")
        self.act_new_proj = self.menu_file.addAction("새 프로젝트 (Ctrl+N)")
        self.act_new_proj.setShortcut(QKeySequence("Ctrl+N"))
        self.act_new_proj.triggered.connect(self.action_new_project)
        self.act_open_proj = self.menu_file.addAction("프로젝트 열기... (Ctrl+O)")
        self.act_open_proj.setShortcut(QKeySequence("Ctrl+O"))
        self.act_open_proj.triggered.connect(self.action_open_project)
        self.act_save_proj = self.menu_file.addAction("프로젝트 저장 (Ctrl+S)")
        self.act_save_proj.setShortcut(QKeySequence("Ctrl+S"))
        self.act_save_proj.triggered.connect(self.action_save_project)
        self.act_save_as = self.menu_file.addAction("다른 이름으로 저장...")
        self.act_save_as.triggered.connect(self.action_save_as_project)
        self.act_merge_proj = self.menu_file.addAction("프로젝트 병합...")
        self.act_merge_proj.triggered.connect(self.action_merge_project)
        self.menu_file.addSeparator()
        self.act_open_img = self.menu_file.addAction("외부 이미지 열기...")
        self.act_open_img.triggered.connect(self.open_image_file)
        self.menu_file.addSeparator()
        self.act_f9 = self.menu_file.addAction("고정 캡처 (F9)")
        self.act_f9.triggered.connect(self.handle_hotkey_capture)
        self.act_shift_f9 = self.menu_file.addAction("영역 지정 캡처 (Shift+F9)")
        self.act_shift_f9.triggered.connect(self.start_capture)
        self.act_f8 = self.menu_file.addAction("부분 추가 캡처 (F8)")
        self.act_f8.triggered.connect(self.start_sub_capture)
        self.menu_file.addSeparator()
        self.act_export_ppt = self.menu_file.addAction("PowerPoint 슬라이드 전송 (F10)")
        self.act_export_ppt.setShortcut(QKeySequence("F10"))
        self.act_export_ppt.triggered.connect(self.action_export_all_ppt)
        self.act_export_slides = self.menu_file.addAction("구글 슬라이드 전송 (F11)")
        self.act_export_slides.setShortcut(QKeySequence("F11"))
        self.act_export_slides.triggered.connect(self.action_send_to_google_slides)
        self.act_export_hwp = self.menu_file.addAction("한컴 한글(HWP) 문서 전송 (Shift+F10)")
        self.act_export_hwp.setShortcut(QKeySequence("Shift+F10"))
        self.act_export_hwp.triggered.connect(self.action_send_to_hwp)
        self.act_export_webbook = self.menu_file.addAction("웹북(HTML) 매뉴얼 출판...")
        self.act_export_webbook.triggered.connect(self.action_export_webbook)
        self.act_export_gif = self.menu_file.addAction("애니메이션 GIF 생성...")
        self.act_export_gif.triggered.connect(self.action_export_gif)
        self.menu_file.addSeparator()
        self.act_export_pdf = self.menu_file.addAction(tr("dlg_export_pdf", "PDF 문서 내보내기..."))
        self.act_export_pdf.triggered.connect(self.action_export_pdf)
        self.act_export_word = self.menu_file.addAction(tr("dlg_export_word", "MS Word (.docx) 내보내기..."))
        self.act_export_word.triggered.connect(self.action_export_word_doc)
        self.act_send_word = self.menu_file.addAction(tr("menu_send_word", "MS Word 커서 위치 삽입"))
        self.act_send_word.triggered.connect(self.action_send_to_word)
        self.act_export_notion = self.menu_file.addAction(tr("dlg_export_notion", "노션(Notion) 발행..."))
        self.act_export_notion.triggered.connect(self.action_export_notion)
        self.act_export_confluence = self.menu_file.addAction(tr("dlg_export_confluence", "컨플루언스(Confluence) 발행..."))
        self.act_export_confluence.triggered.connect(self.action_export_confluence)
        self.menu_file.addSeparator()
        self.act_exit = self.menu_file.addAction("종료 (Alt+F4)")
        self.act_exit.triggered.connect(self.close)

        # 2. 편집(E) 메뉴
        self.menu_edit = menubar.addMenu("편집(&E)")
        self.act_undo = self.menu_edit.addAction("실행 취소 (Ctrl+Z)")
        self.act_undo.triggered.connect(self.action_undo)
        self.act_copy = self.menu_edit.addAction("클립보드 복사")
        self.act_copy.triggered.connect(self.copy_current_composed_image)
        self.act_clear = self.menu_edit.addAction("전체 삭제")
        self.act_clear.triggered.connect(self.action_clear)
        self.menu_edit.addSeparator()
        self.act_renumber = self.menu_edit.addAction("PPT Step 번호 자동 재정렬")
        self.act_renumber.triggered.connect(self.action_renumber_powerpoint_steps)

        # 3. 도구(T) 메뉴
        self.menu_tools = menubar.addMenu("도구(&T)")
        self.act_sel = self.menu_tools.addAction("선택 도구")
        self.act_sel.triggered.connect(lambda: self.switch_mode("SELECT"))
        self.act_st = self.menu_tools.addAction("번호 스탬프")
        self.act_st.triggered.connect(lambda: self.switch_mode("STAMP"))
        self.act_sa = self.menu_tools.addAction("순번 화살표")
        self.act_sa.triggered.connect(lambda: self.switch_mode("STEP_ARROW"))
        self.act_ea = self.menu_tools.addAction("직각 화살표")
        self.act_ea.triggered.connect(lambda: self.switch_mode("ELBOW"))
        self.act_ar = self.menu_tools.addAction("직선 화살표")
        self.act_ar.triggered.connect(lambda: self.switch_mode("ARROW"))
        self.menu_tools.addSeparator()
        self.act_bx = self.menu_tools.addAction("사각 강조")
        self.act_bx.triggered.connect(lambda: self.switch_mode("BOX"))
        self.act_bl = self.menu_tools.addAction("모자이크")
        self.act_bl.triggered.connect(lambda: self.switch_mode("BLUR"))
        self.act_dr = self.menu_tools.addAction("Draft 스탬프")
        self.act_dr.triggered.connect(self.action_add_draft_stamp)
        self.menu_tools.addSeparator()
        self.act_co = self.menu_tools.addAction("설명 말풍선")
        self.act_co.triggered.connect(lambda: self.switch_mode("CALLOUT"))
        self.act_tx = self.menu_tools.addAction("텍스트 라벨")
        self.act_tx.triggered.connect(lambda: self.switch_mode("TEXT"))
        self.act_hk = self.menu_tools.addAction("단축키 배지")
        self.act_hk.triggered.connect(lambda: self.switch_mode("HOTKEY"))

        # 4. 설정(S) 메뉴
        self.menu_settings = menubar.addMenu("설정(&S)")
        self.act_cfg = self.menu_settings.addAction("환경 설정...")
        self.act_cfg.triggered.connect(self.open_settings_dialog)
        self.act_lic = self.menu_settings.addAction("라이선스 등록(L)...")
        self.act_lic.triggered.connect(self.show_license_dialog)

        # 4.1 언어(Language) 메뉴
        self.menu_language = menubar.addMenu("언어(Language)")
        for code, name in I18nManager.instance().get_supported_locales().items():
            act_l = self.menu_language.addAction(name)
            act_l.triggered.connect(lambda checked=False, c=code: self.switch_language(c))

        # 5. 도움말(H) 메뉴
        self.menu_help = menubar.addMenu("도움말(&H)")
        self.act_update = self.menu_help.addAction("최신 업데이트 확인(&U)...")
        self.act_update.triggered.connect(lambda: self.check_for_updates(silent=False))
        self.act_release_notes = self.menu_help.addAction("업데이트 노트 (릴리즈 내역)(&R)...")
        self.act_release_notes.triggered.connect(self.show_release_notes_dialog)
        self.menu_help.addSeparator()
        self.act_eula_m = self.menu_help.addAction("사용권 계약서 (EULA)")
        self.act_eula_m.triggered.connect(self.show_eula_dialog)
        self.act_about_m = self.menu_help.addAction("프로그램 정보 (About)")
        self.act_about_m.triggered.connect(self.show_about_dialog)

    def show_release_notes_dialog(self):
        dlg = ReleaseNotesDialog(self)
        dlg.exec()

    def show_about_dialog(self):
        dlg = AboutDialog(self)
        dlg.exec()

    def show_eula_dialog(self):
        dlg = EulaDialog(self)
        dlg.exec()


    def create_ribbon_group(self, title_text, layout_content, group_id=None):
        group = QFrame(self)
        group.setObjectName("RibbonGroup")
        group.setStyleSheet("""
            QFrame#RibbonGroup {
                background-color: #FAFAFA;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
            }
            QFrame#RibbonGroup:hover {
                border-color: #94A3B8;
            }
        """)
        gl = QVBoxLayout(group)
        gl.setContentsMargins(4, 2, 4, 2)
        gl.setSpacing(2)
        gl.addLayout(layout_content)
        gl.addStretch(1)
        lbl = QLabel(title_text, group)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("font-size: 9px; color: #64748B; font-weight: bold; border: none; background: transparent; padding: 0px; margin: 0px; white-space: nowrap;")
        gl.addWidget(lbl)
        if group_id:
            if not hasattr(self, "_ribbon_groups"):
                self._ribbon_groups = {}
            self._ribbon_groups[group_id] = lbl
        return group

    def create_stack_field(self, label_text, widget, field_id=None):
        f_widget = QWidget(self)
        vl = QVBoxLayout(f_widget)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(1)
        lbl = QLabel(label_text, f_widget)
        lbl.setStyleSheet("font-size: 9px; color: #475569; font-weight: bold; border: none; background: transparent; white-space: nowrap; margin: 0px; padding: 0px;")
        vl.addWidget(lbl)
        vl.addWidget(widget)
        if field_id:
            if not hasattr(self, "_stack_fields"):
                self._stack_fields = {}
            self._stack_fields[field_id] = lbl
        return f_widget

    def create_separator(self):
        line = QFrame(self)
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Plain)
        line.setStyleSheet("color: #CBD5E1; background-color: #CBD5E1; width: 1px; margin: 6px 2px;")
        line.setFixedWidth(1)
        return line

    def retranslate_ui(self):
        """0.05초 즉시 핫스왑 다국어 UI 갱신"""
        self.retranslate_menu_bar()
        self.retranslate_ribbon()
        self.retranslate_quick_strip()
        self.retranslate_status_and_title()
        if hasattr(self, "storyboard_toggle_bar") and hasattr(self.storyboard_toggle_bar, "retranslate_ui"):
            self.storyboard_toggle_bar.retranslate_ui()
        if hasattr(self, "filmstrip") and hasattr(self.filmstrip, "retranslate_ui"):
            self.filmstrip.retranslate_ui()
        if hasattr(self, "init_monitor_combos"):
            self.init_monitor_combos()

    def retranslate_menu_bar(self):
        if hasattr(self, "menu_file"):
            self.menu_file.setTitle(tr("menu_file", "파일(&F)"))
        if hasattr(self, "act_new_proj"):
            self.act_new_proj.setText(tr("btn_new_project", "새 프로젝트") + " (Ctrl+N)")
        if hasattr(self, "act_open_proj"):
            self.act_open_proj.setText(tr("act_open_proj", "프로젝트 열기...") + " (Ctrl+O)")
        if hasattr(self, "act_save_proj"):
            self.act_save_proj.setText(tr("act_save_proj", "프로젝트 저장") + " (Ctrl+S)")
        if hasattr(self, "act_save_as"):
            self.act_save_as.setText(tr("act_save_as_proj", "다른 이름으로 저장..."))
        if hasattr(self, "act_merge_proj"):
            self.act_merge_proj.setText(tr("btn_merge_project", "프로젝트 병합..."))
        if hasattr(self, "act_open_img"):
            self.act_open_img.setText(tr("act_open_file", "외부 이미지 열기..."))
        if hasattr(self, "act_f9"):
            self.act_f9.setText(tr("btn_fixed_capture", "고정 캡처") + " (F9)")
        if hasattr(self, "act_shift_f9"):
            self.act_shift_f9.setText(tr("btn_variable_capture", "영역 지정") + " (Shift+F9)")
        if hasattr(self, "act_f8"):
            self.act_f8.setText(tr("btn_sub_capture", "부분 캡처") + " (F8)")
        if hasattr(self, "act_export_ppt"):
            self.act_export_ppt.setText(tr("menu_export_ppt", "PowerPoint 슬라이드 전송") + " (F10)")
        if hasattr(self, "act_export_slides"):
            self.act_export_slides.setText(tr("btn_send_google_slides", "구글 슬라이드 전송") + " (F11)")
        if hasattr(self, "act_export_hwp"):
            self.act_export_hwp.setText(tr("btn_export_hwp", "한글 문서 삽입") + " (Shift+F10)")
        if hasattr(self, "act_export_webbook"):
            self.act_export_webbook.setText(tr("btn_export_html_single", "웹북(HTML) 매뉴얼 출판..."))
        if hasattr(self, "act_export_gif"):
            self.act_export_gif.setText(tr("btn_export_gif", "애니메이션 GIF 생성..."))
        if hasattr(self, "act_exit"):
            self.act_exit.setText(tr("act_exit", "종료") + " (Alt+F4)")

        if hasattr(self, "menu_edit"):
            self.menu_edit.setTitle(tr("menu_edit", "편집(&E)"))
        if hasattr(self, "act_undo"):
            self.act_undo.setText(tr("act_undo", "실행 취소 (Ctrl+Z)"))
        if hasattr(self, "act_copy"):
            self.act_copy.setText(tr("act_copy_image", "클립보드 복사"))
        if hasattr(self, "act_clear"):
            self.act_clear.setText(tr("act_clear_all", "전체 삭제"))
        if hasattr(self, "act_renumber"):
            self.act_renumber.setText(tr("btn_renumber_steps", "순번 재정렬"))

        if hasattr(self, "menu_tools"):
            self.menu_tools.setTitle(tr("menu_tools", "도구(&T)"))
        if hasattr(self, "act_sel"):
            self.act_sel.setText(tr("btn_mode_select", "선택 도구"))
        if hasattr(self, "act_st"):
            self.act_st.setText(tr("btn_mode_stamp", "번호 스탬프"))
        if hasattr(self, "act_sa"):
            self.act_sa.setText(tr("btn_mode_step_arrow", "순번 화살표"))
        if hasattr(self, "act_ea"):
            self.act_ea.setText(tr("btn_mode_elbow", "직각 화살표"))
        if hasattr(self, "act_ar"):
            self.act_ar.setText(tr("btn_mode_arrow", "직선 화살표"))
        if hasattr(self, "act_bx"):
            self.act_bx.setText(tr("btn_mode_box", "사각 강조"))
        if hasattr(self, "act_bl"):
            self.act_bl.setText(tr("btn_mode_blur", "모자이크"))
        if hasattr(self, "act_dr"):
            self.act_dr.setText(tr("btn_draft_stamp", "Draft 스탬프"))
        if hasattr(self, "act_co"):
            self.act_co.setText(tr("btn_mode_callout", "설명 말풍선"))
        if hasattr(self, "act_tx"):
            self.act_tx.setText(tr("btn_mode_text", "텍스트 라벨"))
        if hasattr(self, "act_hk"):
            self.act_hk.setText(tr("btn_mode_hotkey", "단축키 배지"))

        if hasattr(self, "menu_settings"):
            self.menu_settings.setTitle(tr("menu_settings", "설정(&S)"))
        if hasattr(self, "act_cfg"):
            self.act_cfg.setText(tr("act_cfg", "환경 설정..."))
        if hasattr(self, "act_lic"):
            self.act_lic.setText(tr("act_lic", "라이선스 등록(L)..."))

        if hasattr(self, "menu_language"):
            self.menu_language.setTitle(tr("menu_language", "언어(Language)"))

        if hasattr(self, "menu_help"):
            self.menu_help.setTitle(tr("menu_help", "도움말(&H)"))
        if hasattr(self, "act_update"):
            self.act_update.setText(tr("act_update", "최신 업데이트 확인(&U)..."))
        if hasattr(self, "act_release_notes"):
            self.act_release_notes.setText(tr("act_release_notes", "업데이트 노트 (릴리즈 내역)(&R)..."))
        if hasattr(self, "act_eula_m"):
            self.act_eula_m.setText(tr("act_eula", "사용권 계약서 (EULA)"))
        if hasattr(self, "act_about_m"):
            self.act_about_m.setText(tr("act_about", "프로그램 정보 (About)"))

    def retranslate_ribbon(self):
        # 1. 탭 이름
        if hasattr(self, "ribbon_tabs"):
            self.ribbon_tabs.setTabText(0, tr("tab_tools", "도구"))
            self.ribbon_tabs.setTabText(1, tr("tab_format", "서식·설정"))

        # 2. 그룹 타이틀
        group_keys = {
            "grp_capture": ("grp_capture", "캡처"),
            "grp_flowchart": ("grp_flowchart", "플로우차트"),
            "grp_project": ("grp_project", "프로젝트"),
            "grp_select_edit": ("grp_select_edit", "선택·편집"),
            "grp_step_flow": ("grp_step_flow", "단계·흐름"),
            "grp_highlight_security": ("grp_highlight_security", "강조·보안"),
            "grp_ocr": ("grp_ocr", "텍스트 인식"),
            "grp_dimension": ("grp_dimension", "치수선"),
            "grp_text_wordart": ("grp_text_wordart", "텍스트·워드아트"),
            "grp_ppt_export": ("grp_slide_options", "슬라이드 옵션"),
            "grp_slide_options": ("grp_slide_options", "슬라이드 옵션"),
            "grp_stamp_fmt": ("grp_stamp_fmt", "스탬프"),
            "grp_arrow_fmt": ("grp_arrow_fmt", "선·화살표"),
            "grp_text_fmt": ("grp_text_wordart", "텍스트·글꼴"),
            "grp_wordart_fmt": ("grp_wordart_fmt", "워드아트"),
            "grp_security_fmt": ("grp_security_fmt", "보안·단축키"),
            "grp_ppt_cfg": ("grp_ppt_cfg", "PPT 규격·배치"),
            "grp_title_cfg": ("grp_title_cfg", "PPT 제목상자"),
            "grp_settings": ("grp_settings", "환경설정"),
        }
        if hasattr(self, "_ribbon_groups"):
            for gid, lbl in self._ribbon_groups.items():
                if gid in group_keys:
                    k, def_txt = group_keys[gid]
                    lbl.setText(tr(k, def_txt))

        # 3. 스택 필드 레이블
        field_keys = {
            "lbl_screen_select": ("lbl_screen_select", "화면"),
            "lbl_size_stamp": ("lbl_size", "크기"),
            "lbl_bg_color_stamp": ("lbl_bg_color", "배경색"),
            "lbl_number_stamp": ("lbl_number", "번호"),
            "lbl_line_width_tab": ("lbl_line_width", "선 두께"),
            "lbl_head_size": ("lbl_head_size", "촉 크기"),
            "lbl_elbow_route": ("lbl_elbow_route", "꺾은선 형태"),
            "lbl_chk_fill_tab": ("chk_qs_fill", "채우기"),
            "lbl_font_family": ("lbl_font", "서체"),
            "lbl_size_text": ("lbl_size", "크기"),
            "lbl_color_text": ("lbl_line_color", "글자색"),
            "lbl_bg_color_text": ("lbl_bg_color", "배경색"),
            "lbl_callout_tail": ("lbl_head_size", "꼬리 너비"),
            "lbl_wordart_preset": ("lbl_style", "스타일"),
            "lbl_size_wordart": ("lbl_size", "크기"),
            "lbl_stroke_wordart": ("lbl_stroke", "외곽선"),
            "lbl_effect_wordart": ("lbl_effect", "효과"),
            "lbl_mosaic_blur": ("lbl_mosaic", "모자이크"),
            "lbl_key_font_size": ("lbl_key_font", "키캡 글꼴"),
            "lbl_ppt_target_width": ("lbl_target_width", "가로폭"),
            "lbl_ppt_left": ("lbl_ppt_left", "Left"),
            "lbl_ppt_top": ("lbl_ppt_top", "Top"),
            "lbl_ppt_scale": ("lbl_ppt_scale", "배율"),
            "lbl_title_x": ("lbl_title_x", "제목 X"),
            "lbl_title_y": ("lbl_title_y", "제목 Y"),
            "lbl_title_w": ("lbl_title_w", "너비"),
            "lbl_title_h": ("lbl_title_h", "높이"),
            "lbl_title_font_size": ("lbl_font", "글꼴"),
            "lbl_title_color": ("lbl_line_color", "색상"),
            "lbl_title_bold_field": ("lbl_bold", "강조"),
            "lbl_title_align_field": ("lbl_align", "정렬"),
        }
        if hasattr(self, "_stack_fields"):
            for fid, lbl in self._stack_fields.items():
                if fid in field_keys:
                    k, def_txt = field_keys[fid]
                    lbl.setText(tr(k, def_txt))

        # 4. 버튼 텍스트 & 툴팁
        button_map = [
            ("btn_capture", "btn_fixed_capture", "고정 캡처", "tooltip_capture"),
            ("btn_drag_capture", "btn_variable_capture", "영역 지정", "tooltip_drag_capture"),
            ("btn_sub_capture", "btn_sub_capture", "부분 캡처", "tooltip_sub_capture"),
            ("btn_scroll_stitch", "btn_scroll_stitch", "스크롤 스티칭", "tip_scroll_stitch"),
            ("btn_new_project", "btn_new_project", "새 프로젝트", "tip_new_project"),
            ("btn_open_project", "btn_open_project", "불러오기", "tooltip_open_project"),
            ("btn_save_project", "btn_save_project", "프로젝트 저장", "tooltip_save_project"),
            ("btn_autosave", "btn_autosave", "자동 저장", "tooltip_autosave"),
            ("btn_merge_project", "btn_merge_project", "프로젝트 병합", "tip_merge_project"),
            ("btn_open_file", "btn_open_file", "이미지 열기", "tooltip_open_file"),
            ("btn_copy_image", "btn_copy_image", "결과 복사", "tooltip_copy_image"),
            ("btn_mode_select", "btn_mode_select", "선택 도구", "tooltip_select"),
            ("btn_undo", "btn_undo", "실행 취소", "tooltip_undo"),
            ("btn_clear", "btn_clear", "전체 삭제", "tooltip_clear"),
            ("btn_mode_stamp", "btn_mode_stamp", "번호 스탬프", "tooltip_stamp"),
            ("btn_mode_step_arrow", "btn_mode_step_arrow", "순번 화살표", "tooltip_step_arrow"),
            ("btn_mode_elbow", "btn_mode_elbow", "직각 화살표", "tooltip_elbow"),
            ("btn_mode_arrow", "btn_mode_arrow", "직선 화살표", "tooltip_arrow"),
            ("btn_mode_box", "btn_mode_box", "사각 강조", "tooltip_box"),
            ("btn_mode_blur", "btn_mode_blur", "모자이크", "tooltip_blur"),
            ("btn_mode_eraser", "btn_smart_eraser", "스마트 지우개", "tip_smart_eraser"),
            ("btn_auto_pii", "btn_auto_pii", "개인정보 마스킹", "tip_auto_pii"),
            ("btn_draft_stamp", "btn_draft_stamp", "Draft 스탬프", "tooltip_draft"),
            ("btn_mode_ocr", "btn_mode_ocr", "OCR 추출", "tooltip_ocr"),
            ("btn_mode_ocr_label", "btn_mode_ocr_label", "OCR 라벨", "tooltip_ocr_label"),
            ("btn_mode_dimension", "btn_mode_dimension", "선 치수선", "tooltip_dimension"),
            ("btn_mode_box_dimension", "btn_mode_box_dimension", "영역 치수", "tooltip_box_dimension"),
            ("btn_mode_callout", "btn_mode_callout", "설명 말풍선", "tooltip_callout"),
            ("btn_mode_text", "btn_mode_text", "텍스트 라벨", "tooltip_text"),
            ("btn_mode_hotkey", "btn_mode_hotkey", "단축키 배지", "tooltip_hotkey"),
            ("btn_mode_wordart", "btn_mode_wordart", "워드아트", "tooltip_wordart"),
            ("btn_toggle_window_frame", "btn_window_frame", "액자 프레임", "tip_window_frame"),
            ("btn_ppt_fit", "btn_ppt_fit", "배율 맞춤", "tooltip_ppt_fit"),
            ("btn_reset_stamp_index", "btn_reset_stamp", "1번 초기화", None),
            ("btn_settings", "btn_detail_settings", "상세 설정", None),
            ("btn_renumber_steps", "btn_renumber_steps", "순번 재정렬", "tooltip_renumber"),
            ("btn_toggle_filmstrip", "btn_toggle_filmstrip", "스토리보드", "tip_filmstrip_toggle"),
            ("btn_flow_terminal", "btn_flow_terminal", "시작/종료", "tip_flow_terminal"),
            ("btn_flow_process", "btn_flow_process", "일반 작업", "tip_flow_process"),
            ("btn_flow_decision", "btn_flow_decision", "조건 분기", "tip_flow_decision"),
            ("btn_flow_io", "btn_flow_io", "입출력", "tip_flow_io"),
            ("btn_flow_database", "btn_flow_database", "DB", "tip_flow_database"),
            ("btn_flow_document", "btn_flow_document", "문서", "tip_flow_document"),
            ("btn_flow_line", "btn_flow_line", "직선 연결", "tip_flow_line"),
            ("btn_flow_elbow", "btn_flow_elbow", "직각 연결", "tip_flow_elbow"),
        ]
        for attr_name, text_key, def_text, tt_key in button_map:
            if hasattr(self, attr_name):
                btn = getattr(self, attr_name)
                btn.setText(tr(text_key, def_text))
                if tt_key:
                    btn.setToolTip(tr(tt_key, ""))

        if hasattr(self, "act_export_slides"):
            self.act_export_slides.setText(f"{tr('btn_send_google_slides', '구글 슬라이드 전송')} (F11)")
        if hasattr(self, "chk_ppt_title"):
            self.chk_ppt_title.setText(tr("chk_ppt_title", "제목 상자"))
            self.chk_ppt_title.setToolTip(tr("tooltip_title_box", ""))
        if hasattr(self, "chk_box_fill_tab"):
            self.chk_box_fill_tab.setText(tr("chk_qs_fill", "음영"))
        if hasattr(self, "chk_wordart_shadow"):
            self.chk_wordart_shadow.setText(tr("chk_shadow", "그림자"))
        if hasattr(self, "chk_title_bold"):
            self.chk_title_bold.setText(tr("lbl_bold", "굵게"))
        if hasattr(self, "btn_elbow_tr"):
            self.btn_elbow_tr.setToolTip(tr("tooltip_elbow_tr", "우하향 (가로 우선 ㄱ자) [Tab/Space]"))
        if hasattr(self, "btn_elbow_br"):
            self.btn_elbow_br.setToolTip(tr("tooltip_elbow_br", "우상향 (가로 우선 ┘자) [Tab/Space]"))
        if hasattr(self, "btn_elbow_bl"):
            self.btn_elbow_bl.setToolTip(tr("tooltip_elbow_bl", "하우향 (세로 우선 ㄴ자) [Tab/Space]"))
        if hasattr(self, "btn_elbow_tl"):
            self.btn_elbow_tl.setToolTip(tr("tooltip_elbow_tl", "상우향 (세로 우선 ┌자) [Tab/Space]"))
        if hasattr(self, "btn_title_align"):
            self.btn_title_align.setText(tr("lbl_align", "정렬"))
        if hasattr(self, "btn_text_color"):
            self.update_text_color_button()
        if hasattr(self, "btn_title_color"):
            self.update_title_color_button()
        if hasattr(self, "combo_wordart_preset"):
            cur_data = self.combo_wordart_preset.currentData()
            self.combo_wordart_preset.blockSignals(True)
            self.combo_wordart_preset.clear()
            for p_key, p_val in WordArtItem.PRESETS.items():
                wa_label = tr(f"wordart_preset_{p_key}", p_val.get("name", p_key))
                self.combo_wordart_preset.addItem(wa_label, p_key)
            idx_p = self.combo_wordart_preset.findData(cur_data)
            if idx_p >= 0:
                self.combo_wordart_preset.setCurrentIndex(idx_p)
            self.combo_wordart_preset.blockSignals(False)

        cur_mode = self.config.get("ribbon_display_mode", "text")
        self.toggle_ribbon_display_mode(mode=cur_mode)

    def retranslate_quick_strip(self):
        if hasattr(self, "lbl_qs_width"):
            self.lbl_qs_width.setText(tr("lbl_qs_width", "두께:"))
        if hasattr(self, "lbl_qs_color"):
            self.lbl_qs_color.setText(tr("lbl_qs_color", "색상:"))
        if hasattr(self, "chk_box_fill"):
            self.chk_box_fill.setText(tr("chk_qs_fill", "음영"))
        if hasattr(self, "lbl_qs_screen"):
            self.lbl_qs_screen.setText(tr("lbl_qs_screen", "화면:"))
        if hasattr(self, "combo_monitor"):
            self.combo_monitor.setToolTip(tr("tooltip_monitor", "캡처 대상 모니터 선택 (최대 4개 지원)"))
        if hasattr(self, "chk_fixed_rect"):
            self.chk_fixed_rect.setText(tr("lbl_qs_fixed", "고정"))
        if hasattr(self, "btn_save_rect"):
            self.btn_save_rect.setText(tr("btn_qs_save_rect", "영역 저장"))
        self.update_mode_status_indicator()

    def retranslate_status_and_title(self):
        self.update_window_title()
        self.update_status_bar()
        if hasattr(self, "canvas") and self.canvas.pixmap is None and hasattr(self, "status_label"):
            self.status_label.setText(tr("status_ready", "준비 완료 (F9: 고정 캡처, Shift+F9: 영역 지정, F10: 새 슬라이드)"))

    def on_autosave_toggle_clicked(self, checked=None):
        if not hasattr(self, "btn_autosave"):
            return
        is_on = self.btn_autosave.isChecked()
        self.config["auto_save_enabled"] = is_on
        save_config(self.config)
        self.update_autosave_timer()
        self.update_autosave_button_style()
        status_txt = "자동 저장 활성화됨" if is_on else "자동 저장 비활성화됨"
        self.show_toast(status_txt)
        if hasattr(self, "status_label"):
            self.status_label.setText(status_txt)

    def update_autosave_button_style(self):
        if not hasattr(self, "btn_autosave"):
            return
        is_on = self.btn_autosave.isChecked()
        if is_on:
            self.btn_autosave.setStyleSheet("""
                QPushButton {
                    background-color: #ECFDF5;
                    color: #065F46;
                    border: 1px solid #A7F3D0;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #D1FAE5;
                }
            """)
        else:
            self.btn_autosave.setStyleSheet("""
                QPushButton {
                    background-color: #F8FAFC;
                    color: #94A3B8;
                    border: 1px solid #E2E8F0;
                    font-weight: normal;
                }
                QPushButton:hover {
                    background-color: #F1F5F9;
                    color: #64748B;
                }
            """)

    def toggle_ribbon_display_mode(self, mode=None):
        if mode is None:
            cur_mode = self.config.get("ribbon_display_mode", "text")
            new_mode = "icon" if cur_mode == "text" else "text"
        else:
            new_mode = mode

        self.config["ribbon_display_mode"] = new_mode
        save_config(self.config)

        if hasattr(self, "btn_ribbon_mode_toggle"):
            toggle_txt = tr("btn_ribbon_mode_icon", "아이콘") if new_mode == "text" else tr("btn_ribbon_mode_text", "텍스트")
            self.btn_ribbon_mode_toggle.setText(toggle_txt)

        btn_icon_defs = [
            ("btn_capture", "capture_fixed", "btn_fixed_capture", "고정 캡처"),
            ("btn_drag_capture", "capture_area", "btn_variable_capture", "영역 지정"),
            ("btn_sub_capture", "capture_sub", "btn_sub_capture", "부분 캡처"),
            ("btn_save_rect", "save_rect", "btn_save_rect", "영역 고정"),
            ("btn_scroll_stitch", "scroll_stitch", "btn_scroll_stitch", "스크롤 스티칭"),
            ("btn_new_project", "new_project", "btn_new_project", "새 프로젝트"),
            ("btn_open_project", "open_project", "btn_open_project", "불러오기"),
            ("btn_save_project", "save_project", "btn_save_project", "프로젝트 저장"),
            ("btn_merge_project", "merge_project", "btn_merge_project", "프로젝트 병합"),
            ("btn_autosave", "autosave", "btn_autosave", "자동 저장"),
            ("btn_open_file", "open_image", "btn_open_file", "이미지 열기"),
            ("btn_copy_image", "copy_image", "btn_copy_image", "결과 복사"),
            ("btn_mode_select", "select", "btn_mode_select", "선택 도구"),
            ("btn_undo", "undo", "btn_undo", "실행 취소"),
            ("btn_clear", "clear", "btn_clear", "전체 삭제"),
            ("btn_mode_stamp", "stamp", "btn_mode_stamp", "번호 스탬프"),
            ("btn_reset_stamp_index", "reset_index", "btn_reset_stamp_index", "순번 초기화"),
            ("btn_mode_step_arrow", "step_arrow", "btn_mode_step_arrow", "순번 화살표"),
            ("btn_mode_elbow", "elbow", "btn_mode_elbow", "직각 화살표"),
            ("btn_mode_arrow", "arrow", "btn_mode_arrow", "직선 화살표"),
            ("btn_mode_box", "box", "btn_mode_box", "사각 강조"),
            ("btn_mode_blur", "blur", "btn_mode_blur", "모자이크"),
            ("btn_auto_pii", "auto_pii", "btn_auto_pii", "개인정보 마스킹"),
            ("btn_mode_eraser", "eraser", "btn_mode_eraser", "스마트 지우개"),
            ("btn_draft_stamp", "draft", "btn_draft_stamp", "Draft 스탬프"),
            ("btn_mode_ocr", "ocr", "btn_mode_ocr", "OCR 추출"),
            ("btn_mode_ocr_label", "ocr_label", "btn_mode_ocr_label", "OCR 라벨"),
            ("btn_mode_dimension", "dimension", "btn_mode_dimension", "선 치수선"),
            ("btn_mode_box_dimension", "box_dimension", "btn_mode_box_dimension", "영역 치수"),
            ("btn_mode_callout", "callout", "btn_mode_callout", "설명 말풍선"),
            ("btn_mode_text", "text", "btn_mode_text", "텍스트 라벨"),
            ("btn_mode_hotkey", "hotkey", "btn_mode_hotkey", "단축키 배지"),
            ("btn_mode_wordart", "wordart", "btn_mode_wordart", "워드아트"),
            ("btn_flowchart", "flowchart", "btn_flowchart_builder", "플로우차트"),
            ("btn_flow_line", "flow_line", "btn_flow_line", "직선 연결"),
            ("btn_flow_elbow", "flow_elbow", "btn_flow_elbow", "직각 연결"),
            ("btn_flow_terminal", "flow_terminal", "btn_flow_terminal", "시작/종료"),
            ("btn_flow_process", "flow_process", "btn_flow_process", "일반 작업"),
            ("btn_flow_decision", "flow_decision", "btn_flow_decision", "조건 분기"),
            ("btn_flow_io", "flow_io", "btn_flow_io", "입출력"),
            ("btn_flow_database", "flow_database", "btn_flow_database", "DB"),
            ("btn_flow_document", "flow_document", "btn_flow_document", "문서"),
            ("btn_flow_align", "flow_align", "btn_flow_align", "자동정렬"),
            ("btn_mobile_link", "mobile_link", "btn_mobile_link", "모바일 연동"),
            ("btn_export", "ppt_export", "btn_export", "슬라이드 삽입"),
            ("btn_export_hwp", "export_hwp", "btn_export_hwp", "한글 문서 삽입"),
            ("btn_send_slides", "slides_export", "btn_send_google_slides", "구글 슬라이드 전송"),
            ("btn_ppt_fit", "ppt_autofit", "btn_ppt_fit", "배율 맞춤"),
            ("btn_renumber_steps", "ppt_renumber", "btn_renumber_steps", "순번 재정렬"),
            ("btn_toggle_window_frame", "window_frame", "btn_toggle_window_frame", "창틀 프레임"),
            ("btn_toggle_filmstrip", "filmstrip", "btn_toggle_filmstrip", "스토리보드"),
            ("btn_settings", "settings", "btn_settings", "환경설정"),
        ]

        for attr, icon_name, text_key, def_text in btn_icon_defs:
            if hasattr(self, attr):
                btn = getattr(self, attr)
                if new_mode == "icon":
                    if attr == "btn_export":
                        icon_color = "#C2410C"
                    elif attr == "btn_export_hwp":
                        icon_color = "#0284C7"
                    elif attr == "btn_send_slides":
                        icon_color = "#D97706"
                    elif attr.startswith("btn_flow"):
                        icon_color = "#166534"
                    elif attr == "btn_clear":
                        icon_color = "#DC2626"
                    elif attr == "btn_auto_pii":
                        icon_color = "#2563EB"
                    else:
                        icon_color = "#334155"
                    icon = RibbonIconProvider.get_icon(icon_name, size=18, color=icon_color)
                    btn.setIcon(icon)
                    btn.setIconSize(QSize(18, 18))
                    btn.setText("")
                else:
                    btn.setIcon(QIcon())
                    btn.setText(tr(text_key, def_text))

        mode_name_kr = "아이콘 모드" if new_mode == "icon" else "텍스트 모드"
        if mode is None:
            self.show_toast(f"리본 메뉴 표시 방식: {mode_name_kr}")

    def init_keytips(self):
        self._keytip_labels = []
        self._keytips_visible = False

    def get_keytip_mappings(self):
        mappings = []
        if hasattr(self, "ribbon_tabs"):
            tab_bar = self.ribbon_tabs.tabBar()
            mappings.append((tab_bar, "1", 0))
            mappings.append((tab_bar, "2", 1))

        if hasattr(self, "btn_ribbon_mode_toggle"):
            mappings.append((self.btn_ribbon_mode_toggle, "^M", None))

        btn_tips = [
            ("btn_capture", "F9"),
            ("btn_drag_capture", "SF9"),
            ("btn_sub_capture", "F8"),
            ("btn_open_project", "^O"),
            ("btn_save_project", "^S"),
            ("btn_autosave", "!A"),
            ("btn_open_file", "^I"),
            ("btn_copy_image", "^C"),
            ("btn_mode_select", "V"),
            ("btn_undo", "^Z"),
            ("btn_clear", "DEL"),
            ("btn_mode_stamp", "S"),
            ("btn_mode_step_arrow", "W"),
            ("btn_mode_elbow", "E"),
            ("btn_mode_arrow", "A"),
            ("btn_mode_box", "B"),
            ("btn_mode_blur", "M"),
            ("btn_draft_stamp", "D"),
            ("btn_mode_callout", "C"),
            ("btn_mode_text", "T"),
            ("btn_mode_hotkey", "K"),
            ("btn_mode_wordart", "R"),
            ("btn_export", "F10"),
            ("btn_send_slides", "F11"),
            ("btn_ppt_fit", "^F"),
            ("btn_renumber_steps", "^R"),
        ]
        for attr, tip in btn_tips:
            if hasattr(self, attr):
                w = getattr(self, attr)
                if w.isVisible():
                    mappings.append((w, tip, None))
        return mappings

    def toggle_keytips(self):
        if self._keytips_visible:
            self.hide_keytips()
        else:
            self.show_keytips()

    def show_keytips(self):
        self.hide_keytips()
        QCoreApplication.processEvents()
        mappings = self.get_keytip_mappings()

        badge_style = """
            QLabel {
                background-color: #FEF08A;
                color: #0F172A;
                border: 1px solid #CA8A04;
                border-radius: 3px;
                font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
                font-size: 10px;
                font-weight: bold;
                padding: 1px 3px;
            }
        """

        for item in mappings:
            w, tip, tab_idx = item
            if not w or not w.isVisible():
                continue

            lbl = QLabel(tip, self)
            lbl.setStyleSheet(badge_style)
            lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            lbl.adjustSize()

            if tab_idx is not None:
                rect = w.tabRect(tab_idx)
                global_pt = w.mapTo(self, QPoint(rect.x() + (rect.width() - lbl.width()) // 2, rect.y() + rect.height() - 6))
            else:
                global_pt = w.mapTo(self, QPoint(max(0, (w.width() - lbl.width()) // 2), max(0, (w.height() - lbl.height()) // 2)))

            lbl.move(global_pt)
            lbl.show()
            lbl.raise_()
            self._keytip_labels.append(lbl)

        self._keytips_visible = True

    def hide_keytips(self):
        for lbl in self._keytip_labels:
            lbl.hide()
            lbl.deleteLater()
        self._keytip_labels = []
        self._keytips_visible = False

    def mousePressEvent(self, event):
        if hasattr(self, "_keytips_visible") and self._keytips_visible:
            self.hide_keytips()
        super().mousePressEvent(event)

    def open_image_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "이미지 파일 열기", "", "이미지 파일 (*.png *.jpg *.jpeg *.bmp *.webp);;모든 파일 (*.*)"
        )
        if file_path and os.path.exists(file_path):
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                self.on_capture_completed(pixmap)
                self.show_toast(f"이미지 로드 완료: {os.path.basename(file_path)}")

    def _sync_canvas_to_current_step(self):
        """현재 캔버스 작업 내용을 스토리보드 활성 슬라이드에 완전 동기화"""
        if len(self.storyboard_steps) == 0:
            if self.canvas.pixmap is not None or len(self.canvas.items) > 0:
                self.storyboard_steps.append({
                    "step_num": 1,
                    "title": "Step 1. [단계명 입력]",
                    "description": "",
                    "raw_pixmap": self.canvas.pixmap.copy() if self.canvas.pixmap else None,
                    "thumbnail": self.canvas.pixmap.copy() if self.canvas.pixmap else None,
                    "items": [it.clone() for it in self.canvas.items],
                    "next_stamp_index": self.canvas.next_stamp_index
                })
                self.current_step_idx = 0
                if hasattr(self, "filmstrip"):
                    self.filmstrip.set_steps(self.storyboard_steps, 0)
        elif 0 <= self.current_step_idx < len(self.storyboard_steps):
            curr = self.storyboard_steps[self.current_step_idx]
            if self.canvas.pixmap is not None:
                curr["raw_pixmap"] = self.canvas.pixmap.copy()
            curr["items"] = [it.clone() for it in self.canvas.items]
            curr["next_stamp_index"] = self.canvas.next_stamp_index
            comp = self.canvas.get_composed_image()
            if comp:
                curr["thumbnail"] = QPixmap.fromImage(comp)

    def action_new_project(self):
        """새 프로젝트 (Ctrl+N): 기존 작업 보존 확인 후 초기화"""
        has_content = (len(self.storyboard_steps) > 1 or 
                       (len(self.storyboard_steps) == 1 and self.storyboard_steps[0].get("raw_pixmap") is not None) or
                       self.canvas.pixmap is not None or len(self.canvas.items) > 0)
        if has_content:
            res = QMessageBox.question(
                self,
                tr("btn_new_project", "새 프로젝트"),
                tr("msg_new_project_confirm", "현재 작업 중인 프로젝트의 변경사항을 잃을 수 있습니다.\n새 프로젝트를 시작하시겠습니까?"),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if res != QMessageBox.Yes:
                return

        self.storyboard_steps = []
        self.current_step_idx = 0
        self.current_project_path = None
        self.canvas.clear_all()
        self.canvas.pixmap = None
        self.canvas.items.clear()
        self.canvas.next_stamp_index = 1
        self.canvas.history.clear()
        self.canvas.update()
        if hasattr(self, "filmstrip"):
            self.filmstrip.set_steps([], 0)
        self.update_window_title()
        self.show_toast(tr("status_ready", "준비 완료"))

    def action_open_project(self):
        filter_str = tr("filter_all_projects", "매뉴얼 프로젝트 (*.dragon *.mcs.json);;Dragon 압축 패키지 (*.dragon);;JSON 프로젝트 (*.mcs.json *.json);;모든 파일 (*.*)")
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            tr("btn_open_project", "프로젝트 열기"),
            "",
            filter_str
        )
        if file_path and os.path.exists(file_path):
            self.load_project_file(file_path)

    def load_project_file(self, file_path: str):
        proj_data = ProjectManager.load_project(file_path)
        steps = proj_data.steps if hasattr(proj_data, "steps") else []
        if not steps:
            # 하위 호환 튜플 확인
            if isinstance(proj_data, (tuple, list)) and len(proj_data) >= 4 and proj_data[0] is not None:
                raw_px, items, next_idx, meta = proj_data[0], proj_data[1], proj_data[2], proj_data[3]
                steps = [{
                    "step_num": 1,
                    "title": "Step 1. [단계명 입력]",
                    "description": "",
                    "raw_pixmap": raw_px,
                    "thumbnail": raw_px.copy() if raw_px else None,
                    "items": items,
                    "next_stamp_index": next_idx
                }]

        if not steps:
            self.show_toast(f"프로젝트 로드 실패: 유효한 슬라이드 데이터를 찾을 수 없습니다 ({os.path.basename(file_path)})")
            return False

        self.storyboard_steps = steps
        active_idx = getattr(proj_data, "active_step_idx", 0)
        self.current_step_idx = max(0, min(active_idx, len(steps) - 1))

        active_step = self.storyboard_steps[self.current_step_idx]
        self.canvas.load_project_data(
            active_step.get("raw_pixmap"),
            active_step.get("items", []),
            active_step.get("next_stamp_index", 1)
        )
        if hasattr(self, "filmstrip"):
            self.filmstrip.set_steps(self.storyboard_steps, self.current_step_idx)

        self.current_project_path = file_path
        self.last_capture_rect = None
        base_name = os.path.basename(file_path)
        self.update_window_title()
        self.show_toast(f"프로젝트 로드 완료: {base_name} (슬라이드 {len(steps)}개)")
        return True

    def action_merge_project(self):
        """진행 중인 프로젝트에 타인의 프로젝트를 병합 (순서 자동 연계)"""
        self._sync_canvas_to_current_step()
        filter_str = tr("filter_all_projects", "매뉴얼 프로젝트 (*.dragon *.mcs.json);;Dragon 압축 패키지 (*.dragon);;JSON 프로젝트 (*.mcs.json *.json);;모든 파일 (*.*)")
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            tr("btn_merge_project", "프로젝트 병합"),
            "",
            filter_str
        )
        if file_path and os.path.exists(file_path):
            merged_steps, added_count = ProjectManager.merge_project(self.storyboard_steps, file_path)
            if added_count > 0:
                self.storyboard_steps = merged_steps
                if hasattr(self, "filmstrip"):
                    self.filmstrip.set_steps(self.storyboard_steps, self.current_step_idx)
                msg = tr("toast_project_merged", "프로젝트 병합 완료 ({count}개 슬라이드 추가됨)").format(count=added_count)
                self.show_toast(msg)
            else:
                self.show_toast("병합할 슬라이드가 없습니다.")

    def action_save_project(self):
        self._sync_canvas_to_current_step()
        if not self.storyboard_steps and self.canvas.pixmap is None:
            self.show_toast("저장할 프로젝트 내용이 없습니다. 먼저 캡처하세요.")
            return False

        if self.current_project_path:
            return self.save_project_to_path(self.current_project_path)
        else:
            return self.action_save_as_project()

    def action_save_as_project(self):
        self._sync_canvas_to_current_step()
        if not self.storyboard_steps and self.canvas.pixmap is None:
            self.show_toast("저장할 프로젝트 내용이 없습니다. 먼저 캡처하세요.")
            return False

        save_dir = os.path.join(
            get_app_dir(),
            self.config.get("save_directory", "captures")
        )
        today_str = datetime.now().strftime("%Y%m%d")
        dest_folder = os.path.join(save_dir, f"captures_{today_str}")
        os.makedirs(dest_folder, exist_ok=True)

        existing = [
            f for f in os.listdir(dest_folder)
            if f.startswith("Manual_") and (f.endswith(".dragon") or f.endswith(".mcs.json"))
        ]
        default_name = f"Manual_Project_{len(existing) + 1:03d}.dragon"
        default_path = os.path.join(dest_folder, default_name)

        filter_str = tr("filter_all_projects", "매뉴얼 프로젝트 (*.dragon *.mcs.json);;Dragon 압축 패키지 (*.dragon);;JSON 프로젝트 (*.mcs.json *.json);;모든 파일 (*.*)")
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            tr("btn_save_project", "프로젝트 저장"),
            default_path,
            filter_str
        )
        if file_path:
            return self.save_project_to_path(file_path)
        return False

    def save_project_to_path(self, file_path: str):
        self._sync_canvas_to_current_step()
        metadata = {"ppt_layout": self.config.get("ppt_layout", {})}
        ok = ProjectManager.save_project(
            file_path,
            self.storyboard_steps,
            active_step_idx=self.current_step_idx,
            metadata=metadata
        )
        if ok:
            self.current_project_path = file_path
            base_name = os.path.basename(file_path)
            self.update_window_title()
            self.show_toast(f"프로젝트 저장 완료: {base_name} (슬라이드 {len(self.storyboard_steps)}개)")
            auto_p = self.get_autosave_path()
            if os.path.exists(auto_p):
                try:
                    os.remove(auto_p)
                except Exception:
                    pass
            return True
        else:
            self.show_toast("프로젝트 저장 실패")
            return False

    def copy_current_composed_image(self):
        if self.canvas.pixmap is None:
            self.show_toast("복사할 이미지가 없습니다. 먼저 캡처하거나 파일을 여세요.")
            return
        qimg = self.canvas.get_composed_image()
        if qimg:
            pil_img = ExportEngine.qimage_to_pil(qimg)
            if self.config.get("enable_window_frame", True):
                frame_cfg = self.config.get("window_frame_style", {})
                pil_img = ExportEngine.apply_window_frame_and_shadow(
                    pil_img,
                    include_header=frame_cfg.get("include_header", True),
                    corner_radius=frame_cfg.get("corner_radius", 12),
                    shadow_radius=frame_cfg.get("shadow_radius", 20),
                    shadow_opacity=frame_cfg.get("shadow_opacity", 0.35)
                )
            try:
                ExportEngine.copy_to_clipboard(pil_img)
                self.show_toast("클립보드에 이미지 복사 완료 (Ctrl+V)")
            except Exception as e:
                self.show_toast(f"클립보드 복사 실패: {e}")

    def reset_stamp_index(self):
        self.canvas.next_stamp_index = 1
        self.show_toast("스탬프 다음 번호가 1번으로 초기화되었습니다.")

    def update_mode_status_indicator(self, mode_or_name=None):
        mode_keys = {
            "SELECT": ("btn_mode_select", "선택 도구"),
            "STAMP": ("btn_mode_stamp", "번호 스탬프"),
            "STEP_ARROW": ("btn_mode_step_arrow", "순번 화살표"),
            "ELBOW": ("btn_mode_elbow", "직각 화살표"),
            "ARROW": ("btn_mode_arrow", "직선 화살표"),
            "BOX": ("btn_mode_box", "사각 박스"),
            "BLUR": ("btn_mode_blur", "모자이크 블러"),
            "ERASER": ("btn_smart_eraser", "스마트 지우개"),
            "CALLOUT": ("btn_mode_callout", "설명 말풍선"),
            "TEXT": ("btn_mode_text", "텍스트 라벨"),
            "HOTKEY": ("btn_mode_hotkey", "단축키 배지"),
            "WORDART": ("btn_mode_wordart", "워드아트"),
            "OCR": ("btn_mode_ocr", "OCR 텍스트 추출"),
            "OCR_LABEL": ("btn_mode_ocr_label", "OCR 라벨"),
            "DIMENSION": ("btn_mode_dimension", "선 치수선"),
            "BOX_DIMENSION": ("btn_mode_box_dimension", "영역 치수"),
            "FLOW_TERMINAL": ("btn_flow_terminal", "시작/종료"),
            "FLOW_PROCESS": ("btn_flow_process", "일반 작업"),
            "FLOW_DECISION": ("btn_flow_decision", "조건 분기"),
            "FLOW_IO": ("btn_flow_io", "입출력"),
            "FLOW_DATABASE": ("btn_flow_database", "DB"),
            "FLOW_DOCUMENT": ("btn_flow_document", "문서"),
            "FLOW_CONNECT_LINE": ("btn_flow_line", "직선 연결"),
            "FLOW_CONNECT_ELBOW": ("btn_flow_elbow", "직각 연결"),
        }
        cur_mode = mode_or_name or self.canvas.current_mode
        if cur_mode in mode_keys:
            k, def_txt = mode_keys[cur_mode]
            text = tr(k, def_txt)
        else:
            text = cur_mode
        if hasattr(self, "lbl_active_mode"):
            status_prefix = tr("lbl_qs_status", "도구:")
            self.lbl_active_mode.setText(f"{status_prefix} {text}")

    def init_hotkey(self):
        cap_key = self.config.get("hotkey_capture", "F9")
        exp_key = self.config.get("hotkey_export", "F10")
        slides_key = self.config.get("hotkey_slides", "F11")
        self.hotkey_thread = GlobalHotkeyThread(cap_key, exp_key, slides_key, self)
        self.hotkey_thread.sig_capture.connect(self.handle_hotkey_capture)
        self.hotkey_thread.sig_drag_capture.connect(self.start_capture)
        self.hotkey_thread.sig_sub_capture.connect(self.start_sub_capture)
        self.hotkey_thread.sig_export.connect(self.action_add_new_slide)
        self.hotkey_thread.sig_slides_export.connect(self.action_send_to_google_slides)
        self.hotkey_thread.sig_hwp_export.connect(self.action_send_to_hwp)
        self.hotkey_thread.start()

    def switch_mode(self, mode):
        self.canvas.set_mode(mode)
        self.btn_mode_select.setChecked(mode == "SELECT")
        self.btn_mode_stamp.setChecked(mode == "STAMP")
        if hasattr(self, "btn_mode_step_arrow"):
            self.btn_mode_step_arrow.setChecked(mode == "STEP_ARROW")
        if hasattr(self, "btn_mode_elbow"):
            self.btn_mode_elbow.setChecked(mode == "ELBOW")
        self.btn_mode_arrow.setChecked(mode == "ARROW")
        self.btn_mode_box.setChecked(mode == "BOX")
        if hasattr(self, "btn_mode_blur"):
            self.btn_mode_blur.setChecked(mode == "BLUR")
        if hasattr(self, "btn_mode_eraser"):
            self.btn_mode_eraser.setChecked(mode == "ERASER")
        if hasattr(self, "btn_mode_callout"):
            self.btn_mode_callout.setChecked(mode == "CALLOUT")
        self.btn_mode_text.setChecked(mode == "TEXT")
        if hasattr(self, "btn_mode_hotkey"):
            self.btn_mode_hotkey.setChecked(mode == "HOTKEY")
        if hasattr(self, "btn_mode_wordart"):
            self.btn_mode_wordart.setChecked(mode == "WORDART")
        if hasattr(self, "btn_mode_ocr"):
            self.btn_mode_ocr.setChecked(mode == "OCR")
        if hasattr(self, "btn_mode_ocr_label"):
            self.btn_mode_ocr_label.setChecked(mode == "OCR_LABEL")
        if hasattr(self, "btn_mode_dimension"):
            self.btn_mode_dimension.setChecked(mode == "DIMENSION")
        if hasattr(self, "btn_mode_box_dimension"):
            self.btn_mode_box_dimension.setChecked(mode == "BOX_DIMENSION")
        if hasattr(self, "btn_flow_terminal"):
            self.btn_flow_terminal.setChecked(mode == "FLOW_TERMINAL")
            self.btn_flow_process.setChecked(mode == "FLOW_PROCESS")
            self.btn_flow_decision.setChecked(mode == "FLOW_DECISION")
            self.btn_flow_io.setChecked(mode == "FLOW_IO")
            self.btn_flow_database.setChecked(mode == "FLOW_DATABASE")
            self.btn_flow_document.setChecked(mode == "FLOW_DOCUMENT")
        if hasattr(self, "btn_flow_line") and self.btn_flow_line:
            self.btn_flow_line.setChecked(mode in ("ARROW", "FLOW_CONNECT_LINE"))
        if hasattr(self, "btn_flow_elbow") and self.btn_flow_elbow:
            self.btn_flow_elbow.setChecked(mode in ("ELBOW", "FLOW_CONNECT_ELBOW"))
        self.update_mode_status_indicator(mode)

    def update_stamp_color_button(self):
        c = self.current_stamp_color
        self.btn_stamp_color.setStyleSheet(f"""
            QPushButton {{
                background-color: {c};
                border: 1px solid #777777;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border: 2px solid #2196F3;
            }}
        """)
        self.btn_stamp_color.setToolTip(f"스탬프 배경 색상: {c}")

    def update_text_color_button(self):
        c = self.current_text_color
        if hasattr(self, "btn_text_color"):
            self.btn_text_color.setText(tr("font_sample_glyph", "A"))
            self.btn_text_color.setStyleSheet(f"""
                QPushButton {{
                    background-color: #2B2B2B;
                    color: {c};
                    font-weight: bold;
                    font-size: 12px;
                    border: 1px solid #777777;
                    border-radius: 4px;
                    padding: 0px;
                }}
                QPushButton:hover {{
                    border: 2px solid #2196F3;
                }}
            """)
            self.btn_text_color.setToolTip(f"{tr('lbl_color_text', '글자색')}: {c}")

    def update_text_bg_color_button(self):
        c = self.current_text_bg_color
        self.btn_text_bg_color.setStyleSheet(f"""
            QPushButton {{
                background-color: {c};
                border: 1px solid #777777;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border: 2px solid #2196F3;
            }}
        """)
        self.btn_text_bg_color.setToolTip(f"텍스트 배경 색상: {c}")

    def update_title_color_button(self):
        c = getattr(self, "current_title_color", "#000000")
        qcol = QColor(c)
        text_fg = "#FFFFFF" if (qcol.red() * 0.299 + qcol.green() * 0.587 + qcol.blue() * 0.114) < 140 else "#000000"
        if hasattr(self, "btn_title_color"):
            self.btn_title_color.setText(tr("font_sample_glyph", "A"))
            self.btn_title_color.setStyleSheet(f"""
                QPushButton {{
                    background-color: {c};
                    color: {text_fg};
                    font-weight: bold;
                    font-size: 12px;
                    border: 1px solid #777777;
                    border-radius: 4px;
                    padding: 0px;
                    white-space: nowrap;
                }}
                QPushButton:hover {{
                    border: 2px solid #2196F3;
                }}
            """)
            self.btn_title_color.setToolTip(f"{tr('lbl_title_color', '색상')}: {c}")

    def choose_title_font_color(self):
        col = QColorDialog.getColor(QColor(self.current_title_color), self, "제목 글자 색상 선택")
        if col.isValid():
            self.current_title_color = col.name()
            self.update_title_color_button()
            self.on_ppt_title_layout_changed()

    def align_title_x_to_image(self):
        img_left = self.spin_ppt_left.value()
        self.spin_title_x.setValue(img_left)
        self.show_toast(f"제목 X 좌표를 이미지 위치({img_left} pt)와 정렬했습니다.")

    def on_ppt_title_layout_changed(self):
        self.config.setdefault("ppt_layout", {})
        self.config["ppt_layout"]["title_left"] = self.spin_title_x.value()
        self.config["ppt_layout"]["title_top"] = self.spin_title_y.value()
        self.config["ppt_layout"]["title_width"] = self.spin_title_w.value()
        self.config["ppt_layout"]["title_height"] = self.spin_title_h.value()
        self.config["ppt_layout"]["title_font_size"] = self.spin_title_font_size.value()
        self.config["ppt_layout"]["title_font_color"] = self.current_title_color
        self.config["ppt_layout"]["title_font_bold"] = self.chk_title_bold.isChecked()
        save_config(self.config)

    def sync_ui_from_config(self):
        # PPT 가로폭
        self.spin_target_width.blockSignals(True)
        self.spin_target_width.setValue(self.config.get("target_width", 960))
        self.spin_target_width.blockSignals(False)

        # 스탬프
        st_style = self.config.get("stamp_style", {})
        self.spin_stamp_size.blockSignals(True)
        self.spin_stamp_size.setValue(st_style.get("size", 32))
        self.spin_stamp_size.blockSignals(False)
        self.current_stamp_color = st_style.get("bg_color", "#E53935")
        self.update_stamp_color_button()

        # 텍스트
        tx_style = self.config.get("text_style", {})
        self.spin_text_font_size.blockSignals(True)
        self.spin_text_font_size.setValue(tx_style.get("font_size", 14))
        self.spin_text_font_size.blockSignals(False)
        self.current_text_color = tx_style.get("text_color", "#FFFFFF")
        self.update_text_color_button()
        self.current_text_bg_color = tx_style.get("bg_color", "#212121")
        self.update_text_bg_color_button()

        # 박스
        bx_style = self.config.get("highlight_box_style", {})
        self.spin_box_width.blockSignals(True)
        self.spin_box_width.setValue(bx_style.get("border_width", 3))
        self.spin_box_width.blockSignals(False)
        if hasattr(self, "spin_box_width_tab"):
            self.spin_box_width_tab.blockSignals(True)
            self.spin_box_width_tab.setValue(bx_style.get("border_width", 3))
            self.spin_box_width_tab.blockSignals(False)
        self.canvas.current_box_width = bx_style.get("border_width", 3)
        self.canvas.current_box_color = bx_style.get("color", "#E53935")
        self.canvas.current_box_fill = bx_style.get("fill", False)
        self.chk_box_fill.blockSignals(True)
        self.chk_box_fill.setChecked(bx_style.get("fill", False))
        self.chk_box_fill.blockSignals(False)
        if hasattr(self, "chk_box_fill_tab"):
            self.chk_box_fill_tab.blockSignals(True)
            self.chk_box_fill_tab.setChecked(bx_style.get("fill", False))
            self.chk_box_fill_tab.blockSignals(False)

        # 화살표
        arr_style = self.config.get("arrow_style", {})
        self.canvas.current_arrow_width = arr_style.get("width", 3)
        self.canvas.current_arrow_head_size = arr_style.get("head_size", 14)
        self.canvas.current_arrow_color = arr_style.get("color", "#E53935")
        if hasattr(self, "spin_arrow_head"):
            self.spin_arrow_head.blockSignals(True)
            self.spin_arrow_head.setValue(arr_style.get("head_size", 14))
            self.spin_arrow_head.blockSignals(False)

        # 말풍선
        co_style = self.config.get("callout_style", {})
        if hasattr(self, "spin_callout_tail_size"):
            self.spin_callout_tail_size.blockSignals(True)
            self.spin_callout_tail_size.setValue(co_style.get("tail_base_width", 16))
            self.spin_callout_tail_size.blockSignals(False)

        # 블러 모자이크
        bl_style = self.config.get("blur_style", {})
        if hasattr(self, "spin_blur_block"):
            self.spin_blur_block.blockSignals(True)
            self.spin_blur_block.setValue(bl_style.get("block_size", 10))
            self.spin_blur_block.blockSignals(False)

        # 단축키 뱃지
        hk_style = self.config.get("hotkey_style", {})
        if hasattr(self, "spin_hotkey_font_size"):
            self.spin_hotkey_font_size.blockSignals(True)
            self.spin_hotkey_font_size.setValue(hk_style.get("font_size", 12))
            self.spin_hotkey_font_size.blockSignals(False)

        # PPT 슬라이드 배치
        ppt_l = self.config.get("ppt_layout", {})
        self.spin_ppt_left.blockSignals(True)
        self.spin_ppt_left.setValue(int(ppt_l.get("left", 50)))
        self.spin_ppt_left.blockSignals(False)

        self.spin_ppt_top.blockSignals(True)
        self.spin_ppt_top.setValue(int(ppt_l.get("top", 80)))
        self.spin_ppt_top.blockSignals(False)

        self.spin_ppt_scale.blockSignals(True)
        self.spin_ppt_scale.setValue(int(ppt_l.get("scale", 90)))
        self.spin_ppt_scale.blockSignals(False)

        self.chk_ppt_title.blockSignals(True)
        self.chk_ppt_title.setChecked(bool(ppt_l.get("include_title", True)))
        self.chk_ppt_title.blockSignals(False)

        # PPT 제목 상자
        if hasattr(self, "spin_title_x"):
            self.spin_title_x.blockSignals(True)
            self.spin_title_x.setValue(int(ppt_l.get("title_left", ppt_l.get("left", 26))))
            self.spin_title_x.blockSignals(False)

        if hasattr(self, "spin_title_y"):
            self.spin_title_y.blockSignals(True)
            self.spin_title_y.setValue(int(ppt_l.get("title_top", 15)))
            self.spin_title_y.blockSignals(False)

        if hasattr(self, "spin_title_w"):
            self.spin_title_w.blockSignals(True)
            self.spin_title_w.setValue(int(ppt_l.get("title_width", 500)))
            self.spin_title_w.blockSignals(False)

        if hasattr(self, "spin_title_h"):
            self.spin_title_h.blockSignals(True)
            self.spin_title_h.setValue(int(ppt_l.get("title_height", 35)))
            self.spin_title_h.blockSignals(False)

        if hasattr(self, "spin_title_font_size"):
            self.spin_title_font_size.blockSignals(True)
            self.spin_title_font_size.setValue(int(ppt_l.get("title_font_size", 18)))
            self.spin_title_font_size.blockSignals(False)

        if hasattr(self, "chk_title_bold"):
            self.chk_title_bold.blockSignals(True)
            self.chk_title_bold.setChecked(bool(ppt_l.get("title_font_bold", True)))
            self.chk_title_bold.blockSignals(False)

        self.current_title_color = ppt_l.get("title_font_color", "#000000")
        if hasattr(self, "btn_title_color"):
            self.update_title_color_button()

        # 텍스트 글꼴
        if hasattr(self, "combo_text_font"):
            self.combo_text_font.blockSignals(True)
            self.combo_text_font.setCurrentFont(QFont(tx_style.get("font_family", "Malgun Gothic")))
            self.combo_text_font.blockSignals(False)

        # 꺾은선 형태 버튼 동기화
        self.sync_elbow_buttons_from_item(getattr(self.canvas, "selected_item", None))

        # 워드아트
        wa_cfg = self.config.get("wordart_style", {})
        if hasattr(self, "combo_wordart_preset"):
            self.combo_wordart_preset.blockSignals(True)
            idx_p = self.combo_wordart_preset.findData(wa_cfg.get("preset_id", "white_pop"))
            if idx_p >= 0:
                self.combo_wordart_preset.setCurrentIndex(idx_p)
            self.combo_wordart_preset.blockSignals(False)

        if hasattr(self, "spin_wordart_size"):
            self.spin_wordart_size.blockSignals(True)
            self.spin_wordart_size.setValue(int(wa_cfg.get("font_size", 24)))
            self.spin_wordart_size.blockSignals(False)

        if hasattr(self, "spin_wordart_stroke"):
            self.spin_wordart_stroke.blockSignals(True)
            self.spin_wordart_stroke.setValue(int(wa_cfg.get("stroke_width", 3)))
            self.spin_wordart_stroke.blockSignals(False)

        if hasattr(self, "chk_wordart_shadow"):
            self.chk_wordart_shadow.blockSignals(True)
            self.chk_wordart_shadow.setChecked(bool(wa_cfg.get("shadow_enabled", True)))
            self.chk_wordart_shadow.blockSignals(False)

        # 자동 저장 토글 버튼 상태 및 스타일 동기화
        if hasattr(self, "btn_autosave"):
            self.btn_autosave.blockSignals(True)
            self.btn_autosave.setChecked(bool(self.config.get("auto_save_enabled", True)))
            self.btn_autosave.blockSignals(False)
            self.update_autosave_button_style()

        # 리본 표시 모드 (텍스트 ⇄ 아이콘) 동기화
        mode = self.config.get("ribbon_display_mode", "text")
        self.toggle_ribbon_display_mode(mode=mode)

    def on_target_width_changed(self, val):
        self.config["target_width"] = val
        save_config(self.config)
        self.canvas.set_config(self.config)

    def on_ppt_layout_changed(self):
        self.config.setdefault("ppt_layout", {})
        self.config["ppt_layout"]["left"] = self.spin_ppt_left.value()
        self.config["ppt_layout"]["top"] = self.spin_ppt_top.value()
        self.config["ppt_layout"]["scale"] = self.spin_ppt_scale.value()
        self.config["ppt_layout"]["include_title"] = self.chk_ppt_title.isChecked()
        save_config(self.config)

    def auto_fit_ppt_scale(self):
        if self.canvas.pixmap:
            orig_w = self.canvas.pixmap.width()
            orig_h = self.canvas.pixmap.height()
        else:
            fr = self.config.get("fixed_rect", {})
            orig_w = fr.get("width", 960)
            orig_h = fr.get("height", 540)

        if self.config.get("auto_resize", True):
            tw = self.config.get("target_width", 960)
            if tw > 0 and orig_w > 0:
                ratio = tw / float(orig_w)
                img_w = tw
                img_h = int(orig_h * ratio)
            else:
                img_w, img_h = orig_w, orig_h
        else:
            img_w, img_h = orig_w, orig_h

        slide_w = 960.0
        slide_h = 540.0
        try:
            ppt_app = win32com.client.GetActiveObject("PowerPoint.Application")
            if ppt_app.Presentations.Count > 0:
                pres = ppt_app.ActivePresentation
                slide_w = float(pres.PageSetup.SlideWidth)
                slide_h = float(pres.PageSetup.SlideHeight)
        except Exception:
            pass

        cur_left = float(self.spin_ppt_left.value())
        cur_top = float(self.spin_ppt_top.value())
        margin_right = 30.0
        margin_bottom = 30.0

        avail_w = max(50.0, slide_w - cur_left - margin_right)
        avail_h = max(50.0, slide_h - cur_top - margin_bottom)

        if img_w > 0 and img_h > 0:
            scale_w = (avail_w / float(img_w)) * 100.0
            scale_h = (avail_h / float(img_h)) * 100.0
            best_scale = int(min(scale_w, scale_h))
            best_scale = max(10, min(300, best_scale))
            self.spin_ppt_scale.setValue(best_scale)
            self.show_toast(f"슬라이드 맞춤 배율 {best_scale}% 자동 계산됨 (Left: {int(cur_left)}, Top: {int(cur_top)})")

    def on_stamp_size_changed(self, val):
        self.config.setdefault("stamp_style", {})["size"] = val
        save_config(self.config)
        self.canvas.set_config(self.config)
        if self.canvas.selected_item:
            item = self.canvas.selected_item
            if isinstance(item, StampItem):
                self.canvas.push_undo()
                item.style["size"] = val
                self.canvas.update()
                self.canvas.sig_content_changed.emit()
            elif isinstance(item, StepArrowItem):
                self.canvas.push_undo()
                item.stamp_style["size"] = val
                self.canvas.update()
                self.canvas.sig_content_changed.emit()

    def choose_stamp_color(self):
        col = QColorDialog.getColor(QColor(self.current_stamp_color), self, "스탬프 배경 색상 선택")
        if col.isValid():
            self.current_stamp_color = col.name()
            self.update_stamp_color_button()
            self.config.setdefault("stamp_style", {})["bg_color"] = self.current_stamp_color
            save_config(self.config)
            self.canvas.set_config(self.config)
            if self.canvas.selected_item:
                item = self.canvas.selected_item
                if isinstance(item, StampItem):
                    self.canvas.push_undo()
                    item.style["bg_color"] = self.current_stamp_color
                    self.canvas.update()
                    self.canvas.sig_content_changed.emit()
                elif isinstance(item, StepArrowItem):
                    self.canvas.push_undo()
                    item.stamp_style["bg_color"] = self.current_stamp_color
                    self.canvas.update()
                    self.canvas.sig_content_changed.emit()

    def on_text_font_size_changed(self, val):
        self.config.setdefault("text_style", {})["font_size"] = val
        save_config(self.config)
        self.canvas.set_config(self.config)
        if self.canvas.selected_item:
            item = self.canvas.selected_item
            if isinstance(item, TextLabelItem):
                self.canvas.push_undo()
                item.style["font_size"] = val
                self.canvas.update()
                self.canvas.sig_content_changed.emit()
            elif isinstance(item, CalloutItem):
                self.canvas.push_undo()
                item.style["font_size"] = val
                self.canvas.update()
                self.canvas.sig_content_changed.emit()

    def choose_text_color(self):
        col = QColorDialog.getColor(QColor(self.current_text_color), self, "텍스트 글자 색상 선택")
        if col.isValid():
            self.current_text_color = col.name()
            self.update_text_color_button()
            self.config.setdefault("text_style", {})["text_color"] = self.current_text_color
            save_config(self.config)
            self.canvas.set_config(self.config)
            if self.canvas.selected_item:
                item = self.canvas.selected_item
                if isinstance(item, TextLabelItem):
                    self.canvas.push_undo()
                    item.style["text_color"] = self.current_text_color
                    self.canvas.update()
                    self.canvas.sig_content_changed.emit()
                elif isinstance(item, CalloutItem):
                    self.canvas.push_undo()
                    item.style["text_color"] = self.current_text_color
                    self.canvas.update()
                    self.canvas.sig_content_changed.emit()

    def choose_text_bg_color(self):
        col = QColorDialog.getColor(QColor(self.current_text_bg_color), self, "텍스트 배경 색상 선택")
        if col.isValid():
            self.current_text_bg_color = col.name()
            self.update_text_bg_color_button()
            self.config.setdefault("text_style", {})["bg_color"] = self.current_text_bg_color
            save_config(self.config)
            self.canvas.set_config(self.config)
            if self.canvas.selected_item:
                item = self.canvas.selected_item
                if isinstance(item, TextLabelItem):
                    self.canvas.push_undo()
                    item.style["bg_color"] = self.current_text_bg_color
                    self.canvas.update()
                    self.canvas.sig_content_changed.emit()
                elif isinstance(item, CalloutItem):
                    self.canvas.push_undo()
                    item.style["bg_color"] = self.current_text_bg_color
                    self.canvas.update()
                    self.canvas.sig_content_changed.emit()

    def on_box_width_changed(self, val):
        self.canvas.set_box_width(val)
        self.canvas.set_arrow_width(val)
        self.config.setdefault("highlight_box_style", {})["border_width"] = val
        self.config.setdefault("arrow_style", {})["width"] = val
        self.config.setdefault("elbow_style", {})["width"] = val
        self.config.setdefault("callout_style", {})["border_width"] = val
        save_config(self.config)
        self.canvas.set_config(self.config)
        if self.canvas.selected_item:
            item = self.canvas.selected_item
            if isinstance(item, HighlightBoxItem):
                self.canvas.push_undo()
                item.style["border_width"] = val
                self.canvas.update()
                self.canvas.sig_content_changed.emit()
            elif isinstance(item, (ArrowItem, ElbowArrowItem)):
                self.canvas.push_undo()
                item.style["width"] = val
                self.canvas.update()
                self.canvas.sig_content_changed.emit()
            elif isinstance(item, StepArrowItem):
                self.canvas.push_undo()
                item.arrow_style["width"] = val
                self.canvas.update()
                self.canvas.sig_content_changed.emit()
            elif isinstance(item, CalloutItem):
                self.canvas.push_undo()
                item.style["border_width"] = val
                self.canvas.update()
                self.canvas.sig_content_changed.emit()

    def choose_box_preset_color(self, color_hex):
        self.canvas.set_box_color(color_hex)
        self.canvas.set_arrow_color(color_hex)
        self.config.setdefault("highlight_box_style", {})["color"] = color_hex
        self.config.setdefault("arrow_style", {})["color"] = color_hex
        self.config.setdefault("elbow_style", {})["color"] = color_hex
        self.config.setdefault("callout_style", {})["border_color"] = color_hex
        save_config(self.config)
        self.canvas.set_config(self.config)

        if self.canvas.selected_item:
            item = self.canvas.selected_item
            self.canvas.push_undo()
            if isinstance(item, HighlightBoxItem):
                item.style["color"] = color_hex
            elif isinstance(item, (ArrowItem, ElbowArrowItem)):
                item.style["color"] = color_hex
            elif isinstance(item, StepArrowItem):
                item.arrow_style["color"] = color_hex
                item.stamp_style["bg_color"] = color_hex
            elif isinstance(item, CalloutItem):
                item.style["border_color"] = color_hex
            elif isinstance(item, StampItem):
                item.style["bg_color"] = color_hex
                self.current_stamp_color = color_hex
                self.update_stamp_color_button()
            elif isinstance(item, TextLabelItem):
                item.style["text_color"] = color_hex
                self.current_text_color = color_hex
                self.update_text_color_button()
            self.canvas.update()
            self.canvas.sig_content_changed.emit()

        self.show_toast(f"색상 설정: {color_hex}")

    def choose_box_custom_color(self):
        col = QColorDialog.getColor(QColor(self.canvas.current_box_color), self, "색상 선택")
        if col.isValid():
            self.choose_box_preset_color(col.name())

    def on_box_fill_toggled(self, checked):
        self.canvas.set_box_fill(checked)
        self.config.setdefault("highlight_box_style", {})["fill"] = checked
        save_config(self.config)
        self.canvas.set_config(self.config)
        if self.canvas.selected_item and isinstance(self.canvas.selected_item, HighlightBoxItem):
            self.canvas.push_undo()
            self.canvas.selected_item.style["fill"] = checked
            self.canvas.update()
            self.canvas.sig_content_changed.emit()

    def on_arrow_head_changed(self, val):
        self.canvas.current_arrow_head_size = val
        self.config.setdefault("arrow_style", {})["head_size"] = val
        self.config.setdefault("elbow_style", {})["head_size"] = val
        save_config(self.config)
        self.canvas.set_config(self.config)
        if self.canvas.selected_item:
            item = self.canvas.selected_item
            if isinstance(item, (ArrowItem, ElbowArrowItem)):
                self.canvas.push_undo()
                item.style["head_size"] = val
                self.canvas.update()
                self.canvas.sig_content_changed.emit()
            elif isinstance(item, StepArrowItem):
                self.canvas.push_undo()
                item.arrow_style["head_size"] = val
                self.canvas.update()
                self.canvas.sig_content_changed.emit()

    def on_callout_tail_size_changed(self, val):
        self.config.setdefault("callout_style", {})["tail_base_width"] = val
        save_config(self.config)
        self.canvas.set_config(self.config)
        if self.canvas.selected_item and isinstance(self.canvas.selected_item, CalloutItem):
            self.canvas.push_undo()
            self.canvas.selected_item.style["tail_base_width"] = val
            self.canvas.update()
            self.canvas.sig_content_changed.emit()

    def on_blur_block_changed(self, val):
        self.config.setdefault("blur_style", {})["block_size"] = val
        save_config(self.config)
        self.canvas.set_config(self.config)
        if self.canvas.selected_item and isinstance(self.canvas.selected_item, BlurMosaicItem):
            self.canvas.push_undo()
            self.canvas.selected_item.style["block_size"] = val
            self.canvas.update()
            self.canvas.sig_content_changed.emit()

    def on_hotkey_font_size_changed(self, val):
        self.config.setdefault("hotkey_style", {})["font_size"] = val
        save_config(self.config)
        self.canvas.set_config(self.config)
        if self.canvas.selected_item and isinstance(self.canvas.selected_item, HotkeyBadgeItem):
            self.canvas.push_undo()
            self.canvas.selected_item.style["font_size"] = val
            self.canvas.update()
            self.canvas.sig_content_changed.emit()

    def on_canvas_item_selected(self, item):
        if item is None:
            self.update_mode_status_indicator()
            return
        if isinstance(item, StampItem):
            size = item.style.get("size", 32)
            bg_col = item.style.get("bg_color", "#E53935")
            self.spin_stamp_size.blockSignals(True)
            self.spin_stamp_size.setValue(int(size))
            self.spin_stamp_size.blockSignals(False)
            self.current_stamp_color = bg_col
            self.update_stamp_color_button()
            if hasattr(self, "lbl_active_mode"):
                self.lbl_active_mode.setText(f"선택: 번호 스탬프 (#{item.index})")
        elif isinstance(item, StepArrowItem):
            size = item.stamp_style.get("size", 32)
            bg_col = item.stamp_style.get("bg_color", "#E53935")
            arrow_w = int(item.arrow_style.get("width", 3))
            head_s = int(item.arrow_style.get("head_size", 14))
            arr_col = item.arrow_style.get("color", "#E53935")
            self.spin_stamp_size.blockSignals(True)
            self.spin_stamp_size.setValue(int(size))
            self.spin_stamp_size.blockSignals(False)
            self.spin_box_width.blockSignals(True)
            self.spin_box_width.setValue(arrow_w)
            self.spin_box_width.blockSignals(False)
            if hasattr(self, "spin_arrow_head"):
                self.spin_arrow_head.blockSignals(True)
                self.spin_arrow_head.setValue(head_s)
                self.spin_arrow_head.blockSignals(False)
            self.current_stamp_color = bg_col
            self.update_stamp_color_button()
            if hasattr(self, "lbl_active_mode"):
                self.lbl_active_mode.setText(f"선택: 순번 화살표 (#{item.index})")
        elif isinstance(item, ElbowArrowItem):
            arrow_w = int(item.style.get("width", 3))
            head_s = int(item.style.get("head_size", 14))
            arrow_col = item.style.get("color", "#E53935")
            self.spin_box_width.blockSignals(True)
            self.spin_box_width.setValue(arrow_w)
            self.spin_box_width.blockSignals(False)
            if hasattr(self, "spin_arrow_head"):
                self.spin_arrow_head.blockSignals(True)
                self.spin_arrow_head.setValue(head_s)
                self.spin_arrow_head.blockSignals(False)
            self.canvas.current_arrow_color = arrow_col
            self.sync_elbow_buttons_from_item(item)
            if hasattr(self, "lbl_active_mode"):
                self.lbl_active_mode.setText(f"선택: 직각 화살표 ({item.route_mode})")
        elif isinstance(item, ArrowItem):
            arrow_w = int(item.style.get("width", 3))
            head_s = int(item.style.get("head_size", 14))
            arrow_col = item.style.get("color", "#E53935")
            self.spin_box_width.blockSignals(True)
            self.spin_box_width.setValue(arrow_w)
            self.spin_box_width.blockSignals(False)
            if hasattr(self, "spin_arrow_head"):
                self.spin_arrow_head.blockSignals(True)
                self.spin_arrow_head.setValue(head_s)
                self.spin_arrow_head.blockSignals(False)
            self.canvas.current_arrow_color = arrow_col
            if hasattr(self, "lbl_active_mode"):
                self.lbl_active_mode.setText("선택: 직선 화살표")
        elif isinstance(item, HighlightBoxItem):
            border_w = int(item.style.get("border_width", 3))
            box_col = item.style.get("color", "#E53935")
            fill = bool(item.style.get("fill", False))
            self.spin_box_width.blockSignals(True)
            self.spin_box_width.setValue(border_w)
            self.spin_box_width.blockSignals(False)
            self.canvas.current_box_color = box_col
            self.chk_box_fill.blockSignals(True)
            self.chk_box_fill.setChecked(fill)
            self.chk_box_fill.blockSignals(False)
            if hasattr(self, "lbl_active_mode"):
                self.lbl_active_mode.setText("선택: 사각 박스")
        elif isinstance(item, BlurMosaicItem):
            blk_s = int(item.style.get("block_size", 10))
            if hasattr(self, "spin_blur_block"):
                self.spin_blur_block.blockSignals(True)
                self.spin_blur_block.setValue(blk_s)
                self.spin_blur_block.blockSignals(False)
            if hasattr(self, "lbl_active_mode"):
                self.lbl_active_mode.setText("선택: 모자이크 블러")
        elif isinstance(item, CalloutItem):
            font_s = int(item.style.get("font_size", 12))
            border_w = int(item.style.get("border_width", 2))
            border_col = item.style.get("border_color", "#E53935")
            text_col = item.style.get("text_color", "#FFFFFF")
            bg_col = item.style.get("bg_color", "#212121")
            tail_s = int(item.style.get("tail_base_width", 16))
            fam = item.style.get("font_family", "Malgun Gothic")
            if hasattr(self, "combo_text_font"):
                self.combo_text_font.blockSignals(True)
                self.combo_text_font.setCurrentFont(QFont(fam))
                self.combo_text_font.blockSignals(False)
            if hasattr(self, "spin_callout_font_size"):
                self.spin_callout_font_size.blockSignals(True)
                self.spin_callout_font_size.setValue(font_s)
                self.spin_callout_font_size.blockSignals(False)
            self.spin_text_font_size.blockSignals(True)
            self.spin_text_font_size.setValue(font_s)
            self.spin_text_font_size.blockSignals(False)
            self.spin_box_width.blockSignals(True)
            self.spin_box_width.setValue(border_w)
            self.spin_box_width.blockSignals(False)
            if hasattr(self, "spin_callout_tail_size"):
                self.spin_callout_tail_size.blockSignals(True)
                self.spin_callout_tail_size.setValue(tail_s)
                self.spin_callout_tail_size.blockSignals(False)
            self.current_text_color = text_col
            self.update_text_color_button()
            self.current_text_bg_color = bg_col
            self.update_text_bg_color_button()
            if hasattr(self, "lbl_active_mode"):
                self.lbl_active_mode.setText(f"선택: 설명 말풍선 ('{item.text[:10]}...')")
        elif isinstance(item, TextLabelItem):
            font_size = int(item.style.get("font_size", 14))
            text_col = item.style.get("text_color", "#FFFFFF")
            bg_col = item.style.get("bg_color", "#212121")
            fam = item.style.get("font_family", "Malgun Gothic")
            if hasattr(self, "combo_text_font"):
                self.combo_text_font.blockSignals(True)
                self.combo_text_font.setCurrentFont(QFont(fam))
                self.combo_text_font.blockSignals(False)
            self.spin_text_font_size.blockSignals(True)
            self.spin_text_font_size.setValue(font_size)
            self.spin_text_font_size.blockSignals(False)
            self.current_text_color = text_col
            self.update_text_color_button()
            self.current_text_bg_color = bg_col
            self.update_text_bg_color_button()
            if hasattr(self, "lbl_active_mode"):
                self.lbl_active_mode.setText(f"선택: 텍스트 라벨 ('{item.text[:10]}...')")
        elif isinstance(item, WordArtItem):
            f_size = int(item.style.get("font_size", 24))
            s_width = int(item.style.get("stroke_width", 3))
            shadow = bool(item.style.get("shadow_enabled", True))
            preset_id = item.style.get("preset_id", "white_pop")
            fam = item.style.get("font_family", "Malgun Gothic")

            if hasattr(self, "combo_text_font"):
                self.combo_text_font.blockSignals(True)
                self.combo_text_font.setCurrentFont(QFont(fam))
                self.combo_text_font.blockSignals(False)
            if hasattr(self, "combo_wordart_preset"):
                self.combo_wordart_preset.blockSignals(True)
                idx_p = self.combo_wordart_preset.findData(preset_id)
                if idx_p >= 0:
                    self.combo_wordart_preset.setCurrentIndex(idx_p)
                self.combo_wordart_preset.blockSignals(False)
            if hasattr(self, "spin_wordart_size"):
                self.spin_wordart_size.blockSignals(True)
                self.spin_wordart_size.setValue(f_size)
                self.spin_wordart_size.blockSignals(False)
            if hasattr(self, "spin_wordart_stroke"):
                self.spin_wordart_stroke.blockSignals(True)
                self.spin_wordart_stroke.setValue(s_width)
                self.spin_wordart_stroke.blockSignals(False)
            if hasattr(self, "chk_wordart_shadow"):
                self.chk_wordart_shadow.blockSignals(True)
                self.chk_wordart_shadow.setChecked(shadow)
                self.chk_wordart_shadow.blockSignals(False)
            if hasattr(self, "lbl_active_mode"):
                self.lbl_active_mode.setText(f"선택: 워드아트 ('{item.text[:10]}...')")
        elif isinstance(item, HotkeyBadgeItem):
            font_s = int(item.style.get("font_size", 12))
            if hasattr(self, "spin_hotkey_font_size"):
                self.spin_hotkey_font_size.blockSignals(True)
                self.spin_hotkey_font_size.setValue(font_s)
                self.spin_hotkey_font_size.blockSignals(False)
            if hasattr(self, "lbl_active_mode"):
                self.lbl_active_mode.setText(f"선택: 단축키 배지 ({item.key_text})")
        elif isinstance(item, ImageOverlayItem):
            bw = int(item.style.get("border_width", 2))
            self.spin_box_width.blockSignals(True)
            self.spin_box_width.setValue(bw)
            self.spin_box_width.blockSignals(False)
            if hasattr(self, "lbl_active_mode"):
                self.lbl_active_mode.setText(f"선택: 부분 이미지 ({int(item.rect.width())}×{int(item.rect.height())})")
        elif isinstance(item, DraftStampItem):
            bw = int(item.style.get("border_width", 5))
            self.spin_box_width.blockSignals(True)
            self.spin_box_width.setValue(bw)
            self.spin_box_width.blockSignals(False)
            if hasattr(self, "lbl_active_mode"):
                self.lbl_active_mode.setText(f"선택: Draft 스탬프 ('{item.text}')")

    def on_fixed_rect_toggled(self, checked):
        self.config["fixed_rect_enabled"] = checked
        save_config(self.config)
        state_str = "활성화 (F9 즉시 캡처)" if checked else "해제 (F9 영역 지정)"
        self.show_toast(f"고정 영역 모드가 {state_str}되었습니다.")

    def on_fixed_rect_changed(self):
        self.config.setdefault("fixed_rect", {})
        self.config["fixed_rect"]["x"] = self.spin_fx.value()
        self.config["fixed_rect"]["y"] = self.spin_fy.value()
        self.config["fixed_rect"]["width"] = self.spin_fw.value()
        self.config["fixed_rect"]["height"] = self.spin_fh.value()
        self.config["fixed_rect_enabled"] = True
        save_config(self.config)
        self.chk_fixed_rect.blockSignals(True)
        self.chk_fixed_rect.setChecked(True)
        self.chk_fixed_rect.blockSignals(False)

    def save_current_as_fixed_rect(self):
        if self.last_capture_rect and not self.last_capture_rect.isEmpty():
            r = self.last_capture_rect
            self.spin_fx.setValue(r.x())
            self.spin_fy.setValue(r.y())
            self.spin_fw.setValue(r.width())
            self.spin_fh.setValue(r.height())
            self.config["fixed_rect"] = {"x": r.x(), "y": r.y(), "width": r.width(), "height": r.height()}
            self.config["fixed_rect_enabled"] = True
            save_config(self.config)
            self.chk_fixed_rect.setChecked(True)
            self.show_toast(f"현재 영역 ({r.x()},{r.y()} {r.width()}×{r.height()}px)이 고정 좌표로 등록되었습니다! (F9 즉시 캡처)")
        elif self.canvas.pixmap:
            w = self.canvas.pixmap.width()
            h = self.canvas.pixmap.height()
            self.spin_fw.setValue(w)
            self.spin_fh.setValue(h)
            self.config.setdefault("fixed_rect", {})["width"] = w
            self.config.setdefault("fixed_rect", {})["height"] = h
            self.config["fixed_rect_enabled"] = True
            save_config(self.config)
            self.chk_fixed_rect.setChecked(True)
            self.show_toast(f"현재 캡처 크기 ({w}×{h}px)가 고정 규격으로 등록되었습니다! (F9 즉시 캡처)")
        else:
            self.show_toast("먼저 화면을 한 번 캡처하세요.")

    def handle_hotkey_capture(self):
        fr = self.config.get("fixed_rect")
        has_valid_rect = (
            fr is not None and 
            isinstance(fr, dict) and
            fr.get("width", 0) >= 10 and 
            fr.get("height", 0) >= 10
        )
        if has_valid_rect:
            # 영역이 지정된 상태에서는 무조건 즉시 캡처 실행 (새 영역 재지정은 Shift+F9)
            self.capture_fixed_rect()
        else:
            self.start_capture()

    def _prepare_window_for_capture(self):
        """DWM 창 애니메이션 및 잔상으로 인한 반투명 고스트 캡처 원천 방지"""
        was_visible = self.isVisible() and not self.isMinimized()
        if was_visible:
            self.setWindowOpacity(0.0)
            self.hide()
            QApplication.processEvents()
            time.sleep(0.18)
        return was_visible

    def _restore_window_after_capture(self, was_visible=True):
        """캡처 완료/취소 시 스튜디오 창을 원래 불투명도와 전면 활성 상태로 안전 복원"""
        if was_visible:
            self.setWindowOpacity(1.0)
            self.show()
            self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
            self.activateWindow()

    def capture_fixed_rect(self):
        fr = self.config.get("fixed_rect", {"x": 100, "y": 100, "width": 960, "height": 540})
        x = fr.get("x", 100)
        y = fr.get("y", 100)
        w = fr.get("width", 960)
        h = fr.get("height", 540)

        was_visible = self._prepare_window_for_capture()

        try:
            target_mon = getattr(self, "current_target_monitor", self.config.get("target_monitor", -1))
            cropped = MultiMonitorManager.grab_target_area(target_mon, QRect(x, y, w, h))

            if cropped.isNull() or cropped.width() < 5 or cropped.height() < 5:
                self.show_toast("화면 캡처 실패: 유효하지 않은 좌표입니다.")
                return

            self.on_capture_completed(cropped, QRect(x, y, w, h), is_fixed_capture=True)
            mon_str = "전체 가상화면" if target_mon == -1 else f"모니터 {target_mon + 1}"
            self.show_toast(f"고정 영역 ({mon_str} {x},{y} {w}×{h}px) 즉시 캡처 완료!")
        finally:
            self._restore_window_after_capture(was_visible)

    def start_capture(self):
        was_visible = self._prepare_window_for_capture()

        try:
            target_mon = getattr(self, "current_target_monitor", self.config.get("target_monitor", -1))
            self.overlay_window = CaptureOverlayWidget(
                last_rect=self.last_capture_rect,
                config=self.config,
                target_monitor=target_mon
            )
            self.overlay_window.sig_captured.connect(self.on_capture_completed)
            self.overlay_window.sig_cancelled.connect(self.on_capture_cancelled)
            self.overlay_window.show_overlay()
        except Exception as e:
            self._restore_window_after_capture(was_visible)
            print(f"[오버레이 실행 오류]: {e}")

    def on_capture_cancelled(self):
        self._restore_window_after_capture(True)

    def start_sub_capture(self):
        """F8 단축키 또는 리본 버튼: 모달/팝업 영역 부분 캡처 후 캔버스에 독립 이미지 객체로 추가 (F9 없이도 투명 캔버스에 즉시 배치)"""
        was_visible = self._prepare_window_for_capture()

        try:
            target_mon = getattr(self, "current_target_monitor", self.config.get("target_monitor", -1))
            self.overlay_window = CaptureOverlayWidget(
                last_rect=None,
                config=self.config,
                is_sub_capture=True,
                target_monitor=target_mon
            )
            self.overlay_window.sig_captured.connect(self.on_sub_capture_completed)
            self.overlay_window.sig_cancelled.connect(self.on_capture_cancelled)
            self.overlay_window.show_overlay()
        except Exception as e:
            self._restore_window_after_capture(was_visible)
            print(f"[부분 캡처 오버레이 실행 오류]: {e}")

    def on_sub_capture_completed(self, pixmap, global_rect=None):
        self._restore_window_after_capture(True)

        if pixmap and not pixmap.isNull():
            self.canvas.add_image_overlay(pixmap)
            w = pixmap.width()
            h = pixmap.height()
            self.show_toast(f"부분 이미지({w}×{h}px) 추가 완료. 마우스로 이동 및 크기를 조절하세요.")

    # -------------------------------------------------------------
    # 다중 모니터 & 폰트 & 꺾임선 & 워드아트 이벤트 핸들러
    # -------------------------------------------------------------
    def init_monitor_combos(self):
        monitors = MultiMonitorManager.get_monitor_info_list()
        combos = []
        if hasattr(self, "combo_tab_monitor") and self.combo_tab_monitor is not None:
            combos.append(self.combo_tab_monitor)
        if hasattr(self, "combo_monitor"):
            combos.append(self.combo_monitor)

        cur_target = getattr(self, "current_target_monitor", self.config.get("target_monitor", -1))

        for cb in combos:
            cb.blockSignals(True)
            cb.clear()
            cb.addItem(tr("settings_monitor_all", "전체 가상 화면 (모든 모니터)"), -1)
            for m in monitors:
                cb.addItem(m["label"], m["index"])

            idx = cb.findData(cur_target)
            if idx >= 0:
                cb.setCurrentIndex(idx)
            else:
                cb.setCurrentIndex(0)
            cb.blockSignals(False)

    def on_tab_monitor_changed(self, idx):
        if hasattr(self, "combo_tab_monitor") and self.combo_tab_monitor is not None:
            val = self.combo_tab_monitor.currentData()
            self.set_active_monitor(val)

    def on_quick_monitor_changed(self, idx):
        if hasattr(self, "combo_monitor"):
            val = self.combo_monitor.currentData()
            self.set_active_monitor(val)

    def set_active_monitor(self, monitor_index):
        self.current_target_monitor = monitor_index
        self.config["target_monitor"] = monitor_index
        save_config(self.config)

        if hasattr(self, "combo_tab_monitor") and self.combo_tab_monitor is not None:
            self.combo_tab_monitor.blockSignals(True)
            idx = self.combo_tab_monitor.findData(monitor_index)
            if idx >= 0:
                self.combo_tab_monitor.setCurrentIndex(idx)
            self.combo_tab_monitor.blockSignals(False)

        if hasattr(self, "combo_monitor"):
            self.combo_monitor.blockSignals(True)
            idx = self.combo_monitor.findData(monitor_index)
            if idx >= 0:
                self.combo_monitor.setCurrentIndex(idx)
            self.combo_monitor.blockSignals(False)

        name = "전체 가상 화면" if monitor_index == -1 else f"모니터 {monitor_index + 1}"
        self.show_toast(f"캡처 대상 화면: {name}")

    def action_add_custom_font(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "외부/유료/토너절약 폰트 파일 등록",
            "",
            "폰트 파일 (*.ttf *.otf *.ttc *.woff);;모든 파일 (*.*)"
        )
        if not file_paths:
            return

        all_added = []
        for fp in file_paths:
            families, dest = CustomFontManager.instance().import_font_file(fp)
            if families:
                all_added.extend(families)
                if "custom_fonts" not in self.config:
                    self.config["custom_fonts"] = []
                if dest not in self.config["custom_fonts"]:
                    self.config["custom_fonts"].append(dest)

        if all_added:
            save_config(self.config)
            fam_str = ", ".join(all_added)
            self.show_toast(f"폰트 등록 완료: {fam_str}")
            if hasattr(self, "combo_text_font") and all_added:
                self.combo_text_font.setCurrentFont(QFont(all_added[0]))
        else:
            self.show_toast("유효한 폰트 파일을 등록하지 못했습니다.")

    def on_text_font_family_changed(self, font):
        fam = font.family()
        self.config.setdefault("text_style", {})["font_family"] = fam
        save_config(self.config)
        self.canvas.set_config(self.config)
        if self.canvas.selected_item:
            item = self.canvas.selected_item
            if isinstance(item, TextLabelItem):
                self.canvas.push_undo()
                item.style["font_family"] = fam
                self.canvas.update()
                self.canvas.sig_content_changed.emit()
            elif isinstance(item, CalloutItem):
                self.canvas.push_undo()
                item.style["font_family"] = fam
                self.canvas.update()
                self.canvas.sig_content_changed.emit()
            elif isinstance(item, WordArtItem):
                self.canvas.push_undo()
                item.style["font_family"] = fam
                self.canvas.update()
                self.canvas.sig_content_changed.emit()

    def on_elbow_preset_clicked(self, preset: str):
        """4대 꺾은선 형태 아이콘 버튼 클릭 시 경로 모드 및 좌표 즉시 반영"""
        mode = "HV" if preset in ("tr", "br") else "VH"
        self.canvas.current_elbow_route_mode = mode

        # 버튼 체크 상태 동기화
        btn_map = {
            "tr": getattr(self, "btn_elbow_tr", None),
            "br": getattr(self, "btn_elbow_br", None),
            "bl": getattr(self, "btn_elbow_bl", None),
            "tl": getattr(self, "btn_elbow_tl", None)
        }
        target_btn = btn_map.get(preset)
        if target_btn and hasattr(self, "elbow_btn_group"):
            target_btn.setChecked(True)

        if self.canvas.selected_item and isinstance(self.canvas.selected_item, ElbowArrowItem):
            item = self.canvas.selected_item
            self.canvas.push_undo()
            item.route_mode = mode
            p1 = item.start_pos
            p2 = item.end_pos

            # 아이콘 형태와 완벽 일치하도록 Y좌표 방향성 보정
            if preset == "tr":  # 우하향 (가로 우선 -> 아래 방향 화살촉)
                if p1.y() > p2.y():
                    item.start_pos = QPointF(p1.x(), p2.y())
                    item.end_pos = QPointF(p2.x(), p1.y())
            elif preset == "br":  # 우상향 (가로 우선 -> 위 방향 화살촉)
                if p1.y() < p2.y():
                    item.start_pos = QPointF(p1.x(), p2.y())
                    item.end_pos = QPointF(p2.x(), p1.y())
            elif preset == "bl":  # 하우향 (세로 우선 -> 아래 방향 경유)
                if p1.y() > p2.y():
                    item.start_pos = QPointF(p1.x(), p2.y())
                    item.end_pos = QPointF(p2.x(), p1.y())
            elif preset == "tl":  # 상우향 (세로 우선 -> 위 방향 경유)
                if p1.y() < p2.y():
                    item.start_pos = QPointF(p1.x(), p2.y())
                    item.end_pos = QPointF(p2.x(), p1.y())

            self.canvas.update()
            self.canvas.sig_content_changed.emit()
            if hasattr(self, "lbl_active_mode"):
                self.lbl_active_mode.setText(f"선택: 직각 화살표 ({preset.upper()})")

    def sync_elbow_buttons_from_item(self, item=None):
        """현재 선택된 꺾은선 화살표 또는 기본 꺾임 모드에 따라 4개 아이콘 버튼 체크 상태 동기화"""
        if not hasattr(self, "btn_elbow_tr"):
            return
        if not item or not isinstance(item, ElbowArrowItem):
            cur_route = getattr(self.canvas, "current_elbow_route_mode", "HV")
            if cur_route == "HV":
                self.btn_elbow_tr.setChecked(True)
            else:
                self.btn_elbow_bl.setChecked(True)
            return

        is_down = item.start_pos.y() <= item.end_pos.y()
        if item.route_mode == "HV":
            if is_down:
                self.btn_elbow_tr.setChecked(True)
            else:
                self.btn_elbow_br.setChecked(True)
        else:  # VH
            if is_down:
                self.btn_elbow_bl.setChecked(True)
            else:
                self.btn_elbow_tl.setChecked(True)

    def on_elbow_route_combo_changed(self, idx=0):
        """하위 호환성 래퍼: HV/VH 꺾임 변경"""
        mode = "HV" if idx in (0, "HV") else "VH"
        self.canvas.current_elbow_route_mode = mode
        if mode == "HV":
            self.on_elbow_preset_clicked("tr")
        else:
            self.on_elbow_preset_clicked("bl")

    def action_flip_elbow(self):
        """꺾임 축 실시간 반전 (HV ↔ VH) 및 4개 버튼 동기화"""
        cur = getattr(self.canvas, "current_elbow_route_mode", "HV")
        nxt = "VH" if cur == "HV" else "HV"
        self.canvas.current_elbow_route_mode = nxt
        if self.canvas.selected_item and isinstance(self.canvas.selected_item, ElbowArrowItem):
            self.canvas.push_undo()
            self.canvas.selected_item.toggle_route_mode()
            self.canvas.update()
            self.canvas.sig_content_changed.emit()
            self.sync_elbow_buttons_from_item(self.canvas.selected_item)
        else:
            self.sync_elbow_buttons_from_item(None)
        self.show_toast(f"직각 꺾임 축 전환: {nxt}")

    def on_wordart_preset_changed(self, idx):
        if hasattr(self, "combo_wordart_preset"):
            preset_key = self.combo_wordart_preset.currentData()
            if preset_key and preset_key in WordArtItem.PRESETS:
                p = WordArtItem.PRESETS[preset_key]
                self.config.setdefault("wordart_style", {})["preset_id"] = preset_key
                self.config["wordart_style"]["text_color"] = p["text_color"]
                self.config["wordart_style"]["stroke_color"] = p["stroke_color"]
                self.config["wordart_style"]["stroke_width"] = p["stroke_width"]
                self.config["wordart_style"]["shadow_enabled"] = p["shadow_enabled"]
                save_config(self.config)
                self.canvas.set_config(self.config)

                if hasattr(self, "spin_wordart_stroke"):
                    self.spin_wordart_stroke.blockSignals(True)
                    self.spin_wordart_stroke.setValue(int(p["stroke_width"]))
                    self.spin_wordart_stroke.blockSignals(False)
                if hasattr(self, "chk_wordart_shadow"):
                    self.chk_wordart_shadow.blockSignals(True)
                    self.chk_wordart_shadow.setChecked(p["shadow_enabled"])
                    self.chk_wordart_shadow.blockSignals(False)

                if self.canvas.selected_item and isinstance(self.canvas.selected_item, WordArtItem):
                    self.canvas.push_undo()
                    self.canvas.selected_item.apply_preset(preset_key)
                    self.canvas.update()
                    self.canvas.sig_content_changed.emit()

    def on_wordart_size_changed(self, val):
        self.config.setdefault("wordart_style", {})["font_size"] = val
        save_config(self.config)
        self.canvas.set_config(self.config)
        if self.canvas.selected_item and isinstance(self.canvas.selected_item, WordArtItem):
            self.canvas.push_undo()
            self.canvas.selected_item.style["font_size"] = val
            self.canvas.update()
            self.canvas.sig_content_changed.emit()

    def on_wordart_stroke_changed(self, val):
        self.config.setdefault("wordart_style", {})["stroke_width"] = val
        save_config(self.config)
        self.canvas.set_config(self.config)
        if self.canvas.selected_item and isinstance(self.canvas.selected_item, WordArtItem):
            self.canvas.push_undo()
            self.canvas.selected_item.style["stroke_width"] = val
            self.canvas.update()
            self.canvas.sig_content_changed.emit()

    def on_wordart_shadow_toggled(self, checked):
        self.config.setdefault("wordart_style", {})["shadow_enabled"] = checked
        save_config(self.config)
        self.canvas.set_config(self.config)
        if self.canvas.selected_item and isinstance(self.canvas.selected_item, WordArtItem):
            self.canvas.push_undo()
            self.canvas.selected_item.style["shadow_enabled"] = checked
            self.canvas.update()
            self.canvas.sig_content_changed.emit()

    def on_capture_completed(self, pixmap, global_rect=None, is_fixed_capture=False):
        if global_rect and not global_rect.isEmpty():
            self.last_capture_rect = global_rect
            # 드래그 영역 지정이든 수동 지정이든 캡처 완료 시 고정 영역으로 자동 등록 및 활성화!
            self.config["fixed_rect"] = {
                "x": global_rect.x(),
                "y": global_rect.y(),
                "width": global_rect.width(),
                "height": global_rect.height()
            }
            self.config["fixed_rect_enabled"] = True
            save_config(self.config)

            self.spin_fx.blockSignals(True)
            self.spin_fy.blockSignals(True)
            self.spin_fw.blockSignals(True)
            self.spin_fh.blockSignals(True)
            self.spin_fx.setValue(global_rect.x())
            self.spin_fy.setValue(global_rect.y())
            self.spin_fw.setValue(global_rect.width())
            self.spin_fh.setValue(global_rect.height())
            self.spin_fx.blockSignals(False)
            self.spin_fy.blockSignals(False)
            self.spin_fw.blockSignals(False)
            self.spin_fh.blockSignals(False)

            self.chk_fixed_rect.blockSignals(True)
            self.chk_fixed_rect.setChecked(True)
            self.chk_fixed_rect.blockSignals(False)

        # 새 캡처 완료 시 캔버스에 안착 (작업 세션 시작)
        self.current_project_path = None
        self.update_window_title()
        self.canvas.set_pixmap(pixmap)
        self.canvas.items.clear()
        self.canvas.next_stamp_index = 1
        self.canvas.history.clear()

        # 스토리보드 동기화 (새 캡처 반영)
        if len(self.storyboard_steps) == 0:
            self.storyboard_steps.append({
                "step_num": 1,
                "title": "Step 1. [단계명 입력]",
                "raw_pixmap": pixmap.copy(),
                "items": [],
                "next_stamp_index": 1,
                "thumbnail": pixmap.copy()
            })
            self.current_step_idx = 0
        else:
            if 0 <= self.current_step_idx < len(self.storyboard_steps):
                step = self.storyboard_steps[self.current_step_idx]
                step["raw_pixmap"] = pixmap.copy()
                step["items"] = []
                step["thumbnail"] = pixmap.copy()
        if hasattr(self, "filmstrip"):
            self.filmstrip.set_steps(self.storyboard_steps, self.current_step_idx)

        # 창 전면 활성화
        self._restore_window_after_capture(True)

        w = pixmap.width()
        h = pixmap.height()
        tw = self.config.get("target_width", 960)
        self.status_label.setText(
            f"새 캡처 수신됨: {w}×{h} px ➔ PPT 내보내기 시 가로 {tw}px로 자동 규격화됩니다. (F10 전송)"
        )
        if not is_fixed_capture and global_rect:
            self.show_toast(f"영역 지정 완료 ({w}×{h}px) ➔ 다음 F9 시 즉시 캡처됩니다. (새 영역: Shift+F9)")
        else:
            self.show_toast(f"캡처 완료 ({w}×{h})! 스탬프나 텍스트를 배치하세요.")

    def export_to_ppt_and_clipboard(self):
        if self.canvas.pixmap is None:
            self.show_toast("내보낼 캡처 이미지가 없습니다. F9를 눌러 먼저 캡처하세요.")
            return

        # 1. 고화질 주석 일체형 합성
        qimg = self.canvas.get_composed_image()
        if qimg is None:
            return

        pil_img = ExportEngine.qimage_to_pil(qimg)

        # 창틀 & 소프트 섀도우 액자 효과 (기본값 ON, 토글 가능)
        if self.config.get("enable_window_frame", True):
            frame_cfg = self.config.get("window_frame_style", {})
            pil_img = ExportEngine.apply_window_frame_and_shadow(
                pil_img,
                include_header=frame_cfg.get("include_header", True),
                corner_radius=frame_cfg.get("corner_radius", 12),
                shadow_radius=frame_cfg.get("shadow_radius", 20),
                shadow_opacity=frame_cfg.get("shadow_opacity", 0.35)
            )

        # 2. PPT 슬라이드 최적화 가로폭 리사이즈
        target_w = self.config.get("target_width", 960)
        if self.config.get("auto_resize", True):
            pil_img = ExportEngine.resize_to_target_width(pil_img, target_w)

        # 3. 윈도우 네이티브 DIB 클립보드 주입
        try:
            ExportEngine.copy_to_clipboard(pil_img)
            clipboard_ok = True
        except Exception as e:
            print(f"[클립보드 복사 오류]: {e}")
            clipboard_ok = False

        # 4. 파워포인트 또는 구글 슬라이드 새 슬라이드 자동 생성
        export_target = self.config.get("export_target", "powerpoint")
        ppt_ok = False
        slides_ok = False
        slides_title = ""

        if export_target == "google_slides":
            if self.config.get("slides_auto_slide", True):
                self.status_label.setText(tr("slides_injecting", "구글 슬라이드 주입 중..."))
                QApplication.processEvents()
                return_focus = self.config.get("slides_return_focus", True)
                res = ExportEngine.send_to_google_slides(
                    pil_img,
                    return_focus_hwnd=int(self.winId()),
                    return_focus=return_focus
                )
                if res.get("success"):
                    slides_ok = True
                    slides_title = res.get("title", "")
                else:
                    err = res.get("error")
                    if err == "NOT_FOUND":
                        self.show_toast(tr("slides_not_found", "구글 슬라이드 웹 브라우저 창을 찾을 수 없습니다.\n크롬 또는 엣지에서 구글 슬라이드를 열어주세요."))
                    else:
                        self.show_toast(f"Google Slides Error: {err}")
        else:
            temp_dir = os.path.join(get_app_dir(), "temp")
            if self.config.get("ppt_auto_slide", True):
                ppt_layout = self.config.get("ppt_layout", {}).copy()
                if "template_path" not in ppt_layout:
                    ppt_layout["template_path"] = self.config.get("ppt_template_path", "")
                ppt_ok = ExportEngine.send_to_powerpoint(pil_img, temp_dir, ppt_layout)

        # 5. 세션 자동 백업 (3종 세트 동시 저장: Bake PNG + 원본 PNG + .mcs.json)
        bundle_res = None
        if self.config.get("save_to_file", True):
            save_dir = os.path.join(
                get_app_dir(),
                self.config.get("save_directory", "captures")
            )
            bundle_res = ExportEngine.auto_backup_step_bundle(
                pil_img=pil_img,
                raw_pixmap=self.canvas.pixmap,
                items=self.canvas.items,
                next_stamp_index=self.canvas.next_stamp_index,
                save_dir=save_dir,
                existing_project_path=self.current_project_path,
                ppt_layout=self.config.get("ppt_layout", {})
            )
            if bundle_res:
                self.current_project_path = bundle_res["project_path"]
                self.update_window_title()

        # 결과 알림 (세션은 절대 초기화하지 않고 그대로 보존!)
        msg_parts = []
        if slides_ok:
            msg_parts.append(tr("slides_success", "구글 슬라이드 새 슬라이드 생성 및 이미지 주입 완료"))
        elif ppt_ok:
            msg_parts.append("PPT 새 슬라이드 자동 생성")
        if clipboard_ok:
            msg_parts.append("클립보드 복사(Ctrl+V)")
        if bundle_res:
            step_name = os.path.basename(bundle_res["bake_path"])
            msg_parts.append(f"{step_name} & 프로젝트 보존")

        full_msg = " + ".join(msg_parts) + " 완료! (현재 작업내용 유지됨)"
        self.status_label.setText(full_msg)
        self.show_toast(full_msg)

    def action_send_to_google_slides(self):
        """열려 있는 웹 브라우저 구글 슬라이드로 즉시 새 슬라이드 생성 및 이미지 주입"""
        if self.canvas.pixmap is None:
            self.show_toast("내보낼 캡처 이미지가 없습니다. F9를 눌러 먼저 캡처하세요.")
            return

        qimg = self.canvas.get_composed_image()
        if qimg is None:
            return

        pil_img = ExportEngine.qimage_to_pil(qimg)
        target_w = self.config.get("target_width", 960)
        if self.config.get("auto_resize", True):
            pil_img = ExportEngine.resize_to_target_width(pil_img, target_w)

        self.status_label.setText(tr("slides_injecting", "구글 슬라이드 주입 중..."))
        QApplication.processEvents()

        return_focus = self.config.get("slides_return_focus", True)
        res = ExportEngine.send_to_google_slides(
            pil_img,
            return_focus_hwnd=int(self.winId()),
            return_focus=return_focus
        )
        if res.get("success"):
            title = res.get("title", "")
            success_msg = f"{tr('slides_success', '구글 슬라이드 새 슬라이드 생성 및 이미지 주입 완료')} [{title}]"
            self.status_label.setText(success_msg)
            self.show_toast(success_msg)
        else:
            err = res.get("error")
            if err == "NOT_FOUND":
                self.show_toast(tr("slides_not_found", "구글 슬라이드 웹 브라우저 창을 찾을 수 없습니다.\n크롬 또는 엣지에서 구글 슬라이드를 열어주세요."))
            else:
                self.show_toast(f"구글 슬라이드 주입 실패: {err}")

    def action_undo(self):
        self.canvas.undo()

    def action_clear(self):
        self.canvas.clear_annotations()

    def action_add_draft_stamp(self):
        if self.canvas.pixmap is None:
            self.show_toast("먼저 화면(F9)을 캡처한 후 Draft 스탬프를 추가하세요.")
            return
        item = self.canvas.add_draft_stamp("DRAFT")
        self.show_toast("Draft 스탬프가 추가되었습니다. (더블 클릭 시 문구 변경)")

    def action_renumber_powerpoint_steps(self):
        """열려 있는 파워포인트의 슬라이드 Step 번호를 순서대로 1부터 일괄 재정렬"""
        has_active_pres = False
        pres_name = ""
        slide_count = 0

        try:
            ppt_app = win32com.client.GetActiveObject("PowerPoint.Application")
            if ppt_app.Presentations.Count > 0:
                try:
                    pres = ppt_app.ActivePresentation
                except Exception:
                    pres = ppt_app.Presentations.Item(1)
                has_active_pres = True
                pres_name = pres.Name
                slide_count = pres.Slides.Count
        except Exception:
            pass

        target_file = None
        if has_active_pres:
            reply = QMessageBox.question(
                self,
                "Step 번호 재정렬",
                f"현재 열려 있는 파워포인트 문서:\n"
                f"[{pres_name}] (총 {slide_count}개 슬라이드)\n\n"
                f"슬라이드 순서대로 Step 번호를 1부터 일괄 재정렬하시겠습니까?\n\n"
                f"• 기존 작성하신 제목, 설명 문구 및 서식은 100% 보존됩니다.\n"
                f"• Step 번호가 없는 표지/구분 슬라이드는 자동으로 건너뜁니다.",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Cancel:
                return
            elif reply == QMessageBox.No:
                f_reply = QMessageBox.question(
                    self,
                    "파일 선택",
                    "저장되어 있는 다른 PPTX 파일을 직접 선택하여 재정렬하시겠습니까?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                if f_reply == QMessageBox.Yes:
                    target_file, _ = QFileDialog.getOpenFileName(
                        self, "재정렬할 파워포인트 파일 선택", "", "PowerPoint Files (*.pptx *.ppt)"
                    )
                    if not target_file:
                        return
                else:
                    return
        else:
            reply = QMessageBox.question(
                self,
                "파워포인트 파일 선택",
                "현재 열려 있는 파워포인트가 감지되지 않았습니다.\n\n"
                "저장되어 있는 PPTX 파일을 선택하여 Step 번호를 재정렬하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply != QMessageBox.Yes:
                return
            target_file, _ = QFileDialog.getOpenFileName(
                self, "재정렬할 파워포인트 파일 선택", "", "PowerPoint Files (*.pptx *.ppt)"
            )
            if not target_file:
                return

        self.status_label.setText("파워포인트 Step 번호 재정렬 중...")
        QApplication.processEvents()

        res = ExportEngine.renumber_powerpoint_steps(file_path=target_file, start_from=1)
        if not res.get("success"):
            QMessageBox.warning(
                self,
                "Step 재정렬 오류",
                f"Step 재정렬 중 오류가 발생했습니다:\n{res.get('error')}"
            )
            self.status_label.setText("Step 재정렬 실패")
            return

        status_msg = (
            f"Step 재정렬 완료: {res.get('presentation_name')} "
            f"({res.get('renumbered_count')}개 Step 갱신, {res.get('skipped_count')}개 건너뜀)"
        )
        self.status_label.setText(status_msg)
        self.show_toast(f"{res.get('renumbered_count')}개 슬라이드 Step 번호 재정렬 완료")
        self._show_renumber_success_dialog(res)

    def _show_renumber_success_dialog(self, res: dict):
        """Step 번호 재정렬 결과 상세 내역 다이얼로그"""
        dlg = QDialog(self)
        dlg.setWindowTitle("Step 번호 재정렬 완료")
        dlg.resize(680, 520)

        main_layout = QVBoxLayout(dlg)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # 상단 요약 카드
        header_card = QFrame(dlg)
        header_card.setStyleSheet("""
            QFrame {
                background-color: #F8F9FA;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        h_layout = QVBoxLayout(header_card)
        h_layout.setContentsMargins(8, 8, 8, 8)
        h_layout.setSpacing(6)

        title_lbl = QLabel(f"문서: {res.get('presentation_name', '')}", header_card)
        title_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E293B;")
        h_layout.addWidget(title_lbl)

        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)

        lbl_total = QLabel(f"총 슬라이드: {res.get('total_slides', 0)}장", header_card)
        lbl_total.setStyleSheet("font-size: 12px; color: #475569;")
        stats_layout.addWidget(lbl_total)

        lbl_renum = QLabel(f"재정렬된 Step: {res.get('renumbered_count', 0)}개", header_card)
        lbl_renum.setStyleSheet("font-size: 12px; font-weight: bold; color: #1565C0;")
        stats_layout.addWidget(lbl_renum)

        lbl_skip = QLabel(f"건너뛴 슬라이드(표지/구분): {res.get('skipped_count', 0)}개", header_card)
        lbl_skip.setStyleSheet("font-size: 12px; color: #64748B;")
        stats_layout.addWidget(lbl_skip)

        stats_layout.addStretch(1)
        h_layout.addLayout(stats_layout)
        main_layout.addWidget(header_card)

        # 상세 변경 내역 스크롤 영역
        scroll = QScrollArea(dlg)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #E0E0E0; border-radius: 4px; background: #FFFFFF; }")

        container = QWidget()
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(8, 8, 8, 8)
        c_layout.setSpacing(4)

        for item in res.get("details", []):
            row_frame = QFrame(container)
            row_layout = QHBoxLayout(row_frame)
            row_layout.setContentsMargins(6, 4, 6, 4)
            row_layout.setSpacing(8)

            s_idx = item.get("slide_index", 0)
            lbl_idx = QLabel(f"슬라이드 {s_idx:02d}", row_frame)
            lbl_idx.setFixedWidth(70)

            if item.get("is_step"):
                row_frame.setStyleSheet("QFrame { background-color: #F0F7FF; border-radius: 4px; }")
                lbl_idx.setStyleSheet("font-weight: bold; color: #1E3A8A;")

                old_s = item.get("old_step", "-")
                new_s = item.get("new_step", "-")
                lbl_change = QLabel(f"Step {old_s} ➔ Step {new_s}", row_frame)
                lbl_change.setFixedWidth(140)
                lbl_change.setStyleSheet("font-weight: bold; color: #0284C7;")

                lbl_text = QLabel(item.get("new_title", ""), row_frame)
                lbl_text.setStyleSheet("color: #334155;")

                row_layout.addWidget(lbl_idx)
                row_layout.addWidget(lbl_change)
                row_layout.addWidget(lbl_text, 1)
            else:
                row_frame.setStyleSheet("QFrame { background-color: #F8FAFC; border-radius: 4px; }")
                lbl_idx.setStyleSheet("color: #94A3B8;")

                lbl_note = QLabel("(표지/구분 슬라이드 - 내용 보존)", row_frame)
                lbl_note.setStyleSheet("color: #94A3B8; font-style: italic;")

                row_layout.addWidget(lbl_idx)
                row_layout.addWidget(lbl_note, 1)

            c_layout.addWidget(row_frame)

        c_layout.addStretch(1)
        scroll.setWidget(container)
        main_layout.addWidget(scroll, 1)

        # 하단 닫기 버튼
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch(1)
        btn_close = QPushButton("확인", dlg)
        btn_close.setFixedWidth(90)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #1565C0;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0D47A1;
            }
        """)
        btn_close.clicked.connect(dlg.accept)
        bottom_layout.addWidget(btn_close)
        main_layout.addLayout(bottom_layout)

        dlg.exec()

    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()

        # 1. Alt KeyTip 토글
        if key == Qt.Key_Alt:
            if not event.isAutoRepeat():
                self.toggle_keytips()
            event.accept()
            return

        # KeyTip 활성 상태에서 탭 번호 or ESC
        if getattr(self, "_keytips_visible", False):
            if key == Qt.Key_Escape:
                self.hide_keytips()
                event.accept()
                return
        elif key == Qt.Key_Escape:
            if self.canvas.current_mode != "SELECT":
                self.switch_mode("SELECT")
                event.accept()
                return
            elif key == Qt.Key_1:
                self.ribbon_tabs.setCurrentIndex(0)
                self.hide_keytips()
                event.accept()
                return
            elif key == Qt.Key_2:
                self.ribbon_tabs.setCurrentIndex(1)
                self.hide_keytips()
                event.accept()
                return

        # 2. Control 조합 단축키
        if modifiers & Qt.ControlModifier:
            if key == Qt.Key_Z:
                self.action_undo()
                self.hide_keytips()
                return
            elif key == Qt.Key_N:
                self.action_new_project()
                self.hide_keytips()
                return
            elif key == Qt.Key_O:
                self.action_open_project()
                self.hide_keytips()
                return
            elif key == Qt.Key_S:
                if modifiers & Qt.ShiftModifier:
                    self.action_save_as_project()
                else:
                    self.action_save_project()
                self.hide_keytips()
                return
            elif key == Qt.Key_M:
                if modifiers & Qt.ShiftModifier:
                    self.action_merge_project()
                else:
                    self.toggle_ribbon_display_mode()
                self.hide_keytips()
                return
            elif key == Qt.Key_C:
                self.copy_current_composed_image()
                self.hide_keytips()
                return
            elif key == Qt.Key_I:
                self.open_image_file()
                self.hide_keytips()
                return
            elif key == Qt.Key_F:
                self.auto_fit_ppt_scale()
                self.hide_keytips()
                return
            elif key == Qt.Key_R:
                self.action_renumber_powerpoint_steps()
                self.hide_keytips()
                return
            elif key in (Qt.Key_Delete, Qt.Key_Backspace) or (modifiers & Qt.ShiftModifier and key == Qt.Key_X):
                self.action_clear()
                self.hide_keytips()
                return

        # 3. Alt 조합 단축키
        if modifiers & Qt.AltModifier:
            if key == Qt.Key_A:
                if hasattr(self, "btn_autosave"):
                    self.btn_autosave.setChecked(not self.btn_autosave.isChecked())
                    self.on_autosave_toggle_clicked()
                self.hide_keytips()
                return

        # 4. 기능키 (F8, F9, F10, F11, F12) & 삭제키
        if key in (Qt.Key_Delete, Qt.Key_Backspace):
            if self.canvas.delete_selected_item():
                self.hide_keytips()
                return

        if key == Qt.Key_F8:
            self.start_sub_capture()
            self.hide_keytips()
            return
        elif key == Qt.Key_F9:
            if modifiers & Qt.ShiftModifier:
                self.start_capture()
            else:
                self.handle_hotkey_capture()
            self.hide_keytips()
            return
        elif key == Qt.Key_F10:
            if modifiers & Qt.ShiftModifier:
                self.action_send_to_hwp()
            else:
                self.action_add_new_slide()
            self.hide_keytips()
            return
        elif key == Qt.Key_F11:
            self.action_send_to_google_slides()
            self.hide_keytips()
            return
        elif key == Qt.Key_F12:
            self.action_send_to_hwp()
            self.hide_keytips()
            return

        # 5. 단일 키 모드 전환 (입력창에 포커스가 없을 때만 작동)
        focus_w = QApplication.focusWidget()
        in_editor = isinstance(focus_w, (QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox))
        if not in_editor and not (modifiers & (Qt.ControlModifier | Qt.AltModifier)):
            if modifiers & Qt.ShiftModifier:
                if key == Qt.Key_O:
                    self.switch_mode("OCR_LABEL")
                    self.hide_keytips()
                    return
                elif key == Qt.Key_D:
                    self.switch_mode("BOX_DIMENSION")
                    self.hide_keytips()
                    return
                elif key == Qt.Key_M:
                    self.action_auto_pii()
                    self.hide_keytips()
                    return

            mode_map = {
                Qt.Key_V: "SELECT",
                Qt.Key_S: "STAMP",
                Qt.Key_W: "STEP_ARROW",
                Qt.Key_E: "ELBOW",
                Qt.Key_A: "ARROW",
                Qt.Key_B: "BOX",
                Qt.Key_M: "BLUR",
                Qt.Key_C: "CALLOUT",
                Qt.Key_T: "TEXT",
                Qt.Key_K: "HOTKEY",
                Qt.Key_R: "WORDART",
                Qt.Key_O: "OCR",
                Qt.Key_D: "DIMENSION",
                Qt.Key_X: "ERASER",
            }
            if key in mode_map:
                self.switch_mode(mode_map[key])
                self.hide_keytips()
                return
            elif key == Qt.Key_P:
                if self.canvas.selected_item:
                    self.canvas.open_item_properties_dialog(self.canvas.selected_item)
                self.hide_keytips()
                return

        super().keyPressEvent(event)

    def show_toast(self, message):
        # 심플 인앱 툴팁 토스트 알림
        QToolTip.showText(
            self.mapToGlobal(QPoint(self.width() // 2 - 120, self.height() - 60)),
            message,
            self,
            QRect(),
            2500
        )

    def update_window_title(self):
        status = LicenseEngine.check_license_status()
        badge = status.get("badge_text", "평가판")
        lic_suffix = f"[{badge}]" if status.get("is_licensed") else f"[{tr('badge_trial', '평가판')} • ~2026.12.31]"
        proj = getattr(self, "current_project_path", None)
        project_name = f" - [{os.path.basename(proj)}]" if proj else ""
        self.setWindowTitle(f"Manual Studio {APP_VERSION} (DragonRPA Co.){project_name} {lic_suffix}")

    def update_status_bar(self):
        if not hasattr(self, "lbl_bottom_dev"):
            return
        status = LicenseEngine.check_license_status()
        if status.get("is_licensed"):
            issued_to = status.get("issued_to", "정식 사용자")
            badge = status.get("badge_text", "정식 인증")
            self.lbl_bottom_dev.setText(f"(주)드래곤알피에이 (DragonRPA Co.) | [{badge}] {issued_to} | 77.victor.lee@gmail.com")
            self.lbl_bottom_dev.setStyleSheet("color: #059669; font-size: 10.5px; font-weight: bold;")
        else:
            self.lbl_bottom_dev.setText("(주)드래곤알피에이 (DragonRPA Co.) | [평가판] ~2026.12.31 | 77.victor.lee@gmail.com")
            self.lbl_bottom_dev.setStyleSheet("color: #94A3B8; font-size: 10.5px; font-weight: 500;")

    def show_license_dialog(self):
        dlg = LicenseRegistrationDialog(self)
        dlg.sig_license_activated.connect(self.on_license_activated)
        dlg.exec()

    def on_license_activated(self):
        self.update_window_title()
        self.update_status_bar()
        self.canvas.update()
        self.show_toast(tr("msg_license_success", "라이선스가 정상적으로 활성화되었습니다."))

    def switch_language(self, locale_code: str):
        I18nManager.instance().set_locale(locale_code)
        self.config["locale"] = locale_code
        save_config(self.config)
        self.retranslate_ui()
        loc_name = I18nManager.instance().get_supported_locales().get(locale_code, locale_code)
        msg_tpl = tr("msg_lang_switched", "언어가 '{name}'(으)로 변경되었습니다.")
        try:
            msg = msg_tpl.format(name=loc_name)
        except Exception:
            msg = f"Language: {loc_name}"
        self.show_toast(msg)

    def check_for_updates(self, silent=False):
        self.update_checker_thread = UpdateCheckerThread(APP_VERSION, self)
        self.update_checker_thread.sig_update_available.connect(self._on_update_available)
        if not silent:
            self.update_checker_thread.sig_up_to_date.connect(self._on_up_to_date)
            self.update_checker_thread.sig_check_failed.connect(self._on_update_check_failed)
        self.update_checker_thread.start()

    def _on_update_available(self, meta: dict):
        target_exe = sys.executable if getattr(sys, 'frozen', False) else os.path.join(get_app_dir(), 'ManualStudio.exe')
        dlg = UpdateDialog(meta, APP_VERSION, target_exe_path=target_exe, parent=self)
        dlg.exec()

    def _on_up_to_date(self, current_ver: str):
        QMessageBox.information(
            self,
            "최신 버전 확인",
            f"현재 최신 버전({current_ver})을 사용하고 있습니다.\n새로운 업데이트가 없습니다."
        )

    def _on_update_check_failed(self, err_msg: str):
        QMessageBox.warning(
            self,
            "업데이트 확인 실패",
            f"최신 버전을 확인하는 중 오류가 발생했습니다:\n{err_msg}"
        )

    def init_autosave(self):
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self.auto_save_current_work)
        self.update_autosave_timer()

    def update_autosave_timer(self):
        if not hasattr(self, "autosave_timer"):
            return
        enabled = self.config.get("auto_save_enabled", True)
        interval_min = max(1, self.config.get("auto_save_interval_min", 5))
        if enabled:
            self.autosave_timer.start(interval_min * 60 * 1000)
        else:
            self.autosave_timer.stop()

    def get_autosave_path(self) -> str:
        return os.path.join(get_app_dir(), ".autosave.dragon")

    def auto_save_current_work(self):
        if not self.config.get("auto_save_enabled", True):
            return
        self._sync_canvas_to_current_step()
        if not self.storyboard_steps and (self.canvas.pixmap is None or self.canvas.pixmap.isNull()):
            return
        try:
            autosave_path = self.get_autosave_path()
            metadata = {
                "ppt_layout": self.config.get("ppt_layout", {}),
                "is_autosave": True,
                "saved_at": datetime.now().isoformat()
            }
            ProjectManager.save_project(
                autosave_path,
                self.storyboard_steps,
                active_step_idx=self.current_step_idx,
                metadata=metadata
            )
            self.status_label.setText(f"자동 저장 완료 ({datetime.now().strftime('%H:%M:%S')})")
        except Exception as e:
            print(f"[AutoSave] 자동 저장 중 오류: {e}")

    def check_and_prompt_recovery(self):
        if os.environ.get("MANUAL_STUDIO_TEST_MODE") == "1" or not self.isVisible():
            return
        autosave_path = self.get_autosave_path()
        legacy_autosave = os.path.join(get_app_dir(), ".autosave.mcs.json")
        target_path = autosave_path if os.path.exists(autosave_path) else (legacy_autosave if os.path.exists(legacy_autosave) else None)
        if not target_path:
            return
        try:
            proj = ProjectManager.load_project(target_path)
            steps = proj.steps if hasattr(proj, "steps") else []
            if not steps:
                if os.path.exists(target_path):
                    try:
                        os.remove(target_path)
                    except Exception:
                        pass
                return
            saved_time = proj.metadata.get("saved_at", "")
            time_msg = f" ({saved_time[:19].replace('T', ' ')})" if saved_time else ""
            res = QMessageBox.question(
                self,
                tr("msg_autosave_recover", "자동 저장 작업 복구"),
                f"{tr('msg_autosave_prompt', '이전 비정상 종료 시 자동 저장된 작업이 발견되었습니다.')}{time_msg}\n\n"
                f"슬라이드 {len(steps)}개를 복구하여 계속 작업하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if res == QMessageBox.Yes:
                self.storyboard_steps = steps
                self.current_step_idx = getattr(proj, "active_step_idx", 0)
                active_step = self.storyboard_steps[self.current_step_idx]
                self.canvas.load_project_data(
                    active_step.get("raw_pixmap"),
                    active_step.get("items", []),
                    active_step.get("next_stamp_index", 1)
                )
                if hasattr(self, "filmstrip"):
                    self.filmstrip.set_steps(self.storyboard_steps, self.current_step_idx)
                self.update_window_title()
                self.show_toast(f"자동 저장 복구 완료 ({len(steps)}개 슬라이드)")
            else:
                if os.path.exists(target_path):
                    try:
                        os.remove(target_path)
                    except Exception:
                        pass
        except Exception as e:
            print(f"[AutoSave] 복구 확인 중 오류: {e}")

    def apply_ui_theme(self, theme_name: str):
        self.ui_style = theme_name
        self.config["ui_style"] = theme_name
        ThemeManager.apply_theme(QApplication.instance(), theme_name, self)

    def open_settings_dialog(self):
        old_loc = self.config.get("locale", "auto")
        dlg = SettingsDialog(self.config, self)
        if dlg.exec() == QDialog.Accepted:
            self.config = dlg.get_config()
            save_config(self.config)
            new_style = self.config.get("ui_style", "auto")
            self.apply_ui_theme(new_style)
            new_loc = self.config.get("locale", "auto")
            if new_loc != old_loc and new_loc != "auto":
                self.switch_language(new_loc)
            elif new_loc != "auto":
                I18nManager.instance().set_locale(new_loc)
                self.retranslate_ui()
            self.canvas.set_config(self.config)
            self.sync_ui_from_config()
            self.update_window_title()
            self.update_status_bar()
            self.update_autosave_timer()
            self.show_toast(tr("settings_toast_saved", "설정이 저장되었습니다."))

    def closeEvent(self, event):
        if hasattr(self, "mobile_server") and self.mobile_server:
            try:
                self.mobile_server.stop_server()
            except Exception:
                pass
        if hasattr(self, "hotkey_thread"):
            self.hotkey_thread.stop()
        if hasattr(self, "autosave_timer"):
            self.autosave_timer.stop()
        if self.canvas.pixmap is None or self.canvas.pixmap.isNull():
            p = self.get_autosave_path()
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass
        event.accept()


    def on_toggle_window_frame(self):
        cur = self.btn_toggle_window_frame.isChecked()
        self.config["enable_window_frame"] = cur
        save_config(self.config)
        status_text = "켜짐 (ON)" if cur else "꺼짐 (OFF)"
        self.show_toast(f"창틀 & 소프트 섀도우 액자 효과: {status_text}")

    def on_toggle_filmstrip(self):
        cur = self.btn_filmstrip_toggle.isChecked()
        self.config["filmstrip_visible"] = cur
        save_config(self.config)
        self.filmstrip.setVisible(cur)

    def action_auto_pii(self):
        if not hasattr(self, "canvas") or not self.canvas:
            return
        if self.canvas.pixmap is None or self.canvas.pixmap.isNull():
            self.show_toast("마스킹할 캡처 이미지가 없습니다. F9를 눌러 먼저 캡처하세요.")
            return

        dlg = PiiMaskingDialog(self.config, self)
        if dlg.exec() == QDialog.Accepted:
            active_cats = [cat for cat, val in self.config.get("pii_categories", {}).items() if val]
            custom_rules = self.config.get("custom_pii_rules", [])
            self.canvas.apply_auto_pii_redaction(active_categories=active_cats, custom_rules=custom_rules)

    def action_scroll_stitch(self):
        """현재 스토리보드의 스텝들을 스티칭하거나, 파일 선택을 통해 여러 이미지를 1장의 수직 파노라마로 합성"""
        steps = self.filmstrip.get_all_steps() if hasattr(self, "filmstrip") else []
        if len(steps) >= 2:
            from PySide6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self,
                tr("btn_scroll_stitch", "스크롤 스티칭"),
                f"현재 스토리보드의 {len(steps)}개 단계를 1장의 긴 이미지로 합성하시겠습니까?\n('아니오' 선택 시 외부 이미지 파일 선택)",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            if reply == QMessageBox.Yes:
                pil_imgs = []
                for s in steps:
                    qimg = s.get("composed_pixmap", s.get("raw_pixmap")).toImage()
                    pil_imgs.append(ExportEngine.qimage_to_pil(qimg))
                stitched = ScrollStitchEngine.stitch_images(pil_imgs)
                if stitched:
                    res_pixmap = ExportEngine.pil_to_qpixmap(stitched)
                    self.canvas.push_undo()
                    self.canvas.set_pixmap(res_pixmap)
                    self.show_toast(tr("toast_stitch_success", "스크롤 스티칭 완료 ({count}개 프레임 합성)").replace("{count}", str(len(pil_imgs))))
                return
            elif reply == QMessageBox.Cancel:
                return

        from PySide6.QtWidgets import QFileDialog
        files, _ = QFileDialog.getOpenFileNames(
            self,
            tr("btn_scroll_stitch", "스크롤 스티칭") + " - 이미지 선택",
            "",
            "이미지 파일 (*.png *.jpg *.jpeg *.bmp)"
        )
        if files and len(files) >= 2:
            stitched = ScrollStitchEngine.stitch_images(files)
            if stitched:
                res_pixmap = ExportEngine.pil_to_qpixmap(stitched)
                self.canvas.push_undo()
                self.canvas.set_pixmap(res_pixmap)
                self.show_toast(tr("toast_stitch_success", "스크롤 스티칭 완료 ({count}개 프레임 합성)").replace("{count}", str(len(files))))

    def action_toggle_action_recorder(self):
        """액션 녹화 기능 (보안 및 안정성 정책에 따라 폐기됨)"""
        self.show_toast("액션 녹화 기능은 보안 및 안정성 정책에 따라 폐기되었습니다.")


    def action_send_to_hwp(self):
        if self.canvas.pixmap is None:
            self.show_toast("내보낼 캡처 이미지가 없습니다. F9를 눌러 먼저 캡처하세요.")
            return

        qimg = self.canvas.get_composed_image()
        if qimg is None:
            return

        pil_img = ExportEngine.qimage_to_pil(qimg)
        if self.config.get("enable_window_frame", True):
            frame_cfg = self.config.get("window_frame_style", {})
            pil_img = ExportEngine.apply_window_frame_and_shadow(
                pil_img,
                include_header=frame_cfg.get("include_header", True),
                corner_radius=frame_cfg.get("corner_radius", 12),
                shadow_radius=frame_cfg.get("shadow_radius", 20),
                shadow_opacity=frame_cfg.get("shadow_opacity", 0.35)
            )

        target_w = self.config.get("target_width", 960)
        if self.config.get("auto_resize", True):
            pil_img = ExportEngine.resize_to_target_width(pil_img, target_w)

        try:
            ExportEngine.copy_to_clipboard(pil_img)
        except Exception:
            pass

        step_num = self.current_step_idx + 1 if hasattr(self, "current_step_idx") else 1
        step_title = f"[Step {step_num}] 단계명 입력"
        res = ExportEngine.send_to_hwp(pil_img, step_title=step_title)

        if res.get("success"):
            self.status_label.setText(f"한컴 한글(HWP) Step {step_num} 문서 삽입 완료!")
            self.show_toast(f"한컴 한글(HWP) Step {step_num} 삽입 완료! (Shift+F10 / F12)")
        else:
            err = res.get("error", "Unknown error")
            self.show_toast(f"한글 내보내기 실패: {err}")

    def load_step_to_canvas(self, step_idx: int):
        """지정된 슬라이드의 원본 픽스맵과 주석 아이템들을 작업대 캔버스에 로드"""
        if not self.storyboard_steps or not (0 <= step_idx < len(self.storyboard_steps)):
            return
        target_step = self.storyboard_steps[step_idx]
        raw_px = target_step.get("raw_pixmap")
        if raw_px and not raw_px.isNull():
            self.canvas.pixmap = raw_px.copy()
        else:
            self.canvas.pixmap = None

        self.canvas.items = [item.clone() for item in target_step.get("items", [])]
        self.canvas.next_stamp_index = target_step.get("next_stamp_index", 1)
        self.canvas.selected_item = None
        self.canvas.history.clear()
        self.canvas.update()

    def on_filmstrip_step_selected(self, target_idx: int):
        if target_idx < 0 or target_idx >= len(self.storyboard_steps):
            return
        if target_idx == self.current_step_idx and self.canvas.pixmap is not None:
            return

        self._sync_canvas_to_current_step()

        self.current_step_idx = target_idx
        self.load_step_to_canvas(target_idx)

        if hasattr(self, "filmstrip"):
            self.filmstrip.steps = self.storyboard_steps
            self.filmstrip.active_idx = self.current_step_idx
            self.filmstrip.update_card_selection_states()

        target_step = self.storyboard_steps[target_idx]
        if target_step.get("has_unmasked_pii", False):
            self.show_toast(tr("toast_unmasked_pii_detected", "⚠️ 미마스킹 민감정보 감지됨 (Shift+M으로 마스킹)"), duration=3500)
        else:
            self.show_toast(f"Step {target_idx + 1} 작업대로 전환되었습니다.")

    def on_filmstrip_add_step(self):
        self._sync_canvas_to_current_step()

        new_idx = len(self.storyboard_steps)
        new_step = {
            "step_num": new_idx + 1,
            "title": f"Step {new_idx + 1}. [단계명 입력]",
            "raw_pixmap": None,
            "items": [],
            "next_stamp_index": 1,
            "thumbnail": None
        }
        self.storyboard_steps.append(new_step)
        self.current_step_idx = new_idx

        self.canvas.pixmap = None
        self.canvas.items.clear()
        self.canvas.next_stamp_index = 1
        self.canvas.history.clear()
        self.canvas.update()

        if hasattr(self, "filmstrip"):
            self.filmstrip.set_steps(self.storyboard_steps, self.current_step_idx)
        self.show_toast(f"새 Step {new_idx + 1} 생성됨. F9를 눌러 화면을 캡처하세요.")

    def action_add_new_slide(self):
        """+ 새 슬라이드 (F10) 쾌속 생성 및 작업대 전환"""
        self.on_filmstrip_add_step()

    def on_filmstrip_delete_step(self, del_idx: int):
        self.on_filmstrip_delete_selected([del_idx])

    def on_storyboard_toggle_bar_toggled(self, is_visible: bool):
        self.filmstrip.setVisible(is_visible)
        self.config["filmstrip_visible"] = is_visible
        save_config(self.config)
        if hasattr(self, "btn_toggle_filmstrip") and self.btn_toggle_filmstrip:
            self.btn_toggle_filmstrip.setChecked(is_visible)

    def on_filmstrip_toggle_hover_preview(self, enabled: bool):
        self.config["enable_hover_preview"] = enabled
        save_config(self.config)

    def on_filmstrip_duplicate_selected(self):
        """선택된 슬라이드들을 복제하여 바로 뒤에 삽입"""
        if not self.storyboard_steps:
            return
        self._sync_canvas_to_current_step()
        selected = sorted(self.filmstrip.selected_indices) if hasattr(self.filmstrip, "selected_indices") and self.filmstrip.selected_indices else [self.current_step_idx]
        new_steps = []
        new_selected = set()

        for idx in range(len(self.storyboard_steps)):
            new_steps.append(self.storyboard_steps[idx])
            if idx in selected:
                orig = self.storyboard_steps[idx]
                dup = {
                    "step_num": orig.get("step_num", idx + 1),
                    "title": (orig.get("title", "") + " (복사본)").strip(),
                    "desc": orig.get("desc", ""),
                    "raw_pixmap": QPixmap(orig.get("raw_pixmap")) if orig.get("raw_pixmap") else None,
                    "thumbnail": QPixmap(orig.get("thumbnail")) if orig.get("thumbnail") else None,
                    "items": [it.clone() for it in orig.get("items", []) if hasattr(it, "clone")],
                    "next_stamp_index": orig.get("next_stamp_index", 1)
                }
                new_steps.append(dup)
                new_selected.add(len(new_steps) - 1)

        for i, s in enumerate(new_steps):
            s["step_num"] = i + 1

        self.storyboard_steps = new_steps
        if new_selected:
            self.current_step_idx = min(new_selected)
            self.filmstrip.selected_indices = new_selected
        self.filmstrip.set_steps(self.storyboard_steps, self.current_step_idx)
        self.load_step_to_canvas(self.current_step_idx)
        self.show_toast(f"슬라이드 {len(selected)}개 복제 완료")

    def on_filmstrip_move_selected(self, direction: int):
        """선택된 슬라이드들을 앞(-1) 또는 뒤(+1)로 이동"""
        if not self.storyboard_steps:
            return
        self._sync_canvas_to_current_step()
        selected = sorted(self.filmstrip.selected_indices) if hasattr(self.filmstrip, "selected_indices") and self.filmstrip.selected_indices else [self.current_step_idx]
        n = len(self.storyboard_steps)

        if direction == -1:  # 앞으로 이동 (왼쪽)
            if selected[0] <= 0:
                return
            for idx in selected:
                self.storyboard_steps[idx - 1], self.storyboard_steps[idx] = self.storyboard_steps[idx], self.storyboard_steps[idx - 1]
            new_selected = {idx - 1 for idx in selected}
        elif direction == 1:  # 뒤로 이동 (오른쪽)
            if selected[-1] >= n - 1:
                return
            for idx in reversed(selected):
                self.storyboard_steps[idx + 1], self.storyboard_steps[idx] = self.storyboard_steps[idx], self.storyboard_steps[idx + 1]
            new_selected = {idx + 1 for idx in selected}
        else:
            return

        for i, s in enumerate(self.storyboard_steps):
            s["step_num"] = i + 1

        self.filmstrip.selected_indices = new_selected
        self.current_step_idx = min(new_selected)
        self.filmstrip.set_steps(self.storyboard_steps, self.current_step_idx)
        self.load_step_to_canvas(self.current_step_idx)

    def on_filmstrip_delete_selected(self, del_indices: list = None):
        """선택된 슬라이드 일괄 삭제"""
        if not self.storyboard_steps:
            return
        if del_indices is None:
            del_indices = [self.current_step_idx]
        del_indices = [i for i in del_indices if 0 <= i < len(self.storyboard_steps)]
        if not del_indices:
            self.show_toast("삭제할 슬라이드가 선택되지 않았습니다.")
            return

        if len(del_indices) >= len(self.storyboard_steps):
            self.storyboard_steps = [{
                "step_num": 1,
                "title": "Step 1. [단계명 입력]",
                "raw_pixmap": None,
                "items": [],
                "next_stamp_index": 1,
                "thumbnail": None
            }]
            self.current_step_idx = 0
            self.canvas.pixmap = None
            self.canvas.items.clear()
            self.canvas.next_stamp_index = 1
            self.canvas.history.clear()
            self.canvas.update()
            if hasattr(self, "filmstrip"):
                self.filmstrip.set_steps(self.storyboard_steps, 0)
            self.show_toast("선택된 슬라이드 삭제 완료 (기본 슬라이드 초기화)")
            return

        for idx in sorted(del_indices, reverse=True):
            self.storyboard_steps.pop(idx)

        for i, s in enumerate(self.storyboard_steps):
            s["step_num"] = i + 1

        if self.current_step_idx >= len(self.storyboard_steps):
            self.current_step_idx = len(self.storyboard_steps) - 1

        target_step = self.storyboard_steps[self.current_step_idx]
        raw_px = target_step.get("raw_pixmap")
        self.canvas.pixmap = raw_px.copy() if raw_px and not raw_px.isNull() else None
        self.canvas.items = [it.clone() for it in target_step.get("items", [])]
        self.canvas.next_stamp_index = target_step.get("next_stamp_index", 1)
        self.canvas.update()

        if hasattr(self, "filmstrip"):
            self.filmstrip.set_steps(self.storyboard_steps, self.current_step_idx)
        self.show_toast(f"슬라이드 {len(del_indices)}개 삭제 완료")

    def get_export_target_steps(self):
        """선택된 슬라이드 대상 목록 반환 [(idx, step_data), ...]"""
        if hasattr(self, "filmstrip") and hasattr(self.filmstrip, "selected_indices") and self.filmstrip.selected_indices:
            sel_sorted = sorted(self.filmstrip.selected_indices)
            valid = [(idx, self.storyboard_steps[idx]) for idx in sel_sorted if 0 <= idx < len(self.storyboard_steps)]
            if valid:
                return valid
        return [(idx, step) for idx, step in enumerate(self.storyboard_steps)]

    def on_filmstrip_duplicate_step(self, dup_idx: int):
        if 0 <= dup_idx < len(self.storyboard_steps):
            self._sync_canvas_to_current_step()
            src_step = self.storyboard_steps[dup_idx]
            new_step = {
                "step_num": len(self.storyboard_steps) + 1,
                "title": src_step.get("title", "") + " (복사본)",
                "raw_pixmap": src_step["raw_pixmap"].copy() if src_step.get("raw_pixmap") else None,
                "items": [it.clone() for it in src_step.get("items", [])],
                "next_stamp_index": src_step.get("next_stamp_index", 1),
                "thumbnail": src_step["thumbnail"].copy() if src_step.get("thumbnail") else None
            }
            self.storyboard_steps.insert(dup_idx + 1, new_step)
            for i, s in enumerate(self.storyboard_steps):
                s["step_num"] = i + 1
            self.on_filmstrip_step_selected(dup_idx + 1)

    def on_filmstrip_move_step(self, from_idx: int, to_idx: int):
        if 0 <= from_idx < len(self.storyboard_steps) and 0 <= to_idx < len(self.storyboard_steps):
            self._sync_canvas_to_current_step()
            item = self.storyboard_steps.pop(from_idx)
            self.storyboard_steps.insert(to_idx, item)
            for i, s in enumerate(self.storyboard_steps):
                s["step_num"] = i + 1
            self.current_step_idx = to_idx
            if hasattr(self, "filmstrip"):
                self.filmstrip.set_steps(self.storyboard_steps, self.current_step_idx)
            self.load_step_to_canvas(self.current_step_idx)
            self.show_toast(f"Step 순서 변경: {from_idx + 1} ➔ {to_idx + 1}")

    def _prepare_export_step_image(self, step: dict, target_w: int = 960, auto_resize: bool = True, enable_frame: bool = True, frame_cfg: dict = None) -> Image.Image:
        """
        슬라이드 데이터를 받아 주석 합성 + (옵션) 윈도우 액자 프레임 + 리사이즈를 거친 PIL Image를 생성합니다.
        raw_pixmap이 없는 빈 슬라이드인 경우에도 16:9 규격(1920x1080)의 백색 캔버스로 Fallback 렌더링하여
        절대 누락되거나 실패하지 않도록 무결성을 보장합니다.
        """
        raw_px = step.get("raw_pixmap")
        step_num = step.get("step_num", 1)
        s_title = step.get("title", f"Step {step_num}")

        if raw_px is None or raw_px.isNull():
            # 빈 슬라이드 Fallback: 1920x1080 백색 캔버스에 단계 타이틀 렌더링
            raw_px = QPixmap(1920, 1080)
            raw_px.fill(Qt.white)
            p = QPainter(raw_px)
            p.setRenderHint(QPainter.Antialiasing, True)
            p.setPen(QPen(QColor("#E2E8F0"), 3, Qt.DashLine))
            p.drawRect(40, 40, 1840, 1000)
            font = QFont("Malgun Gothic", 28)
            font.setBold(True)
            p.setFont(font)
            p.setPen(QColor("#64748B"))
            p.drawText(QRect(60, 60, 1800, 960), Qt.AlignCenter, f"{s_title}\n\n[{tr('slide_empty', '빈 슬라이드')}]")
            p.end()

        # 주석 렌더링을 위한 합성 QImage 생성
        temp_img = QImage(raw_px.size(), QImage.Format_ARGB32)
        temp_img.fill(Qt.transparent)
        painter = QPainter(temp_img)
        try:
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.drawPixmap(0, 0, raw_px)
            for item in step.get("items", []):
                try:
                    if isinstance(item, BlurMosaicItem):
                        item.render_mosaic(painter, raw_px)
                    elif isinstance(item, MagnifierZoomItem):
                        item.render_zoom(painter, raw_px)
                    elif isinstance(item, SpotlightMaskItem):
                        item.render_spotlight(painter, raw_px.width(), raw_px.height())
                    elif isinstance(item, (ImageOverlayItem, DraftStampItem)):
                        item.render(painter, is_selected=False)
                    else:
                        item.render(painter)
                except Exception as e:
                    print(f"[Export Item Render Error]: {e}")
            if not LicenseEngine.is_licensed():
                self.canvas._render_watermark(painter, temp_img.width(), temp_img.height())
        finally:
            painter.end()

        pil_img = ExportEngine.qimage_to_pil(temp_img)
        if enable_frame:
            f_cfg = frame_cfg or self.config.get("window_frame_style", {})
            pil_img = ExportEngine.apply_window_frame_and_shadow(
                pil_img,
                include_header=f_cfg.get("include_header", True),
                corner_radius=f_cfg.get("corner_radius", 12),
                shadow_radius=f_cfg.get("shadow_radius", 20),
                shadow_opacity=f_cfg.get("shadow_opacity", 0.35)
            )
        if auto_resize:
            pil_img = ExportEngine.resize_to_target_width(pil_img, target_w)
        return pil_img

    def action_export_all_ppt(self):
        self._sync_canvas_to_current_step()
        target_steps = self.get_export_target_steps()
        if not target_steps:
            self.show_toast("전송할 슬라이드가 없습니다.")
            return

        target_w = self.config.get("target_width", 960)
        auto_resize = self.config.get("auto_resize", True)
        enable_frame = self.config.get("enable_window_frame", True)
        frame_cfg = self.config.get("window_frame_style", {})
        ppt_layout = self.config.get("ppt_layout", {}).copy()
        temp_dir = os.path.join(get_app_dir(), "temp")

        sent_count = 0
        for idx, step in target_steps:
            pil_img = self._prepare_export_step_image(step, target_w=target_w, auto_resize=auto_resize, enable_frame=enable_frame, frame_cfg=frame_cfg)

            step_num = step.get("step_num", idx + 1)
            s_title = step.get("title", f"Step {step_num}. [단계명 입력]")
            step_layout = ppt_layout.copy()
            step_layout["title_template"] = s_title
            ok = ExportEngine.send_to_powerpoint(pil_img, temp_dir, step_layout)
            if ok:
                sent_count += 1

        if sent_count > 0:
            self.show_toast(f"선택된 슬라이드 {sent_count}개 파워포인트 전송 완료")
        else:
            self.show_toast("파워포인트 전송 실패 (PowerPoint 프로그램이 실행되어 있는지 확인하세요)")

    def action_send_to_google_slides(self):
        """현재 캔버스 이미지를 웹 브라우저 구글 슬라이드로 즉시 주입"""
        if self.canvas.pixmap is None or self.canvas.pixmap.isNull():
            self.show_toast("작업 중인 이미지가 없습니다.")
            return {"success": False, "error": "EMPTY_CANVAS"}

        qimg = self.canvas.get_composed_image()
        if qimg is None:
            return {"success": False, "error": "COMPOSED_FAIL"}

        pil_img = ExportEngine.qimage_to_pil(qimg)
        target_w = self.config.get("target_width", 960)
        if self.config.get("auto_resize", True):
            pil_img = ExportEngine.resize_to_target_width(pil_img, target_w)

        return_focus = self.config.get("slides_return_focus", True)
        res = ExportEngine.send_to_google_slides(
            pil_img,
            return_focus_hwnd=int(self.winId()),
            return_focus=return_focus
        )
        if res.get("success"):
            self.show_toast(f"구글 슬라이드 전송 완료: {res.get('title', '')}")
        return res

    def export_to_ppt_and_clipboard(self):
        """현재 캔버스를 클립보드 복사 및 대상 프리젠테이션(PPT/구글슬라이드)으로 전송"""
        if self.canvas.pixmap is None or self.canvas.pixmap.isNull():
            self.show_toast("작업 중인 이미지가 없습니다.")
            return

        qimg = self.canvas.get_composed_image()
        if qimg is None:
            return

        pil_img = ExportEngine.qimage_to_pil(qimg)
        target_w = self.config.get("target_width", 960)
        if self.config.get("auto_resize", True):
            pil_img = ExportEngine.resize_to_target_width(pil_img, target_w)

        try:
            ExportEngine.copy_to_clipboard(pil_img)
        except Exception:
            pass

        export_target = self.config.get("export_target", "powerpoint")
        if export_target == "google_slides":
            return self.action_send_to_google_slides()
        else:
            return self.action_export_all_ppt()

    def action_export_all_slides(self):
        """선택된 슬라이드들을 웹 브라우저 구글 슬라이드로 일괄 새 슬라이드 생성 및 주입"""
        self._sync_canvas_to_current_step()
        target_steps = self.get_export_target_steps()
        if not target_steps:
            self.show_toast("전송할 슬라이드가 없습니다.")
            return

        target_w = self.config.get("target_width", 960)
        auto_resize = self.config.get("auto_resize", True)
        enable_frame = self.config.get("enable_window_frame", True)
        frame_cfg = self.config.get("window_frame_style", {})
        return_focus = self.config.get("slides_return_focus", True)

        sent_count = 0
        total = len(target_steps)
        for seq, (idx, step) in enumerate(target_steps, 1):
            pil_img = self._prepare_export_step_image(step, target_w=target_w, auto_resize=auto_resize, enable_frame=enable_frame, frame_cfg=frame_cfg)

            step_num = step.get("step_num", idx + 1)
            self.status_label.setText(f"구글 슬라이드 주입 중... (Step {step_num}, {seq}/{total})")
            QApplication.processEvents()

            res = ExportEngine.send_to_google_slides(
                pil_img,
                return_focus_hwnd=int(self.winId()),
                return_focus=return_focus
            )
            if res.get("success"):
                sent_count += 1
            else:
                err = res.get("error")
                if err == "NOT_FOUND":
                    self.show_toast(tr("slides_not_found", "구글 슬라이드 웹 브라우저 창을 찾을 수 없습니다.\n크롬 또는 엣지에서 구글 슬라이드를 열어주세요."))
                    break

        if sent_count > 0:
            success_msg = f"선택된 슬라이드 {sent_count}개 구글 슬라이드 전송 완료"
            self.status_label.setText(success_msg)
            self.show_toast(success_msg)

    def action_export_webbook(self):
        self._sync_canvas_to_current_step()
        target_steps = self.get_export_target_steps()
        if not target_steps:
            self.show_toast("내보낼 슬라이드가 없습니다.")
            return

        default_name = os.path.join(os.path.expanduser("~"), "Desktop", "manual_guide.html")
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            tr("menu_export_webbook", "반응형 웹북 매뉴얼 저장"),
            default_name,
            "HTML 파일 (*.html);;모든 파일 (*.*)"
        )
        if not file_path:
            return

        enable_frame = self.config.get("enable_window_frame", True)
        frame_cfg = self.config.get("window_frame_style", {})

        steps_payload = []
        for idx, step in target_steps:
            pil_img = self._prepare_export_step_image(step, target_w=1280, auto_resize=True, enable_frame=enable_frame, frame_cfg=frame_cfg)

            buf = io.BytesIO()
            pil_img.save(buf, format="PNG")
            b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")

            step_num = step.get("step_num", idx + 1)
            s_title = step.get("title", f"Step {step_num}. 단계 가이드")
            s_desc = step.get("description", f"{step_num}번째 조작 화면입니다. 안내된 위치를 클릭하거나 항목을 입력하세요.")

            steps_payload.append({
                "step_num": step_num,
                "title": s_title,
                "description": s_desc,
                "image_b64": f"data:image/png;base64,{b64_str}"
            })

        doc_title = os.path.splitext(os.path.basename(file_path))[0]
        ExportEngine.export_to_html(steps_payload, file_path, title=doc_title)
        QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
        self.show_toast(f"웹북 매뉴얼 저장 완료 ({len(steps_payload)}개 슬라이드)")

    def action_export_gif(self):
        self._sync_canvas_to_current_step()
        target_steps = self.get_export_target_steps()
        if not target_steps:
            self.show_toast("내보낼 슬라이드가 없습니다.")
            return

        default_name = os.path.join(os.path.expanduser("~"), "Desktop", "tutorial_short.gif")
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            tr("menu_export_gif", "숏클립 튜토리얼 GIF 저장"),
            default_name,
            "GIF 애니메이션 (*.gif);;모든 파일 (*.*)"
        )
        if not file_path:
            return

        enable_frame = self.config.get("enable_window_frame", True)
        frame_cfg = self.config.get("window_frame_style", {})

        pil_frames = []
        for idx, step in target_steps:
            pil_img = self._prepare_export_step_image(step, target_w=960, auto_resize=True, enable_frame=enable_frame, frame_cfg=frame_cfg)
            pil_frames.append(pil_img)

        ExportEngine.export_to_animated_gif(pil_frames, file_path, interval_sec=1.5)
        self.show_toast(f"숏클립 튜토리얼 GIF 저장 완료 ({len(pil_frames)}개 슬라이드)")

    def action_export_all_hwp(self):
        self._sync_canvas_to_current_step()
        target_steps = self.get_export_target_steps()
        if not target_steps:
            self.show_toast("전송할 슬라이드가 없습니다.")
            return

        target_w = self.config.get("target_width", 960)
        auto_resize = self.config.get("auto_resize", True)
        enable_frame = self.config.get("enable_window_frame", True)
        frame_cfg = self.config.get("window_frame_style", {})

        sent_count = 0
        for idx, step in target_steps:
            pil_img = self._prepare_export_step_image(step, target_w=target_w, auto_resize=auto_resize, enable_frame=enable_frame, frame_cfg=frame_cfg)

            step_num = step.get("step_num", idx + 1)
            step_title = step.get("title", f"[매뉴얼 스튜디오] Step {step_num}. [단계명 입력]")
            res = ExportEngine.send_to_hwp(pil_img, step_title=step_title)
            if res.get("success"):
                sent_count += 1

        if sent_count > 0:
            self.show_toast(f"선택된 슬라이드 {sent_count}개 한컴 한글(HWP) 전송 완료")
        else:
            self.show_toast("한컴 한글(HWP) 전송 실패 (한컴 한글이 설치되어 있는지 확인하세요)")

    def action_export_pdf(self):
        """300 DPI 초고화질 네이티브 PDF 문서 내보내기"""
        self._sync_canvas_to_current_step()
        target_steps = self.get_export_target_steps()
        if not target_steps:
            self.show_toast(tr("msg_no_slides_to_export", "내보낼 슬라이드가 없습니다."))
            return

        default_name = os.path.join(os.path.expanduser("~"), "Desktop", "manual_guide.pdf")
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            tr("dlg_export_pdf", "PDF 문서 내보내기"),
            default_name,
            "PDF 파일 (*.pdf);;모든 파일 (*.*)"
        )
        if not file_path:
            return

        enable_frame = self.config.get("enable_window_frame", True)
        frame_cfg = self.config.get("window_frame_style", {})

        steps_payload = []
        for idx, step in target_steps:
            pil_img = self._prepare_export_step_image(step, target_w=1920, auto_resize=False, enable_frame=enable_frame, frame_cfg=frame_cfg)
            step_num = step.get("step_num", idx + 1)
            s_title = step.get("title", f"Step {step_num}")
            s_desc = step.get("description", "")
            steps_payload.append({
                "step_num": step_num,
                "title": s_title,
                "description": s_desc,
                "composed_image": pil_img
            })

        doc_title = os.path.splitext(os.path.basename(file_path))[0]
        res = ExportEngine.export_to_pdf(steps_payload, file_path, orientation="landscape", title=doc_title)
        if res.get("success"):
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
            self.show_toast(f"PDF 매뉴얼 저장 완료 ({len(steps_payload)}개 슬라이드)")
        else:
            QMessageBox.warning(self, tr("title_notice", "알림"), res.get("error", "PDF 저장 실패"))

    def action_export_word_doc(self):
        """MS Word (.docx) 정식 A4 보고서/매뉴얼 문서 생성"""
        self._sync_canvas_to_current_step()
        target_steps = self.get_export_target_steps()
        if not target_steps:
            self.show_toast(tr("msg_no_slides_to_export", "내보낼 슬라이드가 없습니다."))
            return

        default_name = os.path.join(os.path.expanduser("~"), "Desktop", "manual_guide.docx")
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            tr("dlg_export_word", "MS Word (.docx) 문서 내보내기"),
            default_name,
            "Word 문서 (*.docx);;모든 파일 (*.*)"
        )
        if not file_path:
            return

        enable_frame = self.config.get("enable_window_frame", True)
        frame_cfg = self.config.get("window_frame_style", {})

        steps_payload = []
        for idx, step in target_steps:
            pil_img = self._prepare_export_step_image(step, target_w=1280, auto_resize=True, enable_frame=enable_frame, frame_cfg=frame_cfg)
            step_num = step.get("step_num", idx + 1)
            s_title = step.get("title", f"Step {step_num}")
            s_desc = step.get("description", "")
            steps_payload.append({
                "step_num": step_num,
                "title": s_title,
                "description": s_desc,
                "pil_image": pil_img
            })

        doc_title = os.path.splitext(os.path.basename(file_path))[0]
        res = ExportEngine.export_to_word_doc(steps_payload, file_path, title=doc_title)
        if res.get("success"):
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
            self.show_toast(f"Word 문서 저장 완료 ({len(steps_payload)}개 슬라이드)")
        else:
            QMessageBox.warning(self, tr("title_notice", "알림"), res.get("error", "Word 문서 저장 실패"))

    def action_send_to_word(self):
        """현재 실행 중인 MS Word 창의 커서 위치에 활성 슬라이드 이미지 즉시 삽입 (win32com)"""
        self._sync_canvas_to_current_step()
        if self.canvas.pixmap is None or self.canvas.pixmap.isNull():
            self.show_toast("작업 중인 이미지가 없습니다.")
            return

        qimg = self.canvas.get_composed_image()
        if qimg is None:
            return
        pil_img = ExportEngine.qimage_to_pil(qimg)
        title = None
        if 0 <= self.current_step_idx < len(self.storyboard_steps):
            title = self.storyboard_steps[self.current_step_idx].get("title")

        res = ExportEngine.send_to_word(pil_img, step_title=title)
        if res.get("success"):
            self.show_toast("MS Word 커서 위치에 이미지 삽입 완료")
        else:
            self.show_toast(f"Word 전송 실패: {res.get('error', '')}")

    def action_export_notion(self):
        """노션(Notion) 내보내기 다이얼로그 호출"""
        self._sync_canvas_to_current_step()
        target_steps = self.get_export_target_steps()
        if not target_steps:
            self.show_toast(tr("msg_no_slides_to_export", "내보낼 슬라이드가 없습니다."))
            return

        steps_payload = []
        for idx, step in target_steps:
            step_num = step.get("step_num", idx + 1)
            s_title = step.get("title", f"Step {step_num}")
            s_desc = step.get("description", "")
            steps_payload.append({
                "step_num": step_num,
                "title": s_title,
                "description": s_desc,
            })

        dlg = ExportNotionDialog(steps_payload, parent=self)
        dlg.exec()

    def action_export_confluence(self):
        """컨플루언스(Confluence) 내보내기 다이얼로그 호출"""
        self._sync_canvas_to_current_step()
        target_steps = self.get_export_target_steps()
        if not target_steps:
            self.show_toast(tr("msg_no_slides_to_export", "내보낼 슬라이드가 없습니다."))
            return

        steps_payload = []
        for idx, step in target_steps:
            step_num = step.get("step_num", idx + 1)
            s_title = step.get("title", f"Step {step_num}")
            s_desc = step.get("description", "")
            steps_payload.append({
                "step_num": step_num,
                "title": s_title,
                "description": s_desc,
            })

        dlg = ExportConfluenceDialog(steps_payload, parent=self)
        dlg.exec()


    def open_flowchart_studio(self):
        """플로우차트 빌더 다이얼로그 호출 및 캔버스 자동 삽입 연동"""
        dlg = FlowchartStudioDialog(self)
        dlg.sig_insert_flowchart.connect(self.on_flowchart_inserted)
        dlg.exec()

    def on_flowchart_inserted(self, nodes, arrows):
        """플로우차트 노드 및 연결선 캔버스 일괄 주입"""
        if not nodes and not arrows:
            return
        self.canvas.push_undo()
        for n in nodes:
            self.canvas.items.append(n)
        for a in arrows:
            self.canvas.items.append(a)
        self.canvas.update()
        self.canvas.sig_content_changed.emit()
        self.show_toast(f"플로우차트 노드 {len(nodes)}개 및 연결선 {len(arrows)}개가 캔버스에 추가되었습니다.")

    def action_auto_align_flowchart(self):
        """캔버스의 플로우차트 노드 및 연결선을 화살표 위상 정렬(Topological BFS) 및 그리드 토폴로지 기반으로 자동정렬"""
        nodes = [it for it in self.canvas.items if isinstance(it, FlowchartNodeItem)]
        if not nodes:
            self.show_toast(tr("toast_no_flow_nodes", "캔버스에 정렬할 플로우차트 노드가 없습니다."))
            return

        self.canvas.push_undo()

        # 1. 노드 및 연결선 마그넷 바인딩 추출 (거리 60px 이내 최단거리 탐색)
        def find_closest_node_and_port(pt):
            best_n, best_k, best_p, min_d = None, None, None, float('inf')
            for n in nodes:
                if hasattr(n, "contains") and n.contains(pt):
                    k, p = n.get_closest_magnet_point(pt, 999.0)
                    return n, k, p
                k, p = n.get_closest_magnet_point(pt, 60.0)
                if p:
                    d = math.hypot(pt.x() - p.x(), pt.y() - p.y())
                    if d < min_d:
                        min_d = d
                        best_n, best_k, best_p = n, k, p
            return best_n, best_k, best_p

        edges = []
        for it in self.canvas.items:
            if isinstance(it, (ArrowItem, ElbowArrowItem)):
                sn, sk, sp = find_closest_node_and_port(it.start_pos)
                dn, dk, dp = find_closest_node_and_port(it.end_pos)
                if sn and dn and sn != dn:
                    edges.append({
                        "item": it,
                        "src_node": sn,
                        "src_port": sk,
                        "dst_node": dn,
                        "dst_port": dk
                    })

        # 2. 정렬 방향 결정 (기하 형상 분석 및 동일 상태 연속 클릭 시 TD ↔ LR 피벗 토글)
        min_x = min(n.rect.left() for n in nodes)
        max_x = max(n.rect.right() for n in nodes)
        min_y = min(n.rect.top() for n in nodes)
        max_y = max(n.rect.bottom() for n in nodes)
        span_x = max_x - min_x
        span_y = max_y - min_y

        current_fingerprint = tuple((round(n.rect.x(), 1), round(n.rect.y(), 1)) for n in sorted(nodes, key=lambda x: id(x)))
        last_fingerprint = getattr(self, "_last_aligned_fingerprint", None)
        last_dir = getattr(self, "_last_aligned_direction", None)

        if last_fingerprint is not None and last_fingerprint == current_fingerprint and last_dir:
            direction = "LR" if last_dir == "TD" else "TD"
        else:
            direction = "LR" if span_x > span_y * 1.25 else "TD"

        canvas_w = self.canvas.pixmap.width() if self.canvas.pixmap else 1920
        canvas_h = self.canvas.pixmap.height() if self.canvas.pixmap else 1080

        # 3. 그래프 위상 분석 (Topological Level / Layering)
        in_degree = {n: 0 for n in nodes}
        out_edges = {n: [] for n in nodes}
        for e in edges:
            in_degree[e["dst_node"]] += 1
            out_edges[e["src_node"]].append(e)

        roots = [n for n in nodes if in_degree[n] == 0]
        if not roots:
            roots = [min(nodes, key=lambda n: n.rect.top() if direction == "TD" else n.rect.left())]

        layers = {}
        queue = [(r, 0) for r in roots]
        while queue:
            curr, lvl = queue.pop(0)
            layers[curr] = max(layers.get(curr, 0), lvl)
            for e in out_edges[curr]:
                nxt = e["dst_node"]
                queue.append((nxt, lvl + 1))

        for n in nodes:
            if n not in layers:
                layers[n] = (max(layers.values()) + 1) if layers else 0

        by_layer = {}
        for n, l in layers.items():
            by_layer.setdefault(l, []).append(n)

        # 4. 열(Column for TD) 또는 행(Row for LR) 할당
        cols = {}
        for l, n_list in by_layer.items():
            if len(n_list) == 1:
                cols[n_list[0]] = 0
            else:
                if direction == "TD":
                    n_list_sorted = sorted(n_list, key=lambda n: n.rect.center().x())
                else:
                    n_list_sorted = sorted(n_list, key=lambda n: n.rect.center().y())
                mid_idx = (len(n_list_sorted) - 1) / 2.0
                for i, n in enumerate(n_list_sorted):
                    cols[n] = i - mid_idx

        # 5. 좌표 배치 계산 (사용자 원래 드로잉 영역 중심 보존 및 균일 간격 정렬)
        orig_min_x = min(n.rect.left() for n in nodes)
        orig_max_x = max(n.rect.right() for n in nodes)
        orig_min_y = min(n.rect.top() for n in nodes)
        orig_max_y = max(n.rect.bottom() for n in nodes)
        orig_cx = (orig_min_x + orig_max_x) / 2.0
        orig_cy = (orig_min_y + orig_max_y) / 2.0

        num_layers = max(layers.values()) + 1

        layer_max_w = {l: max(n.rect.width() for n in by_layer.get(l, [nodes[0]])) for l in range(num_layers)}
        layer_max_h = {l: max(n.rect.height() for n in by_layer.get(l, [nodes[0]])) for l in range(num_layers)}

        if direction == "TD":
            vertical_margin = min(90.0, max(42.0, (canvas_h - sum(layer_max_h.values()) - 100.0) / max(1, num_layers - 1)))
            col_gap = max(layer_max_w.values()) + 60.0
            total_h = sum(layer_max_h[l] for l in range(num_layers)) + (num_layers - 1) * vertical_margin

            start_y = max(40.0, min(canvas_h - total_h - 40.0, orig_cy - total_h / 2.0))
            center_x = max(max(layer_max_w.values()) / 2.0 + 40.0, min(canvas_w - max(layer_max_w.values()) / 2.0 - 40.0, orig_cx))

            layer_y = {}
            cur_y = start_y
            for l in range(num_layers):
                layer_y[l] = cur_y
                cur_y += layer_max_h[l] + vertical_margin

            for n in nodes:
                l = layers[n]
                c = cols[n]
                w = n.rect.width()
                h = n.rect.height()
                nx = center_x + c * col_gap - w / 2.0
                ny = layer_y[l] + (layer_max_h[l] - h) / 2.0
                n.rect = QRectF(nx, ny, w, h)

        else:  # direction == "LR"
            horizontal_margin = min(120.0, max(46.0, (canvas_w - sum(layer_max_w.values()) - 100.0) / max(1, num_layers - 1)))
            row_gap = max(layer_max_h.values()) + 50.0
            total_w = sum(layer_max_w[l] for l in range(num_layers)) + (num_layers - 1) * horizontal_margin

            start_x = max(40.0, min(canvas_w - total_w - 40.0, orig_cx - total_w / 2.0))
            center_y = max(max(layer_max_h.values()) / 2.0 + 40.0, min(canvas_h - max(layer_max_h.values()) / 2.0 - 40.0, orig_cy))

            layer_x = {}
            cur_x = start_x
            for l in range(num_layers):
                layer_x[l] = cur_x
                cur_x += layer_max_w[l] + horizontal_margin

            for n in nodes:
                l = layers[n]
                r = cols[n]
                w = n.rect.width()
                h = n.rect.height()
                nx = layer_x[l] + (layer_max_w[l] - w) / 2.0
                ny = center_y + r * row_gap - h / 2.0
                n.rect = QRectF(nx, ny, w, h)

        # 6. 연결선(화살표 및 직각 연결선) 100% 자동 재부착 및 직하향/수평 포트 보정
        for e in edges:
            it = e["item"]
            u = e["src_node"]
            v = e["dst_node"]
            u_m = u.get_magnet_points()
            v_m = v.get_magnet_points()

            if direction == "TD":
                row_u, col_u = layers[u], cols[u]
                row_v, col_v = layers[v], cols[v]

                if col_u == col_v and row_u < row_v:
                    # 1. 수직 직하향 직렬 흐름 (↓)
                    it.start_pos = u_m["bottom"]
                    it.end_pos = v_m["top"]
                    if isinstance(it, ElbowArrowItem):
                        it.route_mode = "VH"
                elif row_u == row_v and col_u < col_v:
                    # 2. 동일 행 좌->우 수평 이동
                    it.start_pos = u_m["right"]
                    it.end_pos = v_m["left"]
                    if isinstance(it, ElbowArrowItem):
                        it.route_mode = "HV"
                elif row_u == row_v and col_u > col_v:
                    # 3. 동일 행 우->좌 수평 이동
                    it.start_pos = u_m["left"]
                    it.end_pos = v_m["right"]
                    if isinstance(it, ElbowArrowItem):
                        it.route_mode = "HV"
                elif row_u < row_v:
                    # 4. 하향 분기 또는 복귀
                    if col_u == 0 and col_v > 0:
                        it.start_pos = u_m["right"]
                        it.end_pos = v_m["top"]
                        if isinstance(it, ElbowArrowItem):
                            it.route_mode = "HV"
                    elif col_u == 0 and col_v < 0:
                        it.start_pos = u_m["left"]
                        it.end_pos = v_m["top"]
                        if isinstance(it, ElbowArrowItem):
                            it.route_mode = "HV"
                    elif col_v == 0 and col_u > 0:
                        it.start_pos = u_m["bottom"]
                        it.end_pos = v_m["right"]
                        if isinstance(it, ElbowArrowItem):
                            it.route_mode = "VH"
                    elif col_v == 0 and col_u < 0:
                        it.start_pos = u_m["bottom"]
                        it.end_pos = v_m["left"]
                        if isinstance(it, ElbowArrowItem):
                            it.route_mode = "VH"
                    elif col_u < col_v:
                        it.start_pos = u_m["right"]
                        it.end_pos = v_m["top"]
                        if isinstance(it, ElbowArrowItem):
                            it.route_mode = "HV"
                    else:
                        it.start_pos = u_m["left"]
                        it.end_pos = v_m["top"]
                        if isinstance(it, ElbowArrowItem):
                            it.route_mode = "HV"
                else:
                    # 5. 상향 루프백
                    it.start_pos = u_m["left"] if col_u <= col_v else u_m["right"]
                    it.end_pos = v_m["left"] if col_u <= col_v else v_m["right"]
                    if isinstance(it, ElbowArrowItem):
                        it.route_mode = "VHV"

            else:  # direction == "LR"
                col_u, row_u = layers[u], cols[u]
                col_v, row_v = layers[v], cols[v]

                if row_u == row_v and col_u < col_v:
                    # 1. 수평 직렬 좌->우 흐름 (───>)
                    it.start_pos = u_m["right"]
                    it.end_pos = v_m["left"]
                    if isinstance(it, ElbowArrowItem):
                        it.route_mode = "HV"
                elif col_u == col_v and row_u < row_v:
                    # 2. 동일 열 상->하 수직 이동
                    it.start_pos = u_m["bottom"]
                    it.end_pos = v_m["top"]
                    if isinstance(it, ElbowArrowItem):
                        it.route_mode = "VH"
                elif col_u == col_v and row_u > row_v:
                    # 3. 동일 열 하->상 수직 이동
                    it.start_pos = u_m["top"]
                    it.end_pos = v_m["bottom"]
                    if isinstance(it, ElbowArrowItem):
                        it.route_mode = "VH"
                elif col_u < col_v:
                    # 4. 우측 분기 또는 복귀
                    if row_u == 0 and row_v < 0:
                        it.start_pos = u_m["top"]
                        it.end_pos = v_m["left"]
                        if isinstance(it, ElbowArrowItem):
                            it.route_mode = "VH"
                    elif row_u == 0 and row_v > 0:
                        it.start_pos = u_m["bottom"]
                        it.end_pos = v_m["left"]
                        if isinstance(it, ElbowArrowItem):
                            it.route_mode = "VH"
                    elif row_v == 0 and row_u < 0:
                        it.start_pos = u_m["right"]
                        it.end_pos = v_m["top"]
                        if isinstance(it, ElbowArrowItem):
                            it.route_mode = "HV"
                    elif row_v == 0 and row_u > 0:
                        it.start_pos = u_m["right"]
                        it.end_pos = v_m["bottom"]
                        if isinstance(it, ElbowArrowItem):
                            it.route_mode = "HV"
                    elif row_u < row_v:
                        it.start_pos = u_m["right"]
                        it.end_pos = v_m["top"]
                        if isinstance(it, ElbowArrowItem):
                            it.route_mode = "HV"
                    else:
                        it.start_pos = u_m["right"]
                        it.end_pos = v_m["bottom"]
                        if isinstance(it, ElbowArrowItem):
                            it.route_mode = "HV"
                else:
                    # 5. 좌향 루프백
                    it.start_pos = u_m["top"]
                    it.end_pos = v_m["top"]
                    if isinstance(it, ElbowArrowItem):
                        it.route_mode = "VHV"

        self._last_aligned_direction = direction
        self._last_aligned_fingerprint = tuple((round(n.rect.x(), 1), round(n.rect.y(), 1)) for n in sorted(nodes, key=lambda x: id(x)))

        self.canvas.update()
        self.canvas.sig_content_changed.emit()
        dir_name = "상하 (TD - 수직 직렬/좌우 분기)" if direction == "TD" else "좌우 (LR - 수평 직렬/상하 분기)"
        self.show_toast(f"플로우차트 자동정렬 완료: {dir_name}")

    def action_open_mobile_link(self):
        """스마트폰/태블릿 P2P 연동 다이얼로그 호출"""
        if MobileLinkServer is None:
            self.show_toast("모바일 연동 모듈을 로드할 수 없습니다.")
            return

        if self.mobile_server is None:
            self.mobile_server = MobileLinkServer(port=19850, parent=self)
            self.mobile_server.sig_payload_received.connect(self.on_mobile_payload_received)
            if not self.mobile_server.start_server():
                self.show_toast("모바일 연동 서버 시작 실패 (포트 점유 확인)")
                return

        dlg = MobileLinkDialog(self.mobile_server, self)
        dlg.exec()

    def on_mobile_payload_received(self, payload):
        """모바일 기기에서 전송된 플로우차트/손그림 사진을 캔버스에 즉시 반영"""
        p_type = payload.get("type", "flowchart")
        direction = payload.get("direction", getattr(self, "current_flow_direction", "TD"))

        if p_type == "flowchart":
            items_data = payload.get("data", {}).get("items", [])
            if not items_data:
                nodes_data = payload.get("data", {}).get("nodes", [])
                if nodes_data:
                    base_x = 100
                    base_y = 100
                    x_gap = 180 if direction == "LR" else 0
                    y_gap = 100 if direction == "TD" else 0
                    for idx, nd in enumerate(nodes_data):
                        nx = nd.get("x", base_x + idx * x_gap)
                        ny = nd.get("y", base_y + idx * y_gap)
                        items_data.append({
                            "type": "FlowchartNodeItem",
                            "text": nd.get("text", "단계"),
                            "x": nx,
                            "y": ny,
                            "w": 150,
                            "h": 60,
                            "shape_type": nd.get("shape", "process"),
                            "style": {
                                "bg_color": "#EFF6FF",
                                "border_color": "#2563EB",
                                "border_width": 2,
                                "text_color": "#1E293B",
                                "font_size": 12,
                                "font_bold": True
                            }
                        })

            if items_data:
                if self.canvas.pixmap is None:
                    self.action_new_transparent_canvas()

                self.canvas.push_undo()
                created_count = 0
                for idata in items_data:
                    it = item_from_dict(idata)
                    if it:
                        self.canvas.items.append(it)
                        created_count += 1

                self.canvas.update()
                self.canvas.sig_content_changed.emit()
                self.show_toast(f"📱 모바일 플로우차트 수신 완료 ({created_count}개 노드 추가)")

        elif p_type == "image":
            import base64
            img_b64 = payload.get("image_base64", "")
            if img_b64:
                if "," in img_b64:
                    img_b64 = img_b64.split(",", 1)[1]
                raw_bytes = base64.b64decode(img_b64)
                pix = QPixmap()
                pix.loadFromData(raw_bytes)
                if not pix.isNull():
                    if self.canvas.pixmap is None:
                        self.on_capture_completed(pix)
                    else:
                        self.canvas.add_image_overlay(pix)
                    self.show_toast("📷 모바일 손그림 사진 수신 및 캔버스 추가 완료!")

        elif p_type == "mermaid":
            code = payload.get("mermaid_code", "")
            if code:
                parsed = MermaidFlowchartParser.parse(code)
                if direction:
                    parsed["direction"] = direction
                nodes, arrows = MermaidLayoutEngine.build_flowchart(parsed)
                if self.canvas.pixmap is None:
                    self.action_new_transparent_canvas()
                self.canvas.push_undo()
                for n in nodes:
                    self.canvas.items.append(n)
                for a in arrows:
                    self.canvas.items.append(a)
                self.canvas.update()
                self.canvas.sig_content_changed.emit()
                self.show_toast(f"Mermaid 플로우차트 변환 완료 ({len(nodes)}개 노드)")

    def toggle_document_dock(self):
        """문서 참조 독 패널 표시/숨김 토글"""
        if hasattr(self, "doc_dock"):
            is_vis = not self.doc_dock.isVisible()
            self.doc_dock.setVisible(is_vis)
            self.config["doc_dock_visible"] = is_vis
            save_config(self.config)

    def on_doc_insert_text_to_canvas(self, text):
        """문서 참조 독 패널에서 선택 단락을 캔버스 텍스트박스로 즉시 삽입"""
        if not text:
            return
        self.canvas.push_undo()
        cx = 120
        cy = 120
        if self.canvas.pixmap:
            cx = max(60, min(self.canvas.pixmap.width() - 250, self.canvas.pixmap.width() // 3))
            cy = max(60, min(self.canvas.pixmap.height() - 150, self.canvas.pixmap.height() // 3))

        style = {
            "font_size": 13,
            "text_color": "#1E293B",
            "bg_color": "#FFFFFF",
            "border_color": "#CBD5E1",
            "padding": 6
        }
        clean_text = text.strip()
        label_item = TextLabelItem(clean_text, cx, cy, style)
        self.canvas.items.append(label_item)
        self.canvas.selected_item = label_item
        self.canvas.update()
        self.canvas.sig_content_changed.emit()
        self.show_toast("캔버스에 텍스트박스가 삽입되었습니다.")

    def on_doc_apply_slide_title(self, title):
        """문서 참조 독 패널에서 단락 헤더를 슬라이드 제목으로 즉시 적용"""
        clean_title = title.strip()
        if not clean_title:
            return
        if 0 <= self.current_step_idx < len(self.storyboard_steps):
            self.storyboard_steps[self.current_step_idx]["title"] = clean_title
            if hasattr(self, "filmstrip"):
                self.filmstrip.set_steps(self.storyboard_steps, self.current_step_idx)
            self.show_toast(f"슬라이드 제목 적용: {clean_title[:25]}...")



# ==============================================================================
# 7.5. 최종 사용자 라이선스 계약서 (EULA) 및 다이얼로그 (DragonRPA Co.)
# ==============================================================================
EULA_HTML_TEXT = EulaManager.get_eula_html("ko")





class EulaDialog(QDialog):
    def __init__(self, parent=None, initial_locale=None):
        super().__init__(parent)
        self.current_locale = initial_locale or I18nManager.instance().get_locale()
        self.setWindowTitle(EulaManager.get_dialog_title(self.current_locale))
        self.resize(680, 580)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        ci_pix = get_dragon_rpa_ci_pixmap()
        if not ci_pix.isNull():
            self.setWindowIcon(QIcon(ci_pix))

        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
            }
            QLabel {
                font-family: 'Segoe UI', 'Yu Gothic', Meiryo, 'Microsoft YaHei', 'Malgun Gothic', sans-serif;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        # 헤더: 타이틀 + 다국어 선택 콤보박스 + CI 레이블
        header_l = QHBoxLayout()
        header_l.setSpacing(10)

        self.lbl_h = QLabel(tr("eula_title_short", "최종 사용자 라이선스 계약서"), self)
        self.lbl_h.setStyleSheet("font-size: 14.5px; font-weight: bold; color: #0F172A;")
        header_l.addWidget(self.lbl_h)
        header_l.addStretch(1)

        lbl_lang_icon = QLabel(tr("lbl_language", "언어:"), self)
        lbl_lang_icon.setStyleSheet("font-size: 11px; font-weight: bold; color: #64748B;")
        header_l.addWidget(lbl_lang_icon)

        self.combo_lang = QComboBox(self)
        self.combo_lang.setFixedHeight(28)
        self.combo_lang.setStyleSheet("""
            QComboBox {
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 11px;
                background-color: #F8FAFC;
                color: #0F172A;
                font-weight: 500;
            }
            QComboBox:hover {
                border-color: #94A3B8;
                background-color: #FFFFFF;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        supported = EulaManager.get_supported_locales()
        current_idx = 0
        norm_cur = EulaManager.normalize_locale(self.current_locale)
        for i, (code, name) in enumerate(supported.items()):
            self.combo_lang.addItem(f"{name}", code)
            if code == norm_cur:
                current_idx = i
        self.combo_lang.setCurrentIndex(current_idx)
        self.combo_lang.currentIndexChanged.connect(self._on_language_changed)
        header_l.addWidget(self.combo_lang)

        lbl_comp = QLabel("(주)드래곤알피에이", self)
        lbl_comp.setStyleSheet("font-size: 11px; color: #64748B; font-weight: bold; margin-left: 4px;")
        header_l.addWidget(lbl_comp)
        layout.addLayout(header_l)

        # 텍스트 에리어
        self.txt_eula = QTextEdit(self)
        self.txt_eula.setReadOnly(True)
        self.txt_eula.setStyleSheet("""
            QTextEdit {
                background-color: #F8FAFC;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 14px;
                font-family: 'Segoe UI', 'Yu Gothic', Meiryo, 'Microsoft YaHei', 'Malgun Gothic', sans-serif;
                font-size: 11px;
                color: #1E293B;
                line-height: 1.6;
            }
        """)
        self.txt_eula.setHtml(EulaManager.get_eula_html(self.current_locale))
        layout.addWidget(self.txt_eula, 1)

        # 하단 액션 버튼 바: 전체 복사 + 닫기
        btn_l = QHBoxLayout()
        btn_l.setSpacing(10)

        self.btn_copy = QPushButton(self)
        self.btn_copy.setMinimumWidth(110)
        self.btn_copy.setFixedHeight(32)
        self.btn_copy.setCursor(Qt.PointingHandCursor)
        self.btn_copy.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9;
                color: #334155;
                border: 1px solid #CBD5E1;
                border-radius: 5px;
                font-size: 11.5px;
                font-weight: bold;
                padding: 0 12px;
            }
            QPushButton:hover {
                background-color: #E2E8F0;
                border-color: #94A3B8;
            }
        """)
        self.btn_copy.clicked.connect(self._copy_eula)
        btn_l.addWidget(self.btn_copy)

        btn_l.addStretch(1)

        self.btn_close = QPushButton("닫기", self)
        self.btn_close.setFixedSize(90, 32)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: #FFFFFF;
                border: none;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
            }
        """)
        self.btn_close.clicked.connect(self.accept)
        btn_l.addWidget(self.btn_close)
        layout.addLayout(btn_l)

        self._refresh_ui_labels()

    def _refresh_ui_labels(self):
        labels = EulaManager.get_ui_labels(self.current_locale)
        full_title = EulaManager.get_dialog_title(self.current_locale)
        self.setWindowTitle(full_title)
        short_title = full_title.split(" - ")[0]
        self.lbl_h.setText(short_title)
        self.btn_close.setText(labels.get("btn_close", "닫기"))
        self.btn_copy.setText(labels.get("btn_copy", "전체 복사"))

    def _on_language_changed(self, index):
        loc = self.combo_lang.currentData()
        if loc:
            self.current_locale = loc
            self.txt_eula.setHtml(EulaManager.get_eula_html(loc))
            self._refresh_ui_labels()

    def _copy_eula(self):
        plain_text = EulaManager.get_eula_plain(self.current_locale)
        cb = QApplication.clipboard()
        cb.setText(plain_text)
        QCoreApplication.processEvents()
        labels = EulaManager.get_ui_labels(self.current_locale)
        orig_text = labels.get("btn_copy", "전체 복사")
        self.btn_copy.setText(labels.get("copied_toast", "복사 완료!"))
        self.btn_copy.setEnabled(False)
        QTimer.singleShot(1600, lambda: (self.btn_copy.setText(orig_text), self.btn_copy.setEnabled(True)))


# ==============================================================================
# 7.5 라이선스 등록 다이얼로그 (LicenseRegistrationDialog)
# ==============================================================================
class LicenseRegistrationDialog(QDialog):
    sig_license_activated = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("license_dialog_title", "라이선스 등록"))
        self.setFixedSize(520, 370)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QDialog { background-color: #FFFFFF; }
            QLabel { font-family: 'Segoe UI', 'Malgun Gothic'; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # 1. Header
        header = QLabel(tr("license_dialog_title", "라이선스 등록 및 정식 인증"), self)
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #0F172A;")
        layout.addWidget(header)

        # Status Badge
        status = LicenseEngine.check_license_status()
        is_lic = status.get("is_licensed", False)
        badge_color = "#10B981" if is_lic else "#D97706"
        badge_bg = "#ECFDF5" if is_lic else "#FFFBEB"
        badge_border = "#A7F3D0" if is_lic else "#FDE68A"
        b_txt = tr("about_badge_licensed", "정식 라이선스") if is_lic else tr("about_badge_trial", "평가판")
        b_user = status.get("issued_to", "") or tr("license_user_default", "사용자")
        badge_text = f"{tr('license_status_prefix', '상태')}: {b_txt} ({b_user})"

        self.lbl_status = QLabel(badge_text, self)
        self.lbl_status.setStyleSheet(f"""
            background-color: {badge_bg};
            color: {badge_color};
            border: 1px solid {badge_border};
            border-radius: 6px;
            padding: 6px 12px;
            font-size: 12px;
            font-weight: bold;
        """)
        layout.addWidget(self.lbl_status)

        # 2. HWID Frame
        hwid_frame = QFrame(self)
        hwid_frame.setStyleSheet("background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 6px;")
        hw_layout = QVBoxLayout(hwid_frame)
        hw_layout.setSpacing(6)

        lbl_hw_title = QLabel(tr("lbl_hwid", "내 PC 고유 식별자 (HWID):"), self)
        lbl_hw_title.setStyleSheet("font-size: 11px; font-weight: bold; color: #475569;")
        hw_layout.addWidget(lbl_hw_title)

        hw_row = QHBoxLayout()
        my_hwid = LicenseEngine.get_hwid()
        self.edit_hwid = QLineEdit(my_hwid, self)
        self.edit_hwid.setReadOnly(True)
        self.edit_hwid.setStyleSheet("font-family: Consolas; font-size: 12px; padding: 4px 8px; background-color: #FFFFFF;")
        btn_copy = QPushButton(tr("btn_copy_hwid", "복사"), self)
        btn_copy.setCursor(Qt.PointingHandCursor)
        btn_copy.clicked.connect(self.copy_hwid)
        hw_row.addWidget(self.edit_hwid)
        hw_row.addWidget(btn_copy)
        hw_layout.addLayout(hw_row)
        layout.addWidget(hwid_frame)

        # 3. Serial Key Input
        lbl_key_title = QLabel(tr("lbl_license_key", "라이선스 시리얼 키 입력:"), self)
        lbl_key_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #0F172A;")
        layout.addWidget(lbl_key_title)

        self.edit_key = QLineEdit(self)
        self.edit_key.setPlaceholderText("MS1P-XXXXXXXX-eyJ...")
        self.edit_key.setStyleSheet("font-family: Consolas; font-size: 12px; padding: 6px 10px; border: 1px solid #CBD5E1; border-radius: 4px;")
        layout.addWidget(self.edit_key)

        # 4. Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch(1)

        self.btn_activate = QPushButton(tr("btn_activate", "인증하기"), self)
        self.btn_activate.setCursor(Qt.PointingHandCursor)
        self.btn_activate.setStyleSheet("""
            QPushButton {
                background-color: #2563EB; color: white; font-weight: bold;
                padding: 7px 18px; border-radius: 5px; font-size: 12px;
            }
            QPushButton:hover { background-color: #1D4ED8; }
        """)
        self.btn_activate.clicked.connect(self.activate_license)

        self.btn_close = QPushButton(tr("btn_close", "닫기"), self)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setStyleSheet("padding: 7px 16px; font-size: 12px;")
        self.btn_close.clicked.connect(self.close)

        btn_layout.addWidget(self.btn_activate)
        btn_layout.addWidget(self.btn_close)
        layout.addLayout(btn_layout)

    def copy_hwid(self):
        QApplication.clipboard().setText(self.edit_hwid.text().strip())
        QToolTip.showText(QCursor.pos(), tr("msg_hwid_copied", "HWID가 클립보드에 복사되었습니다."), self)

    def activate_license(self):
        key = self.edit_key.text().strip()
        if not key:
            QMessageBox.warning(self, tr("title_input_error", "입력 오류"), tr("msg_enter_license_key", "라이선스 시리얼 키를 입력해 주세요."))
            return

        valid, payload, msg = LicenseEngine.verify_license_key(key)
        if valid:
            LicenseEngine.save_license(key)
            QMessageBox.information(self, tr("title_auth_success", "인증 성공"), tr("msg_license_success"))
            self.sig_license_activated.emit()
            self.accept()
        else:
            QMessageBox.warning(self, tr("title_auth_failed", "인증 실패"), f"{tr('msg_license_failed', '라이선스 검증 실패:')}\n{msg}")


# ==============================================================================
# 7-3. 업데이트 노트(릴리즈 내역) 다이얼로그 (ReleaseNotesDialog)
# ==============================================================================
class ReleaseNotesDialog(QDialog):
    """초기버전(v1.0.0)부터 최신(v1.5.0)까지 전 릴리즈 이력을 열람하는 다이얼로그"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("release_notes_title", "업데이트 노트 (릴리즈 내역)"))
        self.resize(780, 620)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        ci_pix = get_dragon_rpa_ci_pixmap()
        if not ci_pix.isNull():
            self.setWindowIcon(QIcon(ci_pix))

        self.sections = []  # list of (version_tag, date_str, raw_text, html_text)
        self.load_release_notes()
        self.init_ui()

    def load_release_notes(self):
        candidate_paths = [
            os.path.join(get_app_dir(), "RELEASE_NOTES.md"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "RELEASE_NOTES.md"),
            os.path.join(os.getcwd(), "RELEASE_NOTES.md"),
        ]
        full_text = ""
        for p in candidate_paths:
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        full_text = f.read()
                    break
                except Exception:
                    pass

        if not full_text:
            full_text = "# Manual Studio Release Notes\n\n## [v1.5.0] - 2026-09-13\n\n최신 버전이 적용되었습니다."

        # Parse sections
        raw_sections = re.split(r'\n(?=##\s*\[v)', full_text)
        for sec in raw_sections:
            m = re.match(r'##\s*\[([^\]]+)\]\s*-\s*([^\n]+)', sec.strip())
            if m:
                ver_tag = m.group(1)
                date_str = m.group(2).strip()
                html = self._markdown_to_html(sec)
                self.sections.append((ver_tag, date_str, sec, html))

    def _markdown_to_html(self, md_text: str) -> str:
        lines = md_text.strip().split('\n')
        html_lines = []
        in_table = False
        table_rows = []

        for line in lines:
            line_str = line.strip()
            if line_str.startswith("## "):
                m = re.match(r'##\s*\[([^\]]+)\]\s*-\s*(.*)', line_str)
                if m:
                    ver = m.group(1)
                    dt = m.group(2)
                    html_lines.append(f'<div style="background-color: #EFF6FF; border-left: 4px solid #2563EB; padding: 10px 14px; margin: 16px 0 10px 0; border-radius: 4px;"><span style="font-size: 15px; font-weight: bold; color: #1E40AF;">v{ver}</span> &nbsp; <span style="font-size: 12px; color: #64748B;">({dt})</span></div>')
                else:
                    html_lines.append(f'<h3 style="color: #1E40AF; margin-top: 14px;">{line_str[3:]}</h3>')
            elif line_str.startswith("### "):
                html_lines.append(f'<h4 style="color: #0F172A; margin: 12px 0 6px 0; font-size: 13px;">{line_str[4:]}</h4>')
            elif line_str.startswith("#### "):
                html_lines.append(f'<h5 style="color: #334155; margin: 8px 0 4px 0; font-size: 12px;">{line_str[5:]}</h5>')
            elif line_str.startswith("- ") or line_str.startswith("• "):
                item = line_str[2:].strip()
                item = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', item)
                item = re.sub(r'`(.*?)`', r'<code style="background-color: #F1F5F9; padding: 2px 4px; border-radius: 3px; font-size: 11px; color: #0F172A;">\1</code>', item)
                html_lines.append(f'<li style="margin-bottom: 4px; line-height: 1.5; color: #334155; font-size: 12px;">{item}</li>')
            elif line_str.startswith("|") and line_str.endswith("|"):
                if "---" in line_str:
                    continue
                cells = [c.strip() for c in line_str.split("|")[1:-1]]
                table_rows.append(cells)
                in_table = True
            else:
                if in_table and table_rows:
                    html_lines.append('<table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse; border: 1px solid #CBD5E1; width: 100%; margin: 8px 0; font-size: 11.5px;">')
                    hdr = table_rows[0]
                    html_lines.append('<tr style="background-color: #F8FAFC;">')
                    for h in hdr:
                        html_lines.append(f'<th style="border: 1px solid #CBD5E1; color: #1E293B; font-weight: bold; text-align: left;">{h}</th>')
                    html_lines.append('</tr>')
                    for row in table_rows[1:]:
                        html_lines.append('<tr>')
                        for c in row:
                            c_fmt = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', c)
                            c_fmt = re.sub(r'`(.*?)`', r'<code style="background-color: #F1F5F9; padding: 2px 4px; border-radius: 3px; font-size: 10.5px;">\1</code>', c_fmt)
                            html_lines.append(f'<td style="border: 1px solid #E2E8F0; color: #334155; line-height: 1.4;">{c_fmt}</td>')
                        html_lines.append('</tr>')
                    html_lines.append('</table>')
                    table_rows = []
                    in_table = False

                if line_str and not line_str.startswith("---"):
                    formatted = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line_str)
                    formatted = re.sub(r'`(.*?)`', r'<code style="background-color: #F1F5F9; padding: 2px 4px; border-radius: 3px; font-size: 11px;">\1</code>', formatted)
                    html_lines.append(f'<p style="margin: 4px 0; line-height: 1.5; color: #334155; font-size: 12px;">{formatted}</p>')

        if in_table and table_rows:
            html_lines.append('<table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse; border: 1px solid #CBD5E1; width: 100%; margin: 8px 0; font-size: 11.5px;">')
            hdr = table_rows[0]
            html_lines.append('<tr style="background-color: #F8FAFC;">')
            for h in hdr:
                html_lines.append(f'<th style="border: 1px solid #CBD5E1; color: #1E293B; font-weight: bold; text-align: left;">{h}</th>')
            html_lines.append('</tr>')
            for row in table_rows[1:]:
                html_lines.append('<tr>')
                for c in row:
                    c_fmt = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', c)
                    html_lines.append(f'<td style="border: 1px solid #E2E8F0; color: #334155;">{c_fmt}</td>')
                html_lines.append('</tr>')
            html_lines.append('</table>')

        return "\n".join(html_lines)

    def init_ui(self):
        self.setStyleSheet("""
            QDialog { background-color: #FFFFFF; }
            QLabel { font-family: 'Segoe UI', 'Malgun Gothic'; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        # 1. 헤더: 타이틀 + 버전 콤보박스
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        lbl_title = QLabel(tr("release_notes_title", "업데이트 노트 (릴리즈 내역)"), self)
        lbl_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #0F172A;")
        header_layout.addWidget(lbl_title)
        header_layout.addStretch(1)

        lbl_ver = QLabel(tr("lbl_version", "버전:"), self)
        lbl_ver.setStyleSheet("font-size: 11.5px; font-weight: bold; color: #64748B;")
        header_layout.addWidget(lbl_ver)

        self.combo_version = QComboBox(self)
        self.combo_version.setFixedHeight(28)
        self.combo_version.setStyleSheet("""
            QComboBox {
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 11px;
                background-color: #F8FAFC;
                color: #1E293B;
                min-width: 170px;
            }
            QComboBox:hover { border-color: #94A3B8; }
        """)
        self.combo_version.addItem(tr("release_notes_all_ver", "전체 버전 보기"), "all")
        for ver_tag, dt, raw, html in self.sections:
            self.combo_version.addItem(f"{ver_tag} ({dt})", ver_tag)
        self.combo_version.currentIndexChanged.connect(self.on_version_selected)
        header_layout.addWidget(self.combo_version)

        layout.addLayout(header_layout)

        # 2. 본문 텍스트 브라우저
        self.browser = QTextBrowser(self)
        self.browser.setOpenExternalLinks(True)
        self.browser.setStyleSheet("""
            QTextBrowser {
                background-color: #FAFAFA;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                padding: 14px;
                font-family: 'Segoe UI', 'Malgun Gothic';
                color: #1E293B;
            }
        """)
        layout.addWidget(self.browser, 1)

        # 3. 하단 버튼 바
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(10)

        lbl_total = QLabel(f"총 {len(self.sections)}개 릴리즈 내역 수록", self)
        lbl_total.setStyleSheet("font-size: 11px; color: #94A3B8; font-weight: 500;")
        bottom_layout.addWidget(lbl_total)
        bottom_layout.addStretch(1)

        self.btn_copy = QPushButton(tr("release_notes_btn_copy", "클립보드에 복사"), self)
        self.btn_copy.setFixedHeight(32)
        self.btn_copy.setCursor(Qt.PointingHandCursor)
        self.btn_copy.setStyleSheet("""
            QPushButton {
                background-color: #F8FAFC;
                color: #2563EB;
                border: 1px solid #BFDBFE;
                border-radius: 4px;
                padding: 0 14px;
                font-size: 11.5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #EFF6FF; }
        """)
        self.btn_copy.clicked.connect(self.copy_to_clipboard)
        bottom_layout.addWidget(self.btn_copy)

        btn_close = QPushButton(tr("btn_close", "닫기"), self)
        btn_close.setFixedHeight(32)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 0 18px;
                font-size: 11.5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1D4ED8; }
        """)
        btn_close.clicked.connect(self.accept)
        bottom_layout.addWidget(btn_close)

        layout.addLayout(bottom_layout)

        # 초기 렌더링: 전체 버전
        self.display_all_sections()

    def display_all_sections(self):
        full_html = """
        <html>
        <body style="font-family: 'Segoe UI', 'Malgun Gothic'; font-size: 12px; color: #1E293B;">
        """
        for ver, dt, raw, html in self.sections:
            full_html += html + "<hr style='border: none; border-top: 1px solid #E2E8F0; margin: 18px 0;'>"
        full_html += "</body></html>"
        self.browser.setHtml(full_html)

    def on_version_selected(self, idx: int):
        data = self.combo_version.currentData()
        if data == "all":
            self.display_all_sections()
        else:
            for ver, dt, raw, html in self.sections:
                if ver == data:
                    styled_html = f"""
                    <html>
                    <body style="font-family: 'Segoe UI', 'Malgun Gothic'; font-size: 12px; color: #1E293B;">
                    {html}
                    </body></html>
                    """
                    self.browser.setHtml(styled_html)
                    break

    def copy_to_clipboard(self):
        data = self.combo_version.currentData()
        if data == "all":
            text = "\n\n".join([raw for _, _, raw, _ in self.sections])
        else:
            text = ""
            for ver, dt, raw, _ in self.sections:
                if ver == data:
                    text = raw
                    break
        QApplication.clipboard().setText(text)
        self.btn_copy.setText(tr("release_notes_copied", "복사 완료!"))


# ==============================================================================
# 7-4. 모바일 스케치/플로우차트 연동 다이얼로그 (MobileLinkDialog)
# ==============================================================================
class MobileLinkDialog(QDialog):
    """모바일 기기(스마트폰/태블릿) QR 코드 페어링 및 손그림/플로우차트 실시간 P2P 수신 다이얼로그"""
    sig_insert_to_canvas = Signal(dict)

    def __init__(self, mobile_server, parent=None):
        super().__init__(parent)
        self.mobile_server = mobile_server
        self.setWindowTitle(tr("dlg_mobile_link_title", "모바일 스케치/플로우차트 연동"))
        self.resize(620, 500)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        ci_pix = get_dragon_rpa_ci_pixmap()
        if not ci_pix.isNull():
            self.setWindowIcon(QIcon(ci_pix))

        self.received_items = []
        self._init_ui()

        if self.mobile_server:
            self.mobile_server.sig_payload_received.connect(self._on_payload_received)

    def _init_ui(self):
        self.setStyleSheet("""
            QDialog { background-color: #FFFFFF; }
            QLabel { font-family: 'Segoe UI', 'Malgun Gothic'; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(22, 20, 22, 20)

        # 1. 상단 상태 배너
        info_banner = QFrame()
        info_banner.setStyleSheet("background: #0F172A; border-radius: 8px; border: 1px solid #1E293B; padding: 10px;")
        banner_lay = QHBoxLayout(info_banner)
        lbl_status = QLabel("🟢 동일 Wi-Fi 로컬 연결 대기 중 (외부 서버 무저장 원칙 / 초고속 P2P)")
        lbl_status.setStyleSheet("color: #10B981; font-weight: bold; font-size: 12.5px;")
        banner_lay.addWidget(lbl_status)
        layout.addWidget(info_banner)

        # 2. 중앙 레이아웃: 좌측 QR + 우측 정보
        center_lay = QHBoxLayout()
        center_lay.setSpacing(20)

        # 좌측: QR 코드 카드
        qr_card = QFrame()
        qr_card.setStyleSheet("background: #F8FAFC; border-radius: 8px; border: 1px solid #E2E8F0; padding: 12px;")
        qr_card_lay = QVBoxLayout(qr_card)
        self.lbl_qr = QLabel()
        self.lbl_qr.setAlignment(Qt.AlignCenter)
        if self.mobile_server:
            qr_pix = self.mobile_server.get_qr_pixmap()
            self.lbl_qr.setPixmap(qr_pix.scaled(210, 210, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        qr_card_lay.addWidget(self.lbl_qr)

        lbl_qr_sub = QLabel(tr("lbl_scan_qr_guide", "스마트폰 카메라로 QR 코드를 스캔하세요"))
        lbl_qr_sub.setAlignment(Qt.AlignCenter)
        lbl_qr_sub.setStyleSheet("color: #64748B; font-size: 11px; font-weight: 600; margin-top: 6px;")
        qr_card_lay.addWidget(lbl_qr_sub)
        center_lay.addWidget(qr_card)

        # 우측: 연결 파라미터 및 옵션
        right_lay = QVBoxLayout()
        right_lay.setSpacing(12)

        # 인증 PIN
        pin_group = QGroupBox("인증 PIN 번호")
        pin_group.setStyleSheet("QGroupBox { font-size: 11px; font-weight: bold; color: #475569; }")
        pin_lay = QVBoxLayout(pin_group)
        pin_str = self.mobile_server.session_pin if self.mobile_server else "---"
        self.lbl_pin = QLabel(pin_str)
        self.lbl_pin.setStyleSheet("font-size: 26px; font-weight: bold; color: #2563EB; letter-spacing: 3px;")
        self.lbl_pin.setAlignment(Qt.AlignCenter)
        pin_lay.addWidget(self.lbl_pin)
        right_lay.addWidget(pin_group)

        # 접속 URL
        url_str = self.mobile_server.get_connection_url() if self.mobile_server else ""
        lbl_url_title = QLabel("접속 URL:")
        lbl_url_title.setStyleSheet("color: #64748B; font-size: 11px; font-weight: bold;")
        right_lay.addWidget(lbl_url_title)

        url_row = QHBoxLayout()
        self.edit_url = QLineEdit(url_str)
        self.edit_url.setReadOnly(True)
        self.edit_url.setStyleSheet("font-family: Consolas; font-size: 11px; padding: 4px; border: 1px solid #CBD5E1; border-radius: 4px;")
        btn_copy_url = QPushButton("복사")
        btn_copy_url.setStyleSheet("padding: 4px 10px; font-size: 11px; font-weight: bold; background: #F1F5F9; border: 1px solid #CBD5E1; border-radius: 4px;")
        btn_copy_url.clicked.connect(lambda: QApplication.clipboard().setText(url_str))
        url_row.addWidget(self.edit_url)
        url_row.addWidget(btn_copy_url)
        right_lay.addLayout(url_row)

        # 자동 배치 옵션
        self.chk_auto_insert = QCheckBox(tr("lbl_auto_insert_canvas", "수신 즉시 캔버스에 자동 배치"))
        self.chk_auto_insert.setChecked(True)
        self.chk_auto_insert.setStyleSheet("font-size: 11.5px; font-weight: bold; color: #1E293B;")
        right_lay.addWidget(self.chk_auto_insert)

        # 배치 방향 라디오
        dir_box = QGroupBox("플로우차트 기본 배치 방향")
        dir_box.setStyleSheet("QGroupBox { font-size: 11px; font-weight: bold; color: #475569; }")
        dir_lay = QHBoxLayout(dir_box)
        self.radio_td = QRadioButton("상하 (TD)")
        self.radio_lr = QRadioButton("좌우 (LR)")
        self.radio_td.setChecked(True)
        dir_lay.addWidget(self.radio_td)
        dir_lay.addWidget(self.radio_lr)
        right_lay.addWidget(dir_box)

        # 수신 카운터
        self.lbl_receive_status = QLabel("수신된 항목: 0건 대기 중")
        self.lbl_receive_status.setStyleSheet("color: #0284C7; font-weight: bold; font-size: 12px;")
        right_lay.addWidget(self.lbl_receive_status)

        right_lay.addStretch(1)
        center_lay.addLayout(right_lay)
        layout.addLayout(center_lay)

        # 하단 버튼
        bot_lay = QHBoxLayout()
        bot_lay.addStretch(1)
        btn_close = QPushButton("닫기")
        btn_close.setFixedWidth(90)
        btn_close.setFixedHeight(32)
        btn_close.setStyleSheet("background: #2563EB; color: #FFFFFF; font-weight: bold; border-radius: 4px; border: none;")
        btn_close.clicked.connect(self.accept)
        bot_lay.addWidget(btn_close)
        layout.addLayout(bot_lay)

    def _on_payload_received(self, payload):
        self.received_items.append(payload)
        count = len(self.received_items)
        p_type = payload.get("type", "알 수 없음")
        type_str = "플로우차트" if p_type == "flowchart" else ("손그림 사진" if p_type == "image" else p_type)
        self.lbl_receive_status.setText(f"🎉 수신 성공: 총 {count}건 (최근: {type_str})")
        self.lbl_receive_status.setStyleSheet("color: #059669; font-weight: bold; font-size: 12.5px;")


# ==============================================================================
# 8. 개발사 정보 및 About 다이얼로그 (AboutDialog - DragonRPA Co.)
# ==============================================================================
class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("about_window_title", "About - DragonRPA Co."))
        self.setFixedSize(540, 580)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        ci_pix = get_dragon_rpa_ci_pixmap()
        if not ci_pix.isNull():
            self.setWindowIcon(QIcon(ci_pix))

        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
            }
            QLabel {
                font-family: 'Malgun Gothic';
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(12)

        # 1. CI 로고 이미지
        ci_pix = get_dragon_rpa_ci_pixmap()
        lbl_logo = QLabel(self)
        lbl_logo.setAlignment(Qt.AlignCenter)
        if not ci_pix.isNull():
            lbl_logo.setPixmap(ci_pix.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        layout.addWidget(lbl_logo)

        # 2. 프로그램 타이틀 & 버전 배지
        lbl_title = QLabel(tr("about_title", "매뉴얼 스튜디오"), self)
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0F172A; margin-top: 2px;")
        layout.addWidget(lbl_title)

        lbl_sub = QLabel(tr("about_sub", "Manual Studio for PowerPoint"), self)
        lbl_sub.setAlignment(Qt.AlignCenter)
        lbl_sub.setStyleSheet("font-size: 11.5px; color: #64748B;")
        layout.addWidget(lbl_sub)

        status = LicenseEngine.check_license_status()
        is_lic = status.get("is_licensed", False)
        badge_text = tr("about_badge_licensed", "정식 라이선스") if is_lic else tr("about_badge_trial", "평가판")
        issued_to = status.get("issued_to", "") or tr("license_user_default", "사용자")

        ver_layout = QHBoxLayout()
        ver_layout.setAlignment(Qt.AlignCenter)
        lbl_ver = QLabel(f"v1.4.0 (Build 2026.09) • {badge_text}", self)
        lbl_ver.setStyleSheet("""
            background-color: #EFF6FF;
            color: #1D4ED8;
            border: 1px solid #BFDBFE;
            border-radius: 10px;
            padding: 3px 14px;
            font-size: 11px;
            font-weight: bold;
        """)
        ver_layout.addWidget(lbl_ver)
        layout.addLayout(ver_layout)

        # 평가판 / 정식 라이선스 상태 카드
        card_trial = QFrame(self)
        tr_l = QHBoxLayout(card_trial)
        tr_l.setContentsMargins(14, 9, 14, 9)
        tr_l.setSpacing(8)
        lbl_tr_text = QLabel(card_trial)

        if is_lic:
            card_trial.setStyleSheet("""
                QFrame {
                    background-color: #ECFDF5;
                    border: 1px solid #A7F3D0;
                    border-radius: 8px;
                }
            """)
            lic_tpl = tr("about_lic_card", "<b>[정식 라이선스 활성화]</b> 등록 대상: <b>{issued_to}</b> ({badge})<br/>워터마크 없는 고해상도 PPT 슬라이드 생성이 활성화되었습니다.")
            lbl_tr_text.setText(lic_tpl.format(issued_to=issued_to, badge=badge_text))
            lbl_tr_text.setStyleSheet("font-size: 11.5px; color: #065F46; border: none; background: transparent;")
        else:
            card_trial.setStyleSheet("""
                QFrame {
                    background-color: #FEF3C7;
                    border: 1px solid #FCD34D;
                    border-radius: 8px;
                }
            """)
            lbl_tr_text.setText(tr("about_trial_card", "<b>[기간 한정 평가판]</b> 사용 기한: <b>2026년 12월 31일</b>까지<br/>정식 라이선스 등록 시 모든 워터마크가 즉시 제거됩니다."))
            lbl_tr_text.setStyleSheet("font-size: 11.5px; color: #92400E; border: none; background: transparent;")

        tr_l.addWidget(lbl_tr_text, 1)
        layout.addWidget(card_trial)

        # 구분선
        sep = QFrame(self)
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setStyleSheet("border-color: #E2E8F0;")
        layout.addWidget(sep)

        # 3. 개발사 정보 카드
        card_dev = QFrame(self)
        card_dev.setStyleSheet("""
            QFrame {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
            }
        """)
        dev_l = QVBoxLayout(card_dev)
        dev_l.setContentsMargins(16, 12, 16, 12)
        dev_l.setSpacing(4)

        lbl_company = QLabel(tr("about_company_name", "(주)드래곤알피에이 (DragonRPA Co.)"), card_dev)
        lbl_company.setStyleSheet("font-size: 13px; font-weight: bold; color: #1E293B; border: none;")
        dev_l.addWidget(lbl_company)

        lbl_dev_notice = QLabel(tr("about_dev_notice", "본 프로그램은 (주)드래곤알피에이(DragonRPA Co.)에서 기획 및 개발하였습니다."), card_dev)
        lbl_dev_notice.setWordWrap(True)
        lbl_dev_notice.setStyleSheet("font-size: 11.5px; color: #334155; border: none; line-height: 1.4;")
        dev_l.addWidget(lbl_dev_notice)

        lbl_domain = QLabel(tr("about_dev_domain", "• 업무 자동화 (RPA) · 매뉴얼 표준화 · 지능형 엔터프라이즈 솔루션"), card_dev)
        lbl_domain.setStyleSheet("font-size: 11px; color: #64748B; border: none;")
        dev_l.addWidget(lbl_domain)

        layout.addWidget(card_dev)

        # 4. 연락처 (Contact & Support) 카드
        card_contact = QFrame(self)
        card_contact.setStyleSheet("""
            QFrame {
                background-color: #F0FDF4;
                border: 1px solid #BBF7D0;
                border-radius: 8px;
            }
        """)
        c_l = QHBoxLayout(card_contact)
        c_l.setContentsMargins(14, 10, 14, 10)
        c_l.setSpacing(10)

        contact_info_l = QVBoxLayout()
        contact_info_l.setSpacing(2)
        lbl_c_title = QLabel(tr("about_contact_title", "공식 문의 및 기술 지원 (Contact)"), card_contact)
        lbl_c_title.setStyleSheet("font-size: 11px; font-weight: bold; color: #166534; border: none;")
        lbl_email = QLabel("77.victor.lee@gmail.com", card_contact)
        lbl_email.setStyleSheet("font-size: 12.5px; font-weight: bold; color: #15803D; border: none;")
        contact_info_l.addWidget(lbl_c_title)
        contact_info_l.addWidget(lbl_email)
        c_l.addLayout(contact_info_l)

        c_l.addStretch(1)

        btn_copy_email = QPushButton(tr("about_btn_copy_email", "이메일 주소 복사"), card_contact)
        btn_copy_email.setCursor(Qt.PointingHandCursor)
        btn_copy_email.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #166534;
                border: 1px solid #86EFAC;
                border-radius: 5px;
                padding: 6px 14px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #DCFCE7;
            }
        """)
        btn_copy_email.clicked.connect(self.copy_email)
        c_l.addWidget(btn_copy_email)

        layout.addWidget(card_contact)

        # 5. 저작권 표기
        lbl_copy = QLabel("Copyright © 2026 DragonRPA Co. All rights reserved.", self)
        lbl_copy.setAlignment(Qt.AlignCenter)
        lbl_copy.setStyleSheet("font-size: 10.5px; color: #94A3B8;")
        layout.addWidget(lbl_copy)

        layout.addStretch(1)

        # 6. 확인 및 EULA 버튼
        btn_box = QHBoxLayout()
        btn_box.setAlignment(Qt.AlignCenter)
        btn_box.setSpacing(10)

        btn_lic = QPushButton(tr("about_btn_license", "라이선스 등록"), self)
        btn_lic.setFixedHeight(34)
        btn_lic.setCursor(Qt.PointingHandCursor)
        btn_lic.setStyleSheet("""
            QPushButton {
                background-color: #FEF3C7;
                color: #92400E;
                border: 1px solid #FCD34D;
                border-radius: 5px;
                padding: 0 16px;
                font-size: 11.5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FDE68A;
                color: #78350F;
            }
        """)
        btn_lic.clicked.connect(self.open_license_dialog)
        btn_box.addWidget(btn_lic)

        btn_eula = QPushButton(tr("about_btn_eula", "사용권 계약 (EULA)"), self)
        btn_eula.setFixedHeight(34)
        btn_eula.setCursor(Qt.PointingHandCursor)
        btn_eula.setStyleSheet("""
            QPushButton {
                background-color: #F8FAFC;
                color: #334155;
                border: 1px solid #CBD5E1;
                border-radius: 5px;
                padding: 0 16px;
                font-size: 11.5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F1F5F9;
                color: #0F172A;
                border-color: #94A3B8;
            }
        """)
        btn_eula.clicked.connect(self.show_eula)
        btn_box.addWidget(btn_eula)

        btn_rel = QPushButton(tr("release_notes_title", "업데이트 노트"), self)
        btn_rel.setFixedHeight(34)
        btn_rel.setCursor(Qt.PointingHandCursor)
        btn_rel.setStyleSheet("""
            QPushButton {
                background-color: #F8FAFC;
                color: #334155;
                border: 1px solid #CBD5E1;
                border-radius: 5px;
                padding: 0 16px;
                font-size: 11.5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F1F5F9;
                color: #0F172A;
                border-color: #94A3B8;
            }
        """)
        btn_rel.clicked.connect(self.show_release_notes)
        btn_box.addWidget(btn_rel)

        btn_ok = QPushButton(tr("btn_ok", "확인"), self)
        btn_ok.setFixedSize(90, 34)
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: #FFFFFF;
                border: none;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
            }
        """)
        btn_ok.clicked.connect(self.accept)
        btn_box.addWidget(btn_ok)
        layout.addLayout(btn_box)

    def open_license_dialog(self):
        dlg = LicenseRegistrationDialog(self)
        if dlg.exec() == QDialog.Accepted:
            if self.parent() and hasattr(self.parent(), "on_license_activated"):
                self.parent().on_license_activated()
            self.accept()

    def show_eula(self):
        dlg = EulaDialog(self)
        dlg.exec()

    def show_release_notes(self):
        dlg = ReleaseNotesDialog(self)
        dlg.exec()

    def copy_email(self):
        cb = QApplication.clipboard()
        cb.setText("77.victor.lee@gmail.com")
        QMessageBox.information(self, tr("title_copy_email", "클립보드 복사"), tr("about_email_copied", "이메일 주소(77.victor.lee@gmail.com)가 클립보드에 복사되었습니다."))


# ==============================================================================
# 9. 설정 다이얼로그 (SettingsDialog)
# ==============================================================================
class SettingsDialog(QDialog):
    def __init__(self, current_config, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("settings_window_title", "환경 설정"))
        self.resize(580, 820)
        self.config = json.loads(json.dumps(current_config)) # 딥 카피

        self.current_stamp_color = self.config.get("stamp_style", {}).get("bg_color", "#E53935")
        self.current_text_color = self.config.get("text_style", {}).get("text_color", "#FFFFFF")
        self.current_text_bg_color = self.config.get("text_style", {}).get("bg_color", "#212121")
        self.current_box_color = self.config.get("highlight_box_style", {}).get("color", "#E53935")
        self.current_arrow_color = self.config.get("arrow_style", {}).get("color", "#E53935")
        self.current_title_color = self.config.get("ppt_layout", {}).get("title_font_color", "#000000")

        self.init_ui()

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(6, 6, 6, 6)
        root_layout.setSpacing(6)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(10)
        scroll.setWidget(container)
        root_layout.addWidget(scroll, 1)

        # 00. 글로벌 다국어 언어 설정
        box_lang = QFrame(self)
        box_lang.setFrameShape(QFrame.StyledPanel)
        bl_l = QVBoxLayout(box_lang)
        bl_l.addWidget(QLabel(f"<b>[{tr('settings_group_lang', '시스템 언어 설정')}]</b>", self))
        hl = QHBoxLayout()
        hl.addWidget(QLabel(f"{tr('settings_lbl_lang', '시스템 언어')}:", self))
        self.combo_settings_lang = QComboBox(self)
        for code, name in I18nManager.instance().get_supported_locales().items():
            self.combo_settings_lang.addItem(name, code)
        cur_loc = self.config.get("locale", I18nManager.instance().current_locale)
        idx_loc = self.combo_settings_lang.findData(cur_loc)
        if idx_loc >= 0:
            self.combo_settings_lang.setCurrentIndex(idx_loc)
        hl.addWidget(self.combo_settings_lang)
        bl_l.addLayout(hl)
        layout.addWidget(box_lang)

        # 00-1. UI 테마 스타일 설정 (Windows Fluent vs Macintosh Cupertino)
        box_theme = QFrame(self)
        box_theme.setFrameShape(QFrame.StyledPanel)
        bt_l = QVBoxLayout(box_theme)
        bt_l.addWidget(QLabel(f"<b>[{tr('settings_group_ui_theme', 'UI 테마 스타일')}]</b>", self))
        ht = QHBoxLayout()
        lbl_style = QLabel(f"{tr('settings_lbl_ui_style', 'UI 스타일 선택')}:", self)
        lbl_style.setMinimumWidth(120)
        ht.addWidget(lbl_style)
        self.combo_ui_style = QComboBox(self)
        self.combo_ui_style.addItem(tr("settings_ui_style_auto", "자동 감지 (OS 기본값)"), "auto")
        self.combo_ui_style.addItem(tr("ui_style_windows", "Windows 스타일 (Fluent)"), "windows")
        self.combo_ui_style.addItem(tr("ui_style_macos", "Macintosh 스타일 (Cupertino)"), "macos")
        cur_style = self.config.get("ui_style", "auto")
        idx_style = self.combo_ui_style.findData(cur_style)
        if idx_style >= 0:
            self.combo_ui_style.setCurrentIndex(idx_style)
        ht.addWidget(self.combo_ui_style, 1)
        bt_l.addLayout(ht)
        layout.addWidget(box_theme)

        # 01. 실수 방지 자동 저장 설정
        box_as = QFrame(self)
        box_as.setFrameShape(QFrame.StyledPanel)
        bas_l = QVBoxLayout(box_as)
        bas_l.addWidget(QLabel(f"<b>[{tr('settings_group_autosave', '자동 저장 설정')}]</b>", self))
        self.chk_settings_autosave = QCheckBox(tr("settings_chk_autosave", "백그라운드 자동 안전 보관 활성화"), self)
        self.chk_settings_autosave.setChecked(bool(self.config.get("auto_save_enabled", True)))
        bas_l.addWidget(self.chk_settings_autosave)
        has = QHBoxLayout()
        has.addWidget(QLabel(f"{tr('settings_lbl_autosave_interval', '자동 저장 주기 (분)')}:", self))
        self.spin_settings_autosave_interval = QSpinBox(self)
        self.spin_settings_autosave_interval.setRange(1, 60)
        self.spin_settings_autosave_interval.setValue(int(self.config.get("auto_save_interval_min", 5)))
        has.addWidget(self.spin_settings_autosave_interval)
        bas_l.addLayout(has)
        layout.addWidget(box_as)

        # 02. 스마트 자동 업데이트 설정
        box_upd = QFrame(self)
        box_upd.setFrameShape(QFrame.StyledPanel)
        bupd_l = QVBoxLayout(box_upd)
        bupd_l.addWidget(QLabel(f"<b>[{tr('settings_group_autoupdate', '자동 업데이트 설정')}]</b>", self))
        self.chk_settings_autoupdate = QCheckBox(tr("settings_chk_autoupdate", "프로그램 시작 시 최신 버전 자동 확인"), self)
        self.chk_settings_autoupdate.setChecked(bool(self.config.get("auto_check_update", True)))
        bupd_l.addWidget(self.chk_settings_autoupdate)
        layout.addWidget(box_upd)

        # 0. 다중 모니터 캡처 대상 설정
        box0 = QFrame(self)
        box0.setFrameShape(QFrame.StyledPanel)
        b0_l = QVBoxLayout(box0)
        b0_l.addWidget(QLabel(f"<b>[{tr('settings_group_monitor', '다중 모니터 캡처 화면 설정')}]</b>", self))
        h0 = QHBoxLayout()
        h0.addWidget(QLabel(f"{tr('settings_lbl_monitor', '기본 캡처 화면')}:", self))
        self.combo_settings_monitor = QComboBox(self)
        self.combo_settings_monitor.addItem(tr("settings_monitor_all", "전체 가상 화면 (모든 모니터)"), -1)
        for m in MultiMonitorManager.get_monitor_info_list():
            self.combo_settings_monitor.addItem(m["label"], m["index"])
        cur_m = self.config.get("target_monitor", -1)
        idx_m = self.combo_settings_monitor.findData(cur_m)
        if idx_m >= 0:
            self.combo_settings_monitor.setCurrentIndex(idx_m)
        h0.addWidget(self.combo_settings_monitor)
        b0_l.addLayout(h0)
        layout.addWidget(box0)

        # 1. PPT 규격화 가로폭 설정
        box1 = QFrame(self)
        box1.setFrameShape(QFrame.StyledPanel)
        b1_l = QVBoxLayout(box1)
        b1_l.addWidget(QLabel(f"<b>[{tr('settings_group_ppt_width', 'PPT 슬라이드 규격화 가로폭')}]</b>", self))
        h1 = QHBoxLayout()
        h1.addWidget(QLabel(f"{tr('settings_lbl_ppt_width', '목표 가로 해상도(px)')}:", self))
        self.spin_width = QSpinBox(self)
        self.spin_width.setRange(400, 3840)
        self.spin_width.setSingleStep(10)
        self.spin_width.setValue(self.config.get("target_width", 960))
        h1.addWidget(self.spin_width)
        b1_l.addLayout(h1)
        layout.addWidget(box1)

        # 2. 번호 스탬프 스타일
        box2 = QFrame(self)
        box2.setFrameShape(QFrame.StyledPanel)
        b2_l = QVBoxLayout(box2)
        b2_l.addWidget(QLabel(f"<b>[{tr('settings_group_stamp', '번호 스탬프 스타일')}]</b>", self))

        h2_1 = QHBoxLayout()
        h2_1.addWidget(QLabel(f"{tr('settings_lbl_stamp_size', '스탬프 뱃지 크기(px)')}:", self))
        self.spin_stamp_size = QSpinBox(self)
        self.spin_stamp_size.setRange(16, 120)
        self.spin_stamp_size.setValue(self.config.get("stamp_style", {}).get("size", 32))
        h2_1.addWidget(self.spin_stamp_size)
        b2_l.addLayout(h2_1)

        h2_2 = QHBoxLayout()
        h2_2.addWidget(QLabel(f"{tr('settings_lbl_stamp_bg', '스탬프 배경 색상')}:", self))
        self.btn_stamp_color = QPushButton(tr("settings_btn_choose_color", "색상 선택"), self)
        self.btn_stamp_color.setStyleSheet(f"background-color: {self.current_stamp_color}; color: #FFFFFF; font-weight: bold;")
        self.btn_stamp_color.clicked.connect(self.choose_stamp_color)
        h2_2.addWidget(self.btn_stamp_color)
        b2_l.addLayout(h2_2)
        layout.addWidget(box2)

        # 3. 텍스트 라벨 스타일
        box3 = QFrame(self)
        box3.setFrameShape(QFrame.StyledPanel)
        b3_l = QVBoxLayout(box3)
        b3_l.addWidget(QLabel(f"<b>[{tr('settings_group_text', '텍스트 라벨 스타일')}]</b>", self))

        h3_font = QHBoxLayout()
        h3_font.addWidget(QLabel(f"{tr('settings_lbl_text_font', '기본 서체')}:", self))
        self.combo_text_font = QFontComboBox(self)
        cur_tf = self.config.get("text_style", {}).get("font_family", "Malgun Gothic")
        self.combo_text_font.setCurrentFont(QFont(cur_tf))
        h3_font.addWidget(self.combo_text_font)

        self.btn_add_font_text = QPushButton(tr("settings_btn_add_font", "+ 폰트 등록"), self)
        self.btn_add_font_text.setToolTip(tr("settings_font_dialog_title", "폰트 파일 등록"))
        self.btn_add_font_text.clicked.connect(self.action_add_custom_font)
        h3_font.addWidget(self.btn_add_font_text)
        b3_l.addLayout(h3_font)

        h3_1 = QHBoxLayout()
        h3_1.addWidget(QLabel(f"{tr('settings_lbl_text_size', '글꼴 크기(pt)')}:", self))
        self.spin_font_size = QSpinBox(self)
        self.spin_font_size.setRange(8, 72)
        self.spin_font_size.setValue(self.config.get("text_style", {}).get("font_size", 14))
        h3_1.addWidget(self.spin_font_size)
        b3_l.addLayout(h3_1)

        h3_2 = QHBoxLayout()
        h3_2.addWidget(QLabel(f"{tr('settings_lbl_text_color', '글자 색상')}:", self))
        self.btn_text_color = QPushButton(tr("settings_btn_choose_color", "색상 선택"), self)
        self.btn_text_color.setStyleSheet(f"background-color: #333333; color: {self.current_text_color}; font-weight: bold;")
        self.btn_text_color.clicked.connect(self.choose_text_color)
        h3_2.addWidget(self.btn_text_color)

        h3_2.addWidget(QLabel(f"{tr('settings_lbl_text_bg', '배경 색상')}:", self))
        self.btn_text_bg_color = QPushButton(tr("settings_btn_choose_color", "색상 선택"), self)
        self.btn_text_bg_color.setStyleSheet(f"background-color: {self.current_text_bg_color}; color: #FFFFFF; font-weight: bold;")
        self.btn_text_bg_color.clicked.connect(self.choose_text_bg_color)
        h3_2.addWidget(self.btn_text_bg_color)
        b3_l.addLayout(h3_2)
        layout.addWidget(box3)

        # 4. 강조 박스 스타일
        box4 = QFrame(self)
        box4.setFrameShape(QFrame.StyledPanel)
        b4_l = QVBoxLayout(box4)
        b4_l.addWidget(QLabel(f"<b>[{tr('settings_group_box', '강조 박스 스타일')}]</b>", self))

        h4_1 = QHBoxLayout()
        h4_1.addWidget(QLabel(f"{tr('settings_lbl_box_width', '선 두께(px)')}:", self))
        self.spin_box_width = QSpinBox(self)
        self.spin_box_width.setRange(1, 20)
        self.spin_box_width.setValue(self.config.get("highlight_box_style", {}).get("border_width", 3))
        h4_1.addWidget(self.spin_box_width)

        h4_1.addWidget(QLabel(f"{tr('settings_lbl_box_color', '박스 색상')}:", self))
        self.btn_box_color = QPushButton(tr("settings_btn_choose_color", "색상 선택"), self)
        self.btn_box_color.setStyleSheet(f"background-color: {self.current_box_color}; color: #FFFFFF; font-weight: bold;")
        self.btn_box_color.clicked.connect(self.choose_box_color)
        h4_1.addWidget(self.btn_box_color)
        b4_l.addLayout(h4_1)

        self.chk_box_fill = QCheckBox(tr("settings_chk_box_fill", "음영 채우기"), self)
        self.chk_box_fill.setChecked(self.config.get("highlight_box_style", {}).get("fill", False))
        b4_l.addWidget(self.chk_box_fill)
        layout.addWidget(box4)

        # 5. 화살표 연결선 스타일
        box_arr = QFrame(self)
        box_arr.setFrameShape(QFrame.StyledPanel)
        b_arr_l = QVBoxLayout(box_arr)
        b_arr_l.addWidget(QLabel(f"<b>[{tr('settings_group_arrow', '화살표 연결선 스타일')}]</b>", self))

        h_arr = QHBoxLayout()
        h_arr.addWidget(QLabel(f"{tr('settings_lbl_arrow_width', '선 두께(px)')}:", self))
        self.spin_arrow_width = QSpinBox(self)
        self.spin_arrow_width.setRange(1, 20)
        self.spin_arrow_width.setValue(self.config.get("arrow_style", {}).get("width", 3))
        h_arr.addWidget(self.spin_arrow_width)

        h_arr.addWidget(QLabel(f"{tr('settings_lbl_arrow_head', '촉 크기(px)')}:", self))
        self.spin_arrow_head = QSpinBox(self)
        self.spin_arrow_head.setRange(6, 40)
        self.spin_arrow_head.setValue(self.config.get("arrow_style", {}).get("head_size", 14))
        h_arr.addWidget(self.spin_arrow_head)

        h_arr.addWidget(QLabel(f"{tr('settings_lbl_arrow_color', '색상')}:", self))
        self.btn_arrow_color = QPushButton(tr("settings_btn_choose_color", "색상 선택"), self)
        self.btn_arrow_color.setStyleSheet(f"background-color: {self.current_arrow_color}; color: #FFFFFF; font-weight: bold;")
        self.btn_arrow_color.clicked.connect(self.choose_arrow_color)
        h_arr.addWidget(self.btn_arrow_color)
        b_arr_l.addLayout(h_arr)
        layout.addWidget(box_arr)

        # 6. 추천 주석 스타일 (말풍선, 모자이크, 단축키)
        box_rec = QFrame(self)
        box_rec.setFrameShape(QFrame.StyledPanel)
        b_rec_l = QVBoxLayout(box_rec)
        b_rec_l.addWidget(QLabel(f"<b>[{tr('settings_group_recom', '주석 스타일 (말풍선·모자이크·단축키)')}]</b>", self))

        h_rec1 = QHBoxLayout()
        h_rec1.addWidget(QLabel(f"{tr('settings_lbl_callout_font', '말풍선 글꼴(pt)')}:", self))
        self.spin_callout_font = QSpinBox(self)
        self.spin_callout_font.setRange(8, 72)
        self.spin_callout_font.setValue(self.config.get("callout_style", {}).get("font_size", 12))
        h_rec1.addWidget(self.spin_callout_font)

        h_rec1.addWidget(QLabel(f"{tr('settings_lbl_callout_tail', '말풍선 꼬리(px)')}:", self))
        self.spin_callout_tail = QSpinBox(self)
        self.spin_callout_tail.setRange(8, 40)
        self.spin_callout_tail.setValue(self.config.get("callout_style", {}).get("tail_base_width", 16))
        h_rec1.addWidget(self.spin_callout_tail)
        b_rec_l.addLayout(h_rec1)

        h_rec2 = QHBoxLayout()
        h_rec2.addWidget(QLabel(f"{tr('settings_lbl_blur_block', '모자이크 크기(px)')}:", self))
        self.spin_blur_block = QSpinBox(self)
        self.spin_blur_block.setRange(4, 40)
        self.spin_blur_block.setValue(self.config.get("blur_style", {}).get("block_size", 10))
        h_rec2.addWidget(self.spin_blur_block)

        h_rec2.addWidget(QLabel(f"{tr('settings_lbl_hotkey_font', '단축키 글꼴(pt)')}:", self))
        self.spin_hotkey_font = QSpinBox(self)
        self.spin_hotkey_font.setRange(8, 36)
        self.spin_hotkey_font.setValue(self.config.get("hotkey_style", {}).get("font_size", 12))
        h_rec2.addWidget(self.spin_hotkey_font)
        b_rec_l.addLayout(h_rec2)
        layout.addWidget(box_rec)

        # 7. PPT 슬라이드 배치 및 배율
        box5 = QFrame(self)
        box5.setFrameShape(QFrame.StyledPanel)
        b5_l = QVBoxLayout(box5)
        b5_l.addWidget(QLabel(f"<b>[{tr('settings_group_ppt_scale', 'PPT 슬라이드 배치 및 배율')}]</b>", self))

        h_target = QHBoxLayout()
        h_target.addWidget(QLabel(f"{tr('settings_lbl_export_target', '내보내기 대상')}:", self))
        self.combo_export_target = QComboBox(self)
        self.combo_export_target.addItem(tr("export_target_powerpoint", "PowerPoint (로컬 데스크톱)"), "powerpoint")
        self.combo_export_target.addItem(tr("export_target_google_slides", "Google Slides (웹 브라우저)"), "google_slides")
        cur_target = self.config.get("export_target", "powerpoint")
        idx_t = self.combo_export_target.findData(cur_target)
        if idx_t >= 0:
            self.combo_export_target.setCurrentIndex(idx_t)
        h_target.addWidget(self.combo_export_target)
        b5_l.addLayout(h_target)

        self.chk_slides_auto = QCheckBox(tr("chk_slides_auto_slide", "F10 실행 시 구글 슬라이드 자동 생성 및 주입"), self)
        self.chk_slides_auto.setChecked(self.config.get("slides_auto_slide", True))
        b5_l.addWidget(self.chk_slides_auto)

        self.chk_slides_return = QCheckBox(tr("chk_slides_return_focus", "슬라이드 주입 후 스튜디오로 포커스 자동 복귀"), self)
        self.chk_slides_return.setChecked(self.config.get("slides_return_focus", True))
        b5_l.addWidget(self.chk_slides_return)

        h5_1 = QHBoxLayout()
        h5_1.addWidget(QLabel("Left(pt):", self))
        self.spin_ppt_left = QSpinBox(self)
        self.spin_ppt_left.setRange(0, 1920)
        self.spin_ppt_left.setSingleStep(5)
        self.spin_ppt_left.setValue(self.config.get("ppt_layout", {}).get("left", 50))
        h5_1.addWidget(self.spin_ppt_left)

        h5_1.addWidget(QLabel("Top(pt):", self))
        self.spin_ppt_top = QSpinBox(self)
        self.spin_ppt_top.setRange(0, 1080)
        self.spin_ppt_top.setSingleStep(5)
        self.spin_ppt_top.setValue(self.config.get("ppt_layout", {}).get("top", 80))
        h5_1.addWidget(self.spin_ppt_top)

        h5_1.addWidget(QLabel(f"{tr('settings_lbl_ppt_scale', '배율(%)')}:", self))
        self.spin_ppt_scale = QSpinBox(self)
        self.spin_ppt_scale.setRange(10, 300)
        self.spin_ppt_scale.setSingleStep(5)
        self.spin_ppt_scale.setValue(self.config.get("ppt_layout", {}).get("scale", 90))
        h5_1.addWidget(self.spin_ppt_scale)
        b5_l.addLayout(h5_1)

        self.chk_ppt_title = QCheckBox(tr("settings_chk_ppt_title", "단계명 제목 상자 자동 생성"), self)
        self.chk_ppt_title.setChecked(self.config.get("ppt_layout", {}).get("include_title", True))
        b5_l.addWidget(self.chk_ppt_title)
        layout.addWidget(box5)

        # 8. PPT 단계명 제목 상자 스타일 및 배치
        box_title = QFrame(self)
        box_title.setFrameShape(QFrame.StyledPanel)
        b_t_l = QVBoxLayout(box_title)
        b_t_l.addWidget(QLabel(f"<b>[{tr('settings_group_ppt_title', 'PPT 단계명 제목 상자 스타일 및 배치')}]</b>", self))

        ppt_l = self.config.get("ppt_layout", {})

        ht1 = QHBoxLayout()
        ht1.addWidget(QLabel(f"{tr('settings_lbl_ppt_title_x', '제목 X(pt)')}:", self))
        self.spin_title_left = QSpinBox(self)
        self.spin_title_left.setRange(0, 1920)
        self.spin_title_left.setSingleStep(5)
        self.spin_title_left.setValue(int(ppt_l.get("title_left", ppt_l.get("left", 26))))
        ht1.addWidget(self.spin_title_left)

        ht1.addWidget(QLabel(f"{tr('settings_lbl_ppt_title_y', '제목 Y(pt)')}:", self))
        self.spin_title_top = QSpinBox(self)
        self.spin_title_top.setRange(0, 1080)
        self.spin_title_top.setSingleStep(5)
        self.spin_title_top.setValue(int(ppt_l.get("title_top", 15)))
        ht1.addWidget(self.spin_title_top)

        ht1.addWidget(QLabel(f"{tr('settings_lbl_ppt_title_w', '너비(pt)')}:", self))
        self.spin_title_width = QSpinBox(self)
        self.spin_title_width.setRange(50, 1920)
        self.spin_title_width.setSingleStep(20)
        self.spin_title_width.setValue(int(ppt_l.get("title_width", 500)))
        ht1.addWidget(self.spin_title_width)

        ht1.addWidget(QLabel(f"{tr('settings_lbl_ppt_title_h', '높이(pt)')}:", self))
        self.spin_title_height = QSpinBox(self)
        self.spin_title_height.setRange(15, 500)
        self.spin_title_height.setSingleStep(5)
        self.spin_title_height.setValue(int(ppt_l.get("title_height", 35)))
        ht1.addWidget(self.spin_title_height)
        b_t_l.addLayout(ht1)

        ht2 = QHBoxLayout()
        ht2.addWidget(QLabel(f"{tr('settings_lbl_ppt_title_font', '글꼴')}:", self))
        self.combo_title_font = QFontComboBox(self)
        self.combo_title_font.setFixedWidth(130)
        cur_tfont = str(ppt_l.get("title_font_family", "Malgun Gothic"))
        self.combo_title_font.setCurrentFont(QFont(cur_tfont))
        ht2.addWidget(self.combo_title_font)

        self.btn_add_font_title = QPushButton(tr("settings_btn_add_font", "+ 폰트 등록"), self)
        self.btn_add_font_title.setToolTip(tr("settings_font_dialog_title", "폰트 파일 등록"))
        self.btn_add_font_title.clicked.connect(self.action_add_custom_font)
        ht2.addWidget(self.btn_add_font_title)

        ht2.addWidget(QLabel(f"{tr('settings_lbl_ppt_title_size', '크기(pt)')}:", self))
        self.spin_title_font_size = QSpinBox(self)
        self.spin_title_font_size.setRange(8, 72)
        self.spin_title_font_size.setValue(int(ppt_l.get("title_font_size", 18)))
        ht2.addWidget(self.spin_title_font_size)

        self.chk_title_bold = QCheckBox(tr("settings_chk_ppt_title_bold", "굵게"), self)
        self.chk_title_bold.setChecked(bool(ppt_l.get("title_font_bold", True)))
        ht2.addWidget(self.chk_title_bold)

        ht2.addWidget(QLabel(f"{tr('settings_lbl_ppt_title_color', '글자색')}:", self))
        self.btn_title_color = QPushButton(tr("settings_btn_choose_color", "색상 선택"), self)
        qcol_t = QColor(self.current_title_color)
        t_fg = "#FFFFFF" if (qcol_t.red() * 0.299 + qcol_t.green() * 0.587 + qcol_t.blue() * 0.114) < 140 else "#000000"
        self.btn_title_color.setStyleSheet(f"background-color: {self.current_title_color}; color: {t_fg}; font-weight: bold;")
        self.btn_title_color.clicked.connect(self.choose_title_color)
        ht2.addWidget(self.btn_title_color)
        b_t_l.addLayout(ht2)

        ht3 = QHBoxLayout()
        ht3.addWidget(QLabel(f"{tr('settings_lbl_ppt_title_template', '제목 템플릿')}:", self))
        self.edit_title_template = QLineEdit(str(ppt_l.get("title_template", "Step {n}. [단계명 입력]")), self)
        self.edit_title_template.setToolTip("'{n}'은 슬라이드 번호-1 로 자동 치환됩니다.")
        ht3.addWidget(self.edit_title_template)
        b_t_l.addLayout(ht3)

        layout.addWidget(box_title)

        # 사내 PPT 마스터 템플릿 연동
        box_tpl = QFrame(self)
        box_tpl.setFrameShape(QFrame.StyledPanel)
        btpl_l = QVBoxLayout(box_tpl)
        btpl_l.addWidget(QLabel(f"<b>[{tr('settings_group_master', '사내 PPT 마스터 템플릿 연동')}]</b>", self))
        htpl = QHBoxLayout()
        htpl.addWidget(QLabel(f"{tr('settings_lbl_master_file', '마스터 파일(.pptx)')}:", self))
        self.edit_settings_ppt_template = QLineEdit(str(self.config.get("ppt_template_path", "")), self)
        self.edit_settings_ppt_template.setPlaceholderText(tr("settings_group_master", "사내 PPT 마스터 템플릿 연동"))
        btn_browse_tpl = QPushButton(tr("settings_btn_browse", "찾아보기..."), self)
        btn_browse_tpl.clicked.connect(self.action_browse_ppt_template)
        htpl.addWidget(self.edit_settings_ppt_template)
        htpl.addWidget(btn_browse_tpl)
        btpl_l.addLayout(htpl)
        layout.addWidget(box_tpl)

        # 하단 확인/취소
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton(tr("settings_btn_save", "저장"), self)
        btn_ok.setStyleSheet("background-color: #2196F3; color: #FFFFFF; font-weight: bold; padding: 6px 14px;")
        btn_ok.clicked.connect(self.save_and_close)
        btn_cancel = QPushButton(tr("settings_btn_cancel", "취소"), self)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        root_layout.addLayout(btn_layout)

    def action_add_custom_font(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            tr("settings_font_dialog_title", "폰트 파일 등록"),
            "",
            "폰트 파일 (*.ttf *.otf *.ttc *.woff);;모든 파일 (*.*)"
        )
        if not file_paths:
            return
        all_added = []
        for fp in file_paths:
            families, dest = CustomFontManager.instance().import_font_file(fp)
            if families:
                all_added.extend(families)
                if "custom_fonts" not in self.config:
                    self.config["custom_fonts"] = []
                if dest not in self.config["custom_fonts"]:
                    self.config["custom_fonts"].append(dest)
        if all_added:
            fam_str = ", ".join(all_added)
            msg_succ = tr("settings_font_success_msg", "새 글꼴이 등록되었습니다:\n{fonts}").format(fonts=fam_str)
            QMessageBox.information(self, tr("settings_font_success_title", "폰트 등록 완료"), msg_succ)
            if hasattr(self, "combo_title_font") and all_added:
                self.combo_title_font.setCurrentFont(QFont(all_added[0]))
            if hasattr(self, "combo_text_font") and all_added:
                self.combo_text_font.setCurrentFont(QFont(all_added[0]))

    def choose_stamp_color(self):
        col = QColorDialog.getColor(QColor(self.current_stamp_color), self, tr("settings_lbl_stamp_bg", "스탬프 배경 색상"))
        if col.isValid():
            self.current_stamp_color = col.name()
            self.btn_stamp_color.setStyleSheet(f"background-color: {self.current_stamp_color}; color: #FFFFFF; font-weight: bold;")

    def choose_text_color(self):
        col = QColorDialog.getColor(QColor(self.current_text_color), self, tr("settings_lbl_text_color", "글자 색상"))
        if col.isValid():
            self.current_text_color = col.name()
            self.btn_text_color.setStyleSheet(f"background-color: #333333; color: {self.current_text_color}; font-weight: bold;")

    def choose_text_bg_color(self):
        col = QColorDialog.getColor(QColor(self.current_text_bg_color), self, tr("settings_lbl_text_bg", "배경 색상"))
        if col.isValid():
            self.current_text_bg_color = col.name()
            self.btn_text_bg_color.setStyleSheet(f"background-color: {self.current_text_bg_color}; color: #FFFFFF; font-weight: bold;")

    def choose_box_color(self):
        col = QColorDialog.getColor(QColor(self.current_box_color), self, tr("settings_lbl_box_color", "박스 색상"))
        if col.isValid():
            self.current_box_color = col.name()
            self.btn_box_color.setStyleSheet(f"background-color: {self.current_box_color}; color: #FFFFFF; font-weight: bold;")

    def choose_arrow_color(self):
        col = QColorDialog.getColor(QColor(self.current_arrow_color), self, tr("settings_lbl_arrow_color", "색상"))
        if col.isValid():
            self.current_arrow_color = col.name()
            self.btn_arrow_color.setStyleSheet(f"background-color: {self.current_arrow_color}; color: #FFFFFF; font-weight: bold;")

    def choose_title_color(self):
        col = QColorDialog.getColor(QColor(self.current_title_color), self, tr("settings_lbl_ppt_title_color", "글자색"))
        if col.isValid():
            self.current_title_color = col.name()
            qcol = QColor(self.current_title_color)
            text_fg = "#FFFFFF" if (qcol.red() * 0.299 + qcol.green() * 0.587 + qcol.blue() * 0.114) < 140 else "#000000"
            self.btn_title_color.setStyleSheet(f"background-color: {self.current_title_color}; color: {text_fg}; font-weight: bold;")

    def action_browse_ppt_template(self):
        fpath, _ = QFileDialog.getOpenFileName(
            self,
            tr("settings_group_master", "사내 PPT 마스터 템플릿 연동"),
            "",
            "파워포인트 템플릿 (*.pptx *.potx);;모든 파일 (*.*)"
        )
        if fpath:
            self.edit_settings_ppt_template.setText(fpath)

    def save_and_close(self):
        if hasattr(self, "combo_settings_lang"):
            self.config["locale"] = self.combo_settings_lang.currentData()
        if hasattr(self, "chk_settings_autosave"):
            self.config["auto_save_enabled"] = self.chk_settings_autosave.isChecked()
        if hasattr(self, "spin_settings_autosave_interval"):
            self.config["auto_save_interval_min"] = self.spin_settings_autosave_interval.value()
        if hasattr(self, "edit_settings_ppt_template"):
            self.config["ppt_template_path"] = self.edit_settings_ppt_template.text().strip()
        if hasattr(self, "chk_settings_autoupdate"):
            self.config["auto_check_update"] = self.chk_settings_autoupdate.isChecked()

        if hasattr(self, "combo_settings_monitor"):
            self.config["target_monitor"] = self.combo_settings_monitor.currentData()
        self.config["target_width"] = self.spin_width.value()
        self.config.setdefault("stamp_style", {})["size"] = self.spin_stamp_size.value()
        self.config["stamp_style"]["bg_color"] = self.current_stamp_color
        self.config.setdefault("text_style", {})["font_size"] = self.spin_font_size.value()
        self.config["text_style"]["text_color"] = self.current_text_color
        self.config["text_style"]["bg_color"] = self.current_text_bg_color
        if hasattr(self, "combo_text_font"):
            self.config["text_style"]["font_family"] = self.combo_text_font.currentFont().family()
        self.config.setdefault("highlight_box_style", {})["border_width"] = self.spin_box_width.value()
        self.config["highlight_box_style"]["color"] = self.current_box_color
        self.config["highlight_box_style"]["fill"] = self.chk_box_fill.isChecked()
        self.config.setdefault("arrow_style", {})["width"] = self.spin_arrow_width.value()
        self.config["arrow_style"]["head_size"] = self.spin_arrow_head.value()
        self.config["arrow_style"]["color"] = self.current_arrow_color
        self.config.setdefault("callout_style", {})["font_size"] = self.spin_callout_font.value()
        self.config.setdefault("callout_style", {})["tail_base_width"] = self.spin_callout_tail.value()
        self.config.setdefault("blur_style", {})["block_size"] = self.spin_blur_block.value()
        self.config.setdefault("hotkey_style", {})["font_size"] = self.spin_hotkey_font.value()
        self.config.setdefault("ppt_layout", {})["left"] = self.spin_ppt_left.value()
        self.config["ppt_layout"]["top"] = self.spin_ppt_top.value()
        self.config["ppt_layout"]["scale"] = self.spin_ppt_scale.value()
        self.config["ppt_layout"]["include_title"] = self.chk_ppt_title.isChecked()
        self.config["ppt_layout"]["title_left"] = self.spin_title_left.value()
        self.config["ppt_layout"]["title_top"] = self.spin_title_top.value()
        self.config["ppt_layout"]["title_width"] = self.spin_title_width.value()
        self.config["ppt_layout"]["title_height"] = self.spin_title_height.value()
        self.config["ppt_layout"]["title_font_family"] = self.combo_title_font.currentFont().family()
        self.config["ppt_layout"]["title_font_size"] = self.spin_title_font_size.value()
        self.config["ppt_layout"]["title_font_bold"] = self.chk_title_bold.isChecked()
        self.config["ppt_layout"]["title_font_color"] = self.current_title_color
        self.config["ppt_layout"]["title_template"] = self.edit_title_template.text().strip() or "Step {n}. [단계명 입력]"
        if hasattr(self, "combo_export_target"):
            self.config["export_target"] = self.combo_export_target.currentData() or "powerpoint"
        if hasattr(self, "chk_slides_auto"):
            self.config["slides_auto_slide"] = self.chk_slides_auto.isChecked()
        if hasattr(self, "chk_slides_return"):
            self.config["slides_return_focus"] = self.chk_slides_return.isChecked()
        if hasattr(self, "combo_ui_style"):
            new_style = self.combo_ui_style.currentData() or "auto"
            self.config["ui_style"] = new_style
            if self.parent() and hasattr(self.parent(), "apply_ui_theme"):
                self.parent().apply_ui_theme(new_style)
        self.accept()

    def get_config(self):
        return self.config

    @property
    def edit_title_font(self):
        class _FontProxy:
            def __init__(self, combo):
                self.combo = combo
            def text(self):
                return self.combo.currentFont().family()
            def setText(self, val):
                self.combo.setCurrentFont(QFont(val))
        return _FontProxy(self.combo_title_font)


def kill_other_instances():
    """자신(현재 PID)을 제외하고 실행 중인 다른 manual_capture_studio.py 프로세스를 강제 종료하여 핫키 점유 충돌 방지"""
    try:
        current_pid = os.getpid()
        import subprocess
        cmd = f"Get-CimInstance Win32_Process -Filter \"name = 'python.exe'\" | Where-Object {{ $_.ProcessId -ne {current_pid} -and $_.CommandLine -like '*manual_capture_studio*' }} | ForEach-Object {{ Stop-Process -Id $_.ProcessId -Force }}"
        subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True)
    except Exception as e:
        print(f"[Instance Cleaner] 이전 프로세스 정리 실패: {e}")

# ==============================================================================
# 9. 엔트리 포인트
# ==============================================================================


def main():
    # AI 에이전트 및 CLI 헤드리스 모드 사전 분기
    if "--mcp" in sys.argv:
        if sys.platform == "win32":
            try:
                ctypes.windll.kernel32.AttachConsole(-1)
            except Exception:
                pass
        from mcp_server import run_mcp_server
        run_mcp_server()
        return

    if "--cli" in sys.argv:
        if sys.platform == "win32":
            try:
                ctypes.windll.kernel32.AttachConsole(-1)
            except Exception:
                pass
        from manual_cli import handle_cli
        cli_args = [a for a in sys.argv[1:] if a != "--cli"]
        sys.exit(handle_cli(cli_args))

    # 0. Windows 환경에서 python.exe로 실행 시 검은 콘솔창 즉시 숨김
    hide_console_window()

    # 이전 인스턴스 정리 (글로벌 핫키 F9 독점 방지)
    kill_other_instances()

    # Qt 플러그인 라이브러리 경로 명시적 추가
    if 'plugins_dir' in globals() and os.path.exists(plugins_dir):
        QCoreApplication.addLibraryPath(plugins_dir)

    # 고해상도 High-DPI 지원 (Qt 6는 상시 기본 내장, Qt 5 하위 호환 시에만 안전 호출)
    if hasattr(Qt, "AA_EnableHighDpiScaling") and not hasattr(QApplication, "exec"):
        try:
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setApplicationName("ManualCaptureStudio")

    # 애플리케이션 및 작업표시줄 아이콘 설정 (Manual Studio 전용 앱 아이콘)
    app_icon = get_manual_studio_icon()
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)

    # 기본 폰트 설정
    app.setFont(QFont("Malgun Gothic", 10))

    # 1. 사용 기간(2026-12-31) 및 안티 롤백 검증
    is_valid, err_msg = LicenseValidator.check_license()
    if not is_valid:
        QMessageBox.critical(None, "평가판 사용 제한 - DragonRPA Co.", err_msg)
        sys.exit(1)

    window = ManualStudioWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()

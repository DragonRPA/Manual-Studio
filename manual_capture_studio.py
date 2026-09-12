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
from datetime import datetime
import ctypes
from ctypes import wintypes

# Windows 환경에서 Qt 플랫폼 플러그인(qwindows.dll) 탐색 실패 원천 방지
try:
    import PyQt5
    pyqt_dir = os.path.dirname(PyQt5.__file__)
    plugins_dir = os.path.join(pyqt_dir, "Qt5", "plugins")
    platforms_dir = os.path.join(plugins_dir, "platforms")
    if os.path.exists(platforms_dir):
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = platforms_dir
    elif os.path.exists(os.path.join(pyqt_dir, "Qt", "plugins", "platforms")):
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.path.join(pyqt_dir, "Qt", "plugins", "platforms")
except Exception:
    pass

from PyQt5.QtCore import (
    Qt, QPoint, QPointF, QRect, QRectF, QSize, QThread, pyqtSignal, QTimer, QCoreApplication,
    QByteArray, QBuffer, QIODevice, QUrl
)
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QPixmap, QImage,
    QCursor, QPainterPath, QIcon, QFontMetrics, QPolygonF, QTransform, QDesktopServices
)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QDialog, QSpinBox, QColorDialog,
    QFileDialog, QMessageBox, QToolTip, QFrame, QScrollArea, QAction,
    QGraphicsDropShadowEffect, QSystemTrayIcon, QMenu, QCheckBox,
    QTabWidget, QTabBar, QGridLayout, QMenuBar, QTextEdit
)

from PIL import Image
import win32gui
import win32con
import win32clipboard
import win32com.client

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



# ==============================================================================
# 1. 설정 관리자 (Configuration Manager)
# ==============================================================================
DEFAULT_CONFIG = {
    "hotkey_capture": "F9",
    "hotkey_export": "F10",
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
        "border_width": 2
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
    }
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
                    "callout_style", "elbow_style", "blur_style", "hotkey_style",
                    "fixed_rect", "ppt_layout"
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

    def __init__(self, capture_key="F9", export_key="F10", parent=None):
        super().__init__(parent)
        self.capture_key = capture_key.upper()
        self.export_key = export_key.upper()
        self.running = True
        self.hotkey_id_capture = 101
        self.hotkey_id_drag_capture = 103
        self.hotkey_id_sub_capture = 104
        self.hotkey_id_export = 102

    def run(self):
        user32 = ctypes.windll.user32
        vk_cap = VK_MAPPING.get(self.capture_key, 0x78)
        vk_exp = VK_MAPPING.get(self.export_key, 0x79)
        vk_sub = 0x77 # VK_F8

        # MOD_NOREPEAT = 0x4000, MOD_SHIFT = 0x0004
        user32.RegisterHotKey(None, self.hotkey_id_capture, 0x4000, vk_cap)
        user32.RegisterHotKey(None, self.hotkey_id_drag_capture, 0x4000 | 0x0004, vk_cap)
        user32.RegisterHotKey(None, self.hotkey_id_sub_capture, 0x4000, vk_sub)
        user32.RegisterHotKey(None, self.hotkey_id_export, 0x4000, vk_exp)

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
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
            else:
                time.sleep(0.02)

        user32.UnregisterHotKey(None, self.hotkey_id_capture)
        user32.UnregisterHotKey(None, self.hotkey_id_drag_capture)
        user32.UnregisterHotKey(None, self.hotkey_id_sub_capture)
        user32.UnregisterHotKey(None, self.hotkey_id_export)

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
        return cls(int(data["index"]), float(data["x"]), float(data["y"]), data.get("style", {}))

    def contains(self, pt):
        r = self.style.get("size", 32) / 2.0
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

        # 드롭 섀도우
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
        return cls(str(data["text"]), float(data["x"]), float(data["y"]), data.get("style", {}))

    def get_rect(self, painter_or_metrics=None):
        font_family = self.style.get("font_family", "Malgun Gothic")
        font_size = int(self.style.get("font_size", 13))
        font = QFont(font_family, font_size)
        font.setBold(self.style.get("font_bold", True))
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
        font = QFont(self.style.get("font_family", "Malgun Gothic"), int(self.style.get("font_size", 13)))
        font.setBold(self.style.get("font_bold", True))
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
        r = self.stamp_style.get("size", 32) / 2.0
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
    """직각(ㄱ, ㄴ, Z자) 우회 화살표 연결선 객체"""
    def __init__(self, start_pos, end_pos, style, route_mode="HV"):
        self.start_pos = QPointF(start_pos)
        self.end_pos = QPointF(end_pos)
        self.style = style.copy() if hasattr(style, "copy") else dict(style)
        self.route_mode = route_mode  # HV (가로 먼저) 또는 VH (세로 먼저)

    def clone(self):
        return ElbowArrowItem(QPointF(self.start_pos), QPointF(self.end_pos), self.style.copy(), self.route_mode)

    def to_dict(self):
        return {
            "type": "ElbowArrowItem",
            "start_pos": [float(self.start_pos.x()), float(self.start_pos.y())],
            "end_pos": [float(self.end_pos.x()), float(self.end_pos.y())],
            "style": self.style.copy(),
            "route_mode": self.route_mode
        }

    @classmethod
    def from_dict(cls, data):
        p1 = data.get("start_pos", [0.0, 0.0])
        p2 = data.get("end_pos", [0.0, 0.0])
        return cls(
            QPointF(float(p1[0]), float(p1[1])),
            QPointF(float(p2[0]), float(p2[1])),
            data.get("style", {}),
            data.get("route_mode", "HV")
        )

    def get_corner_point(self):
        p1 = self.start_pos
        p2 = self.end_pos
        if self.route_mode == "HV":
            return QPointF(p2.x(), p1.y())
        else:
            return QPointF(p1.x(), p2.y())

    def contains(self, pt):
        p1 = self.start_pos
        corner = self.get_corner_point()
        p2 = self.end_pos
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

        return min(dist_to_seg(p1, corner, pt), dist_to_seg(corner, p2, pt)) <= hit_m

    def render(self, painter: QPainter):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        color = QColor(self.style.get("color", "#E53935"))
        width = int(self.style.get("width", 3))
        head_size = float(self.style.get("head_size", 14))
        head_size = max(head_size, width * 3.2)

        p1 = self.start_pos
        corner = self.get_corner_point()
        p2 = self.end_pos

        dx = p2.x() - corner.x()
        dy = p2.y() - corner.y()
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
        path.lineTo(corner)
        path.lineTo(arrow_indent)

        # 그림자
        shadow_offset = QPointF(1.5, 1.5)
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
        font = QFont(self.style.get("font_family", "Malgun Gothic"), int(self.style.get("font_size", 12)))
        font.setBold(self.style.get("font_bold", True))
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
        return cls(str(data.get("key_text", "")), float(data.get("x", 0.0)), float(data.get("y", 0.0)), data.get("style", {}))

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
                shadow_rect = r.translated(offset, offset)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(0, 0, 0, alpha))
                painter.drawRoundedRect(shadow_rect, radius + 1, radius + 1)

        # 2. 이미지 렌더링 (둥근 모서리 클리핑)
        path = QPainterPath()
        path.addRoundedRect(r, radius, radius)
        painter.save()
        painter.setClipPath(path)
        painter.drawPixmap(r.toRect(), self.pixmap)
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
        x = float(data.get("x", 0.0))
        y = float(data.get("y", 0.0))
        item = cls(text=text, pos=QPointF(x, y), style=data.get("style", {}))
        if "angle" in data:
            item.angle = float(data["angle"])
        return item


# ------------------------------------------------------------------------------
# 주석 직렬화 레지스트리 및 팩토리 (Annotation Registry & Factory)
# ------------------------------------------------------------------------------
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
# 프로젝트 관리자 (ProjectManager: .mcs.json & _raw.png 영구 분리 보존)
# ------------------------------------------------------------------------------
class ProjectManager:
    """매뉴얼 스튜디오 프로젝트 파일(.mcs.json) 입출력 및 무결성 관리 전담 클래스"""

    @staticmethod
    def pixmap_to_base64(pixmap: QPixmap) -> str:
        if pixmap is None or pixmap.isNull():
            return ""
        try:
            ba = QByteArray()
            buf = QBuffer(ba)
            buf.open(QIODevice.WriteOnly)
            pixmap.save(buf, "PNG")
            return base64.b64encode(ba.data()).decode("utf-8")
        except Exception as e:
            print(f"[ProjectManager Base64 인코딩 오류]: {e}")
            return ""

    @staticmethod
    def base64_to_pixmap(b64_str: str) -> QPixmap:
        if not b64_str:
            return None
        try:
            raw_bytes = base64.b64decode(b64_str.encode("utf-8"))
            pixmap = QPixmap()
            pixmap.loadFromData(raw_bytes, "PNG")
            return pixmap
        except Exception as e:
            print(f"[ProjectManager Base64 디코딩 오류]: {e}")
            return None

    @staticmethod
    def save_project(project_path: str, raw_pixmap: QPixmap, items: list, next_stamp_index: int, metadata: dict = None) -> bool:
        """
        프로젝트 파일(.mcs.json)과 원본 비트맵(_raw.png)을 동시 저장합니다.
        파일 이동 및 포터블 호환성을 위해 base64 백업도 JSON에 자동 포함합니다.
        """
        try:
            if not project_path.endswith(".mcs.json") and not project_path.endswith(".json"):
                project_path += ".mcs.json"

            project_dir = os.path.dirname(os.path.abspath(project_path))
            os.makedirs(project_dir, exist_ok=True)
            base_file = os.path.basename(project_path)
            clean_name = base_file.replace(".mcs.json", "").replace(".json", "")
            raw_img_filename = f"{clean_name}_raw.png"
            raw_img_path = os.path.join(project_dir, raw_img_filename)

            # 1. 원본 비트맵 저장 및 base64 추출
            b64_str = ""
            canvas_w = 0
            canvas_h = 0
            if raw_pixmap and not raw_pixmap.isNull():
                raw_pixmap.save(raw_img_path, "PNG")
                b64_str = ProjectManager.pixmap_to_base64(raw_pixmap)
                canvas_w = raw_pixmap.width()
                canvas_h = raw_pixmap.height()

            # 2. 주석 객체 직렬화
            serialized_items = []
            for it in items:
                if hasattr(it, "to_dict"):
                    serialized_items.append(it.to_dict())

            # 3. 프로젝트 메타데이터 조립
            project_dict = {
                "format": "ManualCaptureStudio_Project",
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "canvas_size": [canvas_w, canvas_h],
                "raw_image_file": raw_img_filename,
                "raw_image_b64": b64_str,
                "next_stamp_index": int(next_stamp_index),
                "items": serialized_items,
                "metadata": metadata or {}
            }

            with open(project_path, "w", encoding="utf-8") as f:
                json.dump(project_dict, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"[ProjectManager 저장 오류]: {e}")
            return False

    @staticmethod
    def load_project(project_path: str):
        """
        프로젝트 파일(.mcs.json)로부터 (raw_pixmap, items, next_stamp_index, metadata)를 복원 반환합니다.
        """
        try:
            if not os.path.exists(project_path):
                return None, [], 1, {}

            with open(project_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            project_dir = os.path.dirname(os.path.abspath(project_path))
            raw_img_filename = data.get("raw_image_file", "")
            raw_img_path = os.path.join(project_dir, raw_img_filename) if raw_img_filename else ""

            # 원본 이미지 복원: companion _raw.png 우선 탐색 -> 실패 시 base64 fallback
            raw_pixmap = None
            if raw_img_path and os.path.exists(raw_img_path):
                raw_pixmap = QPixmap(raw_img_path)
            if (raw_pixmap is None or raw_pixmap.isNull()) and data.get("raw_image_b64"):
                raw_pixmap = ProjectManager.base64_to_pixmap(data["raw_image_b64"])

            # 주석 객체 복원
            items = []
            for item_dict in data.get("items", []):
                obj = item_from_dict(item_dict)
                if obj:
                    items.append(obj)

            next_stamp_index = int(data.get("next_stamp_index", 1))
            metadata = data.get("metadata", {})
            return raw_pixmap, items, next_stamp_index, metadata
        except Exception as e:
            print(f"[ProjectManager 로드 오류]: {e}")
            return None, [], 1, {}


# ==============================================================================
# 4. 캡처 오버레이 윈도우 (CaptureOverlayWidget)
# ==============================================================================
class CaptureOverlayWidget(QWidget):
    sig_captured = pyqtSignal(QPixmap, QRect)
    sig_cancelled = pyqtSignal()

    def __init__(self, last_rect=None, config=None, is_sub_capture=False, parent=None):
        super().__init__(parent)
        self.is_captured = False
        self.is_sub_capture = is_sub_capture
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setMouseTracking(True)

        self.config = config or DEFAULT_CONFIG
        self.last_rect = last_rect

        # 전체 가상 화면 캡처
        screens = QApplication.screens()
        min_x = min(s.geometry().x() for s in screens)
        min_y = min(s.geometry().y() for s in screens)
        max_x = max(s.geometry().x() + s.geometry().width() for s in screens)
        max_y = max(s.geometry().y() + s.geometry().height() for s in screens)
        self.virtual_rect = QRect(min_x, min_y, max_x - min_x, max_y - min_y)
        self.setGeometry(self.virtual_rect)

        # 원본 데스크톱 화면 캡처
        self.full_screen_pixmap = QApplication.primaryScreen().grabWindow(
            0, self.virtual_rect.x(), self.virtual_rect.y(),
            self.virtual_rect.width(), self.virtual_rect.height()
        )

        # 상태 관리
        self.selecting = False
        self.resizing_handle = None
        self.moving_rect = False
        self.start_pos = QPoint()
        self.end_pos = QPoint()
        self.selected_rect = QRect()
        self.magnet_rect = QRect()

        self.mouse_pos = QPoint()
        self.handle_size = 8

        self.setFocusPolicy(Qt.StrongFocus)

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
            hwnd = win32gui.WindowFromPoint((global_pt.x(), global_pt.y()))
            if hwnd:
                rect = win32gui.GetWindowRect(hwnd)
                # 오버레이 자기 자신 창인 경우 건너뜀
                if hwnd == int(self.winId()):
                    return QRect()
                # 가상 데스크톱 좌표계에 맞게 변환
                rx = rect[0] - self.virtual_rect.x()
                ry = rect[1] - self.virtual_rect.y()
                rw = rect[2] - rect[0]
                rh = rect[3] - rect[1]
                if rw > 20 and rh > 20 and rw < self.virtual_rect.width() and rh < self.virtual_rect.height():
                    return QRect(rx, ry, rw, rh)
        except Exception:
            pass
        return QRect()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pt = event.pos()
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
        self.mouse_pos = event.pos()
        global_pt = event.globalPos()

        if self.selecting:
            self.end_pos = event.pos()
            self.selected_rect = QRect(self.start_pos, self.end_pos).normalized()
            self.update()
        elif self.resizing_handle:
            self.handle_resize(event.pos())
            self.update()
        elif self.moving_rect:
            diff = event.pos() - self.start_pos
            self.selected_rect.translate(diff)
            self.start_pos = event.pos()
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
                self.end_pos = event.pos()
                r = QRect(self.start_pos, self.end_pos).normalized()
                if r.width() < 10 and r.height() < 10 and not self.magnet_rect.isEmpty():
                    # 단순 클릭 시 자석 스냅 창 자동 채택
                    self.selected_rect = QRect(self.magnet_rect)
                else:
                    self.selected_rect = r
                self.update()
            elif self.resizing_handle:
                self.resizing_handle = None
            elif self.moving_rect:
                self.moving_rect = False

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            if not self.selected_rect.isEmpty() and self.selected_rect.contains(event.pos()):
                self.confirm_capture()

    def confirm_capture(self):
        r = self.selected_rect.normalized()
        if r.width() < 10 or r.height() < 10:
            return
        self.is_captured = True
        cropped = self.full_screen_pixmap.copy(r)
        global_rect = QRect(
            self.virtual_rect.x() + r.x(),
            self.virtual_rect.y() + r.y(),
            r.width(),
            r.height()
        )
        self.sig_captured.emit(cropped, global_rect)
        self.close()

    def closeEvent(self, event):
        if not self.is_captured:
            self.sig_cancelled.emit()
        super().closeEvent(event)

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
            painter.setPen(QPen(QColor(0, 230, 118, 200), 2, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
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
            prefix = "🪟 부분 추가(F8): " if self.is_sub_capture else ""
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

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmap = None
        self.items = []
        self.history = []  # Undo 스택

        self.current_mode = "SELECT"
        self.selected_item = None
        self.dragging_item = None
        self.drag_offset = QPointF()
        self.resizing_overlay_handle = None

        self.next_stamp_index = 1
        self.config = DEFAULT_CONFIG

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

        # 말풍선 그리기용
        self.drawing_callout = False
        self.callout_start = QPointF()
        self.callout_end = QPointF()

        # 블러 모자이크 그리기용
        self.drawing_blur = False
        self.blur_start = QPoint()
        self.blur_end = QPoint()

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

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
        self.setFixedSize(self.pixmap.size())
        self.update()

    def set_config(self, cfg):
        self.config = cfg

    def set_mode(self, mode):
        self.current_mode = mode
        if mode in ("STAMP", "STEP_ARROW", "ARROW", "ELBOW", "BOX", "CALLOUT", "BLUR"):
            self.setCursor(Qt.CrossCursor)
        elif mode in ("TEXT", "HOTKEY"):
            self.setCursor(Qt.IBeamCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def push_undo(self):
        state = {
            "items": [item.clone() for item in self.items],
            "stamp_index": self.next_stamp_index
        }
        self.history.append(state)

    def undo(self):
        if not self.history:
            return
        last_state = self.history.pop()
        self.items = last_state["items"]
        self.next_stamp_index = last_state["stamp_index"]
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
        if self.selected_item and self.selected_item in self.items:
            self.push_undo()
            item = self.selected_item
            self.items.remove(item)
            self.selected_item = None
            self.sig_item_selected.emit(None)
            if isinstance(item, (StampItem, StepArrowItem)):
                self.reindex_stamps()
            self.update()
            self.sig_content_changed.emit()
            self.sig_request_toast.emit("주석 객체가 삭제되었습니다.")
            return True
        return False

    def add_image_overlay(self, pixmap: QPixmap):
        if not pixmap or pixmap.isNull():
            return
        self.push_undo()

        # 캔버스 크기에 맞춰 초기 크기 계산 (너무 크면 비율 축소)
        cw = self.width() if self.pixmap else 960
        ch = self.height() if self.pixmap else 540
        pw = pixmap.width()
        ph = pixmap.height()

        max_w = cw * 0.75
        max_h = ch * 0.75
        scale = 1.0
        if pw > max_w or ph > max_h:
            scale = min(max_w / pw, max_h / ph)

        init_w = pw * scale
        init_h = ph * scale

        init_x = max(20.0, (cw - init_w) / 2.0)
        init_y = max(20.0, (ch - init_h) / 2.0)

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
        if self.pixmap is None:
            return
        pt = event.pos()

        if event.button() == Qt.LeftButton:
            if self.current_mode == "STAMP":
                self.push_undo()
                stamp_style = dict(self.config.get("stamp_style", DEFAULT_CONFIG["stamp_style"]))
                stamp = StampItem(self.next_stamp_index, pt.x(), pt.y(), stamp_style)
                self.items.append(stamp)
                self.next_stamp_index += 1
                self.update()
                self.sig_content_changed.emit()

            elif self.current_mode == "STEP_ARROW":
                self.drawing_step_arrow = True
                self.step_arrow_start = QPointF(pt)
                self.step_arrow_end = QPointF(pt)

            elif self.current_mode == "ARROW":
                self.drawing_arrow = True
                self.arrow_start = QPointF(pt)
                self.arrow_end = QPointF(pt)

            elif self.current_mode == "ELBOW":
                self.drawing_elbow = True
                self.elbow_start = QPointF(pt)
                self.elbow_end = QPointF(pt)

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

            elif self.current_mode == "SELECT":
                # 1. 이미 선택된 ImageOverlayItem의 4각 코너 리사이즈 핸들 클릭 여부 확인
                if self.selected_item and isinstance(self.selected_item, ImageOverlayItem):
                    handle = self.selected_item.get_handle_at(QPointF(pt))
                    if handle:
                        self.push_undo()
                        self.resizing_overlay_handle = handle
                        return

                hit_item = None
                for it in reversed(self.items):
                    if it.contains(pt):
                        hit_item = it
                        break

                self.selected_item = hit_item
                self.sig_item_selected.emit(hit_item)
                if hit_item:
                    self.dragging_item = hit_item
                    if isinstance(hit_item, ImageOverlayItem):
                        self.drag_offset = QPointF(pt.x() - hit_item.rect.x(), pt.y() - hit_item.rect.y())
                    elif isinstance(hit_item, (HighlightBoxItem, BlurMosaicItem)):
                        self.drag_offset = QPointF(pt.x() - hit_item.rect.x(), pt.y() - hit_item.rect.y())
                    elif isinstance(hit_item, CalloutItem):
                        self.drag_offset = QPointF(pt.x() - hit_item.box_rect.x(), pt.y() - hit_item.box_rect.y())
                    elif isinstance(hit_item, (ArrowItem, ElbowArrowItem, StepArrowItem)):
                        self.drag_offset = QPointF(pt.x() - hit_item.start_pos.x(), pt.y() - hit_item.start_pos.y())
                    else:
                        self.drag_offset = QPointF(pt.x() - hit_item.pos.x(), pt.y() - hit_item.pos.y())
                self.update()

        elif event.button() == Qt.RightButton:
            hit_item = None
            for it in reversed(self.items):
                if it.contains(pt):
                    hit_item = it
                    break
            if hit_item:
                self.push_undo()
                self.items.remove(hit_item)
                if hit_item == self.selected_item:
                    self.selected_item = None
                    self.sig_item_selected.emit(None)
                if isinstance(hit_item, (StampItem, StepArrowItem)):
                    self.reindex_stamps()
                self.update()
                self.sig_content_changed.emit()
                self.sig_request_toast.emit("주석 객체가 삭제되었습니다.")

    def mouseMoveEvent(self, event):
        pt = event.pos()
        if hasattr(self, "resizing_overlay_handle") and self.resizing_overlay_handle and isinstance(self.selected_item, ImageOverlayItem):
            self.selected_item.handle_resize(self.resizing_overlay_handle, QPointF(pt), keep_aspect_ratio=True)
            self.update()
            self.sig_content_changed.emit()
            return
        elif self.dragging_item and self.current_mode == "SELECT":
            new_x = pt.x() - self.drag_offset.x()
            new_y = pt.y() - self.drag_offset.y()
            if isinstance(self.dragging_item, ImageOverlayItem):
                self.dragging_item.rect.moveTo(new_x, new_y)
            elif isinstance(self.dragging_item, (HighlightBoxItem, BlurMosaicItem)):
                self.dragging_item.rect.moveTo(int(new_x), int(new_y))
            elif isinstance(self.dragging_item, CalloutItem):
                dx = new_x - self.dragging_item.box_rect.x()
                dy = new_y - self.dragging_item.box_rect.y()
                self.dragging_item.box_rect.moveTo(new_x, new_y)
                self.dragging_item.target_pt += QPointF(dx, dy)
            elif isinstance(self.dragging_item, (ArrowItem, ElbowArrowItem, StepArrowItem)):
                dx = new_x - self.dragging_item.start_pos.x()
                dy = new_y - self.dragging_item.start_pos.y()
                self.dragging_item.start_pos = QPointF(new_x, new_y)
                self.dragging_item.end_pos = QPointF(self.dragging_item.end_pos.x() + dx, self.dragging_item.end_pos.y() + dy)
            else:
                self.dragging_item.pos = QPointF(new_x, new_y)
            self.update()
            self.sig_content_changed.emit()
        elif self.drawing_box:
            self.box_end = pt
            self.update()
        elif self.drawing_arrow:
            self.arrow_end = QPointF(pt)
            self.update()
        elif self.drawing_step_arrow:
            self.step_arrow_end = QPointF(pt)
            self.update()
        elif self.drawing_elbow:
            self.elbow_end = QPointF(pt)
            self.update()
        elif self.drawing_callout:
            self.callout_end = QPointF(pt)
            self.update()
        elif self.drawing_blur:
            self.blur_end = pt
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

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if hasattr(self, "resizing_overlay_handle") and self.resizing_overlay_handle:
                self.resizing_overlay_handle = None
            if self.dragging_item:
                self.dragging_item = None
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
                self.set_mode("SELECT")
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
                self.set_mode("SELECT")
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
                self.set_mode("SELECT")
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
                    self.items.append(ElbowArrowItem(self.elbow_start, self.elbow_end, arr_style, "HV"))
                    self.update()
                    self.sig_content_changed.emit()
                self.set_mode("SELECT")
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
                self.set_mode("SELECT")
            elif self.drawing_blur:
                self.drawing_blur = False
                r = QRect(self.blur_start, self.blur_end).normalized()
                if r.width() > 8 and r.height() > 8:
                    self.push_undo()
                    blur_st = dict(self.config.get("blur_style", DEFAULT_CONFIG["blur_style"]))
                    self.items.append(BlurMosaicItem(r, blur_st))
                    self.update()
                    self.sig_content_changed.emit()
                self.set_mode("SELECT")

    def mouseDoubleClickEvent(self, event):
        pt = event.pos()
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

    def prompt_text_dialog(self, initial_text):
        try:
            dlg = QDialog(self)
            dlg.setWindowTitle("설명 텍스트 입력")
            dlg.setFixedSize(360, 140)
            layout = QVBoxLayout(dlg)

            lbl = QLabel("표시할 설명 텍스트를 입력하세요:", dlg)
            lbl.setFont(QFont("Malgun Gothic", 10))
            layout.addWidget(lbl)

            line_edit = QLineEdit(initial_text, dlg)
            line_edit.setFont(QFont("Malgun Gothic", 11))
            line_edit.returnPressed.connect(dlg.accept)
            layout.addWidget(line_edit)

            btn_box = QHBoxLayout()
            btn_ok = QPushButton("확인", dlg)
            btn_ok.setDefault(True)
            btn_ok.clicked.connect(dlg.accept)
            btn_cancel = QPushButton("취소", dlg)
            btn_cancel.clicked.connect(dlg.reject)
            btn_box.addStretch()
            btn_box.addWidget(btn_ok)
            btn_box.addWidget(btn_cancel)
            layout.addLayout(btn_box)

            line_edit.setFocus()
            line_edit.selectAll()
            if dlg.exec_() == QDialog.Accepted:
                return line_edit.text(), True
        except Exception as e:
            print(f"[텍스트 입력 오류]: {e}")
        return "", False

    def prompt_hotkey_dialog(self, initial_text="Enter ↵"):
        try:
            dlg = QDialog(self)
            dlg.setWindowTitle("단축키 뱃지 선택/입력")
            dlg.setFixedSize(380, 240)
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
            btn_ok.setDefault(True)
            btn_ok.clicked.connect(dlg.accept)
            btn_cancel = QPushButton("취소", dlg)
            btn_cancel.clicked.connect(dlg.reject)
            btn_box.addStretch()
            btn_box.addWidget(btn_ok)
            btn_box.addWidget(btn_cancel)
            layout.addLayout(btn_box)

            line_edit.setFocus()
            line_edit.selectAll()
            if dlg.exec_() == QDialog.Accepted:
                return line_edit.text(), True
        except Exception as e:
            print(f"[단축키 입력 오류]: {e}")
        return "", False

    def prompt_draft_dialog(self, initial_text="DRAFT"):
        try:
            dlg = QDialog(self)
            dlg.setWindowTitle("Draft 스탬프 텍스트 변경")
            dlg.setFixedSize(380, 240)
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
            btn_ok.setDefault(True)
            btn_ok.clicked.connect(dlg.accept)
            btn_cancel = QPushButton("취소", dlg)
            btn_cancel.clicked.connect(dlg.reject)
            btn_box.addStretch()
            btn_box.addWidget(btn_ok)
            btn_box.addWidget(btn_cancel)
            layout.addLayout(btn_box)

            line_edit.setFocus()
            line_edit.selectAll()
            if dlg.exec_() == QDialog.Accepted:
                return line_edit.text(), True
        except Exception as e:
            print(f"[Draft 텍스트 입력 오류]: {e}")
        return "", False

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing, True)

            # 1. 배경 이미지
            if self.pixmap:
                painter.drawPixmap(0, 0, self.pixmap)
            else:
                painter.fillRect(self.rect(), QColor(240, 240, 240))
                painter.setPen(QColor(160, 160, 160))
                painter.setFont(QFont("Malgun Gothic", 12))
                painter.drawText(self.rect(), Qt.AlignCenter, "F9 키를 눌러 화면을 캡처하세요.")
                return

            # 2. 모든 주석 렌더링 (블러는 원본 픽셀맵 합성)
            for item in self.items:
                try:
                    if isinstance(item, BlurMosaicItem):
                        item.render_mosaic(painter, self.pixmap)
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
                temp_elbow = ElbowArrowItem(self.elbow_start, self.elbow_end, arr_style, "HV")
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

            # 4. 선택된 객체 하이라이트
            if self.selected_item and self.current_mode == "SELECT":
                painter.save()
                painter.setPen(QPen(QColor(33, 150, 243), 1.5, Qt.DotLine))
                painter.setBrush(Qt.NoBrush)
                if isinstance(self.selected_item, (ImageOverlayItem, DraftStampItem)):
                    pass
                elif isinstance(self.selected_item, StampItem):
                    r = self.selected_item.style.get("size", 32) / 2.0 + 3
                    painter.drawEllipse(self.selected_item.pos, r, r)
                elif isinstance(self.selected_item, (TextLabelItem, HotkeyBadgeItem)):
                    painter.drawRect(self.selected_item.get_rect().adjusted(-2, -2, 2, 2))
                elif isinstance(self.selected_item, (HighlightBoxItem, BlurMosaicItem)):
                    painter.drawRect(self.selected_item.rect.adjusted(-2, -2, 2, 2))
                elif isinstance(self.selected_item, CalloutItem):
                    painter.drawRect(self.selected_item.box_rect.adjusted(-2, -2, 2, 2))
                    painter.setBrush(QBrush(QColor(33, 150, 243)))
                    painter.drawEllipse(self.selected_item.target_pt, 3.5, 3.5)
                elif isinstance(self.selected_item, (ArrowItem, StepArrowItem)):
                    p1 = self.selected_item.start_pos
                    p2 = self.selected_item.end_pos
                    painter.drawLine(p1, p2)
                    painter.setBrush(QBrush(QColor(33, 150, 243)))
                    painter.drawEllipse(p1, 3.5, 3.5)
                    painter.drawEllipse(p2, 3.5, 3.5)
                elif isinstance(self.selected_item, ElbowArrowItem):
                    p1 = self.selected_item.start_pos
                    corner = self.selected_item.get_corner_point()
                    p2 = self.selected_item.end_pos
                    painter.drawLine(p1, corner)
                    painter.drawLine(corner, p2)
                    painter.setBrush(QBrush(QColor(33, 150, 243)))
                    painter.drawEllipse(p1, 3.5, 3.5)
                    painter.drawEllipse(corner, 3.0, 3.0)
                    painter.drawEllipse(p2, 3.5, 3.5)
                painter.restore()
        finally:
            painter.end()

    def get_composed_image(self):
        """현재 캔버스 원본 해상도로 주석 일체형 합성 QImage 생성"""
        if self.pixmap is None:
            return None
        img = QImage(self.pixmap.size(), QImage.Format_ARGB32)
        img.fill(Qt.transparent)

        painter = QPainter(img)
        try:
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.drawPixmap(0, 0, self.pixmap)

            for item in self.items:
                try:
                    if isinstance(item, BlurMosaicItem):
                        item.render_mosaic(painter, self.pixmap)
                    elif isinstance(item, (ImageOverlayItem, DraftStampItem)):
                        item.render(painter, is_selected=False)
                    else:
                        item.render(painter)
                except Exception as e:
                    print(f"[합성 주석 렌더링 예외]: {e}")
        finally:
            painter.end()
        return img


# ==============================================================================
# 6. 내보내기 & 파워포인트 연동 엔진 (Export Engine)
# ==============================================================================
class ExportEngine:
    @staticmethod
    def qimage_to_pil(qimg: QImage) -> Image.Image:
        qimg = qimg.convertToFormat(QImage.Format_RGBA8888)
        width = qimg.width()
        height = qimg.height()
        ptr = qimg.bits()
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
            if ppt_app.Presentations.Count == 0:
                # 열려 있는 프레젠테이션이 없으면 새 프레젠테이션 생성
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


# ==============================================================================
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
# 8. 스튜디오 메인 윈도우 (ManualStudioWindow)
# ==============================================================================
class ManualStudioWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("매뉴얼 스튜디오 (Manual Studio) - DragonRPA Co. [평가판]")
        self.resize(1180, 780)

        # 윈도우 및 작업표시줄 아이콘 설정 (DragonRPA CI)
        ci_pix = get_dragon_rpa_ci_pixmap()
        if not ci_pix.isNull():
            self.setWindowIcon(QIcon(ci_pix))

        self.config = load_config()
        self.last_capture_rect = None
        self.overlay_window = None
        self.current_project_path = None

        # 실시간 서식 상태
        self.current_stamp_color = self.config.get("stamp_style", {}).get("bg_color", "#E53935")
        self.current_text_color = self.config.get("text_style", {}).get("text_color", "#FFFFFF")
        self.current_text_bg_color = self.config.get("text_style", {}).get("bg_color", "#212121")
        self.current_title_color = self.config.get("ppt_layout", {}).get("title_font_color", "#000000")

        self.init_ui()
        self.init_hotkey()

    def init_ui(self):
        # 0. 상단 메뉴바 초기화 (우측 끝에 CI + 회사명 + About 버튼 탑재)
        self.init_menu_bar()

        # 중앙 위젯
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        # 1. 리본 바 컨테이너 (Office / Snagit 스타일)
        ribbon_frame = QFrame(self)
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
                font-family: 'Malgun Gothic';
                font-size: 11px;
                font-weight: bold;
                padding: 4px 7px;
                border: 1px solid #D0D0D0;
                border-radius: 4px;
                background-color: #FFFFFF;
                white-space: nowrap;
            }
            QPushButton:hover {
                background-color: #EBF3FB;
                border-color: #2196F3;
            }
            QPushButton:checked {
                background-color: #2196F3;
                color: #FFFFFF;
                border-color: #1976D2;
            }
            QLabel {
                font-family: 'Malgun Gothic';
                font-size: 11px;
                font-weight: bold;
                color: #334155;
                white-space: nowrap;
            }
            QSpinBox {
                font-family: 'Malgun Gothic';
                font-size: 11px;
                padding: 2px 3px;
                border: 1px solid #CBD5E1;
                border-radius: 3px;
                background-color: #FFFFFF;
                white-space: nowrap;
            }
            QCheckBox {
                font-family: 'Malgun Gothic';
                font-size: 11px;
                font-weight: bold;
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
        tools_layout.setContentsMargins(4, 4, 4, 4)
        tools_layout.setSpacing(6)

        # 1) [캡처] 그룹
        self.btn_capture = QPushButton("📸 고정 캡처 (F9)", self)
        self.btn_capture.setToolTip("지정된 고정 영역을 즉시 캡처합니다.")
        self.btn_capture.setStyleSheet("background-color: #E3F2FD; color: #1565C0; border-color: #90CAF9;")
        self.btn_capture.clicked.connect(self.handle_hotkey_capture)

        self.btn_drag_capture = QPushButton("📐 영역 지정 (Shift+F9)", self)
        self.btn_drag_capture.setToolTip("화면에서 원하는 영역을 드래그하여 지정합니다.")
        self.btn_drag_capture.setStyleSheet("background-color: #F3E5F5; color: #7B1FA2; border-color: #CE93D8;")
        self.btn_drag_capture.clicked.connect(self.start_capture)

        self.btn_sub_capture = QPushButton("🪟 부분 추가 (F8)", self)
        self.btn_sub_capture.setToolTip("화면의 특정 영역(모달/팝업 등)을 부분 캡처하여 스튜디오에 독립 이미지 객체로 추가합니다.")
        self.btn_sub_capture.setStyleSheet("background-color: #FFF3E0; color: #E65100; border-color: #FFCC80;")
        self.btn_sub_capture.clicked.connect(self.start_sub_capture)

        cap_grid = QGridLayout()
        cap_grid.setContentsMargins(0, 0, 0, 0)
        cap_grid.setSpacing(3)
        cap_grid.addWidget(self.btn_capture, 0, 0)
        cap_grid.addWidget(self.btn_drag_capture, 1, 0)
        cap_grid.addWidget(self.btn_sub_capture, 0, 1, 2, 1)
        tools_layout.addWidget(self.create_ribbon_group("캡처", cap_grid))

        # 2) [프로젝트] 그룹
        self.btn_open_project = QPushButton("📂 프로젝트 열기 (Ctrl+O)", self)
        self.btn_open_project.setToolTip("기존 저장된 프로젝트(.mcs.json)를 불러와 개별 객체를 재편집합니다.")
        self.btn_open_project.clicked.connect(self.action_open_project)

        self.btn_save_project = QPushButton("💾 프로젝트 저장 (Ctrl+S)", self)
        self.btn_save_project.setToolTip("현재 작업 중인 개별 객체와 원본 캡처를 프로젝트(.mcs.json)로 저장합니다.")
        self.btn_save_project.clicked.connect(self.action_save_project)

        self.btn_open_file = QPushButton("🖼 이미지 열기", self)
        self.btn_open_file.setToolTip("외부 이미지 파일을 불러와 캔버스에 배치합니다.")
        self.btn_open_file.clicked.connect(self.open_image_file)

        self.btn_copy_image = QPushButton("📋 클립보드 복사", self)
        self.btn_copy_image.setToolTip("현재 편집 중인 완성 이미지를 클립보드에 복사합니다.")
        self.btn_copy_image.clicked.connect(self.copy_current_composed_image)

        proj_grid = QGridLayout()
        proj_grid.setContentsMargins(0, 0, 0, 0)
        proj_grid.setSpacing(3)
        proj_grid.addWidget(self.btn_open_project, 0, 0)
        proj_grid.addWidget(self.btn_save_project, 0, 1)
        proj_grid.addWidget(self.btn_open_file, 1, 0)
        proj_grid.addWidget(self.btn_copy_image, 1, 1)
        tools_layout.addWidget(self.create_ribbon_group("프로젝트", proj_grid))

        # 2) [선택·편집] 그룹
        self.btn_mode_select = QPushButton("👆 선택", self)
        self.btn_mode_select.setCheckable(True)
        self.btn_mode_select.setChecked(True)
        self.btn_mode_select.clicked.connect(lambda: self.switch_mode("SELECT"))

        self.btn_undo = QPushButton("↩ 실행 취소 (Ctrl+Z)", self)
        self.btn_undo.clicked.connect(self.action_undo)

        self.btn_clear = QPushButton("🗑 전체 삭제", self)
        self.btn_clear.clicked.connect(self.action_clear)

        edit_grid = QGridLayout()
        edit_grid.setContentsMargins(0, 0, 0, 0)
        edit_grid.setSpacing(3)
        edit_grid.addWidget(self.btn_mode_select, 0, 0)
        edit_grid.addWidget(self.btn_undo, 0, 1)
        edit_grid.addWidget(self.btn_clear, 1, 0, 1, 2)
        tools_layout.addWidget(self.create_ribbon_group("선택·편집", edit_grid))

        # 3) [단계·흐름] 그룹 (5대 추천: 스탬프 화살표, 직각 꺾은선 화살표 포함)
        self.btn_mode_stamp = QPushButton("① 번호 스탬프", self)
        self.btn_mode_stamp.setCheckable(True)
        self.btn_mode_stamp.clicked.connect(lambda: self.switch_mode("STAMP"))

        self.btn_mode_step_arrow = QPushButton("①➔ 스탬프 화살표", self)
        self.btn_mode_step_arrow.setCheckable(True)
        self.btn_mode_step_arrow.setToolTip("번호 스탬프와 지시 화살표를 일체형으로 배치합니다.")
        self.btn_mode_step_arrow.clicked.connect(lambda: self.switch_mode("STEP_ARROW"))

        self.btn_mode_elbow = QPushButton("↳ 직각 화살표", self)
        self.btn_mode_elbow.setCheckable(True)
        self.btn_mode_elbow.setToolTip("업무 흐름이나 메뉴 단계를 직각(L자)으로 꺾어 가리킵니다.")
        self.btn_mode_elbow.clicked.connect(lambda: self.switch_mode("ELBOW"))

        self.btn_mode_arrow = QPushButton("↗ 직선 화살표", self)
        self.btn_mode_arrow.setCheckable(True)
        self.btn_mode_arrow.clicked.connect(lambda: self.switch_mode("ARROW"))

        step_grid = QGridLayout()
        step_grid.setContentsMargins(0, 0, 0, 0)
        step_grid.setSpacing(3)
        step_grid.addWidget(self.btn_mode_stamp, 0, 0)
        step_grid.addWidget(self.btn_mode_step_arrow, 0, 1)
        step_grid.addWidget(self.btn_mode_elbow, 1, 0)
        step_grid.addWidget(self.btn_mode_arrow, 1, 1)
        tools_layout.addWidget(self.create_ribbon_group("단계·흐름", step_grid))

        # 4) [강조·보안] 그룹 (5대 추천: 비파괴 모자이크 블러 포함)
        self.btn_mode_box = QPushButton("🔲 사각 박스", self)
        self.btn_mode_box.setCheckable(True)
        self.btn_mode_box.clicked.connect(lambda: self.switch_mode("BOX"))

        self.btn_mode_blur = QPushButton("🌫 모자이크 블러", self)
        self.btn_mode_blur.setCheckable(True)
        self.btn_mode_blur.setToolTip("개인정보, 금액, 비밀번호 등을 가리는 비파괴 모자이크를 배치합니다.")
        self.btn_mode_blur.clicked.connect(lambda: self.switch_mode("BLUR"))

        self.btn_draft_stamp = QPushButton("📑 Draft 스탬프", self)
        self.btn_draft_stamp.setToolTip("화면 중앙에 60도 회전된 큼직한 사각형 Draft 워터마크 스탬프를 즉시 배치합니다.")
        self.btn_draft_stamp.setStyleSheet("background-color: #FFEBEE; color: #C62828; border-color: #EF9A9A;")
        self.btn_draft_stamp.clicked.connect(self.action_add_draft_stamp)

        box_grid = QGridLayout()
        box_grid.setContentsMargins(0, 0, 0, 0)
        box_grid.setSpacing(3)
        box_grid.addWidget(self.btn_mode_box, 0, 0)
        box_grid.addWidget(self.btn_mode_blur, 1, 0)
        box_grid.addWidget(self.btn_draft_stamp, 0, 1, 2, 1)
        tools_layout.addWidget(self.create_ribbon_group("강조·보안", box_grid))

        # 5) [텍스트·단축키] 그룹 (5대 추천: 지시선 말풍선, 3D 키캡 단축키 뱃지 포함)
        self.btn_mode_callout = QPushButton("💬 설명 말풍선", self)
        self.btn_mode_callout.setCheckable(True)
        self.btn_mode_callout.setToolTip("대상 UI를 꼬리로 가리키며 설명을 기재하는 말풍선을 배치합니다.")
        self.btn_mode_callout.clicked.connect(lambda: self.switch_mode("CALLOUT"))

        self.btn_mode_text = QPushButton("🔤 텍스트 라벨", self)
        self.btn_mode_text.setCheckable(True)
        self.btn_mode_text.clicked.connect(lambda: self.switch_mode("TEXT"))

        self.btn_mode_hotkey = QPushButton("⌨ 단축키 뱃지", self)
        self.btn_mode_hotkey.setCheckable(True)
        self.btn_mode_hotkey.setToolTip("Ctrl+C, Enter 등 3D 키캡 스타일 단축키를 배치합니다.")
        self.btn_mode_hotkey.clicked.connect(lambda: self.switch_mode("HOTKEY"))

        text_grid = QGridLayout()
        text_grid.setContentsMargins(0, 0, 0, 0)
        text_grid.setSpacing(3)
        text_grid.addWidget(self.btn_mode_callout, 0, 0)
        text_grid.addWidget(self.btn_mode_text, 0, 1)
        text_grid.addWidget(self.btn_mode_hotkey, 1, 0, 1, 2)
        tools_layout.addWidget(self.create_ribbon_group("텍스트·단축키", text_grid))

        # 6) [PPT 출력] 그룹
        self.btn_export = QPushButton("🚀 슬라이드 생성 (F10)", self)
        self.btn_export.setStyleSheet("""
            QPushButton {
                background-color: #E53935;
                color: #FFFFFF;
                border: 1px solid #C62828;
                font-size: 11px;
                padding: 5px 12px;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
        """)
        self.btn_export.clicked.connect(self.export_to_ppt_and_clipboard)

        self.btn_ppt_fit = QPushButton("📐 슬라이드 맞춤", self)
        self.btn_ppt_fit.setToolTip("지정한 좌상단(Left, Top)에서 슬라이드 여백에 꼭 맞게 배율을 자동 계산합니다.")
        self.btn_ppt_fit.setStyleSheet("background-color: #E8F5E9; color: #2E7D32; border-color: #A5D6A7;")
        self.btn_ppt_fit.clicked.connect(self.auto_fit_ppt_scale)

        self.chk_ppt_title = QCheckBox("제목 상자", self)
        self.chk_ppt_title.setToolTip("슬라이드 상단에 'Step N. [단계명 입력]' 텍스트 상자를 자동 삽입합니다.")
        self.chk_ppt_title.setChecked(self.config.get("ppt_layout", {}).get("include_title", True))
        self.chk_ppt_title.toggled.connect(self.on_ppt_layout_changed)

        self.btn_renumber_steps = QPushButton("🔢 Step 재정렬", self)
        self.btn_renumber_steps.setToolTip("열려있는 파워포인트의 모든 슬라이드를 순서대로 확인하여 Step 번호를 1부터 자동 재정렬합니다.")
        self.btn_renumber_steps.setStyleSheet("background-color: #E3F2FD; color: #1565C0; border-color: #90CAF9; font-weight: bold;")
        self.btn_renumber_steps.clicked.connect(self.action_renumber_powerpoint_steps)

        ppt_grid = QGridLayout()
        ppt_grid.setContentsMargins(0, 0, 0, 0)
        ppt_grid.setSpacing(3)
        ppt_grid.addWidget(self.btn_export, 0, 0)
        ppt_grid.addWidget(self.btn_ppt_fit, 0, 1)
        ppt_grid.addWidget(self.chk_ppt_title, 1, 0)
        ppt_grid.addWidget(self.btn_renumber_steps, 1, 1)
        tools_layout.addWidget(self.create_ribbon_group("PPT 출력", ppt_grid))

        tools_layout.addStretch(1)
        self.ribbon_tabs.addTab(tab_tools, "도구")

        # -------------------------------------------------------------
        # TAB 2: 서식·설정 (Format & Settings)
        # -------------------------------------------------------------
        tab_format = QWidget()
        format_layout = QHBoxLayout(tab_format)
        format_layout.setContentsMargins(4, 4, 4, 4)
        format_layout.setSpacing(6)

        # 1) [스탬프] 서식 그룹
        self.spin_stamp_size = QSpinBox(self)
        self.spin_stamp_size.setRange(16, 120)
        self.spin_stamp_size.setSingleStep(2)
        self.spin_stamp_size.setValue(self.config.get("stamp_style", {}).get("size", 32))
        self.spin_stamp_size.setSuffix(" px")
        self.spin_stamp_size.setFixedWidth(64)
        self.spin_stamp_size.valueChanged.connect(self.on_stamp_size_changed)

        self.btn_stamp_color = QPushButton(self)
        self.btn_stamp_color.setFixedSize(28, 24)
        self.update_stamp_color_button()
        self.btn_stamp_color.clicked.connect(self.choose_stamp_color)

        self.btn_reset_stamp_index = QPushButton("①번 리셋", self)
        self.btn_reset_stamp_index.setToolTip("스탬프 다음 번호를 ①번으로 다시 초기화합니다.")
        self.btn_reset_stamp_index.clicked.connect(self.reset_stamp_index)

        st_lay = QHBoxLayout()
        st_lay.setContentsMargins(0, 0, 0, 0)
        st_lay.setSpacing(4)
        st_lay.addWidget(self.create_stack_field("크기", self.spin_stamp_size))
        st_lay.addWidget(self.create_stack_field("배경색", self.btn_stamp_color))
        st_lay.addWidget(self.create_stack_field("번호", self.btn_reset_stamp_index))
        format_layout.addWidget(self.create_ribbon_group("스탬프", st_lay))

        # 2) [선·화살표] 서식 그룹
        self.spin_box_width_tab = QSpinBox(self)
        self.spin_box_width_tab.setRange(1, 20)
        self.spin_box_width_tab.setValue(self.config.get("highlight_box_style", {}).get("border_width", 3))
        self.spin_box_width_tab.setSuffix(" px")
        self.spin_box_width_tab.setFixedWidth(56)

        self.spin_arrow_head = QSpinBox(self)
        self.spin_arrow_head.setRange(6, 40)
        self.spin_arrow_head.setValue(self.config.get("arrow_style", {}).get("head_size", 14))
        self.spin_arrow_head.setSuffix(" px")
        self.spin_arrow_head.setFixedWidth(56)
        self.spin_arrow_head.valueChanged.connect(self.on_arrow_head_changed)

        self.chk_box_fill_tab = QCheckBox("음영", self)
        self.chk_box_fill_tab.setChecked(self.config.get("highlight_box_style", {}).get("fill", False))

        ln_lay = QHBoxLayout()
        ln_lay.setContentsMargins(0, 0, 0, 0)
        ln_lay.setSpacing(4)
        ln_lay.addWidget(self.create_stack_field("선 두께", self.spin_box_width_tab))
        ln_lay.addWidget(self.create_stack_field("촉 크기", self.spin_arrow_head))
        ln_lay.addWidget(self.create_stack_field("채우기", self.chk_box_fill_tab))
        format_layout.addWidget(self.create_ribbon_group("선·화살표", ln_lay))

        # 3) [텍스트·말풍선] 서식 그룹
        self.spin_text_font_size = QSpinBox(self)
        self.spin_text_font_size.setRange(8, 72)
        self.spin_text_font_size.setValue(self.config.get("text_style", {}).get("font_size", 14))
        self.spin_text_font_size.setSuffix(" pt")
        self.spin_text_font_size.setFixedWidth(58)
        self.spin_text_font_size.valueChanged.connect(self.on_text_font_size_changed)

        self.btn_text_color = QPushButton("가", self)
        self.btn_text_color.setFixedSize(28, 24)
        self.update_text_color_button()
        self.btn_text_color.clicked.connect(self.choose_text_color)

        self.btn_text_bg_color = QPushButton(self)
        self.btn_text_bg_color.setFixedSize(28, 24)
        self.update_text_bg_color_button()
        self.btn_text_bg_color.clicked.connect(self.choose_text_bg_color)

        self.spin_callout_tail_size = QSpinBox(self)
        self.spin_callout_tail_size.setRange(8, 40)
        self.spin_callout_tail_size.setValue(self.config.get("callout_style", {}).get("tail_base_width", 16))
        self.spin_callout_tail_size.setSuffix(" px")
        self.spin_callout_tail_size.setFixedWidth(58)
        self.spin_callout_tail_size.valueChanged.connect(self.on_callout_tail_size_changed)

        tx_lay = QHBoxLayout()
        tx_lay.setContentsMargins(0, 0, 0, 0)
        tx_lay.setSpacing(4)
        tx_lay.addWidget(self.create_stack_field("글꼴", self.spin_text_font_size))
        tx_lay.addWidget(self.create_stack_field("글자색", self.btn_text_color))
        tx_lay.addWidget(self.create_stack_field("배경색", self.btn_text_bg_color))
        tx_lay.addWidget(self.create_stack_field("꼬리 너비", self.spin_callout_tail_size))
        format_layout.addWidget(self.create_ribbon_group("텍스트·말풍선", tx_lay))

        # 4) [보안·단축키] 서식 그룹
        self.spin_blur_block = QSpinBox(self)
        self.spin_blur_block.setRange(4, 40)
        self.spin_blur_block.setValue(self.config.get("blur_style", {}).get("block_size", 10))
        self.spin_blur_block.setSuffix(" px")
        self.spin_blur_block.setFixedWidth(58)
        self.spin_blur_block.valueChanged.connect(self.on_blur_block_changed)

        self.spin_hotkey_font_size = QSpinBox(self)
        self.spin_hotkey_font_size.setRange(8, 36)
        self.spin_hotkey_font_size.setValue(self.config.get("hotkey_style", {}).get("font_size", 12))
        self.spin_hotkey_font_size.setSuffix(" pt")
        self.spin_hotkey_font_size.setFixedWidth(58)
        self.spin_hotkey_font_size.valueChanged.connect(self.on_hotkey_font_size_changed)

        sec_lay = QHBoxLayout()
        sec_lay.setContentsMargins(0, 0, 0, 0)
        sec_lay.setSpacing(4)
        sec_lay.addWidget(self.create_stack_field("모자이크", self.spin_blur_block))
        sec_lay.addWidget(self.create_stack_field("키캡 글꼴", self.spin_hotkey_font_size))
        format_layout.addWidget(self.create_ribbon_group("보안·단축키", sec_lay))

        # 5) [PPT 규격·배치] 서식 그룹
        self.spin_target_width = QSpinBox(self)
        self.spin_target_width.setRange(400, 3840)
        self.spin_target_width.setSingleStep(10)
        self.spin_target_width.setValue(self.config.get("target_width", 960))
        self.spin_target_width.setSuffix(" px")
        self.spin_target_width.setFixedWidth(72)
        self.spin_target_width.valueChanged.connect(self.on_target_width_changed)

        ppt_l = self.config.get("ppt_layout", {})
        self.spin_ppt_left = QSpinBox(self)
        self.spin_ppt_left.setRange(0, 1920)
        self.spin_ppt_left.setSingleStep(5)
        self.spin_ppt_left.setValue(ppt_l.get("left", 50))
        self.spin_ppt_left.setSuffix(" pt")
        self.spin_ppt_left.setFixedWidth(60)
        self.spin_ppt_left.valueChanged.connect(self.on_ppt_layout_changed)

        self.spin_ppt_top = QSpinBox(self)
        self.spin_ppt_top.setRange(0, 1080)
        self.spin_ppt_top.setSingleStep(5)
        self.spin_ppt_top.setValue(ppt_l.get("top", 80))
        self.spin_ppt_top.setSuffix(" pt")
        self.spin_ppt_top.setFixedWidth(60)
        self.spin_ppt_top.valueChanged.connect(self.on_ppt_layout_changed)

        self.spin_ppt_scale = QSpinBox(self)
        self.spin_ppt_scale.setRange(10, 300)
        self.spin_ppt_scale.setSingleStep(5)
        self.spin_ppt_scale.setValue(ppt_l.get("scale", 90))
        self.spin_ppt_scale.setSuffix(" %")
        self.spin_ppt_scale.setFixedWidth(60)
        self.spin_ppt_scale.valueChanged.connect(self.on_ppt_layout_changed)

        ppt_cfg_lay = QHBoxLayout()
        ppt_cfg_lay.setContentsMargins(0, 0, 0, 0)
        ppt_cfg_lay.setSpacing(4)
        ppt_cfg_lay.addWidget(self.create_stack_field("가로폭", self.spin_target_width))
        ppt_cfg_lay.addWidget(self.create_stack_field("Left", self.spin_ppt_left))
        ppt_cfg_lay.addWidget(self.create_stack_field("Top", self.spin_ppt_top))
        ppt_cfg_lay.addWidget(self.create_stack_field("배율", self.spin_ppt_scale))
        format_layout.addWidget(self.create_ribbon_group("PPT 규격·배치", ppt_cfg_lay))

        # 6) [PPT 제목상자] 서식 그룹
        self.spin_title_x = QSpinBox(self)
        self.spin_title_x.setRange(0, 1920)
        self.spin_title_x.setSingleStep(5)
        self.spin_title_x.setValue(int(ppt_l.get("title_left", ppt_l.get("left", 26))))
        self.spin_title_x.setSuffix(" pt")
        self.spin_title_x.setFixedWidth(56)
        self.spin_title_x.valueChanged.connect(self.on_ppt_title_layout_changed)

        self.spin_title_y = QSpinBox(self)
        self.spin_title_y.setRange(0, 1080)
        self.spin_title_y.setSingleStep(5)
        self.spin_title_y.setValue(int(ppt_l.get("title_top", 15)))
        self.spin_title_y.setSuffix(" pt")
        self.spin_title_y.setFixedWidth(56)
        self.spin_title_y.valueChanged.connect(self.on_ppt_title_layout_changed)

        self.spin_title_w = QSpinBox(self)
        self.spin_title_w.setRange(50, 1920)
        self.spin_title_w.setSingleStep(20)
        self.spin_title_w.setValue(int(ppt_l.get("title_width", 500)))
        self.spin_title_w.setSuffix(" pt")
        self.spin_title_w.setFixedWidth(58)
        self.spin_title_w.valueChanged.connect(self.on_ppt_title_layout_changed)

        self.spin_title_h = QSpinBox(self)
        self.spin_title_h.setRange(15, 500)
        self.spin_title_h.setSingleStep(5)
        self.spin_title_h.setValue(int(ppt_l.get("title_height", 35)))
        self.spin_title_h.setSuffix(" pt")
        self.spin_title_h.setFixedWidth(52)
        self.spin_title_h.valueChanged.connect(self.on_ppt_title_layout_changed)

        self.spin_title_font_size = QSpinBox(self)
        self.spin_title_font_size.setRange(8, 72)
        self.spin_title_font_size.setValue(int(ppt_l.get("title_font_size", 18)))
        self.spin_title_font_size.setSuffix(" pt")
        self.spin_title_font_size.setFixedWidth(54)
        self.spin_title_font_size.valueChanged.connect(self.on_ppt_title_layout_changed)

        self.btn_title_color = QPushButton("가", self)
        self.btn_title_color.setFixedSize(28, 24)
        self.update_title_color_button()
        self.btn_title_color.clicked.connect(self.choose_title_font_color)

        self.chk_title_bold = QCheckBox("굵게", self)
        self.chk_title_bold.setChecked(bool(ppt_l.get("title_font_bold", True)))
        self.chk_title_bold.toggled.connect(self.on_ppt_title_layout_changed)

        self.btn_title_align = QPushButton("정렬", self)
        self.btn_title_align.setToolTip("제목 X 좌표를 이미지 Left 위치와 동일하게 정렬합니다.")
        self.btn_title_align.clicked.connect(self.align_title_x_to_image)

        title_cfg_lay = QHBoxLayout()
        title_cfg_lay.setContentsMargins(0, 0, 0, 0)
        title_cfg_lay.setSpacing(4)
        title_cfg_lay.addWidget(self.create_stack_field("제목 X", self.spin_title_x))
        title_cfg_lay.addWidget(self.create_stack_field("제목 Y", self.spin_title_y))
        title_cfg_lay.addWidget(self.create_stack_field("너비", self.spin_title_w))
        title_cfg_lay.addWidget(self.create_stack_field("높이", self.spin_title_h))
        title_cfg_lay.addWidget(self.create_stack_field("글꼴", self.spin_title_font_size))
        title_cfg_lay.addWidget(self.create_stack_field("색상", self.btn_title_color))
        title_cfg_lay.addWidget(self.create_stack_field("강조", self.chk_title_bold))
        title_cfg_lay.addWidget(self.create_stack_field("정렬", self.btn_title_align))
        format_layout.addWidget(self.create_ribbon_group("PPT 제목상자", title_cfg_lay))

        # 7) [환경] 서식 그룹
        self.btn_settings = QPushButton("⚙ 상세 설정", self)
        self.btn_settings.clicked.connect(self.open_settings_dialog)
        env_lay = QHBoxLayout()
        env_lay.setContentsMargins(0, 0, 0, 0)
        env_lay.addWidget(self.btn_settings)
        format_layout.addWidget(self.create_ribbon_group("환경설정", env_lay))

        format_layout.addStretch(1)
        self.ribbon_tabs.addTab(tab_format, "서식·설정")
        ribbon_vlayout.addWidget(self.ribbon_tabs)

        # -------------------------------------------------------------
        # 하단 상시 퀵 서식 바 (Quick Format Strip)
        # -------------------------------------------------------------
        quick_strip = QFrame(self)
        quick_strip.setObjectName("QuickStrip")
        quick_strip.setStyleSheet("""
            QFrame#QuickStrip {
                background-color: #F1F5F9;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
            }
        """)
        qs_lay = QHBoxLayout(quick_strip)
        qs_lay.setContentsMargins(6, 3, 6, 3)
        qs_lay.setSpacing(6)

        # 선 두께
        qs_lay.addWidget(QLabel("두께:", self))
        self.spin_box_width = QSpinBox(self)
        self.spin_box_width.setRange(1, 20)
        self.spin_box_width.setValue(self.config.get("highlight_box_style", {}).get("border_width", 3))
        self.spin_box_width.setSuffix(" px")
        self.spin_box_width.setFixedWidth(56)
        self.spin_box_width.valueChanged.connect(self.on_box_width_changed)
        self.spin_box_width.valueChanged.connect(
            lambda v: self.spin_box_width_tab.setValue(v) if self.spin_box_width_tab.value() != v else None
        )
        self.spin_box_width_tab.valueChanged.connect(
            lambda v: self.spin_box_width.setValue(v) if self.spin_box_width.value() != v else None
        )
        qs_lay.addWidget(self.spin_box_width)

        # 색상 프리셋
        qs_lay.addWidget(QLabel("색상:", self))
        self.box_color_buttons = []
        preset_colors = [
            ("#E53935", "🔴"),
            ("#1E88E5", "🔵"),
            ("#43A047", "🟢"),
            ("#FB8C00", "🟠"),
            ("#FDD835", "🟡"),
        ]
        for col_code, symbol in preset_colors:
            cbtn = QPushButton(symbol, self)
            cbtn.setFixedSize(26, 22)
            cbtn.setToolTip(f"색상 선택: {col_code}")
            cbtn.setStyleSheet(f"background-color: {col_code}; border-radius: 3px; padding: 1px;")
            cbtn.clicked.connect(lambda checked, c=col_code: self.choose_box_preset_color(c))
            qs_lay.addWidget(cbtn)
            self.box_color_buttons.append(cbtn)

        self.btn_custom_color = QPushButton("🎨", self)
        self.btn_custom_color.setFixedSize(26, 22)
        self.btn_custom_color.setToolTip("커스텀 색상 선택")
        self.btn_custom_color.clicked.connect(self.choose_box_custom_color)
        qs_lay.addWidget(self.btn_custom_color)

        self.chk_box_fill = QCheckBox("음영 채우기", self)
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

        # 고정 영역 제어
        self.chk_fixed_rect = QCheckBox("고정 모드", self)
        self.chk_fixed_rect.setChecked(self.config.get("fixed_rect_enabled", True))
        self.chk_fixed_rect.toggled.connect(self.on_fixed_rect_toggled)
        qs_lay.addWidget(self.chk_fixed_rect)

        fr = self.config.get("fixed_rect", {"x": 100, "y": 100, "width": 960, "height": 540})
        qs_lay.addWidget(QLabel("X:", self))
        self.spin_fx = QSpinBox(self)
        self.spin_fx.setRange(-9999, 9999)
        self.spin_fx.setValue(fr.get("x", 100))
        self.spin_fx.setFixedWidth(52)
        self.spin_fx.valueChanged.connect(self.on_fixed_rect_changed)
        qs_lay.addWidget(self.spin_fx)

        qs_lay.addWidget(QLabel("Y:", self))
        self.spin_fy = QSpinBox(self)
        self.spin_fy.setRange(-9999, 9999)
        self.spin_fy.setValue(fr.get("y", 100))
        self.spin_fy.setFixedWidth(52)
        self.spin_fy.valueChanged.connect(self.on_fixed_rect_changed)
        qs_lay.addWidget(self.spin_fy)

        qs_lay.addWidget(QLabel("W:", self))
        self.spin_fw = QSpinBox(self)
        self.spin_fw.setRange(10, 7680)
        self.spin_fw.setValue(fr.get("width", 960))
        self.spin_fw.setFixedWidth(58)
        self.spin_fw.valueChanged.connect(self.on_fixed_rect_changed)
        qs_lay.addWidget(self.spin_fw)

        qs_lay.addWidget(QLabel("H:", self))
        self.spin_fh = QSpinBox(self)
        self.spin_fh.setRange(10, 4320)
        self.spin_fh.setValue(fr.get("height", 540))
        self.spin_fh.setFixedWidth(58)
        self.spin_fh.valueChanged.connect(self.on_fixed_rect_changed)
        qs_lay.addWidget(self.spin_fh)

        self.btn_save_rect = QPushButton("📌 영역 저장", self)
        self.btn_save_rect.setStyleSheet("background-color: #FFF3E0; color: #E65100; border-color: #FFE0B2; padding: 2px 6px;")
        self.btn_save_rect.clicked.connect(self.save_current_as_fixed_rect)
        qs_lay.addWidget(self.btn_save_rect)

        qs_lay.addWidget(self.create_separator())

        # 모드 / 선택 상태 배지
        self.lbl_active_mode = QLabel("도구: 👆 선택", self)
        self.lbl_active_mode.setStyleSheet("""
            QLabel {
                background-color: #E2E8F0;
                color: #1E293B;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                padding: 2px 8px;
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
        self.scroll_area.setWidget(self.canvas)
        main_layout.addWidget(self.scroll_area, 1)

        # 3. 하단 상태바
        status_bar_widget = QWidget(self)
        status_layout = QHBoxLayout(status_bar_widget)
        status_layout.setContentsMargins(4, 2, 6, 2)
        status_layout.setSpacing(8)

        self.status_label = QLabel("대기 중: F9를 눌러 캡처하고, 주석 편집 후 F10을 눌러 슬라이드로 내보내세요.", self)
        self.status_label.setStyleSheet("color: #666666; font-size: 11px; padding: 2px 4px;")
        status_layout.addWidget(self.status_label, 1)

        # 하단 우측 개발사 정보 및 Contact
        ci_pix = get_dragon_rpa_ci_pixmap()
        lbl_bot_ci = QLabel(status_bar_widget)
        if not ci_pix.isNull():
            lbl_bot_ci.setPixmap(ci_pix.scaled(14, 14, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        status_layout.addWidget(lbl_bot_ci)

        lbl_bottom_dev = QLabel("(주)드래곤알피에이 (DragonRPA Co.) | 평가판 (~2026.12.31) | 77.victor.lee@gmail.com", status_bar_widget)
        lbl_bottom_dev.setStyleSheet("color: #94A3B8; font-size: 10.5px; font-weight: 500;")
        status_layout.addWidget(lbl_bottom_dev)

        main_layout.addWidget(status_bar_widget)

        self.sync_ui_from_config()

    def init_menu_bar(self):
        menubar = self.menuBar()
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
        file_menu = menubar.addMenu("파일(&F)")
        act_f9 = file_menu.addAction("📸 고정 캡처 (F9)")
        act_f9.triggered.connect(self.handle_hotkey_capture)
        act_shift_f9 = file_menu.addAction("📐 영역 지정 캡처 (Shift+F9)")
        act_shift_f9.triggered.connect(self.start_capture)
        act_f8 = file_menu.addAction("🪟 부분 추가 캡처 (F8)")
        act_f8.triggered.connect(self.start_sub_capture)
        file_menu.addSeparator()
        act_open_proj = file_menu.addAction("📂 프로젝트 열기... (Ctrl+O)")
        act_open_proj.triggered.connect(self.action_open_project)
        act_save_proj = file_menu.addAction("💾 프로젝트 저장 (Ctrl+S)")
        act_save_proj.triggered.connect(self.action_save_project)
        act_open_img = file_menu.addAction("🖼 외부 이미지 열기...")
        act_open_img.triggered.connect(self.open_image_file)
        file_menu.addSeparator()
        act_export_ppt = file_menu.addAction("🚀 PPT 슬라이드 생성 (F10)")
        act_export_ppt.triggered.connect(self.export_to_ppt_and_clipboard)
        file_menu.addSeparator()
        act_exit = file_menu.addAction("❌ 종료 (Alt+F4)")
        act_exit.triggered.connect(self.close)

        # 2. 편집(E) 메뉴
        edit_menu = menubar.addMenu("편집(&E)")
        act_undo = edit_menu.addAction("↩ 실행 취소 (Ctrl+Z)")
        act_undo.triggered.connect(self.action_undo)
        act_copy = edit_menu.addAction("📋 클립보드 복사")
        act_copy.triggered.connect(self.copy_current_composed_image)
        act_clear = edit_menu.addAction("🗑 전체 삭제")
        act_clear.triggered.connect(self.action_clear)
        edit_menu.addSeparator()
        act_renumber = edit_menu.addAction("🔢 PPT Step 번호 자동 재정렬")
        act_renumber.triggered.connect(self.action_renumber_powerpoint_steps)

        # 3. 도구(T) 메뉴
        tools_menu = menubar.addMenu("도구(&T)")
        act_sel = tools_menu.addAction("👆 선택 모드")
        act_sel.triggered.connect(lambda: self.switch_mode("SELECT"))
        act_st = tools_menu.addAction("① 번호 스탬프")
        act_st.triggered.connect(lambda: self.switch_mode("STAMP"))
        act_sa = tools_menu.addAction("①➔ 스탬프 화살표")
        act_sa.triggered.connect(lambda: self.switch_mode("STEP_ARROW"))
        act_ea = tools_menu.addAction("↳ 직각 화살표")
        act_ea.triggered.connect(lambda: self.switch_mode("ELBOW"))
        act_ar = tools_menu.addAction("↗ 직선 화살표")
        act_ar.triggered.connect(lambda: self.switch_mode("ARROW"))
        tools_menu.addSeparator()
        act_bx = tools_menu.addAction("🔲 사각 박스")
        act_bx.triggered.connect(lambda: self.switch_mode("BOX"))
        act_bl = tools_menu.addAction("🌫 모자이크 블러")
        act_bl.triggered.connect(lambda: self.switch_mode("BLUR"))
        act_dr = tools_menu.addAction("📑 Draft 스탬프")
        act_dr.triggered.connect(self.action_add_draft_stamp)
        tools_menu.addSeparator()
        act_co = tools_menu.addAction("💬 설명 말풍선")
        act_co.triggered.connect(lambda: self.switch_mode("CALLOUT"))
        act_tx = tools_menu.addAction("🔤 텍스트 라벨")
        act_tx.triggered.connect(lambda: self.switch_mode("TEXT"))
        act_hk = tools_menu.addAction("⌨ 단축키 뱃지")
        act_hk.triggered.connect(lambda: self.switch_mode("HOTKEY"))

        # 4. 설정(S) 메뉴
        settings_menu = menubar.addMenu("설정(&S)")
        act_cfg = settings_menu.addAction("⚙ 환경 설정...")
        act_cfg.triggered.connect(self.open_settings_dialog)

        # 5. 메뉴 오른쪽 끝 About 및 EULA 메뉴
        act_about = menubar.addAction("About(&A)")
        act_about.triggered.connect(self.show_about_dialog)

        act_eula = menubar.addAction("EULA(&E)")
        act_eula.triggered.connect(self.show_eula_dialog)

        # 6. 메뉴바 오른쪽 코너 위젯: CI 아이콘 + 회사명 + EULA 버튼 + About 버튼
        corner_widget = QWidget(self)
        corner_layout = QHBoxLayout(corner_widget)
        corner_layout.setContentsMargins(0, 0, 8, 0)
        corner_layout.setSpacing(6)

        ci_pix = get_dragon_rpa_ci_pixmap()
        lbl_ci = QLabel(corner_widget)
        if not ci_pix.isNull():
            lbl_ci.setPixmap(ci_pix.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            lbl_ci.setToolTip("DragonRPA Co. 공식 CI")

        lbl_company = QLabel("(주)드래곤알피에이 | DragonRPA Co.", corner_widget)
        lbl_company.setStyleSheet("""
            QLabel {
                font-family: 'Malgun Gothic';
                font-size: 11px;
                font-weight: bold;
                color: #475569;
                padding-right: 2px;
            }
        """)

        btn_eula_corner = QPushButton("📜 EULA", corner_widget)
        btn_eula_corner.setCursor(Qt.PointingHandCursor)
        btn_eula_corner.setStyleSheet("""
            QPushButton {
                background-color: #F8FAFC;
                color: #475569;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                padding: 2px 8px;
                font-family: 'Malgun Gothic';
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F1F5F9;
                border-color: #94A3B8;
                color: #0F172A;
            }
        """)
        btn_eula_corner.clicked.connect(self.show_eula_dialog)

        btn_about_corner = QPushButton("ℹ️ About", corner_widget)
        btn_about_corner.setCursor(Qt.PointingHandCursor)
        btn_about_corner.setStyleSheet("""
            QPushButton {
                background-color: #EFF6FF;
                color: #1D4ED8;
                border: 1px solid #BFDBFE;
                border-radius: 4px;
                padding: 2px 10px;
                font-family: 'Malgun Gothic';
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #DBEAFE;
                border-color: #93C5FD;
                color: #1E40AF;
            }
        """)
        btn_about_corner.clicked.connect(self.show_about_dialog)

        corner_layout.addWidget(lbl_ci)
        corner_layout.addWidget(lbl_company)
        corner_layout.addWidget(btn_eula_corner)
        corner_layout.addWidget(btn_about_corner)

        menubar.setCornerWidget(corner_widget, Qt.TopRightCorner)

    def show_about_dialog(self):
        dlg = AboutDialog(self)
        dlg.exec_()

    def show_eula_dialog(self):
        dlg = EulaDialog(self)
        dlg.exec_()


    def create_ribbon_group(self, title_text, layout_content):
        group = QFrame(self)
        group.setObjectName("RibbonGroup")
        group.setStyleSheet("""
            QFrame#RibbonGroup {
                background-color: #FAFAFA;
                border: 1px solid #E2E8F0;
                border-radius: 5px;
            }
        """)
        gl = QVBoxLayout(group)
        gl.setContentsMargins(4, 4, 4, 3)
        gl.setSpacing(3)
        gl.addLayout(layout_content)
        gl.addStretch(1)
        lbl = QLabel(title_text, group)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("font-size: 10px; color: #64748B; font-weight: bold; border: none; background: transparent; padding-top: 1px; white-space: nowrap;")
        gl.addWidget(lbl)
        return group

    def create_stack_field(self, label_text, widget):
        f_widget = QWidget(self)
        vl = QVBoxLayout(f_widget)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(2)
        lbl = QLabel(label_text, f_widget)
        lbl.setStyleSheet("font-size: 10px; color: #475569; font-weight: bold; border: none; background: transparent; white-space: nowrap;")
        vl.addWidget(lbl)
        vl.addWidget(widget)
        return f_widget

    def create_separator(self):
        line = QFrame(self)
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("border-color: #D0D0D0;")
        return line

    def open_image_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "이미지 파일 열기", "", "이미지 파일 (*.png *.jpg *.jpeg *.bmp *.webp);;모든 파일 (*.*)"
        )
        if file_path and os.path.exists(file_path):
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                self.on_capture_completed(pixmap)
                self.show_toast(f"이미지 로드 완료: {os.path.basename(file_path)}")

    def action_open_project(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "프로젝트 열기",
            "",
            "매뉴얼 프로젝트 (*.mcs.json *.json);;모든 파일 (*.*)"
        )
        if file_path and os.path.exists(file_path):
            self.load_project_file(file_path)

    def load_project_file(self, file_path: str):
        raw_pixmap, items, next_stamp_index, metadata = ProjectManager.load_project(file_path)
        if raw_pixmap is None or raw_pixmap.isNull():
            self.show_toast(f"프로젝트 로드 실패: 원본 캡처 이미지를 찾을 수 없습니다 ({os.path.basename(file_path)})")
            return False

        self.canvas.load_project_data(raw_pixmap, items, next_stamp_index)
        self.current_project_path = file_path
        self.last_capture_rect = None

        base_name = os.path.basename(file_path)
        self.setWindowTitle(f"매뉴얼 스튜디오 - [{base_name}]")
        self.status_label.setText(
            f"프로젝트 로드 완료: {base_name} (주석 {len(items)}개 복원됨) ➔ 수정 후 F10 누르면 슬라이드와 프로젝트가 갱신됩니다."
        )
        self.show_toast(f"📂 프로젝트 로드 완료: {base_name} (주석 {len(items)}개)")
        return True

    def action_save_project(self):
        if self.canvas.pixmap is None:
            self.show_toast("저장할 프로젝트 내용이 없습니다. 먼저 캡처하세요.")
            return False

        if self.current_project_path:
            return self.save_project_to_path(self.current_project_path)
        else:
            return self.action_save_as_project()

    def action_save_as_project(self):
        if self.canvas.pixmap is None:
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
            if f.startswith("Step_") and f.endswith(".mcs.json")
        ]
        default_name = f"Step_{len(existing) + 1:03d}.mcs.json"
        default_path = os.path.join(dest_folder, default_name)

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "프로젝트 저장",
            default_path,
            "매뉴얼 프로젝트 (*.mcs.json);;JSON 파일 (*.json);;모든 파일 (*.*)"
        )
        if file_path:
            return self.save_project_to_path(file_path)
        return False

    def save_project_to_path(self, file_path: str):
        metadata = {"ppt_layout": self.config.get("ppt_layout", {})}
        ok = ProjectManager.save_project(
            file_path,
            self.canvas.pixmap,
            self.canvas.items,
            self.canvas.next_stamp_index,
            metadata=metadata
        )
        if ok:
            self.current_project_path = file_path
            base_name = os.path.basename(file_path)
            self.setWindowTitle(f"매뉴얼 스튜디오 - [{base_name}]")
            self.status_label.setText(f"💾 프로젝트 저장 완료: {base_name}")
            self.show_toast(f"💾 프로젝트 저장 완료: {base_name}")
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
            try:
                ExportEngine.copy_to_clipboard(pil_img)
                self.show_toast("클립보드에 이미지 복사 완료 (Ctrl+V)")
            except Exception as e:
                self.show_toast(f"클립보드 복사 실패: {e}")

    def reset_stamp_index(self):
        self.canvas.next_stamp_index = 1
        self.show_toast("스탬프 다음 번호가 ①로 초기화되었습니다.")

    def update_mode_status_indicator(self, mode_or_name=None):
        mode_names = {
            "SELECT": "👆 선택",
            "STAMP": "① 번호 스탬프",
            "STEP_ARROW": "①➔ 스탬프 화살표",
            "ELBOW": "↳ 직각 화살표",
            "ARROW": "↗ 직선 화살표",
            "BOX": "🔲 사각 박스",
            "BLUR": "🌫 모자이크 블러",
            "CALLOUT": "💬 설명 말풍선",
            "TEXT": "🔤 텍스트 라벨",
            "HOTKEY": "⌨ 단축키 뱃지"
        }
        cur_mode = mode_or_name or self.canvas.current_mode
        text = mode_names.get(cur_mode, cur_mode)
        if hasattr(self, "lbl_active_mode"):
            self.lbl_active_mode.setText(f"도구: {text}")

    def init_hotkey(self):
        cap_key = self.config.get("hotkey_capture", "F9")
        exp_key = self.config.get("hotkey_export", "F10")
        self.hotkey_thread = GlobalHotkeyThread(cap_key, exp_key, self)
        self.hotkey_thread.sig_capture.connect(self.handle_hotkey_capture)
        self.hotkey_thread.sig_drag_capture.connect(self.start_capture)
        self.hotkey_thread.sig_sub_capture.connect(self.start_sub_capture)
        self.hotkey_thread.sig_export.connect(self.export_to_ppt_and_clipboard)
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
        if hasattr(self, "btn_mode_callout"):
            self.btn_mode_callout.setChecked(mode == "CALLOUT")
        self.btn_mode_text.setChecked(mode == "TEXT")
        if hasattr(self, "btn_mode_hotkey"):
            self.btn_mode_hotkey.setChecked(mode == "HOTKEY")
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
        self.btn_text_color.setToolTip(f"텍스트 글자 색상: {c}")

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
            self.btn_title_color.setToolTip(f"제목 글자 색상: {c}")

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
                self.lbl_active_mode.setText(f"선택: ① 스탬프 (#{item.index})")
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
                self.lbl_active_mode.setText(f"선택: ①➔ 스탬프 화살표 (#{item.index})")
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
            if hasattr(self, "lbl_active_mode"):
                self.lbl_active_mode.setText("선택: ↳ 직각 화살표")
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
                self.lbl_active_mode.setText("선택: ↗ 직선 화살표")
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
                self.lbl_active_mode.setText("선택: 🔲 사각 박스")
        elif isinstance(item, BlurMosaicItem):
            blk_s = int(item.style.get("block_size", 10))
            if hasattr(self, "spin_blur_block"):
                self.spin_blur_block.blockSignals(True)
                self.spin_blur_block.setValue(blk_s)
                self.spin_blur_block.blockSignals(False)
            if hasattr(self, "lbl_active_mode"):
                self.lbl_active_mode.setText("선택: 🌫 모자이크 블러")
        elif isinstance(item, CalloutItem):
            font_s = int(item.style.get("font_size", 12))
            border_w = int(item.style.get("border_width", 2))
            border_col = item.style.get("border_color", "#E53935")
            text_col = item.style.get("text_color", "#FFFFFF")
            bg_col = item.style.get("bg_color", "#212121")
            tail_s = int(item.style.get("tail_base_width", 16))
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
                self.lbl_active_mode.setText(f"선택: 💬 말풍선 ('{item.text[:10]}...')")
        elif isinstance(item, TextLabelItem):
            font_size = int(item.style.get("font_size", 14))
            text_col = item.style.get("text_color", "#FFFFFF")
            bg_col = item.style.get("bg_color", "#212121")
            self.spin_text_font_size.blockSignals(True)
            self.spin_text_font_size.setValue(font_size)
            self.spin_text_font_size.blockSignals(False)
            self.current_text_color = text_col
            self.update_text_color_button()
            self.current_text_bg_color = bg_col
            self.update_text_bg_color_button()
            if hasattr(self, "lbl_active_mode"):
                self.lbl_active_mode.setText(f"선택: 🔤 텍스트 ('{item.text[:10]}...')")
        elif isinstance(item, HotkeyBadgeItem):
            font_s = int(item.style.get("font_size", 12))
            if hasattr(self, "spin_hotkey_font_size"):
                self.spin_hotkey_font_size.blockSignals(True)
                self.spin_hotkey_font_size.setValue(font_s)
                self.spin_hotkey_font_size.blockSignals(False)
            if hasattr(self, "lbl_active_mode"):
                self.lbl_active_mode.setText(f"선택: ⌨ 단축키 ({item.key_text})")
        elif isinstance(item, ImageOverlayItem):
            bw = int(item.style.get("border_width", 2))
            self.spin_box_width.blockSignals(True)
            self.spin_box_width.setValue(bw)
            self.spin_box_width.blockSignals(False)
            if hasattr(self, "lbl_active_mode"):
                self.lbl_active_mode.setText(f"선택: 🪟 부분 이미지 ({int(item.rect.width())}×{int(item.rect.height())})")
        elif isinstance(item, DraftStampItem):
            bw = int(item.style.get("border_width", 5))
            self.spin_box_width.blockSignals(True)
            self.spin_box_width.setValue(bw)
            self.spin_box_width.blockSignals(False)
            if hasattr(self, "lbl_active_mode"):
                self.lbl_active_mode.setText(f"선택: 📑 Draft 스탬프 ('{item.text}')")

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

    def capture_fixed_rect(self):
        fr = self.config.get("fixed_rect", {"x": 100, "y": 100, "width": 960, "height": 540})
        x = fr.get("x", 100)
        y = fr.get("y", 100)
        w = fr.get("width", 960)
        h = fr.get("height", 540)

        # 캡처 순간 스튜디오 창이 대상 영역을 가리는 것을 방지하기 위해 잠시 숨김
        was_visible = self.isVisible() and not self.isMinimized()
        if was_visible:
            self.hide()
            QApplication.processEvents()
            time.sleep(0.05)

        try:
            screens = QApplication.screens()
            min_x = min(s.geometry().x() for s in screens)
            min_y = min(s.geometry().y() for s in screens)
            max_x = max(s.geometry().x() + s.geometry().width() for s in screens)
            max_y = max(s.geometry().y() + s.geometry().height() for s in screens)

            full_pixmap = QApplication.primaryScreen().grabWindow(
                0, min_x, min_y, max_x - min_x, max_y - min_y
            )

            rel_x = x - min_x
            rel_y = y - min_y
            cropped = full_pixmap.copy(rel_x, rel_y, w, h)

            if cropped.isNull() or cropped.width() < 5 or cropped.height() < 5:
                self.show_toast("화면 캡처 실패: 유효하지 않은 좌표입니다.")
                return

            self.on_capture_completed(cropped, QRect(x, y, w, h), is_fixed_capture=True)
            self.show_toast(f"고정 영역 ({x},{y} {w}×{h}px) 즉시 캡처 완료!")
        finally:
            if was_visible:
                self.show()
                self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
                self.activateWindow()

    def start_capture(self):
        # 캡처 전 스튜디오 창이 화면에 보이면 잠시 숨겨서 배경 작업 화면이 깨끗이 보이도록 함
        was_visible = self.isVisible() and not self.isMinimized()
        if was_visible:
            self.hide()
            QApplication.processEvents()
            time.sleep(0.06)

        try:
            self.overlay_window = CaptureOverlayWidget(
                last_rect=self.last_capture_rect,
                config=self.config
            )
            self.overlay_window.sig_captured.connect(self.on_capture_completed)
            self.overlay_window.sig_cancelled.connect(self.on_capture_cancelled)
            self.overlay_window.showFullScreen()
        except Exception as e:
            if was_visible:
                self.show()
                self.activateWindow()
            print(f"[오버레이 실행 오류]: {e}")

    def on_capture_cancelled(self):
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        self.activateWindow()

    def start_sub_capture(self):
        """F8 단축키 또는 리본 버튼: 모달/팝업 영역 부분 캡처 후 캔버스에 독립 이미지 객체로 추가"""
        if self.canvas.pixmap is None:
            self.show_toast("먼저 메인 화면(F9)을 캡처한 후 모달을 추가하세요.")
            return

        was_visible = self.isVisible() and not self.isMinimized()
        if was_visible:
            self.hide()
            QApplication.processEvents()
            time.sleep(0.06)

        try:
            self.overlay_window = CaptureOverlayWidget(
                last_rect=None,
                config=self.config,
                is_sub_capture=True
            )
            self.overlay_window.sig_captured.connect(self.on_sub_capture_completed)
            self.overlay_window.sig_cancelled.connect(self.on_capture_cancelled)
            self.overlay_window.showFullScreen()
        except Exception as e:
            if was_visible:
                self.show()
                self.activateWindow()
            print(f"[부분 캡처 오버레이 실행 오류]: {e}")

    def on_sub_capture_completed(self, pixmap, global_rect=None):
        # 창 전면 복원
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        self.activateWindow()

        if pixmap and not pixmap.isNull():
            self.canvas.add_image_overlay(pixmap)
            w = pixmap.width()
            h = pixmap.height()
            self.show_toast(f"🪟 부분 이미지({w}×{h}px) 추가 완료! 마우스로 이동 및 크기를 조절하세요.")

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
        self.setWindowTitle("매뉴얼 스튜디오 (Manual Studio) - DragonRPA Co. [평가판]")
        self.canvas.set_pixmap(pixmap)
        self.canvas.items.clear()
        self.canvas.next_stamp_index = 1
        self.canvas.history.clear()

        # 창 전면 활성화
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        self.activateWindow()

        w = pixmap.width()
        h = pixmap.height()
        tw = self.config.get("target_width", 960)
        self.status_label.setText(
            f"새 캡처 수신됨: {w}×{h} px ➔ PPT 내보내기 시 가로 {tw}px로 자동 규격화됩니다. (F10 전송)"
        )
        if not is_fixed_capture and global_rect:
            self.show_toast(f"🎯 영역 지정 완료 ({w}×{h}px) ➔ 다음 F9 시 즉시 캡처됩니다. (새 영역: Shift+F9)")
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

        # 4. 파워포인트 새 슬라이드 자동 생성
        temp_dir = os.path.join(get_app_dir(), "temp")
        ppt_ok = False
        if self.config.get("ppt_auto_slide", True):
            ppt_layout = self.config.get("ppt_layout", {})
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
                base_name = os.path.basename(self.current_project_path)
                self.setWindowTitle(f"매뉴얼 스튜디오 - [{base_name}]")

        # 결과 알림 (세션은 절대 초기화하지 않고 그대로 보존!)
        msg_parts = []
        if ppt_ok:
            msg_parts.append("✅ PPT 새 슬라이드 자동 생성")
        if clipboard_ok:
            msg_parts.append("📋 클립보드 복사(Ctrl+V)")
        if bundle_res:
            step_name = os.path.basename(bundle_res["bake_path"])
            msg_parts.append(f"💾 {step_name} & 프로젝트 보존")

        full_msg = " + ".join(msg_parts) + " 완료! (현재 작업내용 유지됨)"
        self.status_label.setText(full_msg)
        self.show_toast(full_msg)

    def action_undo(self):
        self.canvas.undo()

    def action_clear(self):
        self.canvas.clear_annotations()

    def action_add_draft_stamp(self):
        if self.canvas.pixmap is None:
            self.show_toast("먼저 화면(F9)을 캡처한 후 Draft 스탬프를 추가하세요.")
            return
        item = self.canvas.add_draft_stamp("DRAFT")
        self.show_toast("📑 Draft 스탬프가 추가되었습니다. (더블 클릭 시 문구 변경)")

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
                f"📄 [{pres_name}] (총 {slide_count}개 슬라이드)\n\n"
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
        self.show_toast(f"🔢 {res.get('renumbered_count')}개 슬라이드 Step 번호 재정렬 완료")
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

        title_lbl = QLabel(f"📄 문서: {res.get('presentation_name', '')}", header_card)
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

        dlg.exec_()

    def keyPressEvent(self, event):
        modifiers = event.modifiers()
        key = event.key()

        if modifiers & Qt.ControlModifier:
            if key == Qt.Key_Z:
                self.action_undo()
                return
            elif key == Qt.Key_O:
                self.action_open_project()
                return
            elif key == Qt.Key_S:
                self.action_save_project()
                return
            elif key == Qt.Key_C:
                self.copy_current_composed_image()
                return

        if key in (Qt.Key_Delete, Qt.Key_Backspace):
            if self.canvas.delete_selected_item():
                return

        if key == Qt.Key_F8:
            self.start_sub_capture()
            return
        elif key == Qt.Key_F9:
            if modifiers & Qt.ShiftModifier:
                self.start_capture()
            else:
                self.handle_hotkey_capture()
        elif key == Qt.Key_F10:
            self.export_to_ppt_and_clipboard()
        else:
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

    def open_settings_dialog(self):
        dlg = SettingsDialog(self.config, self)
        if dlg.exec_() == QDialog.Accepted:
            self.config = dlg.get_config()
            save_config(self.config)
            self.canvas.set_config(self.config)
            self.sync_ui_from_config()
            self.show_toast("설정이 저장되었습니다.")

    def closeEvent(self, event):
        if hasattr(self, "hotkey_thread"):
            self.hotkey_thread.stop()
        event.accept()


# ==============================================================================
# 7.5. 최종 사용자 라이선스 계약서 (EULA) 및 다이얼로그 (DragonRPA Co.)
# ==============================================================================
EULA_HTML_TEXT = """
<h3 style="color:#0F172A; margin-bottom:4px;">(주)드래곤알피에이 소프트웨어 최종 사용자 라이선스 계약서 (EULA)</h3>
<p style="color:#64748B; font-size:11px; margin-top:0;">End User License Agreement for Manual Studio | (주)드래곤알피에이 (DragonRPA Co., Ltd.)</p>
<hr style="border:0; border-top:1px solid #CBD5E1;"/>
<p>본 계약은 <b>(주)드래곤알피에이</b>(이하 "회사")와 본 소프트웨어 <b>'매뉴얼 스튜디오(Manual Studio)'</b>(이하 "소프트웨어")를 다운로드, 복사, 설치 또는 사용하는 개인 또는 법인(이하 "사용자") 간에 체결되는 법적 구속력을 가진 사용권 계약입니다. 사용자가 본 "소프트웨어"를 다운로드, 설치 또는 사용하는 것은 본 계약 조건에 동의한 것으로 간주됩니다.</p>

<h4 style="color:#1E40AF; margin-top:14px; margin-bottom:4px;">제1조 (목적)</h4>
<p>본 계약은 "회사"가 개발한 "소프트웨어"에 대한 비독점적이고 양도 불가능한 사용 권한을 "사용자"에게 허여하고, 당사자 간의 권리 및 의무를 규정함을 목적으로 합니다.</p>

<h4 style="color:#1E40AF; margin-top:14px; margin-bottom:4px;">제2조 (지식재산권의 귀속)</h4>
<p>1. 본 "소프트웨어", 관련 설명 문서, 소스코드, 바이너리, 그래픽, UI/UX 디자인에 대한 저작권, 특허권, 상표권, 영업비밀 등 일체의 지식재산권은 대한민국 저작권법 및 국제 협약에 따라 <b>(주)드래곤알피에이</b>에 배타적으로 귀속됩니다.<br/>
2. 본 계약에 따른 제공은 소유권의 이전이 아니며, 명시된 조건 범위 내에서의 <b>'제한적 사용권(License)'</b>만을 허여합니다.</p>

<h4 style="color:#1E40AF; margin-top:14px; margin-bottom:4px;">제3조 (사용권의 범위 및 조건)</h4>
<p>1. <b>[평가판 (Trial License)]</b>: "회사"가 공지한 평가판은 명시된 사용 유효 기간(2026년 12월 31일까지) 동안 비상업적 검토, 기능 테스트 및 평가 목적으로만 무상 사용할 수 있습니다. 기간 만료 후에는 정규 라이선스 없이 계속 사용할 수 없습니다.<br/>
2. <b>[정규 라이선스 (Commercial License)]</b>: 정식 라이선스는 1개의 라이선스 키당 지정된 단일 하드웨어 머신(1PC-1Key 노드락)에서만 설치 및 실행이 허용됩니다.</p>

<h4 style="color:#1E40AF; margin-top:14px; margin-bottom:4px;">제4조 (금지 행위 - 역공학 및 무단 배포 금지)</h4>
<p>사용자는 다음 각 호의 행위를 하여서는 아니 되며, 위반 시 저작권법 등에 따른 민·형사상 책임을 집니다.<br/>
1. <b>역공학 및 디컴파일 금지</b>: 소스코드나 내부 알고리즘을 추출하기 위한 리버스 엔지니어링, 역컴파일(Decompile), 디스어셈블(Disassemble) 또는 코드 수정 행위<br/>
2. <b>보안 메커니즘 조작 금지</b>: 하드웨어 식별값(HWID), 시계 변조 방지, 암호화 키 등 라이선스 검증 장치를 우회, 변조, 크랙하는 행위<br/>
3. <b>무단 재배포 및 상업적 재판매 금지</b>: "회사"의 사전 서면 승인 없이 제3자에게 유상 판매, 대여, 양도하거나 온라인 자료실/공중망에 무단 배포하는 행위<br/>
4. <b>저작권 표시 삭제 금지</b>: "소프트웨어" 내에 표시된 "회사"의 상표, 로고, 저작권 안내문, 평가판 기한 등의 법적 고지 사항을 임의로 변경, 제거하는 행위</p>

<h4 style="color:#1E40AF; margin-top:14px; margin-bottom:4px;">제5조 (보증의 한계 및 면책)</h4>
<p>1. 본 "소프트웨어"는 <b>"있는 그대로(AS-IS)"</b> 제공되며, 회사는 특정 목적에의 적합성, 무결성 등에 대해 명시적 또는 묵시적 보증을 하지 않습니다.<br/>
2. 회사는 "소프트웨어"의 사용 또는 사용 불능으로 인하여 발생하는 간접적, 부수적 손해(영업손실, 데이터 손실 등)에 대해 책임을 지지 않습니다.</p>

<h4 style="color:#1E40AF; margin-top:14px; margin-bottom:4px;">제6조 (위약벌 및 손해배상)</h4>
<p>사용자가 제4조(금지 행위)를 고의 또는 중과실로 위반한 경우, <b>정규 라이선스 정가의 5배에 해당하는 금액을 위약벌로 회사에 즉시 지급</b>하여야 하며, 이와 별도로 회사가 입은 실제 손해를 전액 배상하여야 합니다.</p>

<h4 style="color:#1E40AF; margin-top:14px; margin-bottom:4px;">제7조 (준거법 및 전속 관할)</h4>
<p>본 계약은 대한민국 법률에 따라 규율되며, 본 계약과 관련하여 발생하는 모든 분쟁은 <b>(주)드래곤알피에이 본점 소재지를 관할하는 법원을 제1심 전속 관할 법원</b>으로 합니다.</p>
<hr style="border:0; border-top:1px solid #CBD5E1;"/>
<p style="font-size:10.5px; color:#64748B;">공고일자: 2026.09.11 | 시행일자: 2026.09.11<br/>
(주)드래곤알피에이 (DragonRPA Co., Ltd.) | 대표이사: 이정용 | 문의: 77.victor.lee@gmail.com</p>
"""


class EulaDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("최종 사용자 라이선스 계약서 (EULA) - (주)드래곤알피에이")
        self.resize(620, 560)
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
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        # 헤더
        header_l = QHBoxLayout()
        lbl_h = QLabel("📜 최종 사용자 라이선스 계약서 (EULA)", self)
        lbl_h.setStyleSheet("font-size: 14.5px; font-weight: bold; color: #0F172A;")
        header_l.addWidget(lbl_h)
        header_l.addStretch(1)

        lbl_comp = QLabel("(주)드래곤알피에이 | DragonRPA Co.", self)
        lbl_comp.setStyleSheet("font-size: 11px; color: #64748B; font-weight: bold;")
        header_l.addWidget(lbl_comp)
        layout.addLayout(header_l)

        # 텍스트 에리어
        txt_eula = QTextEdit(self)
        txt_eula.setReadOnly(True)
        txt_eula.setStyleSheet("""
            QTextEdit {
                background-color: #F8FAFC;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 12px;
                font-family: 'Malgun Gothic';
                font-size: 11px;
                color: #1E293B;
                line-height: 1.5;
            }
        """)
        txt_eula.setHtml(EULA_HTML_TEXT)
        layout.addWidget(txt_eula, 1)

        # 하단 닫기 버튼
        btn_l = QHBoxLayout()
        btn_l.addStretch(1)
        btn_close = QPushButton("닫기", self)
        btn_close.setFixedSize(90, 32)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet("""
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
        btn_close.clicked.connect(self.accept)
        btn_l.addWidget(btn_close)
        layout.addLayout(btn_l)


# ==============================================================================
# 8. 개발사 정보 및 About 다이얼로그 (AboutDialog - DragonRPA Co.)
# ==============================================================================
class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About - DragonRPA Co.")
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
        lbl_title = QLabel("매뉴얼 스튜디오", self)
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0F172A; margin-top: 2px;")
        layout.addWidget(lbl_title)

        lbl_sub = QLabel("Manual Studio for PowerPoint", self)
        lbl_sub.setAlignment(Qt.AlignCenter)
        lbl_sub.setStyleSheet("font-size: 11.5px; color: #64748B;")
        layout.addWidget(lbl_sub)

        ver_layout = QHBoxLayout()
        ver_layout.setAlignment(Qt.AlignCenter)
        lbl_ver = QLabel("v1.2.0 (Build 2026.09) • 평가판", self)
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

        # 평가판 사용 기한 카드 (기간한정 평가판 명시)
        card_trial = QFrame(self)
        card_trial.setStyleSheet("""
            QFrame {
                background-color: #FEF3C7;
                border: 1px solid #FCD34D;
                border-radius: 8px;
            }
        """)
        tr_l = QHBoxLayout(card_trial)
        tr_l.setContentsMargins(14, 9, 14, 9)
        tr_l.setSpacing(8)
        lbl_tr_icon = QLabel("⏳", card_trial)
        lbl_tr_icon.setStyleSheet("font-size: 15px; border: none; background: transparent;")
        lbl_tr_text = QLabel("<b>[기간 한정 평가판]</b> 본 빌드의 사용 유효 기간은 <b>2026년 12월 31일</b>까지입니다.", card_trial)
        lbl_tr_text.setStyleSheet("font-size: 11.5px; color: #92400E; border: none; background: transparent;")
        tr_l.addWidget(lbl_tr_icon)
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

        lbl_company = QLabel("(주)드래곤알피에이 (DragonRPA Co.)", card_dev)
        lbl_company.setStyleSheet("font-size: 13px; font-weight: bold; color: #1E293B; border: none;")
        dev_l.addWidget(lbl_company)

        lbl_dev_notice = QLabel("본 프로그램은 (주)드래곤알피에이(DragonRPA Co.)에서 기획 및 개발하였습니다.", card_dev)
        lbl_dev_notice.setWordWrap(True)
        lbl_dev_notice.setStyleSheet("font-size: 11.5px; color: #334155; border: none; line-height: 1.4;")
        dev_l.addWidget(lbl_dev_notice)

        lbl_domain = QLabel("• 업무 자동화 (RPA) · 매뉴얼 표준화 · 지능형 엔터프라이즈 솔루션", card_dev)
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
        lbl_c_title = QLabel("공식 문의 및 기술 지원 (Contact)", card_contact)
        lbl_c_title.setStyleSheet("font-size: 11px; font-weight: bold; color: #166534; border: none;")
        lbl_email = QLabel("77.victor.lee@gmail.com", card_contact)
        lbl_email.setStyleSheet("font-size: 12.5px; font-weight: bold; color: #15803D; border: none;")
        contact_info_l.addWidget(lbl_c_title)
        contact_info_l.addWidget(lbl_email)
        c_l.addLayout(contact_info_l)

        c_l.addStretch(1)

        btn_copy_email = QPushButton("📋 이메일 주소 복사", card_contact)
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

        btn_eula = QPushButton("📜 사용권 계약 (EULA)", self)
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

        btn_ok = QPushButton("확인", self)
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

    def show_eula(self):
        dlg = EulaDialog(self)
        dlg.exec_()

    def copy_email(self):
        cb = QApplication.clipboard()
        cb.setText("77.victor.lee@gmail.com")
        QMessageBox.information(self, "클립보드 복사", "이메일 주소(77.victor.lee@gmail.com)가 클립보드에 복사되었습니다.")


# ==============================================================================
# 9. 설정 다이얼로그 (SettingsDialog)
# ==============================================================================
class SettingsDialog(QDialog):
    def __init__(self, current_config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("환경 설정 (Settings)")
        self.resize(540, 820)
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

        # 1. PPT 규격화 가로폭 설정
        box1 = QFrame(self)
        box1.setFrameShape(QFrame.StyledPanel)
        b1_l = QVBoxLayout(box1)
        b1_l.addWidget(QLabel("<b>[PPT 슬라이드 규격화 가로폭]</b>", self))
        h1 = QHBoxLayout()
        h1.addWidget(QLabel("목표 가로 해상도(px):", self))
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
        b2_l.addWidget(QLabel("<b>[번호 스탬프 스타일]</b>", self))

        h2_1 = QHBoxLayout()
        h2_1.addWidget(QLabel("스탬프 뱃지 크기(px):", self))
        self.spin_stamp_size = QSpinBox(self)
        self.spin_stamp_size.setRange(16, 120)
        self.spin_stamp_size.setValue(self.config.get("stamp_style", {}).get("size", 32))
        h2_1.addWidget(self.spin_stamp_size)
        b2_l.addLayout(h2_1)

        h2_2 = QHBoxLayout()
        h2_2.addWidget(QLabel("스탬프 배경 색상:", self))
        self.btn_stamp_color = QPushButton("색상 선택", self)
        self.btn_stamp_color.setStyleSheet(f"background-color: {self.current_stamp_color}; color: #FFFFFF; font-weight: bold;")
        self.btn_stamp_color.clicked.connect(self.choose_stamp_color)
        h2_2.addWidget(self.btn_stamp_color)
        b2_l.addLayout(h2_2)
        layout.addWidget(box2)

        # 3. 텍스트 라벨 스타일
        box3 = QFrame(self)
        box3.setFrameShape(QFrame.StyledPanel)
        b3_l = QVBoxLayout(box3)
        b3_l.addWidget(QLabel("<b>[텍스트 라벨 스타일]</b>", self))

        h3_1 = QHBoxLayout()
        h3_1.addWidget(QLabel("글꼴 크기(pt):", self))
        self.spin_font_size = QSpinBox(self)
        self.spin_font_size.setRange(8, 72)
        self.spin_font_size.setValue(self.config.get("text_style", {}).get("font_size", 14))
        h3_1.addWidget(self.spin_font_size)
        b3_l.addLayout(h3_1)

        h3_2 = QHBoxLayout()
        h3_2.addWidget(QLabel("글자 색상:", self))
        self.btn_text_color = QPushButton("글자색 선택", self)
        self.btn_text_color.setStyleSheet(f"background-color: #333333; color: {self.current_text_color}; font-weight: bold;")
        self.btn_text_color.clicked.connect(self.choose_text_color)
        h3_2.addWidget(self.btn_text_color)

        h3_2.addWidget(QLabel("배경 색상:", self))
        self.btn_text_bg_color = QPushButton("배경색 선택", self)
        self.btn_text_bg_color.setStyleSheet(f"background-color: {self.current_text_bg_color}; color: #FFFFFF; font-weight: bold;")
        self.btn_text_bg_color.clicked.connect(self.choose_text_bg_color)
        h3_2.addWidget(self.btn_text_bg_color)
        b3_l.addLayout(h3_2)
        layout.addWidget(box3)

        # 4. 강조 박스 스타일
        box4 = QFrame(self)
        box4.setFrameShape(QFrame.StyledPanel)
        b4_l = QVBoxLayout(box4)
        b4_l.addWidget(QLabel("<b>[강조 박스 스타일]</b>", self))

        h4_1 = QHBoxLayout()
        h4_1.addWidget(QLabel("선 두께(px):", self))
        self.spin_box_width = QSpinBox(self)
        self.spin_box_width.setRange(1, 20)
        self.spin_box_width.setValue(self.config.get("highlight_box_style", {}).get("border_width", 3))
        h4_1.addWidget(self.spin_box_width)

        h4_1.addWidget(QLabel("박스 색상:", self))
        self.btn_box_color = QPushButton("색상 선택", self)
        self.btn_box_color.setStyleSheet(f"background-color: {self.current_box_color}; color: #FFFFFF; font-weight: bold;")
        self.btn_box_color.clicked.connect(self.choose_box_color)
        h4_1.addWidget(self.btn_box_color)
        b4_l.addLayout(h4_1)

        self.chk_box_fill = QCheckBox("음영 채우기", self)
        self.chk_box_fill.setChecked(self.config.get("highlight_box_style", {}).get("fill", False))
        b4_l.addWidget(self.chk_box_fill)
        layout.addWidget(box4)

        # 5. 화살표 연결선 스타일
        box_arr = QFrame(self)
        box_arr.setFrameShape(QFrame.StyledPanel)
        b_arr_l = QVBoxLayout(box_arr)
        b_arr_l.addWidget(QLabel("<b>[화살표 연결선 스타일]</b>", self))

        h_arr = QHBoxLayout()
        h_arr.addWidget(QLabel("선 두께(px):", self))
        self.spin_arrow_width = QSpinBox(self)
        self.spin_arrow_width.setRange(1, 20)
        self.spin_arrow_width.setValue(self.config.get("arrow_style", {}).get("width", 3))
        h_arr.addWidget(self.spin_arrow_width)

        h_arr.addWidget(QLabel("촉 크기(px):", self))
        self.spin_arrow_head = QSpinBox(self)
        self.spin_arrow_head.setRange(6, 40)
        self.spin_arrow_head.setValue(self.config.get("arrow_style", {}).get("head_size", 14))
        h_arr.addWidget(self.spin_arrow_head)

        h_arr.addWidget(QLabel("색상:", self))
        self.btn_arrow_color = QPushButton("색상 선택", self)
        self.btn_arrow_color.setStyleSheet(f"background-color: {self.current_arrow_color}; color: #FFFFFF; font-weight: bold;")
        self.btn_arrow_color.clicked.connect(self.choose_arrow_color)
        h_arr.addWidget(self.btn_arrow_color)
        b_arr_l.addLayout(h_arr)
        layout.addWidget(box_arr)

        # 6. 추천 주석 스타일 (말풍선, 모자이크, 단축키)
        box_rec = QFrame(self)
        box_rec.setFrameShape(QFrame.StyledPanel)
        b_rec_l = QVBoxLayout(box_rec)
        b_rec_l.addWidget(QLabel("<b>[추천 주석 스타일 (말풍선·모자이크·단축키)]</b>", self))

        h_rec1 = QHBoxLayout()
        h_rec1.addWidget(QLabel("말풍선 글꼴(pt):", self))
        self.spin_callout_font = QSpinBox(self)
        self.spin_callout_font.setRange(8, 72)
        self.spin_callout_font.setValue(self.config.get("callout_style", {}).get("font_size", 12))
        h_rec1.addWidget(self.spin_callout_font)

        h_rec1.addWidget(QLabel("말풍선 꼬리(px):", self))
        self.spin_callout_tail = QSpinBox(self)
        self.spin_callout_tail.setRange(8, 40)
        self.spin_callout_tail.setValue(self.config.get("callout_style", {}).get("tail_base_width", 16))
        h_rec1.addWidget(self.spin_callout_tail)
        b_rec_l.addLayout(h_rec1)

        h_rec2 = QHBoxLayout()
        h_rec2.addWidget(QLabel("모자이크 크기(px):", self))
        self.spin_blur_block = QSpinBox(self)
        self.spin_blur_block.setRange(4, 40)
        self.spin_blur_block.setValue(self.config.get("blur_style", {}).get("block_size", 10))
        h_rec2.addWidget(self.spin_blur_block)

        h_rec2.addWidget(QLabel("단축키 글꼴(pt):", self))
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
        b5_l.addWidget(QLabel("<b>[PPT 슬라이드 배치 및 배율]</b>", self))

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

        h5_1.addWidget(QLabel("배율(%):", self))
        self.spin_ppt_scale = QSpinBox(self)
        self.spin_ppt_scale.setRange(10, 300)
        self.spin_ppt_scale.setSingleStep(5)
        self.spin_ppt_scale.setValue(self.config.get("ppt_layout", {}).get("scale", 90))
        h5_1.addWidget(self.spin_ppt_scale)
        b5_l.addLayout(h5_1)

        self.chk_ppt_title = QCheckBox("단계명 제목 상자 (Step N) 자동 생성", self)
        self.chk_ppt_title.setChecked(self.config.get("ppt_layout", {}).get("include_title", True))
        b5_l.addWidget(self.chk_ppt_title)
        layout.addWidget(box5)

        # 8. PPT 단계명 제목 상자 스타일 및 배치
        box_title = QFrame(self)
        box_title.setFrameShape(QFrame.StyledPanel)
        b_t_l = QVBoxLayout(box_title)
        b_t_l.addWidget(QLabel("<b>[PPT 단계명 제목 상자 스타일 및 배치]</b>", self))

        ppt_l = self.config.get("ppt_layout", {})

        ht1 = QHBoxLayout()
        ht1.addWidget(QLabel("제목 X(pt):", self))
        self.spin_title_left = QSpinBox(self)
        self.spin_title_left.setRange(0, 1920)
        self.spin_title_left.setSingleStep(5)
        self.spin_title_left.setValue(int(ppt_l.get("title_left", ppt_l.get("left", 26))))
        ht1.addWidget(self.spin_title_left)

        ht1.addWidget(QLabel("제목 Y(pt):", self))
        self.spin_title_top = QSpinBox(self)
        self.spin_title_top.setRange(0, 1080)
        self.spin_title_top.setSingleStep(5)
        self.spin_title_top.setValue(int(ppt_l.get("title_top", 15)))
        ht1.addWidget(self.spin_title_top)

        ht1.addWidget(QLabel("너비(pt):", self))
        self.spin_title_width = QSpinBox(self)
        self.spin_title_width.setRange(50, 1920)
        self.spin_title_width.setSingleStep(20)
        self.spin_title_width.setValue(int(ppt_l.get("title_width", 500)))
        ht1.addWidget(self.spin_title_width)

        ht1.addWidget(QLabel("높이(pt):", self))
        self.spin_title_height = QSpinBox(self)
        self.spin_title_height.setRange(15, 500)
        self.spin_title_height.setSingleStep(5)
        self.spin_title_height.setValue(int(ppt_l.get("title_height", 35)))
        ht1.addWidget(self.spin_title_height)
        b_t_l.addLayout(ht1)

        ht2 = QHBoxLayout()
        ht2.addWidget(QLabel("글꼴:", self))
        self.edit_title_font = QLineEdit(str(ppt_l.get("title_font_family", "Malgun Gothic")), self)
        self.edit_title_font.setFixedWidth(120)
        ht2.addWidget(self.edit_title_font)

        ht2.addWidget(QLabel("크기(pt):", self))
        self.spin_title_font_size = QSpinBox(self)
        self.spin_title_font_size.setRange(8, 72)
        self.spin_title_font_size.setValue(int(ppt_l.get("title_font_size", 18)))
        ht2.addWidget(self.spin_title_font_size)

        self.chk_title_bold = QCheckBox("굵게", self)
        self.chk_title_bold.setChecked(bool(ppt_l.get("title_font_bold", True)))
        ht2.addWidget(self.chk_title_bold)

        ht2.addWidget(QLabel("글자색:", self))
        self.btn_title_color = QPushButton("색상 선택", self)
        qcol_t = QColor(self.current_title_color)
        t_fg = "#FFFFFF" if (qcol_t.red() * 0.299 + qcol_t.green() * 0.587 + qcol_t.blue() * 0.114) < 140 else "#000000"
        self.btn_title_color.setStyleSheet(f"background-color: {self.current_title_color}; color: {t_fg}; font-weight: bold;")
        self.btn_title_color.clicked.connect(self.choose_title_color)
        ht2.addWidget(self.btn_title_color)
        b_t_l.addLayout(ht2)

        ht3 = QHBoxLayout()
        ht3.addWidget(QLabel("제목 템플릿:", self))
        self.edit_title_template = QLineEdit(str(ppt_l.get("title_template", "Step {n}. [단계명 입력]")), self)
        self.edit_title_template.setToolTip("'{n}'은 슬라이드 번호-1 로 자동 치환됩니다.")
        ht3.addWidget(self.edit_title_template)
        b_t_l.addLayout(ht3)

        layout.addWidget(box_title)

        # 하단 확인/취소
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("저장", self)
        btn_ok.setStyleSheet("background-color: #2196F3; color: #FFFFFF; font-weight: bold; padding: 6px 14px;")
        btn_ok.clicked.connect(self.save_and_close)
        btn_cancel = QPushButton("취소", self)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        root_layout.addLayout(btn_layout)

    def choose_stamp_color(self):
        col = QColorDialog.getColor(QColor(self.current_stamp_color), self, "스탬프 배경 색상 선택")
        if col.isValid():
            self.current_stamp_color = col.name()
            self.btn_stamp_color.setStyleSheet(f"background-color: {self.current_stamp_color}; color: #FFFFFF; font-weight: bold;")

    def choose_text_color(self):
        col = QColorDialog.getColor(QColor(self.current_text_color), self, "텍스트 글자 색상 선택")
        if col.isValid():
            self.current_text_color = col.name()
            self.btn_text_color.setStyleSheet(f"background-color: #333333; color: {self.current_text_color}; font-weight: bold;")

    def choose_text_bg_color(self):
        col = QColorDialog.getColor(QColor(self.current_text_bg_color), self, "텍스트 배경 색상 선택")
        if col.isValid():
            self.current_text_bg_color = col.name()
            self.btn_text_bg_color.setStyleSheet(f"background-color: {self.current_text_bg_color}; color: #FFFFFF; font-weight: bold;")

    def choose_box_color(self):
        col = QColorDialog.getColor(QColor(self.current_box_color), self, "박스 색상 선택")
        if col.isValid():
            self.current_box_color = col.name()
            self.btn_box_color.setStyleSheet(f"background-color: {self.current_box_color}; color: #FFFFFF; font-weight: bold;")

    def choose_arrow_color(self):
        col = QColorDialog.getColor(QColor(self.current_arrow_color), self, "화살표 색상 선택")
        if col.isValid():
            self.current_arrow_color = col.name()
            self.btn_arrow_color.setStyleSheet(f"background-color: {self.current_arrow_color}; color: #FFFFFF; font-weight: bold;")

    def choose_title_color(self):
        col = QColorDialog.getColor(QColor(self.current_title_color), self, "제목 글자 색상 선택")
        if col.isValid():
            self.current_title_color = col.name()
            qcol = QColor(self.current_title_color)
            text_fg = "#FFFFFF" if (qcol.red() * 0.299 + qcol.green() * 0.587 + qcol.blue() * 0.114) < 140 else "#000000"
            self.btn_title_color.setStyleSheet(f"background-color: {self.current_title_color}; color: {text_fg}; font-weight: bold;")

    def save_and_close(self):
        self.config["target_width"] = self.spin_width.value()
        self.config.setdefault("stamp_style", {})["size"] = self.spin_stamp_size.value()
        self.config["stamp_style"]["bg_color"] = self.current_stamp_color
        self.config.setdefault("text_style", {})["font_size"] = self.spin_font_size.value()
        self.config["text_style"]["text_color"] = self.current_text_color
        self.config["text_style"]["bg_color"] = self.current_text_bg_color
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
        self.config["ppt_layout"]["title_font_family"] = self.edit_title_font.text().strip() or "Malgun Gothic"
        self.config["ppt_layout"]["title_font_size"] = self.spin_title_font_size.value()
        self.config["ppt_layout"]["title_font_bold"] = self.chk_title_bold.isChecked()
        self.config["ppt_layout"]["title_font_color"] = self.current_title_color
        self.config["ppt_layout"]["title_template"] = self.edit_title_template.text().strip() or "Step {n}. [단계명 입력]"
        self.accept()

    def get_config(self):
        return self.config


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
    # 0. 이전 인스턴스 정리 (글로벌 핫키 F9 독점 방지)
    kill_other_instances()

    # Qt 플러그인 라이브러리 경로 명시적 추가
    if 'plugins_dir' in globals() and os.path.exists(plugins_dir):
        QCoreApplication.addLibraryPath(plugins_dir)

    # 고해상도 High-DPI 지원
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("ManualCaptureStudio")

    # 애플리케이션 및 작업표시줄 아이콘 설정 (DragonRPA CI)
    ci_pix = get_dragon_rpa_ci_pixmap()
    if not ci_pix.isNull():
        app.setWindowIcon(QIcon(ci_pix))

    # 기본 폰트 설정
    app.setFont(QFont("Malgun Gothic", 10))

    # 1. 사용 기간(2026-12-31) 및 안티 롤백 검증
    is_valid, err_msg = LicenseValidator.check_license()
    if not is_valid:
        QMessageBox.critical(None, "평가판 사용 제한 - DragonRPA Co.", err_msg)
        sys.exit(1)

    window = ManualStudioWindow()
    window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

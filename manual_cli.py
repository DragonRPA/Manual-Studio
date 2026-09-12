"""
================================================================================
DragonRPA Manual Studio - Headless CLI Automation Engine
================================================================================
Enables AI Agents, CLI scripts, and background workers to capture screens,
apply visual annotations, render .mcs.json project files, and export to
PowerPoint / Google Slides without launching the GUI window.
================================================================================
"""

import sys
import os
import json
import argparse
from datetime import datetime
from PIL import Image

from PySide6.QtCore import Qt, QPointF, QRect, QRectF
from PySide6.QtGui import QPainter, QColor, QPixmap, QImage, QGuiApplication
from PySide6.QtWidgets import QApplication

from manual_capture_studio import (
    StampItem, HighlightBoxItem, ArrowItem, CalloutItem,
    TextLabelItem, BlurMosaicItem, HotkeyBadgeItem,
    ProjectManager, ExportEngine, DEFAULT_CONFIG, APP_VERSION,
    item_from_dict
)
from license_engine import LicenseEngine


def get_or_create_app() -> QApplication:
    """헤드리스 Qt 애플리케이션 싱글톤 인스턴스 획득"""
    app = QApplication.instance()
    if app is None:
        # GUI 창 없이 백그라운드 렌더링 및 모니터 캡처 수행
        app = QApplication([sys.argv[0]])
        app.setApplicationName("ManualStudioCLI")
    return app


def load_user_config() -> dict:
    """config.json 로드 또는 기본 설정 반환"""
    cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                merged = DEFAULT_CONFIG.copy()
                merged.update(cfg)
                return merged
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def cli_status() -> dict:
    """애플리케이션 상태, 버전, 모니터 정보 및 설정 조회"""
    app = get_or_create_app()
    screens_info = []
    primary = QGuiApplication.primaryScreen()
    for i, s in enumerate(QGuiApplication.screens()):
        g = s.geometry()
        screens_info.append({
            "index": i,
            "name": s.name(),
            "geometry": [g.x(), g.y(), g.width(), g.height()],
            "is_primary": (s == primary)
        })

    cfg = load_user_config()
    is_lic = LicenseEngine.is_licensed() if hasattr(LicenseEngine, "is_licensed") else True

    return {
        "status": "ok",
        "app_name": "Manual Studio",
        "version": APP_VERSION,
        "is_licensed": is_lic,
        "screens": screens_info,
        "fixed_rect": cfg.get("fixed_rect", {}),
        "export_target": cfg.get("export_target", "powerpoint"),
        "timestamp": datetime.now().isoformat()
    }


def cli_capture(rect: str = None, monitor: int = 0, fixed: bool = False, output: str = None) -> dict:
    """헤드리스 화면 캡처 수행 및 PNG 저장"""
    app = get_or_create_app()
    screens = QGuiApplication.screens()
    if not screens:
        return {"status": "error", "message": "No display screens detected"}

    target_screen = screens[0]
    if 0 <= monitor < len(screens):
        target_screen = screens[monitor]

    cfg = load_user_config()
    cap_x, cap_y, cap_w, cap_h = 0, 0, 0, 0

    if fixed:
        f_rect = cfg.get("fixed_rect", {"x": 100, "y": 100, "width": 960, "height": 540})
        cap_x = int(f_rect.get("x", 100))
        cap_y = int(f_rect.get("y", 100))
        cap_w = int(f_rect.get("width", 960))
        cap_h = int(f_rect.get("height", 540))
    elif rect:
        parts = [int(p.strip()) for p in rect.split(",")]
        if len(parts) != 4:
            return {"status": "error", "message": "Invalid rect format. Expected 'x,y,w,h'"}
        cap_x, cap_y, cap_w, cap_h = parts
    else:
        # 모니터 전체 영역 캡처
        geom = target_screen.geometry()
        cap_x, cap_y, cap_w, cap_h = geom.x(), geom.y(), geom.width(), geom.height()

    # 스크린 캡처 실행 (QScreen.grabWindow)
    pixmap = target_screen.grabWindow(0, cap_x, cap_y, cap_w, cap_h)
    if pixmap.isNull():
        return {"status": "error", "message": "Failed to capture screen image"}

    # 저장 경로 결정
    if not output:
        save_dir = cfg.get("save_directory", "captures")
        os.makedirs(save_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = os.path.join(save_dir, f"capture_{ts}.png")
    else:
        out_dir = os.path.dirname(os.path.abspath(output))
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

    success = pixmap.save(output, "PNG")
    if not success:
        return {"status": "error", "message": f"Failed to save captured image to {output}"}

    return {
        "status": "ok",
        "output_file": os.path.abspath(output),
        "width": pixmap.width(),
        "height": pixmap.height(),
        "rect": [cap_x, cap_y, cap_w, cap_h]
    }


def parse_item_specs(stamps=None, boxes=None, arrows=None, callouts=None, texts=None, raw_items=None) -> list:
    """CLI 인자 및 JSON 스펙을 주석 Item 객체 목록으로 파싱"""
    items = []
    cfg = load_user_config()

    # 1. Stamps: "index:x,y[:bg_color:size]"
    if stamps:
        for s in stamps:
            parts = s.split(":")
            idx = int(parts[0])
            coords = [float(c) for c in parts[1].split(",")]
            style = cfg.get("stamp_style", {}).copy()
            if len(parts) > 2 and parts[2]:
                style["bg_color"] = parts[2]
            if len(parts) > 3 and parts[3]:
                style["size"] = int(parts[3])
            items.append(StampItem(idx, coords[0], coords[1], style))

    # 2. Boxes: "x,y,w,h[:color:width:fill]"
    if boxes:
        for b in boxes:
            parts = b.split(":")
            rect_vals = [int(v) for v in parts[0].split(",")]
            style = cfg.get("highlight_box_style", {}).copy()
            if len(parts) > 1 and parts[1]:
                style["color"] = parts[1]
            if len(parts) > 2 and parts[2]:
                style["border_width"] = int(parts[2])
            if len(parts) > 3 and parts[3].lower() in ("true", "1", "fill"):
                style["fill"] = True
            items.append(HighlightBoxItem(QRect(rect_vals[0], rect_vals[1], rect_vals[2], rect_vals[3]), style))

    # 3. Arrows: "x1,y1,x2,y2[:color:width]"
    if arrows:
        for a in arrows:
            parts = a.split(":")
            coords = [float(v) for v in parts[0].split(",")]
            style = cfg.get("arrow_style", {}).copy()
            if len(parts) > 1 and parts[1]:
                style["color"] = parts[1]
            if len(parts) > 2 and parts[2]:
                style["width"] = int(parts[2])
            items.append(ArrowItem(QPointF(coords[0], coords[1]), QPointF(coords[2], coords[3]), style))

    # 4. Callouts: "text:box_x,box_y,box_w,box_h:tail_x,tail_y[:border_color:font_size]"
    if callouts:
        for c in callouts:
            parts = c.split(":")
            text = parts[0]
            box_coords = [float(v) for v in parts[1].split(",")]
            tail_coords = [float(v) for v in parts[2].split(",")]
            style = cfg.get("callout_style", {}).copy()
            if len(parts) > 3 and parts[3]:
                style["border_color"] = parts[3]
            if len(parts) > 4 and parts[4]:
                style["font_size"] = int(parts[4])
            items.append(CalloutItem(
                text,
                QRectF(box_coords[0], box_coords[1], box_coords[2], box_coords[3]),
                QPointF(tail_coords[0], tail_coords[1]),
                style
            ))

    # 5. Texts: "text:x,y[:text_color:font_size:bg_color]"
    if texts:
        for t in texts:
            parts = t.split(":")
            text = parts[0]
            coords = [float(v) for v in parts[1].split(",")]
            style = cfg.get("text_style", {}).copy()
            if len(parts) > 2 and parts[2]:
                style["text_color"] = parts[2]
            if len(parts) > 3 and parts[3]:
                style["font_size"] = int(parts[3])
            if len(parts) > 4 and parts[4]:
                style["bg_color"] = parts[4]
            items.append(TextLabelItem(text, coords[0], coords[1], style))

    # 6. Raw JSON Items
    if raw_items:
        for item_dict in raw_items:
            obj = item_from_dict(item_dict)
            if obj:
                items.append(obj)

    return items


def cli_annotate(input_path: str, output_path: str = None, stamps=None, boxes=None,
                 arrows=None, callouts=None, texts=None, raw_items=None) -> dict:
    """기존 이미지에 주석 객체를 합성 렌더링하여 새 이미지로 저장"""
    get_or_create_app()
    if not os.path.exists(input_path):
        return {"status": "error", "message": f"Input image not found: {input_path}"}

    pixmap = QPixmap(input_path)
    if pixmap.isNull():
        return {"status": "error", "message": f"Failed to load image: {input_path}"}

    items = parse_item_specs(stamps, boxes, arrows, callouts, texts, raw_items)

    img = QImage(pixmap.size(), QImage.Format_ARGB32)
    img.fill(Qt.transparent)

    painter = QPainter(img)
    try:
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.drawPixmap(0, 0, pixmap)

        for item in items:
            try:
                if isinstance(item, BlurMosaicItem):
                    item.render_mosaic(painter, pixmap)
                else:
                    item.render(painter)
            except Exception as e:
                print(f"[CLI 주석 렌더링 예외]: {e}")
    finally:
        painter.end()

    if not output_path:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_annotated.png"
    else:
        out_dir = os.path.dirname(os.path.abspath(output_path))
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

    saved = img.save(output_path, "PNG")
    if not saved:
        return {"status": "error", "message": f"Failed to save annotated image to {output_path}"}

    return {
        "status": "ok",
        "output_file": os.path.abspath(output_path),
        "items_applied": len(items),
        "width": img.width(),
        "height": img.height()
    }


def cli_render_project(project_path: str, output_path: str = None,
                       export_ppt: bool = False, export_slides: bool = False) -> dict:
    """프로젝트 파일(.mcs.json) 로드 및 주석 합성 렌더링"""
    get_or_create_app()
    if not os.path.exists(project_path):
        return {"status": "error", "message": f"Project file not found: {project_path}"}

    raw_pixmap, items, next_idx, metadata = ProjectManager.load_project(project_path)
    if raw_pixmap is None or raw_pixmap.isNull():
        return {"status": "error", "message": "Failed to restore raw bitmap from project file"}

    img = QImage(raw_pixmap.size(), QImage.Format_ARGB32)
    img.fill(Qt.transparent)

    painter = QPainter(img)
    try:
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.drawPixmap(0, 0, raw_pixmap)

        for item in items:
            try:
                if isinstance(item, BlurMosaicItem):
                    item.render_mosaic(painter, raw_pixmap)
                else:
                    item.render(painter)
            except Exception as e:
                print(f"[CLI 프로젝트 렌더링 예외]: {e}")
    finally:
        painter.end()

    if not output_path:
        base, _ = os.path.splitext(project_path)
        clean = base.replace(".mcs", "")
        output_path = f"{clean}_rendered.png"

    out_dir = os.path.dirname(os.path.abspath(output_path))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    saved = img.save(output_path, "PNG")
    if not saved:
        return {"status": "error", "message": f"Failed to save rendered project to {output_path}"}

    result = {
        "status": "ok",
        "output_file": os.path.abspath(output_path),
        "items_count": len(items),
        "width": img.width(),
        "height": img.height()
    }

    # PPT / 슬라이드 즉시 내보내기 옵션 연계
    if export_ppt or export_slides:
        pil_img = ExportEngine.qimage_to_pil(img)
        if export_ppt:
            cfg = load_user_config()
            temp_dir = os.path.join(os.path.dirname(os.path.abspath(output_path)), "temp_export")
            ppt_ok = ExportEngine.send_to_powerpoint(pil_img, temp_dir, cfg.get("ppt_layout", {}))
            result["powerpoint_exported"] = ppt_ok
        if export_slides:
            slides_ok = ExportEngine.send_to_google_slides(pil_img)
            result["google_slides_exported"] = slides_ok

    return result


def cli_export(input_path: str, target: str = "powerpoint", title: str = None, template: str = None) -> dict:
    """이미지 파일을 파워포인트 또는 구글 슬라이드로 즉시 내보내기"""
    get_or_create_app()
    if not os.path.exists(input_path):
        return {"status": "error", "message": f"Input image file not found: {input_path}"}

    try:
        pil_img = Image.open(input_path)
    except Exception as e:
        return {"status": "error", "message": f"Failed to open image: {e}"}

    cfg = load_user_config()
    target_lower = target.lower()

    if target_lower in ("powerpoint", "ppt"):
        layout = cfg.get("ppt_layout", {}).copy()
        if template:
            layout["template_path"] = template
        if title:
            layout["include_title"] = True
            layout["step_title_text"] = title

        temp_dir = os.path.join(os.path.dirname(os.path.abspath(input_path)), "temp_export")
        ok = ExportEngine.send_to_powerpoint(pil_img, temp_dir, layout)
        if not ok:
            return {"status": "error", "message": "Failed to send image to PowerPoint"}
        return {"status": "ok", "target": "powerpoint", "message": "Exported to PowerPoint successfully"}

    elif target_lower in ("google_slides", "slides"):
        ok = ExportEngine.send_to_google_slides(pil_img)
        if not ok:
            return {"status": "error", "message": "Failed to send image to Google Slides"}
        return {"status": "ok", "target": "google_slides", "message": "Exported to Google Slides successfully"}

    elif target_lower in ("clipboard", "clip"):
        ExportEngine.copy_to_clipboard(pil_img)
        return {"status": "ok", "target": "clipboard", "message": "Copied to clipboard as CF_DIB successfully"}

    else:
        return {"status": "error", "message": f"Unsupported target '{target}'. Use 'powerpoint', 'google_slides', or 'clipboard'"}


def handle_cli(argv: list) -> int:
    """CLI 명령어 파싱 및 실행 메인 핸들러"""
    parser = argparse.ArgumentParser(
        prog="ManualStudio",
        description="DragonRPA Manual Studio Headless Automation CLI"
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Subcommands")

    # 1. status
    subparsers.add_parser("status", help="Get application readiness, version, and monitors")

    # 2. capture
    p_cap = subparsers.add_parser("capture", help="Capture screen region")
    p_cap.add_argument("--rect", type=str, help="Capture rectangle: x,y,w,h")
    p_cap.add_argument("--monitor", type=int, default=0, help="Monitor index (0=Primary)")
    p_cap.add_argument("--fixed", action="store_true", help="Use configured fixed rect")
    p_cap.add_argument("--output", "-o", type=str, help="Output PNG path")

    # 3. annotate
    p_ann = subparsers.add_parser("annotate", help="Apply visual annotations to image")
    p_ann.add_argument("--input", "-i", type=str, required=True, help="Input image path")
    p_ann.add_argument("--output", "-o", type=str, help="Output image path")
    p_ann.add_argument("--stamp", "-s", action="append", help="Stamp: index:x,y[:color:size]")
    p_ann.add_argument("--box", "-b", action="append", help="Box: x,y,w,h[:color:width:fill]")
    p_ann.add_argument("--arrow", "-a", action="append", help="Arrow: x1,y1,x2,y2[:color:width]")
    p_ann.add_argument("--callout", "-c", action="append", help="Callout: text:bx,by,bw,bh:tx,ty")
    p_ann.add_argument("--text", "-t", action="append", help="Text: text:x,y[:color:size:bg]")

    # 4. render-project
    p_rnd = subparsers.add_parser("render-project", help="Render .mcs.json project file")
    p_rnd.add_argument("--input", "-i", type=str, required=True, help="Input .mcs.json path")
    p_rnd.add_argument("--output", "-o", type=str, help="Output PNG path")
    p_rnd.add_argument("--export-ppt", action="store_true", help="Export to PowerPoint")
    p_rnd.add_argument("--export-slides", action="store_true", help="Export to Google Slides")

    # 5. export
    p_exp = subparsers.add_parser("export", help="Export image to presentation")
    p_exp.add_argument("--input", "-i", type=str, required=True, help="Input image path")
    p_exp.add_argument("--target", type=str, default="powerpoint", choices=["powerpoint", "google_slides", "clipboard"])
    p_exp.add_argument("--title", type=str, help="Step title")
    p_exp.add_argument("--template", type=str, help="PowerPoint template path (.pptx)")

    args = parser.parse_args(argv)

    if args.subcommand == "status":
        res = cli_status()
    elif args.subcommand == "capture":
        res = cli_capture(args.rect, args.monitor, args.fixed, args.output)
    elif args.subcommand == "annotate":
        res = cli_annotate(
            args.input, args.output,
            stamps=args.stamp, boxes=args.box, arrows=args.arrow,
            callouts=args.callout, texts=args.text
        )
    elif args.subcommand == "render-project":
        res = cli_render_project(args.input, args.output, args.export_ppt, args.export_slides)
    elif args.subcommand == "export":
        res = cli_export(args.input, args.target, args.title, args.template)
    else:
        parser.print_help()
        return 1

    # 기계 판독형 JSON 출력
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0 if res.get("status") == "ok" else 1


if __name__ == "__main__":
    sys.exit(handle_cli(sys.argv[1:]))

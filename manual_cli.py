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
    StampItem, HighlightBoxItem, ArrowItem, ElbowArrowItem, CalloutItem,
    TextLabelItem, BlurMosaicItem, HotkeyBadgeItem,
    SpotlightMaskItem, ClickRippleItem, MagnifierZoomItem,
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


def parse_item_specs(stamps=None, boxes=None, arrows=None, elbows=None, callouts=None, texts=None, spotlights=None, clicks=None, magnifiers=None, raw_items=None) -> list:
    """CLI/MCP 문자열 인자를 파싱하여 주석 객체 리스트 생성"""
    cfg = DEFAULT_CONFIG
    items = []

    # 1. Stamps: "index:x,y[:color:size]"
    if stamps:
        for s in stamps:
            parts = s.split(":")
            idx = int(parts[0])
            coords = [float(v) for v in parts[1].split(",")]
            style = cfg.get("stamp_style", {}).copy()
            if len(parts) > 2 and parts[2]:
                style["bg_color"] = parts[2]
            if len(parts) > 3 and parts[3]:
                style["size"] = int(parts[3])
            items.append(StampItem(idx, coords[0], coords[1], style))

    # 2. Highlight Boxes: "x,y,w,h[:color:width:fill]"
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

    # 3-1. Elbow Arrows: "x1,y1,x2,y2[:color:width:route_mode]"
    if elbows:
        for ea in elbows:
            parts = ea.split(":")
            coords = [float(v) for v in parts[0].split(",")]
            style = cfg.get("arrow_style", {}).copy()
            route_mode = "HV"
            if len(parts) > 1 and parts[1]:
                style["color"] = parts[1]
            if len(parts) > 2 and parts[2]:
                style["width"] = int(parts[2])
            if len(parts) > 3 and parts[3]:
                raw_mode = parts[3].strip().lower()
                if raw_mode in ("vh", "bl", "tl"):
                    route_mode = "VH"
                else:
                    route_mode = "HV"
            items.append(ElbowArrowItem(QPointF(coords[0], coords[1]), QPointF(coords[2], coords[3]), style, route_mode))

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

    # 5.1 Spotlights: "x,y,w,h[:border_color:dim_opacity:border_width]"
    if spotlights:
        for sp in spotlights:
            parts = sp.split(":")
            rect_vals = [int(v) for v in parts[0].split(",")]
            style = {}
            if len(parts) > 1 and parts[1]:
                style["border_color"] = parts[1]
            if len(parts) > 2 and parts[2]:
                style["dim_opacity"] = int(parts[2])
            if len(parts) > 3 and parts[3]:
                style["border_width"] = int(parts[3])
            items.append(SpotlightMaskItem(QRect(rect_vals[0], rect_vals[1], rect_vals[2], rect_vals[3]), style))

    # 5.2 Clicks: "x,y[:left|right|double:label]"
    if clicks:
        for clk in clicks:
            parts = clk.split(":")
            coords = [float(v) for v in parts[0].split(",")]
            click_type = parts[1] if len(parts) > 1 and parts[1] else "left"
            style = {}
            if len(parts) > 2 and parts[2]:
                style["label"] = parts[2]
            items.append(ClickRippleItem(coords[0], coords[1], click_type, style))

    # 5.3 Magnifiers: "sx,sy,sw,sh:lx,ly,lw,lh[:zoom:border_color]"
    if magnifiers:
        for mag in magnifiers:
            parts = mag.split(":")
            src_vals = [int(v) for v in parts[0].split(",")]
            lens_vals = [int(v) for v in parts[1].split(",")]
            zoom = float(parts[2]) if len(parts) > 2 and parts[2] else 2.0
            style = {}
            if len(parts) > 3 and parts[3]:
                style["border_color"] = parts[3]
            items.append(MagnifierZoomItem(
                QRect(src_vals[0], src_vals[1], src_vals[2], src_vals[3]),
                QRect(lens_vals[0], lens_vals[1], lens_vals[2], lens_vals[3]),
                zoom, style
            ))

    # 6. Raw JSON Items
    if raw_items:
        for item_dict in raw_items:
            obj = item_from_dict(item_dict)
            if obj:
                items.append(obj)

    return items


def cli_annotate(input_path: str, output_path: str = None, stamps=None, boxes=None,
                 arrows=None, elbows=None, callouts=None, texts=None, spotlights=None, clicks=None, magnifiers=None, raw_items=None) -> dict:
    """기존 이미지에 주석 객체를 합성 렌더링하여 새 이미지로 저장"""
    get_or_create_app()
    if not os.path.exists(input_path):
        return {"status": "error", "message": f"Input image not found: {input_path}"}

    pixmap = QPixmap(input_path)
    if pixmap.isNull():
        return {"status": "error", "message": f"Failed to load image: {input_path}"}

    items = parse_item_specs(stamps, boxes, arrows, elbows, callouts, texts, spotlights, clicks, magnifiers, raw_items)

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
                elif isinstance(item, MagnifierZoomItem):
                    item.render_zoom(painter, pixmap)
                elif isinstance(item, SpotlightMaskItem):
                    item.render_spotlight(painter, pixmap.width(), pixmap.height())
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


def cli_batch(workflow_path: str, output_dir: str = None, doc_format: str = "all", title: str = None) -> dict:
    """AI 에이전트 다단계 매뉴얼 일괄 캡처 및 복합 문서(MD, HTML, PPT) 동시 생성 파이프라인"""
    get_or_create_app()
    if not os.path.exists(workflow_path):
        return {"status": "error", "message": f"Workflow file not found: {workflow_path}"}

    try:
        with open(workflow_path, "r", encoding="utf-8") as f:
            workflow = json.load(f)
    except Exception as e:
        return {"status": "error", "message": f"Failed to parse workflow JSON: {e}"}

    manual_title = title or workflow.get("title", "Automated Manual Guide")
    steps_data = workflow.get("steps", [])
    if not steps_data:
        return {"status": "error", "message": "Workflow contains no steps"}

    if not output_dir:
        output_dir = os.path.join(os.path.dirname(os.path.abspath(workflow_path)), "manual_output")
    os.makedirs(output_dir, exist_ok=True)

    generated_steps = []

    for i, step_spec in enumerate(steps_data):
        step_idx = i + 1
        s_title = step_spec.get("title", f"Step {step_idx}")
        s_desc = step_spec.get("description", "")
        s_source = step_spec.get("source", "capture")

        # 1. 원본 이미지 확보 (캡처 또는 기존 파일)
        if s_source == "capture":
            rect = step_spec.get("rect")
            mon = int(step_spec.get("monitor", 0))
            fixed = bool(step_spec.get("fixed", False))
            step_raw_path = os.path.join(output_dir, f"step_{step_idx:03d}_raw.png")
            cap_res = cli_capture(rect=rect, monitor=mon, fixed=fixed, output=step_raw_path)
            if cap_res.get("status") != "ok":
                return {"status": "error", "message": f"Step {step_idx} capture failed: {cap_res.get('message')}"}
            source_img = cap_res["output_file"]
        else:
            source_img = s_source
            if not os.path.exists(source_img):
                return {"status": "error", "message": f"Step {step_idx} source file not found: {source_img}"}

        # 2. 주석 합성
        step_ann_path = os.path.join(output_dir, f"step_{step_idx:03d}.png")
        ann_cfg = step_spec.get("annotations", {})

        ann_res = cli_annotate(
            input_path=source_img,
            output_path=step_ann_path,
            stamps=ann_cfg.get("stamps"),
            boxes=ann_cfg.get("boxes"),
            arrows=ann_cfg.get("arrows"),
            elbows=ann_cfg.get("elbows"),
            callouts=ann_cfg.get("callouts"),
            texts=ann_cfg.get("texts"),
            spotlights=ann_cfg.get("spotlights"),
            clicks=ann_cfg.get("clicks"),
            magnifiers=ann_cfg.get("magnifiers"),
            raw_items=ann_cfg.get("raw_items")
        )
        if ann_res.get("status") != "ok":
            return {"status": "error", "message": f"Step {step_idx} annotation failed: {ann_res.get('message')}"}

        generated_steps.append({
            "step_num": step_idx,
            "title": s_title,
            "description": s_desc,
            "image_file": os.path.abspath(step_ann_path)
        })

    # 3. 문서 내보내기 (Markdown, HTML)
    md_path = None
    html_path = None

    if doc_format in ("all", "md", "markdown"):
        md_path = os.path.join(output_dir, "manual.md")
        ExportEngine.export_to_markdown(generated_steps, md_path, title=manual_title)

    if doc_format in ("all", "html"):
        html_path = os.path.join(output_dir, "manual.html")
        ExportEngine.export_to_html(generated_steps, html_path, title=manual_title)

    return {
        "status": "ok",
        "title": manual_title,
        "total_steps": len(generated_steps),
        "output_dir": os.path.abspath(output_dir),
        "markdown_file": os.path.abspath(md_path) if md_path else None,
        "html_file": os.path.abspath(html_path) if html_path else None,
        "steps": generated_steps
    }


def cli_export_doc(input_files: list, output_path: str, doc_format: str = "md", title: str = None) -> dict:
    """기존 이미지 목록을 단일 마크다운 또는 HTML 매뉴얼 문서로 통합 내보내기"""
    get_or_create_app()
    steps = []
    for i, p in enumerate(input_files):
        if os.path.exists(p):
            base = os.path.basename(p)
            clean = os.path.splitext(base)[0].replace("_", " ")
            steps.append({
                "step_num": i + 1,
                "title": f"Step {i+1}: {clean}",
                "description": "",
                "image_file": os.path.abspath(p)
            })

    if not steps:
        return {"status": "error", "message": "No valid input image files found"}

    doc_title = title or "Manual Studio Document"
    fmt = doc_format.lower()
    if fmt in ("md", "markdown"):
        out = ExportEngine.export_to_markdown(steps, output_path, title=doc_title)
    elif fmt == "html":
        out = ExportEngine.export_to_html(steps, output_path, title=doc_title)
    else:
        return {"status": "error", "message": f"Unsupported format: {doc_format}. Use 'md' or 'html'"}

    return {
        "status": "ok",
        "format": fmt,
        "output_file": os.path.abspath(out),
        "steps_count": len(steps)
    }


def cli_stitch(input_files: list, output_path: str = None) -> dict:
    """수직 스크롤 프레임 이미지 목록을 파노라마로 자동 스티칭하여 저장"""
    get_or_create_app()
    if not input_files:
        return {"status": "error", "message": "No input files provided for stitching"}

    valid_files = [p for p in input_files if os.path.exists(p)]
    if not valid_files:
        return {"status": "error", "message": "None of the specified input files exist"}

    from manual_capture_studio import ScrollStitchEngine
    stitched = ScrollStitchEngine.stitch_images(valid_files)
    if stitched is None:
        return {"status": "error", "message": "Stitching failed"}

    if not output_path:
        out_dir = "captures"
        os.makedirs(out_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(out_dir, f"stitched_{ts}.png")
    else:
        out_dir = os.path.dirname(os.path.abspath(output_path))
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

    stitched.save(output_path, "PNG")
    return {
        "status": "ok",
        "output_file": os.path.abspath(output_path),
        "width": stitched.width,
        "height": stitched.height,
        "frames_count": len(valid_files)
    }


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
    p_ann.add_argument("--elbow", "-e", action="append", help="Elbow: x1,y1,x2,y2[:color:width:route_mode]")
    p_ann.add_argument("--callout", "-c", action="append", help="Callout: text:bx,by,bw,bh:tx,ty")
    p_ann.add_argument("--text", "-t", action="append", help="Text: text:x,y[:color:size:bg]")
    p_ann.add_argument("--spotlight", action="append", help="Spotlight: x,y,w,h[:border:dim:bw]")
    p_ann.add_argument("--click", action="append", help="Click: x,y[:left|right|double:label]")
    p_ann.add_argument("--magnifier", action="append", help="Magnifier: sx,sy,sw,sh:lx,ly,lw,lh[:zoom:border]")

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

    # 6. batch
    p_bat = subparsers.add_parser("batch", help="Execute multi-step manual workflow JSON")
    p_bat.add_argument("--input", "-i", type=str, required=True, help="Workflow JSON file path")
    p_bat.add_argument("--output-dir", "-o", type=str, help="Output directory")
    p_bat.add_argument("--format", type=str, default="all", choices=["all", "md", "html", "markdown"])
    p_bat.add_argument("--title", type=str, help="Manual title")

    # 7. export-doc
    p_doc = subparsers.add_parser("export-doc", help="Export images to Markdown or HTML manual")
    p_doc.add_argument("--input", "-i", nargs="+", required=True, help="List of step image paths")
    p_doc.add_argument("--output", "-o", type=str, required=True, help="Output document path (.md or .html)")
    p_doc.add_argument("--format", type=str, default="md", choices=["md", "html", "markdown"])
    p_doc.add_argument("--title", type=str, help="Document title")

    # 8. stitch (Phase 4 Scroll Stitching)
    p_st = subparsers.add_parser("stitch", help="Vertically stitch sequential scroll frame images into panorama")
    p_st.add_argument("--input", "-i", nargs="+", required=True, help="List of scroll frame image paths in top-to-bottom order")
    p_st.add_argument("--output", "-o", type=str, help="Output stitched PNG path")

    args = parser.parse_args(argv)

    if args.subcommand == "status":
        res = cli_status()
    elif args.subcommand == "capture":
        res = cli_capture(args.rect, args.monitor, args.fixed, args.output)
    elif args.subcommand == "annotate":
        res = cli_annotate(
            args.input, args.output,
            stamps=args.stamp, boxes=args.box, arrows=args.arrow,
            elbows=args.elbow,
            callouts=args.callout, texts=args.text,
            spotlights=args.spotlight, clicks=args.click, magnifiers=args.magnifier
        )
    elif args.subcommand == "render-project":
        res = cli_render_project(args.input, args.output, args.export_ppt, args.export_slides)
    elif args.subcommand == "export":
        res = cli_export(args.input, args.target, args.title, args.template)
    elif args.subcommand == "batch":
        res = cli_batch(args.input, args.output_dir, args.format, args.title)
    elif args.subcommand == "export-doc":
        res = cli_export_doc(args.input, args.output, args.format, args.title)
    elif args.subcommand == "stitch":
        res = cli_stitch(args.input, args.output)
    else:
        parser.print_help()
        return 1

    # 기계 판독형 JSON 출력
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0 if res.get("status") == "ok" else 1


if __name__ == "__main__":
    sys.exit(handle_cli(sys.argv[1:]))

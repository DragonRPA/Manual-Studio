# AGENTS.md - DragonRPA Manual Studio AI Agent Specification & Interface

Welcome, Agent. This document provides a high-density, machine-readable specification of **Manual Studio (매뉴얼 스튜디오)**.
Use this reference to inspect, control, automate, and extend the application via CLI, MCP (Model Context Protocol), or direct Python API.

---

## 1. System Overview & Architecture

Manual Studio is a high-speed manual authoring application built with **PySide6 (Qt 6)** and **Python 3.11**.
It automates the full workflow: **Screen Capture -> Annotation Overlay -> Presentation / Document Export (PowerPoint / Google Slides / Markdown / HTML)**.

### Core Modules
| Module | Role | Key Classes / Functions |
|:---|:---|:---|
| `manual_capture_studio.py` | Main GUI, Canvas, Annotations, Export | `ManualStudioWindow`, `ExportEngine`, `ProjectManager`, `ThemeManager` |
| `manual_cli.py` | Headless Command-Line Interface | `handle_cli()`, `cli_capture()`, `cli_annotate()`, `cli_batch()`, `cli_export()` |
| `mcp_server.py` | Anthropic Model Context Protocol Server | `MCPServer`, 9 Core MCP Tools |
| `i18n_manager.py` | Global 13-Language Engine | `I18nManager`, `tr(key)` (KO, EN, ZH, ZH-TW, JA, DE, ES, FR, IT, PT, RU, VI, ID) |
| `license_engine.py` | License Validator (HMAC-SHA256) | `LicenseEngine`, `LicenseType`, `get_hwid()` |
| `updater_engine.py` | Smart Auto-Updater Client | `UpdateCheckerThread`, `VersionComparator` |

---

## 2. CLI Headless Interface (`--cli`)

Agents can execute full workflows without launching the GUI.

### Base Invocation
```bash
# Via Compiled Binary
ManualStudio.exe --cli <subcommand> [options]

# Via Python Source
python manual_capture_studio.py --cli <subcommand> [options]
```

### Supported Subcommands

#### 1) `status` - Application Health & Metadata
```bash
ManualStudio.exe --cli status
```
- **Output**: JSON object with `version`, `is_licensed`, `screens`, `fixed_rect`, `export_target`.

#### 2) `capture` - Headless Screen Capture
```bash
ManualStudio.exe --cli capture --rect 100,100,960,540 --output captures/step1_raw.png
ManualStudio.exe --cli capture --monitor 0 --output captures/screen0.png
ManualStudio.exe --cli capture --fixed --output captures/step_fixed.png
```

#### 3) `annotate` - Apply Graphic Annotations (Basic & Advanced)
```bash
ManualStudio.exe --cli annotate \
  --input captures/step1_raw.png \
  --stamp "1:150,220:#007AFF:32" \
  --box "100,180,300,120:#007AFF:3:fill" \
  --arrow "120,100,150,200:#007AFF:3" \
  --elbow "120,100,250,220:#007AFF:3:tr" \
  --callout "Click Here:450,250,300,200" \
  --spotlight "100,180,300,120:#007AFF:160:2" \
  --click "250,240:left:CLICK" \
  --magnifier "100,180,60,40:450,180,180,120:2.5" \
  --output captures/step1_annotated.png
```
- `--elbow <x1,y1,x2,y2[:color:width:route_mode]>`: Right-angle elbow arrow (`route_mode`: `HV`, `VH`, `tr`, `br`, `bl`, `tl`).
- `--spotlight <x,y,w,h[:border:opacity:bw]>`: Dims surrounding area to spotlight target.
- `--click <x,y[:left|right|double:label]>`: Renders concentric ripple indicator.
- `--magnifier <sx,sy,sw,sh:lx,ly,lw,lh[:zoom:border]>`: Lens magnifying UI detail.

#### 4) `batch` - Execute Declarative Multi-Step Workflow JSON
```bash
ManualStudio.exe --cli batch --input workflow.json --output-dir ./out --format all --title "User Guide"
```
- Generates all annotated step PNGs, Markdown (`manual.md`), and standalone HTML (`manual.html`) in one call.

#### 5) `export-doc` - Export Existing Steps to Markdown or HTML
```bash
ManualStudio.exe --cli export-doc --input step1.png step2.png --output manual.md --format md --title "Guide"
```

#### 6) `render-project` - Render `.mcs.json` Project File
```bash
ManualStudio.exe --cli render-project --input project.mcs.json --output rendered.png [--export-ppt]
```

#### 7) `export` - Direct Presentation Ingestion
```bash
ManualStudio.exe --cli export --input captures/step1_annotated.png --target powerpoint --title "Step 1. Login"
ManualStudio.exe --cli export --input captures/step1_annotated.png --target google_slides
```

---

## 3. Model Context Protocol (MCP) Server

Manual Studio includes a built-in standard stdio JSON-RPC 2.0 MCP server.

### Claude Desktop / Cowork Configuration
Add to `claude_desktop_config.json` (or Cowork agent settings):
```json
{
  "mcpServers": {
    "manual-studio": {
      "command": "D:/01.AntiGravity/999.매뉴얼제작/ManualStudio.exe",
      "args": ["--mcp"]
    }
  }
}
```

### Registered MCP Tools (9)
1. **`manual_studio_status()`**: Returns application status, version, display geometry, and license validity.
2. **`manual_studio_capture_screen(rect=None, monitor=0, fixed=False, output_path=None)`**: High-resolution screenshot.
3. **`manual_studio_add_annotations(input_path, output_path=None, stamps=None, boxes=None, arrows=None, elbows=None, ...)`**: Injects graphic annotations.
4. **`manual_studio_add_spotlight(input_path, rect, border_color="#007AFF", dim_opacity=160, output_path=None)`**: Spotlight focus mask.
5. **`manual_studio_render_project(project_path, output_path=None, export_ppt=False, export_slides=False)`**: Renders `.mcs.json`.
6. **`manual_studio_export_presentation(input_path, target="powerpoint", title=None)`**: Direct PPT/Google Slides export.
7. **`manual_studio_create_step(rect, annotations, export_target=None, step_title=None)`**: All-in-one Capture -> Annotate -> Export.
8. **`manual_studio_batch_pipeline(workflow_path=None, workflow_data=None, output_dir=None, format="all", title=None)`**: All-in-one multi-step manual generation from declarative JSON.
9. **`manual_studio_export_document(steps, output_path, format="md"|"html", title=None)`**: Exports steps into Markdown or HTML guide.

---

## 4. Declarative Batch Workflow Schema (`workflow.json`)

```json
{
  "title": "ERP System Quick Start Guide",
  "steps": [
    {
      "step_num": 1,
      "title": "Authentication",
      "description": "Log in with employee credentials.",
      "source": "capture",
      "rect": "100,100,800,600",
      "annotations": {
        "stamps": ["1:150,220:#007AFF:32"],
        "boxes": ["100,180,300,120:#007AFF:3:fill"],
        "arrows": ["120,100,150,200:#007AFF:3"],
        "elbows": ["120,100,250,220:#007AFF:3:tr"],
        "spotlights": ["100,180,300,120:#007AFF:160:2"],
        "clicks": ["250,240:left:LOGIN"]
      }
    }
  ]
}
```

---

## 5. Declarative Project Specification (`.drg` / `.mcs.json`)

Manual Studio uses a multi-layered annotation schema supporting single-file JSON (`.mcs.json`) and self-contained ZIP archive packages (`.drg`):

### 1) Package Archive (`.drg`)
- Structure:
  - `manifest.json`: Multi-step metadata and annotation layers.
  - `slides/step_{i:03d}_raw.png`: Lossless raw capture bitmaps.

### 2) JSON Manifest Schema (`manifest.json` / `.mcs.json`)
```json
{
  "version": "1.5.0",
  "project_title": "ERP User Guide",
  "canvas_size": [1920, 1080],
  "slides": [
    {
      "step_num": 1,
      "title": "Authentication",
      "raw_image_file": "slides/step_001_raw.png",
      "items": [
        {
          "type": "StampItem",
          "index": 1,
          "pos": [240.0, 310.0],
          "style": { "size": 32, "bg_color": "#007AFF", "text_color": "#FFFFFF" }
        },
        {
          "type": "HighlightBoxItem",
          "rect": [200, 280, 450, 120],
          "style": { "color": "#007AFF", "border_width": 3, "fill": false }
        },
        {
          "type": "ElbowArrowItem",
          "start_pos": [120.0, 100.0],
          "end_pos": [250.0, 220.0],
          "route_mode": "HV",
          "style": { "color": "#007AFF", "width": 3, "head_size": 14 }
        }
      ]
    }
  ]
}
```

---

## 6. UI Automation (UIA) & Shortcuts Map

- Window Title Pattern: `매뉴얼 스튜디오 - Manual Studio*`
- OS UI Auto-Branching: `ui_style: "auto"` (Auto-detects macOS Cupertino on darwin, Windows Fluent on win32).
- Key UI Elements & Controls:
  - `BtnFixedCapture` / F9: Quick fixed capture.
  - `BtnVariableCapture` / Shift+F9: Interactive region capture.
  - `BtnSubCapture` / F8: Modal sub-window capture.
  - `BtnExportPpt` / F10: PowerPoint slide insertion (+ new slide creation).
  - `BtnExportHwp` / Shift+F10, F12: Hancom Hangul (HWP) document/cursor insertion.
  - `BtnSendSlides` / F11: Direct Google Slides browser injection.
  - `BtnNewProject` / Ctrl+N: Initialize new empty project.
  - `BtnOpenProject` / Ctrl+O: Open `.drg` / `.mcs.json` project.
  - `BtnSaveProject` / Ctrl+S: Save `.drg` / `.mcs.json` project.
  - `BtnSaveAsProject` / Ctrl+Shift+S: Save project with new filename.
  - `BtnMergeProject` / Ctrl+Shift+M: Merge external project slides into current timeline.
  - `BtnReleaseNotes`: Open Release Notes history dialog (30 releases viewable).
  - `BtnToggleRibbon` / Ctrl+M: Toggle ribbon mode (Standard vs 42 Vector Icons).
  - `BtnElbowTR`: Elbow arrow Right then Down (`─┐`, Top-Right corner).
  - `BtnElbowBR`: Elbow arrow Right then Up (`─┘`, Bottom-Right corner).
  - `BtnElbowBL`: Elbow arrow Down then Right (`│└`, Bottom-Left corner).
  - `BtnElbowTL`: Elbow arrow Up then Right (`│┌`, Top-Left corner).
  - `Tab` / `Space`: Toggle right-angle routing axis (`HV` ↔ `VH`).
  - Mode switches: `V` (Select), `S` (Stamp), `B` (Box), `A` (Arrow), `E` (Elbow), `T` (Text), `C` (Callout), `M` (Blur), `X` (Smart Eraser).

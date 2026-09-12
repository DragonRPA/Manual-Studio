# AGENTS.md - DragonRPA Manual Studio AI Agent Specification & Interface

Welcome, Agent. This document provides a high-density, machine-readable specification of **Manual Studio (매뉴얼 스튜디오)**.
Use this reference to inspect, control, automate, and extend the application via CLI, MCP (Model Context Protocol), or direct Python API.

---

## 1. System Overview & Architecture

Manual Studio is a high-speed manual authoring application built with **PySide6 (Qt 6)** and **Python 3.11**.
It automates the full workflow: **Screen Capture -> Annotation Overlay -> Presentation Export (PowerPoint / Google Slides)**.

### Core Modules
| Module | Role | Key Classes / Functions |
|:---|:---|:---|
| `manual_capture_studio.py` | Main GUI, Canvas, Annotations, Export | `ManualStudioWindow`, `ExportEngine`, `ProjectManager`, `ThemeManager` |
| `manual_cli.py` | Headless Command-Line Interface | `handle_cli()`, `cli_capture()`, `cli_annotate()`, `cli_export()` |
| `mcp_server.py` | Anthropic Model Context Protocol Server | `MCPServer`, `manual_studio_status`, `capture_screen`, `create_step` |
| `i18n_manager.py` | Global 9-Language Engine | `I18nManager`, `tr(key)` (KO, EN, ZH, JA, DE, ES, FR, PT, RU) |
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
- **Output**: JSON object with `version`, `license_status`, `monitors`, `config_path`.

#### 2) `capture` - Headless Screen Capture
```bash
ManualStudio.exe --cli capture --rect 100,100,960,540 --output captures/step1_raw.png
ManualStudio.exe --cli capture --monitor 0 --output captures/screen0.png
ManualStudio.exe --cli capture --fixed --output captures/step_fixed.png
```
- `--rect <x,y,w,h>`: Crop specific screen coordinates.
- `--monitor <index>`: Capture specific display (0 = Primary).
- `--fixed`: Use configured fixed capture rectangle from `config.json`.
- `--output <path>`: Target PNG image path (defaults to auto-generated timestamp file).

#### 3) `annotate` - Apply Graphic Annotations
```bash
ManualStudio.exe --cli annotate \
  --input captures/step1_raw.png \
  --stamp "1:150,220" \
  --box "100,180,300,120:#E53935:3" \
  --arrow "120,100,150,200:#E53935:3" \
  --callout "Click Here:450,250,300,200" \
  --text "Notice:50,50:#FFFFFF:#212121" \
  --output captures/step1_annotated.png
```

#### 4) `render-project` - Render `.mcs.json` Project File
```bash
ManualStudio.exe --cli render-project --input project.mcs.json --output rendered.png [--export-ppt]
```

#### 5) `export` - Direct Presentation Ingestion
```bash
ManualStudio.exe --cli export --input captures/step1_annotated.png --target powerpoint --title "Step 1. Login"
ManualStudio.exe --cli export --input captures/step1_annotated.png --target google_slides
```
- `--target`: `powerpoint` (local desktop) or `google_slides` (web browser).
- `--title`: Optional step title to insert.

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
*(Or if running from source: `"command": "python", "args": ["D:/01.AntiGravity/999.매뉴얼제작/mcp_server.py"]`)*

### Registered MCP Tools
1. **`manual_studio_status()`**: Returns application status, version, display geometry, and license validity.
2. **`capture_screen(rect=None, monitor=0, output_path=None)`**: Takes a high-resolution screenshot.
3. **`add_annotations(image_path, annotations, output_path=None)`**: Injects stamps, boxes, arrows, callouts.
4. **`render_project(project_file, output_path=None)`**: Renders an existing `.mcs.json` file.
5. **`export_presentation(image_path, target="powerpoint", title=None)`**: Sends image to PowerPoint or Google Slides.
6. **`create_step(rect, annotations, export_target=None, step_title=None)`**: All-in-one composite action (Capture -> Annotate -> Export).

---

## 4. Declarative Project Specification (`.mcs.json`)

Manual Studio uses a simple JSON schema for multi-layered annotation projects:
```json
{
  "version": "1.4.0",
  "canvas_size": [1920, 1080],
  "raw_image_file": "step_001_raw.png",
  "items": [
    {
      "type": "StampItem",
      "index": 1,
      "pos": [240.0, 310.0],
      "style": { "size": 32, "bg_color": "#E53935", "text_color": "#FFFFFF" }
    },
    {
      "type": "HighlightBoxItem",
      "rect": [200, 280, 450, 120],
      "style": { "color": "#E53935", "border_width": 3, "fill": false }
    },
    {
      "type": "CalloutItem",
      "text": "Enter credentials",
      "rect": [400, 200, 200, 60],
      "tail_pos": [250.0, 300.0],
      "style": { "font_size": 12, "text_color": "#FFFFFF", "bg_color": "#212121" }
    }
  ]
}
```

---

## 5. UI Automation (UIA) & Shortcuts Map

When interacting via OS-level automation (`pywinauto`, `Playwright`, `Accessibility`):
- Window Title Pattern: `매뉴얼 스튜디오 - Manual Studio*`
- Key UI Elements:
  - `BtnFixedCapture` / F9: Quick fixed capture.
  - `BtnVariableCapture` / Shift+F9: Interactive region capture.
  - `BtnSubCapture` / F8: Modal sub-window capture.
  - `BtnExportPpt` / F10: PPT/Slides generation.
  - `BtnSaveProject` / Ctrl+S: Save `.mcs.json`.
  - `BtnOpenProject` / Ctrl+O: Open `.mcs.json`.
  - Mode switches: `V` (Select), `S` (Stamp), `B` (Box).

---

## 6. Error Handling & Recovery SOP for Agents

1. **PowerPoint Not Running**:
   - If COM `GetActiveObject` fails, `ExportEngine` automatically falls back to `Dispatch` (starts a new PowerPoint instance) or opens a blank presentation.
2. **Google Slides Browser Window Missing**:
   - `ExportEngine.find_google_slides_window()` looks for tabs matching `docs.google.com/presentation`.
   - If `NOT_FOUND` is returned, open Google Slides in Chrome first: `start https://slides.new`.
3. **Capture Permission on macOS**:
   - Verify `kTCCServiceScreenCapture` access. If denied, prompt user to enable permissions in macOS Privacy Settings.

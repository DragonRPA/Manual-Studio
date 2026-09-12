# Manual Studio v1.4.0 Benutzerhandbuch (Deutsch)
> **Automatisierte PowerPoint-Handbucherstellung • DragonRPA Co.**
> *Official Release Build v1.4.0 | (주)드래곤알피에이 (DragonRPA Co., Ltd.)*

---

## 📌 1. Core Features (Deutsch)
Manual Studio is an enterprise standardization software that covers the entire manual generation workflow: high-precision screen captures, 10 professional annotations, corporate PPT master template inheritance, and one-click slide generation.

![Manual Studio Main Window Interface](images/guide_main_window.png)

---

## ⚡ 2. Hotkeys & Instant Capture

| Hotkey | Name | Description |
| :--- | :--- | :--- |
| **`F9`** | Fixed Capture | Instantly captures the configured screen coordinate area |
| **`Shift + F9`** | Area Capture | Instant capture upon mouse release without Enter key delay |
| **`F8`** | Sub Capture | Captures secondary windows or popups as floating overlays |
| **`F10`** | PPT Export | Inserts high-res slide into PowerPoint and copies to clipboard |
| **`Ctrl + S`** | Save Project | Losslessly stores raw bitmap and annotation vector items in `.mcs.json` |
| **`Ctrl + Z`** | Undo | Restores previous canvas state safely |


> **Tip**: Shift+F9 또는 F8 캡처 시, 마우스 드래그를 마치고 손을 떼는 순간(Mouse Release) 엔터키 입력 대기 없이 즉시 확정되어 캔버스에 안착됩니다.

---

## 🎨 3. 10 Professional Annotation Tools

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


![Annotation Tools and Canvas Overview](images/guide_annotations.png)

---

## 📊 4. Corporate PPT Master Template & Slide Generation

- **Corporate Master Template (`.pptx`, `.potx`) Binding**:
  - Configure your company's master presentation under `Settings -> Preferences`. Generated slides automatically inherit corporate headers, logos, and slide master designs.
- **Standardized Slide Layout**:
  - Automatically scales images to target width (960px or 16:9 aspect fit) and aligns them with consistent margins.
- **Sequential Step Renumbering**:
  - Automatically adds `Step {n}. [Enter Title]` headers. If slides are inserted or removed, use `Edit -> 🔢 Auto-renumber PowerPoint Steps` to re-index all slides in 1 second.


![Settings and Master Template Configuration](images/guide_settings_dialog.png)

---

## 💾 5. Disaster Recovery & Auto-Save System

- **Loss-Prevention Auto-Save**:
  - Automatically saves the active canvas and annotation layers at user-defined intervals (1 to 30 minutes).
- **One-Click Crash Recovery**:
  - In the event of an abnormal shutdown or power outage, restart Manual Studio to receive an automatic recovery prompt, restoring your full workspace without data loss.


---

## 🔑 6. License Activation & Watermark Policy

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


![License Registration Dialog](images/guide_license_dialog.png)

---

## 🌐 7. Global 9-Language Support & Multilingual Fonts
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

## 📮 8. Official Support & Inquiries
- **Company**: (주)드래곤알피에이 (DragonRPA Co., Ltd.)
- **CEO & Lead Architect**: 이정용 (Victor Lee)
- **Official Contact**: `77.victor.lee@gmail.com`
- **Copyright**: Copyright © 2026 DragonRPA Co. All rights reserved.

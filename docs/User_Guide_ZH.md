# Manual Studio v1.4.0 官方用户指南
> **企业级 PowerPoint 操作手册制作自动化解决方案 • DragonRPA Co.**
> *Official Release Build v1.4.0 | (주)드래곤알피에이 (DragonRPA Co., Ltd.)*

---

## 📌 1. 核心功能概览
Manual Studio 是一款专业的企业级屏幕捕获与手册制作软件。它将截屏、10种专业标注、企业PPT母版继承、PPT幻灯片自动排版一键打通，大幅减少手册制作时间。

![Manual Studio Main Window Interface](images/guide_main_window.png)

---

## ⚡ 2. 快捷键与即时截图

| 快捷键 | 功能名称 | 详细说明 |
| :--- | :--- | :--- |
| **`F9`** | 固定坐标截图 | 按照预设坐标和尺寸立即抓取屏幕 |
| **`Shift + F9`** | 区域选取截图 | 鼠标拖拽释放时立即捕获，无需回车确认 |
| **`F8`** | 部分追加截图 | 将附加窗口或弹出框截取为可调整的图层贴片 |
| **`F10`** | 生成 PPT 幻灯片 | 自动在打开的 PPT 中创建幻灯片并写入剪贴板 |
| **`Ctrl + S`** | 保存工程 | 将原始位图与标注矢量数据无损保存至 `.mcs.json` |
| **`Ctrl + Z`** | 撤销 | 撤销上一步标注操作 |


> **Tip**: Shift+F9 또는 F8 캡처 시, 마우스 드래그를 마치고 손을 떼는 순간(Mouse Release) 엔터키 입력 대기 없이 즉시 확정되어 캔버스에 안착됩니다.

---

## 🎨 3. 10 大专业标注工具

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


![Annotation Tools and Canvas Overview](images/guide_annotations.png)

---

## 📊 4. 企业 PPT 母版集成与自动排版

- **关联企业 PPT 母版文件(`.pptx`, `.potx`)**:
  - 在`设置 -> 首选项`中指定公司的母版文件，自动继承公司标准页眉、底色与企业 Logo。
- **幻灯片标准化对齐**:
  - 自动将截图规整为统一宽度（960px或16:9比例），整齐居中排版。
- **步骤编号一键重排**:
  - 自动插入 `Step {n}. [步骤名称]`。增删幻灯片后，通过`编辑 -> 🔢 自动重排 PPT 步骤编号`在 1 秒内刷新全局序号。


![Settings and Master Template Configuration](images/guide_settings_dialog.png)

---

## 💾 5. 防遗失自动保存与崩溃恢复

- **自动保存机制**:
  - 支持 1 至 30 分钟周期性自动保存当前作业进度。
- **异常崩溃恢复**:
  - 意外断电或关闭后重新启动时，自动提示恢复未保存工程，保障工作数据零丢失。


---

## 🔑 6. 许可证激活与水印说明

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


![License Registration Dialog](images/guide_license_dialog.png)

---

## 🌐 7. 全球 9 种语言与中文字体支持
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

## 📮 8. 官方技术支持与联系方式
- **Company**: (주)드래곤알피에이 (DragonRPA Co., Ltd.)
- **CEO & Lead Architect**: 이정용 (Victor Lee)
- **Official Contact**: `77.victor.lee@gmail.com`
- **Copyright**: Copyright © 2026 DragonRPA Co. All rights reserved.

"""
================================================================================
(주)드래곤알피에이 매뉴얼 스튜디오 글로벌 다국어 엔진 (I18nManager)
Global Internationalization & Localization Engine for Manual Studio
Supported: KO, EN, ZH, JA, DE, ES, FR, PT, RU (9 Languages)
================================================================================
"""

import os
import json
from PySide6.QtCore import QLocale

class I18nManager:
    _instance = None

    SUPPORTED_LOCALES = {
        "ko": "한국어 (Korean)",
        "en": "English",
        "zh": "简体中文 (Chinese Simplified)",
        "ja": "日本語 (Japanese)",
        "de": "Deutsch (German)",
        "es": "Español (Spanish)",
        "fr": "Français (French)",
        "pt": "Português (Portuguese)",
        "ru": "Русский (Russian)"
    }

    FALLBACK_FONTS = [
        "Segoe UI",
        "Microsoft YaHei",
        "Yu Gothic",
        "Meiryo",
        "Malgun Gothic",
        "Arial",
        "sans-serif"
    ]

    PPT_STEP_TEMPLATES = {
        "ko": "Step {n}. [단계명 입력]",
        "en": "Step {n}. [Enter Step Title]",
        "zh": "步骤 {n}. [输入步骤名称]",
        "ja": "ステップ {n}. [手順名を入力]",
        "de": "Schritt {n}. [Schrittbezeichnung eingeben]",
        "es": "Paso {n}. [Ingrese título del paso]",
        "fr": "Étape {n}. [Entrez le titre de l'étape]",
        "pt": "Passo {n}. [Digite o título da etapa]",
        "ru": "Шаг {n}. [Введите название шага]"
    }

    CATALOG = {
        # --- Common UI ---
        "app_title": {
            "ko": "매뉴얼 스튜디오 (Manual Studio) - DragonRPA Co.",
            "en": "Manual Studio - DragonRPA Co.",
            "zh": "Manual Studio 手册工作室 - DragonRPA Co.",
            "ja": "マニュアルスタジオ (Manual Studio) - DragonRPA Co.",
            "de": "Manual Studio - DragonRPA Co.",
            "es": "Manual Studio - DragonRPA Co.",
            "fr": "Manual Studio - DragonRPA Co.",
            "pt": "Manual Studio - DragonRPA Co.",
            "ru": "Manual Studio - DragonRPA Co."
        },
        "trial_badge": {
            "ko": "[평가판]",
            "en": "[Trial]",
            "zh": "[试用版]",
            "ja": "[評価版]",
            "de": "[Testversion]",
            "es": "[Prueba]",
            "fr": "[Essai]",
            "pt": "[Avaliação]",
            "ru": "[Пробная версия]"
        },
        "licensed_badge": {
            "ko": "[정식 라이선스]",
            "en": "[Licensed]",
            "zh": "[正式授权]",
            "ja": "[正規ライセンス]",
            "de": "[Lizenziert]",
            "es": "[Con Licencia]",
            "fr": "[Sous Licence]",
            "pt": "[Licenciado]",
            "ru": "[Лицензия]"
        },
        "watermark_text": {
            "ko": "Manual Studio • 평가판 (Trial Version)",
            "en": "Manual Studio • Trial Version",
            "zh": "Manual Studio • 试用版 (Trial Version)",
            "ja": "Manual Studio • 評価版 (Trial Version)",
            "de": "Manual Studio • Testversion",
            "es": "Manual Studio • Versión de Prueba",
            "fr": "Manual Studio • Version d'Essai",
            "pt": "Manual Studio • Versão de Teste",
            "ru": "Manual Studio • Пробная Версия"
        },
        # --- Menus ---
        "menu_file": {
            "ko": "파일(F)", "en": "File(F)", "zh": "文件(F)", "ja": "ファイル(F)",
            "de": "Datei(F)", "es": "Archivo(F)", "fr": "Fichier(F)", "pt": "Arquivo(F)", "ru": "Файл(F)"
        },
        "menu_edit": {
            "ko": "편집(E)", "en": "Edit(E)", "zh": "编辑(E)", "ja": "編集(E)",
            "de": "Bearbeiten(E)", "es": "Editar(E)", "fr": "Édition(E)", "pt": "Editar(E)", "ru": "Правка(E)"
        },
        "menu_tools": {
            "ko": "도구(T)", "en": "Tools(T)", "zh": "工具(T)", "ja": "ツール(T)",
            "de": "Werkzeuge(T)", "es": "Herramientas(T)", "fr": "Outils(T)", "pt": "Ferramentas(T)", "ru": "Инструменты(T)"
        },
        "menu_settings": {
            "ko": "설정(S)", "en": "Settings(S)", "zh": "设置(S)", "ja": "設定(S)",
            "de": "Einstellungen(S)", "es": "Configuración(S)", "fr": "Paramètres(S)", "pt": "Configurações(S)", "ru": "Настройки(S)"
        },
        "menu_help": {
            "ko": "도움말(H)", "en": "Help(H)", "zh": "帮助(H)", "ja": "ヘルプ(H)",
            "de": "Hilfe(H)", "es": "Ayuda(H)", "fr": "Aide(H)", "pt": "Ajuda(H)", "ru": "Справка(H)"
        },
        "action_license_reg": {
            "ko": "라이선스 등록(L)...", "en": "License Registration(L)...", "zh": "注册许可证(L)...", "ja": "ライセンス登録(L)...",
            "de": "Lizenz registrieren(L)...", "es": "Registro de licencia(L)...", "fr": "Enregistrement licence(L)...",
            "pt": "Registro de licença(L)...", "ru": "Регистрация лицензии(L)..."
        },
        # --- Ribbon Tabs ---
        "tab_tools": {
            "ko": "도구", "en": "Tools", "zh": "工具", "ja": "ツール",
            "de": "Werkzeuge", "es": "Herramientas", "fr": "Outils", "pt": "Ferramentas", "ru": "Инструменты"
        },
        "tab_format": {
            "ko": "서식·설정", "en": "Format & Settings", "zh": "格式与设置", "ja": "書式・設定",
            "de": "Format & Optionen", "es": "Formato y Ajustes", "fr": "Format et Options", "pt": "Formato e Opções", "ru": "Формат и настройки"
        },
        # --- Group Titles ---
        "grp_capture": {
            "ko": "캡처", "en": "Capture", "zh": "截图", "ja": "キャプチャ",
            "de": "Erfassung", "es": "Captura", "fr": "Capture", "pt": "Captura", "ru": "Захват"
        },
        "grp_project": {
            "ko": "프로젝트", "en": "Project", "zh": "项目", "ja": "プロジェクト",
            "de": "Projekt", "es": "Proyecto", "fr": "Projet", "pt": "Projeto", "ru": "Проект"
        },
        "grp_select_edit": {
            "ko": "선택·편집", "en": "Select & Edit", "zh": "选择与编辑", "ja": "選択・編集",
            "de": "Auswahl & Bearbeitung", "es": "Seleccionar y Editar", "fr": "Sélection et Édition", "pt": "Selecionar e Editar", "ru": "Выбор и правка"
        },
        "grp_step_flow": {
            "ko": "단계·흐름", "en": "Steps & Flow", "zh": "步骤与流程", "ja": "手順・フロー",
            "de": "Schritte & Ablauf", "es": "Pasos y Flujo", "fr": "Étapes et Flux", "pt": "Etapas e Fluxo", "ru": "Шаги и поток"
        },
        "grp_highlight_security": {
            "ko": "강조·보안", "en": "Highlight & Privacy", "zh": "突出与隐私", "ja": "強調・プライバシー",
            "de": "Hervorhebung & Schutz", "es": "Resaltado y Privacidad", "fr": "Mise en valeur et Confidentialité", "pt": "Destaque e Privacidade", "ru": "Акцент и защита"
        },
        "grp_text_wordart": {
            "ko": "텍스트·워드아트", "en": "Text & WordArt", "zh": "文本与艺术字", "ja": "テキスト・ワードアート",
            "de": "Text & WordArt", "es": "Texto y WordArt", "fr": "Texte et WordArt", "pt": "Texto e WordArt", "ru": "Текст и WordArt"
        },
        "grp_ppt_export": {
            "ko": "PPT 출력", "en": "PPT Export", "zh": "导出PPT", "ja": "PPT出力",
            "de": "PPT-Export", "es": "Exportar a PPT", "fr": "Export PPT", "pt": "Exportar PPT", "ru": "Экспорт в PPT"
        },
        # --- Buttons & Actions ---
        "btn_fixed_capture": {
            "ko": "📷 고정 캡처 (F9)", "en": "📷 Fixed Capture (F9)", "zh": "📷 固定区域截图 (F9)", "ja": "📷 固定キャプチャ (F9)",
            "de": "📷 Feste Erfassung (F9)", "es": "📷 Captura Fija (F9)", "fr": "📷 Capture Fixe (F9)", "pt": "📷 Captura Fixa (F9)", "ru": "📷 Фикс. захват (F9)"
        },
        "btn_variable_capture": {
            "ko": "📐 영역 지정 (Shift+F9)", "en": "📐 Area Select (Shift+F9)", "zh": "📐 自选区域 (Shift+F9)", "ja": "📐 領域選択 (Shift+F9)",
            "de": "📐 Bereichswahl (Shift+F9)", "es": "📐 Seleccionar Área (Shift+F9)", "fr": "📐 Sélection Zone (Shift+F9)", "pt": "📐 Selecionar Área (Shift+F9)", "ru": "📐 Выбор области (Shift+F9)"
        },
        "btn_sub_capture": {
            "ko": "🌄 부분 추가 (F8)", "en": "🌄 Sub-Capture (F8)", "zh": "🌄 画中画追加 (F8)", "ja": "🌄 部分追加 (F8)",
            "de": "🌄 Bild-in-Bild (F8)", "es": "🌄 Agregar Imagen (F8)", "fr": "🌄 Image incrustée (F8)", "pt": "🌄 Adicionar Imagem (F8)", "ru": "🌄 Врезка (F8)"
        },
        "lbl_screen_select": {
            "ko": "화면 선택", "en": "Monitor", "zh": "屏幕选择", "ja": "画面選択",
            "de": "Bildschirm", "es": "Pantalla", "fr": "Écran", "pt": "Monitor", "ru": "Монитор"
        },
        "btn_stamp": {
            "ko": "① 번호 스탬프", "en": "① Step Stamp", "zh": "① 序号印章", "ja": "① 番号スタンプ",
            "de": "① Nummernstempel", "es": "① Sello de Paso", "fr": "① Tampon étape", "pt": "① Carimbo de Etapa", "ru": "① Номер шага"
        },
        "btn_step_arrow": {
            "ko": "①➔ 스탬프 화살표", "en": "①➔ Step Arrow", "zh": "①➔ 步骤箭头", "ja": "①➔ 手順矢印",
            "de": "①➔ Schrittpfeil", "es": "①➔ Flecha de Paso", "fr": "①➔ Flèche étape", "pt": "①➔ Seta de Etapa", "ru": "①➔ Стрелка шага"
        },
        "btn_elbow_arrow": {
            "ko": "↳ 직각 화살표", "en": "↳ Elbow Arrow", "zh": "↳ 折线箭头", "ja": "↳ 鉤型矢印",
            "de": "↳ Winkelpfeil", "es": "↳ Flecha Angular", "fr": "↳ Flèche coudée", "pt": "↳ Seta Angular", "ru": "↳ Угловая стрелка"
        },
        "btn_straight_arrow": {
            "ko": "↗ 직선 화살표", "en": "↗ Straight Arrow", "zh": "↗ 直线箭头", "ja": "↗ 直線矢印",
            "de": "↗ Gerade Pfeil", "es": "↗ Flecha Recta", "fr": "↗ Flèche droite", "pt": "↗ Seta Reta", "ru": "↗ Прямая стрелка"
        },
        "btn_box": {
            "ko": "⏹ 사각 박스", "en": "⏹ Highlight Box", "zh": "⏹ 矩形框", "ja": "⏹ 四角ボックス",
            "de": "⏹ Rechteckrahmen", "es": "⏹ Caja de Resalte", "fr": "⏹ Boîte de mise en valeur", "pt": "⏹ Caixa de Destaque", "ru": "⏹ Рамка выделения"
        },
        "btn_blur": {
            "ko": "🌫 모자이크 블러", "en": "🌫 Blur Mosaic", "zh": "🌫 马赛克模糊", "ja": "🌫 モザイクぼかし",
            "de": "🌫 Mosaik-Weichzeichner", "es": "🌫 Desenfoque Mosaico", "fr": "🌫 Flou mosaïque", "pt": "🌫 Mosaico de Desfoque", "ru": "🌫 Размытие мозаикой"
        },
        "btn_draft_stamp": {
            "ko": "📋 Draft 스탬프", "en": "📋 Draft Stamp", "zh": "📋 草稿水印", "ja": "📋 Draftスタンプ",
            "de": "📋 Entwurfsstempel", "es": "📋 Sello de Borrador", "fr": "📋 Tampon Brouillon", "pt": "📋 Carimbo de Rascunho", "ru": "📋 Штамп черновика"
        },
        "btn_callout": {
            "ko": "💬 설명 말풍선", "en": "💬 Callout Bubble", "zh": "💬 说明气泡", "ja": "💬 説明吹き出し",
            "de": "💬 Hinweiskallout", "es": "💬 Bocadillo Informativo", "fr": "💬 Légende bulle", "pt": "💬 Balão de Informação", "ru": "💬 Выноска"
        },
        "btn_text_label": {
            "ko": "🔤 텍스트 라벨", "en": "🔤 Text Label", "zh": "🔤 文本标签", "ja": "🔤 テキストラベル",
            "de": "🔤 Textetikett", "es": "🔤 Etiqueta de Texto", "fr": "🔤 Étiquette texte", "pt": "🔤 Rótulo de Texto", "ru": "🔤 Текстовая метка"
        },
        "btn_hotkey_badge": {
            "ko": "⌨️ 단축키 뱃지", "en": "⌨️ Hotkey Badge", "zh": "⌨️ 快捷键徽章", "ja": "⌨️ ショートカットバッジ",
            "de": "⌨️ Tastenkürzel-Badge", "es": "⌨️ Atajo de Teclado", "fr": "⌨️ Badge raccourci", "pt": "⌨️ Tecla de Atalho", "ru": "⌨️ Значок горячей клавиши"
        },
        "btn_wordart": {
            "ko": "🎨 워드아트", "en": "🎨 WordArt", "zh": "🎨 艺术字", "ja": "🎨 ワードアート",
            "de": "🎨 WordArt", "es": "🎨 WordArt", "fr": "🎨 WordArt", "pt": "🎨 WordArt", "ru": "🎨 WordArt"
        },
        "btn_ppt_export": {
            "ko": "🚀 슬라이드 생성 (F10)", "en": "🚀 Export Slide (F10)", "zh": "🚀 生成幻灯片 (F10)", "ja": "🚀 スライド生成 (F10)",
            "de": "🚀 Folie erstellen (F10)", "es": "🚀 Exportar Diapositiva (F10)", "fr": "🚀 Créer Diapositive (F10)", "pt": "🚀 Exportar Slide (F10)", "ru": "🚀 Создать слайд (F10)"
        },
        "btn_ppt_fit": {
            "ko": "📐 슬라이드 맞춤", "en": "📐 Auto-Fit Slide", "zh": "📐 自动适应幻灯片", "ja": "📐 スライド自動調整",
            "de": "📐 An Folie anpassen", "es": "📐 Ajustar a Diapositiva", "fr": "📐 Ajuster à la diapositive", "pt": "📐 Ajustar ao Slide", "ru": "📐 Автоподгонка слайда"
        },
        "btn_step_renumber": {
            "ko": "🔢 Step 재정렬", "en": "🔢 Renumber Steps", "zh": "🔢 重新编号步骤", "ja": "🔢 Step番号再整列",
            "de": "🔢 Schritte nummerieren", "es": "🔢 Renumerar Pasos", "fr": "🔢 Renuméroter Étapes", "pt": "🔢 Renumerar Etapas", "ru": "🔢 Перенумерация шагов"
        },
        "chk_include_title": {
            "ko": "제목 상자", "en": "Title Box", "zh": "标题文本框", "ja": "タイトル枠",
            "de": "Titelkasten", "es": "Caja de Título", "fr": "Boîte de titre", "pt": "Caixa de Título", "ru": "Поле заголовка"
        },
        "btn_add_font": {
            "ko": "폰트 등록", "en": "Add Font", "zh": "添加字体", "ja": "フォント追加",
            "de": "Schrift hinzufügen", "es": "Añadir Fuente", "fr": "Ajouter Police", "pt": "Adicionar Fonte", "ru": "Добавить шрифт"
        },
        "btn_reverse_elbow": {
            "ko": "꺾임 반전", "en": "Flip Route", "zh": "反转拐角", "ja": "反転",
            "de": "Richtung umkehren", "es": "Invertir Ruta", "fr": "Inverser Sens", "pt": "Inverter Rota", "ru": "Инвертировать угол"
        },
        # --- Settings Dialog ---
        "settings_dialog_title": {
            "ko": "환경 설정", "en": "Preferences", "zh": "首选项设置", "ja": "環境設定",
            "de": "Einstellungen", "es": "Preferencias", "fr": "Préférences", "pt": "Preferências", "ru": "Параметры"
        },
        "sec_language": {
            "ko": "[글로벌 다국어 언어 설정]", "en": "[Global Language & Locale]", "zh": "[全局多语言设置]", "ja": "[グローバル言語設定]",
            "de": "[Sprach- & Regionaleinstellungen]", "es": "[Idioma y Región]", "fr": "[Langue et Région]", "pt": "[Idioma e Região]", "ru": "[Языковые настройки]"
        },
        "sec_autosave": {
            "ko": "[실수 방지 자동 저장 설정]", "en": "[Safety Auto-Save Settings]", "zh": "[防止丢失自动保存设置]", "ja": "[自動保存設定]",
            "de": "[Automatisches Speichern]", "es": "[Autoguardado de Seguridad]", "fr": "[Sauvegarde Automatique]", "pt": "[Salvamento Automático]", "ru": "[Автосохранение]"
        },
        "chk_autosave_enabled": {
            "ko": "백그라운드 자동 저장 활성화", "en": "Enable background auto-save", "zh": "启用后台自动保存", "ja": "バックグラウンド自動保存を有効化",
            "de": "Automatisches Speichern im Hintergrund aktivieren", "es": "Activar autoguardado en segundo plano",
            "fr": "Activer la sauvegarde automatique en arrière-plan", "pt": "Ativar salvamento automático em segundo plano", "ru": "Включить фоновое автосохранение"
        },
        "lbl_autosave_interval": {
            "ko": "자동 저장 주기 (분):", "en": "Auto-save interval (minutes):", "zh": "自动保存间隔 (分钟):", "ja": "自動保存間隔 (分):",
            "de": "Intervall für automatisches Speichern (Min.):", "es": "Intervalo de autoguardado (minutos):",
            "fr": "Intervalle de sauvegarde (minutes) :", "pt": "Intervalo de salvamento (minutos):", "ru": "Интервал автосохранения (мин):"
        },
        "sec_ppt_template": {
            "ko": "[사내 PPT 마스터 템플릿 연동]", "en": "[Corporate PPT Master Template]", "zh": "[企业PPT母版模板联动]", "ja": "[企業PPTマスターテンプレート連携]",
            "de": "[Unternehmens-PPT-Vorlage]", "es": "[Plantilla Maestra de PPT]", "fr": "[Modèle PPT d'Entreprise]", "pt": "[Modelo Mestre de PPT]", "ru": "[Корпоративный шаблон PPT]"
        },
        "lbl_ppt_template_path": {
            "ko": "마스터 템플릿 파일 (.pptx):", "en": "Master template file (.pptx):", "zh": "母版模板文件 (.pptx):", "ja": "マスターテンプレートファイル (.pptx):",
            "de": "Master-Vorlagendatei (.pptx):", "es": "Archivo de plantilla maestra (.pptx):",
            "fr": "Fichier modèle maître (.pptx) :", "pt": "Arquivo de modelo mestre (.pptx):", "ru": "Файл шаблона (.pptx):"
        },
        "btn_browse": {
            "ko": "찾아보기...", "en": "Browse...", "zh": "浏览...", "ja": "参照...",
            "de": "Durchsuchen...", "es": "Examinar...", "fr": "Parcourir...", "pt": "Procurar...", "ru": "Обзор..."
        },
        # --- License Registration Dialog ---
        "license_dialog_title": {
            "ko": "라이선스 등록", "en": "License Registration", "zh": "注册许可证", "ja": "ライセンス登録",
            "de": "Lizenzregistrierung", "es": "Registro de Licencia", "fr": "Enregistrement de Licence", "pt": "Registro de Licença", "ru": "Регистрация лицензии"
        },
        "lbl_hwid": {
            "ko": "내 PC 고유 식별자 (HWID):", "en": "Machine ID (HWID):", "zh": "本机唯一识别码 (HWID):", "ja": "固有マシンID (HWID):",
            "de": "Geräte-ID (HWID):", "es": "ID de Máquina (HWID):", "fr": "ID Machine (HWID) :", "pt": "ID da Máquina (HWID):", "ru": "Идентификатор ПК (HWID):"
        },
        "btn_copy_hwid": {
            "ko": "📋 복사", "en": "📋 Copy", "zh": "📋 复制", "ja": "📋 コピー",
            "de": "📋 Kopieren", "es": "📋 Copiar", "fr": "📋 Copier", "pt": "📋 Copiar", "ru": "📋 Копировать"
        },
        "lbl_license_key": {
            "ko": "라이선스 시리얼 키 입력:", "en": "Enter License Serial Key:", "zh": "输入许可证序列号:", "ja": "ライセンスキー入力:",
            "de": "Lizenzschlüssel eingeben:", "es": "Ingrese la Clave de Licencia:", "fr": "Entrez la Clé de Licence :", "pt": "Digite a Chave de Licença:", "ru": "Введите лицензионный ключ:"
        },
        "btn_activate": {
            "ko": "인증하기", "en": "Activate", "zh": "激活", "ja": "ライセンス認証",
            "de": "Aktivieren", "es": "Activar", "fr": "Activer", "pt": "Ativar", "ru": "Активировать"
        },
        "btn_close": {
            "ko": "닫기", "en": "Close", "zh": "关闭", "ja": "閉じる",
            "de": "Schließen", "es": "Cerrar", "fr": "Fermer", "pt": "Fechar", "ru": "Закрыть"
        },
        # --- Toast & Notification ---
        "msg_auto_saved": {
            "ko": "💾 안전 백업 완료 (자동 저장됨)", "en": "💾 Auto-saved safely in background", "zh": "💾 已自动安全备份", "ja": "💾 自動バックアップ完了",
            "de": "💾 Automatisch im Hintergrund gesichert", "es": "💾 Autoguardado con éxito", "fr": "💾 Sauvegardé automatiquement", "pt": "💾 Salvo automaticamente", "ru": "💾 Автосохранение выполнено"
        },
        "msg_restore_prompt_title": {
            "ko": "이전 작업 자동 복구", "en": "Auto-Recover Previous Work", "zh": "自动恢复上次作业", "ja": "前回作業の自動復元",
            "de": "Vorherige Arbeit wiederherstellen", "es": "Recuperar Trabajo Anterior", "fr": "Récupérer le Travail Précédent", "pt": "Recuperar Trabalho Anterior", "ru": "Восстановление работы"
        },
        "msg_restore_prompt_body": {
            "ko": "이전 비정상 종료 또는 저장되지 않은 작업 데이터가 발견되었습니다.\n복구하시겠습니까?",
            "en": "Unsaved session or recovery data from previous run was found.\nWould you like to recover it?",
            "zh": "检测到上次异常关闭或未保存的作业数据。\n是否立即恢复？",
            "ja": "前回保存されなかった作業データが見つかりました。\n復元しますか？",
            "de": "Es wurden ungespeicherte Daten der vorherigen Sitzung gefunden.\nMöchten Sie diese wiederherstellen?",
            "es": "Se encontraron datos de trabajo no guardados de la sesión anterior.\n¿Desea recuperarlos?",
            "fr": "Des données de session non enregistrées ont été trouvées.\nSouhaitez-vous les récupérer ?",
            "pt": "Dados de trabalho não salvos foram encontrados da sessão anterior.\nDeseja recuperá-los?",
            "ru": "Обнаружены несохраненные данные предыдущего сеанса.\nХотите восстановить их?"
        },
        "msg_license_success": {
            "ko": "정식 라이선스가 성공적으로 등록되었습니다!\n워터마크가 완전히 해제되었습니다.",
            "en": "License activated successfully!\nAll export watermarks have been removed.",
            "zh": "正式许可证已成功激活！\n所有水印已完全解除。",
            "ja": "ライセンスが正常に認証されました！\nウォーターマークが解除されました。",
            "de": "Lizenz erfolgreich aktiviert!\nAlle Wasserzeichen wurden entfernt.",
            "es": "¡Licencia activada con éxito!\nTodas las marcas de agua han sido eliminadas.",
            "fr": "Licence activée avec succès !\nTous les filigranes ont été supprimés.",
            "pt": "Licença ativada com sucesso!\nTodas as marcas d'água foram removidas.",
            "ru": "Лицензия успешно активирована!\nВсе водяные знаки отключены."
        }
    }

    def __init__(self, default_locale="ko"):
        self.current_locale = default_locale

    @classmethod
    def instance(cls):
        if cls._instance is None:
            detected = cls.detect_system_locale()
            cls._instance = cls(default_locale=detected)
        return cls._instance

    @classmethod
    def detect_system_locale(cls) -> str:
        """Windows OS 기본 언어 자동 감지"""
        try:
            sys_name = QLocale.system().name().lower() # e.g. "ko_kr", "en_us", "zh_cn", "ja_jp", "de_de"
            prefix = sys_name.split("_")[0]
            if prefix in cls.SUPPORTED_LOCALES:
                return prefix
        except Exception:
            pass
        return "ko"

    def set_locale(self, locale_code: str):
        if locale_code in self.SUPPORTED_LOCALES:
            self.current_locale = locale_code

    def t(self, key: str, default: str = None) -> str:
        """다국어 텍스트 조회 (현재 로케일 -> 영어 -> 기본값 순)"""
        item = self.CATALOG.get(key)
        if not item:
            return default if default is not None else key
        val = item.get(self.current_locale)
        if val:
            return val
        # Fallback to English
        val_en = item.get("en")
        if val_en:
            return val_en
        # Fallback to Korean
        val_ko = item.get("ko")
        if val_ko:
            return val_ko
        return default if default is not None else key

    def get_step_template(self, locale: str = None) -> str:
        loc = locale or self.current_locale
        return self.PPT_STEP_TEMPLATES.get(loc, "Step {n}. [Title]")

    def get_supported_locales(self):
        return self.SUPPORTED_LOCALES.copy()

    @classmethod
    def get_font_families(cls):
        return cls.FALLBACK_FONTS.copy()

    def get_locale(self) -> str:
        return self.current_locale

def t(key: str, default: str = None, locale: str = None) -> str:
    mgr = I18nManager.instance()
    if locale and locale in mgr.SUPPORTED_LOCALES:
        item = mgr.CATALOG.get(key, {})
        return item.get(locale, default or key)
    return mgr.t(key, default)

def tr(key: str, default: str = None) -> str:
    return I18nManager.instance().t(key, default)

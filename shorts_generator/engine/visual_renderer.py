# -*- coding: utf-8 -*-
import os
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

def hex_to_rgb(hex_str: str) -> tuple:
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 3:
        hex_str = ''.join(c * 2 for c in hex_str)
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

class VisualRenderer:
    def __init__(self, assets_dir: str):
        self.width = 1080
        self.height = 1920
        self.assets_dir = assets_dir
        
        # Windows Fonts
        windir = os.environ.get('WINDIR', 'C:\\Windows')
        font_bold = os.path.join(windir, 'Fonts', 'malgunbd.ttf')
        font_reg = os.path.join(windir, 'Fonts', 'malgun.ttf')
        
        self.font_hero = ImageFont.truetype(font_bold, 62)
        self.font_title = ImageFont.truetype(font_bold, 52)
        self.font_subtitle = ImageFont.truetype(font_bold, 46)
        self.font_badge = ImageFont.truetype(font_bold, 36)
        self.font_brand = ImageFont.truetype(font_bold, 30)
        self.font_body = ImageFont.truetype(font_bold, 36)
        self.font_small = ImageFont.truetype(font_reg, 28)
        
        # Load and cache assets
        self.logo_img = self._load_asset("dragon_rpa_ci.png", (60, 60))
        if not self.logo_img:
            self.logo_img = self._load_asset("symbol-512.png", (60, 60))
            
        self.cached_images = {}

    def _load_asset(self, filename: str, resize: tuple = None):
        if not filename:
            return None
        path = os.path.join(self.assets_dir, filename)
        if not os.path.exists(path):
            return None
        try:
            img = Image.open(path).convert('RGBA')
            if resize:
                img = img.resize(resize, Image.Resampling.LANCZOS)
            return img
        except Exception:
            return None

    def get_cached_asset(self, filename: str):
        if not filename:
            return None
        if filename not in self.cached_images:
            img = self._load_asset(filename)
            self.cached_images[filename] = img
        return self.cached_images[filename]

    def render_frame(self, current_time: float, total_duration: float, active_scene: dict, scenario: dict) -> Image.Image:
        """Renders a single 1080x1920 frame."""
        theme = scenario.get("theme", {})
        bg_gradient = theme.get("bg_gradient", ["#090D16", "#1E293B"])
        primary_color = hex_to_rgb(theme.get("primary_color", "#3B82F6"))
        accent_color = hex_to_rgb(theme.get("accent_color", "#FACC15"))
        
        # 1. Base Gradient Background
        c_top = hex_to_rgb(bg_gradient[0])
        c_bot = hex_to_rgb(bg_gradient[1])
        frame = Image.new('RGB', (self.width, self.height), c_top)
        draw = ImageDraw.Draw(frame)
        
        # Vertical gradient
        for y in range(0, self.height, 2):
            ratio = y / self.height
            r = int(c_top[0] + (c_bot[0] - c_top[0]) * ratio)
            g = int(c_top[1] + (c_bot[1] - c_top[1]) * ratio)
            b = int(c_top[2] + (c_bot[2] - c_top[2]) * ratio)
            draw.line([(0, y), (self.width, y)], fill=(r, g, b), width=2)
            
        # Scene timing & progress
        scene_start = active_scene.get("start_time", 0.0)
        scene_dur = max(0.1, active_scene.get("duration", 5.0))
        scene_progress = min(1.0, max(0.0, (current_time - scene_start) / scene_dur))
        
        # 2. Top Header Brand Bar (Y: 60 ~ 150)
        brand_y = 90
        brand_text = "DRAGON RPA | 매뉴얼 스튜디오"
        pill_w = 560
        pill_h = 60
        pill_x0 = (self.width - pill_w) // 2
        pill_y0 = brand_y - pill_h // 2
        draw.rounded_rectangle(
            [(pill_x0, pill_y0), (pill_x0 + pill_w, pill_y0 + pill_h)],
            radius=30,
            fill=(15, 23, 42),
            outline=(51, 65, 85),
            width=2
        )
        
        if self.logo_img:
            logo_small = self.logo_img.resize((38, 38), Image.Resampling.LANCZOS)
            frame.paste(logo_small, (pill_x0 + 16, pill_y0 + 11), logo_small)
            draw.text((pill_x0 + 66, brand_y), brand_text, font=self.font_brand, fill="#E2E8F0", anchor="lm")
        else:
            draw.text((self.width // 2, brand_y), brand_text, font=self.font_brand, fill="#E2E8F0", anchor="mm")
            
        # 3. Scene Badge (Y: 180 ~ 260)
        badge_text = active_scene.get("badge", "")
        if badge_text:
            badge_w = 480
            badge_h = 68
            badge_x0 = (self.width - badge_w) // 2
            badge_y0 = 175
            pulse = math.sin(scene_progress * math.pi * 4) * 0.5 + 0.5
            badge_border = (
                int(primary_color[0] * (0.6 + 0.4 * pulse)),
                int(primary_color[1] * (0.6 + 0.4 * pulse)),
                int(primary_color[2] * (0.6 + 0.4 * pulse))
            )
            draw.rounded_rectangle(
                [(badge_x0, badge_y0), (badge_x0 + badge_w, badge_y0 + badge_h)],
                radius=34,
                fill=(30, 41, 59),
                outline=badge_border,
                width=3
            )
            draw.text((self.width // 2, badge_y0 + badge_h // 2), badge_text, font=self.font_badge, fill="#F8FAFC", anchor="mm")

        # 4. Main Headline (Y: 290 ~ 380)
        title_main = active_scene.get("title_main", "")
        if title_main:
            draw.text((self.width // 2 + 2, 332), title_main, font=self.font_hero, fill=(0, 0, 0), anchor="mm")
            draw.text((self.width // 2, 330), title_main, font=self.font_hero, fill="#FFFFFF", anchor="mm")

        # 5. Central Hero Stage (Y: 420 ~ 1380)
        stage_box = (70, 420, 1010, 1380)
        self._render_stage_content(frame, draw, stage_box, active_scene, scene_progress, primary_color, accent_color)

        # 6. Bottom Subtitle Box (Y: 1420 ~ 1760)
        subtitle_lines = active_scene.get("subtitle_lines", [])
        highlights = active_scene.get("highlight_words", [])
        self._render_subtitles(frame, draw, (70, 1420, 1010, 1760), subtitle_lines, highlights, theme)

        # 7. Bottom Progress Bar (Y: 1905 ~ 1920)
        total_prog = min(1.0, max(0.0, current_time / max(1.0, total_duration)))
        bar_w = int(self.width * total_prog)
        draw.rectangle([(0, 1908), (self.width, 1920)], fill=(30, 41, 59))
        draw.rectangle([(0, 1908), (bar_w, 1920)], fill=primary_color)
        
        return frame

    def _render_stage_content(self, frame, draw, box, scene, progress, primary_color, accent_color):
        x0, y0, x1, y1 = box
        w = x1 - x0
        h = y1 - y0
        visual_type = scene.get("visual_type", "ui_demo")
        image_asset = scene.get("image_asset")
        
        if visual_type == "problem":
            draw.rounded_rectangle([(x0, y0), (x1, y1)], radius=28, fill=(15, 23, 42), outline=(239, 68, 68), width=4)
            
            draw.text((x0 + w // 2, y0 + 130), "⚠️", font=self.font_hero, anchor="mm")
            draw.text((x0 + w // 2, y0 + 220), "기존 매뉴얼 작업의 현실", font=self.font_title, fill="#EF4444", anchor="mm")
            
            # Comparison cards
            c1_y = y0 + 310
            draw.rounded_rectangle([(x0 + 40, c1_y), (x1 - 40, c1_y + 240)], radius=18, fill=(30, 41, 59), outline=(239, 68, 68), width=2)
            draw.text((x0 + 70, c1_y + 45), "❌ 기존 캡처 도구 방식", font=self.font_body, fill="#F87171", anchor="lm")
            draw.text((x0 + 70, c1_y + 110), "• 화면 캡처 ➔ 그림판 ➔ 번호 그리기", font=self.font_small, fill="#E2E8F0", anchor="lm")
            draw.text((x0 + 70, c1_y + 175), "• 50페이지 작성 시 3~4시간 야근 확정!", font=self.font_small, fill="#FCA5A5", anchor="lm")
            
            c2_y = c1_y + 280
            draw.rounded_rectangle([(x0 + 40, c2_y), (x1 - 40, c2_y + 240)], radius=18, fill=(16, 185, 129, 40), outline=(16, 185, 129), width=2)
            draw.text((x0 + 70, c2_y + 45), "✅ 매뉴얼 스튜디오 솔루션", font=self.font_body, fill="#34D399", anchor="lm")
            draw.text((x0 + 70, c2_y + 110), "• 평소처럼 클릭만 하면 자동 캡처 & 태깅", font=self.font_small, fill="#E2E8F0", anchor="lm")
            draw.text((x0 + 70, c2_y + 175), "• 1분 완성으로 정시 칼퇴 실현!", font=self.font_small, fill="#A7F3D0", anchor="lm")
            
        elif visual_type == "cta":
            draw.rounded_rectangle([(x0, y0), (x1, y1)], radius=28, fill=(15, 23, 42), outline=primary_color, width=3)
            
            app_img = self.get_cached_asset(image_asset or "preview_about.png")
            if app_img:
                img_w = w - 80
                img_h = int(img_w * (app_img.height / app_img.width))
                if img_h > 460:
                    img_h = 460
                    img_w = int(img_h * (app_img.width / app_img.height))
                app_resized = app_img.resize((img_w, img_h), Image.Resampling.LANCZOS).convert('RGBA')
                paste_x = x0 + (w - img_w) // 2
                paste_y = y0 + 50
                frame.paste(app_resized, (paste_x, paste_y), app_resized)
                
            btn_w = w - 100
            btn_h = 100
            btn_x0 = x0 + 50
            btn_y0 = y1 - 280
            draw.rounded_rectangle(
                [(btn_x0, btn_y0), (btn_x0 + btn_w, btn_y0 + btn_h)],
                radius=50,
                fill=primary_color
            )
            draw.text((x0 + w // 2, btn_y0 + btn_h // 2), "📥 무료 다운로드 바로가기", font=self.font_title, fill="#FFFFFF", anchor="mm")
            
            dom_y = btn_y0 + 130
            draw.rounded_rectangle(
                [(btn_x0, dom_y), (btn_x0 + btn_w, dom_y + 70)],
                radius=20,
                fill=(30, 41, 59),
                outline=(71, 85, 105),
                width=2
            )
            draw.text((x0 + w // 2, dom_y + 35), "🌐 www.dragonrpa.co.kr/manual-studio", font=self.font_badge, fill="#38BDF8", anchor="mm")
            
        else:
            draw.rounded_rectangle([(x0, y0), (x1, y1)], radius=24, fill=(15, 23, 42), outline=primary_color, width=3)
            
            # Chrome Header
            chrome_h = 56
            draw.rounded_rectangle([(x0, y0), (x1, y0 + chrome_h)], radius=24, fill=(30, 41, 59))
            draw.rectangle([(x0, y0 + chrome_h - 10), (x1, y0 + chrome_h)], fill=(30, 41, 59))
            
            draw.ellipse([(x0 + 24, y0 + 18), (x0 + 44, y0 + 38)], fill=(239, 68, 68))
            draw.ellipse([(x0 + 54, y0 + 18), (x0 + 74, y0 + 38)], fill=(234, 179, 8))
            draw.ellipse([(x0 + 84, y0 + 18), (x0 + 104, y0 + 38)], fill=(34, 197, 94))
            draw.text((x0 + w // 2, y0 + 28), "Manual Studio v1.2.0 - 작업 캔버스", font=self.font_small, fill="#94A3B8", anchor="mm")
            
            # UI Screenshot with Zoom
            ui_img = self.get_cached_asset(image_asset or "preview_studio.png")
            if ui_img:
                inner_w = w - 16
                inner_h = h - chrome_h - 16
                inner_x = x0 + 8
                inner_y = y0 + chrome_h + 8
                
                zoom = 1.0 + 0.15 * progress
                crop_w = int(ui_img.width / zoom)
                crop_h = int(ui_img.height / zoom)
                crop_x = (ui_img.width - crop_w) // 2
                crop_y = int((ui_img.height - crop_h) * (0.3 + 0.4 * progress))
                
                cropped = ui_img.crop((crop_x, crop_y, crop_x + crop_w, crop_y + crop_h))
                scaled = cropped.resize((inner_w, inner_h), Image.Resampling.LANCZOS).convert('RGBA')
                frame.paste(scaled, (inner_x, inner_y), scaled)
                
            badge_y = y1 - 90
            draw.rounded_rectangle([(x0 + 30, badge_y), (x1 - 30, badge_y + 64)], radius=32, fill=(15, 23, 42, 230), outline=accent_color, width=2)
            draw.text((x0 + w // 2, badge_y + 32), "⚡ 마우스 클릭 즉시 번호 태그 자동 생성", font=self.font_badge, fill="#FACC15", anchor="mm")

    def _render_subtitles(self, frame, draw, box, subtitle_lines, highlights, theme):
        x0, y0, x1, y1 = box
        w = x1 - x0
        h = y1 - y0
        
        draw.rounded_rectangle([(x0, y0), (x1, y1)], radius=28, fill=(15, 23, 42), outline=(59, 130, 246), width=3)
        
        if not subtitle_lines:
            return
            
        line_count = len(subtitle_lines)
        line_h = 74
        start_y = y0 + (h - line_count * line_h) // 2 + 37
        
        for idx, line in enumerate(subtitle_lines):
            curr_y = start_y + idx * line_h
            self._draw_highlighted_line(draw, line, (self.width // 2, curr_y), highlights)

    def _draw_highlighted_line(self, draw, line_text: str, center_pos: tuple, highlights: list):
        cx, cy = center_pos
        matched_highlight = None
        for h in highlights:
            if h in line_text:
                matched_highlight = h
                break
                
        if not matched_highlight:
            draw.text((cx + 2, cy + 2), line_text, font=self.font_subtitle, fill=(0, 0, 0), anchor="mm")
            draw.text((cx, cy), line_text, font=self.font_subtitle, fill="#FFFFFF", anchor="mm")
        else:
            parts = line_text.split(matched_highlight, 1)
            before_txt = parts[0]
            hl_txt = matched_highlight
            after_txt = parts[1] if len(parts) > 1 else ""
            
            bbox_before = self.font_subtitle.getbbox(before_txt) if before_txt else (0, 0, 0, 0)
            w_before = (bbox_before[2] - bbox_before[0]) if before_txt else 0
            
            bbox_hl = self.font_subtitle.getbbox(hl_txt)
            w_hl = bbox_hl[2] - bbox_hl[0]
            
            bbox_after = self.font_subtitle.getbbox(after_txt) if after_txt else (0, 0, 0, 0)
            w_after = (bbox_after[2] - bbox_after[0]) if after_txt else 0
            
            total_w = w_before + w_hl + w_after
            start_x = cx - total_w // 2
            
            curr_x = start_x
            if before_txt:
                draw.text((curr_x + 2, cy + 2), before_txt, font=self.font_subtitle, fill=(0, 0, 0), anchor="lm")
                draw.text((curr_x, cy), before_txt, font=self.font_subtitle, fill="#FFFFFF", anchor="lm")
                curr_x += w_before
                
            draw.text((curr_x + 2, cy + 2), hl_txt, font=self.font_subtitle, fill=(0, 0, 0), anchor="lm")
            draw.text((curr_x, cy), hl_txt, font=self.font_subtitle, fill="#FACC15", anchor="lm")
            curr_x += w_hl
            
            if after_txt:
                draw.text((curr_x + 2, cy + 2), after_txt, font=self.font_subtitle, fill=(0, 0, 0), anchor="lm")
                draw.text((curr_x, cy), after_txt, font=self.font_subtitle, fill="#FFFFFF", anchor="lm")

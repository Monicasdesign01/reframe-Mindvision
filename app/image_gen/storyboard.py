"""
Composes three generated panel images plus their narrative captions into a
single storyboard illustration: CURRENT REALITY / REFRAME / DESIRED FUTURE
as three side-by-side panels, with a NEXT STEP banner underneath.

Built with Pillow only, no additional model -- this is layout/typesetting
("our own engineering"), not generation, so it stays within the project's
documented scope of five pretrained models (see DESIGN.md) plus this app's
own code around them. SD-Turbo cannot reliably render in-image text or keep
a character consistent across separate generations, so both the captions
and the panel arrangement are drawn here instead of asked of the model.
"""

import textwrap

from PIL import Image, ImageDraw, ImageFont

_PANEL_SIZE = 256
_MARGIN = 20
_GAP = 20
_HEADER_H = 40
_SUBTITLE_H = 28
_CAPTION_H = 190
_BANNER_H = 90

# (header background, header/subtitle text color) per panel, soft pastel to
# match the calm, non-alarming tone required of everything shown to a user
# in distress (same intent as the narrative generator's tone constraints).
_PALETTE = [
    ((247, 214, 212), (150, 45, 45)),   # 1. current reality -- soft red
    ((210, 227, 248), (35, 65, 125)),   # 2. reframe -- soft blue
    ((214, 236, 217), (35, 100, 55)),   # 3. desired future -- soft green
]
_BANNER_BG = (231, 220, 246)
_BANNER_FG = (85, 55, 125)
_CAPTION_BG = (250, 248, 244)
_CAPTION_FG = (55, 55, 55)
_BG = (255, 252, 247)

_TITLES = ["1. CURRENT REALITY", "2. REFRAME", "3. DESIRED FUTURE"]
_PART_KEYS = ["current_reality", "reframe", "desired_future"]


def _load_font(bold: bool, size: int) -> ImageFont.FreeTypeFont:
    candidates = ["segoeuib.ttf", "arialbd.ttf"] if bold else ["segoeui.ttf", "arial.ttf"]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap_and_draw(draw, text, font, box, fill, line_spacing=4):
    x0, y0, x1, y1 = box
    max_width = x1 - x0
    avg_char_w = font.getlength("n") or 7
    wrap_chars = max(10, int(max_width / avg_char_w))
    lines = []
    for paragraph in (text or "").split("\n"):
        lines.extend(textwrap.wrap(paragraph, width=wrap_chars) or [""])
    y = y0
    line_h = getattr(font, "size", 13) + line_spacing
    for line in lines:
        if y + line_h > y1:
            break
        draw.text((x0, y), line, font=font, fill=fill)
        y += line_h


def compose_storyboard(panel_paths: list, subtitles: list, narrative_parts: dict, out_path: str) -> str:
    total_w = _MARGIN * 2 + _PANEL_SIZE * 3 + _GAP * 2
    total_h = (
        _MARGIN + _HEADER_H + _SUBTITLE_H + _PANEL_SIZE + _CAPTION_H + _GAP + _BANNER_H + _MARGIN
    )

    canvas = Image.new("RGB", (total_w, total_h), _BG)
    draw = ImageDraw.Draw(canvas)

    title_font = _load_font(bold=True, size=16)
    subtitle_font = _load_font(bold=False, size=13)
    caption_font = _load_font(bold=False, size=13)
    banner_title_font = _load_font(bold=True, size=15)
    banner_font = _load_font(bold=False, size=13)

    x = _MARGIN
    y0 = _MARGIN
    for i in range(3):
        header_bg, header_fg = _PALETTE[i]

        draw.rectangle([x, y0, x + _PANEL_SIZE, y0 + _HEADER_H], fill=header_bg)
        draw.text((x + 10, y0 + 10), _TITLES[i], font=title_font, fill=header_fg)

        sub_y = y0 + _HEADER_H
        draw.rectangle([x, sub_y, x + _PANEL_SIZE, sub_y + _SUBTITLE_H], fill=header_bg)
        draw.text((x + 10, sub_y + 6), subtitles[i], font=subtitle_font, fill=header_fg)

        img_y = sub_y + _SUBTITLE_H
        panel_img = Image.open(panel_paths[i]).convert("RGB").resize((_PANEL_SIZE, _PANEL_SIZE))
        canvas.paste(panel_img, (x, img_y))

        cap_y = img_y + _PANEL_SIZE
        draw.rectangle([x, cap_y, x + _PANEL_SIZE, cap_y + _CAPTION_H], fill=_CAPTION_BG)
        caption_text = narrative_parts.get(_PART_KEYS[i], "")
        _wrap_and_draw(
            draw, caption_text, caption_font,
            (x + 10, cap_y + 8, x + _PANEL_SIZE - 10, cap_y + _CAPTION_H - 8),
            _CAPTION_FG,
        )

        x += _PANEL_SIZE + _GAP

    banner_y = _MARGIN + _HEADER_H + _SUBTITLE_H + _PANEL_SIZE + _CAPTION_H + _GAP
    banner_w = total_w - _MARGIN * 2
    draw.rectangle([_MARGIN, banner_y, _MARGIN + banner_w, banner_y + _BANNER_H], fill=_BANNER_BG)
    draw.text((_MARGIN + 15, banner_y + 10), "NEXT STEP", font=banner_title_font, fill=_BANNER_FG)
    _wrap_and_draw(
        draw, narrative_parts.get("next_step", ""), banner_font,
        (_MARGIN + 15, banner_y + 32, _MARGIN + banner_w - 15, banner_y + _BANNER_H - 6),
        _BANNER_FG,
    )

    canvas.save(out_path)
    return out_path

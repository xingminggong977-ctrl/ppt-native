# -*- coding: utf-8 -*-
"""minimal-ink — a quiet editorial theme in ink green, cream paper and gold.

Everything visual lives here: palette, type scale, header/footer/card/band
styles, and the page background.  ``scripts/primitives.py`` reads these dicts
and never hard-codes a colour or a font size.

Swap or copy this file to build another theme.  The only contract is:

    THEME.font          {"family", "regular", "bold"}
    THEME.colors        palette used by the theme and by decks
    THEME.size          font-size ladder
    THEME.head/foot/card/band/photo/image_frame   style dicts
    THEME.background(image_href=None)             SVG background fragment
"""
from __future__ import annotations

NAME = "minimal-ink"
TITLE = "极简墨绿"
DESCRIPTION = "墨绿 + 米白 + 金色细线；适合汇报、总结、评审类中文长文。"

# ------------------------------------------------------------------ fonts
# Width measurement uses these files; the family name is written into the SVG.
# On a machine without Microsoft YaHei, point these at any CJK font you have.
FONT = {
    "family": "Microsoft YaHei",
    "regular": r"C:\Windows\Fonts\msyh.ttc",
    "bold": r"C:\Windows\Fonts\msyhbd.ttc",
}

# ------------------------------------------------------------------ palette
COLORS = {
    # ink greens
    "primary": "#0E3A2B",
    "primary_mid": "#2E7D5B",
    "on_primary": "#F5F1E6",
    "on_primary_soft": "#93AC9E",
    "on_primary_faint": "#7C9887",
    # paper
    "paper": "#FAF7F1",
    "paper_deep": "#F2ECDF",
    "card": "#FFFFFF",
    "tint": "#E9EFE7",
    "edge": "#E4DBC9",
    "ghost": "#E7EBE4",
    # text
    "ink": "#1F2E27",
    "ink_soft": "#4C5B53",
    "muted": "#8E9992",
    # accents
    "accent": "#B4883A",
    "accent_light": "#D8B96E",
    "danger": "#B1362A",
    # placeholders
    "placeholder": "#E3E3DC",
    "placeholder_edge": "#A8AEA7",
    "placeholder_text": "#6E7873",
}

# ------------------------------------------------------------------ type scale
SIZE = {
    "display": 64,
    "title": 50,
    "h1": 42,
    "h2": 39,
    "h3": 34,
    "h4": 32,
    "lead": 30,
    "body": 26,
    "body_s": 25,
    "small": 24,
    "caption": 23,
    "meta": 21,
    "label": 19,
    "micro": 16,
    "submicro": 14,
    "ghost_num": 190,
}

# ------------------------------------------------------------------ block styles
HEAD = {
    "x": 60,
    "kicker_y": 74, "kicker_size": SIZE["meta"], "kicker_fill": COLORS["accent"],
    "kicker_ls": "2",
    "title_y": 134, "title_size": SIZE["title"], "title_fill": COLORS["primary"],
    "rule_y": 172, "rule_w": 68, "rule_h": 4, "rule_fill": COLORS["accent"],
    "num_x": 1220, "num_y": 210, "num_size": SIZE["ghost_num"],
    "num_fill": COLORS["ghost"],
}

FOOT = {
    "x": 1223, "y": 694, "size": SIZE["label"], "fill": COLORS["muted"],
    "anchor": "end", "suffix": "",
}

CARD = {
    "fill": COLORS["tint"],
    "bar": COLORS["primary_mid"], "bar_w": 6,
    "title_x": 30, "title_y": 48,
    "title_size": SIZE["meta"], "title_fill": COLORS["accent"],
    "title_weight": "700", "title_ls": "2",
    "body_y": 96, "body_size": SIZE["caption"], "body_fill": COLORS["ink"],
    "lh_ratio": 1.35, "para_gap": 8, "right_pad": 28,
}

BAND = {
    "fill": COLORS["tint"],
    "bar": COLORS["primary_mid"], "bar_w": 6,
    "x_pad": 36,
    "first_y": 40, "title_size": SIZE["meta"], "title_fill": COLORS["accent"],
    "title_weight": "700", "title_ls": "2", "title_gap": 52,
    "line_size": SIZE["small"], "line_fill": COLORS["ink"], "lh_ratio": 1.35,
}

PHOTO = {
    "fill": COLORS["placeholder"], "edge": COLORS["placeholder_edge"],
    "edge_w": 2, "dash": "12 9",
    "label_size": SIZE["small"], "label_fill": COLORS["placeholder_text"],
    "sub_size": 18, "sub_fill": COLORS["placeholder_text"],
    "sub_gap": 30, "sub": "（示意占位，可替换为真实图片）",
}

IMAGE_FRAME = {"fill": COLORS["card"], "stroke": COLORS["edge"],
               "sw": 1, "pad": 2}

# A thin wash over a photographic background keeps text legible.  Set the
# opacity to 0 to show the image untouched.
BG_IMAGE_SCRIM = {"fill": COLORS["paper"], "opacity": 0.16}


class Theme:
    name = NAME
    title = TITLE
    description = DESCRIPTION
    font = FONT
    colors = COLORS
    size = SIZE
    head = HEAD
    foot = FOOT
    card = CARD
    band = BAND
    photo = PHOTO
    image_frame = IMAGE_FRAME

    def background(self, image_href: str | None = None,
                   width: int = 1280, height: int = 720) -> str:
        """Page background: optional full-bleed image, else a paper gradient."""
        if image_href:
            parts = [
                '<image id="bg" href="%s" x="0" y="0" width="%d" height="%d" '
                'preserveAspectRatio="xMidYMid meet" '
                'data-pptx-role="background"/>' % (image_href, width, height)
            ]
            scrim = BG_IMAGE_SCRIM
            if scrim and scrim.get("opacity"):
                parts.append(
                    '<rect id="bg-scrim" x="0" y="0" width="%d" height="%d" fill="%s" '
                    'fill-opacity="%s" data-pptx-role="decoration"/>'
                    % (width, height, scrim["fill"], scrim["opacity"])
                )
            return "\n".join(parts)

        return (
            '<defs>\n'
            '<linearGradient id="page-bg" x1="0" y1="0" x2="1" y2="1">\n'
            '<stop offset="0" stop-color="%s"/>\n'
            '<stop offset="1" stop-color="%s"/>\n'
            '</linearGradient>\n'
            '</defs>\n'
            '<rect id="bg" x="0" y="0" width="%d" height="%d" '
            'fill="url(#page-bg)" data-pptx-role="background"/>'
            % (COLORS["paper"], COLORS["paper_deep"], width, height)
        )


THEME = Theme()

# -*- coding: utf-8 -*-
"""guochao — ink black, hairline gold, seal red and brush-written display type.

Everything visual lives here: palette, type scale, header/footer/card/band
styles, the font chains (with a fallback stack), and the page background.
``scripts/primitives.py`` never hard-codes a colour, a font family or a size.

The contract, identical to every other theme::

    THEME.font          {"family", "regular", "bold"}
    THEME.colors        palette used by the theme and by decks
    THEME.size          font-size ladder
    THEME.head/foot/card/band/photo/image_frame   style dicts
    THEME.background(image_href=None)             SVG background fragment

plus two additions this theme needs:

    THEME.font_for(role)      comma separated family chain for one text run
    THEME.use_font_fallback() swap every brush face for a plain one

Rules taken from ``docs/guochao-theme-spec.md``:

* seven colours only — ``INK_DEEP/INK/GOLD/GOLD_LIGHT/RED/PAPER/MUTED`` —
  plus the radial centre ``#2A241C``; red never covers more than ~3% of a page
  (it is the seal only);
* the brush face (华文行楷) is only used at 40pt and above, i.e. ``display``,
  ``chapter`` and ``thanks`` in the ladder below;
* no background image ⇒ a gradient, never a white page.
"""
from __future__ import annotations

import os
import sys

NAME = "guochao"
TITLE = "国潮"
DESCRIPTION = ("墨底 + 金线 + 朱红印章；行楷大标题、深色弧边面板，"
               "适合品牌提案、文化专题与需要气场的中文演示。")

# ------------------------------------------------------------------ fonts
# 1px = 0.75pt throughout this repo, so a spec value of N pt is 4N/3 px.

# Every chain starts with the Chinese family name because that is what a user
# sees in PowerPoint's font box.  It is followed by the same face's English
# alias: the SVG->DrawingML converter only recognises Latin aliases as CJK
# fonts (``STXingkai``, ``STXinwei``, ``KaiTi``, ``SimHei`` …), so without the
# alias the Chinese glyphs would silently fall back to the body face.
FONT_CHAINS = {
    # 毛笔 — display sizes only (>= 40pt)
    "display": ["华文行楷", "STXingkai", "楷体", "KaiTi"],
    # 次级标题
    "subhead": ["华文新魏", "STXinwei", "黑体", "SimHei"],
    # 正文
    "body": ["Microsoft YaHei", "SimHei", "SimSun"],
    # 数字 / 英文 only — never a chain containing CJK glyphs
    "latin": ["Segoe UI", "Arial"],
}

# Plain, always-installed faces, used when the brush fonts are missing or when
# ``--font-fallback`` is on.  Order matters: the first CJK entry becomes the
# East Asian typeface of the run.
FONT_CHAINS_FALLBACK = {
    "display": ["楷体", "KaiTi", "黑体", "SimHei"],
    "subhead": ["黑体", "SimHei", "KaiTi"],
    "body": ["Microsoft YaHei", "SimHei", "SimSun"],
    "latin": ["Segoe UI", "Arial"],
}

# Font files probed at import time.  The first existing file decides whether
# the brush face is really installed here, which lets a machine without the
# 华文 pack keep working instead of silently shipping a broken deck.
FONT_PROBE = {
    "display": ["STXINGKA.TTF", "STLITI.TTF", "simkai.ttf"],
    "subhead": ["STXINWEI.TTF", "STKAITI.TTF", "simhei.ttf"],
}
FONT_DIRS = [os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")]

# Width measurement (post_fix.py, wrap_text) uses these files, not the chain.
FONT_FILE_CANDIDATES = {
    "regular": ["msyh.ttc", "simhei.ttf", "simsun.ttc"],
    "bold": ["msyhbd.ttc", "simhei.ttf", "simsun.ttc"],
}

_FALLBACK_ON = False
FONT_NOTES = []


def _font_path(filename):
    for directory in FONT_DIRS:
        candidate = os.path.join(directory, filename)
        if os.path.exists(candidate):
            return candidate
    return None


def _first_installed(filenames):
    for filename in filenames:
        found = _font_path(filename)
        if found:
            return found
    return None


def font_for(role="body"):
    """Comma separated family chain for one text run of ``role``.

    Returns an empty string for an unknown role so callers can pass the result
    straight into ``T(..., font=...)``.
    """
    table = FONT_CHAINS_FALLBACK if _FALLBACK_ON else FONT_CHAINS
    chain = table.get(role) or ()
    return ", ".join(chain)


def use_font_fallback(enabled=True):
    """Drop the brush faces for plain ones (``--font-fallback``)."""
    global _FALLBACK_ON
    _FALLBACK_ON = bool(enabled)
    if _FALLBACK_ON:
        FONT_NOTES.append("font fallback forced: display=%s"
                          % FONT_CHAINS_FALLBACK["display"][0])


def font_fallback_on():
    return _FALLBACK_ON


_regular = _first_installed(FONT_FILE_CANDIDATES["regular"])
_bold = _first_installed(FONT_FILE_CANDIDATES["bold"]) or _regular

# The measurement face stays 微软雅黑 (the spec's body face) whenever it is
# installed; the chain written into the SVG is what changes on fallback.
FONT = {
    "family": "Microsoft YaHei",
    "regular": _regular,
    "bold": _bold,
}

if not _first_installed(FONT_PROBE["display"]):
    # Missing 华文行楷 must not break the build: degrade to 楷体 and say so.
    _FALLBACK_ON = True
    FONT_NOTES.append(
        "华文行楷/STXINGKA.TTF not found in %s — falling back to %s"
        % (", ".join(FONT_DIRS), FONT_CHAINS_FALLBACK["display"][0]))
    sys.stderr.write("[theme guochao] %s\n" % FONT_NOTES[-1])

# ------------------------------------------------------------------ palette
# Seven colours, nothing else.  Semantic keys below repeat these values so the
# shared primitives (HEAD/CARD/BAND/FOOT) keep their usual names.
COLORS = {
    # 墨
    "ink_deep": "#0E0C0A",
    "ink": "#1A1613",
    "ink_center": "#2A241C",   # radial centre of the no-image background
    # 金
    "gold": "#C9A227",
    "gold_light": "#E8CE8F",
    # 朱红 — seal only
    "red": "#B1362A",
    # 宣纸
    "paper": "#F5F1E6",
    "muted": "#A79E8C",

    # --- semantic aliases used by the shared block styles
    "primary": "#0E0C0A",
    "primary_mid": "#1A1613",
    "on_primary": "#F5F1E6",
    "on_primary_soft": "#A79E8C",
    "on_primary_faint": "#A79E8C",
    "paper_deep": "#1A1613",
    "card": "#0E0C0A",          # recessed card on the ink panel
    "tint": "#0E0C0A",
    "edge": "#E8CE8F",          # hairlines are gold, never grey
    "ghost": "#1A1613",         # ghost numerals sit one step above the page
    "ink_text": "#F5F1E6",
    "accent": "#C9A227",
    "accent_light": "#E8CE8F",
    "danger": "#B1362A",
    "placeholder": "#1A1613",
    "placeholder_edge": "#C9A227",
    "placeholder_text": "#A79E8C",
}

# ------------------------------------------------------------------ type scale
# 1px = 0.75pt.  display 84px = 63pt, chapter 74px = 56pt, h1 42px = 32pt,
# lead 32px = 24pt, body 24px = 18pt, small 19px = 14pt, micro 16px = 12pt.
SIZE = {
    "display": 84,     # 封面主标题 60–72pt
    "chapter": 74,     # 章节名 56pt
    "thanks": 85,      # 结尾 64pt
    "title": 50,
    "h1": 42,          # 面板标题 32pt
    "h2": 39,
    "h3": 34,
    "h4": 32,
    "lead": 32,        # 副标题 24pt
    "body": 24,        # 正文 18pt
    "body_s": 26,      # 正文 20pt
    "small": 19,       # 小标签 14pt
    "caption": 21,
    "meta": 18,
    "label": 19,
    "micro": 16,       # 页码 12pt
    "submicro": 14,
    "ghost_num": 190,
}

# ------------------------------------------------------------------ block styles
HEAD = {
    "x": 60,
    "kicker_y": 74, "kicker_size": SIZE["small"], "kicker_fill": COLORS["gold"],
    "kicker_ls": "3",
    "title_y": 142, "title_size": SIZE["h1"], "title_fill": COLORS["paper"],
    "rule_y": 178, "rule_w": 64, "rule_h": 2, "rule_fill": COLORS["gold"],
    "num_x": 1220, "num_y": 214, "num_size": SIZE["ghost_num"],
    "num_fill": COLORS["ghost"],
}

FOOT = {
    "x": 1223, "y": 694, "size": SIZE["micro"], "fill": COLORS["muted"],
    "anchor": "end", "suffix": "",
}

CARD = {
    "fill": COLORS["card"],
    "bar": COLORS["gold"], "bar_w": 4,
    "title_x": 30, "title_y": 46,
    "title_size": SIZE["small"], "title_fill": COLORS["gold"],
    "title_weight": "700", "title_ls": "3",
    "body_y": 92, "body_size": SIZE["caption"], "body_fill": COLORS["paper"],
    "lh_ratio": 1.6, "para_gap": 8, "right_pad": 28,
}

BAND = {
    "fill": COLORS["card"],
    "bar": COLORS["gold"], "bar_w": 4,
    "x_pad": 36,
    "first_y": 40, "title_size": SIZE["small"], "title_fill": COLORS["gold"],
    "title_weight": "700", "title_ls": "3", "title_gap": 50,
    "line_size": SIZE["caption"], "line_fill": COLORS["paper"], "lh_ratio": 1.6,
}

PHOTO = {
    "fill": COLORS["placeholder"], "edge": COLORS["placeholder_edge"],
    "edge_w": 1, "dash": "10 8",
    "label_size": SIZE["small"], "label_fill": COLORS["placeholder_text"],
    "sub_size": 17, "sub_fill": COLORS["placeholder_text"],
    "sub_gap": 30, "sub": "（示意占位，可替换为真实图片）",
}

IMAGE_FRAME = {"fill": COLORS["ink"], "stroke": COLORS["gold_light"],
               "sw": 1, "pad": 2}

# Spec: a 30% #0E0C0A wash over a photographic background.  Raise it to ~0.5
# if your image is bright — PAPER text needs the dark half of the page.
BG_IMAGE_SCRIM = {"fill": COLORS["ink_deep"], "opacity": 0.30}

# Fallback ladder for a page with no image (spec §5):
#   "radial" — centre #2A241C fading to #0E0C0A (the preferred look)
#   "linear" — ink_deep → ink, diagonal, plus cloud motifs
#   "flat"   — plain ink_deep
BG_MODE = "radial"

# The right-hand content panel: a full-height block pinned to the right edge
# whose left flank is one long concave sweep.  ``arc`` is the ARC_PANEL shape;
# the inner text column stays clear of the sweep below y=520.
PANEL = {
    "x": 600, "y": 0, "w": 680, "h": 720,
    "fill": COLORS["ink"],
    "text_x": 790,
    "text_w": 406,
    "label_y": 212,
    "title_y": 272,
    "rule_y": 298, "rule_w": 64, "rule_h": 2,
    "body_y": 352,
    "body_bottom": 520,
    "page_y": 690,
    "page_x": 1196,
}

# Cover / closing geometry: title baseline, the gold rule under it, subtitle.
COVER = {
    "x": 110,
    "title_y": 330,
    "rule_y": 366, "rule_w": 120, "rule_h": 3,
    "sub_y": 424,
    "seal_x": 1156, "seal_y": 646, "seal_size": 24,
    "thanks_y": 340,
    "thanks_sub_y": 404,
}

# Concentric rings used on chapter pages (spec: 400/300/200 px, 1.5pt gold,
# 30/50/70 % opacity, all with fill="none").
RINGS = {
    "cx": 640, "cy": 356,
    "radii": [200, 150, 100],
    "stroke": COLORS["gold"], "sw": 2,
    "opacities": [0.30, 0.50, 0.70],
}


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
    panel = PANEL
    cover = COVER
    rings = RINGS

    font_for = staticmethod(font_for)
    use_font_fallback = staticmethod(use_font_fallback)
    font_fallback_on = staticmethod(font_fallback_on)

    def background(self, image_href: str | None = None,
                   width: int = 1280, height: int = 720) -> str:
        """Page background: optional full-bleed image, else the ink gradient."""
        if image_href:
            parts = [
                '<image id="bg" href="%s" x="0" y="0" width="%d" height="%d" '
                'preserveAspectRatio="xMidYMid slice" '
                'data-pptx-role="background"/>' % (image_href, width, height)
            ]
            scrim = BG_IMAGE_SCRIM
            if scrim and scrim.get("opacity"):
                parts.append(
                    '<rect id="bg-scrim" x="0" y="0" width="%d" height="%d" '
                    'fill="%s" fill-opacity="%s" data-pptx-role="decoration"/>'
                    % (width, height, scrim["fill"], scrim["opacity"]))
            return "\n".join(parts)

        if BG_MODE == "radial":
            # A light centre behind the title that dissolves into ink at the
            # edges — reads as lamp light on paper rather than a flat fill.
            return (
                '<defs>\n'
                '<radialGradient id="page-bg" cx="0.5" cy="0.5" r="0.75">\n'
                '<stop offset="0" stop-color="%s"/>\n'
                '<stop offset="0.55" stop-color="%s"/>\n'
                '<stop offset="1" stop-color="%s"/>\n'
                '</radialGradient>\n'
                '</defs>\n'
                '<rect id="bg" x="0" y="0" width="%d" height="%d" '
                'fill="url(#page-bg)" data-pptx-role="background"/>'
                % (COLORS["ink_center"], COLORS["ink"],
                   COLORS["ink_deep"], width, height)
            )
        if BG_MODE == "linear":
            return (
                '<defs>\n'
                '<linearGradient id="page-bg" x1="0" y1="0" x2="0.6" y2="1">\n'
                '<stop offset="0" stop-color="%s"/>\n'
                '<stop offset="1" stop-color="%s"/>\n'
                '</linearGradient>\n'
                '</defs>\n'
                '<rect id="bg" x="0" y="0" width="%d" height="%d" '
                'fill="url(#page-bg)" data-pptx-role="background"/>'
                % (COLORS["ink"], COLORS["ink_deep"], width, height)
            )
        return ('<rect id="bg" x="0" y="0" width="%d" height="%d" fill="%s" '
                'data-pptx-role="background"/>'
                % (width, height, COLORS["ink_deep"]))


THEME = Theme()

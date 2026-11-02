# -*- coding: utf-8 -*-
"""Theme-agnostic SVG layout primitives.

This module deliberately contains **no palette, no font size and no page copy**.
Every visual value is supplied by the caller, normally from a theme module.
That separation is what makes a deck theme-swappable.

Coordinate system: page pixels (1280 x 720 by default, 1 px = 9525 EMU after
conversion).  All helpers return SVG fragments as strings.
"""
from __future__ import annotations

import os
import re
import sys
from xml.sax.saxutils import escape

from PIL import ImageFont

# ---------------------------------------------------------------- fonts

_FONT_FILES = {"regular": None, "bold": None}
_FONT_FAMILY = "sans-serif"
_FONT_CACHE: dict[tuple[bool, int], ImageFont.FreeTypeFont | None] = {}
_WARNED_MISSING = False

# Punctuation that must not start a line (Chinese typesetting rule).
NO_START = "，。、；：？！）〕」』”’%…,.;:?!)]}"


def configure_fonts(family: str, regular: str | None = None,
                    bold: str | None = None) -> None:
    """Register the font used for width measurement.

    ``family`` is written into the SVG root.  ``regular``/``bold`` are font
    files used only for measuring; when they are missing the toolkit still
    runs, using a coarse width estimate instead.
    """
    global _FONT_FAMILY, _WARNED_MISSING
    _FONT_FAMILY = family
    _FONT_FILES["regular"] = regular
    _FONT_FILES["bold"] = bold or regular
    _FONT_CACHE.clear()
    _WARNED_MISSING = False


def font_family() -> str:
    return _FONT_FAMILY


def _is_bold(weight) -> bool:
    if isinstance(weight, (int, float)):
        return weight >= 600
    return str(weight).strip().lower() in {"bold", "bolder", "600", "700", "800", "900"}


def _font(size: float, weight) -> ImageFont.FreeTypeFont | None:
    bold = _is_bold(weight)
    key = (bold, int(size * 4))
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    path = _FONT_FILES["bold" if bold else "regular"]
    font = None
    if path and os.path.exists(path):
        try:
            font = ImageFont.truetype(path, key[1])
        except OSError:
            font = None
    elif path:
        _warn_missing(path)
    _FONT_CACHE[key] = font
    return font


def _warn_missing(path: str) -> None:
    global _WARNED_MISSING
    if _WARNED_MISSING:
        return
    _WARNED_MISSING = True
    print("[primitives] font file not found: %s; using estimated widths" % path,
          file=sys.stderr)


def _estimate(text: str, size: float, weight) -> float:
    units = 0.0
    for ch in text:
        if ch == " ":
            units += 0.30
        elif ord(ch) < 128:
            units += 0.55
        else:
            units += 1.0
    return units * size * (1.02 if _is_bold(weight) else 1.0)


def adv(text: str, size: float, weight="400") -> float:
    """Measured advance width of ``text`` in page pixels."""
    if not text:
        return 0.0
    font = _font(size, weight)
    if font is None:
        return _estimate(text, size, weight)
    return font.getlength(text) / 4.0


# ---------------------------------------------------------------- atoms

_ASCII_WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9._,:;/%+\-]*")


def _atoms(text: str):
    """Split text into wrap atoms.

    Highlight spans are delimited by ``〔…〕``.  Outside them, CJK characters
    become individual atoms (so wrapping can break anywhere) while Latin words
    stay whole (so English does not break mid-word).
    """
    out: list[tuple[str, bool]] = []
    for part in re.split(r"(〔[^〕]*〕)", text):
        if not part:
            continue
        if part.startswith("〔"):
            out.append((part, True))
            continue
        for token in re.findall(r"[A-Za-z0-9][A-Za-z0-9._,:;/%+\-]*|.", part, re.S):
            out.append((token, False))
    return out


def _merge(atoms):
    """Merge neighbouring atoms that share the same style flag."""
    out = []
    for tok, flag in atoms:
        if out and out[-1][1] == flag:
            out[-1] = (out[-1][0] + tok, flag)
        else:
            out.append((tok, flag))
    return out


def wrap_text(text: str, size: float, maxw: float, weight="400",
              marker_color=None, marker_weight="700"):
    """Wrap to ``maxw`` pixels; returns lines of ``(text, color_or_None, weight)``.

    ``color_or_None`` is ``None`` for normal text so the caller can substitute
    its body colour.  Highlight spans keep ``marker_color``.
    """
    lines, cur, curw = [], [], 0.0
    for tok, is_mark in _atoms(text):
        shown = tok[1:-1] if is_mark else tok
        if not shown:
            continue
        tok_weight = marker_weight if is_mark else weight
        w = adv(shown, size, tok_weight)
        if cur and maxw > 0 and curw + w > maxw and shown not in NO_START:
            lines.append(_merge(cur))
            cur, curw = [], 0.0
        color = marker_color if is_mark else None
        cur.append((shown, (color, tok_weight)))
        curw += w
    if cur:
        lines.append(_merge(cur))
    return [[(t, meta[0], meta[1]) for t, meta in line] for line in lines]


def NLINES(text: str, size: float, maxw: float, weight="400",
           marker_weight="700") -> int:
    return len(wrap_text(text, size, maxw, weight, None, marker_weight))


# ---------------------------------------------------------------- text

def _n(value) -> str:
    value = round(float(value), 2)
    if value == int(value):
        return str(int(value))
    return ("%.2f" % value).rstrip("0").rstrip(".")


def _a(value) -> str:
    return escape(str(value), {'"': "&quot;"})


def T(x, y, s, *, size, fill, weight="400", anchor="start", ls=None,
      font=None) -> str:
    """One positioned text run.

    ``font`` is a comma separated family chain that applies to this run only;
    omit it to inherit the page font.  Widths reported by :func:`adv` always
    come from the measuring face configured by the theme, never from ``font``.
    """
    if s is None or s == "":
        return ""
    parts = ['x="%s"' % _n(x), 'y="%s"' % _n(y),
             'font-size="%s"' % _n(size)]
    if font:
        parts.append('font-family="%s"' % _a(font))
    if str(weight) != "400":
        parts.append('font-weight="%s"' % _a(weight))
    if anchor != "start":
        parts.append('text-anchor="%s"' % _a(anchor))
    if ls:
        parts.append('letter-spacing="%s"' % _a(ls))
    parts.append('fill="%s"' % _a(fill))
    return "<text %s>%s</text>" % (" ".join(parts), escape(str(s)))


def TR(x, y, segs, *, size, fill, weight="400", anchor="start",
       font=None) -> str:
    """One visual line built from several coloured runs.

    ``segs`` items are ``(text, color_or_None, weight_or_None)``.  The line is
    laid out by measured width because PowerPoint has no inline flow that
    honours a mixed-run baseline exactly.
    """
    segs = [(t, c, w) for t, c, w in segs if t]
    total = sum(adv(t, size, w or weight) for t, c, w in segs)
    if anchor == "end":
        cx = x - total
    elif anchor == "middle":
        cx = x - total / 2.0
    else:
        cx = x
    out = []
    for text, color, seg_weight in segs:
        wt = seg_weight or weight
        out.append(T(cx, y, text, size=size, fill=color or fill, weight=wt,
                     font=font))
        cx += adv(text, size, wt)
    return "\n".join(out)


def MIX(x, y, text, *, size, fill, weight="400", anchor="start",
        marker_color=None, marker_weight="700", font=None) -> str:
    """A single line that may contain ``〔highlighted〕`` spans."""
    segs = []
    for part in re.split(r"(〔[^〕]*〕)", text):
        if not part:
            continue
        if part.startswith("〔"):
            inner = part[1:-1]
            if inner:
                segs.append((inner, marker_color, marker_weight))
        else:
            segs.append((part, None, weight))
    return TR(x, y, segs, size=size, fill=fill, weight=weight, anchor=anchor,
              font=font)


def PAR(x, y, w, text, *, size, fill, weight="400", lh=None, lh_ratio=1.35,
        marker_color=None, marker_weight="700", font=None) -> str:
    """A wrapped paragraph; one SVG <text> per visual line."""
    lh = lh or round(size * lh_ratio)
    out = []
    for i, segs in enumerate(wrap_text(text, size, w, weight,
                                       marker_color, marker_weight)):
        out.append(TR(x, y + i * lh, segs, size=size, fill=fill, weight=weight,
                      font=font))
    return "\n".join(out)


# ---------------------------------------------------------------- shapes

def R(x, y, w, h, fill, stroke=None, sw=None, dash=None, rx=None,
      fill_opacity=None, stroke_opacity=None, role=None, ident=None) -> str:
    parts = ['x="%s"' % _n(x), 'y="%s"' % _n(y),
             'width="%s"' % _n(w), 'height="%s"' % _n(h)]
    if rx:
        parts.append('rx="%s"' % _n(rx))
    parts.append('fill="%s"' % _a(fill))
    if stroke:
        parts.append('stroke="%s"' % _a(stroke))
        parts.append('stroke-width="%s"' % _n(sw if sw is not None else 1))
    if dash:
        parts.append('stroke-dasharray="%s"' % _a(dash))
    if fill_opacity is not None:
        parts.append('fill-opacity="%s"' % _n(fill_opacity))
    if stroke_opacity is not None:
        parts.append('stroke-opacity="%s"' % _n(stroke_opacity))
    if ident:
        parts.append('id="%s"' % _a(ident))
    if role:
        parts.append('data-pptx-role="%s"' % _a(role))
    return "<rect %s/>" % " ".join(parts)


def PATH(d, *, fill="none", stroke=None, sw=None, role=None, ident=None) -> str:
    parts = ['d="%s"' % _a(d), 'fill="%s"' % _a(fill)]
    if stroke:
        parts.append('stroke="%s"' % _a(stroke))
        parts.append('stroke-width="%s"' % _n(sw if sw is not None else 1))
        parts.append('stroke-linecap="round"')
    if ident:
        parts.append('id="%s"' % _a(ident))
    if role:
        parts.append('data-pptx-role="%s"' % _a(role))
    return "<path %s/>" % " ".join(parts)


EDGE_ARC_ANCHORS = {
    # Fractions of the panel box, traced from the guochao spec path
    #   M 812 0 C 640 150 600 340 700 430 C 770 500 830 600 845 720
    #   L 1280 720 L 1280 0 Z
    # inside the box (600, 0, 680, 720).  The arc bulges left, so the box
    # starts at the left-most control point rather than at the waist.
    "start": (0.31176, 0.0),
    "bow_c1": (0.05882, 0.20833),
    "bow_c2": (0.0, 0.47222),
    "waist": (0.14706, 0.59722),
    "foot_c1": (0.25, 0.69444),
    "foot_c2": (0.33824, 0.83333),
    "end": (0.36029, 1.0),
}


def ARC_PANEL(x, y, w, h, fill, *, curve=48, role=None, edge="top",
              anchors=None, stroke=None, sw=None, ident=None) -> str:
    """A panel with one long sweeping edge.

    ``edge="top"`` bows the top edge upward like a horizon (one moveTo + one
    cubicBezTo + two lnTo).  ``edge="right"`` traces the concave arc from the
    guochao spec down the panel's left flank (one moveTo + two cubicBezTo +
    two lnTo), the panel itself hugging the right page edge.

    Both shapes stay inside the subset the SVG->DrawingML converter turns into
    a real ``<a:custGeom>``.  ``anchors`` overrides any entry of
    :data:`EDGE_ARC_ANCHORS` (``edge="right"`` only) so another theme can
    retune the sweep without copying the path maths.
    """
    if edge == "right":
        a = dict(EDGE_ARC_ANCHORS)
        a.update(anchors or {})

        def px(point):
            return _n(x + point[0] * w)

        def py(point):
            return _n(y + point[1] * h)

        d = "M %s %s C %s %s %s %s %s %s C %s %s %s %s %s %s L %s %s L %s %s Z" % (
            px(a["start"]), py(a["start"]),
            px(a["bow_c1"]), py(a["bow_c1"]),
            px(a["bow_c2"]), py(a["bow_c2"]),
            px(a["waist"]), py(a["waist"]),
            px(a["foot_c1"]), py(a["foot_c1"]),
            px(a["foot_c2"]), py(a["foot_c2"]),
            px(a["end"]), py(a["end"]),
            _n(x + w), _n(y + h), _n(x + w), _n(y),
        )
        return PATH(d, fill=fill, stroke=stroke, sw=sw, role=role, ident=ident)
    if edge != "top":
        raise ValueError("ARC_PANEL edge must be 'top' or 'right', got %r" % (edge,))
    k = curve / 3.0
    d = ("M %s %s C %s %s %s %s %s %s L %s %s L %s %s Z" % (
        _n(x), _n(y + curve),
        _n(x + w * 0.3), _n(y - k), _n(x + w * 0.7), _n(y - k),
        _n(x + w), _n(y + curve),
        _n(x + w), _n(y + h), _n(x), _n(y + h),
    ))
    return PATH(d, fill=fill, stroke=stroke, sw=sw, role=role, ident=ident)


def CIRCLE(cx, cy, r, *, fill="none", stroke=None, sw=None,
           fill_opacity=None, stroke_opacity=None) -> str:
    parts = ['cx="%s"' % _n(cx), 'cy="%s"' % _n(cy), 'r="%s"' % _n(r),
             'fill="%s"' % _a(fill)]
    if stroke:
        parts.append('stroke="%s"' % _a(stroke))
        parts.append('stroke-width="%s"' % _n(sw if sw is not None else 1))
    if fill_opacity is not None:
        parts.append('fill-opacity="%s"' % _n(fill_opacity))
    if stroke_opacity is not None:
        parts.append('stroke-opacity="%s"' % _n(stroke_opacity))
    return "<circle %s/>" % " ".join(parts)


# ---------------------------------------------------------------- images

def IMG(href, x, y, w, h, aspect="xMidYMid meet", role=None) -> str:
    parts = ['href="%s"' % _a(href), 'x="%s"' % _n(x), 'y="%s"' % _n(y),
             'width="%s"' % _n(w), 'height="%s"' % _n(h),
             'preserveAspectRatio="%s"' % _a(aspect)]
    if role:
        parts.append('data-pptx-role="%s"' % _a(role))
    return "<image %s/>" % " ".join(parts)


def PHOTO_IMG(href, x, y, w, h, frame) -> str:
    """Image with a one-pixel card frame behind it."""
    pad = frame.get("pad", 2)
    return "\n".join([
        R(x - pad, y - pad, w + 2 * pad, h + 2 * pad,
          frame["fill"], frame.get("stroke"), frame.get("sw", 1)),
        IMG(href, x, y, w, h),
    ])


def PHOTO(x, y, w, h, label, style) -> str:
    """Dashed placeholder used when no real picture exists yet."""
    cx = x + w / 2.0
    return "\n".join([
        R(x, y, w, h, style["fill"], style["edge"], style["edge_w"],
          style.get("dash")),
        T(cx, y + h / 2 - 4, label, size=style["label_size"],
          fill=style["label_fill"], anchor="middle"),
        T(cx, y + h / 2 + style.get("sub_gap", 30), style.get("sub", ""),
          size=style["sub_size"], fill=style["sub_fill"], anchor="middle"),
    ])


# ---------------------------------------------------------------- blocks

def NOTECARD(x, y, w, h, title, paras, style) -> str:
    """Tinted card: accent bar on the left, small gold title, body paragraphs."""
    out = [R(x, y, w, h, style["fill"])]
    if style.get("bar"):
        out.append(R(x, y, style["bar_w"], h, style["bar"]))
    out.append(T(x + style["title_x"], y + style["title_y"], title,
                 size=style["title_size"], fill=style["title_fill"],
                 weight=style.get("title_weight", "700"),
                 ls=style.get("title_ls")))
    inner = w - style["title_x"] - style.get("right_pad", 28)
    cy = y + style["body_y"]
    for para in paras:
        out.append(PAR(x + style["title_x"], cy, inner, para,
                       size=style["body_size"], fill=style["body_fill"],
                       lh_ratio=style.get("lh_ratio", 1.35)))
        cy += (NLINES(para, style["body_size"], inner) *
               round(style["body_size"] * style.get("lh_ratio", 1.35)) +
               style.get("para_gap", 8))
    return "\n".join(out)


def BAND(x, y, w, h, title, lines, style, styles=None, lh=None) -> str:
    """Tinted statement band: optional gold label plus one line per sentence."""
    lh = lh or round(style["line_size"] * style.get("lh_ratio", 1.35))
    out = [R(x, y, w, h, style["fill"])]
    if style.get("bar"):
        out.append(R(x, y, style["bar_w"], h, style["bar"]))
    cy = y + style["first_y"]
    if title:
        out.append(T(x + style["x_pad"], cy, title,
                     size=style["title_size"], fill=style["title_fill"],
                     weight=style.get("title_weight", "700"),
                     ls=style.get("title_ls")))
        cy += style["title_gap"]
    for i, line in enumerate(lines):
        size, fill, weight = (styles[i] if styles else
                              (style["line_size"], style["line_fill"], "400"))
        out.append(T(x + style["x_pad"], cy + i * lh, line,
                     size=size, fill=fill, weight=weight))
    return "\n".join(out)


# ---------------------------------------------------------------- page frame

def HEAD(n, kicker, title, style) -> str:
    """Page header: ghost number, kicker, title, short rule."""
    out = [T(style["num_x"], style["num_y"], "%02d" % n,
             size=style["num_size"], fill=style["num_fill"],
             weight="700", anchor="end")]
    out.append(T(style["x"], style["kicker_y"], kicker,
                 size=style["kicker_size"], fill=style["kicker_fill"],
                 weight="700", ls=style.get("kicker_ls")))
    out.append(T(style["x"], style["title_y"], title,
                 size=style["title_size"], fill=style["title_fill"],
                 weight="700"))
    out.append(R(style["x"], style["rule_y"], style["rule_w"],
                 style["rule_h"], style["rule_fill"]))
    return "\n".join(out)


def FOOT(n, style) -> str:
    """Page footer: ``NN ｜ suffix``, right aligned."""
    suffix = style.get("suffix", "")
    text = ("%02d ｜ %s" % (n, suffix)) if suffix else ("%02d" % n)
    return T(style["x"], style["y"], text, size=style["size"],
             fill=style["fill"], anchor=style.get("anchor", "end"))


def wrap(role, body, *, font_family, width, height, lang="zh-CN") -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" '
        'width="%d" height="%d" lang="%s" font-family="%s" '
        'data-pptx-page-role="%s">\n%s\n</svg>\n'
        % (width, height, width, height, _a(lang), _a(font_family), _a(role), body)
    )


def page(role, background, body, *, font_family, width, height,
         lang="zh-CN") -> str:
    """Complete SVG page: background fragment + content fragment."""
    return wrap(role, background + "\n" + body,
                font_family=font_family, width=width, height=height, lang=lang)

# -*- coding: utf-8 -*-
"""demo_guochao — six pages of the 国潮 theme.

    A  cover     一盏东方
    B  chapter   山河入盏   (three concentric gold rings)
    C  content   从一片叶子说起 / 我们把工夫花在三处 / 四个数字
    D  closing   感谢聆听

Copy this file as the starting point for a real deck: every colour, size and
panel coordinate comes from ``themes/guochao/theme.py``, so re-skinning the
deck means editing the theme, not the pages.

Build:

    python scripts/build.py --example demo_guochao \
        --out examples/build/demo_guochao.pptx \
        --transition circle --transition-duration 2.0

LibreOffice renders no transitions, so the circle wipe only shows up in
PowerPoint's slideshow view.
"""
from __future__ import annotations

from primitives import ARC_PANEL, CIRCLE, PAR, R, T, adv

# Which theme this example belongs to; build.py picks it up when --theme is
# not given.
THEME_DIR = "themes/guochao"


def _seal(c, x, y, size) -> str:
    """The 朱红 seal at the bottom right: a plain red square, left blank."""
    return R(x, y, size, size, c["red"])


def cover(deck) -> None:
    c, s, cv = deck.theme.colors, deck.theme.size, deck.theme.cover
    body = [
        _seal(c, cv["seal_x"], cv["seal_y"], cv["seal_size"]),
        T(cv["x"], cv["title_y"], "一盏东方",
          size=s["display"], fill=c["paper"], ls="4",
          font=deck.theme.font_for("display")),
        R(cv["x"], cv["rule_y"], cv["rule_w"], cv["rule_h"], c["gold"]),
        T(cv["x"], cv["sub_y"], "青崖茶事 · 2026 春 品牌视觉提案",
          size=s["lead"], fill=c["muted"],
          font=deck.theme.font_for("subhead")),
    ]
    deck.add_page("cover", "\n".join(body), name="cover")


def chapter(deck) -> None:
    c, s, r = deck.theme.colors, deck.theme.size, deck.theme.rings
    title = "山河入盏"
    ls = 10
    line_w = adv(title, s["chapter"]) + ls * (len(title) - 1)
    body = []
    # Three separate rings, largest first, each its own shape and opacity.
    for radius, opacity in zip(r["radii"], r["opacities"]):
        body.append(CIRCLE(r["cx"], r["cy"], radius, fill="none",
                           stroke=r["stroke"], sw=r["sw"],
                           stroke_opacity=opacity))
    body.append(T(r["cx"], 386, title, size=s["chapter"], fill=c["paper"],
                  anchor="middle", ls=str(ls),
                  font=deck.theme.font_for("display")))
    body.append(R(round(r["cx"] - line_w / 2.0), 442, round(line_w), 2,
                  c["gold"]))
    deck.add_page("dividers", "\n".join(body), name="chapter")


def _content(deck, n, label, title, blocks, name) -> None:
    """One C-page: the ink panel with the sweeping left edge, then the column."""
    c, s, p = deck.theme.colors, deck.theme.size, deck.theme.panel
    body = [
        ARC_PANEL(p["x"], p["y"], p["w"], p["h"], p["fill"], edge="right",
                  ident="arc-panel"),
        T(p["text_x"], p["label_y"], label, size=s["small"], fill=c["gold"],
          weight="700", ls="3"),
        T(p["text_x"], p["title_y"], title, size=s["h1"], fill=c["paper"],
          font=deck.theme.font_for("subhead")),
        R(p["text_x"], p["rule_y"], p["rule_w"], p["rule_h"], c["gold"]),
    ]
    body.extend(blocks)
    body.append(T(p["page_x"], p["page_y"], "%02d" % n, size=s["micro"],
                  fill=c["muted"], anchor="end"))
    deck.add_page("content", "\n".join(body), name=name)


def page_origin(deck, n) -> None:
    c, s, p = deck.theme.colors, deck.theme.size, deck.theme.panel
    blocks = [PAR(p["text_x"], p["body_y"], p["text_w"],
                  "青崖茶事起于武夷山北麓的一片老枞。我们只做一件事："
                  "把山场的气息，原样留在一盏茶里。",
                  size=s["body"], fill=c["paper"], lh_ratio=1.6)]
    _content(deck, n, "ORIGIN / 起源", "从一片叶子说起", blocks, "origin")


def page_three(deck, n) -> None:
    c, s, p = deck.theme.colors, deck.theme.size, deck.theme.panel
    items = [
        ("壹 · 择时", "只在谷雨前后七日采青，过时不要。"),
        ("贰 · 守火", "炭焙三道，每道之间静置半月。"),
        ("叁 · 藏拙", "不追香，不夺味，留一点山气。"),
    ]
    blocks = []
    for i, (head, line) in enumerate(items):
        y = p["body_y"] - 12 + i * 70
        blocks.append(T(p["text_x"], y, head, size=s["caption"],
                        fill=c["gold"], weight="700", ls="2"))
        blocks.append(T(p["text_x"], y + 26, line, size=s["body"],
                        fill=c["paper"]))
    _content(deck, n, "THREE THINGS / 三件事", "我们把工夫花在三处",
             blocks, "three")


def page_numbers(deck, n) -> None:
    c, s, p = deck.theme.colors, deck.theme.size, deck.theme.panel
    stats = [("24", "节气"), ("03", "道焙火"), ("01", "座山场")]
    blocks = []
    for i, (value, label) in enumerate(stats):
        x = p["text_x"] + i * 136
        blocks.append(T(x, p["body_y"] + 34, value, size=s["display"] - 32,
                        fill=c["gold_light"], weight="700",
                        font=deck.theme.font_for("latin")))
        blocks.append(T(x, p["body_y"] + 66, label, size=s["small"],
                        fill=c["muted"]))
    blocks.append(T(p["text_x"], p["body_y"] + 130, "数字不解释，茶汤会解释。",
                    size=s["body"], fill=c["paper"]))
    _content(deck, n, "BY THE NUMBERS / 数字", "三个数字，守住一件事",
             blocks, "numbers")


def closing(deck) -> None:
    c, s, cv = deck.theme.colors, deck.theme.size, deck.theme.cover
    body = [
        T(640, cv["thanks_y"], "感谢聆听", size=s["thanks"],
          fill=c["gold_light"], anchor="middle", ls="6",
          font=deck.theme.font_for("display")),
        T(640, cv["thanks_sub_y"], "青崖茶事 · 以东方为名，向日常借光",
          size=s["small"], fill=c["muted"], anchor="middle"),
    ]
    deck.add_page("closing", "\n".join(body), name="closing")


def build(deck) -> None:
    cover(deck)
    chapter(deck)
    page_origin(deck, 3)
    page_three(deck, 4)
    page_numbers(deck, 5)
    closing(deck)

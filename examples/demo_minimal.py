# -*- coding: utf-8 -*-
"""demo_minimal — an 8-page fictional class term report.

Everything here is invented (no real school, class, person or award).  It is
meant to be copied: change the copy, keep the layout, or swap the theme.

    python scripts/build.py --example demo_minimal --out examples/build/demo_minimal.pptx
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from primitives import (ARC_PANEL, BAND, CIRCLE, HEAD, FOOT, NOTECARD, PAR, PHOTO_IMG,
                        R, T, adv)

ASSET_DIR = Path(__file__).resolve().parent / "build" / "_assets"


def _rgb(hex_color: str):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def _artwork(path: Path, theme) -> str:
    """Synthesise a soft abstract illustration so the demo exercises <image>.

    A real deck would point at a photograph instead; keeping this generated
    means the repository ships no third-party picture.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    w, h = 1200, 756
    top, bottom = _rgb(theme.colors["paper_deep"]), _rgb(theme.colors["tint"])
    img = Image.new("RGB", (w, h), top)
    draw = ImageDraw.Draw(img, "RGBA")
    for y in range(h):
        k = y / max(1, h - 1)
        draw.line([(0, y), (w, y)],
                  fill=tuple(int(top[i] + (bottom[i] - top[i]) * k) for i in range(3)))
    ink = _rgb(theme.colors["primary"])
    gold = _rgb(theme.colors["accent_light"])
    draw.ellipse((620, -180, 1320, 520), fill=ink + (52,))
    draw.ellipse((760, 300, 1240, 780), fill=ink + (38,))
    draw.ellipse((120, 430, 520, 830), fill=gold + (62,))
    draw.arc((520, 60, 1060, 600), 200, 340, fill=ink + (110,), width=3)
    img.save(path, "JPEG", quality=90)
    return str(path)


def _foot(deck, n: int) -> str:
    """Footer copy belongs to the deck, not to the theme."""
    return FOOT(n, dict(deck.theme.foot, suffix="青禾班 · 学期总结"))


def _cover(deck) -> None:
    c, s = deck.theme.colors, deck.theme.size
    body = [
        R(0, 0, 1280, 720, c["primary"]),
        CIRCLE(1110, 150, 250, fill="none", stroke=c["accent_light"], sw=1,
               stroke_opacity=0.32),
        CIRCLE(1110, 150, 168, fill="none", stroke=c["accent_light"], sw=1,
               stroke_opacity=0.20),
        R(80, 196, 6, 330, c["accent_light"]),
        T(112, 214, "学期总结 · 2025 秋", size=s["meta"],
          fill=c["accent_light"], weight="700", ls="3"),
        T(110, 310, "把一学期", size=s["display"], fill=c["on_primary"],
          weight="700"),
        T(110, 392, "走成一条线", size=s["display"], fill=c["on_primary"],
          weight="700"),
        T(112, 468, "青禾班 · 四十六名同学的共同记录", size=s["lead"],
          fill=c["on_primary_soft"]),
        ARC_PANEL(0, 596, 1280, 124, c["primary_mid"], curve=30),
        T(80, 668, "秩序", size=s["h3"], fill=c["on_primary"], weight="700"),
        T(196, 668, "·", size=s["h3"], fill=c["accent_light"]),
        T(230, 668, "好奇", size=s["h3"], fill=c["on_primary"], weight="700"),
        T(346, 668, "·", size=s["h3"], fill=c["accent_light"]),
        T(380, 668, "互相托底", size=s["h3"], fill=c["on_primary"], weight="700"),
        T(1200, 670, "01", size=s["caption"], fill=c["on_primary_faint"],
          anchor="end"),
    ]
    deck.add_page("cover", "\n".join(body), name="cover")


def _contents(deck) -> None:
    c, s = deck.theme.colors, deck.theme.size
    items = [
        ("01", "回望", "从开学第一周到期末最后一课"),
        ("02", "三个关键词", "我们想留下的三样东西"),
        ("03", "一起做成的事", "课程、活动与那些没写进课表的时刻"),
        ("04", "下一段路", "把经验变成下学期的动作"),
    ]
    body = [HEAD(2, "CONTENTS", "这一学期，我们这样走过", deck.theme.head)]
    for i, (num, title, desc) in enumerate(items):
        y = 228 + i * 112
        body.append(R(60, y, 1160, 96, c["tint"] if i % 2 == 0 else c["paper_deep"]))
        body.append(T(92, y + 62, num, size=s["h2"], fill=c["accent"],
                      weight="700"))
        body.append(T(176, y + 58, title, size=s["h3"], fill=c["primary"],
                      weight="700"))
        body.append(T(420, y + 58, desc, size=s["caption"], fill=c["ink_soft"]))
        body.append(T(1190, y + 58, "→", size=s["small"], fill=c["muted"],
                      anchor="end"))
    body.append(_foot(deck, 2))
    deck.add_page("content", "\n".join(body), name="contents")


def _keywords(deck) -> None:
    c, s = deck.theme.colors, deck.theme.size
    cards = [
        ("01", "秩序", "先有稳定的节奏，才谈得上把事做好。我们把每天的时间切成可执行的小块。", "写进班规"),
        ("02", "好奇", "遇到不懂的地方先记下来，再一起找答案。问题比标准答案更早出现。", "写进提问本"),
        ("03", "托底", "允许有人暂时落后，也允许有人多走一步。小组之间互相补位。", "写进排班表"),
    ]
    body = [HEAD(3, "KEYWORDS", "三个关键词", deck.theme.head)]
    for i, (num, title, text, tag) in enumerate(cards):
        x, w = 60 + i * 400, 360
        body.append(R(x, 230, w, 390, c["card"]))
        body.append(R(x, 230, w, 6, c["primary_mid"]))
        body.append(T(x + 30, 318, num, size=s["title"], fill=c["ghost"],
                      weight="700"))
        body.append(T(x + 30, 384, title, size=s["h3"], fill=c["primary"],
                      weight="700"))
        body.append(R(x + 30, 402, 44, 3, c["accent"]))
        body.append(PAR(x + 30, 448, w - 60, text, size=s["caption"],
                        fill=c["ink_soft"], lh_ratio=1.5))
        body.append(R(x + 30, 560, w - 60, 1, c["edge"]))
        body.append(T(x + 30, 592, tag, size=s["micro"], fill=c["accent"],
                      weight="700", ls="1"))
    body.append(_foot(deck, 3))
    deck.add_page("content", "\n".join(body), name="keywords")


def _numbers(deck) -> None:
    c, s = deck.theme.colors, deck.theme.size
    stats = [
        ("18", "次", "主题班会", "每周一次，从未间断"),
        ("126", "小时", "共读时间", "人均每周 1.5 小时"),
        ("9", "个", "小组项目", "全部完成并做了展示"),
        ("92", "%", "准时提交率", "比上学期提高 11 个百分点"),
    ]
    body = [HEAD(4, "BY THE NUMBERS", "一学期，四个数字", deck.theme.head)]
    for i, (value, unit, label, note) in enumerate(stats):
        x = 60 + i * 295
        body.append(R(x, 250, 255, 2, c["edge"]))
        body.append(T(x, 344, value, size=s["display"], fill=c["primary"],
                      weight="700"))
        body.append(T(x + adv(value, s["display"], "700") + 8, 344, unit,
                      size=s["micro"], fill=c["accent"], weight="700"))
        body.append(T(x, 392, label, size=s["small"], fill=c["ink"], weight="700"))
        body.append(PAR(x, 426, 240, note, size=s["micro"], fill=c["muted"],
                        lh_ratio=1.4))
    body.append(BAND(60, 510, 1160, 140, "我们更在意的", [
        "数字只是结果，真正留下来的是每天愿意坐下来做事的习惯。"],
        deck.theme.band))
    body.append(_foot(deck, 4))
    deck.add_page("content", "\n".join(body), name="numbers")


def _moments(deck) -> None:
    c, s = deck.theme.colors, deck.theme.size
    art = _artwork(ASSET_DIR / "demo_art.jpg", deck.theme)
    href = deck.add_image(art, name="demo_art")
    body = [
        HEAD(5, "MOMENTS", "把日子拍成一张照片", deck.theme.head),
        PAR(60, 250, 470, "那次我们把桌子搬到走廊，用一下午把展板从头改到尾。"
                          "没有谁被安排，都是自己走过来的。", size=s["body"],
            fill=c["ink"], lh_ratio=1.55),
        R(60, 380, 40, 3, c["accent"]),
        T(60, 430, "活动日 · 展板重做", size=s["caption"], fill=c["accent"],
          weight="700", ls="1"),
        PAR(60, 470, 470, "后来这张照片被贴在教室后墙。它提醒我们："
                          "一件事情的完成，往往始于有人先动手。",
            size=s["caption"], fill=c["ink_soft"], lh_ratio=1.5),
        PHOTO_IMG(href, 620, 218, 540, 340, deck.theme.image_frame),
        T(620, 596, "示意插图：由示例脚本本地生成，不含真实照片", size=s["micro"],
          fill=c["muted"]),
        R(60, 584, 470, 1, c["edge"]),
    ]
    for x, value, label in ((60, "41 人", "当日到场"), (290, "4 小时", "展板重做")):
        body.append(T(x, 636, value, size=s["h4"], fill=c["primary"], weight="700"))
        body.append(T(x, 668, label, size=s["micro"], fill=c["muted"]))
    body.append(_foot(deck, 5))
    deck.add_page("content", "\n".join(body), name="moments")


def _together(deck) -> None:
    c, s = deck.theme.colors, deck.theme.size
    body = [HEAD(6, "TOGETHER", "一起做成的事", deck.theme.head)]
    body.append(NOTECARD(60, 218, 560, 250, "课程之内", [
        "把每周的共读拆成三段：自读、提问、互讲。",
        "作业不再只交给老师，也在小组里先过一遍。",
        "周五留出一节课，只做答疑，不讲新内容。",
    ], deck.theme.card))
    body.append(NOTECARD(660, 218, 560, 250, "课程之外", [
        "四次班级活动，从策划到收尾都由学生轮值。",
        "每次活动留一页复盘，写下下次要改的一件事。",
        "预算由小组自己管，超支不补，结余留给下次。",
    ], deck.theme.card))
    body.append(BAND(60, 496, 1160, 140, "复盘时最常出现的一句话", [
        "“下次早点开始。”——于是我们真的把下次提前了两周。"],
        deck.theme.band))
    body.append(_foot(deck, 6))
    deck.add_page("content", "\n".join(body), name="together")


def _next(deck) -> None:
    c, s = deck.theme.colors, deck.theme.size
    rows = [
        ("01", "把共读做成固定栏目", "每周一篇短文，固定时间、固定领读人。"),
        ("02", "给每个小组一个真实任务", "任务来自班级之外，结果要交给真实的人看。"),
        ("03", "把复盘写成可复用的清单", "不只记录做了什么，也记录为什么这样做。"),
    ]
    body = [HEAD(7, "NEXT TERM", "下学期，先把三件事做实", deck.theme.head)]
    for i, (num, title, desc) in enumerate(rows):
        y = 238 + i * 128
        body.append(T(60, y + 44, num, size=s["h1"], fill=c["accent_light"],
                      weight="700"))
        body.append(T(150, y + 34, title, size=s["h3"], fill=c["primary"],
                      weight="700"))
        body.append(T(150, y + 72, desc, size=s["caption"], fill=c["ink_soft"]))
        body.append(R(60, y + 106, 1160, 1, c["edge"]))
    body.append(_foot(deck, 7))
    deck.add_page("content", "\n".join(body), name="next")


def _closing(deck) -> None:
    c, s = deck.theme.colors, deck.theme.size
    body = [
        R(0, 0, 1280, 720, c["primary"]),
        CIRCLE(1080, 560, 300, fill="none", stroke=c["accent_light"], sw=1,
               stroke_opacity=0.26),
        CIRCLE(1080, 560, 200, fill="none", stroke=c["accent_light"], sw=1,
               stroke_opacity=0.16),
        T(80, 250, "THANK YOU", size=s["meta"], fill=c["accent_light"],
          weight="700", ls="4"),
        T(76, 360, "谢谢，", size=s["display"], fill=c["on_primary"], weight="700"),
        T(76, 444, "下学期见。", size=s["display"], fill=c["on_primary"], weight="700"),
        R(80, 500, 68, 4, c["accent_light"]),
        T(80, 556, "青禾班 · 2026 春", size=s["small"], fill=c["on_primary_soft"]),
    ]
    deck.add_page("closing", "\n".join(body), name="closing")


def build(deck) -> None:
    _cover(deck)
    _contents(deck)
    _keywords(deck)
    _numbers(deck)
    _moments(deck)
    _together(deck)
    _next(deck)
    _closing(deck)

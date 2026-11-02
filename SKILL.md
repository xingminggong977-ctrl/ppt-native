---
name: ppt-native
description: Build a genuinely native, editable .pptx deck from structured Chinese copy — every paragraph, card and rule is a PowerPoint shape. Use when asked to generate a PPT/PPTX report, review, term summary or briefing with real editable text, when a theme must be swappable, or when Chinese typography (line breaking, text-box width) matters. Triggers: 生成PPT, 做一份汇报, 原生可编辑 pptx, 换主题, 中文排版.
---

# ppt-native — operator guide

Read this file before touching the repository. It is written for an AI that
must produce a deck end to end, not for a human browsing the code.

## 1. When to use it

Use ppt-native when **all** of these are true:

- The deliverable is a `.pptx` that a human will edit in PowerPoint.
- The content is mostly text: titles, paragraphs, cards, bands, a few images.
- Chinese typography matters (no broken lines, no one-character runs,
  no text spilling out of its box).
- A consistent visual system is wanted, and the theme may change later.

Do **not** use it for:

- HTML/web slides → use an HTML deck skill.
- Turning an existing HTML page into slides → use an HTML→PPTX converter.
- Photo-heavy portfolios with complex masks and collages (possible, but the
  primitives are text-first).
- Charts/tables/SmartArt (not implemented; draw them as shapes or embed an
  image).

## 2. Prerequisites

| Item | Default |
| --- | --- |
| Python | 3.10+ with `python` on `PATH` |
| Packages | `python-pptx`, `Pillow`, `PyMuPDF` (see `requirements.txt`) |
| LibreOffice | `soffice`; pass `--soffice` if it is not on `PATH` |
| Converter | local `ppt-master` checkout, resolved by `build.py` |
| Fonts | the theme's regular/bold files; default Microsoft YaHei |

The reference build ran on Windows with Microsoft YaHei and LibreOffice under
`C:\Program Files\LibreOffice`. Absolute paths in the defaults are conveniences,
not requirements. Treat the `ppt-master` checkout as a pinned external
dependency: use it, do not edit it.

`build.py` resolves the converter in this order: `--skill-dir`,
`$env:PPT_MASTER_SKILL`, `<repo>/vendor/ppt-master`, then
`~/.dsh/skills/ppt-master`.

## 3. Input format

A deck is one Python module under `examples/` (or any path passed to
`--example`) exposing `build(deck)`:

```python
from primitives import HEAD, FOOT, PAR, R, T

def build(deck):
    c, s = deck.theme.colors, deck.theme.size
    body = [
        HEAD(2, "SECTION", "页面标题", deck.theme.head),
        PAR(60, 240, 700, "正文。用〔方括号〕标记需要强调的短语。",
            size=s["body"], fill=c["ink"]),
        R(60, 320, 1160, 1, c["edge"]),
        FOOT(2, dict(deck.theme.foot, suffix="季度报告")),
    ]
    deck.add_page("content", "\n".join(body), name="section")
```

Rules for the content module:

1. `build(deck)` is required; it is called once.
2. Call `deck.add_page(role, svg_body, name=...)` in reading order. `role` is a
   short label (`cover`, `content`, `closing`); `name` becomes the SVG
   filename (ASCII, no spaces).
3. All colours and font sizes come from `deck.theme`; never write a literal
   `#RRGGBB` or a pixel font size in the content module.
4. `〔…〕` marks an inline highlight inside `PAR`, `MIX` or `wrap_text`.
5. One `PAR()` call emits one `<text>` node per visual line. That is expected:
   it is what keeps PowerPoint from re-wrapping the line differently.

### Page skeleton

Canvas is 1280×720. Content pages start below the header rule (`y≈190`) and
end above the footer (`y≈680`). A safe frame is:

```
left 60   right 1220   top 210   bottom 650
```

`HEAD(n, kicker, title, theme.head)` prints the ghost page number, kicker,
title and gold rule. `FOOT(n, style)` prints `NN ｜ suffix` right-aligned.
Use both on every content page.

## 4. Command

```powershell
python scripts/build.py --example demo_minimal --out examples/build/demo_minimal.pptx
```

Options that matter:

| Flag | Default | Meaning |
| --- | --- | --- |
| `--example` | required | module name under `examples/` or a `.py` path |
| `--out` | `examples/build/<name>.pptx` | output deck |
| `--theme` | example's `THEME_DIR`, else `themes/minimal-ink` | theme directory or `theme.py` |
| `--font-fallback` | off | replace the theme's display face with its system-safe fallback |
| `--bg-image` | none | full-bleed background image (16:9 recommended) |
| `--transition` | `fade` | passed to `svg_to_pptx.py` (`circle`, `push`, `fade`, `cut`, …) |
| `--transition-duration` | converter default | seconds |
| `--work-dir` | `<out>_project` | SVG project directory |
| `--preview-dir` | `<out>_preview` | PNG output directory |
| `--dpi` | `130` | preview resolution |
| `--skip-gate` | off | debug only; requires an existing quality report |
| `--skip-render` | off | skip LibreOffice while iterating |

The command runs five stages:

1. `deck.save()` — writes `svg_output/*.svg` + `images/*` + `deck.json`.
2. `svg_quality_checker.py --quick-generate --canonical-authoring` — blocks on
   errors such as a `data-pptx-role` element without an `id`.
3. `svg_to_pptx.py --quick-generate --primary-language zh-CN -f ppt169`.
4. `post_fix.py` — widens every text box to its measured width × 1.20.
5. `render.py` — LibreOffice → PDF → `page_NN.png`.

## 5. Outputs and acceptance

Expected artefacts:

```
<out>.pptx
<work>/svg_output/01_cover.svg ...
<work>/images/*
<work>/deck.json
<preview>/page_01.png ...
```

Acceptance checklist (do all of it, do not trust "it ran"):

- [ ] `build.py` exits 0 and prints all five stages.
- [ ] `slides` count equals the number of `add_page` calls.
- [ ] `<a:t>` count equals the number of SVG `<text>` nodes (the build prints
      both). If they differ, some text was dropped or merged unexpectedly.
- [ ] `<p:pic>` count equals background images + intentional images only.
- [ ] Open the pptx with `python-pptx`, change one run of text on one slide,
      save, reopen, and confirm the new text. This proves editability.
- [ ] Change `THEME.colors["primary"]`, rebuild to a second output, and
      confirm the `<a:srgbClr val="...">` count moves from the old value to
      the new one.
- [ ] Read at least 3 preview PNGs with an image tool. Check: no missing
      glyphs (tofu), no text outside its box, no overlapping blocks, footer
      clear of content.

## 6. Primitive reference

All functions return SVG fragments (strings). Coordinates are page pixels.

| Function | Signature (essential args) | Notes |
| --- | --- | --- |
| `adv` | `adv(text, size, weight="400")` | measured width in px; CJK/Latin aware |
| `wrap_text` | `wrap_text(text, size, maxw, weight="400", marker_color=None)` | list of lines of `(text, color, weight)` |
| `NLINES` | `NLINES(text, size, maxw, ...)` | line count |
| `T` | `T(x, y, s, *, size, fill, weight, anchor, ls)` | one run |
| `TR` | `TR(x, y, segs, *, size, fill, weight, anchor)` | one line, several coloured runs |
| `MIX` | `MIX(x, y, text, *, size, fill, marker_color=...)` | one line with `〔…〕` |
| `PAR` | `PAR(x, y, w, text, *, size, fill, weight, lh_ratio, marker_color)` | wrapped paragraph |
| `R` | `R(x, y, w, h, fill, stroke=None, sw=None, rx=None, fill_opacity=None, role=None)` | rectangle |
| `PATH` | `PATH(d, *, fill, stroke, sw, role)` | arbitrary path |
| `ARC_PANEL` | `ARC_PANEL(x, y, w, h, fill, *, curve=48)` | arc-top panel, real `custGeom` |
| `CIRCLE` | `CIRCLE(cx, cy, r, *, fill, stroke, sw, fill_opacity, stroke_opacity)` | circle |
| `IMG` | `IMG(href, x, y, w, h, aspect="xMidYMid meet")` | image |
| `PHOTO_IMG` | `PHOTO_IMG(href, x, y, w, h, frame)` | image + card frame |
| `PHOTO` | `PHOTO(x, y, w, h, label, style)` | dashed placeholder |
| `NOTECARD` | `NOTECARD(x, y, w, h, title, paras, style)` | tinted card, left bar |
| `BAND` | `BAND(x, y, w, h, title, lines, style)` | tinted statement band |
| `HEAD` / `FOOT` | `HEAD(n, kicker, title, style)` / `FOOT(n, style)` | page frame |

Images must be registered first so `deck.save()` copies them:

```python
href = deck.add_image("photo.jpg", name="photo")   # returns ../images/photo.jpg
IMG(href, 620, 220, 540, 340)
```

Relative paths are resolved from the current working directory; use absolute
paths in generated content when in doubt.

## 7. Theme contract

`themes/<name>/theme.py` must expose a module-level `THEME` with:

```
font   {"family", "regular", "bold"}
colors { ... }                 # any keys the deck uses
size   { ... }                 # any keys the deck uses
head / foot / card / band / photo / image_frame   # style dicts
background(image_href=None, width=1280, height=720) -> SVG string
```

To make a new theme: copy `themes/minimal-ink/`, change `NAME`, the palette,
the type ladder and the block styles. Do not edit `primitives.py`.

## 8. Pitfalls (short list)

- A `data-pptx-role` on an element **requires an `id`**, otherwise the gate
  fails with `requires a stable id`. The background-image scrim is the classic
  offender.
- Canonical authoring forbids `<style>`, `class=`, paint on the root `<svg>`,
  and a missing root `font-family`.
- Transition XML must sit after `<p:clrMapOvr>` and before `<p:timing>`; the
  converter already does this — do not hand-edit.
- LibreOffice does not render transitions. Only PowerPoint playback shows
  them.
- Fonts are measured through PIL. If the theme points at a missing file, the
  build still works but widths are estimates, so text may overflow.
- `post_fix.py` only **widens** boxes and keeps the right/centre edge fixed;
  it does not shrink text and does not fix vertical overflow. Shorten the copy
  or reduce the font size in the content module.

Full list with symptoms and fixes: `docs/PITFALLS.md`.
Pipeline internals: `docs/PIPELINE.md`.

## 9. Known limitations

- The converter and quality gate are external (`ppt-master`, MIT); a missing
  checkout stops the build with a clear message.
- No native tables, charts, bullets or SmartArt.
- One deck has one global background image (per-page override is possible via
  `add_page(..., background=...)`, but no primitive builds a cropped image
  mask).
- The PNG preview is a layout check, not a fidelity guarantee: LibreOffice and
  PowerPoint may differ by a few pixels and in font fallback.
- Transition timing is written into the XML but cannot be validated without
  PowerPoint.

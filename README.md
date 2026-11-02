# ppt-native

[English](README.md) | [简体中文](README.zh-CN.md)

A small, open toolkit that turns structured copy into a **genuinely native,
editable `.pptx`** — every heading, paragraph, card, band and rule is a real
PowerPoint shape, not a screenshot.

It is built for Chinese long-form decks (reports, reviews, term summaries)
where typography matters: measured text widths, CJK line breaking, no
one-character-per-run text, and a theme layer that is completely separate from
the content.

```
┌─────────────┐   ┌──────────────┐   ┌──────────────┐   ┌─────────────┐
│ example.py  │ → │ SVG project  │ → │ native .pptx │ → │ PNG preview │
│ + theme.py  │   │ 1280×720     │   │ DrawingML    │   │ LibreOffice │
└─────────────┘   └──────────────┘   └──────────────┘   └─────────────┘
```

## What it is

- A **layout primitive library** (`scripts/primitives.py`) with no colours and
  no font sizes of its own.
- A **theme contract** (`themes/*/theme.py`) that owns palette, type scale and
  block styling; swap one file to change the whole look.
- A **deck model** (`scripts/deck.py`) that materialises pages, images and a
  `deck.json` manifest.
- A **one-command pipeline** (`scripts/build.py`) with a quality gate, the
  upstream SVG→PPTX converter, a text-box width fix and a PNG renderer.

## What it is not

- Not a "generate a deck from a prompt" product. You (or an AI) write a short
  Python module describing the pages; the toolkit handles typography and
  conversion.
- Not an image-to-slides tool. No OCR, no screenshot slides.
- Not a template filler. There is no fixed set of layouts you must obey; the
  primitives compose.

## Quick start

Requirements: Windows with Microsoft YaHei, Python 3.10+, LibreOffice, and a
local copy of the MIT-licensed `ppt-master` toolkit (only
`scripts/svg_to_pptx.py` and `scripts/svg_quality_checker.py` are used).

```powershell
python scripts/build.py --example demo_minimal `
    --out examples/build/demo_minimal.pptx
```

If `python` is not on `PATH`, substitute the full path to your own interpreter,
for example `C:\Python310\python.exe`.

That one command produces:

```
examples/build/demo_minimal.pptx            # the deck
examples/build/demo_minimal_project/        # SVG sources + deck.json
examples/build/demo_minimal_preview/        # page_01.png ... page_08.png
```

Useful flags:

```powershell
# two examples ship with the repo
python scripts/build.py --example demo_minimal   # 8 pages, paper-and-ink
python scripts/build.py --example demo_guochao   # 6 pages, dark, brush titles

# swap the theme; without --theme the example's own THEME_DIR is used
python scripts/build.py --example demo_minimal --theme themes/minimal-ink

# replace the theme's display face with a system-safe fallback
python scripts/build.py --example demo_guochao --font-fallback

# full-bleed background photo (16:9 images are centre-cropped)
python scripts/build.py --example demo_minimal --bg-image .\photo.jpg

# circle transition, 2 seconds (passed through to svg_to_pptx.py)
python scripts/build.py --example demo_minimal `
    --transition circle --transition-duration 2.0

# skip the slow LibreOffice render while iterating on layout
python scripts/build.py --example demo_minimal --skip-render
```

By default `build.py` looks for `ppt-master` at `~/.dsh/skills/ppt-master`.
Point elsewhere with `--skill-dir <path>` or the `PPT_MASTER_SKILL`
environment variable.

## Writing a deck

```python
# examples/my_deck.py
from primitives import HEAD, FOOT, PAR, R

def build(deck):
    c, s = deck.theme.colors, deck.theme.size
    body = [
        HEAD(2, "OVERVIEW", "本季度我们做了什么", deck.theme.head),
        PAR(60, 230, 700, "第一段正文，可以用〔高亮〕标出重点。",
            size=s["body"], fill=c["ink"]),
        R(60, 300, 1160, 1, c["edge"]),
        FOOT(2, deck.theme.foot),
    ]
    deck.add_page("content", "\n".join(body), name="overview")
```

Then:

```powershell
python scripts/build.py --example my_deck --out build/my_deck.pptx
```

`build(deck)` is the only required entry point. Pages are ordered by call order.

## Theming

`themes/minimal-ink/theme.py` is the reference theme. It owns:

| Key | Meaning |
| --- | --- |
| `THEME.font` | family name + regular/bold font files for measurement |
| `THEME.colors` | palette (ink green, paper, gold accents) |
| `THEME.size` | type scale, from `micro` 16 to `display` 64 |
| `THEME.head` / `foot` | page frame geometry and colours |
| `THEME.card` / `band` | block styles used by `NOTECARD` / `BAND` |
| `THEME.background()` | gradient fallback or full-bleed image + scrim |

Copy the directory, rename `NAME`, change a few values, and pass
`--theme themes/your-theme`. No primitive needs to change.

## Themes shipped

| Theme | Look | Best for |
| --- | --- | --- |
| `minimal-ink` | warm paper, ink green, gold hairlines | reports, term summaries, anything read on paper |
| `guochao` | near-black panels, three concentric gold rings, arc-edged content panel, brush-titled cover and section pages | brand proposals, culture decks, anything projected in a dark room |

`guochao` sets its display face to `华文行楷` (STXINGKA). If that font is not
installed, pass `--font-fallback`: the layout does not move, only the stroke
character changes from brushed to printed.

## Background images

`--bg-image photo.jpg` is handed to the theme. The image is centre-cropped to
the canvas ratio with PIL **before** conversion (the converter's
`preserveAspectRatio` support is limited), copied into `images/`, and placed
behind every page. A theme-coloured scrim keeps text legible.

Without an image the theme draws its own gradient. Arc-edge panels are real
filled `<path>` shapes converted to `<a:custGeom>`, so they need no clipping
and look identical with or without a photographic background.

## Transitions

`--transition` is passed straight to `svg_to_pptx.py` (`circle`, `push`,
`fade`, `wipe`, `cut`, …), and `--transition-duration` is in seconds. The
generated XML puts `<p:transition>` after `<p:clrMapOvr>` and before
`<p:timing>`, with the duration in milliseconds.

**LibreOffice does not render transitions**, so the preview PNGs cannot show
them. Verify transitions by playing the deck in PowerPoint.

## How it differs from other AI-PPT tools

| | ppt-native | HTML→PPTX tools | Screenshot-to-PPT |
| --- | --- | --- | --- |
| Output | native shapes | native shapes | one big picture |
| Typography control | measured per run | browser approximation | none |
| Editable text | every paragraph | mostly | no |
| Theme swap | one Python file | CSS rewrite | n/a |
| Long Chinese copy | CJK wrapping built in | depends on browser | no |
| Transitions | native PowerPoint | usually none | none |

## Repository layout

```
ppt-native/
├── SKILL.md               # instructions for an AI operator
├── README.md
├── README.zh-CN.md        # Chinese version of this file
├── LICENSE                # MIT
├── requirements.txt
├── scripts/
│   ├── primitives.py      # theme-agnostic SVG primitives
│   ├── deck.py            # Deck model + theme loading + asset export
│   ├── build.py           # one-command pipeline
│   ├── post_fix.py        # widen text boxes to measured width
│   └── render.py          # soffice → PDF → PNG
├── themes/minimal-ink/
│   ├── theme.py
│   └── README.md
├── examples/
│   └── demo_minimal.py    # 8 fictional pages
└── docs/
    ├── PIPELINE.md
    └── PITFALLS.md
```

## Known limitations

- The pipeline depends on a local `ppt-master` checkout (MIT). It is not
  vendored here; `build.py` finds it via `--skill-dir`, `PPT_MASTER_SKILL`,
  `vendor/ppt-master`, or the default DSH path.
- Font files default to Microsoft YaHei under `C:\Windows\Fonts`. On another
  OS, edit `THEME.font`; measurement falls back to estimates if the files are
  missing.
- Text is laid out line by line (one SVG `<text>` per visual line). Inline
  mixed-colour text is supported via `TR`/`MIX`, but there are no native
  bullets, tables, charts or SmartArt.
- No automatic pagination: the author decides what fits on a page.
- LibreOffice's font fallback can differ slightly from PowerPoint's; always
  open the deck once in PowerPoint before shipping.
- PNG previews show static layout only (no transitions, no animations).

## License

MIT. See `LICENSE`.

The pipeline calls the MIT-licensed `ppt-master` converter at runtime; that
project is not modified or redistributed here.

**Optional AGPL dependency.** `scripts/render.py` rasterises the preview PDF
with `pdftoppm` from poppler-utils when it is available. If poppler is missing
and you still want PNG previews, `requirements-render.txt` installs PyMuPDF,
which is **AGPL-3.0** (or commercial). It is deliberately kept out of the
default install: `pip install -r requirements.txt` gives you an MIT-clean tree,
and the build simply skips preview rendering when neither rasteriser is
present.


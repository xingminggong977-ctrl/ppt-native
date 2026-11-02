# minimal-ink

A quiet editorial theme: **ink green, cream paper, one gold hairline**. It was
designed for Chinese text-heavy reports (term summaries, reviews, briefings)
where the writing should carry the page, not the decoration.

## Palette

| Token | Value | Used for |
| --- | --- | --- |
| `primary` | `#0E3A2B` | titles, dark full-bleed pages |
| `primary_mid` | `#2E7D5B` | card bars, cover band |
| `on_primary` | `#F5F1E6` | text on dark |
| `on_primary_soft` | `#93AC9E` | secondary text on dark |
| `paper` | `#FAF7F1` | background top |
| `paper_deep` | `#F2ECDF` | background bottom, alternate rows |
| `card` | `#FFFFFF` | keyword cards |
| `tint` | `#E9EFE7` | note cards, bands |
| `edge` | `#E4DBC9` | hairlines |
| `ghost` | `#E7EBE4` | the 190 px ghost page number |
| `ink` | `#1F2E27` | body text |
| `ink_soft` | `#4C5B53` | secondary body |
| `muted` | `#8E9992` | captions, footer |
| `accent` | `#B4883A` | kickers, labels, rules |
| `accent_light` | `#D8B96E` | gold on dark |

## Type scale

| Token | px | Typical role |
| --- | --- | --- |
| `display` | 64 | cover statement |
| `title` | 50 | page title, big ghost number is separate |
| `h1` | 42 | list index, closing line |
| `h2` | 39 | large number |
| `h3` | 34 | card title |
| `h4` | 32 | compact highlight |
| `lead` | 30 | deck subtitle |
| `body` | 26 | long paragraph |
| `body_s` | 25 | tighter paragraph |
| `small` | 24 | labels, band lines |
| `caption` | 23 | card body |
| `meta` | 21 | kicker |
| `label` | 19 | footer |
| `micro` | 16 | captions, notes |
| `submicro` | 14 | tiny meta |
| `ghost_num` | 190 | background page number |

Font: Microsoft YaHei, with `msyh.ttc` / `msyhbd.ttc` used for measurement.
On another platform, point `FONT["regular"]` and `FONT["bold"]` at any CJK font
and change `FONT["family"]` to its family name.

## Page furniture

- **`HEAD`** — ghost number at the right edge, a gold uppercase kicker, the
  title, then a 68×4 gold rule.
- **`FOOT`** — `NN ｜ suffix`, right aligned. The suffix is empty by default;
  the deck supplies its own (`dict(theme.foot, suffix="...")`).
- **`CARD`** — tinted rectangle, 6 px left bar, small gold title, 23 px body.
- **`BAND`** — a full-width tinted statement strip with an optional title.
- **`BG_IMAGE_SCRIM`** — 16% paper wash over a photographic background. Set
  the opacity to `0` to show the image untouched.

## Background behaviour

`Theme.background(image_href=None)` has two branches:

1. **With an image**: a full-bleed `<image id="bg">` plus a scrim
   `<rect id="bg-scrim" ... data-pptx-role="decoration">`. The image is already
   centre-cropped to 16:9 by `Deck.add_image(crop=True)`, so no SVG crop mask
   is involved.
2. **Without an image**: a diagonal cream `<linearGradient id="page-bg">` and a
   full-page rect marked `data-pptx-role="background"`.

Arc-edge panels (`ARC_PANEL`) are ordinary filled paths, so both branches look
the same.

## Making another theme

```powershell
Copy-Item -Recurse themes/minimal-ink themes/your-theme
```

Then in `themes/your-theme/theme.py`:

1. Change `NAME`, `TITLE`, `DESCRIPTION`.
2. Replace the palette (keep the token names so decks keep working).
3. Adjust `SIZE` if the new face has different metrics.
4. Update the style dicts (`HEAD`, `FOOT`, `CARD`, `BAND`, `PHOTO`,
   `IMAGE_FRAME`) — geometry and colours only.
5. Keep the `Theme.background()` contract.

Run:

```powershell
python scripts/build.py --example demo_minimal --theme themes/your-theme `
    --out examples/build/your-theme.pptx
```

No file in `scripts/` should need to change. If it does, the theme contract is
leaking and should be fixed there instead.

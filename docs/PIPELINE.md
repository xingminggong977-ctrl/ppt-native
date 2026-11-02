# Pipeline

```
example.py ──build(deck)──┐
themes/x/theme.py ────────┤
                          ▼
                    Deck.save(work)
                          │  svg_output/NN_name.svg
                          │  images/*
                          │  deck.json
                          ▼
              svg_quality_checker.py          (gate, blocking)
                          │  validation/svg_quality_report.json
                          ▼
                  svg_to_pptx.py              (SVG → DrawingML)
                          │  raw.pptx
                          ▼
                    post_fix.py               (widen text boxes)
                          │  out.pptx
                          ▼
                     render.py                (soffice → PDF → PNG)
                          │  page_NN.png
                          ▼
                     count report
```

`scripts/build.py` orchestrates all five stages and prints a count table at the
end. Each stage is also runnable on its own.

---

## 1. Materialise: `Deck.save()`

`Deck` is constructed with a theme and an optional background image.

- `primitives.configure_fonts(family, regular, bold)` is called once, so every
  later `adv()` / `wrap_text()` uses the same metrics.
- `--bg-image` is registered first with `add_image(..., crop=True)`. PIL
  centre-crops to 16:9, resizes to 2560×1440, saves JPEG q88 into
  `images/`, and the returned href is `../images/bg.jpg`.
- `add_page(role, body, name)` stores the SVG body produced by the example
  module. The example is responsible for page content; the deck is responsible
  for the page shell.
- For each page, if no per-page `background` is given, the theme's
  `background(image_href, width, height)` is prepended. With an image it emits
  `<image id="bg">` plus a scrim `<rect id="bg-scrim" data-pptx-role="decoration">`;
  without one it emits a `<linearGradient id="page-bg">` and a full-page rect
  with `id="bg"`.
- `primitives.page(role, background, body, ...)` wraps everything in the
  canonical `<svg>` root: namespace, `viewBox="0 0 1280 720"`, `lang="zh-CN"`,
  `font-family` on the root, `data-pptx-page-role`.
- `deck.json` records theme name, canvas, background href, image sources and
  page filenames. It is a manifest for debugging and for downstream tooling.

The output directory is cleaned (`svg_output/*.svg`, `images/*`) so a rebuild
never leaves pages from a previous, longer deck behind.

---

## 2. Gate: `svg_quality_checker.py`

```powershell
python <skill>\scripts\svg_quality_checker.py <work> --quick-generate --canonical-authoring --stage final --json
```

The checker writes `validation/svg_quality_report.json` and exits non-zero on
blocking errors. Warnings do not block.

What it enforces (canonical authoring):

| Rule | Why |
| --- | --- |
| standard SVG namespace | converter only accepts the standard one |
| no `<style>`, no `class` | converter has no CSS cascade |
| no paint on `<svg>` root | paint must belong to a real element/group |
| root `font-family` | otherwise text falls back per element |
| no redundant inherited styles | keeps the XML diffable |
| no compressible coordinates | keeps numbers meaningful |
| `data-pptx-role` needs `id` | the role is a semantic hook, id makes it stable |

Export with `--quick-generate` **requires** this report; that is why `build.py`
runs the gate first and deletes any stale report before doing so.

---

## 3. Export: `svg_to_pptx.py`

```powershell
python <skill>\scripts\svg_to_pptx.py <work> --quick-generate --primary-language zh-CN -f ppt169 -o raw.pptx -t circle --transition-duration 2.0
```

What happens to the SVG:

- **Text.** Each `<text>` becomes a text box; each `<tspan>` becomes a run.
  Because `PAR()` emits one `<text>` per visual line, PowerPoint receives the
  exact same line breaks that were measured.
- **Shapes.** `<rect>` → `<p:sp>` with `a:prstGeom`; `<circle>` → ellipse;
  `<path>` with moveTo + cubicBezTo + lnTo + close → `<a:custGeom>` (this is
  how `ARC_PANEL` stays a real editable shape).
- **Gradients.** `<linearGradient>` / `<radialGradient>` → `<a:gradFill>`;
  `x1/y1/x2/y2` are read as fractions of the object box, the angle is
  `atan2(y2-y1, x2-x1)`.
- **Opacity.** `fill-opacity` is applied per shape/run.
- **Images.** `<image href="../images/x.jpg">` is embedded and related from
  the slide.
- **Background.** The first full-page element with `data-pptx-role="background"`
  is promoted to the slide background.
- **Transition.** `<p:transition>` is inserted after `<p:clrMapOvr` and before
  `<p:timing>`, with `p14:dur` in milliseconds.

The output `raw.pptx` uses a flat, project-owned master and blank layout, so
there are no stock placeholders to fight.

---

## 4. Post-fix: measure and widen

The converter sizes a text box from the SVG ink box. That is too tight for
PowerPoint's own line breaking, so `post_fix.py` walks every shape
(recursively through groups) and every run:

1. Load the real font at `size_pt × 8` with PIL (`SAMPLE = 8`). Measuring at
   8× and dividing by 8 avoids hinting/rounding error at small sizes.
2. `font.getlength(text) / SAMPLE` gives points.
3. Add letter spacing: `rPr@spc` is in hundredths of a point, so
   `(len(text) - 1) × spc / 100`.
4. Paragraph width = sum of its runs. Shape width = the widest paragraph.
5. `need = int((width_pt × 1.20 + 2 × font_size_pt) × 12700)` EMU.
6. If `need > shape.width`, widen and shift the left edge according to the
   paragraph alignment (`RIGHT`: full delta left, `CENTER`: half, else 0).

It never shrinks a box and never changes font size. The safety factors are
deliberately conservative: 20% plus two font-size units of padding. `build.py` passes
the theme's own font files so measurement and rendering use the same face.

---

## 5. Render: LibreOffice → PDF → PNG

```powershell
python scripts/render.py out.pptx preview --dpi 130
```

- `soffice --headless --norestore --nolockcheck`
- `-env:UserInstallation=file:///<unique temp dir>` — mandatory for parallel
  or repeated runs, otherwise a stale profile lock makes the conversion hang.
- `--convert-to pdf --outdir <preview>`
- PyMuPDF opens the PDF and saves `page_%02d.png` at the requested DPI
  (130 DPI ≈ 1734×975 for a 13.33 in wide slide).
- The PDF and the temp profile are deleted unless `--keep-pdf` is given.

This stage is the slowest (~20 s for 8 pages). Use `--skip-render` while
iterating on copy; render before delivery.

---

## 6. Counts and why they matter

`build.py` unzips the final pptx and reports:

| Metric | Meaning | Expected |
| --- | --- | --- |
| `slides` | `ppt/slides/slideN.xml` | number of `add_page` calls |
| `<p:sp>` | native shapes | grows with cards, rules, text boxes |
| `<p:pic>` | pictures | background pages + intentional images |
| `<a:t>` | text runs with content | equals the SVG `<text>` count |
| `<a:srgbClr>` | explicit colours | moves when the theme palette moves |

The `<a:t>` equality is the cheapest proof that no text was dropped between
SVG and PPTX. The `<a:srgbClr>` count is the cheapest proof that theming is
real and not baked into images.

---

## 7. Extension points

- **New page block** → add a function to `primitives.py` that takes a style
  dict, never a literal colour.
- **New theme** → copy `themes/minimal-ink/`, edit `theme.py` only.
- **New content** → add `examples/<name>.py` with `build(deck)`; no pipeline
  change.
- **New output format** → reuse `Deck.save()`; the SVG project is the stable
  intermediate representation.

# Pitfalls

Every item below was hit while building the reference deck. Each entry gives
the symptom, the cause, and the fix that is already in the code.

---

## 1. Every Chinese character becomes its own text run

**Symptom.** After conversion, a paragraph contains dozens of `<a:r>` runs,
one character each. Editing in PowerPoint is painful and the file bloats.

**Cause.** Splitting text per character for wrapping, then emitting one
`<text>`/`<tspan>` per atom.

**Fix.** `primitives._atoms()` splits into wrap atoms, but `_merge()` merges
neighbouring atoms with the same style before emitting; `wrap_text()` returns
merged segments. Latin words are kept whole by the `_ASCII_WORD` regex, so
English never breaks mid-word.

**Rule.** Wrap at atom level, emit at segment level.

---

## 2. Punctuation lands at the start of a line

**Symptom.** A line begins with `，` or `。`, which is invalid Chinese
typesetting.

**Cause.** Naive width-based wrapping breaks before any atom that overflows.

**Fix.** `NO_START = "，。、；：？！）〕」』”’%…,.;:?!)]}"`; `wrap_text()` refuses
to break before a token in that set and lets it overflow by one character
instead. The measured width used by `post_fix.py` then accounts for it.

---

## 3. Text re-wraps after conversion and spills out of the box

**Symptom.** The SVG looks perfect, the PNG looks perfect, but in PowerPoint a
line breaks one word earlier and the last line sits outside the shape.

**Cause.** The converter sizes a text box from the SVG bbox, which is the
tight ink box. PowerPoint's own line breaking, hinting and font fallback need
more room.

**Fix.** `scripts/post_fix.py` measures every run with the real font at 8× the
point size, adds the run's letter spacing (`rPr@spc` in 1/100 pt), and sets:

```
need = max_measured_width × 1.20 + 2 × font_size
```

The box is only ever widened. For `PP_ALIGN.RIGHT` the left edge moves left;
for `CENTER` it moves half; left-aligned boxes grow to the right.

**Limit.** It cannot fix vertical overflow. If a paragraph is too tall, cut
copy or reduce the size in the content module.

---

## 4. Gate fails: `data-pptx-role requires a stable id`

**Symptom.** With `--bg-image`, the quality gate exits 1 with one error per
page:

```
<rect> with data-pptx-role requires a stable id
```

**Cause.** The theme's background-image scrim was a full-page `<rect>` with
`data-pptx-role="decoration"` but no `id`. The gradient fallback had `id="bg"`,
so the bug only appeared when a background image was supplied.

**Fix.** `themes/minimal-ink/theme.py` now writes `id="bg-scrim"` on that rect.

**Rule.** Any element carrying `data-pptx-role` must also carry an `id`.

---

## 5. Canonical-authoring contract errors

**Symptom.** The gate reports errors about `<style>`, `class`, root paint, or
a missing `font-family`.

**Cause.** The converter's canonical mode requires:

- the standard SVG namespace on `<svg>`;
- no `<style>` blocks and no `class=` attributes;
- no `fill`/`stroke`/`font-*` declarations on the root `<svg>` (paint belongs
  on a meaningful group or element);
- a direct `font-family` on the root when the page contains visible text;
- no redundant repetition of inherited styles;
- no compressible coordinate redundancy.

**Fix.** `primitives.wrap()` writes `font-family` on the root and nothing else
paint-related. Colours live on each text/rect. `Deck` composes every page
through that function — do not hand-write an `<svg>` wrapper.

---

## 6. Transition XML order / namespace / duration

**Symptom.** PowerPoint reports a repair prompt, or the transition is ignored.

**Cause.** `<p:transition>` must appear **after** `<p:clrMapOvr>` and
**before** `<p:timing>` in `<p:sld>`. A circle transition is `<p:circle/>`;
the duration attribute is `p14:dur` in **milliseconds**, in the
`http://schemas.microsoft.com/office/powerpoint/2010/main` namespace.

**Fix.** Do not post-process this by hand. `svg_to_pptx.py` already emits the
correct fragment:

```xml
<p:transition xmlns:p14="..." p14:dur="2000"><p:circle/></p:transition>
```

`build.py` passes `-t circle --transition-duration 2.0` through unchanged.

---

## 7. Transitions are invisible in the PNG preview

**Symptom.** The preview looks identical with and without `--transition`.

**Cause.** LibreOffice renders a static page; transitions are a slideshow
feature and are not rasterised.

**Fix.** None in the preview path. Open the `.pptx` in PowerPoint, press F5,
and advance a slide. Document this in every hand-off.

---

## 8. LibreOffice fails or hangs on conversion

**Symptom.** `soffice` exits non-zero, produces no PDF, or a second parallel
run blocks.

**Cause.** LibreOffice locks a shared user profile; two conversions started at
once fight over it.

**Fix.** `render.py` creates a private profile per run and passes
`-env:UserInstallation=file:///<tempdir>`, plus `--headless --norestore
--nolockcheck`. If it still fails, run with `--soffice <path>` explicitly.

---

## 9. Background image is stretched or cropped wrongly

**Symptom.** Faces are squashed, or the image only covers part of the page.

**Cause.** The converter's support for `preserveAspectRatio` is limited (it
does not implement SVG `slice` reliably).

**Fix.** `Deck.add_image(..., crop=True)` centre-crops the file to the canvas
aspect ratio with PIL and resizes it to 2560×1440 **before** conversion. The
SVG then uses `xMidYMid meet` on an already-correct image.

**Limit.** One global background image per deck. Per-page images can be passed
via `add_page(..., background=...)` but no crop-mask primitive exists.

---

## 10. Fonts silently degrade

**Symptom.** The build succeeds but text is wider/narrower than expected, or
the PDF substitutes a different face.

**Cause.** `THEME.font["regular"/"bold"]` points at a file that does not exist.
`primitives` falls back to a coarse width estimate and prints one warning:

```
[primitives] font file not found: ...; using estimated widths
```

**Fix.** Point the theme at real font files. On Windows the defaults are
`C:\Windows\Fonts\msyh.ttc` and `msyhbd.ttc`. `post_fix.py` receives the same
two paths from the theme via `build.py`.

---

## 11. `<a:t>` count does not match the SVG `<text>` count

**Symptom.** The acceptance check fails by a few runs.

**Cause.** `T()` returns an empty string for empty text, so empty `<text>`
nodes never exist in the SVG. The converter also collapses a `<text>` that
ends up with no visible characters. Multi-`<tspan>` lines become several
runs but still one `<a:t>` per `<tspan>`.

**Fix.** Count SVG `<text>` (not `<tspan>`) and expect equality with `<a:t>`.
If the numbers diverge, look for text the converter dropped (usually a
zero-width or whitespace-only node).

---

## 12. `<p:pic>` count is higher than the number of photos

**Symptom.** A deck with one photo reports 9 `<p:pic>` elements.

**Cause.** With `--bg-image`, every slide gets the background picture,
including the cover and closing slides (their opaque panels simply paint over
it). 8 pages + 1 content photo = 9.

**Fix.** Expected, not a bug. Count `slide rels` image relationships if you
need the number of distinct assets; the same image is reused by relationship.

---

## 13. `--skip-gate` fails with "quality report missing"

**Symptom.** After deleting `validation/`, an export with `--quick-generate`
refuses to run.

**Cause.** `svg_to_pptx.py --quick-generate` trusts an existing quality
report instead of re-validating.

**Fix.** Do not delete the report manually. Run the gate stage (the default)
or omit `--skip-gate`. `build.py` deletes a stale report before re-running the
gate, precisely so an old pass cannot authorise a new deck.

---

## 14. Text is editable but the box is 1 px tall / misplaced

**Symptom.** In PowerPoint the text exists in the selection pane but the box
looks wrong.

**Cause.** A hand-written `<text>` with no usable bbox, or a `T()` call with
`y` outside the canvas.

**Fix.** Keep every text inside the 1280×720 viewBox and give it a real font
size from `THEME.size`. Do not use `font-size="0"` or transforms to hide text.

---

## 15. A photographed certificate comes out sideways or squashed

**Symptom.** A phone-scanned award certificate appears rotated 90°, or a 3:2
photo dropped into a 4:3 frame gives everyone a wide forehead.

**Cause.** The scanner app stored the page rotated, and the frame size was
picked before the source aspect ratio was checked.

**Fix.** Rotate the source file once, offline, before it enters the pipeline —
do not rely on an SVG `transform`, the converter may drop it. Derive the frame
from the real ratio instead of the other way round:

```python
w = 300                      # pick one dimension, derive the other
h = round(w * src_h / src_w)  # 1920×1440 → 300×225
IMG(x, y, w, h, path)
```

**Rule.** Normalise the pixels first, then let the frame follow. If a source
file is missing, leave a labelled placeholder rather than substituting a
different picture — a wrong photo is worse than an empty frame.

---

## 16. `post_fix` widens a box past the right margin

**Symptom.** Preview looks fine, but a shape overhangs the canvas or collides
with the page number. Only shows up on long lines.

**Cause.** `post_fix.py` widens every text box to `measured_width * 1.20 + 2 ×
font_size` so PowerPoint does not re-wrap. A line already flush to the margin
gains 20% of its own width.

**Fix.** Keep authored lines at most ~85% of the available width. If a line has
to run edge to edge, shorten the copy — do not shrink the font, and do not
widen the box further.

**Rule.** The fixer guarantees no re-wrap; the author guarantees no overflow.


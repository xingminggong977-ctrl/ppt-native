# -*- coding: utf-8 -*-
"""Widen text boxes to their measured single-line width.

Why: the SVG -> PPTX converter sizes a text box from the SVG bbox, but the
renderer may break a Chinese line differently and push words past the edge.
We measure every run with the real font at its real size, then widen the
shape (keeping the aligned edge fixed) so PowerPoint never re-wraps it.

    python scripts/post_fix.py raw.pptx out.pptx [--regular msyh.ttc] [--bold msyhbd.ttc]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import ImageFont
from pptx import Presentation
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu

EMU_PER_PT = 12700
SAFETY = 1.20      # measured width -> box width
PAD_PT = 2.0       # keep descenders/side bearings inside the box
SAMPLE = 8         # render at 8x pt, divide back: finer hinting


def _font(path: str | None, size_pt: float, bold: bool):
    if not path:
        return None
    try:
        return ImageFont.truetype(path, max(6, int(round(size_pt * SAMPLE))))
    except OSError:
        return None


def _text_width_pt(run, regular: str | None, bold: str | None) -> tuple[float, float]:
    """Measured width of one run in points, plus the largest font size in it."""
    text = run.text or ""
    if not text.strip():
        return 0.0, 0.0
    size = run.font.size.pt if run.font.size is not None else 18.0
    is_bold = bool(run.font.bold)
    font = _font(bold if is_bold else regular, size, is_bold)
    if font is None:
        return len(text) * size * 0.62, size
    width = font.getlength(text) / SAMPLE
    spc = run._r.find("{http://schemas.openxmlformats.org/drawingml/2006/main}rPr")
    if spc is not None and spc.get("spc"):
        width += max(0, len(text) - 1) * int(spc.get("spc")) / 100.0
    return width, size


def _iter_shapes(shapes):
    for shape in shapes:
        if shape.shape_type == 6 and hasattr(shape, "shapes"):  # group
            yield from _iter_shapes(shape.shapes)
        elif getattr(shape, "has_text_frame", False):
            yield shape


def fix(pptx_in: Path, pptx_out: Path, regular=None, bold=None) -> int:
    prs = Presentation(str(pptx_in))
    widened = 0
    for slide in prs.slides:
        for shape in _iter_shapes(slide.shapes):
            need_pt = 0.0
            max_size = 0.0
            for para in shape.text_frame.paragraphs:
                line = sum(_text_width_pt(r, regular, bold)[0] for r in para.runs)
                if line <= 0:
                    continue
                need_pt = max(need_pt, line)
                max_size = max(max_size, max(
                    (_text_width_pt(r, regular, bold)[1] for r in para.runs),
                    default=0.0,
                ))
            if need_pt <= 0:
                continue
            need = Emu(int((need_pt * SAFETY + PAD_PT * max_size) * EMU_PER_PT))
            if need <= shape.width:
                continue
            delta = need - shape.width
            align = shape.text_frame.paragraphs[0].alignment
            if align == PP_ALIGN.RIGHT:
                shape.left -= delta
            elif align == PP_ALIGN.CENTER:
                shape.left -= delta // 2
            shape.width = need
            widened += 1
    prs.save(str(pptx_out))
    return widened


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("raw_pptx")
    parser.add_argument("out_pptx")
    parser.add_argument("--regular", default=None)
    parser.add_argument("--bold", default=None)
    args = parser.parse_args()
    count = fix(Path(args.raw_pptx), Path(args.out_pptx), args.regular, args.bold)
    print("widened %d text shapes" % count)
    return 0


if __name__ == "__main__":
    sys.exit(main())

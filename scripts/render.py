# -*- coding: utf-8 -*-
"""PPTX -> PDF (LibreOffice) -> PNG per slide.

    python scripts/render.py out.pptx preview_dir --dpi 130

Notes
  * LibreOffice needs a private user profile or two parallel conversions
    fight over the same lock: -env:UserInstallation=file:///<temp>.
  * Transitions and animations are NOT rendered; the PNGs are the static
    layout check only. Play the deck in PowerPoint to judge transitions.
  * PDF rasterisation is pluggable on purpose. `pdftoppm` (poppler) is used
    when present, otherwise PyMuPDF. PyMuPDF is AGPL-3.0, so it is an optional
    dependency: this file never imports it at module scope.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

WIN_DEFAULT = r"C:\Program Files\LibreOffice\program\soffice.exe"


def find_soffice(explicit: str | None) -> str:
    for item in (explicit, os.environ.get("SOFFICE"), WIN_DEFAULT,
                 shutil.which("soffice")):
        if item and Path(item).exists():
            return str(item)
    raise SystemExit("soffice not found; pass --soffice <path> or set SOFFICE")


def _rasterise_with_poppler(pdf: Path, out_dir: Path, dpi: int) -> int:
    """poppler's pdftoppm writes page-01.png, page-02.png, ..."""
    exe = shutil.which("pdftoppm")
    if not exe:
        return 0
    proc = subprocess.run(
        [exe, "-r", str(dpi), "-png", str(pdf), str(out_dir / "page")],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=600)
    if proc.returncode != 0:
        sys.stderr.write((proc.stdout or "") + (proc.stderr or ""))
        return 0
    made = sorted(out_dir.glob("page-*.png"))
    for path in made:
        suffix = path.stem.rsplit("-", 1)[-1]
        path.rename(out_dir / ("page_%s.png" % suffix))
    return len(made)


def _rasterise_with_pymupdf(pdf: Path, out_dir: Path, dpi: int) -> int:
    try:
        import pymupdf
    except ImportError:
        try:
            import fitz as pymupdf  # PyMuPDF < 1.24 module name
        except ImportError:
            return 0
    doc = pymupdf.open(str(pdf))
    try:
        for index, page in enumerate(doc, start=1):
            page.get_pixmap(dpi=dpi).save(str(out_dir / ("page_%02d.png" % index)))
        return doc.page_count
    finally:
        doc.close()


def rasterise(pdf: Path, out_dir: Path, dpi: int = 130) -> int:
    """PDF -> page_XX.png. Returns the number of pages written."""
    pages = _rasterise_with_poppler(pdf, out_dir, dpi)
    if pages:
        print("rasteriser: pdftoppm (poppler)")
        return pages
    pages = _rasterise_with_pymupdf(pdf, out_dir, dpi)
    if pages:
        print("rasteriser: PyMuPDF (AGPL-3.0 optional dependency)")
        return pages
    raise SystemExit(
        "[render] no PDF rasteriser available.\n"
        "         Install poppler-utils so `pdftoppm` is on PATH (preferred), or\n"
        "         `pip install -r requirements-render.txt` to use PyMuPDF, which\n"
        "         is AGPL-3.0 and therefore kept out of the default install.")


def render(pptx: Path, out_dir: Path, dpi: int = 130, soffice: str | None = None,
           keep_pdf: bool = False) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("page_*.png"):
        old.unlink()

    profile = tempfile.mkdtemp(prefix="ppt_native_lo_")
    cmd = [
        find_soffice(soffice), "--headless", "--norestore", "--nolockcheck",
        "-env:UserInstallation=file:///" + profile.replace("\\", "/"),
        "--convert-to", "pdf", "--outdir", str(out_dir), str(pptx),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=600)
    if proc.returncode != 0:
        sys.stderr.write((proc.stdout or "") + (proc.stderr or ""))
        raise SystemExit("LibreOffice conversion failed (exit %s)" % proc.returncode)

    pdf = out_dir / (pptx.stem + ".pdf")
    if not pdf.exists():
        raise SystemExit("LibreOffice produced no PDF for %s" % pptx)

    try:
        pages = rasterise(pdf, out_dir, dpi)
    finally:
        if not keep_pdf and pdf.exists():
            pdf.unlink()
        shutil.rmtree(profile, ignore_errors=True)
    print("rendered %d pages -> %s" % (pages, out_dir))
    return pages


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("pptx")
    parser.add_argument("out_dir")
    parser.add_argument("--dpi", type=int, default=130)
    parser.add_argument("--soffice", default=None)
    parser.add_argument("--keep-pdf", action="store_true")
    args = parser.parse_args()
    render(Path(args.pptx), Path(args.out_dir), args.dpi, args.soffice, args.keep_pdf)
    return 0


if __name__ == "__main__":
    sys.exit(main())

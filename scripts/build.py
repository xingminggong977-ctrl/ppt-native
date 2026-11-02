# -*- coding: utf-8 -*-
"""One command: example -> SVG project -> native PPTX -> PNG preview.

    python scripts/build.py --example demo_minimal --out examples/build/demo_minimal.pptx

Stages
  1. materialise   example module + theme -> <work>/svg_output/*.svg
  2. gate          upstream svg_quality_checker.py (blocking errors stop here)
  3. export        upstream svg_to_pptx.py (real DrawingML shapes, transitions)
  4. post_fix      widen text boxes to measured width (prevents re-wrap)
  5. render        LibreOffice -> PDF -> PNG for visual review
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from deck import Deck, load_module, load_theme  # noqa: E402

DEFAULT_SKILL = str(Path.home() / ".dsh" / "skills" / "ppt-master")


def _utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def _rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def _run(cmd, title: str, *, tail: int = 12) -> subprocess.CompletedProcess:
    print("\n[build] %s" % title)
    print("        " + " ".join('"%s"' % c if " " in c else c for c in cmd))
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    started = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", env=env, timeout=900)
    out = (proc.stdout or "") + (proc.stderr or "")
    lines = [line.rstrip() for line in out.splitlines() if line.strip()]
    for line in lines[-tail:]:
        print("        " + line)
    print("        exit=%s  %.1fs" % (proc.returncode, time.time() - started))
    if proc.returncode != 0:
        raise SystemExit("[build] %s failed; see output above" % title)
    return proc


def _find_skill(explicit: str | None) -> Path:
    candidates = [
        explicit,
        os.environ.get("PPT_MASTER_SKILL"),
        str(ROOT / "vendor" / "ppt-master"),
        DEFAULT_SKILL,
    ]
    for item in candidates:
        if not item:
            continue
        path = Path(item)
        if (path / "scripts" / "svg_to_pptx.py").exists():
            return path
    raise SystemExit(
        "[build] cannot find ppt-master (svg_to_pptx.py).\n"
        "        Pass --skill-dir <path>, or set PPT_MASTER_SKILL."
    )


def _load_example(name: str):
    path = Path(name)
    if not path.exists():
        path = ROOT / "examples" / (name if name.endswith(".py") else name + ".py")
    if not path.exists():
        raise SystemExit("[build] example not found: %s" % name)
    return load_module(path, "ppt_native_example")


def _resolve_theme(explicit: str | None, example) -> Path:
    """``--theme`` wins; else the example's own ``THEME_DIR``; else minimal-ink."""
    for candidate in (explicit, getattr(example, "THEME_DIR", None)):
        if not candidate:
            continue
        path = Path(candidate)
        if not path.exists():
            path = ROOT / candidate
        return path
    return ROOT / "themes" / "minimal-ink"


def _counts(pptx: Path) -> dict:
    with zipfile.ZipFile(pptx) as zf:
        slides = sorted(
            n for n in zf.namelist()
            if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)
        )
        stats = {"slides": len(slides), "sp": 0, "pic": 0, "at": 0, "srgb": 0}
        for name in slides:
            xml = zf.read(name).decode("utf-8")
            stats["sp"] += len(re.findall(r"<p:sp[ >]", xml))
            stats["pic"] += len(re.findall(r"<p:pic[ >]", xml))
            stats["at"] += len(re.findall(r"<a:t>", xml))
            stats["srgb"] += len(re.findall(r"<a:srgbClr ", xml))
    return stats


def _svg_text_nodes(project: Path) -> int:
    return sum(
        len(re.findall(r"<text[ >]", p.read_text(encoding="utf-8")))
        for p in (project / "svg_output").glob("*.svg")
    )


def main() -> int:
    _utf8_stdio()
    parser = argparse.ArgumentParser(
        description="Build a native, editable .pptx from an example/theme pair.")
    parser.add_argument("--example", required=True,
                        help="module name under examples/ or a .py path")
    parser.add_argument("--out", default=None,
                        help="output .pptx (default: examples/build/<example>.pptx)")
    parser.add_argument("--theme", default=None,
                        help="theme directory or theme.py "
                             "(default: the example's THEME_DIR, else minimal-ink)")
    parser.add_argument("--bg-image", default=None,
                        help="optional full-bleed background image")
    parser.add_argument("--transition", default="fade",
                        help="upstream transition key (circle, push, fade, cut ...)")
    parser.add_argument("--transition-duration", type=float, default=None,
                        help="transition duration in seconds")
    parser.add_argument("--work-dir", default=None,
                        help="generated SVG project directory")
    parser.add_argument("--preview-dir", default=None,
                        help="PNG preview directory")
    parser.add_argument("--dpi", type=int, default=130)
    parser.add_argument("--soffice", default=None, help="path to soffice executable")
    parser.add_argument("--skill-dir", default=None, help="ppt-master root")
    parser.add_argument("--skip-gate", action="store_true",
                        help="debug only: reuse an existing quality report")
    parser.add_argument("--skip-render", action="store_true")
    parser.add_argument("--font-fallback", action="store_true",
                        help="build with the theme's fallback font stack "
                             "(no 华文 brush faces; plain 楷体/黑体 instead)")
    args = parser.parse_args()

    example = _load_example(args.example)
    if not hasattr(example, "build"):
        raise SystemExit("[build] %s must expose build(deck)" % args.example)

    theme_path = _resolve_theme(args.theme, example)
    theme = load_theme(theme_path)

    if args.font_fallback:
        if not hasattr(theme, "use_font_fallback"):
            raise SystemExit("[build] theme %s has no font fallback"
                             % getattr(theme, "name", theme_path))
        theme.use_font_fallback(True)

    stem = Path(args.example).stem
    out = Path(args.out) if args.out else ROOT / "examples" / "build" / (stem + ".pptx")
    out = out.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    work = Path(args.work_dir).resolve() if args.work_dir else out.parent / (out.stem + "_project")
    preview = Path(args.preview_dir).resolve() if args.preview_dir else out.parent / (out.stem + "_preview")

    print("[build] theme   : %s (%s)" % (getattr(theme, "name", "?"), _rel(theme_path)))
    print("[build] example : %s" % args.example)
    print("[build] output  : %s" % _rel(out))
    if hasattr(theme, "font_for"):
        label = "fallback stack" if (hasattr(theme, "font_fallback_on")
                                     and theme.font_fallback_on()) else "display face"
        print("[build] fonts   : %s (%s)" % (theme.font_for("display"), label))

    deck = Deck(theme, bg_image=args.bg_image)
    example.build(deck)
    if not deck.pages:
        raise SystemExit("[build] example produced no pages")

    deck.save(work, clean=True)
    print("[build] materialised %d pages -> %s" % (len(deck.pages), _rel(work)))

    skill = _find_skill(args.skill_dir)
    python = sys.executable

    if not args.skip_gate:
        report = work / "validation" / "svg_quality_report.json"
        if report.exists():
            report.unlink()
        _run([python, str(skill / "scripts" / "svg_quality_checker.py"), str(work),
              "--quick-generate", "--canonical-authoring", "--stage", "final",
              "--json"], "gate: svg_quality_checker")

    raw = work / "raw.pptx"
    export = [python, str(skill / "scripts" / "svg_to_pptx.py"), str(work),
              "--quick-generate", "--primary-language", "zh-CN",
              "-f", "ppt169", "-o", str(raw)]
    export += ["-t", args.transition]
    if args.transition_duration is not None:
        export += ["--transition-duration", str(args.transition_duration)]
    _run(export, "export: svg_to_pptx")

    _run([python, str(SCRIPTS / "post_fix.py"), str(raw), str(out),
          "--regular", theme.font.get("regular") or "",
          "--bold", theme.font.get("bold") or ""], "post_fix: widen text boxes")

    try:
        from pptx import Presentation
        pages = len(Presentation(str(out)).slides)
    except Exception as exc:  # noqa: BLE001 - report, then fail loudly
        raise SystemExit("[build] output cannot be reopened by python-pptx: %s" % exc)

    if not args.skip_render:
        render_cmd = [python, str(SCRIPTS / "render.py"), str(out), str(preview),
                      "--dpi", str(args.dpi)]
        if args.soffice:
            render_cmd += ["--soffice", args.soffice]
        _run(render_cmd, "render: LibreOffice -> PNG", tail=6)

    stats = _counts(out)
    print("\n[build] done")
    print("        pptx      : %s (%.1f KB)" % (_rel(out), out.stat().st_size / 1024))
    print("        project   : %s" % _rel(work))
    if not args.skip_render:
        print("        preview   : %s" % _rel(preview))
    print("        slides    : %d (python-pptx read-back: %d)" % (stats["slides"], pages))
    print("        <p:sp>    : %d" % stats["sp"])
    print("        <p:pic>   : %d" % stats["pic"])
    print("        <a:t>     : %d (SVG <text> nodes: %d)" %
          (stats["at"], _svg_text_nodes(work)))
    print("        <a:srgbClr>: %d" % stats["srgb"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

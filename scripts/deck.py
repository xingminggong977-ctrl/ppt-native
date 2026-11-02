# -*- coding: utf-8 -*-
"""Deck model: pages in, a complete SVG project out.

The deck owns theme injection and asset materialisation.  It writes the
project layout expected by the upstream ``svg_to_pptx`` package::

    <project>/
      svg_output/01_cover.svg ...
      images/sample.png ...
      deck.json
"""
from __future__ import annotations

import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path

from PIL import Image

import primitives
from primitives import page as svg_page

CANVAS = (1280, 720)


def load_module(path, name: str):
    """Import a .py file by path (theme modules are not packages)."""
    path = Path(path)
    if path.is_dir():
        path = path / "theme.py"
    if not path.exists():
        raise FileNotFoundError("module not found: %s" % path)
    spec = importlib.util.spec_from_file_location("%s_%s" % (name, abs(hash(str(path)))),
                                                  str(path))
    if spec is None or spec.loader is None:
        raise ImportError("cannot import %s" % path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_theme(path):
    module = load_module(path, "ppt_native_theme")
    theme = getattr(module, "THEME", None)
    if theme is None:
        raise AttributeError("%s must expose a module-level THEME object" % path)
    for attr in ("font", "head", "foot", "background"):
        if not hasattr(theme, attr):
            raise AttributeError("theme %s is missing %r" % (path, attr))
    return theme


def _slug(text: str, fallback: str = "page") -> str:
    slug = re.sub(r"[^A-Za-z0-9_-]+", "_", text or "").strip("_")
    return slug or fallback


class Deck:
    def __init__(self, theme, *, bg_image=None, canvas=CANVAS):
        self.theme = theme
        self.canvas = canvas
        self.pages: list[dict] = []
        self.images: dict[str, dict] = {}
        self.bg_href: str | None = None

        primitives.configure_fonts(
            theme.font["family"],
            theme.font.get("regular"),
            theme.font.get("bold"),
        )

        if bg_image:
            self.bg_href = self.add_image(bg_image, name="bg", crop=True)

    # -------------------------------------------------------------- content
    def add_page(self, role: str, body: str, name: str | None = None,
                 background: str | None = None) -> None:
        self.pages.append({
            "role": role,
            "name": _slug(name or role, role),
            "body": body,
            "background": background,
        })

    def add_image(self, src, name: str | None = None, crop: bool = False) -> str:
        """Register an image and return the project-relative href.

        With ``crop=True`` the image is centre-cropped to the canvas aspect
        ratio at save time, so a full-bleed background never distorts.
        """
        src = Path(src)
        if not src.exists():
            raise FileNotFoundError("image not found: %s" % src)
        if name is None:
            name = src.stem
        ext = ".jpg" if crop else src.suffix.lower()
        filename = "%s%s" % (_slug(name, "image"), ext)
        base, i = filename, 2
        while filename in self.images and self.images[filename]["src"] != str(src):
            filename = "%s_%d%s" % (Path(base).stem, i, Path(base).suffix)
            i += 1
        self.images[filename] = {"src": str(src), "crop": crop}
        return "../images/%s" % filename

    # -------------------------------------------------------------- output
    def save(self, project_dir, *, clean: bool = True) -> Path:
        project = Path(project_dir)
        svg_dir = project / "svg_output"
        img_dir = project / "images"
        svg_dir.mkdir(parents=True, exist_ok=True)
        img_dir.mkdir(parents=True, exist_ok=True)

        if clean:
            for old in svg_dir.glob("*.svg"):
                old.unlink()
            for old in img_dir.iterdir():
                if old.is_file():
                    old.unlink()

        assets = {}
        for filename, entry in self.images.items():
            dst = img_dir / filename
            if entry["crop"]:
                self._write_cropped(Path(entry["src"]), dst)
            else:
                shutil.copy2(entry["src"], dst)
            assets[filename] = str(entry["src"])

        files = []
        for index, item in enumerate(self.pages, start=1):
            background = item["background"]
            if background is None:
                background = self.theme.background(
                    image_href=self.bg_href,
                    width=self.canvas[0], height=self.canvas[1],
                )
            svg = svg_page(
                item["role"], background, item["body"],
                font_family=self.theme.font["family"],
                width=self.canvas[0], height=self.canvas[1],
            )
            filename = "%02d_%s.svg" % (index, item["name"])
            (svg_dir / filename).write_text(svg, encoding="utf-8")
            files.append({"file": filename, "role": item["role"]})

        manifest = {
            "theme": getattr(self.theme, "name", "unknown"),
            "canvas": list(self.canvas),
            "background_image": self.bg_href,
            "images": assets,
            "pages": files,
        }
        (project / "deck.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return project

    def _write_cropped(self, src: Path, dst: Path) -> None:
        target = self.canvas[0] / self.canvas[1]
        with Image.open(src) as im:
            im = im.convert("RGB")
            w, h = im.size
            if w / h > target:
                new_w = int(round(h * target))
                left = (w - new_w) // 2
                im = im.crop((left, 0, left + new_w, h))
            else:
                new_h = int(round(w / target))
                top = (h - new_h) // 2
                im = im.crop((0, top, w, top + new_h))
            im = im.resize((self.canvas[0] * 2, self.canvas[1] * 2),
                           Image.LANCZOS)
            im.save(dst, "JPEG", quality=88)

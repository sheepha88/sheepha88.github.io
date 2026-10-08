"""content + templates + static -> dist/"""
import shutil
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from PIL import Image

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
IMG_DIRS = [ROOT / "static" / "img", ROOT / "static" / "slides"]


def load(name):
    with open(ROOT / "content" / name, encoding="utf-8") as f:
        return yaml.safe_load(f)


def fmt_period(period):
    return " – ".join(str(p).replace("-", ".") for p in period)


def img_size(file):
    for d in IMG_DIRS:
        if (d / file).exists():
            with Image.open(d / file) as im:
                return im.size
    raise FileNotFoundError(file)


def main():
    profile = load("profile.yaml")
    projects = load("projects.yaml")

    env = Environment(
        loader=FileSystemLoader(ROOT / "templates"),
        autoescape=select_autoescape(["html", "j2"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["period"] = fmt_period
    env.globals["img_size"] = img_size

    html = env.get_template("base.html.j2").render(
        site=profile["site"],
        hero=profile["hero"],
        jobs=profile["timeline"]["jobs"],
        product=profile["product"],
        profile=profile["profile"],
        projects=projects,
    )

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    shutil.copytree(ROOT / "static", DIST / "static")
    (DIST / "index.html").write_text(html, encoding="utf-8")
    print("built dist/index.html")


if __name__ == "__main__":
    main()

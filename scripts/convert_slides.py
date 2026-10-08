"""export_slides.ps1 이 만든 PNG 를 2400px WebP(q90)로 변환해 static/slides/ 에 저장한다.
사용: python scripts/convert_slides.py <PNG 폴더>"""
import sys
from pathlib import Path

from PIL import Image

src = Path(sys.argv[1])
out = Path(__file__).resolve().parent.parent / "static" / "slides"
out.mkdir(parents=True, exist_ok=True)
for f in sorted(src.glob("*.png")):
    im = Image.open(f).convert("RGB")
    im.thumbnail((2400, 2400), Image.LANCZOS)
    im.save(out / f"{f.stem}.webp", "WEBP", quality=90, method=6)
    print(f.stem, im.size)

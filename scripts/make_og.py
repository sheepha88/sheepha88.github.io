"""링크 미리보기 카드(1200x630)를 static/og.png 로 생성한다. 한글 폰트가 필요해 로컬(Windows)에서 한 번 만들어 커밋한다."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
BOLD = r"C:\Windows\Fonts\malgunbd.ttf"
REGULAR = r"C:\Windows\Fonts\malgun.ttf"
W, H = 1200, 630

# 브랜드 그라데이션 (페리윙클 블루 -> 보라)
img = Image.new("RGB", (W, H))
px = img.load()
c1, c2 = (77, 91, 214), (123, 107, 240)
for y in range(H):
    for x in range(W):
        t = (x / W * 0.6 + y / H * 0.4)
        px[x, y] = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

d = ImageDraw.Draw(img)
white = (255, 255, 255)
d.text((80, 90), "Product Manager", font=ImageFont.truetype(REGULAR, 34), fill=(225, 228, 250))
d.text((80, 140), "양정우", font=ImageFont.truetype(BOLD, 96), fill=white)
tag = ImageFont.truetype(BOLD, 48)
d.text((80, 290), "데이터로 병목을 규명하고,", font=tag, fill=white)
d.text((80, 355), "반복 가능한 표준 구조로 푸는 PM", font=tag, fill=white)

# 핵심 성과 3개 (지시서 4-1)
small = ImageFont.truetype(BOLD, 29)
x = 80
for text in ("9억원 · 신규 계약 4건", "개발자 투입 100% 제거", "마스킹 97% 자동화"):
    w = int(d.textlength(text, font=small)) + 44
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(overlay).rounded_rectangle((x, 500, x + w, 560), radius=30, fill=(255, 255, 255, 40), outline=(255, 255, 255, 255), width=2)
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    d = ImageDraw.Draw(img)
    d.text((x + 22, 508), text, font=small, fill=white)
    x += w + 16

out = ROOT / "static" / "og.png"
img.save(out, optimize=True)
print(out, img.size)


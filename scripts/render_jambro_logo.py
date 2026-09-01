from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

out = Path(__file__).resolve().parents[1] / "web" / "public" / "brand" / "logo-jambro.png"
out.parent.mkdir(parents=True, exist_ok=True)

w, h = 560, 128
img = Image.new("RGBA", (w, h), (255, 255, 255, 0))
d = ImageDraw.Draw(img)
d.rectangle([0, 8, 14, h - 8], fill=(74, 106, 175, 255))

font_big = ImageFont.load_default()
font_small = ImageFont.load_default()
for candidate in (
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\segoeuib.ttf",
    r"C:\Windows\Fonts\arial.ttf",
):
    p = Path(candidate)
    if p.exists():
        font_big = ImageFont.truetype(str(p), 54)
        font_small = ImageFont.truetype(str(p), 16)
        break

d.text((36, 28), "JAMBRO", fill=(37, 47, 73, 255), font=font_big)
d.text((36, 92), "TECNOLOGIA  ·  DADOS  ·  SAUDE", fill=(74, 106, 175, 255), font=font_small)
img.save(out, "PNG")
print(f"wrote {out} ({out.stat().st_size} bytes)")

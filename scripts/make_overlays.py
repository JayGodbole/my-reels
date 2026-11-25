"""Render professional title/CTA/cover cards with Pillow. No designer needed."""
import json, os, textwrap
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def font(size, bold=True):
    return ImageFont.truetype(BOLD if bold else REG, size)

def rounded(img, rad=60):
    mask = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([0, 0, *img.size], radius=rad, fill=255)
    img.putalpha(mask)
    return img

def main():
    os.makedirs("assets", exist_ok=True)
    with open("product.json") as f:
        p = json.load(f)
    with open("data/script.json") as f:
        d = json.load(f)
    hook, cta, name = d["hook"], p["cta"], p["product_name"]

    # --- hook card (top, first 3s) ---
    lines = textwrap.wrap(hook.upper(), width=26)[:3]
    card = Image.new("RGBA", (980, 120 + 70 * len(lines)), (10, 12, 20, 215))
    card = rounded(card)
    dr = ImageDraw.Draw(card)
    dr.rectangle([0, 0, 14, card.height], fill=(255, 70, 70, 255))  # red accent bar
    y = 40
    for ln in lines:
        dr.text((60, y), ln, font=font(52), fill=(255, 255, 255, 255))
        y += 70
    card.save("assets/hook.png")

    # --- brand pill (top-left, whole video) ---
    brand = Image.new("RGBA", (560, 90), (10, 12, 20, 160))
    brand = rounded(brand, 45)
    dr = ImageDraw.Draw(brand)
    dr.text((30, 20), ("@" + "".join(c for c in name.lower() if c.isalnum())[:18]).upper(),
            font=font(40), fill=(255, 255, 255, 255))
    brand.save("assets/brand.png")

    # --- CTA end card (full screen, last 4s) ---
    end = Image.new("RGB", (W, H), (12, 15, 26))
    dr = ImageDraw.Draw(end)
    for i in range(H):  # subtle vertical gradient
        dr.line([(0, i), (W, i)], fill=(12 + i // 40, 15 + i // 45, 30 + i // 35))
    dr.rounded_rectangle([90, 700, 990, 1220], radius=50, fill=(255, 255, 255))
    for j, ln in enumerate(textwrap.wrap(name.upper(), width=20)[:2]):
        bb = dr.textbbox((0, 0), ln, font=font(64))
        dr.text(((W - (bb[2] - bb[0])) / 2, 780 + j * 80), ln, font=font(64), fill=(15, 15, 20))
    for j, ln in enumerate(textwrap.wrap(cta.upper(), width=26)[:2]):
        bb = dr.textbbox((0, 0), ln, font=font(46))
        dr.text(((W - (bb[2] - bb[0])) / 2, 960 + j * 60), ln, font=font(46), fill=(60, 60, 70))
    dr.rounded_rectangle([290, 1100, 790, 1190], radius=45, fill=(255, 70, 70))
    msg = "LINK IN BIO"
    bb = dr.textbbox((0, 0), msg, font=font(44))
    dr.text(((W - (bb[2] - bb[0])) / 2, 1125), msg, font=font(44), fill=(255, 255, 255))
    end.save("assets/cta.png")
    end.resize((540, 960)).save("assets/cover.jpg", quality=88)
    print("overlays ok")

if __name__ == "__main__":
    main()

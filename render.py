"""On-brand infographic rendering with Pillow. No browser, no system binaries."""

from __future__ import annotations
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont
import brand

C = brand.COLORS

@lru_cache(maxsize=64)
def font(weight: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(brand.FONTS[weight], size)

def _wrap(draw, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def _block(draw, xy, text, fnt, fill, max_w, spacing=1.25, align="left"):
    x, y = xy
    lines = _wrap(draw, text, fnt, max_w)
    lh = int((fnt.getbbox("Ag")[3] - fnt.getbbox("Ag")[1]) * spacing)
    for ln in lines:
        tx = x
        if align == "center":
            tx = x + (max_w - draw.textlength(ln, font=fnt)) / 2
        draw.text((tx, y), ln, font=fnt, fill=fill)
        y += lh
    return y

def _fit(draw, text, weight, max_w, hi, lo=28):
    size = hi
    while size > lo:
        if draw.textlength(text, font=font(weight, size)) <= max_w:
            return font(weight, size)
        size -= 4
    return font(weight, lo)

def _scaled(logo_path, target_h):
    im = Image.open(logo_path).convert("RGBA")
    w = int(im.width * target_h / im.height)
    return im.resize((w, target_h), Image.LANCZOS)

def _footer(img, theme):
    d = ImageDraw.Draw(img)
    W, H = img.size
    band_h = int(H * 0.115)
    y0 = H - band_h
    if theme == "light":
        d.rectangle([0, y0, W, H], fill=C["white"])
        d.line([(0, y0), (W, y0)], fill=C["mist"], width=3)
        l529, lnast = brand.LOGOS["529_color"], brand.LOGOS["nast_steel"]
    else:
        d.rectangle([0, y0, W, H], fill=C["green_deep"])
        l529, lnast = brand.LOGOS["529_white"], brand.LOGOS["nast_white"]
    pad = int(W * 0.05)
    logo = _scaled(l529, int(band_h * 0.40))
    img.paste(logo, (pad, y0 + (band_h - logo.height) // 2), logo)
    nast = _scaled(lnast, int(band_h * 0.28))
    nx = W - pad - nast.width
    img.paste(nast, (nx, y0 + (band_h - nast.height) // 2), nast)
    return band_h

def _chip(draw, xy, text, size, bg, fg):
    x, y = xy
    fnt = font("bold", size)
    tw = draw.textlength(text, font=fnt)
    padx, pady = int(size * 0.9), int(size * 0.55)
    box = [x, y, x + tw + padx * 2, y + size + pady * 2]
    draw.rounded_rectangle(box, radius=int((size + pady * 2) / 2), fill=bg)
    draw.text((x + padx, y + pady - 2), text, font=fnt, fill=fg)
    return box[3] - box[1]

def _accent_bar(img, color):
    d = ImageDraw.Draw(img)
    W, _ = img.size
    d.rectangle([0, 0, W, int(W * 0.012)], fill=color)

def render(spec: dict) -> Image.Image:
    """spec keys: template_type, headline, statement, source, cta, qualifier,
    state, program, myth_text, stats(list of {num,label}), size(w,h),
    theme('green'|'light'), photo(PIL Image or None)."""
    W, H = spec["size"]
    theme = spec.get("theme", "green")
    tt = (spec.get("template_type") or "BIG NUMBER").upper()
    bg = C["green"] if theme == "green" else C["paper"]
    text_main = C["white"] if theme == "green" else C["ink"]
    text_soft = C["mist"] if theme == "green" else C["steel"]

    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)
    _accent_bar(img, C["gold"])
    fh = _footer(img, theme)
    pad = int(W * 0.07)
    max_w = W - pad * 2
    top = int(H * 0.075)
    content_bottom = H - fh - int(H * 0.03)
    landscape = W > H

    if "MYTH" in tt:
        # two panels: myth (light) over fact (green)
        img = Image.new("RGB", (W, H), C["paper"])
        d = ImageDraw.Draw(img)
        _accent_bar(img, C["gold"])
        split = int((H - int(H*0.115)) * 0.42) + int(H*0.02)
        d.rectangle([0, split, W, H], fill=C["green"])
        fh = _footer(img, "green")
        y = top
        d.text((pad, y), "MYTH", font=font("black", int(W*0.05)), fill=C["steel"]); y += int(W*0.075)
        y = _block(d, (pad, y), spec.get("myth_text") or "\u201cI need a lot of money to start.\u201d",
                   font("bold", int(W*0.052)), C["ink"], max_w, 1.2)
        yf = split + int(H*0.05)
        d.text((pad, yf), "FACT", font=font("black", int(W*0.05)), fill=C["mist"]); yf += int(W*0.075)
        yf = _block(d, (pad, yf), spec["statement"], font("semibold", int(W*0.040)), C["white"], max_w, 1.28)
        yf += int(H*0.015)
        _block(d, (pad, yf), "Source: " + spec.get("source",""), font("regular", int(W*0.022)), C["mist"], max_w)
        if spec.get("cta"):
            _chip(d, (pad, content_bottom - int(H*0.02) - int(W*0.05)), "\u2192 " + spec["cta"], int(W*0.03), C["gold"], C["white"])
        return img

    if "ACCESS" in tt and spec.get("stats"):
        y = top
        d.text((pad, y), (spec.get("kicker") or "ACCESS LOOKS DIFFERENT IN EVERY STATE"),
               font=font("bold", int(W*0.030)), fill=C["gold"]); y += int(W*0.06)
        stats = spec["stats"][:3]
        gap = int(H*0.02)
        block_h = (content_bottom - y - gap*len(stats)) // max(len(stats),1)
        for s in stats:
            d.text((pad, y), str(s["num"]), font=font("black", min(int(W*0.11), int(block_h*0.6))), fill=text_main)
            nb = font("black", min(int(W*0.11), int(block_h*0.6))).getbbox(str(s["num"]))[2]
            _block(d, (pad + nb + int(W*0.03), y + int(block_h*0.12)), s["label"],
                   font("semibold", int(W*0.030)), text_soft, max_w - nb - int(W*0.03), 1.15)
            y += block_h + gap
        _block(d, (pad, content_bottom - int(H*0.03)), "Source: " + spec.get("source",""),
               font("regular", int(W*0.020)), text_soft, max_w)
        return img

    if "STATE" in tt or "PARTNER" in tt:
        y = top
        band = spec.get("state") or "STATE SPOTLIGHT"
        prog = spec.get("program") or ""
        d.text((pad, y), band.upper(), font=font("black", int(W*0.058)), fill=text_main); y += int(W*0.085)
        if prog:
            d.text((pad, y), prog, font=font("semibold", int(W*0.034)), fill=C["gold"]); y += int(W*0.065)
        if spec.get("photo") is not None:
            ph = spec["photo"].convert("RGB")
            box_h = int((content_bottom - y) * 0.45)
            ratio = ph.width/ph.height
            ph = ph.resize((int(box_h*ratio), box_h), Image.LANCZOS) if ratio<1.6 else ph.resize((max_w, int(max_w/ratio)), Image.LANCZOS)
            img.paste(ph, (pad, y)); y += ph.height + int(H*0.03)
        hl = spec.get("headline","")
        if hl:
            d.text((pad, y), hl, font=_fit(d, hl, "black", max_w, int(W*0.13)), fill=text_main); y += int(W*0.11)
        y = _block(d, (pad, y), spec["statement"], font("semibold", int(W*0.034)), text_main, max_w, 1.3)
        y += int(H*0.012)
        _block(d, (pad, y), "Source: " + spec.get("source",""), font("regular", int(W*0.020)), text_soft, max_w)
        if spec.get("cta"):
            _chip(d, (pad, content_bottom - int(W*0.045)), "\u2192 " + spec["cta"], int(W*0.028), C["gold"], C["white"])
        return img

    # BIG NUMBER (default)
    y = top
    hl = spec.get("headline","")
    numfont = _fit(d, hl, "black", max_w, int(W*0.30 if not landscape else W*0.16))
    d.text((pad, y), hl, font=numfont, fill=text_main)
    y += (numfont.getbbox(hl)[3] - numfont.getbbox(hl)[1]) + int(H*0.055)
    y = _block(d, (pad, y), spec["statement"], font("semibold", int(W*0.040 if not landscape else W*0.030)),
               text_main, max_w, 1.3)
    y += int(H*0.02)
    if spec.get("qualifier"):
        y = _block(d, (pad, y), spec["qualifier"], font("regular", int(W*0.024)), text_soft, max_w, 1.25)
        y += int(H*0.012)
    _block(d, (pad, y), "Source: " + spec.get("source",""), font("regular", int(W*0.021)), text_soft, max_w)
    if spec.get("cta"):
        _chip(d, (pad, content_bottom - int(W*0.05)), "\u2192 " + spec["cta"], int(W*0.032), C["gold"], C["white"])
    return img

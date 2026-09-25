"""Branded social-image renderer.

Templates deliberately keep artwork simple: graphic = hook, caption = explanation.
The caller supplies the approved/edited graphic text; this module never invents facts.
Content blocks are vertically balanced and carry a small source line for provenance.
"""
from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont, ImageOps
import brand

C = {k: v for k, v in brand.COLORS.items()}


def font(weight: str, size: int):
    size = max(int(size), 12)
    for candidate in brand.FONTS.get(weight, []):
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _wrap(draw, text, fnt, max_w):
    words = str(text or "").split()
    if not words:
        return [""]
    lines, cur = [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if cur and draw.textlength(trial, font=fnt) > max_w:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def _lh(fnt, spacing=1.22):
    bbox = fnt.getbbox("Ag")
    return int((bbox[3] - bbox[1]) * spacing)


def _measure(draw, text, fnt, max_w, spacing=1.22):
    return _lh(fnt, spacing) * len(_wrap(draw, text, fnt, max_w))


def _block(draw, xy, text, fnt, fill, max_w, spacing=1.22):
    x, y = xy
    lh = _lh(fnt, spacing)
    for line in _wrap(draw, text, fnt, max_w):
        draw.text((x, y), line, font=fnt, fill=fill)
        y += lh
    return y


def _fit_single(draw, text, weight, max_w, hi, lo=28):
    size = hi
    while size > lo:
        f = font(weight, size)
        if draw.textlength(str(text), font=f) <= max_w:
            return f
        size -= 3
    return font(weight, lo)


def _body_font(text, W, landscape=False):
    n = len(str(text or ""))
    base = int(W * (0.034 if landscape else 0.040))
    if n > 220:
        base = int(base * 0.68)
    elif n > 160:
        base = int(base * 0.78)
    elif n > 110:
        base = int(base * 0.88)
    return font("semibold", max(base, 22))


def _scaled(path, target_h):
    im = Image.open(path).convert("RGBA")
    w = int(im.width * target_h / im.height)
    return im.resize((w, target_h), Image.Resampling.LANCZOS)


def _footer(img, theme):
    d = ImageDraw.Draw(img)
    W, H = img.size
    band_h = int(H * 0.105)
    y0 = H - band_h
    light = theme == "light"
    d.rectangle([0, y0, W, H], fill=C["white"] if light else C["green_deep"])
    if light:
        d.line([(0, y0), (W, y0)], fill=C["mist"], width=3)
    l529 = brand.LOGOS["529_color" if light else "529_white"]
    lnast = brand.LOGOS["nast_steel" if light else "nast_white"]
    pad = int(W * 0.05)
    logo = _scaled(l529, int(band_h * 0.40))
    img.paste(logo, (pad, y0 + (band_h - logo.height)//2), logo)
    nast = _scaled(lnast, int(band_h * 0.27))
    img.paste(nast, (W - pad - nast.width, y0 + (band_h - nast.height)//2), nast)
    return band_h


def _accent(img):
    d = ImageDraw.Draw(img)
    W, _ = img.size
    d.rectangle([0, 0, W, max(8, int(W * 0.009))], fill=C["gold"])


def _chip(draw, x, y, text, size):
    fnt = font("bold", size)
    tw = draw.textlength(text, font=fnt)
    px, py = int(size*.75), int(size*.42)
    box = [x, y, x + tw + px*2, y + size + py*2]
    draw.rounded_rectangle(box, radius=int((size + py*2)/2), fill=C["gold"])
    draw.text((x+px, y+py-2), text, font=fnt, fill=C["white"])
    return box


def _photo_box(photo, size):
    p = photo.convert("RGB")
    return ImageOps.fit(p, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.45))


def _source_and_cta(d, spec, pad, bottom, max_w, soft, W):
    """Bottom-anchored source line with the CTA chip above it."""
    y = bottom
    if spec.get("source"):
        sf = font("regular", int(W*.020))
        h = _measure(d, "Source: " + str(spec["source"]), sf, max_w)
        y = bottom - h
        _block(d, (pad, y), "Source: " + str(spec["source"]), sf, soft, max_w)
    if spec.get("cta"):
        chip_h = int(W*.026) + int(int(W*.026)*.42)*2
        _chip(d, pad, y - chip_h - int(H_GAP*W), "\u2192 " + spec["cta"], int(W*.026))


H_GAP = 0.02


def render(spec: dict) -> Image.Image:
    W, H = spec["size"]
    theme = spec.get("theme", "green")
    tt = (spec.get("template_type") or "BIG NUMBER").upper()
    bg = C["green"] if theme == "green" else C["paper"]
    main = C["white"] if theme == "green" else C["ink"]
    soft = C["mist"] if theme == "green" else C["steel"]
    landscape = W > H

    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)
    _accent(img)
    footer_h = _footer(img, theme)
    pad = int(W * 0.07)
    max_w = W - 2*pad
    top = int(H * 0.07)
    bottom = H - footer_h - int(H * 0.04)
    statement = spec.get("graphic_text") or spec.get("statement") or ""

    # space reserved at the bottom for the source line + CTA chip
    reserved = 0
    if spec.get("source"):
        reserved += _measure(d, "Source: x", font("regular", int(W*.020)), max_w) + int(H*0.01)
    if spec.get("cta"):
        reserved += int(W*.026) + int(int(W*.026)*.42)*2 + int(H*0.02)

    # MYTH / FACT
    if "MYTH" in tt:
        img = Image.new("RGB", (W, H), C["paper"])
        d = ImageDraw.Draw(img)
        _accent(img)
        footer_h = _footer(img, "green")
        split = int((H-footer_h)*0.40)
        d.rectangle([0, split, W, H-footer_h], fill=C["green"])
        y = top
        d.text((pad, y), "MYTH", font=font("black", int(W*.050)), fill=C["steel"])
        y += int(W*.075)
        _block(d, (pad, y), spec.get("myth_text") or "\u201cI need a lot of money to start.\u201d", font("bold", int(W*.050)), C["ink"], max_w)
        y = split + int(H*.045)
        d.text((pad, y), "FACT", font=font("black", int(W*.050)), fill=C["mist"])
        y += int(W*.072)
        _block(d, (pad, y), statement, _body_font(statement, W, landscape), C["white"], max_w)
        _source_and_cta(d, spec, pad, bottom, max_w, C["mist"], W)
        return img

    # ACCESS / three-number explainer
    if "ACCESS" in tt and spec.get("stats"):
        y = top
        d.text((pad, y), spec.get("kicker") or "MAKING 529 SAVING MORE ACCESSIBLE", font=font("bold", int(W*.029)), fill=C["gold"])
        y += int(W*.065)
        stats = spec["stats"][:3]
        usable = (bottom - reserved) - y
        block_h = usable // max(len(stats), 1)
        for s in stats:
            nf = font("black", min(int(W*.115), int(block_h*.55)))
            num = str(s.get("num", ""))
            d.text((pad, y), num, font=nf, fill=main)
            nw = d.textlength(num, font=nf)
            _block(d, (pad+nw+int(W*.035), y+int(block_h*.10)), s.get("label", ""), font("semibold", int(W*.029)), soft, max_w-nw-int(W*.035))
            y += block_h
        _source_and_cta(d, spec, pad, bottom, max_w, soft, W)
        return img

    # STATE / PEOPLE & PARTNERSHIPS (optional photo)
    if "STATE" in tt or "PEOPLE" in tt or "PARTNER" in tt:
        kicker = (spec.get("state") or "STATE SPOTLIGHT").upper() if "STATE" in tt else "PEOPLE & PARTNERSHIPS"
        kf = font("black", int(W*.047)); kf_h = _lh(kf)
        prog = str(spec.get("program") or "")
        pf = font("semibold", int(W*.029))
        hl = str(spec.get("headline", ""))
        hf = _fit_single(d, hl, "black", max_w, int(W*.105 if not landscape else W*.07), 26) if hl else None
        bf = _body_font(statement, W, landscape)
        has_photo = spec.get("photo") is not None

        if has_photo:
            y = top
            d.text((pad, y), kicker, font=kf, fill=main); y += int(W*.066)
            if prog:
                d.text((pad, y), prog, font=pf, fill=C["gold"]); y += int(W*.052)
            ph_h = int(((bottom - reserved) - y) * .40)
            img.paste(_photo_box(spec["photo"], (max_w, ph_h)), (pad, y)); y += ph_h + int(H*.022)
            if hf:
                d.text((pad, y), hl, font=hf, fill=main); y += (hf.getbbox("Ag")[3]-hf.getbbox("Ag")[1]) + int(H*.016)
            _block(d, (pad, y), statement, bf, main, max_w)
        else:
            total = kf_h + int(W*.014)
            if prog: total += _lh(pf) + int(W*.014)
            if hf: total += (hf.getbbox("Ag")[3]-hf.getbbox("Ag")[1]) + int(H*.016)
            total += _measure(d, statement, bf, max_w)
            avail = (bottom - reserved) - top
            y = top + max(0, (avail - total)//2)
            d.text((pad, y), kicker, font=kf, fill=main); y += kf_h + int(W*.014)
            if prog:
                d.text((pad, y), prog, font=pf, fill=C["gold"]); y += _lh(pf) + int(W*.014)
            if hf:
                d.text((pad, y), hl, font=hf, fill=main); y += (hf.getbbox("Ag")[3]-hf.getbbox("Ag")[1]) + int(H*.016)
            _block(d, (pad, y), statement, bf, main, max_w)
        _source_and_cta(d, spec, pad, bottom, max_w, soft, W)
        return img

    # EVENT / SIMPLE EXPLAINER
    if "EVENT" in tt or "EXPLAINER" in tt:
        y = top
        d.text((pad, y), "THE 529 NETWORK", font=font("bold", int(W*.028)), fill=C["gold"]); y += int(W*.065)
        hl = str(spec.get("headline", ""))
        hf = _fit_single(d, hl, "black", max_w, int(W*.11), 30)
        d.text((pad, y), hl, font=hf, fill=main); y += (hf.getbbox("Ag")[3]-hf.getbbox("Ag")[1]) + int(H*.035)
        _block(d, (pad, y), statement, _body_font(statement, W, landscape), main, max_w)
        _source_and_cta(d, spec, pad, bottom, max_w, soft, W)
        return img


    # TREND (line/area chart from a national series)
    if "TREND" in tt and spec.get("series"):
        series = [(int(x), float(y)) for x, y in spec["series"] if y is not None]
        unit = spec.get("series_unit", "")
        area = C["mist"]
        line_col = C["white"] if theme == "green" else C["green"]
        dot_col = C["white"] if theme == "green" else C["green_deep"]
        # title
        hl = str(spec.get("headline", ""))
        hf = _fit_single(d, hl, "black", max_w, int(W*(.13 if not landscape else .085)), 30)
        d.text((pad, top), hl, font=hf, fill=main)
        title_h = hf.getbbox("Ag")[3]-hf.getbbox("Ag")[1]
        # plot area
        px0, px1 = pad, W - pad
        py0 = top + title_h + int(H*.05)
        py1 = bottom - reserved - int(H*.05)
        xs = [p[0] for p in series]; ys = [p[1] for p in series]
        xmin, xmax = min(xs), max(xs); ymax = max(ys) * 1.12 or 1
        def X(x): return px0 + (px1-px0) * ((x-xmin)/(xmax-xmin) if xmax > xmin else 0)
        def Y(y): return py1 - (py1-py0) * (y/ymax)
        pts = [(X(x), Y(y)) for x, y in series]
        # baseline area
        poly = pts + [(pts[-1][0], py1), (pts[0][0], py1)]
        d.polygon(poly, fill=area)
        d.line(pts, fill=line_col, width=max(4, int(W*.010)), joint="curve")
        # endpoint marker + label
        ex, ey = pts[-1]; r = max(7, int(W*.012))
        d.ellipse([ex-r, ey-r, ex+r, ey+r], fill=dot_col)
        def vlabel(v):
            if unit == "$B":
                return f"${v:g}B"
            if unit == "$K":
                return f"${v:g}K"
            if unit == "K":
                return f"{v:g}K"
            if unit == "M" or "account" in unit.lower():
                return f"{v:g}M"
            if unit.startswith("$"):
                return f"${v:g}B"
            return f"{v:g} {unit}".strip()
        endlbl = vlabel(ys[-1])
        ef = font("black", int(W*.045))
        ew = d.textlength(endlbl, font=ef)
        d.text((min(ex - ew, px1 - ew), ey - int(H*.065)), endlbl, font=ef, fill=main)
        # year axis labels
        yf = font("bold", int(W*.024))
        d.text((px0, py1 + int(H*.006)), str(xmin), font=yf, fill=soft)
        lastlbl = str(xmax); d.text((px1 - d.textlength(lastlbl, font=yf), py1 + int(H*.006)), lastlbl, font=yf, fill=soft)
        _source_and_cta(d, spec, pad, bottom, max_w, soft, W)
        return img

    # BIG NUMBER (default), vertically balanced
    hl = str(spec.get("headline", ""))
    hf = _fit_single(d, hl, "black", max_w, int(W*(.28 if not landscape else .15)), 34)
    num_h = hf.getbbox("Ag")[3] - hf.getbbox("Ag")[1]
    bf = _body_font(statement, W, landscape)
    gap1 = int(H*.045)
    st_h = _measure(d, statement, bf, max_w)
    q_show = bool(spec.get("qualifier")) and len(statement) < 170
    qf = font("regular", int(W*.021))
    q_h = (_measure(d, spec["qualifier"], qf, max_w) + int(H*.015)) if q_show else 0
    total = num_h + gap1 + st_h + q_h
    avail = (bottom - reserved) - top
    y = top + max(0, (avail - total)//2)
    d.text((pad, y), hl, font=hf, fill=main); y += num_h + gap1
    y = _block(d, (pad, y), statement, bf, main, max_w)
    if q_show:
        y += int(H*.015)
        _block(d, (pad, y), spec["qualifier"], qf, soft, max_w)
    _source_and_cta(d, spec, pad, bottom, max_w, soft, W)
    return img

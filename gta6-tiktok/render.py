"""Rendu de la vidéo TikTok GTA 6 (1080x1920, 30 fps). Visuels 100 % originaux, d'inspiration Vice City."""
import math, random, sys, os, subprocess, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
from timing import build, BOUNDS

W, H, FPS = 1080, 1920, 30
M = 1.12  # marge pour les zooms
BW, BH = int(W * M), int(H * M)
FONT_DIR = '/tmp/fonts'
ANTON = f'{FONT_DIR}/Anton-Regular.ttf'
MONT = f'{FONT_DIR}/Montserrat[wght].ttf'
EMOJI = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'

PINK = (255, 46, 151)
CYAN = (0, 240, 255)
PURPLE = (123, 44, 191)
ORANGE = (255, 138, 61)
YELLOW = (255, 225, 77)
WHITE = (255, 255, 255)

LINES = build()
SAFE_CX = 500  # centre horizontal hors zone droite TikTok


# ---------------------------------------------------------------- polices
@functools.lru_cache(None)
def anton(size):
    return ImageFont.truetype(ANTON, size)


@functools.lru_cache(None)
def mont(size, wght=900):
    f = ImageFont.truetype(MONT, size)
    try:
        f.set_variation_by_axes([wght])
    except Exception:
        pass
    return f


@functools.lru_cache(None)
def emoji_img(ch, size):
    f = ImageFont.truetype(EMOJI, 109)
    im = Image.new('RGBA', (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10, 10), ch, font=f, embedded_color=True)
    im = im.crop(im.getbbox())
    r = size / im.height
    return im.resize((max(1, int(im.width * r)), size), Image.LANCZOS)


def is_emoji(w):
    return any(0x1F300 <= ord(c) <= 0x1FAFF or 0x2600 <= ord(c) <= 0x27BF for c in w)


# ---------------------------------------------------------------- texte néon
@functools.lru_cache(None)
def neon(text, size, color, font='anton', core=WHITE, glow=1.0, stroke=0):
    f = anton(size) if font == 'anton' else mont(size)
    bb = f.getbbox(text, stroke_width=stroke)
    pad = int(size * 0.6)
    w, h = bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad
    mask = Image.new('L', (w, h), 0)
    ImageDraw.Draw(mask).text((pad - bb[0], pad - bb[1]), text, font=f, fill=255, stroke_width=stroke, stroke_fill=255)
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for rad, a in ((size * 0.35, 0.9), (size * 0.12, 1.0)):
        g = mask.filter(ImageFilter.GaussianBlur(rad)).point(lambda v: min(255, int(v * a * glow * 1.6)))
        layer = Image.new('RGBA', (w, h), color + (0,))
        layer.putalpha(g)
        out = Image.alpha_composite(out, layer)
    edge = Image.new('RGBA', (w, h), color + (0,))
    edge.putalpha(mask.filter(ImageFilter.MaxFilter(5)))
    out = Image.alpha_composite(out, edge)
    c = Image.new('RGBA', (w, h), core + (0,))
    c.putalpha(mask)
    out = Image.alpha_composite(out, c)
    return out


def paste_c(dst, im, cx, cy, scale=1.0, alpha=1.0, rot=0):
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if rot:
        im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 1.0:
        a = im.getchannel('A').point(lambda v: int(v * alpha))
        im = im.copy()
        im.putalpha(a)
    dst.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


# ---------------------------------------------------------------- décors
def vgrad(w, h, stops):
    ys = np.linspace(0, 1, h)
    out = np.zeros((h, w, 3), np.float32)
    pos = [p for p, _ in stops]
    for ch in range(3):
        col = np.interp(ys, pos, [c[ch] for _, c in stops])
        out[:, :, ch] = col[:, None]
    return out


def palm(d, x, y, hgt, lean, col, scale=1.0):
    # tronc
    pts = []
    for i in range(40):
        t = i / 39
        px = x + lean * hgt * (t ** 1.6)
        py = y - hgt * t
        pts.append((px, py))
        r = (22 - 12 * t) * scale
        d.ellipse([px - r, py - r, px + r, py + r], fill=col)
    tx, ty = pts[-1]
    # palmes
    for ang in [-170, -140, -110, -70, -40, -10, 20, 200]:
        a = math.radians(ang)
        L = hgt * 0.45 * scale
        poly = []
        for i in range(21):
            t = i / 20
            ex = tx + math.cos(a) * L * t
            ey = ty + math.sin(a) * L * t + (L * 0.55) * t * t
            poly.append((ex, ey))
        wdt = 26 * scale
        upper = [(px, py - wdt * math.sin(math.pi * i / 20)) for i, (px, py) in enumerate(poly)]
        lower = [(px, py + wdt * 0.3 * math.sin(math.pi * i / 20)) for i, (px, py) in enumerate(poly)]
        d.polygon(upper + lower[::-1], fill=col)


def skyline(d, base, rng, col_b, w, hmin, hmax, windows=True):
    x = -20
    while x < w + 20:
        bw = rng.randint(50, 130)
        bh = rng.randint(hmin, hmax)
        d.rectangle([x, base - bh, x + bw, base], fill=col_b)
        if rng.random() < 0.25:
            d.rectangle([x + bw // 2 - 4, base - bh - 60, x + bw // 2 + 4, base - bh], fill=col_b)
        if windows:
            for wy in range(base - bh + 14, base - 10, 22):
                for wx in range(x + 8, x + bw - 10, 18):
                    if rng.random() < 0.35:
                        c = rng.choice([PINK, CYAN, (255, 200, 120), (180, 120, 255)])
                        d.rectangle([wx, wy, wx + 7, wy + 10], fill=c)
        x += bw + rng.randint(-10, 8)


def bg_sunset(seed=1):
    rng = random.Random(seed)
    a = vgrad(BW, BH, [(0, (20, 6, 50)), (0.25, (90, 20, 120)), (0.45, (230, 60, 140)), (0.56, (255, 140, 80)), (0.57, (40, 10, 70)), (1, (10, 0, 30))])
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(im)
    hz = int(BH * 0.565)
    # soleil rayé
    sun = Image.new('RGBA', (BW, BH), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sun)
    cx, cy, r = BW // 2, hz - 60, 360
    sg = vgrad(2 * r, 2 * r, [(0, (255, 230, 90)), (0.6, (255, 90, 140)), (1, (230, 40, 160))])
    simg = Image.fromarray(sg.astype(np.uint8)).convert('RGBA')
    m = Image.new('L', (2 * r, 2 * r), 0)
    md = ImageDraw.Draw(m)
    md.ellipse([0, 0, 2 * r, 2 * r], fill=255)
    for i in range(7):
        yy = int(r * 1.05 + i * i * 7 + i * 22)
        md.rectangle([0, yy, 2 * r, yy + 6 + i * 3], fill=0)
    simg.putalpha(m)
    glow = m.filter(ImageFilter.GaussianBlur(60))
    gl = Image.new('RGBA', (2 * r, 2 * r), (255, 80, 160, 0))
    gl.putalpha(glow.point(lambda v: v // 2))
    im.alpha_composite(gl, (cx - r, cy - r))
    im.alpha_composite(simg, (cx - r, cy - r))
    # ligne d'horizon : skyline sombre
    d = ImageDraw.Draw(im)
    skyline(d, hz, rng, (30, 8, 55), BW, 60, 240, windows=False)
    palm(d, 140, hz + 40, 820, 0.18, (15, 2, 30))
    palm(d, BW - 120, hz + 60, 700, -0.22, (15, 2, 30), 0.9)
    return im, hz


def bg_night(seed=2):
    rng = random.Random(seed)
    a = vgrad(BW, BH, [(0, (8, 4, 30)), (0.45, (60, 15, 100)), (0.6, (150, 40, 140)), (0.62, (20, 5, 40)), (1, (5, 0, 20))])
    im = Image.fromarray(a.astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(im)
    for _ in range(160):
        x, y = rng.randint(0, BW), rng.randint(0, int(BH * 0.4))
        s = rng.choice([1, 1, 2, 3])
        d.ellipse([x, y, x + s, y + s], fill=(255, 255, 255))
    hz = int(BH * 0.62)
    skyline(d, hz, rng, (22, 6, 45), BW, 200, 700)
    # reflet dans l'eau
    top = im.crop((0, hz - 500, BW, hz)).transpose(Image.FLIP_TOP_BOTTOM).filter(ImageFilter.GaussianBlur(6))
    top = Image.blend(top, Image.new('RGBA', top.size, (10, 0, 40, 255)), 0.55)
    im.paste(top, (0, hz))
    d = ImageDraw.Draw(im)
    for i in range(40):
        y = hz + 10 + i * 12
        d.line([(0, y), (BW, y)], fill=(255, 46, 151, 40), width=1)
    palm(d, BW - 60, BH - 150, 1000, -0.25, (8, 0, 18), 1.15)
    palm(d, 60, BH - 250, 900, 0.2, (8, 0, 18), 1.0)
    return im, hz


def bg_tunnel(seed=3):
    a = vgrad(BW, BH, [(0, (25, 0, 45)), (0.5, (60, 5, 90)), (1, (20, 0, 40))])
    im = Image.fromarray(a.astype(np.uint8)).convert('RGBA')
    return im, BH // 2


def bg_beach(seed=4):
    rng = random.Random(seed)
    a = vgrad(BW, BH, [(0, (255, 120, 90)), (0.35, (255, 70, 140)), (0.55, (130, 40, 170)), (0.58, (0, 180, 210)), (0.75, (0, 90, 150)), (0.76, (240, 170, 140)), (1, (200, 110, 120))])
    im = Image.fromarray(a.astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(im)
    hz = int(BH * 0.58)
    for i in range(12):
        y = hz + 15 + i * 26
        d.line([(0, y), (BW, y)], fill=(255, 255, 255, 60), width=2)
    palm(d, 100, BH - 80, 1250, 0.3, (30, 5, 40), 1.3)
    palm(d, BW - 40, BH - 40, 1100, -0.32, (30, 5, 40), 1.2)
    palm(d, BW // 2 + 80, BH - 380, 600, -0.1, (60, 15, 70), 0.7)
    return im, hz


BGS = {}


def get_bg(name):
    if name not in BGS:
        BGS[name] = {'sunset': bg_sunset, 'night': bg_night, 'tunnel': bg_tunnel, 'beach': bg_beach}[name]()
    return BGS[name]


def draw_grid(im, hz, t, col=PINK):
    """Sol en grille néon qui défile (dessiné dans l'espace du décor)."""
    d = ImageDraw.Draw(im)
    h = BH - hz
    speed = 0.9
    off = (t * speed) % 1.0
    for i in range(18):
        z = (i + 1 - off)
        y = hz + h * (1.0 / (z * 0.6 + 0.4) - 0.0) * 0.0  # placeholder
    # lignes horizontales en perspective
    for i in range(1, 24):
        z = i - off
        if z <= 0.05:
            continue
        y = hz + h * (1.2 / z) * 0.35
        if y > BH:
            continue
        y = BH - (y - hz)  # inverser pour que ça vienne vers nous
    for i in range(0, 30):
        p = ((i + off) / 30.0)
        y = hz + h * (p ** 2.2)
        a = int(80 + 175 * p)
        d.line([(0, y), (BW, y)], fill=col + (a,), width=max(1, int(1 + 5 * p)))
    vx = BW / 2
    for k in range(-14, 15):
        x2 = vx + k * 190
        d.line([(vx + k * 18, hz), (x2, BH)], fill=col + (200,), width=3)


def draw_tunnel(im, t):
    d = ImageDraw.Draw(im)
    cx, cy = BW / 2, BH * 0.45
    for i in range(14):
        p = ((i + (t * 1.2) % 1.0) / 14.0)
        s = p ** 2.0
        w, h = BW * 1.4 * s, BH * 1.2 * s
        col = PINK if i % 2 == 0 else CYAN
        a = int(255 * min(1, p * 1.5))
        d.rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], outline=col + (a,), width=max(2, int(10 * s)))


def draw_traffic(im, hz, t, rng_seed=7):
    d = ImageDraw.Draw(im)
    rng = random.Random(rng_seed)
    for k in range(26):
        lane = rng.uniform(-1, 1)
        ph = (rng.random() + t * rng.uniform(0.3, 0.7)) % 1.0
        p0 = ph ** 2
        p1 = min(1, (ph + 0.08) ** 2)
        y0, y1 = hz + (BH - hz) * p0, hz + (BH - hz) * p1
        x0, x1 = BW / 2 + lane * BW * 0.8 * p0, BW / 2 + lane * BW * 0.8 * p1
        col = (255, 60, 80) if lane < 0 else (255, 240, 200)
        d.line([(x0, y0), (x1, y1)], fill=col + (230,), width=int(2 + 10 * p1))


def background(kind, t, local, zoom_from, zoom_to, pan, tint):
    name = {'grid': 'sunset', 'city': 'night', 'tunnel': 'tunnel', 'beach': 'beach', 'road': 'night'}[kind]
    base, hz = get_bg(name)
    im = base.copy()
    if kind == 'grid':
        draw_grid(im, hz, t)
    elif kind == 'tunnel':
        draw_tunnel(im, t)
    elif kind == 'road':
        draw_traffic(im, hz, t)
    # zoom / pan
    z = zoom_from + (zoom_to - zoom_from) * local
    cw, ch = W * M / z, H * M / z
    cx = BW / 2 + pan[0] * (BW - cw) / 2 * (local * 2 - 1)
    cy = BH / 2 + pan[1] * (BH - ch) / 2 * (local * 2 - 1)
    box = (cx - cw / 2 * (1 / M) * M, cy - ch / 2, cx + cw / 2, cy + ch / 2)
    cw2 = W / z * M / M  # largeur visible en px décor
    x0 = cx - (W * M / z) / 2 / M * 1.0
    # simplifié : fenêtre de taille (W*M/z/M*?)
    vis_w, vis_h = BW / (z * 1.0) / 1.0 / 1.0, BH / (z * 1.0)
    vis_w, vis_h = W * M / (z * M) * 1.0 * M / M, H / z * 1.0
    vis_w, vis_h = W / z * 1.0, H / z * 1.0
    vis_w, vis_h = vis_w * 1.0, vis_h * 1.0
    cx = BW / 2 + pan[0] * (BW - vis_w) / 2 * (local * 2 - 1)
    cy = BH / 2 + pan[1] * (BH - vis_h) / 2 * (local * 2 - 1)
    box = (cx - vis_w / 2, cy - vis_h / 2, cx + vis_w / 2, cy + vis_h / 2)
    fr = im.transform((W, H), Image.EXTENT, box, Image.BILINEAR)
    if tint:
        fr = Image.blend(fr, Image.new('RGBA', (W, H), tint + (255,)), 0.12)
    # assombrir la zone sous-titres pour la lisibilité
    return fr


@functools.lru_cache(None)
def vignette():
    y, x = np.mgrid[0:H, 0:W]
    d = np.sqrt(((x - W / 2) / (W * 0.75)) ** 2 + ((y - H / 2) / (H * 0.7)) ** 2)
    a = (np.clip(d - 0.55, 0, 1) * 330).clip(0, 200).astype(np.uint8)
    im = Image.new('RGBA', (W, H), (5, 0, 15, 0))
    im.putalpha(Image.fromarray(a))
    # bandeau sombre doux derrière les sous-titres
    band = np.zeros((H, W), np.uint8)
    yy = np.arange(H)
    prof = np.exp(-((yy - 1300) / 170.0) ** 2) * 120
    band[:] = prof[:, None].astype(np.uint8)
    b = Image.new('RGBA', (W, H), (8, 0, 20, 0))
    b.putalpha(Image.fromarray(band))
    return Image.alpha_composite(im, b)


# ---------------------------------------------------------------- éléments graphiques
def ease_out(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def pop(t, t0, dur=0.25):
    """échelle d'apparition avec rebond."""
    x = (t - t0) / dur
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    return 1 + 0.25 * math.sin(math.pi * x) * (1 - x) * 2 - (1 - ease_out(x))


@functools.lru_cache(None)
def card(w, h, col, fill=(20, 5, 40), radius=40, width=8):
    pad = 60
    im = Image.new('RGBA', (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    m = Image.new('L', im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([pad, pad, pad + w, pad + h], radius, outline=255, width=width)
    g = m.filter(ImageFilter.GaussianBlur(22))
    gl = Image.new('RGBA', im.size, col + (0,))
    gl.putalpha(g.point(lambda v: min(255, v * 3)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([pad, pad, pad + w, pad + h], radius, fill=fill + (225,))
    im = Image.alpha_composite(im, gl)
    ImageDraw.Draw(im).rounded_rectangle([pad, pad, pad + w, pad + h], radius, outline=col, width=width)
    return im


@functools.lru_cache(None)
def person(col, flip=False):
    im = Image.new('RGBA', (360, 440), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([120, 40, 240, 170], fill=col)
    d.chord([30, 190, 330, 560], 180, 360, fill=col)
    if not flip:  # cheveux longs
        d.ellipse([105, 25, 255, 140], fill=col)
        d.rectangle([110, 90, 140, 230], fill=col)
        d.rectangle([220, 90, 250, 230], fill=col)
    g = im.getchannel('A').filter(ImageFilter.GaussianBlur(14))
    out = Image.new('RGBA', im.size, col + (0,))
    out.putalpha(g)
    sil = Image.new('RGBA', im.size, (15, 2, 30, 0))
    sil.putalpha(im.getchannel('A'))
    out = Image.alpha_composite(out, sil)
    return out


def chip(fr, t, t0, txt):
    s = pop(t, t0)
    if s > 0:
        c = card(250, 120, PINK, fill=(40, 0, 50), radius=60, width=6)
        im = c.copy()
        paste_c(im, neon(txt, 90, PINK), im.width / 2, im.height / 2 + 4)
        paste_c(fr, im, SAFE_CX, 330, s)


def word_t(line, word):
    for w, k, tt in LINES[line]['words']:
        if w.startswith(word):
            return tt
    return LINES[line]['start']


def foreground(fr, seg, t):
    L = LINES[seg]
    s0 = L['start']
    CY = 700
    if seg == 0:
        s = pop(t, -0.2, 0.35)
        if s:
            paste_c(fr, neon('J-5', 420, PINK), SAFE_CX, CY, s * (1 + 0.04 * math.sin(t * 8)))
        if t > word_t(0, 'TRAVAIL'):
            paste_c(fr, neon('NO WORK', 110, CYAN), SAFE_CX, CY + 300, pop(t, word_t(0, 'TRAVAIL')), rot=6)
    elif seg == 1:
        paste_c(fr, neon('2013', 150, CYAN), SAFE_CX - 220, 470, pop(t, s0 + 0.1))
        paste_c(fr, neon('→', 150, WHITE), SAFE_CX, 470, pop(t, s0 + 0.4))
        paste_c(fr, neon('2026', 150, PINK), SAFE_CX + 220, 470, pop(t, s0 + 0.7))
        paste_c(fr, neon('13 ANS', 300, YELLOW), SAFE_CX, 800, pop(t, s0 + 0.15, 0.35))
    elif seg == 2:
        for i, (txt, tt) in enumerate([('2025', s0 + 0.1), ('MAI 2026', s0 + 0.6)]):
            y = 450 + i * 230
            sc = pop(t, tt)
            if sc:
                paste_c(fr, neon(txt, 130, (160, 160, 200), glow=0.4), SAFE_CX, y - 40, sc)
                paste_c(fr, neon('REPORTÉ', 90, (255, 40, 60)), SAFE_CX + 60, y + 75, sc * (1.6 - 0.6 * ease_out((t - tt) / 0.2)), rot=-12)
        tt = word_t(2, 'BONNE') - 0.2
        if t > tt:
            paste_c(fr, neon('19.11.2026', 170, CYAN), SAFE_CX, 960, pop(t, tt, 0.3))
    elif seg == 3:
        chip(fr, t, s0 + 0.05, '1/5')
        tn = word_t(3, '19')
        if t > tn - 0.1:
            sc = pop(t, tn - 0.1, 0.3) * (1 + 0.03 * math.sin(t * 10))
            paste_c(fr, neon('19.11', 340, PINK), SAFE_CX, 700, sc)
        paste_c(fr, neon('JEUDI', 130, CYAN), SAFE_CX, 960, pop(t, word_t(3, 'jeudi')))
        tm = word_t(3, 'nuit')
        if t > tm:
            paste_c(fr, neon('NUIT DU 18 AU 19', 70, YELLOW, font='mont'), SAFE_CX, 1100 - 60, pop(t, tm))
    elif seg == 4:
        chip(fr, t, s0 + 0.05, '2/5')
        for i, (txt, col, w0) in enumerate([('PS5', CYAN, 'PS5'), ('XBOX SERIES X|S', (80, 255, 120), 'XBOX')]):
            tt = word_t(4, w0)
            sc = pop(t, tt - 0.05)
            if sc:
                c = card(380, 230, col).copy()
                paste_c(c, neon(txt, 70 if i else 110, col, font='anton'), c.width / 2, c.height / 2)
                paste_c(fr, c, SAFE_CX - 210 + i * 420, 590, sc)
        tpc = word_t(4, 'seulement')
        if t > tpc:
            paste_c(fr, neon('PC : PAS ANNONCÉ', 64, (255, 70, 90), font='mont'), SAFE_CX, 790, pop(t, tpc))
        tp = word_t(4, '79,99')
        if t > tp:
            sc = pop(t, tp, 0.3)
            c = card(560, 220, YELLOW, fill=(50, 20, 0)).copy()
            paste_c(c, neon('79,99 €', 150, YELLOW), c.width / 2, c.height / 2)
            paste_c(fr, c, SAFE_CX, 1010, sc * (1 + 0.04 * math.sin((t - tp) * 12) * max(0, 1 - (t - tp))), rot=-3)
    elif seg == 5:
        chip(fr, t, s0 + 0.05, '3/5')
        tv = word_t(5, 'VICE')
        if t > tv - 0.1:
            flick = 1.0 if (t - tv) > 0.5 or int((t - tv) * 20) % 3 else 0.3
            paste_c(fr, neon('VICE', 300, PINK, glow=flick), SAFE_CX, 640, pop(t, tv - 0.1), rot=6)
            paste_c(fr, neon('CITY', 230, CYAN, glow=flick), SAFE_CX + 40, 880, pop(t, tv + 0.15), rot=6)
        tl = word_t(5, 'LEONIDA')
        if t > tl:
            paste_c(fr, neon('ÉTAT DE LEONIDA', 70, YELLOW, font='mont'), SAFE_CX, 1070, pop(t, tl))
    elif seg == 6:
        chip(fr, t, s0 + 0.05, '4/5')
        for i, (name, col, w0) in enumerate([('LUCIA', PINK, 'LUCIA'), ('JASON', CYAN, 'JASON')]):
            tt = word_t(6, w0)
            sc = pop(t, tt - 0.1)
            if sc:
                c = card(400, 560, col).copy()
                paste_c(c, person(col, flip=bool(i)), c.width / 2, c.height / 2 - 40)
                paste_c(c, neon(name, 100, col), c.width / 2, c.height - 150)
                paste_c(fr, c, SAFE_CX - 215 + i * 430, 720, sc, rot=(4 if i == 0 else -4))
        tb = word_t(6, 'BONNIE')
        if t > tb:
            paste_c(fr, neon('BONNIE & CLYDE', 90, YELLOW), SAFE_CX, 1080 - 20, pop(t, tb))
    elif seg == 7:
        chip(fr, t, s0 + 0.05, '5/5')
        tp = word_t(7, 'PRÉCHARGEMENT')
        sc = pop(t, tp - 0.1)
        if sc:
            c = card(820, 360, CYAN).copy()
            d = ImageDraw.Draw(c)
            paste_c(c, neon('PRÉCHARGEMENT', 80, CYAN, font='mont'), c.width / 2, 150)
            prog = ease_out((t - tp) / 4.0)
            x0, y0, x1, y1 = 120, 250, c.width - 120, 310
            d.rounded_rectangle([x0, y0, x1, y1], 30, outline=WHITE, width=4)
            d.rounded_rectangle([x0 + 8, y0 + 8, x0 + 8 + (x1 - x0 - 16) * prog, y1 - 8], 22, fill=PINK)
            paste_c(c, neon(f'{int(prog * 100)} %', 60, WHITE, font='mont'), c.width / 2, 370)
            paste_c(fr, c, SAFE_CX, 650, sc)
        tm = word_t(7, 'MAINTENANT')
        if t > tm:
            paste_c(fr, neon('LANCE-LE !', 150, YELLOW), SAFE_CX, 1010, pop(t, tm), rot=-5)
    elif seg == 8:
        paste_c(fr, neon('VRAIE QUESTION', 110, YELLOW), SAFE_CX, 400, pop(t, s0 + 0.1))
        for i, (txt, col, w0, pct) in enumerate([('JE POSE MA JOURNÉE', CYAN, 'POSES', 0.62), ('JE SUIS « MALADE »', PINK, 'PORTER', 0.38)]):
            tt = word_t(8, w0)
            sc = pop(t, tt)
            if sc:
                c = card(820, 190, col).copy()
                d = ImageDraw.Draw(c)
                fill = ease_out((t - tt) / 1.5) * pct
                d.rounded_rectangle([70, 70, 70 + 780 * fill, 240], 32, fill=col + (90,))
                paste_c(c, neon(txt, 52, col, font='mont'), c.width / 2 - 70, c.height / 2)
                paste_c(c, neon(f'{int(fill * 100)}%', 60, WHITE, font='mont'), c.width - 140, c.height / 2)
                paste_c(fr, c, SAFE_CX, 640 + i * 250, sc)
    elif seg == 9:
        tl, tj = word_t(9, 'LUCIA'), word_t(9, 'JASON')
        paste_c(fr, neon('LUCIA', 190, PINK), SAFE_CX, 470, pop(t, tl - 0.1), rot=-4)
        paste_c(fr, neon('OU', 110, YELLOW), SAFE_CX, 660, pop(t, tl + 0.25))
        paste_c(fr, neon('JASON', 190, CYAN), SAFE_CX, 850, pop(t, tj - 0.1), rot=4)
        tc = word_t(9, 'COMMENTAIRE')
        if t > tc:
            e = emoji_img('👇', 120)
            bob = 15 * math.sin((t - tc) * 9)
            paste_c(fr, e, SAFE_CX, 1060 + bob, pop(t, tc))
    elif seg == 10:
        ta = word_t(10, 'ABONNE')
        sc = pop(t, ta - 0.05, 0.3)
        if sc:
            pulse = 1 + 0.05 * math.sin((t - ta) * 7)
            c = card(700, 220, PINK, fill=(255, 46, 151), radius=110).copy()
            paste_c(c, neon('ABONNE-TOI', 120, WHITE, core=WHITE, glow=0.3), c.width / 2, c.height / 2)
            paste_c(fr, c, SAFE_CX, 620, sc * pulse)
        tj = word_t(10, 'JOUR')
        if t > tj:
            paste_c(fr, neon('JOUR J = 19.11', 120, CYAN), SAFE_CX, 900, pop(t, tj))
    elif seg == 11:
        tt = word_t(11, '5') - 0.1
        if t > tt:
            x = (t - tt) / (60 - tt)
            paste_c(fr, neon('J-5', 420, PINK), SAFE_CX, 700, pop(t, tt, 0.3) * (1 + 0.15 * x))


# ---------------------------------------------------------------- sous-titres
def caption_groups(line):
    words = line['words']
    groups, cur = [], []
    for i, wd in enumerate(words):
        if is_emoji(wd[0]) and cur:
            cur.append(wd)
            continue
        cur.append(wd)
        txt = wd[0]
        n_words = sum(1 for w in cur if not is_emoji(w[0]))
        nxt = words[i + 1][0] if i + 1 < len(words) else ''
        if n_words >= 3 or txt.endswith(('...', '?', ':')) or (nxt and is_emoji(nxt) is False and len(' '.join(w[0] for w in cur) + nxt) > 16):
            if nxt and is_emoji(nxt):
                continue
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)
    return groups


GROUPS = [caption_groups(l) for l in LINES]


def draw_captions(fr, t):
    li = None
    for i, l in enumerate(LINES):
        if l['start'] <= t < (LINES[i + 1]['start'] if i + 1 < len(LINES) else 60.1):
            li = i
    if li is None:
        return
    groups = GROUPS[li]
    g = None
    for gr in groups:
        if t >= gr[0][2] - 0.02:
            g = gr
    if g is None:
        return
    if t > LINES[li]['speech_end'] + 0.6:
        return
    size = 92
    f = mont(size)
    # mise en page sur une ou deux lignes
    items = []
    for w, k, tt in g:
        if is_emoji(w):
            items.append(('E', w, k, tt, size))
        else:
            items.append(('T', w.upper() if k else w.upper(), k, tt, f.getlength(w.upper())))
    space = 26
    rows, row, rw = [], [], 0
    maxw = 860
    for it in items:
        wdt = it[4] if it[0] == 'T' else size
        if row and rw + space + wdt > maxw:
            rows.append(row)
            row, rw = [], 0
        row.append((it, wdt))
        rw += (space if len(row) > 1 else 0) + wdt
    rows.append(row)
    y = 1300 - (len(rows) - 1) * 60
    gi = groups.index(g)
    kw_col = YELLOW if (li + gi) % 2 == 0 else PINK
    for row in rows:
        total = sum(w for _, w in row) + space * (len(row) - 1)
        x = SAFE_CX - total / 2
        for (kind, w, k, tt, _), wdt in row:
            if t < tt - 0.02:
                x += wdt + space
                continue
            age = t - tt
            sc = 1.0 + 0.18 * max(0, 1 - age / 0.15)
            active = age < 0.35
            if kind == 'E':
                paste_c(fr, emoji_img(w, 96), x + wdt / 2, y, sc)
            else:
                col = kw_col if k else (WHITE if not active else (255, 255, 255))
                key = (w, col, size)
                im = text_stroke(w, col, size)
                paste_c(fr, im, x + wdt / 2, y, sc if (k or active) else 1.0)
            x += wdt + space
        y += 120


@functools.lru_cache(None)
def text_stroke(w, col, size):
    f = mont(size)
    bb = f.getbbox(w, stroke_width=10)
    im = Image.new('RGBA', (bb[2] - bb[0] + 30, bb[3] - bb[1] + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # ombre portée
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((15 - bb[0] + 6, 20 - bb[1] + 8), w, font=f, fill=(0, 0, 0, 160), stroke_width=10, stroke_fill=(0, 0, 0, 160))
    sh = sh.filter(ImageFilter.GaussianBlur(4))
    im = Image.alpha_composite(im, sh)
    ImageDraw.Draw(im).text((15 - bb[0], 20 - bb[1]), w, font=f, fill=col, stroke_width=10, stroke_fill=(0, 0, 0))
    return im


# ---------------------------------------------------------------- habillage permanent
def overlays(fr, t):
    d = ImageDraw.Draw(fr)
    # barre de progression en haut
    p = t / 60.0
    d.rectangle([0, 0, W, 14], fill=(0, 0, 0, 150))
    grad_w = int(W * p)
    if grad_w > 0:
        g = np.zeros((14, grad_w, 3), np.uint8)
        xs = np.linspace(0, 1, grad_w)
        for c in range(3):
            g[:, :, c] = (PINK[c] * (1 - xs) + CYAN[c] * xs)[None, :]
        fr.paste(Image.fromarray(g), (0, 0))
    # badge compte à rebours (à partir de 3,1 s, quand le gros J-5 du hook a disparu)
    if 3.1 <= t < 56.8:
        b = badge()
        fr.alpha_composite(b, (40, 190))


@functools.lru_cache(None)
def badge():
    c = card(230, 100, PINK, fill=(30, 0, 40), radius=50, width=5).copy()
    paste_c(c, neon('J-5 ⏳', 1, PINK), 0, 0)  # amorce cache
    t = neon('J-5', 70, PINK)
    paste_c(c, t, c.width / 2 - 25, c.height / 2)
    e = emoji_img('⏳', 56)
    paste_c(c, e, c.width / 2 + 75, c.height / 2)
    return c


# ---------------------------------------------------------------- découpage des plans
KINDS = ['grid', 'city', 'tunnel', 'beach', 'road']
SEG_KINDS = {
    0: ['grid', 'tunnel'], 1: ['city', 'grid'], 2: ['tunnel', 'city'], 3: ['grid', 'road', 'tunnel'],
    4: ['city', 'tunnel', 'grid'], 5: ['beach', 'city', 'beach'], 6: ['road', 'grid', 'city'],
    7: ['tunnel', 'grid', 'road'], 8: ['city', 'beach', 'grid'], 9: ['tunnel', 'road', 'grid'],
    10: ['grid', 'city'], 11: ['tunnel', 'grid'],
}


def shots():
    """Liste des plans (début, fin, type, zoom0, zoom1, pan, teinte) — un plan toutes les ~1,8 s."""
    rng = random.Random(42)
    out = []
    for seg in range(12):
        a, b = BOUNDS[seg], BOUNDS[seg + 1]
        n = max(1, round((b - a) / 1.85))
        ks = SEG_KINDS[seg]
        for j in range(n):
            s = a + (b - a) * j / n
            e = a + (b - a) * (j + 1) / n
            k = ks[j % len(ks)]
            z0 = rng.uniform(1.0, 1.06)
            z1 = z0 + rng.choice([0.07, -0.05, 0.09])
            z1 = max(1.0, z1)
            pan = (rng.uniform(-0.8, 0.8), rng.uniform(-0.4, 0.4))
            tint = rng.choice([None, PINK, CYAN, PURPLE, None])
            out.append((seg, s, e, k, z0, z1, pan, tint))
    return out


SHOTS = shots()
CUTS = sorted(set(round(s[1], 3) for s in SHOTS))[1:]
SEG_STARTS = BOUNDS[1:-1]

# mots-clés : instants des « punch-in »
PUNCH = sorted(tt for l in LINES for w, k, tt in l['words'] if k and not is_emoji(w))


def frame(t):
    sh = [s for s in SHOTS if s[1] <= t < s[2]] or [SHOTS[-1]]
    seg, s, e, k, z0, z1, pan, tint = sh[0]
    local = (t - s) / (e - s)
    fr = background(k, t, local, z0, z1, pan, tint)
    fr.alpha_composite(vignette())
    foreground(fr, seg, t)
    # punch-in global sur les mots-clés
    pz = 1.0
    for pt in PUNCH:
        if 0 <= t - pt < 0.25:
            pz = max(pz, 1 + 0.045 * (1 - (t - pt) / 0.25))
    if pz > 1.0:
        cw, ch = W / pz, H / pz
        fr = fr.transform((W, H), Image.EXTENT, ((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2), Image.BILINEAR)
    draw_captions(fr, t)
    overlays(fr, t)
    # flash blanc aux changements de partie (+ plus léger aux simples coupes)
    for c in CUTS:
        dt = t - c
        if 0 <= dt < 0.1:
            strong = any(abs(c - b) < 0.01 for b in SEG_STARTS)
            a = (0.55 if strong else 0.18) * (1 - dt / 0.1)
            fr = Image.blend(fr, Image.new('RGBA', (W, H), (255, 255, 255, 255)), a)
    # léger grain
    return fr.convert('RGB')


def render_segment(seg):
    a, b = BOUNDS[seg], BOUNDS[seg + 1]
    f0, f1 = round(a * FPS), round(b * FPS)
    tmp = f'seg/seg{seg:02d}.tmp.mp4'
    out = f'seg/seg{seg:02d}.mp4'
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p', '-r', str(FPS), tmp], stdin=subprocess.PIPE)
    for fi in range(f0, f1):
        p.stdin.write(frame(fi / FPS).tobytes())
    p.stdin.close()
    if p.wait() == 0:
        os.replace(tmp, out)
    return seg


if __name__ == '__main__':
    if sys.argv[1] == 'still':
        os.makedirs('stills', exist_ok=True)
        for ts in sys.argv[2:]:
            frame(float(ts)).save(f'stills/f_{ts}.jpg', quality=88)
    elif sys.argv[1] == 'all':
        os.makedirs('seg', exist_ok=True)
        from multiprocessing import Pool
        with Pool(min(12, os.cpu_count())) as pool:
            for s in pool.imap_unordered(render_segment, range(12)):
                print('segment', s, 'ok', flush=True)

#!/usr/bin/env python3
"""Chroma key (verde -> alpha), despill, centrado por bbox y escala uniforme para turntable."""
import os, glob
import numpy as np
from PIL import Image

RAW = "/home/dorti/clients/ai-scroll-demo/assets/kb_raw"
OUT = "/home/dorti/clients/ai-scroll-demo/assets/kb"
os.makedirs(OUT, exist_ok=True)

CANVAS = 600
TARGET_H = 520

def process(path, dst):
    img = Image.open(path).convert("RGB")
    a = np.array(img).astype(np.int16)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    # mascara verde: verde claramente dominante
    green = (g - np.maximum(r, b)) > 45
    alpha = np.where(green, 0, 255).astype(np.uint8)
    # despill: quitar tinte verde del metal
    g2 = np.minimum(g, np.maximum(r, b))
    rgba = np.stack([r, g2, b, alpha], axis=-1).astype(np.uint8)
    out = Image.fromarray(rgba, "RGBA")
    bbox = out.getbbox()
    if bbox is None:
        print(f"  SKIP {dst}: vacio")
        return False
    x0, y0, x1, y1 = bbox
    # margen 24px
    m = 24
    x0 = max(0, x0-m); y0 = max(0, y0-m); x1 = min(out.width, x1+m); y1 = min(out.height, y1+m)
    obj = out.crop((x0, y0, x1, y1))
    # escalar a TARGET_H manteniendo aspecto
    scale = TARGET_H / obj.height
    nw, nh = int(obj.width*scale), TARGET_H
    obj = obj.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    canvas.paste(obj, ((CANVAS - nw)//2, (CANVAS - nh)//2), obj)
    canvas.save(dst)
    print(f"  OK {os.path.basename(dst)} ({nw}x{nh})")
    return True

files = sorted(glob.glob(os.path.join(RAW, "kb_*.png")))
print(f"{len(files)} frames raw")
ok = 0
for i, f in enumerate(files):
    dst = os.path.join(OUT, f"kb_{i:02d}.png")
    if process(f, dst):
        ok += 1
print(f"DONE {ok}/{len(files)} -> {OUT}")

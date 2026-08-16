#!/usr/bin/env python3
"""Genera turntable de 12 angulos de una kettlebell fotorrealista (fondo verde para chroma key)."""
import requests, json, time, random, os, shutil, sys

COMFY = "http://127.0.0.1:8190"
OUTDIR = "/home/dorti/clients/ai-scroll-demo/assets/kb_raw"
os.makedirs(OUTDIR, exist_ok=True)
WF = "/home/dorti/neo-libros/chatgpt-profesionales/workflows/portada_2x3.json"

SEED = 424242
BASE_PROMPT = (
    "professional studio product photograph of a cast iron kettlebell with polished chrome handle "
    "and a red stripe band around the ball, standing on its flat base on the ground, "
    "solid uniform bright green background, softbox studio lighting, soft reflection on the floor, "
    "photorealistic, ultra detailed, centered composition, full object visible, 8k"
)
ANGLE = ", kettlebell viewed from exactly {deg} degrees around the vertical axis"
NEG = (
    "worst quality, low quality, blurry, deformed, ugly, distorted, "
    "text, letters, words, numbers, watermark, signature, logo, "
    "person, hand, human, background objects, other objects, "
    "cartoon, illustration, painting, 3d render, wireframe, "
    "oversaturated, overexposed, grain, noise, jpeg artifacts, pixelated"
)

def generate(idx, deg, seed):
    with open(WF) as f:
        wf = json.load(f)
    prompt = BASE_PROMPT + ANGLE.format(deg=deg)
    for nid, node in wf.items():
        if not isinstance(node, dict):
            continue
        inputs = node.get("inputs", {})
        ct = node.get("class_type", "")
        if ct == "CLIPTextEncode":
            t = str(inputs.get("text", ""))
            if "PROMPT_HERE" in t:
                inputs["text"] = prompt
            elif "NEGATIVE_PROMPT_HERE" in t:
                inputs["text"] = NEG
        elif ct == "KSampler":
            inputs["seed"] = seed
            inputs["steps"] = 30
        elif ct == "EmptyLatentImage":
            inputs["width"], inputs["height"] = 768, 768
    r = requests.post(f"{COMFY}/prompt", json={"prompt": wf}, timeout=15)
    res = r.json()
    if "prompt_id" not in res:
        print(f"  ERROR {idx}: {res}")
        return False
    pid = res["prompt_id"]
    t0 = time.time()
    while time.time() - t0 < 240:
        try:
            hh = requests.get(f"{COMFY}/history/{pid}", timeout=5).json()
            if pid in hh:
                for nid, no in hh[pid].get("outputs", {}).items():
                    for img in no.get("images", []):
                        src = os.path.join("/home/dorti/jarvis/ComfyUI/output", img.get("subfolder", ""), img.get("filename", ""))
                        if os.path.exists(src):
                            dst = os.path.join(OUTDIR, f"kb_{idx:02d}_{deg}.png")
                            shutil.copy2(src, dst)
                            os.remove(src)
                            print(f"  OK {idx:02d} deg={deg} ({time.time()-t0:.0f}s)")
                            return True
        except Exception:
            pass
        time.sleep(2)
    print(f"  TIMEOUT {idx}")
    return False

def main():
    print(f"Generando 12 angulos (seed={SEED})...")
    ok = 0
    for i in range(12):
        deg = i * 30
        if generate(i, deg, SEED):
            ok += 1
        time.sleep(1)
    print(f"DONE {ok}/12")

if __name__ == "__main__":
    main()

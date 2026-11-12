"""Paso 3 · Motor de cortes.
1) Selección editorial por palabras: project.json -> "order": [{"clip": "IMG_0132", "keep": [[0, 16]]}, ...]
   (orden narrativo; rangos de índices de palabra inclusive, de work/transcript.txt).
2) Quita silencios dentro de cada rango (energía del audio, > min_silence s).
3) Quita muletillas sostenidas ("eeeh", "mmm") en huecos o al borde de palabras estiradas.
4) Nunca invade palabras descartadas vecinas (evita que se cuelen repeticiones).
Salida: work/edl.json  [{clip, a, b, words:[{i, w, s, e}]}]
"""
import json, os
import numpy as np
from common import project_from_argv, read_audio

HOP = 0.01

def features(x, sr=16000):
    hop, win = int(sr * HOP), int(sr * 0.03)
    n = (len(x) - win) // hop
    fr = np.stack([x[i * hop:i * hop + win] for i in range(n)]) * np.hanning(win)
    rms = 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9)
    spec = np.log(np.abs(np.fft.rfft(fr, 512, axis=1))[:, 4:160] + 1e-6)
    spec -= spec.mean(1, keepdims=True)
    flux = np.r_[0, np.sqrt(((spec[1:] - spec[:-1]) ** 2).mean(1))]
    return rms, flux

def runs(mask):
    out, i = [], 0
    while i < len(mask):
        if mask[i]:
            j = i
            while j < len(mask) and mask[j]: j += 1
            out.append((i, j)); i = j
        else: i += 1
    return out

def main():
    P = project_from_argv(); C = P.cfg
    TX = json.load(open(P.p("work", "transcript.json"), encoding="utf-8"))
    FPS = C.get("fps", 30)
    MIN_SIL = C.get("min_silence", 0.20); PAD_IN, PAD_OUT = C.get("pad_in", 0.07), C.get("pad_out", 0.11)
    THR = C.get("voice_threshold", 0.20)
    ORDER = [(o["clip"], [tuple(r) for r in o["keep"]]) for o in C["order"]]
    FIX = {tuple([k.rsplit(":", 1)[0], int(k.rsplit(":", 1)[1])]): v for k, v in C.get("fix", {}).items()}
    edl, report = [], []
    for clip, ranges in ORDER:
        x = read_audio(P.source_file(clip))
        rms, flux = features(x)
        floor, peak = np.percentile(rms, 8), np.percentile(rms, 97)
        voiced = rms > floor + THR * (peak - floor)
        for a, b in runs(~voiced):
            if b - a < 6 and a > 0: voiced[a:b] = True
        words = TX[clip]["words"]
        fsm = np.convolve(flux, np.ones(9) / 9, "same")
        stable = voiced & (fsm < np.percentile(fsm[voiced], 22))
        fillers = [(a * HOP, b * HOP) for a, b in runs(stable) if (b - a) * HOP >= 0.30]
        for (i0, i1) in ranges:
            s0, s1 = words[i0]["s"], words[i1]["e"]
            left = max(0, s0 - 0.25) if i0 == 0 else max(s0 - 0.25, words[i0 - 1]["e"] + 0.02)
            right = s1 + 0.35 if i1 + 1 >= len(words) else min(s1 + 0.35, words[i1 + 1]["s"] - 0.02)
            lo, hi = int(left / HOP), int(min(len(rms) * HOP, right) / HOP)
            seg = voiced[lo:hi].copy()
            for fa, fb in fillers:
                inside = any(w["s"] + 0.05 < fa and fb < w["e"] - 0.05 for w in words[i0:i1 + 1])
                over = [w for w in words[i0:i1 + 1] if w["s"] < fb and w["e"] > fa]
                stretched = any((w["e"] - w["s"]) > 0.47 + 0.075 * len(w["w"]) for w in over)
                if (not over or stretched) and not inside:
                    a, b = int(fa / HOP) - lo, int(fb / HOP) - lo
                    if 0 <= a < len(seg):
                        seg[max(0, a):max(0, b)] = False; report.append(f"{clip}: muletilla {fa:.2f}-{fb:.2f}")
            vr = runs(seg)
            if not vr: continue
            merged = [list(vr[0])]
            for a, b in vr[1:]:
                if (a - merged[-1][1]) * HOP < MIN_SIL: merged[-1][1] = b
                else: merged.append([a, b])
            for a, b in merged:
                if (b - a) * HOP < 0.12: continue
                A = max((lo + a) * HOP - PAD_IN, left); B = min((lo + b) * HOP + PAD_OUT, right + 0.02)
                A = max(0, round(A * FPS) / FPS); B = round(B * FPS) / FPS
                if edl and edl[-1]["clip"] == clip and A <= edl[-1]["b"] + 1e-3:
                    edl[-1]["b"] = max(edl[-1]["b"], B); continue
                edl.append({"clip": clip, "a": A, "b": B})
    for s in edl: s["words"] = []
    for clip, rr in ORDER:
        segs = [s for s in edl if s["clip"] == clip]; ws = TX[clip]["words"]
        for (i0, i1) in rr:
            for i in range(i0, i1 + 1):
                w = ws[i]
                ov = [max(0, min(w["e"], s["b"]) - max(w["s"], s["a"])) for s in segs]
                k = max(range(len(segs)), key=lambda j: (ov[j], -abs(segs[j]["a"] - w["s"])))
                if ov[k] <= 0:
                    k = min(range(len(segs)), key=lambda j: min(abs(segs[j]["a"] - w["e"]), abs(segs[j]["b"] - w["s"])))
                s = segs[k]
                a_, b_ = min(max(w["s"], s["a"]), s["b"]), max(min(w["e"], s["b"]), s["a"])
                s["words"].append({"i": i, "w": FIX.get((clip, i), w["w"]), "s": a_, "e": max(b_, a_ + 0.05)})
    json.dump(edl, open(P.p("work", "edl.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    used = sum(TX[c]["duration"] for c, _ in ORDER)
    print("\n".join(report))
    print(f"segmentos={len(edl)}  duración={sum(s['b'] - s['a'] for s in edl):.1f}s  (tomas usadas {used:.1f}s)")

if __name__ == "__main__":
    main()

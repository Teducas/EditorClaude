"""Mapa toma/palabra -> segundo en el montaje (según work/edl.json). Lo usan las animaciones,
las tarjetas y el constructor del borrador para sincronizar con la voz."""
import json
from common import parse_anchor

class Timeline:
    def __init__(self, P):
        self.P = P
        self.edl = json.load(open(P.p("work", "edl.json"), encoding="utf-8"))
        t = 0.0
        for s in self.edl:
            s["t"] = t; t += s["b"] - s["a"]
        self.total = t

    def src_to_tl(self, clip, src):
        segs = [s for s in self.edl if s["clip"] == clip]
        for s in segs:
            if src <= s["b"]: return s["t"] + max(0.0, src - s["a"])
        return segs[-1]["t"] + segs[-1]["b"] - segs[-1]["a"]

    def word(self, clip, i, edge="s"):
        for s in self.edl:
            if s["clip"] != clip: continue
            for w in s["words"]:
                if w["i"] == i: return self.src_to_tl(clip, w[edge])
        raise KeyError(f"La palabra {clip}:{i} no está en el montaje (¿se descartó en 'order'?)")

    def at(self, anchor):
        """'IMG_0136:9:e+0.3' -> segundo del montaje"""
        if isinstance(anchor, (int, float)): return float(anchor)
        clip, i, edge, off = parse_anchor(anchor)
        return round(self.word(clip, i, edge) + off, 3)

    def words(self):
        return [{"clip": s["clip"], "i": w["i"], "w": w["w"], "s": self.src_to_tl(s["clip"], w["s"]), "e": self.src_to_tl(s["clip"], w["e"])}
                for s in self.edl for w in s["words"]]

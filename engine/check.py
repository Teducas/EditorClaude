"""Paso 4 · Control de calidad del corte: ensambla el audio del montaje, lo vuelve a transcribir
y escribe work/check.txt con el texto de cada segmento. Se lee buscando: palabras perdidas,
repeticiones que se colaron y muletillas (marcadas <<MULETILLA?).
"""
import json, os, wave
import numpy as np
from common import project_from_argv, read_audio

FILLERS = {"eh", "ehh", "mmm", "mm", "este", "ah", "pues", "em", "eeh", "um", "ehm"}

def main():
    P = project_from_argv()
    edl = json.load(open(P.p("work", "edl.json"), encoding="utf-8"))
    cache, parts, marks, t = {}, [], [], 0.0
    for s in edl:
        if s["clip"] not in cache: cache[s["clip"]] = read_audio(P.source_file(s["clip"]))
        x = cache[s["clip"]][int(s["a"] * 16000):int(s["b"] * 16000)].copy()
        f = min(160, len(x) // 2); x[:f] *= np.linspace(0, 1, f); x[-f:] *= np.linspace(1, 0, f)
        parts.append(x); marks.append((t, s)); t += len(x) / 16000
    audio = np.concatenate(parts)
    with wave.open(P.p("work", "corte_audio.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
        w.writeframes((np.clip(audio, -1, 1) * 32767).astype(np.int16).tobytes())
    from faster_whisper import WhisperModel
    model = WhisperModel(P.cfg.get("whisper_model", "medium"), device="cpu", compute_type="int8")
    segs, _ = model.transcribe(audio, language=P.cfg.get("language", "es"), word_timestamps=True,
                               condition_on_previous_text=False, initial_prompt="Eh, este, o sea, mmm, ehh, pues, ah, bueno.")
    words = [w for s in segs for w in s.words]
    out = []
    for i, (t0, s) in enumerate(marks):
        t1 = marks[i + 1][0] if i + 1 < len(marks) else t
        ws = [w for w in words if t0 - 0.05 <= (w.start + w.end) / 2 < t1]
        txt = " ".join(w.word.strip() for w in ws)
        flag = " <<MULETILLA?" if any(w.word.strip(" ,.¿?").lower() in FILLERS and w.probability < 0.9 for w in ws) else ""
        flag += " <<VACÍO" if not ws else ""
        out.append(f"{i:3d} {t0:7.2f} {s['clip']} [{s['a']:.2f}-{s['b']:.2f}] {txt}{flag}")
    open(P.p("work", "check.txt"), "w", encoding="utf-8").write("\n".join(out))
    print("\n".join(out)); print("->", P.p("work", "check.txt"), "| audio:", P.p("work", "corte_audio.wav"))

if __name__ == "__main__":
    main()

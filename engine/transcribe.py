"""Paso 1 · Transcribe cada toma con marcas de tiempo por palabra (faster-whisper, CPU).
Salida: work/transcript.json y work/transcript.txt (palabras numeradas, pausas largas [x.xx] y
palabras dudosas con '?'), que es lo que se lee para decidir el montaje.
"""
import json, os, sys
from common import project_from_argv, read_audio

def main():
    P = project_from_argv()
    from faster_whisper import WhisperModel
    model = WhisperModel(P.cfg.get("whisper_model", "medium"), device="cpu", compute_type="int8")
    out_json = P.p("work", "transcript.json")
    result = json.load(open(out_json, encoding="utf-8")) if os.path.exists(out_json) else {}
    for clip in P.clips():
        if clip in result: continue
        audio = read_audio(P.source_file(clip))
        segs, info = model.transcribe(audio, language=P.cfg.get("language", "es"), word_timestamps=True,
                                      vad_filter=False, condition_on_previous_text=False,
                                      initial_prompt=P.cfg.get("whisper_prompt", "Eh, este, o sea, mmm, bueno, pues, ehh, ah."))
        words = [{"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3), "p": round(w.probability, 3)} for s in segs for w in s.words]
        result[clip] = {"duration": info.duration, "words": words}
        json.dump(result, open(out_json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(clip, " ".join(x["w"] for x in words), flush=True)
    write_txt(P, result)

def write_txt(P, result):
    lines = []
    for clip, c in result.items():
        prev, row = 0.0, []
        for i, w in enumerate(c["words"]):
            if w["s"] - prev > 0.25: row.append(f"[{w['s'] - prev:.2f}]")
            row.append(f"{i}:{w['w']}{'?' if w['p'] < 0.5 else ''}@{w['s']:.2f}")
            prev = w["e"]
        lines.append(f"## {clip} ({c['duration']:.1f}s)\n" + " ".join(row) + "\n")
    open(P.p("work", "transcript.txt"), "w", encoding="utf-8").write("\n".join(lines))
    print("->", P.p("work", "transcript.txt"))

if __name__ == "__main__":
    main()

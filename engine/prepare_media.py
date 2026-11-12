"""Paso 5 · Prepara las tomas usadas para CapCut:
- hornea la rotación de los metadatos (los iPhone graban girados) para que CapCut no las muestre al revés,
- mantiene la resolución original (4K permite acercar sin perder nitidez),
- limpia la voz (paso alto 80 Hz, reducción de ruido suave, compresor, limitador) y la nivela a voice_lufs.
Usa el codificador por hardware disponible (Intel QSV, NVIDIA NVENC, AMD AMF) o libx264.
"""
import json, os, re, subprocess
from common import project_from_argv

def pick_encoder():
    enc = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True).stdout
    for name, args in (("h264_nvenc", ["-cq", "19", "-preset", "p5"]), ("h264_qsv", ["-global_quality", "20", "-preset", "faster"]),
                       ("h264_amf", ["-quality", "quality", "-rc", "cqp", "-qp_i", "19", "-qp_p", "21"])):
        if name in enc:
            test = subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=s=256x256:d=0.2", "-c:v", name, *args, "-f", "null", "-"], capture_output=True)
            if test.returncode == 0: return name, args
    return "libx264", ["-crf", "18", "-preset", "fast"]

def main():
    P = project_from_argv()
    edl = json.load(open(P.p("work", "edl.json"), encoding="utf-8"))
    target = P.cfg.get("voice_lufs", -17.5)
    enc, args = pick_encoder(); print("codificador:", enc)
    for clip in dict.fromkeys(s["clip"] for s in edl):
        out = P.p("media", clip + ".mp4")
        if os.path.exists(out): print(clip, "ya preparado"); continue
        src = P.source_file(clip)
        meas = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", src, "-vn", "-af", "highpass=f=80,afftdn=nf=-30,loudnorm=print_format=json",
                               "-f", "null", "-"], capture_output=True, text=True).stderr
        i = float(re.search(r'"input_i"\s*:\s*"(-?[\d.]+)"', meas).group(1))
        gain = round(target - i, 2)
        af = f"highpass=f=80,afftdn=nf=-30,volume={gain}dB,acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=1.5dB,alimiter=limit=0.89"
        vf = [] if enc != "h264_qsv" else ["-pix_fmt", "nv12"]
        r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-map", "0:v:0", "-map", "0:a:0", "-c:v", enc, *args, *vf,
                            "-af", af, "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-movflags", "+faststart",
                            "-metadata:s:v:0", "rotate=0", out])
        print(clip, f"voz {i:.1f} -> {target} LUFS", "OK" if r.returncode == 0 else "ERROR")

if __name__ == "__main__":
    main()

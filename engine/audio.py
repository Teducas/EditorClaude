# Paso 8 · Música de fondo y efectos originales (síntesis con numpy/scipy): libres de derechos, uso comercial.
# Salida: audio/musica_fondo.wav (dura el montaje), musica_cierre.wav, sfx_whoosh(.out), sfx_pop, sfx_ding
import sys, os, wave
import numpy as np

OUT = None
SR = 48000
rng = np.random.default_rng(11)

def save(name, x):
    x = np.asarray(x, np.float32)
    if x.ndim == 1: x = np.stack([x, x], 1)
    peak = np.abs(x).max() or 1
    x = x / peak * 0.89
    with wave.open(os.path.join(OUT, name), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())
    print("ok", name, f"{len(x) / SR:.1f}s")

def midi(n): return 440 * 2 ** ((n - 69) / 12)

def lowpass(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); y = np.zeros_like(x); s = 0.0
    # filtro de un polo (vectorizado por bloques sería más rápido; suficiente aquí)
    from scipy.signal import lfilter
    return lfilter([1 - a], [1, -a], x)

def reverb(x, secs=2.4, mix=0.3):
    from scipy.signal import fftconvolve
    n = int(SR * secs)
    ir = rng.standard_normal((n, 2)) * np.exp(-np.linspace(0, 7, n))[:, None]
    ir[:, 0] = lowpass(ir[:, 0], 5000); ir[:, 1] = lowpass(ir[:, 1], 5000)
    ir /= np.abs(ir).sum(0).max() / 8
    if x.ndim == 1: x = np.stack([x, x], 1)
    wet = np.stack([fftconvolve(x[:, c], ir[:, c])[:len(x)] for c in range(2)], 1)
    return x * (1 - mix) + wet * mix

def music(dur):
    bpm = 84; beat = 60 / bpm; bar = beat * 4
    # Am9 - Fmaj7 - C(add9) - G6 : cálido, motivador, discreto
    chords = [[57, 60, 64, 67, 71], [53, 57, 60, 64, 69], [48, 55, 60, 62, 64], [55, 59, 62, 64, 67]]
    bass = [45, 41, 48, 43]
    n = int(dur * SR); t = np.arange(n) / SR
    pad = np.zeros(n); pl = np.zeros(n); bs = np.zeros(n)
    nb = int(dur / bar) + 2
    for b in range(nb):
        ch = chords[(b // 2) % 4]; t0 = b * bar
        if b % 2 == 0:  # acorde de pad cada 2 compases
            i0, i1 = int(t0 * SR), min(n, int((t0 + bar * 2 + 1.2) * SR))
            if i0 >= n: break
            tt = t[i0:i1] - t0
            env = np.minimum(1, tt / 1.4) * np.minimum(1, np.maximum(0, (bar * 2 + 1.2 - tt) / 1.2))
            for note in ch:
                f = midi(note)
                for det in (-0.12, 0.12):
                    ff = f * 2 ** (det / 12)
                    pad[i0:i1] += env * sum(np.sin(2 * np.pi * ff * k * tt + k) / k ** 1.6 for k in range(1, 6)) * 0.05
            fb = midi(bass[(b // 2) % 4])
            bs[i0:i1] += env * (np.sin(2 * np.pi * fb * tt) + 0.3 * np.sin(4 * np.pi * fb * tt)) * 0.22
        # arpegio de "piano" en corcheas
        pattern = [0, 2, 1, 3, 2, 4, 3, 1]
        for k, idx in enumerate(pattern):
            ts = t0 + k * beat / 2
            i0 = int(ts * SR); i1 = min(n, i0 + int(1.6 * SR))
            if i0 >= n: break
            tt = t[i0:i1] - ts
            f = midi(ch[idx] + 12)
            vel = 0.55 + 0.25 * (k % 2 == 0) + rng.uniform(-0.08, 0.08)
            env = np.exp(-tt * 3.2) * np.minimum(1, tt / 0.004)
            pl[i0:i1] += vel * env * (np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(4 * np.pi * f * tt) * np.exp(-tt * 6) + 0.12 * np.sin(6 * np.pi * f * tt) * np.exp(-tt * 9)) * 0.09
    mix = lowpass(pad, 2200) + lowpass(bs, 600) + pl
    out = reverb(mix, 2.6, 0.35)
    fade = np.ones(n); fi, fo = int(1.5 * SR), int(3 * SR)
    fade[:fi] = np.linspace(0, 1, fi); fade[-fo:] = np.linspace(1, 0, fo)
    return out * fade[:, None]

def whoosh(d=0.7, up=True):
    n = int(d * SR); t = np.linspace(0, 1, n)
    noise = rng.standard_normal(n)
    from scipy.signal import butter, sosfilt
    out = np.zeros(n); steps = 24
    for s in range(steps):  # barrido de filtro paso banda
        a, b = s * n // steps, (s + 1) * n // steps
        f = 300 + (5200 if up else 2500) * (s / steps if up else 1 - s / steps)
        sos = butter(2, [f * 0.6, f * 1.4], "band", fs=SR, output="sos")
        out[a:b] = sosfilt(sos, noise)[a:b]
    env = np.sin(np.pi * t ** (0.6 if up else 1.4)) ** 2
    st = np.stack([out * env * (1 - 0.5 * t), out * env * (0.5 + 0.5 * t)], 1)
    return reverb(st, 0.8, 0.25)

def pop_sfx():
    d = 0.18; n = int(d * SR); t = np.arange(n) / SR
    f = 900 * np.exp(-t * 18) + 380
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 28)
    return reverb(x, 0.4, 0.15)

def ding():
    d = 1.2; n = int(d * SR); t = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * midi(84 + k) * t) * np.exp(-t * (4 + k)) / (1 + k) for k in (0, 7, 12))
    return reverb(x, 1.2, 0.3)

if __name__ == "__main__":
    from common import project_from_argv
    from timeline import Timeline
    P = project_from_argv(); OUT = P.p("audio")
    dur = Timeline(P).total + 1.0
    save("musica_fondo.wav", music(dur))
    rng = np.random.default_rng(23)
    save("musica_cierre.wav", music(9.5))
    save("sfx_whoosh.wav", whoosh(0.7, True))
    save("sfx_whoosh_out.wav", whoosh(0.6, False))
    save("sfx_pop.wav", pop_sfx())
    save("sfx_ding.wav", ding())
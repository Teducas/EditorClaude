"""API para los archivos de escenas de cada proyecto (projects/<video>/broll_scenes.py).

    from mg import *                 # dibujo, easing, colores de la marca, render
    from scenes_api import scene, at, wt

    @scene("01_licencia", at("IMG_0137:0"), at("IMG_0137:12:e+0.15"))
    def licencia():
        bg = background(1)
        ...
        def f(t):            # t = segundos desde el inicio de la toma de apoyo
            fr = drift(bg, t).copy(); ...; return fr
        return f

    @scene("99_cierre", 0, 7.0, outro=True)   # placa final: se coloca tras el último corte
"""
SCENES = {}
TL = None   # lo fija engine/broll.py

def scene(name, start, end, outro=False):
    def deco(fn):
        SCENES[name] = {"start": start, "end": end, "fn": fn, "outro": outro}
        return fn
    return deco

def at(anchor):
    """Segundo del montaje para 'CLIP:indice[:e][+seg]'."""
    return TL.at(anchor)

def wt(clip, i, edge="s"):
    """Segundo del montaje de la palabra i de la toma clip (inicio 's' o final 'e')."""
    return TL.word(clip, i, edge)

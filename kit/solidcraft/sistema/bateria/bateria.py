#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bateria autonoma de SolidCraft (v0.1).
Uso:
  python3 bateria.py                 -> puntua todos los casos con STL y escribe resultados.md/json
  python3 bateria.py enunciados      -> lista los enunciados (cotas) de los casos
  python3 bateria.py registrar ID VOL_BREP CARAS  -> guarda la medida de SolidCraft (measure) del caso
Solo libreria estandar. Los volumenes esperados se calculan a mano aqui, sin SolidCraft."""
import json, math, struct, sys, glob, os, datetime
from math import pi

AQUI = os.path.dirname(os.path.abspath(__file__))
SAL = os.path.join(AQUI, "salida")
SALIDA_PIEZAS = os.path.join(AQUI, "..", "salida")

def _escalera():
    return 20 * (30 + 20 + 10) * 40

# id: (nivel, titulo, enunciado, volumen esperado mm3, bbox X,Y,Z mm, patron STL)
CASOS = {
 "R1": (0, "Regresion: escuadra con cuna (foto 1)", "Pieza ya hecha: base 60x45x10 R15, pared 10, cuna O40/O20, nervadura 5, 2 agujeros O20.",
        53830.1, (60, 45, 50), os.path.join(SALIDA_PIEZAS, "escuadra_cuna_60x45x50_v0.1.stl")),
 "R2": (0, "Regresion: bloque con rampa (foto 2)", "Pieza ya hecha: perfil 70x70, rampa 40->15, ancho 50->30, media cana O20, ranura 10x5.",
        160000 - 9333.3333 - 4712.3890 - 828.125, (70, 50, 70), os.path.join(SALIDA_PIEZAS, "bloque_rampa_70x50x70_v0.1.stl")),
 "C01": (1, "Perfil en L extruido", "Perfil en L (plano XZ): (0,0),(60,0),(60,10),(10,10),(10,40),(0,40). Extrusion 30 en Y.",
        900 * 30, (60, 30, 40), "C01_*.stl"),
 "C02": (1, "Escalera de 3 peldanos", "Perfil (XZ): (0,0),(60,0),(60,10),(40,10),(40,20),(20,20),(20,30),(0,30). Extrusion 40 en Y.",
        _escalera(), (60, 40, 30), "C02_*.stl"),
 "C03": (2, "Taco con taladro y rebaje", "Bloque 40x40x20. Taladro pasante O8 centrado; rebaje O14 de 5 de profundidad desde la cara superior.",
        40*40*20 - pi*4**2*20 - pi*(7**2-4**2)*5, (40, 40, 20), "C03_*.stl"),
 "C04": (2, "Eje escalonado (revolucion)", "Cilindros coaxiales en Z: O30x20 abajo, O20x30, O10x15 arriba. Una sola pieza.",
        pi*(15**2*20 + 10**2*30 + 5**2*15), (30, 30, 65), "C04_*.stl"),
 "C05": (2, "Brida con patron circular", "Disco O80x8, agujero central O20 y 6 agujeros O6 en circulo O60 (patron circular).",
        pi*(40**2*8 - 10**2*8 - 6*3**2*8), (80, 80, 8), "C05_*.stl"),
 "C06": (3, "Cruce de taladros", "Cubo 40. Dos taladros pasantes O10, uno en X y otro en Y, ambos a z=20, que se cruzan.",
        64000 - (2*pi*25*40 - 16/3*125), (40, 40, 40), "C06_*.stl"),
 "C07": (3, "Base con pared y nervadura triangular", "Base 50x30x8; pared 8x30 de alto total 48 en un extremo; nervadura triangular de 5 de espesor, catetos 30 y 30, centrada.",
        50*30*8 + 8*30*40 + 0.5*30*30*5, (50, 30, 48), "C07_*.stl"),
 "C08": (3, "Bloque redondeado con agujero ciego", "Bloque 50x30x20, 4 aristas verticales R6, agujero ciego O12 de 10 de profundidad en la cara superior, centrado.",
        50*30*20 - 4*6**2*(1 - pi/4)*20 - pi*6**2*10, (50, 30, 20), "C08_*.stl"),
 "C09": (3, "Caja vaciada abierta", "Caja 60x40x30 vaciada con pared 3, abierta por arriba, esquinas vivas.",
        60*40*30 - 54*34*27, (60, 40, 30), "C09_*.stl"),
 "C10": (4, "Perfil en U con 3 agujeros en linea", "Perfil en U: exterior 60x30, cavidad 40x20 (paredes de 10), largo 40. 3 agujeros O5 pasantes en la base a x=-15,0,15 (patron lineal).",
        (60*30 - 40*20)*40 - 3*pi*2.5**2*10, (60, 40, 30), "C10_*.stl"),
}

# Centro de masas esperado (mm), calculado a mano: detecta piezas con el volumen bien pero un elemento mal colocado
COM = {
 "C01": (65/3, 15, 35/3),
 "C02": (70/3, 20, 35/3),
 "C03": (0, 0, (32000*10 - pi*16*20*10 - pi*33*5*17.5) / (40*40*20 - pi*16*20 - pi*33*5)),
 "C07": ((12000*25 + 9600*4 + 2250*18) / 23850, 15, (12000*4 + 9600*28 + 2250*18) / 23850),
 "C10": (0, 20, (1000*40*11 - 3*pi*6.25*10*5) / ((1000)*40 - 3*pi*6.25*10)),
}

def leer_stl(ruta):
    d = open(ruta, "rb").read()
    n = struct.unpack("<I", d[80:84])[0] if len(d) >= 84 else -1
    tris = []
    if len(d) == 84 + 50 * n:
        for i in range(n):
            v = struct.unpack("<12fH", d[84 + 50*i: 134 + 50*i])
            tris.append((v[3:6], v[6:9], v[9:12]))
    else:
        t = d.decode("latin-1").split()
        vs = [tuple(map(float, t[i+1:i+4])) for i, w in enumerate(t) if w == "vertex"]
        tris = [tuple(vs[i:i+3]) for i in range(0, len(vs) - 2, 3)]
    return tris

def analizar(tris):
    vol = 0.0; mn = [1e18]*3; mx = [-1e18]*3; aristas = {}; mom = [0.0]*3
    k = lambda p: (round(p[0], 3), round(p[1], 3), round(p[2], 3))
    for a, b, c in tris:
        t = (a[0]*(b[1]*c[2]-b[2]*c[1]) - a[1]*(b[0]*c[2]-b[2]*c[0]) + a[2]*(b[0]*c[1]-b[1]*c[0])) / 6.0
        vol += t
        for j in range(3):
            mom[j] += t * (a[j] + b[j] + c[j]) / 4.0
        for p in (a, b, c):
            for j in range(3):
                mn[j] = min(mn[j], p[j]); mx[j] = max(mx[j], p[j])
        ka, kb, kc = k(a), k(b), k(c)
        if ka == kb or kb == kc or ka == kc:
            continue
        for u, v in ((ka, kb), (kb, kc), (kc, ka)):
            aristas[(u, v)] = aristas.get((u, v), 0) + 1
    malas = sum(1 for (u, v), n in aristas.items() if n != 1 or aristas.get((v, u), 0) != 1)
    return vol, [mx[j]-mn[j] for j in range(3)], malas, len(tris), [mom[j]/vol for j in range(3)]

def puntuar(cid):
    niv, tit, enun, vexp, bexp, patron = CASOS[cid]
    r = {"id": cid, "nivel": niv, "titulo": tit, "vol_esperado": round(vexp, 3), "bbox_esperada": list(bexp)}
    rutas = glob.glob(patron if os.path.isabs(patron) else os.path.join(SAL, patron))
    if not rutas:
        r["estado"] = "sin STL"; r["puntos"] = None; return r
    ruta = sorted(rutas)[-1]
    vol, bb, malas, nt, com = analizar(leer_stl(ruta))
    r["stl"] = os.path.basename(ruta); r["triangulos"] = nt
    p = 0; notas = []
    if malas == 0: p += 25
    else: notas.append("malla no estanca (%d aristas)" % malas)
    ev = abs(vol - vexp) / vexp * 100; r["vol_stl_err_pct"] = round(ev, 4)
    if ev <= 0.5: p += 10
    else: notas.append("volumen STL fuera de 0,5 %")
    eb = max(abs(bb[j] - bexp[j]) for j in range(3)); r["bbox_stl"] = [round(x, 3) for x in bb]; r["bbox_err_mm"] = round(eb, 4)
    if eb <= 0.05: p += 25
    else: notas.append("caja envolvente fuera de 0,05 mm")
    r["com_stl"] = [round(x, 3) for x in com]
    if cid in COM:
        ec = max(abs(com[j] - COM[cid][j]) for j in range(3)); r["com_err_mm"] = round(ec, 4)
        if ec > 0.1: notas.append("centro de masas fuera de 0,1 mm")
    med = os.path.join(SAL, cid + ".medida.json")
    if os.path.exists(med):
        m = json.load(open(med)); eB = abs(m["volumen_brep"] - vexp) / vexp * 100
        r["vol_brep"] = m["volumen_brep"]; r["vol_brep_err_pct"] = round(eB, 5); r["caras"] = m.get("caras")
        if eB <= 0.02: p += 40
        else: notas.append("volumen B-rep fuera de 0,02 %")
    else:
        notas.append("sin medida B-rep (registrar)")
    r["puntos"] = p; r["estado"] = "OK" if (p == 100 and not any("centro" in n for n in notas)) else "REVISAR"; r["notas"] = notas
    return r

def main():
    a = sys.argv[1:]
    if a and a[0] == "enunciados":
        for c, v in CASOS.items():
            print("%s [N%d] %s\n    %s\n    esperado: V=%.2f mm3, caja=%s\n" % (c, v[0], v[1], v[2], v[3], v[4]))
        return
    if a and a[0] == "registrar":
        json.dump({"volumen_brep": float(a[2]), "caras": int(a[3]), "fecha": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")},
                  open(os.path.join(SAL, a[1] + ".medida.json"), "w")); print("registrado", a[1]); return
    res = [puntuar(c) for c in CASOS]
    ok = [r["puntos"] for r in res if r["puntos"] is not None]
    json.dump(res, open(os.path.join(AQUI, "resultados.json"), "w"), indent=1, ensure_ascii=False)
    L = ["# Resultados de la bateria SolidCraft", "", "Generado: " + datetime.datetime.now().strftime("%d/%m/%Y %H:%M"), "",
         "| Caso | Nivel | Pieza | V esperado | V B-rep | Err B-rep % | Err STL % | Caja err mm | CM err mm | Pts | Estado |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in res:
        L.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (r["id"], r["nivel"], r["titulo"], r["vol_esperado"], r.get("vol_brep", "-"),
                 r.get("vol_brep_err_pct", "-"), r.get("vol_stl_err_pct", "-"), r.get("bbox_err_mm", "-"), r.get("com_err_mm", "-"), r["puntos"] if r["puntos"] is not None else "-", r["estado"]))
    L += ["", "Total: %d de %d puntos (%d casos puntuados de %d)." % (sum(ok), 100*len(ok), len(ok), len(res)), "",
          "Reparto: estanco 25, caja 25, V B-rep 40, V STL 10. El centro de masas (CM) no suma puntos: si falla, el caso pasa a REVISAR."]
    open(os.path.join(AQUI, "resultados.md"), "w", encoding="utf-8").write("\n".join(L))
    print("\n".join(L))

if __name__ == "__main__":
    main()

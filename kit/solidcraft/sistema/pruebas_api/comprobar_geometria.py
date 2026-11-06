# comprobar_geometria.py v0.1 - filtro rapido de diseno con las cajas delimitadoras (bbox) de resultados\TRABAJO_medidas.json
# Uso: python comprobar_geometria.py MEDIDAS.json [--cama 250 250 250] [--exige A B MAXGAP]... [--libres PREF,PREF]
# Limite: usa cajas, no geometria real: una pieza dentro de un taladro sale como "solapa"; no mide holguras finas ni detecta choques en movimiento.
import json, sys, itertools
a = sys.argv[1:]; f = a[0]; cama = (250, 250, 250); exige = []; libres = ()
i = 1
while i < len(a):
    if a[i] == "--cama": cama = tuple(float(x) for x in a[i+1:i+4]); i += 4
    elif a[i] == "--exige": exige.append((a[i+1], a[i+2], float(a[i+3]))); i += 4
    elif a[i] == "--libres": libres = tuple(a[i+1].split(",")); i += 2
    else: i += 1
B = {b["name"]: (b["bbox"]["min"], b["bbox"]["max"], b.get("volume_mm3")) for b in json.load(open(f, encoding="utf-8"))["bodies"]}
def gap(p, q):  # >0 separacion (mm) entre cajas; <=0 solapan (valor = penetracion minima)
    return max(max(p[0][k] - q[1][k], q[0][k] - p[1][k]) for k in range(3))
def pref(n, p): return n.startswith(p)
mn = [min(b[0][k] for b in B.values()) for k in range(3)]; mx = [max(b[1][k] for b in B.values()) for k in range(3)]
dim = [round(mx[k] - mn[k], 1) for k in range(3)]
print("Conjunto: %s mm (cama %s) -> %s" % (dim, cama, "CABE" if all(dim[k] <= cama[k] for k in range(3)) else "NO CABE"))
bajo = [n for n, b in B.items() if b[0][2] < -0.001 and not n.startswith("Peana")]
if bajo: print("Piezas por debajo de z=0:", bajo)
sol = []; lejos = {n: 1e9 for n in B}
for p, q in itertools.combinations(B, 2):
    g = gap(B[p], B[q]); lejos[p] = min(lejos[p], g); lejos[q] = min(lejos[q], g)
    if g <= -0.001: sol.append((p, q, round(g, 2)))
print("Pares con cajas solapadas: %d (encaje o choque: revisar los que no sean de la misma pieza prevista)" % len(sol))
flot = [n for n, g in lejos.items() if g > 0.5 and not n.startswith(libres) if libres or True]
print("SUELTAS (a >0,5 mm de toda otra caja):", flot or "ninguna")
fallos = 0
for A, Bp, mxg in exige:
    for n in [x for x in B if pref(x, A)]:
        cand = [(gap(B[n], B[m]), m) for m in B if pref(m, Bp)]
        if not cand: print("EXIGE %s-%s: no hay piezas %s" % (A, Bp, Bp)); fallos += 1; break
        g, m = min(cand)
        if g > mxg: print("FALLA %s no llega a %s: separacion %.2f mm (max %.2f)" % (n, Bp, g, mxg)); fallos += 1
print("Exigencias: %d fallo(s)" % fallos)

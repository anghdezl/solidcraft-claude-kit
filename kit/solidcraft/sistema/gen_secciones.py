# gen_secciones.py v0.2 - convierte un "trabajo" compacto en el lote de comandos de SolidCraft (ver 54-solidcraft-organico.md)
# Uso: python gen_secciones.py trabajo.json  -> imprime {"commands":[...]} (sirve para el batch del MCP o para solidcraft-cli)
# Pasos del trabajo (todas las cotas en mm; ang = grados desde +X hacia +Z; +y del boceto = lado dorsal):
#   ["loft", nombre, y0, [[x,z,ang,a,b,cy], ...]]            loft elíptico (a = semiancho en Y, b = semialto en el plano, cy = desplazamiento)
#   ["seg", nombre, y0, [x0,z0], [x1,z1], a0,b0,a1,b1]        segmento recto de 2 secciones
#   ["esfera", nombre, [x,y,z], r]
#   ["elipse_extruida", nombre, [cx,cy], a, b, altura]        peana: elipse en XY desde z=0
#   ["union", destino, [herramientas...]]                     solid.combine join
#   ["espejo", [cuerpos...]]                                  solid.mirror plano XZ
#   ["cmd", {"command": ..., "params": {...}}]                comando en bruto
import json, math, sys

def _sec(name, P, y0, ang, a, b, cy=0.0):
    dx, dz = math.cos(math.radians(ang)), math.sin(math.radians(ang)); r = lambda v: round(v, 4)
    return [{"command": "sketch.create", "params": {"name": name, "plane": {"origin": [r(P[0]), r(y0), r(P[1])], "x_dir": [0, 1, 0], "y_dir": [r(-dz), 0, r(dx)]}}},
            {"command": "sketch.ellipse", "params": {"center": [0, cy], "major": [a, cy], "minor_radius": b}},
            {"command": "sketch.finish", "params": {}}]

def _loft(name, est, y0):
    c, n = [], []
    for i, (x, z, ang, a, b, cy) in enumerate(est):
        n.append("%s_s%d" % (name, i)); c += _sec(n[-1], (x, z), y0, ang, a, b, cy)
    c.append({"command": "solid.loft", "params": {"sections": [{"sketch": s} for s in n], "name": name, "body_name": name, "operation": "new"}})
    return c

def build(job):
    c = []
    for p in job["pasos"]:
        t = p[0]
        if t == "loft":
            c += _loft(p[1], p[3], p[2])
        elif t == "seg":
            _, nombre, y0, P0, P1, a0, b0, a1, b1 = p
            ang = math.degrees(math.atan2(P1[1] - P0[1], P1[0] - P0[0]))
            c += _loft(nombre, [[P0[0], P0[1], ang, a0, b0, 0], [P1[0], P1[1], ang, a1, b1, 0]], y0)
        elif t == "esfera":
            c.append({"command": "solid.sphere", "params": {"radius": p[3], "center": p[2], "name": p[1], "body_name": p[1], "operation": "new"}})
        elif t == "elipse_extruida":
            _, nombre, ctr, a, b, h = p
            c += [{"command": "sketch.create", "params": {"name": nombre + "_sk", "plane": "XY"}},
                  {"command": "sketch.ellipse", "params": {"center": ctr, "major": [ctr[0] + a, ctr[1]], "minor_radius": b}},
                  {"command": "sketch.finish", "params": {}},
                  {"command": "solid.extrude", "params": {"distance": h, "name": nombre, "body_name": nombre, "operation": "new"}}]
        elif t == "union":
            c.append({"command": "solid.combine", "params": {"target": p[1], "tools": p[2], "operation": "join"}})
        elif t == "espejo":
            c.append({"command": "solid.mirror", "params": {"bodies": p[1], "plane": "XZ"}})
        elif t == "cmd":
            c.append(p[1])
        else:
            raise ValueError("paso desconocido: %r" % (t,))
    return {"commands": c}

if __name__ == "__main__":
    print(json.dumps(build(json.load(open(sys.argv[1], encoding="utf-8-sig"))), separators=(",", ":")))

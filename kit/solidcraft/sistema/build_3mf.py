"""build_3mf.py v0.1 - monta un 3MF multiparte (una parte por color/filamento; formato Bambu/Orca que carga Slicer Next).
Sustituye a los build_3mf_<pieza>.py: la pieza se describe en un manifiesto JSON (carpeta manifiestos_3mf\\), no en codigo.
Solo libreria estandar.
Uso:  python build_3mf.py MANIFIESTO.json [--juego NOMBRE] [--dir CARPETA_STL] [--out SALIDA.3mf]
Manifiesto (rutas relativas a la carpeta del manifiesto):
  {"titulo": "...", "descripcion": "...",            titulo y descripcion que ve el laminador
   "carpeta_stl": "../../salida/pieza",              donde estan los STL (por defecto, la del manifiesto)
   "prefijo": "pieza_v1_",                           se antepone a cada nombre de STL
   "salida": "pieza_v1.3mf",                         ({juego} se sustituye si hay --juego)
   "extruder_objeto": 2, "cama": [125, 125]          opcionales (por defecto 2 y 125,125 = centro de cama 250x250)
   "partes": [["F1_negro.stl", "Nombre de la parte", 1], ...]    [stl, nombre, ranura ACE]
   "juegos": {"kit": [[...], ...]}                   alternativa a "partes": varios 3MF desde un manifiesto}"""
import argparse, json, os, struct, sys, uuid, zipfile
APP = "BambuStudio-01.10.02.76"

def leer_stl(p):
    b = open(p, "rb").read(); n = struct.unpack_from("<I", b, 80)[0]; vs, idx, tr = {}, [], []
    for i in range(n):
        f = struct.unpack_from("<12f", b, 84 + 50 * i); t = []
        for k in range(3):
            v = tuple(round(x, 5) for x in f[3 + 3 * k:6 + 3 * k])
            if v not in vs: vs[v] = len(vs); idx.append(v)
            t.append(vs[v])
        if len({*t}) == 3: tr.append(t)
    return idx, tr

def u(): return str(uuid.uuid4())
def fmt(v): s = f"{v:.5f}".rstrip("0").rstrip("."); return s if s not in ("-0", "") else "0"

def construir(m, qdir, parts, out):
    BED = m.get("cama", [125.0, 125.0]); titulo = m["titulo"]; ext_obj = m.get("extruder_objeto", 2)
    PARTS = [(m.get("prefijo", "") + s, n, e) for s, n, e in parts]
    meshes = [leer_stl(os.path.join(qdir, s)) for s, _, _ in PARTS]
    xs = [v[0] for mm in meshes for v in mm[0]]; ys = [v[1] for mm in meshes for v in mm[0]]
    tx = BED[0] - (min(xs) + max(xs)) / 2; ty = BED[1] - (min(ys) + max(ys)) / 2
    NS = ('xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
          'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
          'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p"')
    sub, comps, cfg = [], [], []
    for pid, ((stl, name, ext), (vv, tt)) in enumerate(zip(PARTS, meshes), start=1):
        v = "\n".join(f'     <vertex x="{fmt(a)}" y="{fmt(b)}" z="{fmt(c)}"/>' for a, b, c in vv)
        t = "\n".join(f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in tt)
        sub.append(f'  <object id="{pid}" p:UUID="{u()}" type="model">\n   <mesh>\n    <vertices>\n{v}\n    </vertices>\n'
                   f'    <triangles>\n{t}\n    </triangles>\n   </mesh>\n  </object>')
        comps.append(f'    <component p:path="/3D/Objects/object_1.model" objectid="{pid}" p:UUID="{u()}" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>')
        cfg.append(f'    <part id="{pid}" subtype="normal_part">\n      <metadata key="name" value="{name}"/>\n'
                   f'      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>\n'
                   f'      <metadata key="extruder" value="{ext}"/>\n'
                   f'      <mesh_stat edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>\n    </part>')
    OID = len(PARTS) + 1
    files = {
     "[Content_Types].xml": '<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
       '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
       '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
       '<Default Extension="png" ContentType="image/png"/></Types>\n',
     "_rels/.rels": '<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
       '<Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>\n',
     "3D/3dmodel.model": f'<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" {NS}>\n'
       f' <metadata name="Application">{APP}</metadata>\n <metadata name="BambuStudio:3mfVersion">1</metadata>\n'
       f' <metadata name="Title">{titulo}</metadata>\n'
       f' <metadata name="Description">{m.get("descripcion", "")}</metadata>\n'
       f' <resources>\n  <object id="{OID}" p:UUID="{u()}" type="model">\n   <components>\n' + "\n".join(comps) +
       f'\n   </components>\n  </object>\n </resources>\n <build p:UUID="{u()}">\n'
       f'  <item objectid="{OID}" p:UUID="{u()}" transform="1 0 0 0 1 0 0 0 1 {fmt(tx)} {fmt(ty)} 0" printable="1"/>\n </build>\n</model>\n',
     "3D/_rels/3dmodel.model.rels": '<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
       '<Relationship Target="/3D/Objects/object_1.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>\n',
     "3D/Objects/object_1.model": f'<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" {NS}>\n'
       ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n <resources>\n' + "\n".join(sub) + '\n </resources>\n <build/>\n</model>\n',
     "Metadata/model_settings.config": '<?xml version="1.0" encoding="UTF-8"?>\n<config>\n'
       f'  <object id="{OID}">\n    <metadata key="name" value="{titulo}"/>\n    <metadata key="extruder" value="{ext_obj}"/>\n' + "\n".join(cfg) +
       f'\n  </object>\n  <plate>\n    <metadata key="plater_id" value="1"/>\n    <metadata key="plater_name" value="{titulo}"/>\n'
       f'    <metadata key="locked" value="false"/>\n    <model_instance>\n      <metadata key="object_id" value="{OID}"/>\n'
       '      <metadata key="instance_id" value="0"/>\n    </model_instance>\n  </plate>\n</config>\n',
    }
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for k in ["[Content_Types].xml", "_rels/.rels", "3D/3dmodel.model", "3D/_rels/3dmodel.model.rels",
                  "3D/Objects/object_1.model", "Metadata/model_settings.config"]:
            z.writestr(k, files[k])
    print("OK", out, len(PARTS), "partes", "traslacion", round(tx, 2), round(ty, 2))

def main():
    ap = argparse.ArgumentParser(description="Monta un 3MF multiparte desde un manifiesto JSON")
    ap.add_argument("manifiesto"); ap.add_argument("--juego"); ap.add_argument("--dir"); ap.add_argument("--out")
    a = ap.parse_args()
    mdir = os.path.dirname(os.path.abspath(a.manifiesto))
    m = json.load(open(a.manifiesto, encoding="utf-8-sig"))
    if a.juego:
        if a.juego not in m.get("juegos", {}): sys.exit("Juego '%s' no esta en el manifiesto. Hay: %s" % (a.juego, ", ".join(m.get("juegos", {})) or "ninguno"))
        parts = m["juegos"][a.juego]
    elif "partes" in m: parts = m["partes"]
    else: sys.exit("El manifiesto tiene 'juegos': indica --juego (%s)" % ", ".join(m.get("juegos", {})))
    qdir = os.path.normpath(a.dir or os.path.join(mdir, m.get("carpeta_stl", ".")))
    sal = m.get("salida", "pieza.3mf").replace("{juego}", a.juego or "")
    out = a.out or os.path.join(qdir, sal)
    construir(m, qdir, parts, out)

if __name__ == "__main__": main()

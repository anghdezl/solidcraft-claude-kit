import json,glob,os,sys
pref=sys.argv[1] if len(sys.argv)>1 else "r2_api_"
for f in sorted(glob.glob("resultados/%s*.json"%pref)):
    if f.endswith(("_comandos.json","_medidas.json")): continue
    r=json.load(open(f,encoding="utf-8")); n=os.path.basename(f)[len(pref):-5]
    e=(r.get("salida_cli") or r.get("error") or "").strip().replace("\n"," ")[:230]
    v=""
    m=r.get("medidas")
    if m and os.path.exists("resultados/"+m):
        try:
            d=json.load(open("resultados/"+m,encoding="utf-8")); v="vol=%s bodies=%s"%(d["total"]["volume_mm3"],d["body_count"])
        except Exception as x: v="?"
    print("%s|%s|%s|%s"%(n,r["estado"],v,e))

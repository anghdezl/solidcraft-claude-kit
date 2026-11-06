# ejecutor_trabajos.py v0.1 (borrador, sin probar con el solidcraft-cli real)
# Vigila trabajos\*.json, los convierte en comandos (gen_secciones.build), los ejecuta con solidcraft-cli
# y deja resultados\NOMBRE.json (estado, tiempos, errores, medidas). Solo biblioteca estandar.
# Trabajo: {"salida": "pieza_v0.1.stl" (opcional, se crea en salida\), "pasos": [...]} - ver gen_secciones.py y 54.
# Parar: crear el fichero flag.stop_ejecutor. Estado: ejecutor_status.json. Entorno: SOLIDCRAFT_CLI cambia el .exe.
import json, os, subprocess, shutil, sys, time, traceback
from pathlib import Path
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
import gen_secciones
JOBS, RES, OUT, DONE = BASE / "trabajos", BASE / "resultados", BASE / "salida", BASE / "trabajos" / "hechos"
TIMEOUT = 1800
def now(): return time.strftime("%d/%m/%Y %H:%M:%S")
def find_cli():
    for c in (os.environ.get("SOLIDCRAFT_CLI"), r"C:\Program Files\SolidCraft\solidcraft-cli.EXE", shutil.which("solidcraft-cli")):
        if c and Path(c).exists(): return str(c)
    return None
def status(state, extra=""):
    (BASE / "ejecutor_status.json").write_text(json.dumps({"state": state, "heartbeat": now(), "detail": extra}, ensure_ascii=False), encoding="utf-8")
def run(cmd):
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=TIMEOUT)
    return p.returncode, (p.stdout + p.stderr)[-3000:], round(time.time() - t0, 1)
def process(jf, cli):
    name = jf.stem; res = {"trabajo": jf.name, "inicio": now(), "estado": "error"}
    try:
        job = json.loads(jf.read_text(encoding="utf-8-sig"))
        script = RES / (name + "_comandos.json")
        script.write_text(json.dumps(gen_secciones.build(job)), encoding="utf-8")
        res["comandos"] = len(json.loads(script.read_text(encoding="utf-8"))["commands"])
        med = RES / (name + "_medidas.json")
        rc, out, s = run([cli, "eval", str(script), "--json-out", str(med)])
        res.update(eval_rc=rc, eval_s=s, medidas=med.name if med.exists() else None)
        if rc != 0: res["salida_cli"] = out
        elif job.get("salida"):
            dest = OUT / Path(job["salida"]).name
            rc2, out2, s2 = run([cli, "run", str(script), "--out", str(dest)])
            res.update(export_rc=rc2, export_s=s2, fichero=dest.name if dest.exists() else None)
            if rc2 != 0: res["salida_cli"] = out2
        res["estado"] = "ok" if rc == 0 and res.get("export_rc", 0) == 0 else "error"
    except Exception as e:
        res["error"] = "%s: %s" % (type(e).__name__, e); res["traza"] = traceback.format_exc()[-1500:]
    res["fin"] = now()
    (RES / (name + ".json")).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    shutil.move(str(jf), str(DONE / jf.name))
def main():
    for d in (JOBS, RES, OUT, DONE): d.mkdir(parents=True, exist_ok=True)
    cli = find_cli()
    if not cli: print("No encuentro solidcraft-cli"); status("error", "sin cli"); return 1
    flag = BASE / "flag.stop_ejecutor"
    print("Ejecutor en espera. Trabajos en", JOBS)
    while not flag.exists():
        status("esperando")
        for jf in sorted(JOBS.glob("*.json")):
            status("trabajando", jf.name); time.sleep(1)  # deja terminar de escribir
            process(jf, cli)
        time.sleep(2)
    flag.unlink(); status("parado"); return 0
if __name__ == "__main__": sys.exit(main())

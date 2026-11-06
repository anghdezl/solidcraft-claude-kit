# comprobar_todo.py v0.1 - comprobaciones de lanzar_todo.bat (sin PowerShell). Solo biblioteca estandar.
#   comprobar_todo.py vivo ventana|ejecutor|ordenes   -> codigo de salida 0 si esta vivo, 1 si no
#   comprobar_todo.py final [segundos]                -> espera (30 s por defecto), escribe logs\lanzar_todo.log y sale 0 (OK) o 1 (FALLO)
#   comprobar_todo.py log "texto"                     -> anade una linea con fecha y hora
import json, socket, sys, time
from pathlib import Path
BASE = Path(__file__).resolve().parent
LOG = BASE / "logs" / "lanzar_todo.log"
PORT = 27878
FICH = {"ejecutor": BASE / "ejecutor_status.json", "ordenes": BASE / "ordenes_status.json"}
def now(): return time.strftime("%d/%m/%Y %H:%M:%S")
def log(t):
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f: f.write("%s %s\n" % (now(), t))
def ventana():
    try:
        with socket.create_connection(("127.0.0.1", PORT), timeout=1): return True
    except OSError: return False
def latido(nombre):
    try:
        d = json.loads(FICH[nombre].read_text(encoding="utf-8-sig"))
        t = time.mktime(time.strptime(d["heartbeat"], "%d/%m/%Y %H:%M:%S"))
        return d.get("state") != "parado" and time.time() - t < 8
    except Exception: return False
def vivo(x): return ventana() if x == "ventana" else latido(x)
def final(seg):
    t0 = time.time(); n = 0
    while True:
        n += 1; v, e, o = ventana(), latido("ejecutor"), latido("ordenes")
        log("comprobacion %d: ventana puerto %d=%d ejecutor=%d ordenes=%d" % (n, PORT, v, e, o))
        if (v and e and o) or time.time() - t0 >= seg: break
        time.sleep(3)
    ok = v and e and o
    log("RESULTADO: %s ; ventana puerto %d=%d ; ejecutor latiendo=%d ; demonio ordenes latiendo=%d ; espera=%.0f s" % ("OK" if ok else "FALLO", PORT, v, e, o, time.time() - t0))
    for nom, p in FICH.items():
        try: log("%s_status.json: %s" % (nom, p.read_text(encoding="utf-8-sig").strip()))
        except OSError as ex: log("%s_status.json: no se puede leer (%s)" % (nom, ex))
    if not ok:
        try:
            for l in (BASE / "logs" / "ordenes.log").read_text(encoding="utf-8", errors="replace").splitlines()[-8:]: log("ordenes.log> " + l)
        except OSError: pass
    log("=== fin")
    return 0 if ok else 1
if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["vivo"] and len(a) == 2: sys.exit(0 if vivo(a[1]) else 1)
    if a[:1] == ["final"]: sys.exit(final(float(a[1]) if len(a) > 1 else 30))
    if a[:1] == ["log"] and len(a) == 2: log(a[1]); sys.exit(0)
    print(__doc__); sys.exit(2)

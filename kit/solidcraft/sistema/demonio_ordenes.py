# demonio_ordenes.py v0.1 (borrador) - ejecuta ACCIONES DE UNA LISTA CERRADA escritas en ordenes.txt
# Cada línea de ordenes.txt: ACCION [argumento]. Se ejecuta, se BORRA la línea y todo queda en logs\ordenes.log
# y resultados\ordenes_ultimo.json. Líneas vacías o que empiezan por # se ignoran. Una línea no reconocida se rechaza y se borra.
# Acciones: ver ACCIONES abajo. NO ejecuta comandos libres. Los .py solo se ejecutan si su hash SHA-256 está en
# %APPDATA%\SolidCraftOrdenes\autorizados.txt (fuera de la carpeta compartida con Claude); lo escribe el usuario con:
#   lanzar_ordenes.bat autorizar [fichero.py ...]    (sin nombres: demonio_ordenes.py, ejecutor_trabajos.py, gen_secciones.py)
# Uso: python demonio_ordenes.py | --autorizar [ficheros] | --relevo (interno) | flag.stop_ordenes para parar.
import hashlib, json, logging, os, re, socket, subprocess, sys, time
from logging.handlers import RotatingFileHandler
from pathlib import Path
VERSION = "0.1"
BASE = Path(__file__).resolve().parent
ORDENES, STOP = BASE / "ordenes.txt", BASE / "flag.stop_ordenes"
LOGS, RES = BASE / "logs", BASE / "resultados"
PIDF, STATUS = BASE / "ordenes.pid", BASE / "ordenes_status.json"
AUTH = Path(os.environ.get("APPDATA") or Path.home()) / "SolidCraftOrdenes" / "autorizados.txt"
GUI = r"C:\Program Files\SolidCraft\solidcraft.EXE"
PORT = 27878
BASICOS = ["demonio_ordenes.py", "ejecutor_trabajos.py", "gen_secciones.py"]
NOFLAGS = getattr(subprocess, "CREATE_NO_WINDOW", 0)
DETACH = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
ARG_RE = re.compile(r"^[A-Za-z0-9_.-]{1,80}$")
def now(): return time.strftime("%d/%m/%Y %H:%M:%S")
LOGS.mkdir(exist_ok=True); RES.mkdir(exist_ok=True)
log = logging.getLogger("ordenes"); log.setLevel(logging.INFO)
_h = RotatingFileHandler(LOGS / "ordenes.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8")
_h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%d/%m/%Y %H:%M:%S")); log.addHandler(_h)
log.addHandler(logging.StreamHandler())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def autorizado(nombre):
    p = BASE / nombre
    if not p.is_file(): return False, "no existe"
    h = sha(p)
    try: ok = any(l.split()[0] == h for l in AUTH.read_text(encoding="utf-8").splitlines() if l.strip())
    except OSError: ok = False
    return ok, h[:12]
def run(cmd, timeout=60):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, cwd=str(BASE))
        return r.returncode, (r.stdout + r.stderr).strip()[-1500:]
    except Exception as e:
        return -1, "%s: %s" % (type(e).__name__, e)
def vivo_exe(nombre):
    rc, out = run(["tasklist", "/FI", "IMAGENAME eq " + nombre, "/NH"], 20)
    return nombre.lower() in out.lower()
def vivo_pid(pid):
    rc, out = run(["tasklist", "/FI", "PID eq %d" % pid, "/NH"], 20)
    return str(pid) in out
def puerto():
    s = socket.socket(); s.settimeout(1)
    try: return s.connect_ex(("127.0.0.1", PORT)) == 0
    finally: s.close()
def esperar(cond, seg):
    t = time.time()
    while time.time() - t < seg:
        if cond(): return True
        time.sleep(1)
    return cond()
def ejecutor_estado():
    try:
        d = json.loads((BASE / "ejecutor_status.json").read_text(encoding="utf-8"))
        t = time.mktime(time.strptime(d["heartbeat"], "%d/%m/%Y %H:%M:%S"))
        return d["state"], time.time() - t
    except Exception: return None, 1e9
# ---------------------------------------------------------------- acciones
def a_estado(arg):
    ej = ejecutor_estado()
    aut = {n: autorizado(n)[0] for n in BASICOS}
    return "ok", "solidcraft.exe=%s puerto%d=%s ejecutor=%s(%.0fs) autorizados=%s" % (vivo_exe("solidcraft.exe"), PORT, puerto(), ej[0], ej[1], aut)
def a_solidcraft_abrir(arg):
    if puerto(): return "ok", "ya escuchando en %d" % PORT
    if not Path(GUI).exists(): return "error", "no existe " + GUI
    subprocess.Popen([GUI, "--control", str(PORT)], creationflags=DETACH, close_fds=True)
    return ("ok", "abierto") if esperar(puerto, 20) else ("error", "no escucha en %d tras 20s" % PORT)
def a_solidcraft_cerrar(arg):
    if not vivo_exe("solidcraft.exe"): return "ok", "no estaba abierto"
    run(["taskkill", "/IM", "solidcraft.exe"], 20)
    if esperar(lambda: not vivo_exe("solidcraft.exe"), 10): return "ok", "cerrado"
    return "error", "sigue abierto (diálogo de guardar o colgado): usar solidcraft_matar (pierde lo no guardado)"
def a_solidcraft_matar(arg):
    rc, out = run(["taskkill", "/F", "/IM", "solidcraft.exe"], 20)
    return ("ok" if esperar(lambda: not vivo_exe("solidcraft.exe"), 8) else "error"), "taskkill rc=%s %s" % (rc, out[:200])
def _lanzar_py(nombre):
    ok, h = autorizado(nombre)
    if not ok: return False, "%s NO autorizado (hash %s): el usuario debe ejecutar lanzar_ordenes.bat autorizar %s" % (nombre, h, nombre)
    return True, h
def a_ejecutor_arrancar(arg):
    st, edad = ejecutor_estado()
    if st in ("esperando", "trabajando") and edad < 15: return "ok", "ya en marcha"
    for n in ("ejecutor_trabajos.py", "gen_secciones.py"):
        ok, m = _lanzar_py(n)
        if not ok: return "rechazada", m
    subprocess.Popen([sys.executable, str(BASE / "ejecutor_trabajos.py")], cwd=str(BASE), creationflags=NOFLAGS | DETACH, close_fds=True)
    return ("ok", "arrancado") if esperar(lambda: ejecutor_estado()[0] in ("esperando", "trabajando") and ejecutor_estado()[1] < 15, 10) else ("error", "no da señal tras 10s")
def a_ejecutor_parar(arg):
    (BASE / "flag.stop_ejecutor").write_text("", encoding="utf-8")
    return ("ok", "parado") if esperar(lambda: ejecutor_estado()[0] == "parado", 12) else ("error", "no confirma la parada en 12s")
def a_ejecutor_reiniciar(arg):
    r1 = a_ejecutor_parar(arg); r2 = a_ejecutor_arrancar(arg)
    return r2[0], "parar: %s | arrancar: %s" % (r1[1], r2[1])
def a_ordenes_reiniciar(arg):
    ok, m = _lanzar_py("demonio_ordenes.py")
    if not ok: return "rechazada", m
    subprocess.Popen([sys.executable, str(Path(__file__)), "--relevo"], cwd=str(BASE), creationflags=NOFLAGS | DETACH, close_fds=True)
    globals()["SALIR"] = True
    return "ok", "relevo lanzado; este proceso termina"
def a_ordenes_parar(arg):
    globals()["SALIR"] = True; return "ok", "parando"
def a_python_script(arg):
    if not arg or not arg.endswith(".py"): return "rechazada", "uso: python_script nombre.py"
    ok, m = _lanzar_py(arg)
    if not ok: return "rechazada", m
    rc, out = run([sys.executable, str(BASE / arg)], 600)
    return ("ok" if rc == 0 else "error"), "rc=%s %s" % (rc, out)
def a_comprobar_sintaxis(arg):
    if not arg or not arg.endswith(".py") or not (BASE / arg).is_file(): return "rechazada", "uso: comprobar_sintaxis nombre.py (existente)"
    try: compile((BASE / arg).read_text(encoding="utf-8-sig"), arg, "exec"); return "ok", "sintaxis correcta"
    except SyntaxError as e: return "error", "línea %s: %s" % (e.lineno, e.msg)
def a_probar(arg):
    res = []
    for p in sorted(BASE.glob("*.py")):
        r = a_comprobar_sintaxis(p.name); res.append("%s:%s" % (p.name, r[0]))
    return "ok", "; ".join(res) + " | " + a_estado(None)[1]
ACCIONES = {k[2:]: v for k, v in globals().items() if k.startswith("a_") and callable(v)}
# ---------------------------------------------------------------- bucle
SALIR = False
def quitar_linea(linea):
    try:
        ls = ORDENES.read_text(encoding="utf-8-sig").splitlines(); ls.remove(linea)
        ORDENES.write_text("\n".join(ls) + ("\n" if ls else ""), encoding="utf-8")
    except (OSError, ValueError): log.warning("no pude borrar la línea: %s", linea)
def atender(linea):
    t = linea.split(); acc = t[0].lower(); arg = t[1] if len(t) > 1 else None
    if acc not in ACCIONES or len(t) > 2 or (arg and not ARG_RE.match(arg)): est, det = "rechazada", "acción o argumento no permitidos"
    else:
        try: est, det = ACCIONES[acc](arg)
        except Exception as e: est, det = "error", "%s: %s" % (type(e).__name__, e)
    log.info("ORDEN %r -> %s | %s", linea, est, det)
    (RES / "ordenes_ultimo.json").write_text(json.dumps({"hora": now(), "orden": linea, "estado": est, "detalle": det}, ensure_ascii=False, indent=1), encoding="utf-8")
    quitar_linea(linea)
def autorizar(nombres):
    AUTH.parent.mkdir(parents=True, exist_ok=True)
    for n in nombres or BASICOS:
        p = BASE / n
        if not p.is_file(): print("no existe", n); continue
        print("%s  sha256=%s  %d bytes  %s" % (n, sha(p)[:16], p.stat().st_size, time.strftime("%d/%m/%Y %H:%M", time.localtime(p.stat().st_mtime))))
        r = input("  ¿Autorizar este contenido? Escribe SI (las dos letras, en mayusculas; cualquier otra cosa = no): ").strip()
        if r == "SI":
            with open(AUTH, "a", encoding="utf-8") as f: f.write("%s  %s  %s\n" % (sha(p), n, now()))
            print("  autorizado")
        else:
            print("  NO autorizado (escribiste %r; hace falta SI)" % r)
def main(relevo=False):
    global SALIR
    if relevo: time.sleep(4)
    try:
        old = int(PIDF.read_text()) if PIDF.exists() else 0
        if old and old != os.getpid() and vivo_pid(old): print("Ya hay un demonio (pid %d)" % old); return 1
    except ValueError: pass
    PIDF.write_text(str(os.getpid())); ORDENES.touch(exist_ok=True)
    log.info("=== demonio_ordenes v%s arrancado (pid %d). Acciones: %s", VERSION, os.getpid(), ", ".join(sorted(ACCIONES)))
    while not SALIR and not STOP.exists():
        STATUS.write_text(json.dumps({"state": "esperando", "heartbeat": now(), "version": VERSION, "pid": os.getpid()}), encoding="utf-8")
        try:
            for l in [x.strip() for x in ORDENES.read_text(encoding="utf-8-sig").splitlines()][:20]:
                if SALIR: break
                if l and not l.startswith("#"): atender(l)
                elif l: quitar_linea(l)
        except OSError as e: log.warning("lectura: %s", e)
        time.sleep(2)
    if STOP.exists(): STOP.unlink()
    STATUS.write_text(json.dumps({"state": "parado", "heartbeat": now(), "version": VERSION}), encoding="utf-8")
    log.info("=== demonio parado"); return 0
if __name__ == "__main__":
    if "--autorizar" in sys.argv: autorizar(sys.argv[sys.argv.index("--autorizar") + 1:])
    else: sys.exit(main("--relevo" in sys.argv))

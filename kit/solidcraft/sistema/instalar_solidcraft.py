#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
instalar_solidcraft.py  v0.1  (borrador: sin probar en otros PC)

Demonio que instala SolidCraft (winget), comprueba que todo funciona y se queda
vigilando flags. Solo biblioteca estandar de Python (3.8 o superior).

FLAGS (ficheros vacios que se dejan en esta misma carpeta):
  flag.stop     el demonio lo detecta, lo BORRA y se para de forma controlada
  flag.check    repite las comprobaciones (se borra al atenderlo)
  flag.install  repite instalacion (si falta) + comprobaciones (se borra al atenderlo)

SALIDAS (en esta carpeta):
  logs\solidcraft.log                   log rotativo UTF-8 (lo revisa Claude)
  status.json                           estado, resultado de cada paso y latido
  salida\                               ficheros de prueba (STEP/STL/JSON)
  claude_desktop_config.snippet.json    bloque para Claude Desktop (NO se aplica solo)

OPCIONES:
  --once        sin demonio: instala, comprueba y sale
  --no-install  no instala; solo detecta y comprueba
  --stop | --check | --install   dejan el flag correspondiente y salen
  --estado      muestra status.json y el final del log
"""
import argparse
import ctypes
import json
import logging
import os
import queue
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

VERSION = "0.1"
BASE = Path(__file__).resolve().parent
ALLOW_PATH = BASE.parent.parent     # carpeta de trabajo (contiene solidcraft\)
LOG_DIR = BASE / "logs"
OUT_DIR = BASE / "salida"
LOG_FILE = LOG_DIR / "solidcraft.log"
STATUS_FILE = BASE / "status.json"
LOCK_FILE = BASE / "solidcraft.lock"
SNIPPET_FILE = BASE / "claude_desktop_config.snippet.json"
FLAG_STOP = BASE / "flag.stop"
FLAG_CHECK = BASE / "flag.check"
FLAG_INSTALL = BASE / "flag.install"
WINGET_ID = "bherbruck.SolidCraft"
BOX_VOLUME = 40 * 30 * 20           # mm3 de la caja de prueba (analitico)
HEARTBEAT_S = 5

log = logging.getLogger("solidcraft")
STOP_EVT = threading.Event()
_last_hb = [0.0]
STATE = {
    "script_version": VERSION,
    "state": "starting",
    "pid": os.getpid(),
    "started": None,
    "heartbeat": None,
    "stopped": None,
    "exe": {},
    "steps": {},
    "summary": None,
}


class StopRequested(Exception):
    pass


# ----------------------------------------------------------------- utilidades
def now():
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def save_status():
    try:
        tmp = STATUS_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(STATE, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(str(tmp), str(STATUS_FILE))
    except OSError as e:
        log.debug("no se pudo escribir status.json: %s", e)


def heartbeat(force=False):
    t = time.time()
    if force or t - _last_hb[0] >= HEARTBEAT_S:
        _last_hb[0] = t
        STATE["heartbeat"] = now()
        save_status()


def stop_requested():
    return STOP_EVT.is_set() or FLAG_STOP.exists()


def check_stop():
    if stop_requested():
        raise StopRequested()


def rec(name, status, detail=""):
    """status: OK, WARN, FAIL, SKIP"""
    STATE["steps"][name] = {"status": status, "detail": detail, "time": now()}
    fn = log.info if status in ("OK", "SKIP") else (log.warning if status == "WARN" else log.error)
    fn("[%s] %s%s", status, name, (" - " + detail) if detail else "")
    save_status()


def log_out(out, limit=3000):
    out = (out or "").strip()
    if not out:
        return
    if len(out) > limit:
        out = out[:limit] + "\n...[recortado %d caracteres]" % (len(out) - limit)
    for line in out.splitlines():
        log.debug("    | %s", line)


def run_cmd(cmd, timeout=120, interruptible=True):
    cmd = [str(c) for c in cmd]
    log.info("$ %s", " ".join('"%s"' % c if " " in c else c for c in cmd))
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, encoding="utf-8", errors="replace")
    except OSError as e:
        return -1, "no se pudo ejecutar: %s" % e
    chunks = []

    def reader():
        for line in p.stdout:
            chunks.append(line)

    th = threading.Thread(target=reader, daemon=True)
    th.start()
    end = time.time() + timeout
    warned = False
    while p.poll() is None:
        heartbeat()
        if stop_requested():
            if interruptible:
                log.warning("stop pedido: se corta el proceso en curso")
                p.terminate()
                try:
                    p.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    p.kill()
                raise StopRequested()
            if not warned:
                log.warning("stop pedido: se atendera al terminar este paso (no interrumpible)")
                warned = True
        if time.time() > end:
            p.kill()
            th.join(2)
            return -2, "".join(chunks) + "\n[timeout tras %ss]" % timeout
        time.sleep(0.3)
    th.join(5)
    out = "".join(chunks)
    log_out(out)
    return p.returncode, out


def refresh_path():
    """Relee el PATH del registro: un programa recien instalado no esta en el PATH de este proceso."""
    try:
        import winreg
    except ImportError:
        return
    parts = []
    for hive, sub in ((winreg.HKEY_LOCAL_MACHINE,
                       r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
                      (winreg.HKEY_CURRENT_USER, "Environment")):
        try:
            with winreg.OpenKey(hive, sub) as k:
                val, _ = winreg.QueryValueEx(k, "Path")
                parts.append(os.path.expandvars(val))
        except OSError:
            pass
    if parts:
        os.environ["PATH"] = os.pathsep.join(parts + [os.environ.get("PATH", "")])


def find_exe(name):
    p = shutil.which(name)
    if p:
        return p
    cands = []
    la = os.environ.get("LOCALAPPDATA")
    if la:
        cands += [(Path(la) / "Programs", 4), (Path(la) / "Microsoft" / "WinGet", 5)]
    for k in ("ProgramFiles", "ProgramFiles(x86)"):
        if os.environ.get(k):
            cands.append((Path(os.environ[k]), 3))
    fname = name.lower() + ".exe"
    for root, depth in cands:
        if not root.is_dir():
            continue
        base_depth = len(root.parts)
        for dp, dn, fn in os.walk(str(root)):
            if len(Path(dp).parts) - base_depth >= depth:
                dn[:] = []
            for f in fn:
                if f.lower() == fname:
                    return str(Path(dp) / f)
    return None


def fresh(path, t0):
    try:
        st = Path(path).stat()
        return st.st_size > 0 and st.st_mtime >= t0 - 2
    except OSError:
        return False


def volumes_in(obj):
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if "volume" in str(k).lower() and isinstance(v, (int, float)):
                out.append(float(v))
            else:
                out += volumes_in(v)
    elif isinstance(obj, list):
        for v in obj:
            out += volumes_in(v)
    return out


def vol_ok(vals):
    return any(abs(v - BOX_VOLUME) / BOX_VOLUME < 0.01 for v in vals)


def box_commands():
    return [
        {"command": "sketch.create", "params": {"plane": "XY"}},
        {"command": "sketch.rectangle.two_point", "params": {"p0": [0, 0], "p1": [40, 30]}},
        {"command": "sketch.finish", "params": {}},
        {"command": "solid.extrude", "params": {"distance": 20}},
    ]


# ------------------------------------------------------------ cliente MCP
class Mcp:
    def __init__(self, cmd):
        cmd = [str(c) for c in cmd]
        log.info("$ (MCP) %s", " ".join('"%s"' % c if " " in c else c for c in cmd))
        self.p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True, encoding="utf-8",
                                  errors="replace", bufsize=1)
        self.q = queue.Queue()
        self.err = []
        self._id = 0
        threading.Thread(target=self._rd_out, daemon=True).start()
        threading.Thread(target=self._rd_err, daemon=True).start()

    def _rd_out(self):
        for line in self.p.stdout:
            self.q.put(line)
        self.q.put(None)

    def _rd_err(self):
        for line in self.p.stderr:
            self.err.append(line.rstrip())

    def _send(self, obj):
        self.p.stdin.write(json.dumps(obj) + "\n")
        self.p.stdin.flush()

    def notify(self, method, params=None):
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        self._send(msg)

    def request(self, method, params=None, timeout=60):
        self._id += 1
        rid = self._id
        self._send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params or {}})
        end = time.time() + timeout
        while time.time() < end:
            heartbeat()
            check_stop()
            try:
                line = self.q.get(timeout=0.5)
            except queue.Empty:
                continue
            if line is None:
                raise RuntimeError("el servidor MCP cerro su salida (stderr: %s)" % " | ".join(self.err[-5:]))
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except ValueError:
                log.debug("    | (no JSON) %s", line[:200])
                continue
            if msg.get("id") == rid:
                return msg
        raise TimeoutError("sin respuesta a %s en %ss" % (method, timeout))

    def tool(self, name, arguments, timeout=90):
        msg = self.request("tools/call", {"name": name, "arguments": arguments}, timeout)
        if "error" in msg:
            raise RuntimeError("error JSON-RPC en %s: %s" % (name, msg["error"]))
        res = msg.get("result", {})
        text = " ".join(c.get("text", "") for c in res.get("content", []) if c.get("type") == "text")
        return bool(res.get("isError")), text

    def close(self):
        try:
            self.p.stdin.close()
        except Exception:
            pass
        try:
            self.p.wait(timeout=5)
        except Exception:
            try:
                self.p.kill()
            except Exception:
                pass


# ---------------------------------------------------------------- pasos
def step_entorno():
    rec("entorno.sistema", "OK" if os.name == "nt" else "WARN",
        "%s, Python %s, carpeta %s" % (sys.platform, sys.version.split()[0], BASE))
    try:
        OUT_DIR.mkdir(exist_ok=True)
        t = OUT_DIR / ".escritura_ok"
        t.write_text(now(), encoding="utf-8")
        rec("entorno.escritura", "OK", "se puede escribir en %s" % OUT_DIR)
    except OSError as e:
        rec("entorno.escritura", "FAIL", str(e))
    try:
        admin = bool(ctypes.windll.shell32.IsUserAnAdmin())
        rec("entorno.admin", "OK", "ejecutando como administrador" if admin else "sin permisos de administrador (el instalador pedira UAC)")
    except Exception:
        rec("entorno.admin", "SKIP", "no determinable")
    w = shutil.which("winget")
    if not w:
        rec("entorno.winget", "FAIL", "winget no esta en el PATH")
        return
    rc, out = run_cmd([w, "--version"], timeout=30)
    rec("entorno.winget", "OK" if rc == 0 else "WARN", "%s (rc=%s)" % (out.strip()[:60], rc))


def step_detect():
    refresh_path()
    cli = find_exe("solidcraft-cli")
    gui = find_exe("solidcraft")
    STATE["exe"] = {"cli": cli, "gui": gui}
    rec("detectar.cli", "OK" if cli else "WARN", cli or "solidcraft-cli.exe no encontrado")
    rec("detectar.gui", "OK" if gui else "WARN", gui or "solidcraft.exe no encontrado")
    return cli


def step_install():
    cli = step_detect()
    if cli:
        rec("instalar", "SKIP", "ya instalado")
        return
    w = shutil.which("winget")
    if not w:
        rec("instalar", "FAIL", "sin winget: instala a mano desde la pagina de releases")
        return
    log.info("instalando %s con winget (puede salir un aviso de UAC o de SmartScreen)", WINGET_ID)
    rc, out = run_cmd([w, "install", "--id", WINGET_ID, "-e", "--accept-package-agreements",
                       "--accept-source-agreements", "--silent"], timeout=1200, interruptible=False)
    cli = step_detect()
    if cli:
        rec("instalar", "OK", "winget rc=%s; solidcraft-cli encontrado" % rc)
    else:
        rec("instalar", "FAIL", "winget rc=%s y solidcraft-cli no aparece (puede que el instalador no lo incluya; ver el log)" % rc)


def check_version(cli):
    rc, out = run_cmd([cli, "--version"], timeout=30)
    rec("cli.version", "OK" if rc == 0 and out.strip() else "FAIL", "%s (rc=%s)" % (out.strip()[:80], rc))


def check_commands(cli):
    rc, out = run_cmd([cli, "commands"], timeout=60)
    if rc != 0:
        rec("cli.commands", "FAIL", "rc=%s" % rc)
        return
    try:
        data = json.loads(out)
        n = len(data) if isinstance(data, (list, dict)) else 0
        rec("cli.commands", "OK" if n else "WARN", "%d comandos en el catalogo" % n)
    except ValueError:
        rec("cli.commands", "WARN", "la salida no es JSON valido")


def check_eval_run(cli):
    OUT_DIR.mkdir(exist_ok=True)
    script = OUT_DIR / "test_caja.json"
    script.write_text(json.dumps({"commands": box_commands()}, indent=2), encoding="utf-8")
    meas = OUT_DIR / "test_caja_medidas.json"
    t0 = time.time()
    rc, out = run_cmd([cli, "eval", script, "--json-out", meas], timeout=120)
    if rc != 0 or not fresh(meas, t0):
        rec("cli.eval_volumen", "FAIL", "rc=%s, fichero de medidas %s" % (rc, "ok" if fresh(meas, t0) else "no generado"))
    else:
        try:
            vals = volumes_in(json.loads(meas.read_text(encoding="utf-8-sig")))
            rec("cli.eval_volumen", "OK" if vol_ok(vals) else "FAIL",
                "volumenes %s; esperado %d mm3 (caja 40x30x20)" % (vals[:4], BOX_VOLUME))
        except (ValueError, OSError) as e:
            rec("cli.eval_volumen", "FAIL", "no se pudo leer %s: %s" % (meas.name, e))
    for ext in ("step", "stl"):
        dest = OUT_DIR / ("test_caja." + ext)
        t0 = time.time()
        rc, out = run_cmd([cli, "run", script, "--out", dest], timeout=120)
        ok = rc == 0 and fresh(dest, t0)
        rec("cli.exportar_" + ext, "OK" if ok else "FAIL",
            "%s (%s bytes)" % (dest.name, dest.stat().st_size if dest.exists() else 0) if ok else "rc=%s, fichero no generado" % rc)


def check_mcp(cli):
    m = None
    try:
        m = Mcp([cli, "mcp", "--allow-path", ALLOW_PATH])
        msg = m.request("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                       "clientInfo": {"name": "instalar_solidcraft", "version": VERSION}}, 40)
        info = msg.get("result", {}).get("serverInfo", {})
        rec("mcp.initialize", "OK" if "result" in msg else "FAIL", "servidor %s" % info)
        m.notify("notifications/initialized")
        msg = m.request("tools/list", {}, 30)
        names = [t.get("name") for t in msg.get("result", {}).get("tools", [])]
        need = ["batch", "measure", "export", "execute"]
        miss = [n for n in need if n not in names]
        rec("mcp.herramientas", "OK" if not miss else "FAIL", "%d herramientas; faltan: %s" % (len(names), miss or "ninguna"))
        err, text = m.tool("batch", {"commands": box_commands(), "verbose": False})
        rec("mcp.modelar_caja", "FAIL" if err else "OK", text[:200].replace("\n", " "))
        err, text = m.tool("measure", {})
        vals = [float(x) for x in re.findall(r"volume_mm3\"?\s*:\s*([0-9.eE+-]+)", text)]
        rec("mcp.medir_volumen", "OK" if vol_ok(vals) else "FAIL", "volumenes %s; esperado %d mm3" % (vals[:4], BOX_VOLUME))
        dest = OUT_DIR / "test_mcp.step"
        t0 = time.time()
        err, text = m.tool("export", {"path": str(dest), "format": "step"})
        ok = (not err) and fresh(dest, t0)
        rec("mcp.exportar_en_carpeta_permitida", "OK" if ok else "FAIL",
            "%s" % (dest.name if ok else text[:200].replace("\n", " ")))
    except StopRequested:
        raise
    except Exception as e:
        rec("mcp.sesion", "FAIL", "%s: %s" % (type(e).__name__, e))
    finally:
        if m:
            m.close()
            for line in m.err[:12]:
                log.info("    mcp stderr: %s", line)


def config_paths():
    c = []
    ad = os.environ.get("APPDATA")
    if ad:
        c.append(Path(ad) / "Claude" / "claude_desktop_config.json")
    la = os.environ.get("LOCALAPPDATA")
    if la:
        c += list(Path(la).glob("Packages/Claude_*/LocalCache/Roaming/Claude/claude_desktop_config.json"))
    return [p for p in c if p.exists()]


def step_config(cli):
    if cli:
        snippet = {"solidcraft": {"command": cli, "args": ["mcp", "--allow-path", str(ALLOW_PATH)]}}
        SNIPPET_FILE.write_text(json.dumps(snippet, indent=2, ensure_ascii=False), encoding="utf-8")
        rec("config.snippet", "OK", "escrito %s (no se aplica solo)" % SNIPPET_FILE.name)
    found = config_paths()
    if not found:
        rec("config.claude_desktop", "WARN", "no se encuentra claude_desktop_config.json")
        return
    for p in found:
        try:
            data = json.loads(p.read_text(encoding="utf-8-sig"))
            keys = list((data.get("mcpServers") or {}).keys())
            rec("config.claude_desktop", "OK" if "solidcraft" in keys else "WARN",
                "%s; servidores: %s%s" % (p, keys, "" if "solidcraft" in keys else " (falta 'solidcraft': anade el bloque del snippet)"))
        except (ValueError, OSError) as e:
            rec("config.claude_desktop", "WARN", "no se pudo leer %s: %s" % (p, e))


def run_all(do_install=True):
    STATE["state"] = "running"
    STATE["steps"] = {}
    STATE["summary"] = None
    heartbeat(True)
    log.info("=== inicio de pasos (instalar=%s) ===", do_install)
    step_entorno()
    check_stop()
    cli = step_install() if do_install else None
    if not do_install:
        cli = step_detect()
    else:
        cli = STATE["exe"].get("cli")
    check_stop()
    if cli:
        check_version(cli)
        check_stop()
        check_commands(cli)
        check_stop()
        check_eval_run(cli)
        check_stop()
        check_mcp(cli)
    else:
        rec("cli", "FAIL", "solidcraft-cli.exe no disponible: se omiten las pruebas")
    step_config(cli)
    n = {"OK": 0, "WARN": 0, "FAIL": 0, "SKIP": 0}
    for s in STATE["steps"].values():
        n[s["status"]] = n.get(s["status"], 0) + 1
    STATE["summary"] = "%s | OK=%d WARN=%d FAIL=%d SKIP=%d" % (now(), n["OK"], n["WARN"], n["FAIL"], n["SKIP"])
    STATE["state"] = "idle_ok" if n["FAIL"] == 0 else "idle_con_fallos"
    log.info("=== RESUMEN: %s ===", STATE["summary"])
    heartbeat(True)


# ---------------------------------------------------------------- demonio
def pid_alive(pid):
    if os.name == "nt":
        k = ctypes.windll.kernel32
        h = k.OpenProcess(0x1000, False, pid)
        if not h:
            return False
        code = ctypes.c_ulong()
        ok = k.GetExitCodeProcess(h, ctypes.byref(code))
        k.CloseHandle(h)
        return bool(ok) and code.value == 259
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def acquire_lock():
    if LOCK_FILE.exists():
        try:
            old = int(LOCK_FILE.read_text().strip())
        except (ValueError, OSError):
            old = 0
        if old and old != os.getpid() and pid_alive(old):
            log.error("ya hay un demonio en marcha (pid %s). Usa flag.stop para pararlo.", old)
            return False
        log.warning("lock huerfano (pid %s): se reemplaza", old)
    LOCK_FILE.write_text(str(os.getpid()), encoding="utf-8")
    return True


def consume(flag):
    try:
        flag.unlink()
        log.info("%s detectado y borrado", flag.name)
        return True
    except OSError as e:
        log.warning("no se pudo borrar %s: %s", flag.name, e)
        return False


def idle_loop():
    log.info("demonio en espera. Flags en %s: flag.stop | flag.check | flag.install", BASE)
    while True:
        heartbeat()
        if stop_requested():
            return
        if FLAG_CHECK.exists():
            consume(FLAG_CHECK)
            run_all(do_install=False)
        if FLAG_INSTALL.exists():
            consume(FLAG_INSTALL)
            run_all(do_install=True)
        time.sleep(1)


def shutdown(reason):
    if FLAG_STOP.exists():
        consume(FLAG_STOP)
    STATE["state"] = "stopped"
    STATE["stopped"] = now()
    STATE["summary"] = "%s | parado: %s" % (STATE["stopped"], reason)
    save_status()
    try:
        LOCK_FILE.unlink()
    except OSError:
        pass
    log.info("=== demonio parado (%s) ===", reason)


def setup_logging():
    LOG_DIR.mkdir(exist_ok=True)
    log.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%d/%m/%Y %H:%M:%S")
    fh = RotatingFileHandler(str(LOG_FILE), maxBytes=1000000, backupCount=3, encoding="utf-8")
    fh.setFormatter(fmt)
    fh.setLevel(logging.DEBUG)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    sh.setLevel(logging.INFO)
    log.addHandler(fh)
    log.addHandler(sh)


def main():
    ap = argparse.ArgumentParser(description="Instala y comprueba SolidCraft (demonio con flags)")
    ap.add_argument("--once", action="store_true", help="sin demonio: instala, comprueba y sale")
    ap.add_argument("--no-install", action="store_true", help="no instala; solo comprueba")
    ap.add_argument("--stop", action="store_true", help="deja flag.stop y sale")
    ap.add_argument("--check", action="store_true", help="deja flag.check y sale")
    ap.add_argument("--install", action="store_true", help="deja flag.install y sale")
    ap.add_argument("--estado", action="store_true", help="muestra status.json y el final del log")
    args = ap.parse_args()
    for wanted, flag in ((args.stop, FLAG_STOP), (args.check, FLAG_CHECK), (args.install, FLAG_INSTALL)):
        if wanted:
            flag.write_text("", encoding="utf-8")
            print("%s creado en %s" % (flag.name, BASE))
            return 0
    if args.estado:
        print(STATUS_FILE.read_text(encoding="utf-8") if STATUS_FILE.exists() else "No hay status.json todavia.")
        print("---- ultimas lineas del log ----")
        if LOG_FILE.exists():
            print("\n".join(LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines()[-25:]))
        else:
            print("No hay log todavia.")
        return 0
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    setup_logging()
    log.info("=== instalar_solidcraft v%s (pid %s) ===", VERSION, os.getpid())
    if not acquire_lock():
        return 2
    if FLAG_STOP.exists():
        log.warning("flag.stop antiguo al arrancar: se borra y se continua")
        consume(FLAG_STOP)
    STATE["started"] = now()

    def on_signal(signum, frame):
        log.warning("senal %s recibida: parada controlada", signum)
        STOP_EVT.set()

    for sig in ("SIGINT", "SIGTERM", "SIGBREAK"):
        if hasattr(signal, sig):
            try:
                signal.signal(getattr(signal, sig), on_signal)
            except (ValueError, OSError):
                pass

    reason = "fin"
    rc = 0
    try:
        run_all(do_install=not args.no_install)
        if not args.once:
            idle_loop()
            reason = "flag.stop o senal"
        else:
            reason = "--once terminado"
    except StopRequested:
        reason = "flag.stop o senal durante un paso"
    except Exception:
        log.exception("error inesperado")
        STATE["state"] = "error"
        reason = "error inesperado"
        rc = 1
    finally:
        shutdown(reason)
    return rc


if __name__ == "__main__":
    sys.exit(main())

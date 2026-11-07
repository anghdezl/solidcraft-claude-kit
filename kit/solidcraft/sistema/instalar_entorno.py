#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
instalar_entorno.py  v0.1  (sin probar en Windows limpio; la logica de configuracion SI esta probada con ficheros de ejemplo)

Prepara el PC para trabajar con Claude + SolidCraft. Solo libreria estandar (Python 3.8+).

USO
  python instalar_entorno.py diagnostico                 solo lee; no cambia nada
  python instalar_entorno.py instalar                    instala SolidCraft con winget (pide confirmacion)
  python instalar_entorno.py configurar [--aplicar]      anade 'solidcraft' a claude_desktop_config.json
                                                         (sin --aplicar: solo muestra que haria)
  python instalar_entorno.py todo                        asistente: carpeta de trabajo, instalar, configurar, autorizar

OPCIONES
  --trabajo CARPETA   carpeta de trabajo (la que contiene solidcraft\ y se conecta a Claude); por defecto, la que contiene este solidcraft\
  --config RUTA       claude_desktop_config.json concreto (si no, se detecta)
  --sobrescribir      reemplaza un bloque 'solidcraft' distinto que ya exista
  --forzar            sigue aunque Claude Desktop parezca abierto (NO recomendado: la app puede pisar el cambio)

SALIDA: sistema\logs\instalar_entorno.log (se sobrescribe en cada ejecucion), con una linea final RESULTADO.
Codigos: 0 correcto | 1 error | 2 hace falta una decision del usuario (p. ej. --sobrescribir).
"""
import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

VERSION = "0.1"
AQUI = Path(__file__).resolve().parent                  # ...\solidcraft\sistema
LOG_DIR = AQUI / "logs"
LOG_FILE = LOG_DIR / "instalar_entorno.log"
WINGET_ID = "bherbruck.SolidCraft"                      # confirmado en el README del proyecto
MSI_URL = "https://github.com/tangency-labs/solidcraft/releases/latest/download/solidcraft-windows-x64.msi"
SERVER = "solidcraft"
CONTADOR = {"OK": 0, "WARN": 0, "FAIL": 0}
ES_WIN = platform.system() == "Windows"


# ---------------------------------------------------------------- utilidades
def log(msg=""):
    print(msg)
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except OSError:
        pass


def rec(estado, nombre, detalle=""):
    CONTADOR[estado] += 1
    log("[%s] %s%s" % (estado, nombre, (" - " + detalle) if detalle else ""))


def preguntar(texto, defecto="s"):
    """Pregunta si/no. Sin consola interactiva devuelve False (no hace nada por su cuenta)."""
    try:
        r = input("%s [%s] " % (texto, "S/n" if defecto == "s" else "s/N")).strip().lower()
    except EOFError:
        return False
    return (r[:1] or defecto) in ("s", "y")


def ejecutar(cmd, timeout=60):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except (OSError, subprocess.SubprocessError) as e:
        return -1, str(e)


def buscar_exe(nombre):
    p = shutil.which(nombre)
    if p:
        return p
    raices = []
    la = os.environ.get("LOCALAPPDATA")
    if la:
        raices += [(Path(la) / "Programs", 4), (Path(la) / "Microsoft" / "WinGet", 5)]
    for k in ("ProgramFiles", "ProgramFiles(x86)"):
        if os.environ.get(k):
            raices.append((Path(os.environ[k]), 3))
    fname = nombre.lower() + ".exe"
    for raiz, prof in raices:
        if not raiz.is_dir():
            continue
        base = len(raiz.parts)
        for dp, dn, fn in os.walk(str(raiz)):
            if len(Path(dp).parts) - base >= prof:
                dn[:] = []
            for f in fn:
                if f.lower() == fname:
                    return str(Path(dp) / f)
    return None


def carpeta_trabajo_por_defecto():
    return AQUI.parent.parent          # ...\solidcraft\sistema -> ...\solidcraft -> carpeta que lo contiene


# ---------------------------------------------------------------- Claude Desktop
def claude_abierto():
    """True/False; None si no se puede saber."""
    if not ES_WIN:
        return None
    rc, out = ejecutar(["tasklist", "/FI", "IMAGENAME eq Claude.exe", "/NH"], 15)
    if rc != 0:
        return None
    return "claude.exe" in out.lower()


def candidatas_config():
    """Devuelve (ruta_a_usar, motivo, lista_de_todas_las_existentes)."""
    la, ad = os.environ.get("LOCALAPPDATA"), os.environ.get("APPDATA")
    msix_dirs = sorted(Path(la).glob("Packages/Claude_*")) if la else []
    msix_cfgs = [d / "LocalCache" / "Roaming" / "Claude" / "claude_desktop_config.json" for d in msix_dirs]
    clasico = Path(ad) / "Claude" / "claude_desktop_config.json" if ad else None
    existentes = [p for p in msix_cfgs + ([clasico] if clasico else []) if p.exists()]
    if msix_cfgs:
        # Instalacion MSIX/Store/winget: la app lee la copia virtualizada, NO %APPDATA%
        elegido = msix_cfgs[0]
        if elegido.parent.is_dir() or elegido.exists():
            return elegido, "instalacion MSIX: la app lee la copia virtualizada", existentes
        return elegido, "instalacion MSIX, pero la carpeta de configuracion aun no existe (abre Claude Desktop una vez)", existentes
    if clasico:
        return clasico, "instalacion clasica (%APPDATA%)", existentes
    return None, "no hay Claude Desktop instalado o faltan variables de entorno", existentes


def bloque_esperado(cli, trabajo):
    return {"command": cli, "args": ["mcp", "--allow-path", str(trabajo)]}


def cargar_config(ruta):
    if not ruta.exists():
        return {}
    texto = ruta.read_text(encoding="utf-8-sig")
    if not texto.strip():
        return {}
    datos = json.loads(texto)              # ValueError si esta corrupto: NO se toca
    if not isinstance(datos, dict):
        raise ValueError("el JSON raiz no es un objeto")
    return datos


def configurar(cli, trabajo, ruta_forzada=None, aplicar=False, sobrescribir=False, forzar=False):
    if not cli:
        rec("FAIL", "config", "no hay solidcraft-cli.exe: instala SolidCraft primero")
        return 1
    if ruta_forzada:
        ruta, motivo, _ = Path(ruta_forzada), "ruta indicada con --config", []
    else:
        ruta, motivo, existentes = candidatas_config()
        if ruta is None:
            rec("FAIL", "config", motivo)
            return 1
        if len(existentes) > 1:
            rec("WARN", "config", "hay %d ficheros de configuracion; se usa %s (%s). Los demas no se tocan: %s" %
                (len(existentes), ruta, motivo, "; ".join(str(p) for p in existentes if p != ruta)))
    if not ruta.parent.is_dir():
        rec("FAIL", "config", "no existe la carpeta %s (%s). Abre Claude Desktop una vez y vuelve a ejecutar" % (ruta.parent, motivo))
        return 1
    try:
        datos = cargar_config(ruta)
    except (ValueError, OSError) as e:
        rec("FAIL", "config", "no se puede leer %s (%s). No se modifica nada: arreglalo a mano" % (ruta, e))
        return 1
    nuevo = bloque_esperado(cli, trabajo)
    servidores = datos.get("mcpServers")
    if servidores is not None and not isinstance(servidores, dict):
        rec("FAIL", "config", "'mcpServers' no es un objeto en %s; no se modifica" % ruta)
        return 1
    actual = (servidores or {}).get(SERVER)
    if actual == nuevo:
        rec("OK", "config", "%s ya contiene el bloque correcto (%s)" % (ruta, motivo))
        return 0
    if actual is not None and not sobrescribir:
        rec("WARN", "config", "ya existe un bloque '%s' DISTINTO en %s:\n    actual:   %s\n    esperado: %s\n    Usa --sobrescribir para reemplazarlo." %
            (SERVER, ruta, json.dumps(actual, ensure_ascii=False), json.dumps(nuevo, ensure_ascii=False)))
        return 2
    otros = [k for k in (servidores or {}) if k != SERVER]
    log("Fichero: %s (%s)" % (ruta, motivo))
    log("Se %s mcpServers.%s = %s" % ("reemplaza" if actual else "anade", SERVER, json.dumps(nuevo, ensure_ascii=False)))
    log("Se conservan intactos: otras claves %s y otros servidores %s" % ([k for k in datos if k != "mcpServers"], otros))
    if not aplicar:
        rec("OK", "config (simulacion)", "no se ha escrito nada; repite con --aplicar")
        return 0
    ab = claude_abierto()
    if ab and not forzar:
        rec("FAIL", "config", "Claude Desktop esta abierto. Cierralo del todo (tambien el icono de la bandeja del sistema) y repite; "
                              "si no, la app puede pisar el cambio")
        return 1
    if ab is None:
        rec("WARN", "config", "no puedo saber si Claude Desktop esta abierto: asegurate de haberlo cerrado del todo")
    copia = None
    if ruta.exists():
        copia = ruta.with_name(ruta.name + ".bak-" + time.strftime("%Y%m%d-%H%M%S"))
        shutil.copy2(str(ruta), str(copia))
    datos.setdefault("mcpServers", {})[SERVER] = nuevo
    tmp = ruta.with_name(ruta.name + ".tmp")
    tmp.write_text(json.dumps(datos, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    try:
        comprobado = json.loads(tmp.read_text(encoding="utf-8"))
        assert comprobado["mcpServers"][SERVER] == nuevo
    except Exception as e:                                     # noqa: BLE001
        tmp.unlink()
        rec("FAIL", "config", "la verificacion del fichero nuevo fallo (%s); no se ha cambiado nada" % e)
        return 1
    os.replace(str(tmp), str(ruta))
    rec("OK", "config", "escrito %s%s. Reinicia Claude Desktop para que cargue el servidor" %
        (ruta, "; copia de seguridad: " + copia.name if copia else " (fichero nuevo)"))
    return 0


# ---------------------------------------------------------------- diagnostico e instalacion
def diagnostico(trabajo, ruta_forzada=None):
    log("=== diagnostico v%s | %s | Python %s ===" % (VERSION, platform.platform(), platform.python_version()))
    if not ES_WIN:
        rec("WARN", "sistema", "esto no es Windows: el kit esta pensado para Windows 10/11")
    if sys.version_info < (3, 8):
        rec("FAIL", "python", "hace falta 3.8 o superior")
    else:
        rec("OK", "python", platform.python_version())
    w = shutil.which("winget")
    if w:
        rc, out = ejecutar([w, "--version"], 20)
        rec("OK" if rc == 0 else "WARN", "winget", out.strip()[:40])
    else:
        rec("WARN", "winget", "no esta en el PATH: SolidCraft se instala a mano con el MSI (%s)" % MSI_URL)
    cli, gui = buscar_exe("solidcraft-cli"), buscar_exe("solidcraft")
    if cli:
        rc, out = ejecutar([cli, "--version"], 20)
        rec("OK", "solidcraft-cli", "%s (%s)" % (cli, out.strip()[:40]))
    else:
        rec("WARN", "solidcraft-cli", "no encontrado: ejecuta 'instalar'")
    rec("OK" if gui else "WARN", "solidcraft.exe", gui or "no encontrado")
    rec("OK" if shutil.which("git") else "WARN", "git", "opcional: solo para clonar/publicar el repo")
    ruta, motivo, existentes = candidatas_config() if not ruta_forzada else (Path(ruta_forzada), "indicada", [Path(ruta_forzada)])
    if ruta is None:
        rec("WARN", "claude desktop", motivo)
    else:
        rec("OK", "claude desktop", "%s [%s]" % (ruta, motivo))
        try:
            srv = (cargar_config(ruta).get("mcpServers") or {}).get(SERVER)
            if srv is None:
                rec("WARN", "config.solidcraft", "falta el bloque: ejecuta 'configurar'")
            elif cli and srv == bloque_esperado(cli, trabajo):
                rec("OK", "config.solidcraft", "bloque correcto")
            else:
                rec("WARN", "config.solidcraft", "existe pero difiere de lo esperado: %s" % json.dumps(srv, ensure_ascii=False))
        except (ValueError, OSError) as e:
            rec("WARN", "config.solidcraft", "no se pudo leer: %s" % e)
    ab = claude_abierto()
    rec("OK", "claude abierto", "no" if ab is False else ("si (cierralo del todo antes de configurar)" if ab else "desconocido"))
    return cli


def instalar():
    if buscar_exe("solidcraft-cli") and buscar_exe("solidcraft"):
        rec("OK", "instalar", "SolidCraft ya esta instalado")
        return 0
    w = shutil.which("winget")
    if not w:
        rec("FAIL", "instalar", "sin winget. Descarga e instala el MSI a mano: %s (Windows pedira confirmacion; "
                                "no esta firmado: SmartScreen > Mas informacion > Ejecutar de todos modos)" % MSI_URL)
        return 1
    rc, out = ejecutar([w, "show", "--id", WINGET_ID, "-e"], 60)
    if rc != 0:
        rec("FAIL", "instalar", "winget no encuentra %s (rc=%s). Usa el MSI: %s" % (WINGET_ID, rc, MSI_URL))
        return 1
    log("Se va a ejecutar: winget install --id %s -e  (puede salir el aviso de Control de cuentas de usuario)" % WINGET_ID)
    if not preguntar("¿Instalar SolidCraft ahora?"):
        rec("WARN", "instalar", "omitido por el usuario")
        return 2
    rc = subprocess.call([w, "install", "--id", WINGET_ID, "-e", "--accept-package-agreements", "--accept-source-agreements"])
    if buscar_exe("solidcraft-cli"):
        rec("OK", "instalar", "winget rc=%s; solidcraft-cli encontrado" % rc)
        return 0
    rec("FAIL", "instalar", "winget rc=%s y solidcraft-cli no aparece. Cierra y abre esta ventana (PATH) y repite; si sigue, usa el MSI: %s" % (rc, MSI_URL))
    return 1


# ---------------------------------------------------------------- asistente
def trabajo_invalido(raiz, trabajo):
    """Devuelve un texto de error si la carpeta de trabajo es el propio repo o esta dentro de el; si no, None."""
    try:
        r, t = Path(raiz).resolve(), Path(trabajo).resolve()
    except OSError:
        return None
    if t == r or r in t.parents:
        return ("la carpeta de trabajo no puede ser la del repo ni estar dentro de ella (%s). "
                "Elige la carpeta que CONTIENE al repo (por ejemplo %s) o una nueva." % (r, r.parent))
    return None


def copiar_kit(origen_raiz, destino):
    ign = shutil.ignore_patterns("__pycache__", "*.pyc", "logs", "resultados", "salida", "trabajos", "*.pid", "flag.*")
    for rel in ("kit/solidcraft", "docs"):
        src = origen_raiz / rel
        dst = destino / ("solidcraft" if rel.endswith("solidcraft") else "docs")
        if src.resolve() == dst.resolve():
            continue
        shutil.copytree(str(src), str(dst), ignore=ign, dirs_exist_ok=True)
    for f in ("PROMPT_PRINCIPAL.md", "README.md"):
        if (origen_raiz / f).exists() and (origen_raiz / f).resolve() != (destino / f).resolve():
            shutil.copy2(str(origen_raiz / f), str(destino / f))
    (destino / "solidcraft" / "salida").mkdir(parents=True, exist_ok=True)
    (destino / "_obsoleto").mkdir(parents=True, exist_ok=True)


def asistente(args):
    log("=== asistente v%s ===" % VERSION)
    raiz = AQUI.parents[2]                                   # repo: ...\kit\solidcraft\sistema -> raiz
    hay_repo = (raiz / "kit" / "solidcraft").is_dir() and (raiz / "docs").is_dir()
    trabajo = Path(args.trabajo) if args.trabajo else None
    if hay_repo:
        padre = raiz.parent
        if padre.name.lower() in ("downloads", "descargas", "desktop", "escritorio") or padre == padre.parent:
            por_defecto = str(Path.home() / "ClaudeSolidCraft")
        else:
            por_defecto = str(padre)               # la carpeta que contiene al repo (normalmente la que conecto Claude)
        if trabajo is None:
            for _ in range(3):
                try:
                    r = input("Carpeta de trabajo (la que conectaras a Claude, NO la del repo) [%s]: " % por_defecto).strip().strip('"')
                except EOFError:
                    r = ""
                trabajo = Path(r or por_defecto)
                err = trabajo_invalido(raiz, trabajo)
                if not err:
                    break
                log("AVISO: " + err)
                trabajo = None
            if trabajo is None:
                rec("FAIL", "copiar", "no se eligio una carpeta de trabajo valida")
                return fin()
        else:
            err = trabajo_invalido(raiz, trabajo)
            if err:
                rec("FAIL", "copiar", err)
                return fin()
        trabajo.mkdir(parents=True, exist_ok=True)
        copiar_kit(raiz, trabajo)
        rec("OK", "copiar", "kit copiado a %s (scripts nuevos o modificados se actualizan; tus salidas y logs no se tocan)" % trabajo)
        sistema = trabajo / "solidcraft" / "sistema"
    else:
        trabajo = trabajo or carpeta_trabajo_por_defecto()
        sistema = AQUI
        rec("OK", "copiar", "se trabaja en el sitio: %s" % trabajo)
    cli = diagnostico(trabajo)
    if not cli:
        if instalar() == 0:
            cli = buscar_exe("solidcraft-cli")
    if cli:
        rc = configurar(cli, trabajo, args.config, aplicar=False, sobrescribir=args.sobrescribir, forzar=args.forzar)
        if rc == 0 and preguntar("¿Aplicar este cambio en la configuracion de Claude Desktop (se hace copia de seguridad)?"):
            for intento in range(3):
                rc = configurar(cli, trabajo, args.config, aplicar=True, sobrescribir=args.sobrescribir, forzar=args.forzar)
                if rc == 0 or claude_abierto() is not True:
                    break
                input("Cierra Claude Desktop del todo (tambien en la bandeja) y pulsa Enter...")
    demonio = sistema / "demonio_ordenes.py"
    if demonio.exists() and preguntar("¿Autorizar ahora los scripts basicos del demonio de ordenes (veras el hash y tendras que escribir SI)?"):
        subprocess.call([sys.executable, str(demonio), "--autorizar"])
    log("")
    log("PASOS MANUALES QUE NINGUN SCRIPT PUEDE HACER POR TI:")
    log("  1. Reinicia Claude Desktop (cierralo del todo y vuelve a abrirlo) para que cargue el servidor 'solidcraft'.")
    log("  2. Crea un proyecto en Claude, pega PROMPT_PRINCIPAL.md en 'Instrucciones' (cambia <CARPETA_TRABAJO> por %s)." % trabajo)
    log("  3. Abre la conversacion DENTRO del proyecto en la app de escritorio de ESTE PC y conecta la carpeta: %s" % trabajo)
    log("  4. Instala tu laminador (para Anycubic Slicer Next, descargalo de la web de Anycubic).")
    log("  5. Doble clic en %s y escribe a Claude: 'Empieza el arranque inicial'." % (trabajo / "solidcraft" / "lanzar_todo.bat"))
    return fin()


def fin():
    estado = "FALLO" if CONTADOR["FAIL"] else ("AVISOS" if CONTADOR["WARN"] else "OK")
    log("RESULTADO: %s | OK=%d WARN=%d FAIL=%d" % (estado, CONTADOR["OK"], CONTADOR["WARN"], CONTADOR["FAIL"]))
    return 1 if CONTADOR["FAIL"] else 0


def main():
    ap = argparse.ArgumentParser(description="Prepara el PC para Claude + SolidCraft")
    ap.add_argument("accion", choices=["diagnostico", "instalar", "configurar", "todo"])
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--trabajo")
    ap.add_argument("--config")
    ap.add_argument("--sobrescribir", action="store_true")
    ap.add_argument("--forzar", action="store_true")
    args = ap.parse_args()
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        LOG_FILE.write_text("", encoding="utf-8")
    except OSError:
        pass
    trabajo = Path(args.trabajo) if args.trabajo else carpeta_trabajo_por_defecto()
    if args.accion == "todo":
        return asistente(args)
    if args.accion == "diagnostico":
        diagnostico(trabajo, args.config)
        return fin()
    if args.accion == "instalar":
        rc = instalar()
        fin()
        return rc
    cli = buscar_exe("solidcraft-cli")
    rc = configurar(cli, trabajo, args.config, args.aplicar, args.sobrescribir, args.forzar)
    fin()
    return rc


if __name__ == "__main__":
    sys.exit(main())

"""Pruebas de configurar() (fusion de claude_desktop_config.json) y de build_3mf.py. Solo libreria estandar."""
import json, os, struct, subprocess, sys, tempfile, unittest, zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SISTEMA = RAIZ / "kit" / "solidcraft" / "sistema"
sys.path.insert(0, str(SISTEMA))
import instalar_entorno as ie  # noqa: E402

CLI = r"C:\Program Files\SolidCraft\solidcraft-cli.exe"
TRABAJO = r"C:\Users\x\ClaudeSolidCraft"


class Configurar(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.cfg = self.d / "claude_desktop_config.json"

    def run_cfg(self, **kw):
        return ie.configurar(CLI, TRABAJO, ruta_forzada=str(self.cfg), forzar=True, **kw)

    def leer(self):
        return json.loads(self.cfg.read_text(encoding="utf-8"))

    def test_simulacion_no_escribe(self):
        self.assertEqual(self.run_cfg(), 0)
        self.assertFalse(self.cfg.exists())

    def test_fichero_nuevo(self):
        self.assertEqual(self.run_cfg(aplicar=True), 0)
        self.assertEqual(self.leer()["mcpServers"]["solidcraft"], ie.bloque_esperado(CLI, TRABAJO))

    def test_conserva_otras_claves_y_servidores(self):
        self.cfg.write_text(json.dumps({"theme": "dark", "mcpServers": {"otro": {"command": "x"}}}), encoding="utf-8")
        self.assertEqual(self.run_cfg(aplicar=True), 0)
        d = self.leer()
        self.assertEqual(d["theme"], "dark")
        self.assertEqual(d["mcpServers"]["otro"], {"command": "x"})
        self.assertIn("solidcraft", d["mcpServers"])

    def test_crea_copia_de_seguridad(self):
        self.cfg.write_text('{"a": 1}', encoding="utf-8")
        self.run_cfg(aplicar=True)
        self.assertEqual(len(list(self.d.glob("*.bak-*"))), 1)

    def test_bloque_identico_no_cambia_nada(self):
        self.run_cfg(aplicar=True)
        antes = self.cfg.read_text(encoding="utf-8")
        self.assertEqual(self.run_cfg(aplicar=True), 0)
        self.assertEqual(antes, self.cfg.read_text(encoding="utf-8"))

    def test_bloque_distinto_sin_sobrescribir_rc2(self):
        self.cfg.write_text(json.dumps({"mcpServers": {"solidcraft": {"command": "viejo"}}}), encoding="utf-8")
        self.assertEqual(self.run_cfg(aplicar=True), 2)
        self.assertEqual(self.leer()["mcpServers"]["solidcraft"], {"command": "viejo"})

    def test_sobrescribir(self):
        self.cfg.write_text(json.dumps({"mcpServers": {"solidcraft": {"command": "viejo"}}}), encoding="utf-8")
        self.assertEqual(self.run_cfg(aplicar=True, sobrescribir=True), 0)
        self.assertEqual(self.leer()["mcpServers"]["solidcraft"], ie.bloque_esperado(CLI, TRABAJO))

    def test_json_corrupto_no_se_toca(self):
        self.cfg.write_text("{esto no es json", encoding="utf-8")
        self.assertEqual(self.run_cfg(aplicar=True), 1)
        self.assertEqual(self.cfg.read_text(encoding="utf-8"), "{esto no es json")

    def test_mcpservers_no_objeto(self):
        self.cfg.write_text(json.dumps({"mcpServers": []}), encoding="utf-8")
        self.assertEqual(self.run_cfg(aplicar=True), 1)

    def test_mayusculas_en_ruta_son_equivalentes_en_windows(self):
        from unittest import mock
        self.cfg.write_text(json.dumps({"mcpServers": {"solidcraft": {
            "command": CLI.replace("solidcraft-cli.exe", "SOLIDCRAFT-CLI.EXE").replace("\\", "/"),
            "args": ["mcp", "--allow-path", TRABAJO.lower()]}}}), encoding="utf-8")
        antes = self.cfg.read_text(encoding="utf-8")
        with mock.patch.object(ie, "ES_WIN", True):
            self.assertEqual(self.run_cfg(aplicar=True), 0)
        self.assertEqual(antes, self.cfg.read_text(encoding="utf-8"))      # no la reescribe
        self.assertEqual(len(list(self.d.glob("*.bak-*"))), 0)

    def test_sin_cli(self):
        self.assertEqual(ie.configurar(None, TRABAJO, ruta_forzada=str(self.cfg)), 1)


class CarpetaTrabajo(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp())
        self.repo = self.base / "solidcraft-claude-kit"
        (self.repo / "kit" / "solidcraft" / "sistema").mkdir(parents=True)
        (self.repo / "kit" / "solidcraft" / "lanzar_todo.bat").write_text("x", encoding="utf-8")
        (self.repo / "docs").mkdir()
        (self.repo / "docs" / "00-indice.md").write_text("i", encoding="utf-8")
        (self.repo / "PROMPT_PRINCIPAL.md").write_text("p", encoding="utf-8")

    def test_repo_o_dentro_son_invalidos(self):
        self.assertIsNotNone(ie.trabajo_invalido(self.repo, self.repo))
        self.assertIsNotNone(ie.trabajo_invalido(self.repo, self.repo / "sub"))

    def test_padre_y_otra_carpeta_son_validos(self):
        self.assertIsNone(ie.trabajo_invalido(self.repo, self.base))
        self.assertIsNone(ie.trabajo_invalido(self.repo, self.base / "otra"))

    def test_copiar_kit_en_la_carpeta_padre(self):
        ie.copiar_kit(self.repo, self.base)
        self.assertTrue((self.base / "solidcraft" / "lanzar_todo.bat").exists())
        self.assertTrue((self.base / "docs" / "00-indice.md").exists())
        self.assertTrue((self.base / "solidcraft" / "salida").is_dir())

    def test_copiar_kit_no_falla_si_destino_es_el_repo(self):
        ie.copiar_kit(self.repo, self.repo)      # defensa extra: no debe lanzar excepcion
        self.assertTrue((self.repo / "docs" / "00-indice.md").exists())


class Descarga(unittest.TestCase):
    def test_descargar_calcula_sha256_y_rechaza_pequenos(self):
        import hashlib
        d = Path(tempfile.mkdtemp())
        origen = d / "x.bin"
        origen.write_bytes(b"a" * 2_000_000)
        n, sha = ie.descargar(origen.as_uri(), d / "copia.bin")
        self.assertEqual(n, 2_000_000)
        self.assertEqual(sha, hashlib.sha256(b"a" * 2_000_000).hexdigest())
        pequeno = d / "p.bin"
        pequeno.write_bytes(b"<html>")
        with self.assertRaises(ValueError):
            ie.descargar(pequeno.as_uri(), d / "c2.bin")

    def test_fallo_ssl_reintenta_con_herramientas_de_windows(self):
        import ssl, urllib.error
        from unittest import mock
        d = Path(tempfile.mkdtemp())
        destino = d / "m.msi"

        def falso_curl(cmd, *a, **k):          # simula curl.exe escribiendo el fichero
            Path(cmd[cmd.index("-o") + 1]).write_bytes(b"b" * 1_500_000)
            return 0
        err = urllib.error.URLError(ssl.SSLCertVerificationError("unable to get local issuer certificate"))
        with mock.patch.object(ie.urllib.request, "urlopen", side_effect=err), \
             mock.patch.object(ie.shutil, "which", return_value="curl"), \
             mock.patch.object(ie.subprocess, "call", side_effect=falso_curl):
            n, sha = ie.descargar("https://example.invalid/x.msi", destino)
        self.assertEqual(n, 1_500_000)

    def test_error_de_red_no_ssl_no_reintenta(self):
        import urllib.error
        from unittest import mock
        err = urllib.error.URLError(OSError("sin red"))
        with mock.patch.object(ie.urllib.request, "urlopen", side_effect=err):
            with self.assertRaises(urllib.error.URLError):
                ie.descargar("https://example.invalid/x.msi", Path(tempfile.mkdtemp()) / "m.msi")

    def test_msi_fijado_a_version_probada(self):
        self.assertIn("v" + ie.SC_VERSION, ie.MSI_URL)
        self.assertNotIn("latest", ie.MSI_URL)


def stl_binario(ruta, tris):
    with open(ruta, "wb") as f:
        f.write(b"\0" * 80 + struct.pack("<I", len(tris)))
        for t in tris:
            f.write(struct.pack("<12fH", 0, 0, 0, *[c for v in t for c in v], 0))


class Build3mf(unittest.TestCase):
    def test_3mf_multiparte(self):
        d = Path(tempfile.mkdtemp())
        a = [(0, 0, 0), (10, 0, 0), (0, 10, 0)]
        b = [(0, 0, 0), (10, 0, 0), (0, 0, 10)]
        stl_binario(d / "F1_a.stl", [a])
        stl_binario(d / "F2_b.stl", [b])
        man = {"titulo": "t", "descripcion": "d", "salida": "out.3mf",
               "partes": [["F1_a.stl", "A", 1], ["F2_b.stl", "B", 2]]}
        (d / "m.json").write_text(json.dumps(man), encoding="utf-8")
        r = subprocess.run([sys.executable, str(SISTEMA / "build_3mf.py"), str(d / "m.json")],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        z = zipfile.ZipFile(d / "out.3mf")
        self.assertIsNone(z.testzip())
        self.assertTrue(any(n.endswith(".model") for n in z.namelist()))


if __name__ == "__main__":
    unittest.main()

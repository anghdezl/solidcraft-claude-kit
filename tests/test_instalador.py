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

    def test_sin_cli(self):
        self.assertEqual(ie.configurar(None, TRABAJO, ruta_forzada=str(self.cfg)), 1)


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

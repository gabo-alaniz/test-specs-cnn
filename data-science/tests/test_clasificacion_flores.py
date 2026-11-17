"""Pruebas del notebook data-science/clasificacion_flores.ipynb (spec 002).

Un asistente ejecuta en un kernel solo las celdas cuyo `metadata.tags` se indica, para probar cada
tarea sin que existan las posteriores. Se lanzan desde la raíz del repositorio.
"""
import subprocess
import sys
import unittest
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[2]
DS = ROOT / "data-science"
NOTEBOOK = DS / "clasificacion_flores.ipynb"
ETIQUETAS = ["titulo", "config", "descarga", "datos", "modelo", "entrenamiento", "evaluacion"]


def leer_notebook() -> nbformat.NotebookNode:
    return nbformat.read(NOTEBOOK, as_version=4)


def etiqueta(celda) -> str:
    return celda.metadata.get("tags", [""])[0]


def ejecutar(etiquetas: list[str], timeout: int = 1800) -> nbformat.NotebookNode:
    """Ejecuta en un kernel nuevo, en orden, las celdas de código con esas etiquetas."""
    origen = leer_notebook()
    nb = nbformat.v4.new_notebook()
    nb.metadata["kernelspec"] = origen.metadata["kernelspec"]
    nb.cells = [c for c in origen.cells if c.cell_type == "code" and etiqueta(c) in etiquetas]
    cliente = NotebookClient(nb, timeout=timeout, kernel_name="python3", resources={"metadata": {"path": str(DS)}})
    # El kernel debe usar el mismo intérprete (el del venv) que lanza las pruebas, no el `python` del PATH.
    cliente.km = cliente.create_kernel_manager()
    cliente.km.kernel_spec.argv = [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"]
    cliente.execute()
    return nb


def salida_texto(nb: nbformat.NotebookNode) -> str:
    partes = []
    for celda in nb.cells:
        for salida in celda.get("outputs", []):
            partes.append(salida.get("text", "") or salida.get("data", {}).get("text/plain", ""))
    return "\n".join(partes)


class EstructuraTestCase(unittest.TestCase):
    """TC-001: git ignora los datos y el notebook es válido con celdas etiquetadas."""

    def test_datos_ignorados_por_git(self) -> None:
        r = subprocess.run(
            ["git", "check-ignore", "-q", "data-science/data/flower_photos/x.jpg"], cwd=ROOT, check=False
        )
        self.assertEqual(r.returncode, 0, "data-science/data/ debe estar en .gitignore")

    def test_notebook_valido_con_celdas_etiquetadas(self) -> None:
        nb = leer_notebook()
        nbformat.validate(nb)
        etiquetas = [etiqueta(c) for c in nb.cells]
        self.assertTrue({"config", "descarga"} <= set(etiquetas))
        self.assertTrue(set(etiquetas) <= set(ETIQUETAS), f"etiquetas desconocidas: {etiquetas}")
        self.assertEqual(etiquetas, sorted(etiquetas, key=ETIQUETAS.index), "celdas fuera de orden")


class DescargaTestCase(unittest.TestCase):
    """TC-002: la descarga deja flower_photos con 5 clases y sin credenciales de Kaggle."""

    def test_descarga_deja_cinco_clases_con_imagenes(self) -> None:
        nb = ejecutar(["config", "descarga"])
        clases = sorted(p.name for p in (DS / "data" / "flower_photos").iterdir() if p.is_dir())
        self.assertEqual(clases, ["daisy", "dandelion", "roses", "sunflowers", "tulips"])
        for clase in clases:
            self.assertTrue(any((DS / "data" / "flower_photos" / clase).glob("*.jpg")), clase)
        self.assertIn("5 clases", salida_texto(nb))

    def test_sin_credenciales_de_kaggle(self) -> None:
        fuente = "\n".join(c.source for c in leer_notebook().cells).lower()
        self.assertNotIn("kaggle", fuente)


class DivisionTestCase(unittest.TestCase):
    """TC-003: la división con la misma semilla es idéntica y disjunta (AC-005)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.nb = ejecutar(["config", "descarga", "datos"])
        cls.salida = salida_texto(cls.nb)

    def test_la_celda_de_datos_construye_lotes(self) -> None:
        self.assertIn("entrenamiento:", self.salida)
        self.assertIn("(32, 3, 96, 96)", self.salida)

    def test_division_reproducible_y_disjunta(self) -> None:
        codigo = "\n".join(c.source for c in leer_notebook().cells if etiqueta(c) in ("config", "descarga", "datos"))
        codigo += """
a_ent, a_val = dividir_rutas(FLOWERS_DIR, SEED)
b_ent, b_val = dividir_rutas(FLOWERS_DIR, SEED)
otra_ent, _ = dividir_rutas(FLOWERS_DIR, SEED + 1)
print("IGUALES", a_ent == b_ent and a_val == b_val)
print("DISJUNTAS", not set(a_ent) & set(a_val))
print("COMPLETAS", len(a_ent) + len(a_val) == len(list(FLOWERS_DIR.glob("*/*.jpg"))))
print("OTRA_SEMILLA_DIFIERE", a_ent != otra_ent)
"""
        nb = nbformat.v4.new_notebook()
        nb.metadata["kernelspec"] = leer_notebook().metadata["kernelspec"]
        nb.cells = [nbformat.v4.new_code_cell(codigo)]
        cliente = NotebookClient(nb, timeout=900, kernel_name="python3", resources={"metadata": {"path": str(DS)}})
        cliente.km = cliente.create_kernel_manager()
        cliente.km.kernel_spec.argv = [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"]
        cliente.execute()
        texto = salida_texto(nb)
        for esperado in ("IGUALES True", "DISJUNTAS True", "COMPLETAS True", "OTRA_SEMILLA_DIFIERE True"):
            self.assertIn(esperado, texto)


class EntrenamientoTestCase(unittest.TestCase):
    """TC-004: el entrenamiento termina en CPU y registra pérdida y exactitud de cada época (AC-003)."""

    @classmethod
    def setUpClass(cls) -> None:
        for carpeta in ("logs", "checkpoints"):
            ruta = DS / "data" / carpeta
            if ruta.exists():
                for archivo in sorted(ruta.rglob("*"), reverse=True):
                    archivo.rmdir() if archivo.is_dir() else archivo.unlink()
        cls.nb = ejecutar(["config", "descarga", "datos", "modelo", "entrenamiento"])
        cls.salida = salida_texto(cls.nb)

    def test_el_modelo_se_construye(self) -> None:
        self.assertIn("CnnFlores:", self.salida)
        self.assertIn("(2, 5)", self.salida)

    def test_entrena_en_cpu_y_termina(self) -> None:
        self.assertIn("en CPU, 3 épocas", self.salida)

    def test_registra_perdida_y_exactitud_por_epoca(self) -> None:
        import csv

        csvs = list((DS / "data" / "logs" / "flores").glob("version_*/metrics.csv"))
        self.assertTrue(csvs, "el CSVLogger no escribió metrics.csv")
        with csvs[-1].open() as f:
            filas = list(csv.DictReader(f))
        for metrica in ("perdida_ent", "perdida_val", "exactitud_ent", "exactitud_val"):
            epocas = {fila["epoch"] for fila in filas if fila.get(metrica)}
            self.assertEqual(epocas, {"0", "1", "2"}, f"{metrica} debe registrarse en cada una de las 3 épocas")


class EvaluacionTestCase(unittest.TestCase):
    """TC-005: la evaluación produce métricas y gráficas sobre validación (AC-004)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.nb = ejecutar(["config", "descarga", "datos", "modelo", "entrenamiento", "evaluacion"])
        cls.celda = next(c for c in cls.nb.cells if etiqueta(c) == "evaluacion")
        cls.texto = salida_texto(cls.nb)

    def test_exactitud_y_reporte_por_clase(self) -> None:
        self.assertRegex(self.texto, r"exactitud en validación: 0\.\d{3} \(\d+ imágenes\)")
        for clase in ("daisy", "dandelion", "roses", "sunflowers", "tulips"):
            self.assertIn(clase, self.texto)
        for columna in ("precision", "recall", "f1-score"):
            self.assertIn(columna, self.texto)

    def test_genera_tres_figuras(self) -> None:
        # matriz de confusión, curvas de pérdida y exactitud (una figura con dos ejes) y muestra de predicciones
        imagenes = [o for o in self.celda.outputs if o.get("output_type") == "display_data" and "image/png" in o.data]
        self.assertEqual(len(imagenes), 3, f"se esperaban 3 figuras, hay {len(imagenes)}")

    def test_sin_errores_en_la_celda(self) -> None:
        self.assertFalse([o for o in self.celda.outputs if o.get("output_type") == "error"])


class NotebookCompletoTestCase(unittest.TestCase):
    """TC-006: el notebook completo se ejecuta de principio a fin sin errores (AC-001)."""

    def test_ejecucion_completa_sin_errores(self) -> None:
        nb = leer_notebook()
        for celda in nb.cells:
            celda.get("outputs", []).clear() if celda.cell_type == "code" else None
        cliente = NotebookClient(nb, timeout=1800, kernel_name="python3", resources={"metadata": {"path": str(DS)}})
        cliente.km = cliente.create_kernel_manager()
        cliente.km.kernel_spec.argv = [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"]
        cliente.execute()  # lanza CellExecutionError ante cualquier excepción
        errores = [o for c in nb.cells if c.cell_type == "code" for o in c.outputs if o.get("output_type") == "error"]
        self.assertEqual(errores, [])
        self.assertTrue(all(c.get("execution_count") for c in nb.cells if c.cell_type == "code"))


class EntregaTestCase(unittest.TestCase):
    """TC-007: el .ipynb entregado trae salidas guardadas y no filtra credenciales ni rutas del equipo (AC-006)."""

    def setUp(self) -> None:
        self.nb = leer_notebook()
        self.crudo = NOTEBOOK.read_text(encoding="utf-8")

    def test_salidas_guardadas_de_metricas_y_graficas(self) -> None:
        codigo = [c for c in self.nb.cells if c.cell_type == "code"]
        self.assertTrue(all(c.outputs for c in codigo), "todas las celdas de código deben traer salida guardada")
        evaluacion = next(c for c in codigo if etiqueta(c) == "evaluacion")
        self.assertEqual(sum("image/png" in o.get("data", {}) for o in evaluacion.outputs), 3)
        self.assertIn("exactitud en validación", salida_texto(self.nb))

    def test_sin_errores_guardados(self) -> None:
        self.assertEqual([o for c in self.nb.cells if c.cell_type == "code" for o in c.outputs if o.get("output_type") == "error"], [])

    def test_sin_rutas_absolutas_del_equipo(self) -> None:
        for prohibido in (str(ROOT), "/home/", "/workspaces", "/Users/", "C:\\\\"):
            self.assertNotIn(prohibido, self.crudo, f"el notebook contiene {prohibido!r}")

    def test_sin_credenciales(self) -> None:
        minusculas = self.crudo.lower()
        for prohibido in ("kaggle", "api_key", "apikey", "auth_token", "password", "secret", "bearer "):
            self.assertNotIn(prohibido, minusculas, f"el notebook contiene {prohibido!r}")

    def test_tamano_razonable(self) -> None:
        self.assertLess(NOTEBOOK.stat().st_size, 5_000_000)


if __name__ == "__main__":
    unittest.main()

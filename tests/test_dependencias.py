"""Un solo origen de versiones: `poetry.lock`. `requirements-pruebas.txt` es
el subconjunto que instala la integración continua (Python 3.11, Linux) y
cada versión que fija debe ser una de las que el lock resolvió para ese
paquete (el lock separa algunas por plataforma o versión de Python). Si
alguien actualiza uno sin el otro, esta prueba falla."""
import re
from collections import defaultdict
from pathlib import Path

R = Path(__file__).resolve().parents[1]


def _lock() -> dict[str, set[str]]:
    texto = (R / "poetry.lock").read_text(encoding="utf-8").replace("\r\n", "\n")
    versiones = defaultdict(set)
    for n, v in re.findall(r'\[\[package\]\]\nname = "([^"]+)"\nversion = "([^"]+)"', texto):
        versiones[n.lower()].add(v)
    return versiones


def test_requirements_de_pruebas_fija_versiones_del_lock():
    lock = _lock()
    fijadas = re.findall(r"^([A-Za-z0-9_.-]+)==(\S+)", (R / "requirements-pruebas.txt").read_text(encoding="utf-8"),
                         flags=re.M)
    assert len(fijadas) >= 10
    distintas = {n: (v, sorted(lock.get(n.lower(), []))) for n, v in fijadas if v not in lock.get(n.lower(), set())}
    assert not distintas, f"requirements-pruebas.txt frente a poetry.lock: {distintas}"

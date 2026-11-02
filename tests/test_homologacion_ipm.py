"""Pruebas de integridad de la matriz de homologación GEIH ↔ Sisbén
(`src/indicadores/homologacion_ipm.py`).

No necesitan los datos de Azure: verifican la matriz contra los
diccionarios oficiales versionados en `docs/insumos/`. Su propósito
principal es que ninguna privación cite un código GEIH o Sisbén que no
exista en el diccionario (la lección del bug de vivienda del 2026-10-28,
ver `CLAUDE.md`).

Uso:
    poetry run pytest tests/test_homologacion_ipm.py
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location("homologacion_ipm", ROOT / "src" / "indicadores" / "homologacion_ipm.py")
h = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = h  # dataclasses necesita el módulo registrado
_SPEC.loader.exec_module(h)


@pytest.fixture(scope="module")
def codigos_geih() -> set[str]:
    return set(pd.read_excel(ROOT / "docs/insumos/DICCIONARIO_GEIH_2024.xlsx")["Nombre"].astype(str))


@pytest.fixture(scope="module")
def codigos_sisben() -> set[str]:
    hojas = pd.read_excel(ROOT / "docs/insumos/DICCIONARIO_SISBEN_2024.xlsx", sheet_name=None)
    return {str(n) for hoja in hojas.values() for n in hoja["Nombre"]}


def test_quince_privaciones_en_orden():
    assert [p.id for p in h.MATRIZ] == [f"I{i}" for i in range(1, 16)]


def test_estados_validos():
    for p in h.MATRIZ:
        assert p.estado in h.ESTADOS, f"{p.id}: estado '{p.estado}' no reconocido"


def test_pesos_oficiales_suman_uno_y_respetan_dimensiones():
    assert sum(p.peso_oficial for p in h.MATRIZ) == pytest.approx(1.0, abs=1e-3)
    for dim, n in h.DIMENSIONES.items():
        miembros = [p for p in h.MATRIZ if p.dimension == dim]
        assert len(miembros) == n, f"{dim}: {len(miembros)} privaciones, se esperaban {n}"
        assert sum(p.peso_oficial for p in miembros) == pytest.approx(0.2, abs=1e-3)


def test_codigos_geih_existen_en_el_diccionario(codigos_geih):
    for p in h.MATRIZ:
        faltan = [c for c in p.geih_original if c not in codigos_geih]
        assert not faltan, f"{p.id}: códigos GEIH sin entrada en el diccionario oficial: {faltan}"


def test_codigos_sisben_existen_en_el_diccionario(codigos_sisben):
    for p in h.MATRIZ:
        assert p.codigo_sisben in codigos_sisben, f"{p.id}: {p.codigo_sisben} no está en el diccionario Sisbén"
        faltan = [c for c in p.preguntas_sisben if c not in codigos_sisben]
        assert not faltan, f"{p.id}: preguntas Sisbén sin entrada en el diccionario: {faltan}"


def test_no_disponibles_declaran_que_no_se_reproducen():
    for p in h.MATRIZ:
        if p.estado == h.NO_DISPONIBLE:
            assert p.regla_geih.startswith("No reproducible"), p.id


def test_campos_obligatorios_completos():
    for p in h.MATRIZ:
        for campo in ("nombre", "regla_oficial", "regla_geih", "diferencias", "poblacion_referencia"):
            assert getattr(p, campo).strip(), f"{p.id}: campo '{campo}' vacío"
        assert "met-IPM p" in p.regla_oficial, f"{p.id}: la regla oficial no cita la página del documento DANE"


def test_insumos_diagnosticados_pertenecen_a_su_privacion():
    por_id = {p.id: p for p in h.MATRIZ}
    for priv, _, var, *_ in h.INSUMOS:
        assert var in por_id[priv].geih_original, f"{priv}: el insumo {var} no está en geih_original"

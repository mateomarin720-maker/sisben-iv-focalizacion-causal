"""Reglas de la imputación fraccional (FHDI) sobre la celda del Hot-Deck.

Usa la misma celda y la misma cadena de respaldos que el Hot-Deck
(`claves_por_nivel`), sin modificarlo: lo único que cambia es «un donante
sorteado» por «varios donantes con peso fraccional».

Reglas:
  1. Nivel: cada hogar usa el primer nivel de la cadena cuya celda tiene
     donantes (celda exacta → sin_menores → … → solo_depto → todo el
     registro), igual que el Hot-Deck.
  2. Donantes: M = 10 por hogar, sorteados sin reemplazo en esa celda y
     estratificados por grupo: al menos uno de cada grupo presente en la
     celda y el resto repartido según la proporción del grupo, π_g
     (mayores restos). Con un sorteo simple, en 4 de cada 10 hogares algún
     grupo poco frecuente de la celda no salía y la calibración no era
     exacta. Si un grupo tiene en la celda tantos donantes como le tocan o
     menos, entran todos los de ese grupo.
  3. Pesos: suman 1 por hogar y se calibran para que la distribución por
     grupo (A, B, C, D) ponderada de los donantes de cada hogar sea la de
     su celda, π_g: w_j = π_g(j) / n_g(j), con n_g el número de donantes
     del grupo g entre los sorteados (Kim y Fuller, 2004). Con el sorteo
     estratificado es exacta en todos los hogares (`calibrado`).
  4. FEFI (fully efficient fractional imputation): todos los donantes de
     la celda, que equivale a darle a cada hogar π de su celda. No se arma
     la base expandida.

Con los pesos calibrados, toda cantidad que dependa del grupo imputado
(proporción de A/B, errores de exclusión e inclusión, pobreza por grupo)
es la misma con M = 10 que con FEFI: el sorteo ya no agrega ruido.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.emparejamiento.emparejamiento_hotdeck_geih_sisben import claves_por_nivel

M_DONANTES = 10
GRUPOS = np.array(["A", "B", "C", "D"])
ELEGIBLE = (0, 1)  # A y B: el tratamiento T del proyecto


def _codigo_grupo(donante: pd.DataFrame) -> np.ndarray:
    codigos = pd.Categorical(donante["Grupo"], categories=GRUPOS).codes.astype(np.int8)
    if (codigos < 0).any():
        raise ValueError("Hay donantes sin grupo A-D: filtrar por Clasificacion antes de imputar")
    return codigos


def niveles(receptor: pd.DataFrame, donante: pd.DataFrame, receptor_en_codigos: bool = False):
    """Para cada nivel de la cadena: (nombre, clave del receptor, clave del
    donante). `receptor_en_codigos=True` cuando el receptor también es del
    Sisbén (validación interna), con la edad en ciclo de vida."""
    cr = claves_por_nivel(receptor, edad_en_codigos=receptor_en_codigos)
    cd = claves_por_nivel(donante, edad_en_codigos=True)
    return [(nombre, r.to_numpy(), d.to_numpy()) for (nombre, r), (_, d) in zip(cr, cd)]


def asignar_nivel(receptor: pd.DataFrame, donante: pd.DataFrame, receptor_en_codigos: bool = False):
    """Primer nivel con donantes para cada receptor.

    Devuelve (nivel, celda_donante): `nivel` es el nombre del nivel
    («pool_nacional» si ninguno tiene donantes) y `celda_donante` un código
    entero de la celda de donantes que le toca, común a receptores y
    donantes del mismo nivel. También devuelve, para cada donante, su
    código de celda en cada nivel (para sortear)."""
    n = len(receptor)
    nivel = np.full(n, "", dtype=object)
    celda = np.full(n, -1, dtype=np.int64)
    celdas_donante = []
    desplazamiento = 0
    for nombre, cr, cd in niveles(receptor, donante, receptor_en_codigos):
        codigos_d, unicas = pd.factorize(cd)
        celdas_donante.append(codigos_d + desplazamiento)
        falta = celda < 0
        if falta.any():
            pos = pd.Index(unicas).get_indexer(cr[falta])
            ok = pos >= 0
            idx = np.flatnonzero(falta)[ok]
            celda[idx] = pos[ok] + desplazamiento
            nivel[idx] = nombre
        desplazamiento += len(unicas)
    falta = celda < 0
    celda[falta] = desplazamiento  # todo el registro
    nivel[falta] = "pool_nacional"
    return nivel, celda, celdas_donante, desplazamiento


def probabilidades(receptor: pd.DataFrame, donante: pd.DataFrame, receptor_en_codigos: bool = False):
    """FEFI: π_g de la celda de cada receptor (n × 4, columnas A-D) y su nivel."""
    g = _codigo_grupo(donante)
    nivel, celda, celdas_donante, total = asignar_nivel(receptor, donante, receptor_en_codigos)
    tabla = np.zeros((total + 1, len(GRUPOS)))
    for codigos in celdas_donante:
        np.add.at(tabla, (codigos, g), 1.0)
    tabla[total] = np.bincount(g, minlength=len(GRUPOS))
    tabla = tabla / np.maximum(tabla.sum(axis=1, keepdims=True), 1)
    return tabla[celda], nivel


def _sin_repetir(rng, n: int, filas: int, m: int) -> np.ndarray:
    """filas × m índices en [0, n) sin repetir dentro de cada fila."""
    if n <= m:
        return np.tile(np.arange(n), (filas, 1))
    if n <= 4 * m:  # pocos: permutación de cada fila
        return np.argsort(rng.random((filas, n)), axis=1)[:, :m]
    idx = rng.integers(0, n, size=(filas, m))
    while True:
        s = np.sort(idx, axis=1)
        repetida = (s[:, 1:] == s[:, :-1]).any(axis=1)
        if not repetida.any():
            return idx
        idx[repetida] = rng.integers(0, n, size=(int(repetida.sum()), m))


def cupos_por_grupo(conteo: np.ndarray, m: int) -> np.ndarray:
    """Cuántos donantes de cada grupo le tocan a un hogar de una celda con
    `conteo` donantes por grupo: uno por grupo presente y el resto según la
    proporción (mayores restos), sin pasar de los que hay."""
    presentes = conteo > 0
    cupo = presentes.astype(int)
    resto = m - cupo.sum()
    if resto > 0:
        ideal = conteo / conteo.sum() * resto
        extra = np.floor(ideal).astype(int)
        faltan = resto - extra.sum()
        extra[np.argsort(-(ideal - extra), kind="stable")[:faltan]] += 1
        cupo = cupo + extra
    return np.minimum(cupo, conteo)


def donantes_fraccionales(receptor: pd.DataFrame, donante: pd.DataFrame, m: int = M_DONANTES, seed: int = 42,
                          receptor_en_codigos: bool = False) -> pd.DataFrame:
    """Base expandida receptor × donante con pesos fraccionales calibrados.

    Columnas: receptor (posición), donante (posición), grupo (0-3 = A-D),
    peso (suma 1 por receptor), nivel y calibrado (si la distribución por
    grupo ponderada reproduce exactamente π de la celda)."""
    rng = np.random.default_rng(seed)
    g = _codigo_grupo(donante)
    pi, _ = probabilidades(receptor, donante, receptor_en_codigos)
    nivel, celda, celdas_donante, total = asignar_nivel(receptor, donante, receptor_en_codigos)

    # Donantes de cada celda (de todos los niveles), ordenados por celda.
    cod = np.concatenate([*celdas_donante, np.full(len(donante), total)])
    pos = np.concatenate([np.arange(len(donante))] * (len(celdas_donante) + 1))
    orden = np.argsort(cod, kind="stable")
    cod, pos = cod[orden], pos[orden]
    inicio = np.searchsorted(cod, np.arange(total + 2))

    rec_l, don_l = [], []
    for c, receptores in pd.Series(np.arange(len(receptor))).groupby(celda):
        pool = pos[inicio[c]:inicio[c + 1]]
        k = len(receptores)
        g_pool = g[pool]
        cupo = cupos_por_grupo(np.bincount(g_pool, minlength=len(GRUPOS)), m)
        for grupo_k in np.flatnonzero(cupo):
            pool_g = pool[g_pool == grupo_k]
            rec_l.append(np.repeat(receptores.to_numpy(), cupo[grupo_k]))
            don_l.append(pool_g[_sin_repetir(rng, len(pool_g), k, cupo[grupo_k])].ravel())
    rec, don = np.concatenate(rec_l), np.concatenate(don_l)
    grupo = g[don]

    # Calibración: w = π_g / n_g dentro de cada receptor.
    conteo = np.zeros((len(receptor), len(GRUPOS)))
    np.add.at(conteo, (rec, grupo), 1.0)
    peso = pi[rec, grupo] / conteo[rec, grupo]
    suma = np.bincount(rec, peso, minlength=len(receptor))
    peso = peso / suma[rec]
    calibrado = ((pi > 0) <= (conteo > 0)).all(axis=1)
    return pd.DataFrame({"receptor": rec, "donante": don, "grupo": grupo, "peso": peso,
                         "nivel": nivel[rec], "calibrado": calibrado[rec]})


def probabilidad_por_receptor(expandida: pd.DataFrame, n: int) -> np.ndarray:
    """P(grupo) de cada receptor según sus donantes ponderados (n × 4)."""
    q = np.zeros((n, len(GRUPOS)))
    np.add.at(q, (expandida["receptor"].to_numpy(), expandida["grupo"].to_numpy()), expandida["peso"].to_numpy())
    return q


def contraste_placebo(y: np.ndarray, peso_hogar: np.ndarray, celda: np.ndarray, expandida: pd.DataFrame):
    """Regresión de Y sobre T = A/B con efectos fijos de celda en la base
    expandida, ponderada por fex × peso fraccional; error estándar robusto
    por conglomerado de hogar (los donantes de un hogar no son independientes).

    Con pesos calibrados el coeficiente es 0 exacto: cada hogar de una
    celda tiene la misma proporción ponderada de A/B, así que T no varía
    entre hogares dentro de la celda (Proposición 1)."""
    r = expandida["receptor"].to_numpy()
    ok = ~np.isnan(y[r])
    r = r[ok]
    t = np.isin(expandida["grupo"].to_numpy()[ok], ELEGIBLE).astype(float)
    w = peso_hogar[r] * expandida["peso"].to_numpy()[ok]
    yy = y[r]
    c = pd.factorize(celda[r])[0]
    sw = np.bincount(c, w)
    yd = yy - (np.bincount(c, w * yy) / sw)[c]
    td = t - (np.bincount(c, w * t) / sw)[c]
    sxx = (w * td * td).sum()
    if sxx <= 1e-12 * w.sum():
        return 0.0, 0.0
    b = (w * td * yd).sum() / sxx
    score = np.bincount(r, w * td * (yd - b * td))
    return float(b), float(np.sqrt((score**2).sum()) / sxx)

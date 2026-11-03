# Avance del 2026-11-02

Corte del trabajo hecho el 2 de noviembre de 2026: los 17 commits del día
en `main`, el estado en que queda el proyecto y lo que falta. El detalle
de cada cambio está en
[`CHANGELOG_PENDIENTES.md`](CHANGELOG_PENDIENTES.md) (entradas 2026-11-02
a (11)); el estado completo y vigente, en
[`RESUMEN_AVANCES.md`](RESUMEN_AVANCES.md).

## 1. Resumen del día

- **Se corrigieron tres errores que cambiaban resultados.**
  - Agosto de GEIH traía los códigos como `"1.0"` en vez de `"1"`.
  - En la propensión del DML, la celda y el departamento entraban como
    números en lugar de categorías.
  - En la reconstrucción monetaria, `P6430 = 7` se leía como "sin
    remuneración", pero es jornalero.
  
  Con el pipeline regenerado, **los efectos que se reportaban antes
  (+0,0235 en IPM-GEIH y +0,0158 en pobreza monetaria) desaparecen**. El
  DML da ≈0 en los cuatro outcomes.
- **Nuevo outcome: pobreza monetaria reconstruida.** Da 33,2 % de
  personas pobres frente al 31,8 % oficial. Comparada hogar por hogar con
  la base oficial del DANE, clasifica igual al 93,9 % de los hogares. La
  clasificación oficial queda como prueba de robustez.
- **Paredes y pisos homologados entre GEIH y Sisbén** con la ficha del
  Sisbén IV. **Pisos entra a la celda del Hot-Deck**, que pasa de 376 a
  993 celdas.
- **OE1 iniciado:** selección de variables con LASSO, Ridge y SHAP sobre
  el Sisbén. `viv_pisos` es la variable más importante en los tres
  métodos.
- **Simulaciones.**
  - **Simulación de identificación** (datos sintéticos): el diseño
    actual devuelve ≈0 sea cual sea el efecto verdadero. Solo una
    discontinuidad con el puntaje continuo lo recupera.
  - **Primera versión de la evaluación semisintética**, sobre hogares
    reales de GEIH: con Hot-Deck, cualquier estimador lleva el efecto a
    ≈0 (efecto verdadero: 0,095).
- **Comparación de proxies del IPM, Fases 1 y 2:** auditoría de
  variables y matriz de homologación de las 15 privaciones. La
  construcción de indicadores nuevos está en espera de revisión.

## 2. Commits del día, en orden

Todos están en `main`. El PR #9 y el PR #11 fueron fusionados.

| # | Commit | Autor | Qué hizo |
|---|---|---|---|
| 1 | `87a06ee` | Mateo Roncancio | Segunda especificación de `W` con la celda exacta del Hot-Deck; corrige el rótulo de ATT/ATU ("efecto en tratados/no tratados", no "error de inclusión/exclusión"). |
| 2 | `b9153ee` | Mateo Roncancio | Quita `warnings.filterwarnings("ignore")` de `5_estimacion.py` (no ocultaba nada). |
| 3 | `a5e7852` | (PR #11) | Simulación de identificación con datos sintéticos: qué diseño recupera el efecto de la elegibilidad. |
| 4 | `884303f` | Mateo Roncancio | OE1: selección de variables con LASSO, Ridge y SHAP sobre el Sisbén; declara `scipy` en `pyproject.toml`. |
| 5 | `465a660` | Juan Sebastián Fonseca | Regenera `poetry.lock` (faltaba `openpyxl`). |
| 6 | `e3508a8` | Juan Sebastián Fonseca | Comparación de proxies del IPM: inventario de variables GEIH, matriz de homologación GEIH ↔ Sisbén de las 15 privaciones y auditoría (PR #9). |
| 7 | `32191ec` | Juan Sebastián Fonseca | Actualiza el hash de `poetry.lock` tras declarar `scipy`. |
| 8 | `393c757` | Mateo Roncancio | Primer outcome de pobreza monetaria (ingreso per cápita, FGT0/FGT1) y boletín oficial del DANE como referencia. |
| 9 | `7657490` | Mateo Roncancio | Conecta la pobreza monetaria a `5_estimacion.py` (4 outcomes × 2 especificaciones de `W`). |
| 10 | `fdc8b35` | Mateo Roncancio | Cotas de Fréchet-Manski también para pobreza monetaria. |
| 11 | `9083a4e` | Mateo Roncancio | Auditoría de las 46 variables de ingreso de GEIH y metodología propuesta de pobreza monetaria (decisiones D1-D7). |
| 12 | `5f3d482` | Mateo Roncancio | Homologa paredes y pisos con la ficha del Sisbén IV; confirma que `geo_zona` vale 1 para urbano en las dos fuentes; documenta el bug de agosto. |
| 13 | `e47e40d` | Mateo Roncancio | Corrige el bug de agosto en el parser de `.DTA` y regenera el pipeline completo. |
| 14 | `40674d8` | Mateo Roncancio | Corrige los modelos auxiliares del DML (categóricas como indicadoras); pobreza monetaria definitiva con D1-D7; consolida la documentación. |
| 15 | `fc3a098` | Mateo Roncancio | Pisos entra a la celda del Hot-Deck; contraste hogar por hogar con la base oficial de pobreza monetaria (catálogo 874). |
| 16 | `527d263` | Mateo Roncancio | Pobreza monetaria oficial como prueba de robustez; evaluación semisintética. |
| 17 | `484422b` | Mateo Roncancio | Corrige el tiempo de ejecución reportado en la simulación semisintética. |

## 3. Estado al cierre del día

### Pipeline

| Etapa | Estado |
|---|---|
| Fuentes (GEIH 12 meses, IPM, Sisbén nacional y Bogotá) | ✅ Integradas. Se suman la base oficial de pobreza monetaria y la marca de víctimas MPMD (catálogo 874), esta última sin usar todavía. |
| Hot-Deck GEIH ← Sisbén | ✅ Celda: departamento + ciclo de vida + cuartos + pisos; 99,98 % en celda exacta. Grupos A/B/C/D: 14,2 / 29,4 / 34,4 / 22,0 %. |
| Outcome IPM-GEIH | ✅ 8 de 15 privaciones; `POBRE_GEIH` 17,1 %. |
| Outcome pobreza monetaria | ✅ Reconstruida: 33,2 % frente a 31,8 % oficial; la clasificación oficial queda como robustez. |
| DML / Causal Forest | ✅ Corregido. Es un **placebo**, no una estimación del efecto: el ATE ≈0 en los 4 outcomes (7 de 8 IC incluyen el 0). |
| Cotas de Fréchet-Manski | ✅ `POBRE_GEIH` [−0,261; +0,380]; `POBRE_MONETARIO` [−0,418; +0,648]. Ninguna celda excluye el 0. |
| OE1: selección de variables | ✅ Exactitud ≈53 % (línea base 30 %); el grupo D se confunde con C. |
| Evaluación semisintética | ✅ Primera versión. |
| Comparación de proxies del IPM | 🔧 Fases 1-2 hechas; Fases 3-5 en espera de revisión (ver §4b). |
| Pruebas | ✅ 35 pasan con `python -m pytest tests/` (ver §4c). |

### Lectura de conjunto

Con dos fuentes sin llave común, el Hot-Deck asigna el grupo Sisbén al
azar dentro de la celda. Por eso cualquier contraste dentro de la celda
da ≈0, sea cual sea el efecto verdadero. Lo muestran las dos
simulaciones y lo confirma la corrida con datos reales. Sin ese supuesto,
las cotas de Fréchet-Manski no fijan ni el signo del efecto. Lo único que
recuperó el efecto en la simulación es una discontinuidad con el puntaje
continuo del Sisbén, que el proyecto no tiene (no se ha solicitado).

### Ramas

- `main` y `ediciones-hotdeck-sdp` están en el mismo commit.
- `comparacion-proxies-ipm` y `simulacion-identificacion-v2` ya están
  fusionadas en `main`.
- Hay tres ramas remotas con un commit que no está en `main`:
  - `arregla-lock-openpyxl`: su arreglo del lock ya entró por otro
    commit (`465a660`).
  - `simulacion-identificacion`: la reemplazó la v2.
  - `corrige-controles-celda`: se bifurcó antes de la corrección del
    diccionario GEIH, así que no debe fusionarse tal cual.
  
  Las tres se pueden archivar o borrar.

## 4. Pendientes

### 4a. Proyecto (de `RESUMEN_AVANCES.md` §4)

1. **Evaluación semisintética, siguientes pasos:** outcome binario de
   pobreza; sensibilidad a gamma y a la fuerza del efecto; más
   repeticiones de Causal Forest; Hot-Deck con toda la cadena de
   respaldos; escenario con discontinuidad.
2. **Pobreza monetaria, Fase 5:** comparación con IPM-GEIH y con el
   grupo imputado, por celda (D6).
3. Angostar las cotas de Fréchet-Manski con supuestos de monotonía
   (MTS/MTR).
4. Construir las privaciones del IPM que faltan en GEIH y refinar
   `sin_cotizacion_pension_jefe`. Se conecta con §4b.
5. Confirmar en ANDA los cortes de `PER002`. Revisar en Bogotá los 6
   hogares con doble jefe y los 227 con `Clasificacion` distinta entre
   miembros.
6. Evaluar la marca de víctimas del DANE como covariable, en lugar del
   RUI.
7. Actualizar el anteproyecto con el enfoque vigente.
8. OE1: falta la concordancia con la pobreza, que con el Hot-Deck solo
   puede medirse por celda. OE3 (reglas de focalización) no ha
   empezado.

### 4b. Comparación de proxies del IPM — decisiones para la Fase 3

Detalle en
[`00_auditoria_variables.md`](../metodologia/comparacion_proxies/00_auditoria_variables.md)
§6 y en la
[matriz de homologación](../metodologia/comparacion_proxies/01_matriz_homologacion.md).
De las 15 privaciones, 12 son homologables, 1 es parcial (I6, trabajo
infantil, solo 15-17 años) y 2 no están disponibles en GEIH (I5, primera
infancia; I10, barreras de salud). Antes de construir `IPM_GEIH_15` e
`IPM_GEIH_ALT` hay que decidir:

1. Cómo repartir el peso de I5 e I10. La propuesta es repartirlo dentro
   de su dimensión.
2. Si I6 entra solo en el indicador alternativo.
3. Qué hacer con la tautología de I13/I14 con las covariables.
   - Revisar a la luz del 2026-11-02: `viv_pisos` salió de `X` y entró a
     `W`.
   - `viv_paredes` sigue en `X`.
4. Cómo convertir semestres de educación superior a años.
5. Cómo identificar a los pensionados.
6. Qué miembros cuentan en el hogar. `P6050` usa los códigos 1-13; la
   auditoría de pobreza monetaria ya resolvió que el 10 es servicio
   doméstico.
7. Agua rural: si "u otra fuente" incluye la pila pública.
8. Hacinamiento: si "cuarto" se toma como cuarto para dormir (`P5010`).
9. Conseguir el documento metodológico del Sisbén del DNP.

### 4c. Mantenimiento del repositorio

- `poetry run pytest tests/` (el comando de `CLAUDE.md`) falla al
  importar en 4 archivos nuevos: `test_hotdeck_celda`,
  `test_local_csv_parser`, `test_preprocesamiento_monetario` y
  `test_simulacion_semisintetica`. Importan `src.*`, y `pytest` no pone
  la raíz del repositorio en el path. Con `python -m pytest tests/`
  pasan las 35 pruebas. Arreglo sugerido: `pythonpath = ["."]` en
  `[tool.pytest.ini_options]` de `pyproject.toml`.
- Archivar o borrar las tres ramas remotas de §3 que no están en `main`.

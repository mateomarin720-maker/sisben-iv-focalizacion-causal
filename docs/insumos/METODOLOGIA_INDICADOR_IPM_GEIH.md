# Metodología del indicador IPM-GEIH

Documenta la construcción de `ipm_geih_score`/`POBRE_GEIH`
(`src/3_preprocesamiento.py`), la familia de umbrales para sensibilidad,
las validaciones obligatorias, y qué queda fuera y por qué.

**No es el IPM oficial.** Es un índice alternativo construido para esta
investigación sobre variables de GEIH, porque GEIH y la encuesta IPM del
DANE no comparten llave de hogar (no se pueden cruzar a nivel micro). Usa
10 de las 15 privaciones de la metodología Alkire-Foster, no las 15.

**Actualizado 2026-10-28.** Hasta esa fecha el índice tenía 4 privaciones
y una estaba mal calculada, porque el repositorio no tenía el diccionario
oficial de variables de GEIH. Se consiguió el diccionario
(`docs/insumos/DICCIONARIO_GEIH_2024.xlsx`) y con él: (a) se corrigió un
error real en `hacinamiento`, y (b) se amplió el índice de 4 a 10
privaciones. La versión anterior de este documento (con el intento
bloqueado de ampliación) queda abajo en "Historial", para quien quiera ver
qué llevó a conseguir el diccionario.

## 1. Las 10 privaciones — código oficial y verificación

Todos los códigos siguientes están confirmados contra
`docs/insumos/DICCIONARIO_GEIH_2024.xlsx` (columna `Pregunta`, que trae el
texto exacto de la pregunta y las categorías de respuesta).

| Privación | Dimensión | Código | Definición oficial | Umbral de privación |
|---|---|---|---|---|
| `analfabetismo` | Educación | `P6160` (jefe) | "¿Sabe leer y escribir? 1 Sí 2 No" | `P6160 == 2` |
| `bajo_logro_educativo_jefe` | Educación | `P3042` (jefe) | "¿Mayor nivel educativo alcanzado...? 1.Ninguno 2.Preescolar 3.Básica primaria 4.Básica secundaria ... 13.Doctorado" | `P3042 < 4` (no alcanzó secundaria) — umbral propio del proyecto, no necesariamente el corte exacto de años de educación por cohorte que usa oficialmente el DANE |
| `inasistencia_escolar_menores` | Niñez | `P6170` + `P6040`, TODOS los miembros | "¿Actualmente asiste...? 1 Sí 2 No" | Algún miembro de 6 a 16 años con `P6170 == 2` |
| `sin_aseguramiento_salud` | Salud | `P6090` (jefe) | "¿Afiliado/cotizante/beneficiario de EPS/ARS? 1 Sí 2 No 9 No sabe" | `P6090 == 2` |
| `sin_cotizacion_pension_jefe` | Trabajo | `P6920` (jefe, módulo `ocupados`) | "¿Cotizando a fondo de pensiones? 1 Sí 2 No 3 Ya pensionado" | `P6920 != 1` |
| `hacinamiento` | Vivienda | `P5010` (cuartos para dormir) + `P6008` (personas) | — | personas/cuarto > 3 |
| `material_pisos_inadecuado` | Vivienda | `P4020` | "a.Tierra/arena b.Cemento/gravilla c.Madera burda d.Baldosín/ladrillo/vinisol e.Mármol f.Madera pulida g.Alfombra" | código 1 (Tierra/arena) |
| `material_paredes_inadecuado` | Vivienda | `P4010` | "a.Ladrillo/bloque/prefabricado/piedra b.Madera pulida c.Adobe/tapia d.Bahareque e.Madera burda f.Guadua g.Caña/esterilla/vegetal h.Zinc/tela/cartón/desechos i.Sin paredes" | códigos 6-9 (f,g,h,i) |
| `sin_alcantarillado` | Vivienda | `P4030S3` | "¿Con cuáles servicios cuenta la vivienda? c.Alcantarillado 1 Sí 2 No" | `P4030S3 == 2` |
| `sin_acueducto` | Vivienda | `P4030S5` | "...e.Acueducto 1 Sí 2 No" | `P4030S5 == 2` |

Cobertura por dimensión: Educación (2), Niñez (1), Salud (1), Trabajo (1),
Vivienda (5) — **5 de las 5 dimensiones del IPM oficial**, con más de un
indicador en Educación y Vivienda (antes: 4 dimensiones de 5, 1
indicador cada una).

### El error que tenía `hacinamiento` antes de 2026-10-28

Usaba `P5020` como si fuera "cuartos para dormir". `P5020` en realidad es
"tipo de servicio sanitario" (categórico 1-6: inodoro+alcantarillado,
inodoro+pozo séptico, inodoro sin conexión, letrina, bajamar, no tiene).
Dividir personas del hogar entre ese código producía un número con forma
de tasa de hacinamiento, sin tener ese significado — el error no era
visible porque ambos rangos de valores (1-6) se parecen. Corregido
usando `P5010` (el código real de cuartos para dormir).

### Por qué `viv_cuartos` (la celda del Hot-Deck) también cambió

El mismo problema de código equivocado afectaba `viv_cuartos` en
`src/armonizacion/armonizar_geih_hogar_2024.py`: tomaba `P5010`
("cuartos para dormir") en vez de `P5000` ("cuántos cuartos en total
dispone el hogar, incluyendo sala-comedor" — el mismo concepto que
`VIV009` del Sisbén). La celda del Hot-Deck estaba matcheando por
"número de alcobas" sin saberlo, no por "tamaño total de la vivienda".
Corregido — ver `docs/seguimiento/CHANGELOG_PENDIENTES.md` (2026-10-28)
para el efecto que tuvo en la distribución de grupos asignados.

### `sin_cotizacion_pension_jefe` sigue mezclando causas distintas

Esto NO se resolvió con el diccionario porque no es un problema de código
mal identificado — es que GEIH no tiene una pregunta que separe
"informal" de "inactivo por elección". Un jefe puede no cotizar por ser
informal (privación real en sentido IPM) o por estar desempleado, ser ama
de casa, o ser adulto mayor sin pensión — casos distintos agrupados en un
solo indicador. Sigue documentado como limitación, sin resolver.

## 2. Qué sigue sin poder construirse

Las 5 privaciones restantes del IPM oficial (rezago escolar, barreras a
atención primera infancia, trabajo infantil, desempleo de larga duración,
barreras de acceso a salud) requerirían variables que o no están en GEIH
con el detalle necesario, o necesitan reglas de elegibilidad más
complejas (edades, historial laboral, tiempo de búsqueda de empleo) que
no se construyeron en este corte — ya no es un problema de diccionario
(se tiene desde 2026-10-28), es un problema de alcance/tiempo. Candidato
a una iteración futura.

## 3. Familia de indicadores implementada

- **`ipm_geih_score`**: conteo de privaciones (0-10), sin ponderar.
- **`POBRE_GEIH`**: binario, `score >= K_POBRE` (K=3, umbral adoptado).
- **`POBRE_GEIH_K1`...`POBRE_GEIH_K10`**: los otros nueve cortes posibles
  — análisis de sensibilidad al umbral, no alternativas en competencia.

## 4. Sensibilidad al umbral (hallazgo, no solo metodología)

| Corte | % hogares clasificados pobres |
|---|---|
| K≥1 | 79,8 % |
| K≥2 | 40,9 % |
| **K≥3 (adoptado)** | **17,2 %** |
| K≥4 | 7,4 % |
| K≥5 | 2,8 % |
| K≥6 | 0,9 % |
| K≥7 | 0,2 % |
| K≥8-10 | ~0,0 % |

K=3 fue adoptado por ser el más cercano, en orden de magnitud, a la tasa
oficial de pobreza por IPM (13,0 %, Hogares Nacional 2024,
`data/catalogo.yaml`) entre los 10 cortes posibles — **verificación de
plausibilidad ex post, no una calibración**.

## 5. Validaciones obligatorias — resultado

Implementadas en `_validar()` (`src/3_preprocesamiento.py`) y en
`tests/test_preprocesamiento.py` (`poetry run pytest tests/`):

- ✅ Una fila por hogar dentro de cada mes (GEIH es panel rotativo).
- ✅ 0 duplicados por llave de hogar + mes.
- ✅ 0 hogares del Hot-Deck sin outcome tras el cruce (290.968 de 290.968).
- ✅ 0 valores faltantes sin tratar en las 10 privaciones.
- ✅ Cobertura por variable: analfabetismo 4,7 %, bajo logro educativo
  29,9 %, inasistencia escolar (6-16 años) 2,1 %, sin aseguramiento de
  salud 3,4 %, sin cotización a pensión 75,4 %, hacinamiento 3,1 %, pisos
  inadecuados 3,5 %, paredes inadecuadas 0,9 %, sin alcantarillado
  18,1 %, sin acueducto 8,1 %. Todas plausibles frente a cifras
  nacionales conocidas.
- ✅ Distribución del score y umbrales monótonos verificados por prueba
  automatizada.

## 6. Historial — el bloqueo (resuelto 2026-10-28)

Antes de conseguir el diccionario oficial, se intentó ampliar el índice
auditando candidatos de GEIH 2024 por ensayo-error (value_counts +
comparación contra cifras nacionales conocidas), sin diccionario de
respaldo. Varios candidatos probados en ese momento (educación:
`P6170`, `P3038`, `P3039`, `P3041`-`P3043`; servicios de vivienda:
`P5070`, `P5080`, `P5090`, `P5100`, `P5110`, `P5130`, `P5140`) **no
correspondían a lo esperado** — ahora que se tiene el diccionario, se
confirma por qué: `P3038`/`P3039` son preguntas de orientación sexual e
identidad de género (no educación), y `P5100`/`P5110`/`P5130`/`P5140` son
preguntas de valor monetario de arriendo/compra (no acceso a servicios).
No se adivinaron esos códigos en su momento — se documentó el bloqueo y
se esperó a conseguir la ficha real, que es justamente lo que permitió la
ampliación de la sección 1.

## 7. Dónde está el código

- Construcción: `src/3_preprocesamiento.py` (`_outcome_mes`, `_validar`).
- Pruebas: `tests/test_preprocesamiento.py`.
- Diccionario oficial: `docs/insumos/DICCIONARIO_GEIH_2024.xlsx`.
- Reporte de sensibilidad: `docs/reports/reporte_sensibilidad_ipm_geih.csv`.
- Uso del outcome en la estimación causal:
  `docs/resultados/RESULTADOS_DML_ATE_ATT_ATU.md`,
  `RESULTADOS_CAUSALFOREST_CATE.md`, `RESULTADOS_FRECHET_MANSKI.md`.

# Metodología del indicador IPM-GEIH (reducido)

Documenta la construcción de `ipm_geih_score`/`POBRE_GEIH`
(`src/3_preprocesamiento.py`), la familia de variantes para sensibilidad,
las validaciones obligatorias y, explícitamente, qué no se pudo construir
todavía y por qué.

**No es el IPM oficial.** Es un índice alternativo construido para esta
investigación sobre variables de GEIH, porque GEIH y la encuesta IPM del
DANE no comparten llave de hogar (no se pueden cruzar a nivel micro). No
reproduce la metodología Alkire-Foster de 15 indicadores del DANE — usa 4.

## 1. Las 4 privaciones actuales — qué código, qué verificación

| Privación | Dimensión | Código GEIH | Cómo se verificó |
|---|---|---|---|
| `analfabetismo` | Educación | `P6160` (jefe) | Código **compartido** con el diccionario oficial de IPM (`docs/insumos/DICCIONARIO_DATOS.md`) — mismo código, misma pregunta en ambas encuestas del DANE. Tasa resultante (4,7%) es plausible para analfabetismo adulto en Colombia. |
| `sin_aseguramiento_salud` | Salud | `P6090` (jefe) | Código compartido con IPM. Tasa resultante (3,4%) calza con cobertura de aseguramiento en salud ~95-96%. |
| `hacinamiento` | Vivienda | `P5020` (cuartos para dormir) + conteo de personas por hogar | `P5020` tiene el mismo nombre de concepto que la variable de IPM Hogares con el mismo código (`P5010`/`P5020`, ver `data/catalogo.yaml`). El umbral (>3 personas/cuarto) **no está verificado** contra la metodología oficial del IPM — es una aproximación razonable, no una réplica exacta. |
| `sin_cotizacion_pension_jefe` | Trabajo | `P6920` (módulo `ocupados`) | Sin código compartido con IPM. Verificado indirectamente: 56,3% de los jefes ocupados no cotiza — calza con la tasa de informalidad laboral nacional reportada por DANE para 2024 (~55-58%), lo que da confianza razonable en la interpretación del código sin tener la ficha oficial. |

Cada una de las 4 privaciones cae en una dimensión distinta del esquema
Alkire-Foster (Educación / Salud / Vivienda / Trabajo) — con exactamente
un indicador por dimensión, ponderar por indicador o por dimensión da el
mismo resultado (no hay margen de sensibilidad de peso con 4 indicadores
de 4 dimensiones distintas; si se amplía el índice con más indicadores
por dimensión, ahí sí habrá que decidir y justificar pesos).

## 2. Familia de indicadores implementada

- **`ipm_geih_score`**: conteo de privaciones (0-4), sin ponderar.
- **`POBRE_GEIH`**: binario, `score >= K_POBRE` (K=2, umbral adoptado).
- **`POBRE_GEIH_K1`...`POBRE_GEIH_K4`**: la misma variable con los otros
  tres cortes posibles — análisis de sensibilidad al umbral, no
  alternativas en competencia.

## 3. Sensibilidad al umbral (hallazgo, no solo metodología)

| Corte | % hogares clasificados pobres |
|---|---|
| K≥1 | 81,9 % |
| **K≥2 (adoptado)** | **23,5 %** |
| K≥3 | 1,5 % |
| K≥4 | 0,0 % |

La tasa de pobreza cambia **drásticamente** según el corte — de 82% a
0,02% entre los extremos. Esto no es un defecto del índice: con solo 4
indicadores binarios, cada privación individual pesa 25% del score, así
que el corte es una decisión con consecuencias grandes, no un detalle
técnico. K=2 fue el adoptado porque es el más cercano, en orden de
magnitud, a la tasa oficial de pobreza por IPM (13,0%, Hogares Nacional
2024, `data/catalogo.yaml`) entre los 4 cortes posibles — **esto es una
verificación de plausibilidad ex post, no una calibración**: no se ajustó
el umbral para forzar ese parecido, se reportan los 4 y se eligió el más
razonable.

## 4. Validaciones obligatorias — resultado

Implementadas en `_validar()` (`src/3_preprocesamiento.py`) y en
`tests/test_preprocesamiento.py` (`poetry run pytest tests/`):

- ✅ Una fila por hogar **dentro de cada mes** (GEIH es panel rotativo —
  no sigue al mismo hogar entre meses, así que "una fila por hogar" se
  valida por mes, no por año).
- ✅ 0 duplicados por llave de hogar + mes.
- ✅ 0 hogares del Hot-Deck sin outcome tras el cruce (290.968 de 290.968).
- ✅ 0 valores faltantes sin tratar en las 4 privaciones (verificado
  explícitamente — ver nota sobre `sin_cotizacion_pension_jefe` abajo).
- ✅ Cobertura por variable reportada (tabla arriba).
- ✅ Distribución del score reportada y umbrales monótonos verificados
  por prueba automatizada (`test_umbrales_k_son_monotonos`).

**Tratamiento explícito de faltantes:** un jefe que no aparece en el
módulo `ocupados` (no ocupado) queda marcado como privado (1) en
`sin_cotizacion_pension_jefe`, no como faltante — es una decisión de
diseño (combina informalidad con desempleo/inactividad en un solo
indicador), no un accidente del cruce. Verificado con prueba automatizada.

## 5. Bloqueo: el indicador AMPLIADO no se pudo construir todavía

Se intentó incorporar, como pide la fase de ampliación: alfabetismo
(ya está), asistencia escolar, logro educativo, material de paredes y
pisos (ya están como confusores, no como privación — ver más abajo),
hacinamiento (ya está), acceso a agua, servicio sanitario, eliminación de
basuras, combustible de cocina, y otros indicadores laborales.

**Resultado de la auditoría de variables candidatas en los archivos
reales de GEIH 2024 (enero, `caracteristicas_generales` y
`hogar_vivienda`):**

| Candidato | Código probado | Qué se encontró |
|---|---|---|
| Asistencia escolar / logro educativo | `P6170`, `P3038`, `P3039`, `P3041`-`P3043` | Distribuciones de valores que no calzan claramente con los conceptos esperados (p. ej. `P3042` tiene 10 categorías con valores como "5", "3", "4", "10", "8" sin patrón reconocible de nivel educativo). |
| Acueducto / alcantarillado / basuras / combustible | `P5070`, `P5080`, `P5090`, `P5100`, `P5110`, `P5130`, `P5140` | **No son indicadores binarios de acceso a servicio.** Varios traen valores monetarios grandes (ej. `P5100`/`P5130`/`P5140` con cifras tipo 500.000, 1.000.000 — parecen pagos de arriendo/administración/servicios) y uno (`P5090S1`) es texto libre ("FAMILIAR", "VIVIENDA FAMILIAR") — sugiere preguntas de tenencia/costo de la vivienda, no de acceso a servicios públicos. |

**Causa raíz:** este repositorio no tiene el diccionario oficial de
variables de GEIH (a diferencia de IPM, que sí trae su DDI completo en
`docs/insumos/DICCIONARIO_IPM_2025.md`). Sin esa ficha, no hay forma
confiable de verificar qué pregunta corresponde a cada código `P####` de
GEIH más allá de los pocos ya corroborados por otras vías (código
compartido con IPM, o tasa resultante comparada contra una cifra nacional
conocida).

**No se adivinaron estos códigos.** Construir privaciones con la
dirección o el universo equivocado sería peor que no construirlas —
cambiaría la definición de "pobreza" de la investigación sin que nadie lo
supiera.

### Alternativas (requieren una decisión, no son rutinarias)

1. **Conseguir la ficha técnica / diccionario de variables oficial de
   GEIH** (DANE, portal de microdatos — sección "Documentos" de la
   encuesta) y repetir esta auditoría con la ficha en mano. Es la opción
   que permite ampliar el índice con la misma rigurosidad que las 4
   privaciones actuales.
2. **Usar las categóricas de vivienda (`viv_paredes`/`viv_pisos`) ya
   presentes como confusores** (no como privación) hasta que se resuelva
   su homologación entre fuentes — ya es lo que hace
   `src/5_estimacion.py` hoy.
3. **Dejar el índice en 4 privaciones como alcance definido de esta etapa
   de la tesis**, documentando la limitación explícitamente en la
   redacción final (ya lo lleva este documento), en vez de forzar una
   ampliación sin verificación.

Mientras no se resuelva (1), este documento recomienda **(3)**: seguir
con las 4 privaciones verificadas, y usar la familia de umbrales (§2-3)
como el eje de sensibilidad disponible en esta etapa — no se amplían las
dimensiones del índice con variables sin verificar.

## 6. Dónde está el código

- Construcción: `src/3_preprocesamiento.py` (`_outcome_mes`, `_validar`).
- Pruebas: `tests/test_preprocesamiento.py`.
- Reporte de sensibilidad: `docs/reports/reporte_sensibilidad_ipm_geih.csv`.
- Uso del outcome en la estimación causal:
  `docs/resultados/RESULTADOS_DML_ATE_ATT_ATU.md`,
  `RESULTADOS_CAUSALFOREST_CATE.md`, `RESULTADOS_FRECHET_MANSKI.md`.

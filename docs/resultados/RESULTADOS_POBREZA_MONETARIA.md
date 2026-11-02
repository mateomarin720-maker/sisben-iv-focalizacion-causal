# Resultados — Pobreza monetaria (ingreso per cápita, FGT0/FGT1)

Generado 2026-11-02 por `src/3b_preprocesamiento_monetario.py`. Salida:
`data/2_models/muestra_estimacion_monetaria_2024.parquet`,
`docs/reports/validacion_fgt_pobreza_monetaria.csv`.

> **Aviso (2026-11-02):** la auditoría de
> `docs/metodologia/pobreza_monetaria/00_auditoria_y_metodologia.md`
> encontró que `INGLABO` **no** está imputado por el DANE y que el "47,7 %
> de no respuesta en `P6500`" eran independientes, a quienes no se les hace
> esa pregunta (§8 de la auditoría). También lista siete diferencias
> metodológicas de este outcome (unidad de gasto, tasas por hogar, líneas,
> ingresos ocasionales, componentes omitidos, no respuesta, vivienda
> propia; §7). Este documento se reescribirá con la nueva construcción.

## Qué es

El nuevo outcome principal según el giro propuesto por el tutor el
2026-10-27 (ver `docs/seguimiento/CHANGELOG_PENDIENTES.md`): en vez de
(o además de) el IPM-GEIH de `3_preprocesamiento.py`, el resultado pasa a
ser la **pobreza monetaria** — ingreso per cápita del hogar comparado
contra la línea de pobreza oficial del DANE, con los indicadores FGT
(Foster, Greer y Thorbecke, 1984): FGT0 (incidencia, % de pobres), FGT1
(brecha, qué tan lejos están los pobres de la línea).

## Fuente oficial de las líneas de pobreza

`docs/insumos/DANE_boletin_PM_2024.pdf` (DANE, *Pobreza Monetaria en
Colombia, año 2024*, boletín técnico oficial, Tablas 1 y 4), pesos
corrientes mensuales por persona:

| Dominio | Línea de pobreza | Línea de pobreza extrema |
|---|---|---|
| Total nacional | $460.198 | $227.220 |
| Cabeceras (urbano) | $510.161 | $242.389 |
| Centros poblados y rural disperso (rural) | $291.998 | $176.154 |

Incidencia y brecha oficiales 2024 (para validar por plausibilidad, el
mismo criterio que la tasa de IPM oficial en `3_preprocesamiento.py`):

| | Nacional | Cabeceras | Centros poblados y rural disperso |
|---|---|---|---|
| FGT0 pobreza | 31,8 % | 28,6 % | 42,5 % |
| FGT1 pobreza | 12,6 % | — | — |
| FGT0 pobreza extrema | 11,7 % | 8,7 % | 21,8 % |
| FGT1 pobreza extrema | 4,5 % | — | — |

## Cómo se construyó

**Ingreso laboral:** `INGLABO` del módulo `ocupados` — la variable de
ingreso laboral que el DANE ya construye e imputa internamente, no una
reconstrucción manual desde `P6500`. Ver "Qué salió mal primero" abajo:
el primer intento sí reconstruyó manualmente desde `P6500` y falló.

**Ingreso no laboral** (módulo `otros_ingresos`, todos los miembros del
hogar): arriendos, pensiones/jubilaciones, pensión alimenticia
(mensuales, directo); dinero de otros hogares, ayudas institucionales,
intereses/dividendos, cesantías, otras fuentes (preguntados sobre los
últimos 12 meses, divididos entre 12 para un equivalente mensual).

**Ingreso ocasional de no ocupados** (módulo `no_ocupados`, `P7422`):
personas no clasificadas como ocupadas que igual ganaron algo el mes
pasado.

**Agregación:** suma de las tres fuentes por TODOS los miembros del
hogar → `ingreso_hogar_mensual`; dividido entre `hog_num_personas` →
`ingreso_percapita`. Comparado contra la línea del dominio
(`geo_zona`: 1=urbano/2=rural) → `POBRE_MONETARIO`/
`POBRE_EXTREMO_MONETARIO`. Brecha por hogar:
`max(0, (línea - ingreso_percapita) / línea)` → agregada ponderando por
`fex` da el FGT1 poblacional.

## Qué SÍ y qué NO replica de la metodología oficial del DANE

El DANE construye el "ingreso per cápita de la unidad de gasto" en 5
pasos (nota 2 del boletín): (1) agregar ingresos por fuente, (2) un
**modelo de imputación** para corregir subreporte, (3) consolidar a
nivel de Población en Edad de Trabajar, (4) agregar a nivel de "unidad
de gasto" (el hogar SIN pensionistas ni empleados domésticos internos),
(5) un **ajuste por propiedad de la vivienda** (arriendo imputado a
propietarios).

Este script hace el paso (1) completo y una versión parcial del (2) — al
usar `INGLABO` (ya imputado por el DANE) en vez de `P6500` crudo, hereda
la imputación oficial del ingreso LABORAL, pero no imputa subreporte en
el ingreso NO laboral (arriendos, pensiones, etc., que no tienen una
variable equivalente ya imputada). Tampoco hace (3), no distingue
"unidad de gasto" de "hogar" (4), y no hace el ajuste (5). Por diseño,
esto **subestima el ingreso real y sobreestima la pobreza** frente a la
cifra oficial — el patrón observado en el resultado (todas las FGT
construidas por encima de las oficiales) es consistente con esa
dirección esperada, no con un error aleatorio.

## Qué salió mal primero (y cómo se encontró)

El primer intento reconstruyó el ingreso laboral sumando `P6500` +
horas extra/primas/bonificaciones (si no estaban ya incluidas, según la
sub-pregunta de cada una) + subsidios + pago en especie — exactamente lo
que sugieren las preguntas del cuestionario, sin usar ninguna variable
derivada. Resultado: FGT0=53,6 %, FGT1=39,0 % — muy por encima de lo
esperable para una aproximación sin imputación (no un margen de 5-10
puntos, sino casi el doble en FGT0 y más de 3 veces en FGT1).

**Causa:** `P6500` por sí solo tiene **47,7 % de no respuesta** entre
las personas ocupadas (13.751 de 28.815 en enero) — casi la mitad de los
ocupados no reportan un valor numérico a esa pregunta. El script
original trataba esos vacíos como ingreso $0 en vez de "no informa", lo
que inflaba el conteo de hogares con ingreso 0 (21,4 % de los hogares,
implausible) y sobre todo inflaba FGT1 (un hogar con ingreso real alto
pero `P6500` vacío contribuía una brecha de pobreza del 100 % en vez de
0 %).

**Corrección:** el módulo `ocupados` trae `INGLABO` ("Ingresos
Laborales"), la variable que el DANE ya construye e imputa (reduce la no
respuesta de 47,7 % a 4,3 %) — es precisamente el paso (2) de la
metodología oficial. Usarla en vez de reconstruir manualmente bajó el
porcentaje de hogares con ingreso $0 de 21,4 % a 4,1 %, y las cuatro FGT
pasaron de estar 1,5-3 veces por encima de lo oficial a estar en un
rango de sobreestimación mucho más consistente con lo que predice la
teoría (ver tabla abajo).

## Resultado

Ingreso per cápita mensual: media $1.045.313, mediana $621.586.

| Indicador | Construido | Oficial DANE 2024 | Diferencia |
|---|---|---|---|
| FGT0 pobreza monetaria | 38,7 % | 31,8 % | +6,9 pp |
| FGT1 brecha pobreza monetaria | 19,5 % | 12,6 % | +6,9 pp |
| FGT0 pobreza extrema | 18,8 % | 11,7 % | +7,1 pp |
| FGT1 brecha pobreza extrema | 10,7 % | 4,5 % | +6,2 pp |

Por zona:

| Dominio | FGT0 construido | FGT0 oficial | FGT1 construido |
|---|---|---|---|
| Cabeceras (urbano) | 36,6 % | 28,6 % | 18,2 % |
| Centros poblados y rural disperso | 46,4 % | 42,5 % | 24,1 % |

## Cómo leerlo

- **La sobreestimación es sistemática y de magnitud razonable** (todas
  las FGT construidas quedan 6-7 puntos porcentuales por encima de la
  oficial, no un orden de magnitud distinto) — consistente con lo
  esperado de no replicar los pasos (2)-(5) de la metodología del DANE,
  no con un error de construcción. Es la misma lógica de validación por
  plausibilidad que se usó para el umbral `K_POBRE` del IPM-GEIH: no se
  espera coincidencia exacta, se espera un orden de magnitud razonable.
- **El patrón urbano/rural se mantiene en la dirección correcta**
  (rural más pobre que urbano en ambas versiones), aunque la brecha
  construida entre zonas (9,8 pp) es más chica que la oficial (13,9 pp)
  — posible señal de que la imputación faltante afecta de forma
  distinta a cada dominio, sin investigar más por ahora.
- **FGT1 sobreestima proporcionalmente más que FGT0** en pobreza extrema
  (+6,2 pp sobre una base de 4,5 %, más del doble) que en pobreza
  moderada (+6,9 pp sobre 12,6 %, poco más de la mitad) — consistente
  con que los hogares peor medidos (sin imputación de subreporte) caen
  desproporcionadamente en la cola más pobre de la distribución.

## Limitaciones

- No replica los pasos (2)-(5) completos de la metodología oficial del
  DANE (imputación de subreporte no laboral, "unidad de gasto" exacta,
  ajuste por vivienda propia) — ver "Qué SÍ y qué NO replica" arriba.
- Dominio geográfico más grueso que el oficial: solo urbano/rural
  (`geo_zona`), no los 5 dominios del boletín (13 ciudades y A.M., otras
  cabeceras, etc.) — usa las líneas de cabeceras/resto, que agregan esos
  sub-dominios.
- `INGLABO` no está documentado en detalle en
  `docs/insumos/DICCIONARIO_GEIH_2024.xlsx` (solo "Ingresos Laborales");
  se asume que ya incluye horas extra/primas/bonificaciones/subsidios/
  pago en especie por su cobertura y orden de magnitud, no por
  confirmación textual de su fórmula exacta.
- Sin ajuste por diseño muestral complejo más allá de ponderar por `fex`
  en la validación (el outcome en sí, a nivel de hogar, no se pondera).
- GEIH es panel rotativo — una fila por hogar DENTRO de cada mes, no un
  hogar único en el año (mismo criterio que `3_preprocesamiento.py`).

## Estimación causal (DML/Causal Forest) — 2026-11-02

Conectado a `src/5_estimacion.py` como tercer y cuarto outcome
(`log_ingreso_percapita` = `log1p(ingreso_percapita)`, y
`POBRE_MONETARIO`), con las mismas dos especificaciones de `W` (proxy
continuo vs. celda exacta del Hot-Deck) que ya se habían usado para
`ipm_geih_score`/`POBRE_GEIH`. Resultado completo y comparación lado a
lado con los outcomes IPM-GEIH:
`docs/resultados/DIAGNOSTICO_W_CELDA_EXACTA.md`.

Resumen:

| Outcome | W = PROXY | W = CELDA EXACTA |
|---|---|---|
| `log_ingreso_percapita` (ATE) | -0,0317 [-0,0539;-0,0096] | -0,0468 [-0,0689;-0,0246] |
| `POBRE_MONETARIO` (ATE) | +0,0136 [+0,0101;+0,0171] | +0,0152 [+0,0118;+0,0187] |

Hallazgo principal: a diferencia de `ipm_geih_score` (cuyo efecto se
encogió 63 % al pasar al `W` con la celda exacta, señal de que el proxy
continuo lo inflaba), los dos outcomes monetarios **no se encogen — se
amplían** (+48 % y +12 % en magnitud respectivamente) y el signo es
estable (Grupo A/B del Sisbén se asocia con menor ingreso y mayor
probabilidad de pobreza monetaria en ambas especificaciones). Bajo la
simulación de sorteo aleatorio limpio (`simulacion_identificacion.py`),
el resultado esperado es ≈0 sin importar el efecto verdadero — que estos
dos outcomes se alejen de 0 en vez de acercarse es la evidencia más
fuerte producida hasta ahora en el proyecto de que el efecto no es un
artefacto del proxy continuo de `W`.

Esto no confirma causalidad por sí solo (siguen pendientes
`viv_paredes`/`viv_pisos` sin homologar con Sisbén y confusores no
observados DPS/RUI), pero es la evidencia de robustez más fuerte entre
los cuatro outcomes probados hasta ahora.

## Próximos pasos

- ~~Conectar este outcome a `src/5_estimacion.py`~~ — hecho 2026-11-02,
  ver arriba.
- ~~Repetir el diagnóstico `W` proxy vs. celda exacta~~ — hecho
  2026-11-02, ver arriba y `DIAGNOSTICO_W_CELDA_EXACTA.md`.
- ~~Correr `cotas_frechet_manski.py` sobre `POBRE_MONETARIO`~~ — hecho
  2026-11-02: cota [-0,5886; +0,7035], contiene el 0 y el ATE del DML.
  Sin la CIA del Hot-Deck, los datos no descartan un efecto de ningún
  signo. Ver `RESULTADOS_FRECHET_MANSKI.md`.

## Cómo reproducirlo

```bash
poetry run python src/3_preprocesamiento.py
poetry run python src/3b_preprocesamiento_monetario.py
poetry run python src/5_estimacion.py
poetry run pytest tests/
```

# Diccionario consolidado — Variables para Hot-Deck (GEIH ↔ Sisbén IV)

*(Actualizado 2026-11-14: celda con pisos desde el 2026-11-02 y cadena de
respaldos desde el 2026-11-04. Toda variable codificada queda con su nombre
y significado aquí, no solo en comentarios de código — observación del
tutor.)*

## 1. Variable de tratamiento

| Variable Sisbén | Etiqueta |
|---|---|
| `Grupo` | Grupo (A/B/C/D) |
| `Nivel` | Nivel dentro del grupo |
| `Clasificacion` | Grupo + Nivel concatenado (ej. "B3") |

## 2. Filtro de jefe de hogar

| Fuente | Variable | Valor filtro | Verificado |
|---|---|---|---|
| GEIH (`caracteristicas_generales`) | `P6050` | `"1"` = jefe de hogar | ✅ 24.402 jefes en agosto = 24.402 hogares (100 %) |
| Sisbén nacional (`personas`) | `PER003` | `"1"` = jefe de hogar | ✅ 1.820.083 de 1.833.166 hogares (99,3 %); 65 con doble jefe (se conserva el primero); 13.083 hogares sin jefe |
| Sisbén Bogotá (SDP) | `tip_parentesco` | `1` = jefe del hogar | ✅ 1.458.474 jefes; 6 hogares con doble jefe |

## 3. Llave de hogar en cada fuente

| Fuente | Llave | Nota |
|---|---|---|
| Sisbén IV nacional | `cod_mpio + ZONA + llave + CORTE + HOGAR` | `llave` es un consecutivo local, **no** identifica al hogar por sí sola. El parquet armonizado crea `llave_hogar_sisben` (única, verificada). Personas trae varias filas por hogar (los miembros); el armonizador conserva solo al jefe. |
| Sisbén Bogotá (SDP) | `ide_ficha_origen + ide_hogar` | `ide_ficha_origen` es la **vivienda**; hay 59.352 viviendas con más de un hogar. Una fila por persona (`ide_persona`). |
| GEIH | `DIRECTORIO + SECUENCIA_P + HOGAR` | Se normalizan a texto de entero antes de cruzar módulos (agosto traía otro formato). |
| IPM | `DIRECTORIO + SECUENCIA_ENCUESTA + SECUENCIA_P` | |

## 4. Esquema canónico (usado en el Hot-Deck)

**Actualizado 2026-10-28** con el diccionario oficial de GEIH
(`docs/insumos/DICCIONARIO_GEIH_2024.xlsx`) y el de Sisbén
(`docs/insumos/DICCIONARIO_SISBEN_2024.xlsx`). Antes de esta fecha,
`viv_paredes`/`viv_pisos`/`viv_cuartos` del lado GEIH usaban códigos
equivocados (ver `docs/metodologia/METODOLOGIA_INDICADOR_IPM_GEIH.md` para el
detalle del error y su efecto en el Hot-Deck).

| Nombre canónico | GEIH | Sisbén nacional | Sisbén Bogotá (SDP) | Estado |
|---|---|---|---|---|
| `geo_depto` | `DPTO` | `cod_mpio[:2]` | `"11"` | ✅ 33 códigos DIVIPOLA idénticos |
| `geo_localidad` | — | — | `Cod_comuna` (localidad, 20 códigos) | Solo descriptiva; GEIH no la desagrega |
| `geo_zona` | `CLASE` — **1=Urbano, 2=Rural** (confirmado) | `ZONA` (1/2) | `Cod_clase` (1 cabecera, 2 centro poblado, 3 rural disperso) | ✅ 1 = urbano en las dos fuentes: GEIH por el diccionario; Sisbén inferido de `I14` (2026-11-02, `HOMOLOGACION_VIVIENDA_GEIH_SISBEN.md`). No entra a la celda |
| `jefe_edad` | `P6040` (**años**, confirmado: "¿cuántos años cumplidos tiene?") | `PER002` (**código de ciclo de vida**) | `fec_nacimiento` → ciclo | ⚠️ Ver sección 5 |
| `jefe_sexo` | `P3271` — confirmada la pregunta ("¿cuál fue su sexo al nacer?"), el diccionario no trae la tabla 1/2 explícita | `PER001` | `sexo_persona` (valor `4` inválido → nulo) | ⚠️ Pregunta confirmada, dirección del código 1/2 sigue sin confirmar |
| `viv_paredes` | **`P4010`** (corregido, antes `P4020`) | `VIV002` | `tip_mat_paredes` | ✅ Homologado el 2026-11-02 con la ficha del Sisbén IV y verificado contra `I13` (`HOMOLOGACION_VIVIENDA_GEIH_SISBEN.md`). Evaluado para la celda y descartado (sección 6) |
| `viv_pisos` | **`P4020`** (corregido, antes `P4030S1`) | `VIV003` | `tip_mat_pisos` | ✅ Homologado el 2026-11-02 (ficha del Sisbén IV, verificado contra `I14`). **En la celda** por nivel: acabado, cemento o madera burda, tierra. Los códigos crudos van al revés entre fuentes (tierra = 1 en GEIH, 5 en Sisbén) |
| `viv_cuartos` | **`P5000`** (corregido, antes `P5010`) — "cuartos en total, incl. sala-comedor" | `VIV009` — "número de cuartos, incl. sala-comedor" | `num_cuartos_vivienda` | ✅ Mismo concepto confirmado en las dos fuentes (antes GEIH medía sin saberlo "cuartos para dormir", un concepto distinto) |
| `viv_cuartos_dormir` | `P5010` (nuevo, separado de `viv_cuartos`) | — | — | Insumo de `hacinamiento` en `3_preprocesamiento.py`, no entra a la celda del Hot-Deck |
| `viv_alcantarillado` | `P4030S3` (nuevo, ya ubicado) | `VIV005` | `ind_tiene_alcantarillado` | ✅ Homologado en GEIH desde 2026-10-28 |
| `viv_acueducto` | `P4030S5` (nuevo, ya ubicado) | `VIV008` | `ind_tiene_acueducto` | ✅ Homologado en GEIH desde 2026-10-28 |
| `hog_num_personas` | `P6008` (nuevo, ya ubicado — "total de personas en el hogar") | `HOG027` | conteo de personas por hogar | ✅ Homologado en GEIH desde 2026-10-28 |
| `fex` | `FEX_C18` | `FEX` | — (fijo en 1: no hay factor de expansión) | Ponderación, no entra a la celda |

`viv_paredes` y `viv_pisos` se comparan entre fuentes solo a través de la
escala común de `HOMOLOGACION_VIVIENDA_GEIH_SISBEN.md`, nunca por el código
crudo. `viv_cuartos` (conteo cardinal) no necesita homologar categorías.
Bogotá (SDP) es coherente con la ficha pero no se pudo verificar con
privaciones.

## 5. Edad del jefe: ciclo de vida (✅ hipótesis corroborada indirectamente, 2026-10-10)

El extracto del Sisbén **no trae la edad en años**. Entre jefes de hogar (`PER003=="1"`, archivo completo de Personas, 1.820.148 jefes) `PER002` toma **solo** los valores 3, 4, 5 y 6 — 0 jefes con los códigos 1 o 2 (ver abajo). Para comparar con GEIH se usa el mismo ciclo en ambas fuentes:

| Código `PER002` | Ciclo (hipótesis) | Jefes de hogar Sisbén nacional |
|---|---|---|
| 3 | 12–17 años | 4.105 (0,2 %) |
| 4 | 18–28 años | 323.701 (17,8 %) |
| 5 | 29–59 años | 1.077.158 (59,2 %) |
| 6 | 60 años o más | 415.184 (22,8 %) |

**Estado: corroborado indirectamente, no con la ficha oficial.** Sigue sin confirmarse en la ficha ANDA (variable `PER002`, V926), pero se cruzó `PER002` contra variables de comportamiento conocidas en la base completa de Personas (4.715.226 filas, todas las edades, no solo jefes) y las proporciones son consistentes con la hipótesis del ciclo de vida:

| `PER002` | % estudia (`PER016`) | % soltero (`PER004`) | % cotiza pensión (`PER018`) | Lectura |
|---|---|---|---|---|
| 1 | — (86 % N/A) | 100 % | — (100 % N/A) | Primera infancia (no responde estas preguntas) |
| 2 | 95,8 % | 100 % | — (100 % N/A) | Niñez — casi todos estudian, nadie casado |
| **3** | 86,6 % | 98,9 % | 25,5 % N/A / 74,1 % no cotiza | Coherente con 12–17: aún estudia, soltero |
| **4** | 22,4 % | 74,7 % | 89,9 % no cotiza | Coherente con 18–28: deja de estudiar, mayoría soltero |
| **5** | 2,5 % | 42,7 % casado | 85,0 % no cotiza | Coherente con 29–59: estado civil mixto, edad laboral |
| **6** | 0,8 % | 49,7 % casado | 90,4 % no cotiza | Coherente con 60+: casi nadie estudia |

Los códigos 1 y 2 (infancia/niñez, nunca jefes de hogar) confirman además que el ciclo de vida completo tiene 6 categorías, no 4 — el hot-deck solo necesita 3–6 porque un jefe de hogar nunca cae en 1/2. Detalle de la verificación: `src/validacion/verificar_codigos_edad_sisben.py`. En Bogotá y en GEIH la edad se convierte con los cortes 17/28/59.

## 6. Celda de matching actual (desde el 2026-11-14)

| Componente | Valores | Desde |
|---|---|---|
| `geo_depto` | 33 códigos DIVIPOLA | 2026-09-17 |
| Ciclo de vida del jefe | 12-17, 18-28, 29-59, 60+ (sección 5; tramos en `src/utils/variables_canonicas.py`) | 2026-10-09 |
| Tramo de `viv_cuartos` | 1, 2, 3 o más | 2026-10-21 (código corregido el 2026-10-28) |
| Nivel de `viv_pisos` | acabado, cemento o madera burda, tierra | 2026-11-02 |
| Tramo de `hog_num_personas` | 1-2, 3 o más | 2026-11-14 |
| Tramo de `hog_num_menores` | 0, 1, 2 o más menores de 18 años | 2026-11-14 |

Las seis entran como coincidencia exacta: ninguna pesa más que otra. Lo
único que las ordena es la cadena de respaldos, que suelta primero la que
menos aporta. Personas y menores son conteos homologados sin tabla de
equivalencias: GEIH `P6008` y personas con `P6040` < 18; Sisbén nacional
`HOG027` y personas con `PER002` en los ciclos 1 a 3; Bogotá, filas por
hogar y `fec_nacimiento` (`src/utils/variables_canonicas.py`, `es_menor`).
Su distribución coincide entre fuentes (sin menores: 56 % GEIH ponderada,
54 % Sisbén nacional, 61 % Bogotá).

Por qué estas y no otras (`RESULTADOS_HOTDECK.md`,
`src/validacion/comparar_celdas_hotdeck_vivienda.py`,
`src/validacion/candidatas_celda_catalogo.py`): pisos subió la
correlación de P(T | celda) con la pobreza monetaria de 0,20 a 0,29
(paredes triplicaba las celdas sin mejorarla); personas y menores la
suben a 0,41 y cierran el ancho de la cota de Fréchet por celda de 0,200 a
0,148, con 99,9 % de los hogares en celda exacta y 3,7 % en celdas con
menos de 30 donantes (umbrales: 99,5 % y 5 %; personas en tres tramos,
1-2, 3-4 y 5 o más, cierra igual pero deja 5,1 % en celdas pequeñas).
Personas y menores son condición de algunas privaciones (hacinamiento,
inasistencia escolar), no la privación misma.

### 6.1 Variables descartadas y motivo

Se revisaron todas las variables de vivienda y hogar de los tres
catálogos (diccionario de la GEIH 2024, ficha del Sisbén IV y la entrega
del SDP). Cada una pasó por cuatro filtros, en este orden: (1) ¿existe en
las tres fuentes?; (2) ¿es una privación del IPM?; (3) ¿homologa, es decir,
su distribución cuadra entre fuentes después de llevar los códigos a
categorías comunes?; (4) ¿aporta sobre la celda sin fragmentarla? Δ es el
ancho medio de la cota de Fréchet por celda (menor es mejor); la
referencia es la celda con personas, Δ = 0,167, 2,9 % de hogares en
celdas con menos de 30 donantes.

| Variable | Filtro donde cae | Motivo |
|---|---|---|
| Zona (urbano / resto) | 4. No aporta | Homologa (ficha: 1 cabecera, 2-3 resto), pero sobre la celda final Δ apenas baja (0,148 → 0,144), casi lo mismo que al permutarla dentro de la celda (placebo 0,146), y las celdas pequeñas suben de 3,7 % a 5,3 %. La celda ya la captura con departamento y pisos. Sí se usa para leer resultados (cotas y heterogeneidad por zona) |
| Paredes | 4. No aporta | Homologa (escala común con `I14`), Δ 0,165 y 4,2 % de celdas pequeñas; desde el 2026-11-02 triplicaba las celdas sin subir la correlación |
| Sexo del jefe | 4. No aporta | Homologa (2 = mujer en las dos fuentes), Δ 0,161 pero 6,5 % de celdas pequeñas, sobre el umbral |
| Mayores de 60 en el hogar | 4. No aporta | Homologa (33 % GEIH, 27 % Sisbén nacional, 31 % Bogotá); Δ 0,166 |
| Cónyuge en el hogar | 4. No aporta | Δ 0,162 con 5,6 % de celdas pequeñas; además la presencia difiere entre fuentes (50 % frente a 35 %) |
| Energía, gas, recolección de basuras, combustible de cocina | 4. No aporta | Homologan (sí/no o limpia/otra); Δ 0,164-0,167. Pisos ya resume las condiciones de la vivienda |
| Suma de todas las débiles (puntaje P(A/B \| variables), en terciles o quintiles) | 4. No aporta | La ganancia aparente (Δ 0,151-0,153) es casi toda partición: con el placebo queda 0,003, y deja 7-12 % de celdas pequeñas |
| Tipo de vivienda | 3. No homologa | "Cuarto" es 2 % en GEIH, 29 % en el Sisbén nacional y 20 % en Bogotá: la pregunta no mide lo mismo |
| Tenencia de la vivienda | 3. No homologa | Los códigos van al revés entre fuentes y "otra" es 24 %, 53 % y 11 %; no hay equivalencia confiable |
| Cuartos para dormir | 3. No homologa | Un dormitorio: 40 % GEIH, 70 % Sisbén nacional, 46 % Bogotá. Además es el insumo del hacinamiento (filtro 2) |
| Sanitario de uso exclusivo | 3. No homologa | Exclusivo: 94 % GEIH, 56 % Sisbén nacional, 67 % Bogotá |
| Acueducto, alcantarillado, tipo de sanitario, fuente de agua | 2. Privación del IPM | Son privaciones del resultado: en la celda atarían el grupo imputado al propio resultado (tautología; principio de 2026-11-02) |
| Analfabetismo, logro educativo, inasistencia escolar, salud, informalidad y pensión | 2. Privación del IPM | Mismo motivo; además la educación y la ocupación no están en Bogotá |
| Estrato | 1. Falta en una fuente | Lo traen la GEIH y Bogotá, pero el archivo nacional del Sisbén 2024 no lo entrega |
| Internet, nevera, lavadora | 1. Falta en una fuente | No están en la GEIH o en Bogotá |
| Estado civil del jefe | 1. Equivale a otra | El Sisbén nacional solo trae dos códigos (con o sin pareja), que es la variable cónyuge |
| Eventos (inundación, avalancha…), días y horas de agua, localidad | 1. Falta en una fuente | Sin equivalente en la GEIH; la localidad solo existe en Bogotá |

Evidencia: `docs/reports/candidatas_celda_catalogo.csv` (distribución por
fuente y aporte de cada candidata) y
`docs/reports/comparacion_celdas_hotdeck_vivienda.csv` (celdas anidadas,
con placebo). Las privaciones del Sisbén (`I1`-`I15`, `H_5`) nunca se usan
(sección 7).

Cadena de respaldos (`claves_por_nivel`, definida una vez para el Hot-Deck
y la simulación): `celda_exacta` → `sin_menores` → `sin_personas` (la
celda del 2026-11-02) → `sin_pisos` → `solo_depto_edad` → `solo_depto` →
`pool_nacional`. Solo son donantes los hogares con `Clasificacion`
observada. Las celdas anteriores quedan como sensibilidad
(`incluir_menores=False`, `incluir_personas=False`, `incluir_pisos=False`).

## 7. ⚠️ Circularidad confirmada — nunca usar como Outcome

| Variable Sisbén | Motivo |
|---|---|
| `I1`–`I15` (Personas) | Privaciones Alkire-Foster proxy calculadas por el propio Sisbén |
| `H_5` (Personas) | Proxy interno del IPM calculado por Sisbén |
| `aseguramiento_salud` | Excluida por el mismo motivo |

## 8. Limitaciones registradas
- **Corte distinto (corregido 2026-10-10, dos iteraciones):** el archivo del SDP no es un corte único — es un registro administrativo continuo con `fec_fin_encuesta` entre 2019-03-22 y 2026-07-29 (verificado: cada hogar aparece una sola vez en el archivo, con la fecha de su único registro — no hay copias duplicadas repitiendo el mismo valor año a año). Antes del 2026-10-10 se usaban los 1.458.474 jefes completos bajo la etiqueta fija `"bogota_sdp_2026-08"`, sin filtrar por fecha.
  - **Primer intento (año exacto 2024):** descartado. Solo 75.488 de 1.458.474 jefes (5,2 %) tienen `fec_fin_encuesta` en el año 2024 exacto. Ese filtro confunde "estar registrado en 2024" con "haber sido re-encuestado en 2024" — el Sisbén no re-visita a todos los hogares cada año, así que subestima brutalmente el universo vigente y sesga la muestra hacia hogares con actualización reciente (que no son representativos del resto).
  - **Filtro adoptado (vigencia hasta corte, `fec_fin_encuesta <= 2024-12-31`):** 1.274.578 de 1.458.468 hogares (87,4 %) quedan vigentes; se descartan 183.890 por ser posteriores (registrados/actualizados en 2025-2026, fuera del alcance de "población 2024"). Es consistente con el nacional, cuyo `CORTE` tampoco trae fecha real por hogar (literal fijo `"SIV_2024"` para los 1.833.166 hogares) — ambas fuentes se tratan como "stock vigente a una fecha", no "encuestados ese año exacto".
  - Efecto en el Hot-Deck con el filtro adoptado: donante total 3.106.489 hogares (vs. 3.290.379 sin filtrar y 1.907.399 con año exacto). Celda exacta: 100 % con la celda de entonces (departamento y edad); 99,98 % con la vigente. Números de Grupo nacional actualizados el 2026-10-28 tras corregir `viv_cuartos` (ver más abajo) — ver `docs/resultados/1_datos_y_enlace/RESULTADOS_HOTDECK.md` para la cifra vigente.
  - **Dentro de Bogotá el filtro de fecha sigue importando** (ver `docs/resultados/1_datos_y_enlace/COMPARACION_FILTROS_SDP.md` para los números vigentes tras la corrección de vivienda) — la muestra de "solo recién actualizados" sigue sin ser representativa del Sisbén vigente de Bogotá.
  - Limitación que persiste: no se puede verificar si el nacional (`CORTE="SIV_2024"` fijo) tiene la misma mezcla de antigüedad por hogar que Bogotá — el extracto no expone una fecha real por hogar como sí lo hace el SDP.
- **Selección:** el Sisbén solo incluye hogares encuestados; asignar su distribución a todo el GEIH sobrerrepresenta A y B.
- **Edad por ciclo de vida**, no en años exactos.
- **Hogares sin jefe:** 13.083 en Sisbén nacional (0,7 %) y 227 en Bogotá con clasificación distinta entre miembros.

## 9. Pendientes de este diccionario
- [x] Confirmar los códigos de `PER002` — corroborado indirectamente (sección 5, 2026-10-10); sigue faltando la ficha ANDA oficial para confirmación 100 %.
- [x] Ubicar en GEIH las columnas equivalentes a `HOG027`, `VIV005`, `VIV008` — hecho 2026-10-28 (`P6008`, `P4030S3`, `P4030S5`), ver sección 4.
- [x] Verificar `geo_zona`, `viv_paredes`, `viv_pisos` contra el diccionario oficial de GEIH — hecho 2026-10-28 (sección 4); del lado Sisbén, con la ficha del Sisbén IV el 2026-11-02.
- [x] Sumar `viv_paredes`/`viv_pisos` a la celda — pisos sumado el 2026-11-02; paredes evaluado y descartado (sección 6).
- [ ] `jefe_sexo`: confirmar el sentido del código 1/2 en las dos fuentes (la pregunta está confirmada). No entra a la celda.

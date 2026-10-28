# Resumen de Avances — Efecto Causal del Sisbén IV

Última actualización: 2026-10-27 | Rama: `hotdeck-azure-avances`

## 1. Fuentes de datos — estado

| Fuente | Estado | Detalle |
|---|---|---|
| **IPM (DANE)** | ✅ Completo, año 2024 | 77.568 hogares nacional / 85.387 departamental. Limpieza en `src/2_limpieza.py` (Hogares, Personas, Viviendas). |
| **GEIH (DANE)** | ✅ Completo, 12 meses | 290.968 hogares (12 meses apilados), 8 módulos por mes. Cargador: `src/ingesta/geih_loader.py`. |
| **Sisbén IV nacional (DNP-ANDA)** | ✅ Obtenido | 1.833.166 hogares, 1.098 municipios. Corte mayo 2024. |
| **Sisbén IV Bogotá (SDP)** | ✅ Recibido, lote 03/08/2026; filtrado por vigencia el 2026-10-10 | El archivo es un registro continuo (`fec_fin_encuesta` 2019-2026), no un corte único. Se filtran los hogares vigentes al 31-dic-2024 (`fec_fin_encuesta <= esa fecha`): 1.274.578 de 1.458.468 (87,4 %); se descartan 183.890 posteriores a 2024. (Se descartó filtrar por año exacto de encuesta: solo deja 75.488 hogares y sesga hacia actualizaciones recientes, no representativo del registro vigente). Reemplaza al municipio 11001 del nacional (que traía 1.255). |
| **Banco de datos** | ✅ Azure Blob Storage (`datos-inferencia-causal`) | Publicación y restauración: `src/utils/publicar_banco_datos_azure.py` y `restaurar_banco_datos_azure.py`. Los datos no se versionan en GitHub. |

## 2. Pipeline por etapas (estructura del código)

| Etapa | Carpeta / script | Qué hace |
|---|---|---|
| Ingesta | `src/1_integracion.py`, `src/ingesta/` | CSV/TXT crudos → Parquet con trazabilidad |
| Limpieza | `src/2_limpieza.py` | Tipado, deduplicación y faltantes estructurales (no imputados) |
| **Armonización** | `src/armonizacion/` | Lleva GEIH, Sisbén nacional y Sisbén Bogotá a un esquema canónico por hogar (jefe de hogar) |
| **Emparejamiento estadístico** | `src/emparejamiento/` | Hot-Deck GEIH ← Sisbén por celdas (departamento + ciclo de vida del jefe + tramo de `viv_cuartos`, desde 2026-10-21) |
| **Validación** | `src/validacion/` | Cobertura de celdas, esquema armonizado, faltantes por módulo |
| Banco de datos | `src/utils/azure_storage.py` + publicar/restaurar | Sincronización con Azure |
| **Identificación causal** | `src/4_dag_identificacion.py` ✅ | Los dos DAG del pipeline (principal y de una sola tabla) + chequeo formal de d-separación — ver `docs/resultados/IDENTIFICACION_CAUSAL.md` |
| **Preprocesamiento** | `src/3_preprocesamiento.py` ✅ | Outcome real: IPM-GEIH reducido (4 de 15 privaciones) — ver `docs/resultados/RESULTADOS_DML_ATE_ATT_ATU.md` |
| **Estimación causal** | `src/5_estimacion.py` ✅ | DML (ATE/ATT/ATU) + Causal Forest (CATE), primera corrida real — ver §3b |
| **Robustez** | `src/estimacion/cotas_frechet_manski.py` ✅ | Cotas de Fréchet-Manski, sin suponer independencia condicional — ver §3c |
| Refutación | `src/6_refutacion.py` | Placebo, random common cause, sensibilidad a confusores — **no iniciado** |

## 3. Resultado del Hot-Deck (datos reales, 12 meses, Bogotá filtrada por vigencia a 2024, vivienda en la celda)

- 290.968 hogares GEIH receptores; **3.106.489** hogares Sisbén donantes (nacional + 1.274.578 de Bogotá vigentes al 31-dic-2024 — ver §1).
- **Celda exacta: 100 %** (departamento + ciclo de vida del jefe + tramo de `viv_cuartos`), también 100 % dentro de Bogotá.
- Grupo asignado, ponderado por factor de expansión: **A 31,2 % · B 35,2 % · C 23,2 % · D 10,3 %** (antes de sumar vivienda a la celda: A 28,0/B 34,4/C 24,9/D 12,7) — sumar `viv_cuartos` corrió la distribución hacia A y en contra de D, 2-3 p.p. en cada extremo.
- Dentro de Bogotá (depto 11, 10.016 hogares GEIH): **A 4,0 % · B 20,9 % · C 47,3 % · D 27,8 %** (con el filtro de vigencia del SDP; con año exacto de encuesta, descartado, D salía en 17,6 %).
- Crosswalk geográfico confirmado: `DPTO` (GEIH) = primeros 2 dígitos de `cod_mpio` (Sisbén).

**Cómo leerlo.** La celda ahora incluye vivienda (`viv_cuartos`), pero sigue sin incluir `viv_paredes`/`viv_pisos` (categorías sin verificar entre fuentes — ver §4). El 100 % de celda exacta no demuestra por sí solo un buen emparejamiento: el chequeo real de validez está en §3b, con DML/Causal Forest. La distribución de grupos refleja a los hogares *registrados* en el Sisbén, no a toda la población; no debe reportarse como prevalencia nacional. El emparejamiento solo es válido a nivel poblacional (no identifica el mismo hogar).

## 3b. Resultado de la estimación (primera corrida real, 2026-10-21)

Outcome: `ipm_geih_score` (IPM-GEIH reducido, 4 de 15 privaciones, 0-4) y
`POBRE_GEIH` (binario, score≥2, 23,5 % de los hogares). Tratamiento:
`T=1` si `Grupo_hotdeck ∈ {A,B}`. `W` = celda completa del Hot-Deck
(depto+edad+cuartos); `X` = `geo_zona`, `jefe_sexo`, `viv_paredes`, `viv_pisos`.

| Modelo | `ipm_geih_score` | `POBRE_GEIH` |
|---|---|---|
| ATE (`LinearDML`) | +0,0137 [IC95% +0,008;+0,019] | +0,0074 [IC95% +0,004;+0,011] |
| ATT | +0,0136 [+0,008;+0,019] | +0,0074 [+0,004;+0,011] |
| ATU | +0,0139 [+0,009;+0,019] | +0,0073 [+0,004;+0,011] |
| CATE medio (`CausalForestDML`) | +0,0149 (jefa mujer +0,029 vs. jefe hombre +0,001) | +0,0031 (jefa mujer +0,014 vs. jefe hombre -0,007) |

**Cómo leerlo:** ambos IC95% excluyen 0 — hay una asociación pequeña pero
estadísticamente distinta de cero entre el grupo asignado y las
privaciones, incluso controlando por la celda completa del Hot-Deck. Según
el chequeo formal de d-separación (`IDENTIFICACION_CAUSAL.md`) esto no
debería pasar si `W` capturara todo lo relevante — la pista más fuerte es
que `viv_paredes` es la segunda variable más importante del Causal Forest
en ambos outcomes: la vivienda sigue colándose por fuera de la celda. **No
se puede leer como efecto causal del Sisbén todavía** — ver
`docs/resultados/RESULTADOS_DML_ATE_ATT_ATU.md` y
`RESULTADOS_CAUSALFOREST_CATE.md` para el detalle y las limitaciones
completas.

## 3c. Cotas de Fréchet-Manski — robustez sin suponer independencia condicional (2026-10-27)

El DML del punto anterior asume que, dentro de la celda del Hot-Deck, el
grupo asignado es como-si-aleatorio. Para ver qué tan fuerte es esa
suposición, se calcularon cotas de Fréchet-Manski usando `P(Y|X)` directo
de GEIH y `P(T|X)` directo de Sisbén, sin pasar por el Hot-Deck:

| | Estimador | Rango (`POBRE_GEIH`) |
|---|---|---|
| Fréchet-Manski (sin CIA) | Cota | **[-0,627; +0,360]** |
| DML con Hot-Deck (con CIA) | Punto + IC95% | +0,0074 [+0,004; +0,011] |

La cota sin CIA es **145 veces más ancha**, y ninguna de las 342 celdas
individuales logra excluir el cero por su cuenta. **Confirma que toda la
precisión del resultado del DML depende de la suposición del Hot-Deck, no
de los datos crudos** — no es un hallazgo negativo, es la honestidad
matemática esperable sin supuestos adicionales. Detalle y propuesta para
angostar la cota (supuestos de monotonía) en
`docs/resultados/RESULTADOS_FRECHET_MANSKI.md`.

### Errores encontrados y corregidos durante la ejecución
1. **Doble jefe en Sisbén:** 65 hogares con dos jefes marcados → se conserva el primero.
2. **Edad del Sisbén en códigos, no en años:** `PER002` ∈ {3,4,5,6}. Con tramos de años, 89 % caía a `solo_depto`. Corregido comparando por ciclo de vida.
3. **GEIH agosto sin jefe:** llaves con formato distinto entre módulos (24.402 hogares). Corregido normalizando identificadores.
4. **Tipos mixtos al fusionar Bogotá:** corregido convirtiendo a texto.

## 4. Pendientes técnicos
- [x] **Verificar los códigos de `PER002`** (hipótesis: 3=12–17, 4=18–28, 5=29–59, 6=60+) — corroborada indirectamente el 2026-10-10 cruzando contra escolaridad/estado civil/pensión en la base completa de Personas; falta la ficha oficial de ANDA. Ver `docs/insumos/DICCIONARIO_HOTDECK.md` §5.
- [x] **Sumar variables de vivienda a la celda** — hecho parcialmente el 2026-10-21: se sumó `viv_cuartos` (conteo, seguro de usar sin homologar categorías). `viv_paredes`/`viv_pisos` siguen fuera — ver el punto siguiente.
- [ ] Verificar categorías de `geo_zona`, `jefe_sexo`, `viv_paredes`, `viv_pisos` entre fuentes — **ahora es el bloqueador principal**: el ATE/ATT/ATU/CATE real (§3b) no colapsa a 0 y la pista más fuerte apunta a `viv_paredes` sin resolver.
- [ ] Ubicar en GEIH los equivalentes de `HOG027`, `VIV005`, `VIV008`.
- [ ] Documentar como limitación la diferencia de corte (Bogotá 2026 vs. resto 2024).
- [ ] 6 hogares de Bogotá con doble jefe y 227 con `Clasificacion` distinta entre miembros: confirmar con SDP cuál es la oficial.
- [ ] Robustez: NND por distancia de Gower.
- [x] **Fase 2 (oficial): DML y Causal Forest** — primera corrida real completa el 2026-10-21 (ver §3b). Pendiente: resolver vivienda (punto de arriba) antes de interpretar el resultado como efecto causal.
- [ ] Completar las 11 privaciones restantes del IPM-GEIH (`ipm_geih_score` solo usa 4 de 15) si se consigue el diccionario oficial de GEIH.
- [ ] Refinar `sin_cotizacion_pension_jefe` (mezcla informalidad con desempleo/inactividad, ver `src/3_preprocesamiento.py`).
- [ ] Fase 3: RD en la frontera B/C (en duda, no hay puntaje continuo en la microdata).

## 5. ⚠️ Higiene del repositorio
Las carpetas `NACIONAL/` y `DEPARTAMENTAL/` (microdatos IPM, ~330 MB en CSV/DTA/SAV) están versionadas en git. Son datos públicos del DANE, pero contradicen la decisión de que Azure sea el único banco de datos. Hay que dejar de versionarlas (`git rm -r --cached`) y agregarlas a `.gitignore`; el historial seguirá conteniéndolas hasta que se reescriba (opcional).

## 6. Gestiones institucionales
| Solicitud | Estado |
|---|---|
| Sisbén IV (DNP-ANDA) | Resuelto — acceso vía ANDA |
| Sisbén Bogotá (SDP) | Resuelto — base recibida (corte 03/08/2026) |

## 7. Documentación de referencia
- `docs/insumos/DICCIONARIO_DATOS.md` — diccionario general IPM/GEIH
- `docs/insumos/DICCIONARIO_HOTDECK.md` — variables y llaves del emparejamiento
- `docs/insumos/CODIGOS_LOCALIDAD_BOGOTA.md` — localidades de Bogotá
- `docs/resultados/README.md` — **índice y resumen ejecutivo de todos los resultados** (empezar por aquí)
- `docs/resultados/IDENTIFICACION_CAUSAL.md` — los dos DAG y el chequeo formal de d-separación
- `docs/resultados/COMPARACION_FILTROS_SDP.md` — vigencia vs. año exacto del SDP, lado a lado
- `docs/resultados/RESULTADOS_DML_ATE_ATT_ATU.md` — primera corrida real de ATE/ATT/ATU
- `docs/resultados/RESULTADOS_CAUSALFOREST_CATE.md` — primera corrida real de CATE
- `docs/resultados/RESULTADOS_FRECHET_MANSKI.md` — cotas sin suponer independencia condicional (robustez)
- `src/estimacion/README.md` — prueba exploratoria que precedió a la corrida real
- `docs/seguimiento/CHANGELOG_PENDIENTES.md` — historial de cambios y pendientes

# Resumen de Avances — Efecto Causal del Sisbén IV

Última actualización: 2026-10-21 | Rama: `hotdeck-azure-avances`

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
| **Emparejamiento estadístico** | `src/emparejamiento/` | Hot-Deck GEIH ← Sisbén por celdas (departamento + ciclo de vida del jefe) |
| **Validación** | `src/validacion/` | Cobertura de celdas, esquema armonizado, faltantes por módulo |
| Banco de datos | `src/utils/azure_storage.py` + publicar/restaurar | Sincronización con Azure |
| **Identificación causal** | `src/4_dag_identificacion.py` | Los dos DAG del pipeline (principal y de una sola tabla) + chequeo formal de d-separación — ver `docs/resultados/IDENTIFICACION_CAUSAL.md` |
| **Prueba exploratoria** | `src/estimacion/` | ATE/ATT/CATE de prueba (no es la Fase 4) — ver `src/estimacion/README.md` |
| Causal (oficial) | `src/3_preprocesamiento.py`, `src/5_estimacion.py`, `src/6_refutacion.py` | Outcome oficial (IPM desde GEIH), DML/Causal Forest formal, refutación — **no iniciado** |

## 3. Resultado del Hot-Deck (datos reales, 12 meses, Bogotá filtrada por vigencia a 2024)

- 290.968 hogares GEIH receptores; **3.106.489** hogares Sisbén donantes (nacional + 1.274.578 de Bogotá vigentes al 31-dic-2024 — ver §1).
- **Celda exacta: 100 %** (departamento + ciclo de vida del jefe), también 100 % dentro de Bogotá.
- Grupo asignado, ponderado por factor de expansión: **A 28,0 % · B 34,4 % · C 24,9 % · D 12,7 %** — prácticamente igual al resultado sin filtrar por fecha (A 28,0/B 34,4/C 25,0/D 12,5), lo que confirma que el filtro de vigencia no distorsiona el agregado nacional.
- Dentro de Bogotá (depto 11, 10.016 hogares GEIH): **A 4,0 % · B 20,9 % · C 47,3 % · D 27,8 %** — aquí el filtro sí importa: con año exacto de encuesta (descartado, ver §8 de `DICCIONARIO_HOTDECK.md`) D salía en 17,6 %, 10 p.p. menos.
- Crosswalk geográfico confirmado: `DPTO` (GEIH) = primeros 2 dígitos de `cod_mpio` (Sisbén).

**Cómo leerlo.** La celda es gruesa (≈130 celdas), por eso el 100 % no demuestra por sí solo un buen emparejamiento: falta la sensibilidad con variables de vivienda. La distribución de grupos refleja a los hogares *registrados* en el Sisbén, no a toda la población; no debe reportarse como prevalencia nacional. El emparejamiento solo es válido a nivel poblacional (no identifica el mismo hogar).

### Errores encontrados y corregidos durante la ejecución
1. **Doble jefe en Sisbén:** 65 hogares con dos jefes marcados → se conserva el primero.
2. **Edad del Sisbén en códigos, no en años:** `PER002` ∈ {3,4,5,6}. Con tramos de años, 89 % caía a `solo_depto`. Corregido comparando por ciclo de vida.
3. **GEIH agosto sin jefe:** llaves con formato distinto entre módulos (24.402 hogares). Corregido normalizando identificadores.
4. **Tipos mixtos al fusionar Bogotá:** corregido convirtiendo a texto.

## 4. Pendientes técnicos
- [x] **Verificar los códigos de `PER002`** (hipótesis: 3=12–17, 4=18–28, 5=29–59, 6=60+) — corroborada indirectamente el 2026-10-10 cruzando contra escolaridad/estado civil/pensión en la base completa de Personas; falta la ficha oficial de ANDA. Ver `docs/DICCIONARIO_HOTDECK.md` §5.
- [ ] Sumar variables de vivienda a la celda y medir sensibilidad (celda exacta vs. todos los niveles).
- [ ] Verificar categorías de `geo_zona`, `jefe_sexo`, `viv_paredes`, `viv_pisos` entre fuentes.
- [ ] Ubicar en GEIH los equivalentes de `HOG027`, `VIV005`, `VIV008`.
- [ ] Documentar como limitación la diferencia de corte (Bogotá 2026 vs. resto 2024).
- [ ] 6 hogares de Bogotá con doble jefe y 227 con `Clasificacion` distinta entre miembros: confirmar con SDP cuál es la oficial.
- [ ] Robustez: NND por distancia de Gower.
- [ ] Fase 2 (oficial): DML y Causal Forest sobre el outcome real (IPM desde GEIH) — la prueba exploratoria (2026-10-21, `src/estimacion/`) ya corrió sobre un outcome provisional (empleo/ingreso del jefe) y encontró que el residuo no explicado por depto+edad se concentra en vivienda, consistente con el punto de arriba. Fase 3: RD en la frontera B/C (en duda, no hay puntaje continuo en la microdata).

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
- `docs/resultados/IDENTIFICACION_CAUSAL.md` — los dos DAG y el chequeo formal de d-separación
- `docs/resultados/COMPARACION_FILTROS_SDP.md` — vigencia vs. año exacto del SDP, lado a lado
- `src/estimacion/README.md` — prueba exploratoria de ATE/ATT/CATE
- `docs/seguimiento/CHANGELOG_PENDIENTES.md` — historial de cambios y pendientes

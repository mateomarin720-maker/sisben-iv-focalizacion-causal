# Changelog del proyecto

Formato: más reciente primero. Rama de trabajo: `hotdeck-azure-avances`.

## 2026-10-21 — Orden de la documentación y acceso a los datos

### Reorganizado
La carpeta `docs/` se agrupa por para qué sirve cada documento (ver [`docs/README.md`](../README.md)):

| Antes | Ahora |
|---|---|
| `docs/DICCIONARIO_DATOS.md`, `docs/DICCIONARIO_HOTDECK.md`, `docs/CODIGOS_LOCALIDAD_BOGOTA.md`, `docs/referencias_teoricas.md` | `docs/insumos/` |
| `data/diccionario_ipm_2025.md` | `docs/insumos/DICCIONARIO_IPM_2025.md` |
| `docs/RESUMEN_AVANCES.md`, `docs/CHANGELOG_PENDIENTES.md` | `docs/seguimiento/` |
| `docs/Anteproyecto_Sisben_IV.docx` | `docs/institucional/` |

`docs/reports/` no cambia: los scripts de calidad de datos escriben allí.

### Añadido
- `docs/insumos/DESCRIPCION_TABLAS.md`: qué es una fila, llave, filas y script de cada tabla de `data/2_models/`.
- `docs/resultados/RESULTADOS_HOTDECK.md`: resultado del emparejamiento y verificación empírica de los códigos de `PER002`.

## 2026-10-09 — Armonización, Hot-Deck con Bogotá y reorganización del código

### Corregido
- **Llave de hogar del GEIH (agosto):** los 24.402 hogares de agosto quedaban sin jefe (sexo y edad nulos) porque los identificadores de `hogar_vivienda` y `caracteristicas_generales` no cruzaban por formato. Ahora `DIRECTORIO`, `SECUENCIA_P` y `HOGAR` se normalizan a texto de entero en ambas tablas, y el script avisa si un mes queda con más del 2 % de hogares sin jefe.
- **Edad del jefe en Sisbén:** `PER002` no está en años: el extracto trae códigos 3–6 (ver `DICCIONARIO_HOTDECK.md`). La celda de matching usaba tramos de años contra códigos, y por eso el 89 % caía a `solo_depto`. Ahora se compara por ciclo de vida.
- **Llave completa del Sisbén en la salida:** el parquet armonizado conserva `cod_mpio`, `geo_zona`, `llave`, `CORTE` y `HOGAR` y crea `llave_hogar_sisben` (única, verificada: 1.833.166 filas = 1.833.166 llaves).
- **Viviendas:** se une por `HOGAR` si el archivo lo trae, y se verifica una fila por hogar.
- **Fusión con Bogotá:** columnas de tipo mixto (texto + entero) rompían la escritura a parquet; se convierten a texto.

### Añadido
- **Sisbén Bogotá (SDP, corte 03/08/2026):** 1.458.468 hogares armonizados. En la fusión reemplazan al municipio 11001 del extracto nacional (que traía 1.255 hogares). Donantes totales: 3.290.379.
- **Validación de cobertura de celdas** (`src/validacion/`).

### Resultado del Hot-Deck (12 meses GEIH, 290.968 hogares, donante con Bogotá)
- Celda exacta (departamento + ciclo de vida del jefe): **100 %**.
- Grupo asignado ponderado por `fex`: A 28,0 % · B 34,4 % · C 25,0 % · D 12,5 %.
- Historial de la cobertura: 10,8 % (edad mal codificada) → 91,6 % (edad por ciclo de vida; 8,4 % eran los hogares sin jefe de agosto) → 100 %.

### Reorganización de scripts (nombres alineados con las etapas de la tesis)
| Antes | Ahora | Etapa |
|---|---|---|
| `src/preprocesamiento/estandarizar_geih.py` | `src/armonizacion/armonizar_geih_hogar_2024.py` | Armonización de fuentes |
| `src/preprocesamiento/estandarizar_sisben.py` | `src/armonizacion/armonizar_sisben_hogar_2024.py` | Armonización de fuentes |
| `src/preprocesamiento/estandarizar_sisben_bogota.py` | `src/armonizacion/armonizar_sisben_bogota_sdp.py` | Armonización de fuentes |
| `src/hotdeck/hotdeck_estandarizado.py` | `src/emparejamiento/emparejamiento_hotdeck_geih_sisben.py` | Emparejamiento estadístico |
| `diagnostico_celdas.py` (raíz) | `src/validacion/validar_cobertura_celdas_hotdeck.py` | Validación |
| `verificar_estandarizado.py` (raíz) | `src/validacion/verificar_esquema_armonizado.py` | Validación |
| `revisar_faltantes_geih.py` (raíz) | `src/validacion/revisar_faltantes_modulos_geih.py` | Validación |
| `src/utils/subir_todo_a_azure.py` | `src/utils/publicar_banco_datos_azure.py` | Banco de datos |
| `src/utils/descargar_todo_desde_azure.py` | `src/utils/restaurar_banco_datos_azure.py` | Banco de datos |

Eliminados de la raíz (scripts temporales, ya cubiertos): `hotdeck_geih_sisben_VALIDADO.py` (primera versión, reemplazada), `diagnostico_env*.py` (depuración de la conexión Azure).
Los nombres de los parquets en `data/2_models/` **no cambiaron**, para no volver a subir el banco de datos.

### Documentación unificada
Todos los `.md` (raíz, `data/`, `docs/`, `src/`, `notebooks/`) y `data/catalogo.yaml` se alinearon al mismo momento del proyecto (2026-10-09): objetivos vigentes P1/OE1, P2/OE2, P3/OE3; fuentes obtenidas (GEIH 2024, IPM 2024, Sisbén nacional y Bogotá); Azure como banco de datos; etapas del código `ingesta → armonizacion → emparejamiento → validacion`. Se retiraron referencias a OE4/OE5, al "puntaje continuo" del Sisbén y a fuentes "por solicitar" que ya se obtuvieron.

### Pendiente
- [ ] Verificar en ANDA (`PER002`, V926) la tabla de códigos de ciclo de vida: **hoy es una hipótesis** (3=12–17, 4=18–28, 5=29–59, 6=60+).
- [ ] Agregar variables de vivienda a la celda y medir sensibilidad de la distribución de grupos.
- [ ] Verificar categorías de `geo_zona`, `jefe_sexo`, `viv_paredes`, `viv_pisos` entre fuentes.
- [ ] Ubicar en el GEIH equivalentes de `HOG027`, `VIV005`, `VIV008`.
- [ ] Unificar la fecha de corte: Bogotá es agosto 2026; el resto de Sisbén, mayo 2024.
- [ ] Retirar del repositorio los microdatos IPM versionados (`NACIONAL/`, `DEPARTAMENTAL/`, ~330 MB) — ver `docs/RESUMEN_AVANCES.md`.
- [ ] Fase 2: DML y Causal Forest; Fase 3: RD en la frontera B/C.

## Sesiones anteriores
- 2026-09-24: estandarización GEIH/Sisbén, Hot-Deck validado, conexión Azure Blob Storage, renombre del repositorio a `sisben-iv-focalizacion-causal`.
- Ingesta IPM, GEIH (12 meses) y Sisbén IV; limpieza IPM; diccionario de datos; IPM corregido al año 2024; `package-mode = false` en `pyproject.toml`.

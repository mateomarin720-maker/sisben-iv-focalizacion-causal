# Resumen de Avances — Efecto Causal del Sisbén IV

Última actualización: 2026-09-24 | Rama: `hotdeck-azure-avances`

## 1. Fuentes de datos — estado

| Fuente | Estado | Detalle |
|---|---|---|
| **IPM (DANE)** | ✅ Completo, año 2024 corregido | 77.568 hogares nacional / 85.387 departamental. Limpieza (`2_limpieza.py`) corre sobre Hogares, Personas, Viviendas. |
| **GEIH (DANE)** | ✅ Completo, 12 meses | 290.968 hogares (12 meses apilados), 8 módulos c/u. Loader automático (`geih_loader.py`). |
| **Sisbén IV (DNP-ANDA)** | ✅ Obtenido, con brecha de cobertura conocida | 1.833.166 hogares nacional, PERO **Bogotá solo trae 1.255 hogares** (0,07% de la muestra) — el Distrito administra su Sisbén aparte vía SDP. Solicitud enviada a SDP para complementar (pendiente respuesta). |
| **Respaldo en la nube** | ✅ Conectado y validado | Azure Blob Storage (`datos-inferencia-causal`), scripts de subida/descarga en `src/utils/azure_storage.py`. |

## 2. Pipeline construido

1. **Ingesta** (`src/1_integracion.py`, `geih_loader.py`, `sisben_loader.py`): CSV/TXT crudos → Parquet, con trazabilidad.
2. **Limpieza** (`2_limpieza.py`): tipado, deduplicación, documentación de faltantes estructurales (77,79% en IPM, 42,02% en GEIH — ambos verificados como no-aleatorios, no imputados).
3. **Estandarización** (`estandarizar_geih.py`, `estandarizar_sisben.py`): ambas fuentes llevadas a un esquema canónico común (9 columnas homologadas: geografía, vivienda, demografía del jefe de hogar).
4. **Hot-Deck** (`hotdeck_estandarizado.py`): fusión estadística GEIH↔Sisbén por celdas (departamento + tramo de edad del jefe), con degradación jerárquica (celda exacta → solo departamento → pool nacional).

## 3. Resultado del Hot-Deck (validado con datos reales)

- **Crosswalk geográfico confirmado 100%**: `DPTO` (GEIH) = primeros 2 dígitos de `cod_mpio` (Sisbén), mismos 33 códigos DIVIPOLA.
- Distribución del tratamiento asignado (Grupo A/B/C/D) razonablemente consistente con la distribución real nacional de Sisbén.
- 11% de emparejamientos en celda exacta, 89% degradó a nivel departamento — esperable dado que Sisbén (población vulnerable) y GEIH (representativa nacional) tienen distribuciones de edad distintas.
- **Bug real encontrado y corregido**: 65 hogares Sisbén con doble "jefe de hogar" marcado — ya resuelto en el estandarizador.

## 4. Pendientes técnicos

- [ ] Sumar variables de vivienda (`viv_paredes`, `viv_pisos`, `viv_cuartos`) a la celda de matching — ya estandarizadas, falta verificar oficialmente la dirección de sus códigos entre fuentes antes de usarlas.
- [ ] Verificar codificación oficial de `geo_zona` (urbano/rural) — actualmente excluida de la celda por esta razón.
- [ ] Integrar datos de Sisbén Bogotá (SDP) una vez lleguen, sin duplicar los 1.255 hogares ya presentes en el extracto nacional.
- [ ] NND por distancia de Gower como robustez complementaria al hot-deck por celdas.
- [ ] Apilar los 12 meses de GEIH en el hot-deck (actualmente probado con 1 mes; el estandarizador ya soporta los 12).

## 5. Gestiones institucionales en curso

| Solicitud | Estado |
|---|---|
| GEIH/Sisbén vinculado (DNP) | Resuelto — acceso directo obtenido vía ANDA |
| Sisbén Bogotá (SDP) | Enviado a `radicacionplaneacionbogota@sdp.gov.co`, en espera |

## 6. Documentación de referencia generada

- `docs/DICCIONARIO_DATOS.md` — diccionario completo IPM/GEIH
- `docs/DICCIONARIO_HOTDECK.md` — variables específicas de matching
- `docs/CODIGOS_LOCALIDAD_BOGOTA.md` — códigos de localidad y CP de Bogotá, para cuando lleguen esos datos

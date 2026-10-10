# Carpeta: Datos y Conexiones
---
Esta carpeta almacena todos los activos de datos del proyecto, organizados
por su estado en el ciclo de vida. Por la naturaleza sensible de los
microdatos del Sisbén IV y la GEIH, **el contenido de las subcarpetas no
se versiona** (ver `.gitignore`); solo se versionan estos `README.md` y
[`catalogo.yaml`](catalogo.yaml).

## Banco de datos (Azure) — los datos NO están en git

El banco de datos principal es **Azure Blob Storage**, contenedor
`datos-inferencia-causal`. Para publicar o restaurar:

```bash
poetry run python -m src.utils.publicar_banco_datos_azure     # sube 2_models, 1_processed, 0_raw
poetry run python -m src.utils.restaurar_banco_datos_azure    # descarga todo a data/
```
La credencial (`AZURE_STORAGE_CONNECTION_STRING`) va en `.env`, nunca en el
repositorio ni en chats.

## Catálogo de fuentes

El detalle de cada fuente (portal, tipo de acceso, identificador, período
y estado de obtención) está en [`catalogo.yaml`](catalogo.yaml). El
diccionario de variables del IPM (DDI oficial de DANE) está en
[`diccionario_ipm_2025.md`](diccionario_ipm_2025.md). Estado actual:

| Fuente | Entidad | Estado (2026-10-09) |
|---|---|---|
| GEIH 2024 | DANE | ✅ 12 meses, 8 módulos por mes; 290.968 hogares |
| Sisbén IV nacional | DNP (ANDA) | ✅ 1.833.166 hogares, 1.098 municipios (corte mayo 2024) |
| Sisbén IV Bogotá | SDP | ✅ 1.458.468 hogares (corte 03/08/2026); reemplaza al municipio 11001 del nacional |
| IPM 2024 | DANE | ✅ 77.568 hogares nacional / 85.387 departamental |
| DPS (participación en programas) | DPS | ⏳ Por gestionar — condiciona el escenario de primera etapa de OE2 |
| RUI | UARIV | ⏳ Fuera del alcance replanteado; por confirmar con el tutor |

## Subcarpetas y artefactos correspondientes

### `0_raw/`
- **Propósito**: Almacenar los datos originales sin modificación alguna.
- **Regla de oro**: Esta carpeta es de **solo lectura**. Toda transformación
  debe partir de una copia en `1_processed/`.

### `1_processed/`
- **Propósito**: Datos limpios, armonizados y preparados para el análisis
  causal.
- **Artefactos esperados**:
  - Parquets limpios por fuente (GEIH por mes y módulo, Sisbén por tabla,
    IPM Hogares/Personas/Viviendas).
  - Pendiente: tabla unificada a nivel hogar con tratamiento, outcomes y
    confusores, lista para DML / Causal Forest.

### `2_models/`
- **Propósito**: Guardar objetos serializados de estimadores y resultados
  intermedios.
- **Artefactos esperados**:
  - **Hoy:** bases armonizadas (`geih_estandarizado_2024`,
    `sisben_estandarizado_2024`, `sisben_bogota_estandarizado`,
    `sisben_estandarizado_2024_con_bogota`) y el resultado del emparejamiento
    (`geih_sisben_fusionado_2024`).
  - **Previsto:** modelos LASSO/Ridge y SHAP (OE1); objetos DML / Causal
    Forest con su identificación documentada (OE2); simulaciones de reglas
    de focalización (OE3).

---
### ⚠️ Nota de seguridad importante

**NUNCA** subas microdatos del Sisbén, GEIH, IPM o DPS a repositorios de Git
(el banco de datos es Azure). El `.gitignore` ya bloquea el contenido
de estas carpetas; no lo modifiques sin coordinación con el equipo y el
profesor tutor.

El manejo de los datos debe ceñirse a la **Ley 1581 de 2012** (protección
de datos personales) y a los términos de uso que establezca el DNP/DANE/DPS/UARIV.

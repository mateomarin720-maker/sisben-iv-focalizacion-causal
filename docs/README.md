# Carpeta: docs (Documentación)
---
Este directorio consolida toda la documentación del proyecto, en formatos
legibles tanto para audiencias técnicas como no técnicas.

## Contenido y artefactos

### Documentos fundamentales
- **[`DICCIONARIO_DATOS.md`](DICCIONARIO_DATOS.md)**
  - Diccionario de datos consolidado: variables efectivamente en uso
    (identificadores, outcome, predictoras, tratamiento pendiente),
    tipo, distribución real y estado por fuente. Se actualiza cada vez
    que se integra una fuente nueva.
- **[`DICCIONARIO_HOTDECK.md`](DICCIONARIO_HOTDECK.md)**
  - Variables, llaves de hogar y limitaciones del emparejamiento
    GEIH ↔ Sisbén (incluye Bogotá y los códigos de edad `PER002`).
- **[`RESUMEN_AVANCES.md`](RESUMEN_AVANCES.md)** y
  **[`CHANGELOG_PENDIENTES.md`](CHANGELOG_PENDIENTES.md)**
  - Estado general del proyecto e historial de cambios y pendientes.
- **[`Anteproyecto_Sisben_IV.docx`](Anteproyecto_Sisben_IV.docx)**
  - Documento formal de anteproyecto (abril 2026): marco teórico, revisión
    de literatura, metodología, cronograma y bibliografía. ⚠️ Contiene la
    formulación anterior de objetivos (OE1–OE5); los objetivos vigentes son
    P1/OE1, P2/OE2 y P3/OE3 (ver `README.md` de la raíz). Su actualización
    está pendiente a cargo del equipo.
- **`DAG_causal.md` / `.png`** *(pendiente)*
  - Diagrama causal (DAG) propuesto: elegibilidad (grupos A/B) →
    participación en programas DPS → bienestar multidimensional,
    confusores y mediadores.
  - Justificación de cada arista con literatura o razonamiento experto.
- **`Supuestos_de_identificacion.md`** *(pendiente)*
  - Criterios evaluados (backdoor, discontinuidad B/C) y supuestos asumidos
    explícitamente (ignorabilidad condicional, positividad, SUTVA).

### Subcarpeta `img/`
- Recursos visuales: DAGs, diagramas de flujo ETL, gráficos exportados
  desde los notebooks.

### Subcarpeta `reports/`
- **`Reporte_EDA.pdf`** *(pendiente, Fase 2)*: hallazgos del análisis
  exploratorio por fuente y subpoblación.
- **`Reporte_Determinantes_y_Validez.pdf`** *(pendiente, OE1)*: LASSO/Ridge,
  SHAP, AUC-ROC y matrices de error de inclusión/exclusión frente a IPM y
  pobreza monetaria.
- **`Reporte_Resultados_Causales.pdf`** *(pendiente, OE2)*: ATE/ATT, CATE,
  test BLP (Causal Forest / DML) y contraste con la discontinuidad B/C.
- **`Informe_Final_Ejecutivo.pdf`** *(pendiente, OE3)*: reglas de
  focalización contrafactuales, brecha FGT1 y recomendaciones de política.

# Comparación de filtros del SDP (Sisbén Bogotá): vigencia vs. año exacto

Generado 2026-10-21 por `src/validacion/comparar_filtros_sdp.py`, refrescado
el mismo día tras sumar `viv_cuartos` a la celda del Hot-Deck (números
actualizados abajo). Resuelve
con evidencia la duda abierta en `docs/seguimiento/CHANGELOG_PENDIENTES.md`
(2026-10-10): el archivo del SDP trae `fec_fin_encuesta` por hogar entre
2019-03-22 y 2026-07-29 — no es un corte único, es un registro
administrativo continuo. Hay dos formas razonables de filtrarlo a "2024":

- **Vigencia (adoptado):** `fec_fin_encuesta <= 2024-12-31` — todo hogar
  cuyo único registro es anterior o igual a esa fecha, sin importar el año
  exacto. Trata el Sisbén como un *stock* vigente a una fecha, igual que el
  nacional (cuyo `CORTE` tampoco trae fecha real por hogar).
- **Año exacto:** `fec_fin_encuesta` cae en 2024. Solo hogares re-encuestados
  ese año exacto — descartado como filtro principal porque la mayoría de
  hogares del Sisbén no se re-encuestan cada año, así que este filtro
  subestima el universo vigente y sesga la muestra hacia actualizaciones
  recientes.

## Resultado lado a lado (celda del Hot-Deck con `viv_cuartos`, 2026-10-21)

| Filtro | Hogares Bogotá | Donante total (con nacional) | Grupo nacional (A/B/C/D, %) | Grupo Bogotá (A/B/C/D, %) |
|---|---|---|---|---|
| Vigencia ≤31-dic-2024 | 1.274.578 (87,4 %) | 3.106.489 | 31,2 / 35,2 / 23,2 / 10,3 | 5,3 / 25,4 / 48,3 / 21,0 |
| Año exacto 2024 | 75.488 (5,2 %) | 1.907.399 | 31,6 / 35,9 / 23,1 / 9,4 | 7,2 / 29,5 / 47,8 / 15,5 |

Detalle completo (incl. % en celda exacta): `docs/reports/comparacion_filtros_sdp.csv`.

## Cómo leerlo

- **A nivel nacional el filtro casi no importa** (ambas filas quedan muy
  cerca entre sí) porque Bogotá es solo una de 33 unidades geográficas en
  la celda del Hot-Deck — el peso de Bogotá en el donante total se diluye.
- **Dentro de Bogotá el filtro sigue importando, aunque algo menos que
  antes de sumar vivienda a la celda:** Grupo D pasa de 21,0 % a 15,5 %
  según cuál se use — 5,5 puntos de diferencia (antes de sumar
  `viv_cuartos` a la celda la brecha era de 10,2 puntos; la celda más fina
  reduce, pero no elimina, la sensibilidad al filtro). La muestra de "solo
  recién actualizados" (año exacto) sigue sesgada: son hogares que por
  algún motivo pidieron o recibieron una actualización reciente, no una
  muestra representativa del registro vigente de la ciudad.
- **Conclusión:** se mantiene el filtro de vigencia como el adoptado para
  el pipeline (`sisben_bogota_estandarizado.parquet`,
  `sisben_estandarizado_2024_con_bogota.parquet`, sin sufijo). El filtro de
  año exacto queda disponible como archivo paralelo
  (`*_anio_exacto.parquet`) para quien quiera reproducir la comparación o
  usarlo como análisis de sensibilidad.

## Cómo reproducirlo

```bash
poetry run python -m src.armonizacion.armonizar_sisben_bogota_sdp RUTA_CSV --modo vigencia
poetry run python -m src.armonizacion.armonizar_sisben_bogota_sdp RUTA_CSV --modo anio_exacto
poetry run python -m src.validacion.comparar_filtros_sdp
```

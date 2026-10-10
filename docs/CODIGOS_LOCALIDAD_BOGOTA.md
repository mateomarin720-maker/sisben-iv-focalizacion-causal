# Códigos de localidad — Bogotá D.C.

Referencia de las localidades de Bogotá para el Sisbén IV entregado por la
SDP (corte 03/08/2026). En esa base la columna `Cod_comuna` trae el código
de localidad de dos dígitos (01–20) de la tabla siguiente; toda Bogotá usa
el código DIVIPOLA de municipio `11001` en el resto de las fuentes, y la
localidad es un nivel de desagregación **más fino, interno de Bogotá**.
La GEIH no desagrega por localidad, por eso `geo_localidad` es solo
descriptiva y **no entra a la celda del Hot-Deck**.

| Código | Localidad | Zona |
|---|---|---|
| 01 | Usaquén | Urbana |
| 02 | Chapinero | Urbana |
| 03 | Santa Fe | Urbana |
| 04 | San Cristóbal | Urbana |
| 05 | Usme | Urbana (con área rural) |
| 06 | Tunjuelito | Urbana |
| 07 | Bosa | Urbana |
| 08 | Kennedy | Urbana |
| 09 | Fontibón | Urbana |
| 10 | Engativá | Urbana |
| 11 | Suba | Urbana (con área rural) |
| 12 | Barrios Unidos | Urbana |
| 13 | Teusaquillo | Urbana |
| 14 | Los Mártires | Urbana |
| 15 | Antonio Nariño | Urbana |
| 16 | Puente Aranda | Urbana |
| 17 | La Candelaria | Urbana |
| 18 | Rafael Uribe Uribe | Urbana |
| 19 | Ciudad Bolívar | Urbana (con área rural) |
| 20 | Sumapaz | **Rural** (única localidad 100% rural) |

## Códigos Postales (CP) — referencia adicional

Colombia usa además un sistema de Código Postal de 6 dígitos, DISTINTO
al `cod_mpio` DIVIPOLA que ya usa el crosswalk geográfico del proyecto
(`cod_mpio="11001"` para Bogotá completa). Estructura: `11` (Bogotá) +
2 dígitos de localidad + 2 dígitos de zona/UPZ. Guardado aquí por si
el archivo de SDP-Bogotá llega identificado por Código Postal en vez
de por número de localidad simple — en ese caso, los primeros 4
dígitos (`11` + localidad) permiten mapear a la tabla de localidades
de arriba.

Ejemplos verificados (rango de CP por localidad, no exhaustivo):

| Localidad | Rango de CP visto |
|---|---|
| Usaquén (01) | 110111–110151 |
| Chapinero (02) | 110211–110231 |
| Santa Fe (03) | 110311–110321 |
| San Cristóbal (04) | 110411–110441 |
| Usme (05) | 110511–110571 |
| Tunjuelito (06) | 110611–110621 |
| Bosa (07) | 110711–110741 |
| Kennedy (08) | 110811–110881 |
| Fontibón (09) | 110911–110931 |
| Engativá (10) | 111011–111071 |
| Suba (11) | 111111–111176 |
| Barrios Unidos (12) | 111211–111221 |
| Teusaquillo (13) | 111311–111321 |
| Los Mártires (14) | 111411 |
| Antonio Nariño (15) | 111511 |
| Puente Aranda (16) | 111611–111631 |
| La Candelaria (17) | 111711 |
| Rafael Uribe Uribe (18) | 111811–111841 |
| Ciudad Bolívar (19) | 111911–111981 |
| Sumapaz (20) | 112011–112041 |

## Estado (2026-10-09)

- [x] Microdato de la SDP obtenido: 1.458.468 hogares (Bogotá), armonizado en
      `src/armonizacion/armonizar_sisben_bogota_sdp.py`.
- [x] La base usa código de localidad 01–20 (no Código Postal); la tabla de
      Códigos Postales queda solo como referencia.
- [x] Integración sin duplicar: las filas del municipio 11001 del extracto
      nacional (1.255 hogares) se reemplazan por las de la SDP.
- [ ] Corte distinto (agosto 2026 vs. mayo 2024 del nacional): documentar
      como limitación.
- [ ] Confirmar con la SDP los 227 hogares cuya `Clasificacion` difiere entre
      sus miembros y los 6 con doble jefe de hogar.

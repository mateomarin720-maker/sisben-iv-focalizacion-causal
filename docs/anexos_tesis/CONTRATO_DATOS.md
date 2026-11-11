# Anexo: contrato de datos

Columnas que exige el módulo de simulación (`src/simulacion/contrato.py`) a quien lo use con sus propios datos. Los nombres son los de las tablas estandarizadas del proyecto y no se cambian ni se traducen: el módulo valida que estén y que sus códigos estén en el dominio, y si no, falla nombrando cada columna. Las variables derivadas (celda del Hot-Deck, zona urbana, jefe mujer, P(T | celda)) las calcula el módulo.

Los códigos se comparan como texto: un código `1.0` no es `1` y se rechaza. Esta tabla se genera del código (`python -m src.utils.anexo_trazabilidad`).

| Columna | Tabla | Obligatoria | Tipo | Dominio y origen |
|---|---|---|---|---|
| `geo_depto` | hogares | sí | código (texto) | código DANE de 2 dígitos |
| `geo_zona` | hogares | sí | código (texto) | 1 urbano, 2 rural (CLASE) |
| `jefe_sexo` | hogares | sí | código (texto) | 1 hombre, 2 mujer (P3271) |
| `jefe_edad` | hogares | sí | entero (texto) | edad del jefe en años, 0 a 120 |
| `viv_cuartos` | hogares | sí | entero (texto) | cuartos en total (P5000), 1 o más |
| `viv_pisos` | hogares | sí | código (texto) | material de pisos, códigos GEIH de P4020 (1-7) |
| `viv_paredes` | hogares | sí | código (texto) | material de paredes, códigos GEIH de P4010 (1-9) |
| `ingreso_percapita` | hogares | sí | real | ingreso per cápita de la unidad de gasto, pesos, 0 o más |
| `dominio_pm` | hogares | sí | código (texto) | dominio de la línea de pobreza: 13_ciudades, otras_cabeceras, rural |
| `fex` | hogares | no | real | factor de expansión, mayor que 0 |
| `Grupo` | hogares | no | código (texto) | grupo del Sisbén observado (A-D) |
| `vinculo` | hogares | no | código (texto) | cómo se obtuvo Grupo: llave o hotdeck |
| `geo_depto` | registro | sí | código (texto) | código DANE de 2 dígitos |
| `jefe_edad` | registro | sí | código (texto) | código de ciclo de vida de PER002 (3-6) |
| `viv_cuartos` | registro | sí | entero (texto) | cuartos en total (VIV009), 1 o más |
| `viv_pisos` | registro | sí | código (texto) | material de pisos, códigos del Sisbén (1-6; orden inverso al de la GEIH) |
| `Grupo` | registro | sí | código (texto) | grupo del Sisbén (A-D) |
| `Clasificacion` | registro | sí | texto | subgrupo del Sisbén; nulo en hogares sin clasificar |

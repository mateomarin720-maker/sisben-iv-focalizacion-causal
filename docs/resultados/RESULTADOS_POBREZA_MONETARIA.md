# Resultados — Pobreza monetaria reconstruida con GEIH 2024

Generado 2026-11-02 por `src/indicadores/pobreza_monetaria_geih.py`.
Metodología y decisiones:
`docs/metodologia/pobreza_monetaria/01_diccionario_ingreso.md` (sobre la
auditoría `00_auditoria_y_metodologia.md`). Salidas:
- `data/2_models/muestra_pobreza_monetaria_reconstruida_2024.parquet` (personas)
- `data/2_models/pobreza_monetaria_hogar_2024.parquet` (hogares)
- `docs/reports/validacion_pobreza_monetaria.csv` y `pobreza_monetaria_geih.txt`

**Es una reconstrucción experimental, no la medición oficial.** El DANE
cruza GEIH con registros administrativos (ayudas institucionales, PILA)
que no son públicos, e imputa con un modelo que no publica. Se rotula
`FUENTE_PM = "reconstruccion_geih_publica"`.

## Resultado (escenario base, personas, `FEX_C18 / 12`)

| Dominio | FGT0 pobreza | Oficial | FGT1 | Oficial | FGT0 extrema | Oficial | Gini | Oficial |
|---|---|---|---|---|---|---|---|---|
| Nacional | 33,2 % | 31,8 % | 13,5 % | 12,6 % | 12,5 % | 11,7 % | 0,565 | 0,551 |
| Cabeceras | 30,9 % | 28,6 % | 12,3 % | 11,0 % | 9,9 % | 8,7 % | 0,548 | 0,530 |
| 13 ciudades y A.M. | 26,4 % | 24,0 % | 10,2 % | 8,9 % | 7,0 % | 5,9 % | 0,545 | 0,522 |
| Otras cabeceras | 36,7 % | 34,8 % | 15,1 % | 13,9 % | 13,8 % | 12,4 % | 0,502 | 0,490 |
| Centros poblados y rural disperso | 41,3 % | 42,5 % | 17,6 % | 17,9 % | 21,3 % | 21,8 % | 0,494 | 0,482 |

FGT2 nacional: 7,8 % (el boletín no lo publica). Población expandida:
51,55 M; 828.305 personas en unidades de gasto.

## Sensibilidad (nacional)

| Escenario | FGT0 | FGT1 | FGT0 extrema | Gini |
|---|---|---|---|---|
| **Base** | **33,2 %** | **13,5 %** | **12,5 %** | **0,565** |
| No respuesta laboral = 0 | 34,9 % | 15,0 % | 14,1 % | 0,571 |
| Caso completo (reponderado por dominio) | 33,6 % | 13,7 % | 12,7 % | 0,564 |
| UG sin `P6050` = 11 y 12 (D2) | 33,2 % | 13,5 % | 12,5 % | 0,565 |
| Sin arriendo imputado (D3) | 38,8 % | 17,3 % | 16,8 % | 0,564 |
| Arriendo imputado solo a propietarios (D3) | 35,3 % | 15,1 % | 14,3 % | 0,571 |
| Ganancia rural `P550` ÷ 12 (D4) | 34,0 % | 14,1 % | 13,3 % | 0,569 |
| Con cesantías y accidentes (D5) | 33,2 % | 13,5 % | 12,5 % | 0,566 |

## Cómo leerlo

- **La reconstrucción queda a 1,4 puntos de la cifra oficial** en lo
  nacional (antes, ≈39 %) y por debajo de ella en lo rural (−1,2). La
  diferencia restante es de esperar: el DANE suma ayudas registradas en
  administrativos que la encuesta subdeclara.
- **La decisión que más pesa es el arriendo imputado** (5,6 puntos). La
  ficha metodológica del DANE (catálogo 874) confirma que se imputa a
  propietarios y usufructuarios, por eso está en la base.
- **La imputación de no respuesta laboral importa poco** (hot-deck vs.
  caso completo: 0,4 puntos). Ponerla en cero sesga hacia más pobreza
  (+1,7).
- Los códigos 11 y 12 de `P6050` y las cesantías no mueven las tasas.
- El Gini queda 0,01-0,02 por encima del oficial en todos los dominios:
  la reconstrucción no corrige ingresos atípicos ni "falsos ceros" fuera
  del ingreso laboral.

## Qué corrigió frente a la versión anterior (`3b`, hasta el 2026-11-02)

| Antes | Ahora |
|---|---|
| Hogar completo | Unidad de gasto (sin servicio doméstico, `P6050` = 10) |
| Tasas por hogar | Tasas por persona |
| Dos líneas (cabecera, rural) | Tres líneas de dominio |
| Incluía ingresos ocasionales | Los excluye |
| Omitía extras, primas anuales, auxilios y especie de independientes | Los suma si no están en `INGLABO` |
| `INGLABO` vacío = 0 y código 98 = $98 | Hot-deck para el laboral; 98/99 no cuentan como monto |
| Sin arriendo imputado | Con arriendo imputado |
| FGT0 37,6 % | FGT0 33,2 % |

Durante la construcción apareció un error de la auditoría: `P6430` = 7 es
**jornalero o peón** (el 99 % declara salario), no un trabajador sin
remuneración. Los números de `P6430` no siguen el orden de las letras del
diccionario, igual que pasa con `P6050`. Sin remuneración son el 6 y el 8.

## En la muestra de estimación

`src/3b_preprocesamiento_monetario.py` pega el escenario base a
`muestra_estimacion_2024.parquet` (290.968 hogares, todos con ingreso
reconstruido). A nivel de hogar, ponderado por `fex`: 27,0 % de hogares
pobres y 10,4 % en pobreza extrema (es menor que la tasa por personas
porque los hogares pobres son más grandes).

Resultados causales con este outcome: `DIAGNOSTICO_W_CELDA_EXACTA.md`
(ATE ≈0, placebo) y `RESULTADOS_FRECHET_MANSKI.md` (cotas
[−0,538; +0,503]).

## Pendiente

- **D1:** la base anonimizada oficial existe (catálogo 874,
  `BDatos-Pobreza_Monetaria_Desigualdad-2024.zip`). Hay que descargarla a
  mano y guardarla en `data/0_raw/pobreza_monetaria/`. Si trae las llaves
  de GEIH, reemplaza esta reconstrucción como referencia hogar por hogar.
- **D7, versión A:** líneas por área (23 ciudades) de los anexos
  estadísticos del boletín.
- Comparación con IPM-GEIH y el grupo Sisbén imputado (Fase 5), **por
  celda** (D6): con el Hot-Deck no se pueden medir errores de inclusión o
  exclusión hogar por hogar.

## Cómo reproducirlo

```bash
PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.indicadores.pobreza_monetaria_geih
poetry run python src/3b_preprocesamiento_monetario.py
poetry run pytest tests/test_preprocesamiento_monetario.py
```

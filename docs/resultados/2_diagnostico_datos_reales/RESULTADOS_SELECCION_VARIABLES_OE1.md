# Resultados — Selección de variables: LASSO, Ridge y SHAP (OE1)

Generado 2026-11-02 por `src/diagnostico/seleccion_variables_lasso_shap.py`;
regenerado el 2026-11-22 con el número de menores (la celda del Hot-Deck lo
usa desde el 2026-11-14) y la muestra ponderada por el `fex` del Sisbén.
Salidas: `docs/reports/seleccion_variables_lasso_ridge_shap.txt` (consola),
`seleccion_variables_lasso_ridge_shap.csv` (importancia combinada),
`seleccion_variables_metricas_por_clase.csv` (por grupo) y
`seleccion_variables_shap_ab.csv` (valores SHAP de la figura). Figuras:
`docs/anexos_tesis/figuras/fig_importancia_variables_oe1.png` y
`fig_shap_oe1.png`.

## Qué es

Responde al objetivo específico 1: qué características del hogar se asocian
con el grupo (A-D) que asigna el Sisbén. **No es inferencia causal**: es
importancia de variables para predecir la clasificación. Tres métodos, para
no depender de uno:

- **LASSO** (logística multinomial con L1, `LogisticRegressionCV`): ordena
  las variables y puede llevar coeficientes a 0.
- **Ridge** (la misma regresión con L2): no elimina nada; si coincide con
  LASSO, la señal es estable.
- **SHAP** sobre un bosque aleatorio: importancia no lineal y con
  interacciones, hogar por hogar.

## Cómo se usa aquí

- **Resultado:** `Grupo` (A/B/C/D) del Sisbén IV nacional y de Bogotá
  (3.093.411 hogares con las 11 variables completas).
- **Predictores:** las variables canónicas comunes a las fuentes, sin las
  privaciones `I1`-`I15`/`H_5` (redescubrirían la fórmula del Sisbén).
  Numéricas: personas, **menores** (desde el 2026-11-22), cuartos y ciclo
  de vida del jefe. Categóricas, en one-hot (su orden no se asume): paredes,
  pisos, alcantarillado, acueducto, sexo del jefe y zona. Control
  geográfico: departamento (33 categorías), reportado aparte.
- **Muestra:** 150.000 hogares sorteados con probabilidad proporcional al
  `fex` (el Sisbén nacional es una muestra expandible; Bogotá trae 1), con
  reemplazo, después de separar los hogares en entrenamiento (70 %) y
  prueba (30 %) para que un hogar repetido no quede en los dos. La muestra
  reproduce la población: A 26,0 %, B 33,8 %, C 26,4 %, D 13,9 % (población
  expandida: 25,9 %, 33,7 %, 26,6 %, 13,9 %). Hasta el 2026-11-22 se
  estratificaba por grupo sin ponderar (A 23,4 %, B 30,4 %, C 29,7 %,
  D 16,5 %).

## Resultado

| Variable | LASSO | Ridge | SHAP (bosque) | Promedio normalizado |
|---|---|---|---|---|
| Departamento (control) | 1,000 | 1,000 | 0,306 | 0,769 |
| Material de pisos | 0,303 | 0,322 | 1,000 | 0,542 |
| Menores del hogar | 0,085 | 0,079 | 0,597 | 0,254 |
| Alcantarillado | 0,034 | 0,031 | 0,391 | 0,152 |
| Material de paredes | 0,076 | 0,079 | 0,211 | 0,122 |
| Personas del hogar | 0,014 | 0,018 | 0,304 | 0,112 |
| Cuartos | 0,024 | 0,022 | 0,247 | 0,098 |
| Sexo del jefe | 0,037 | 0,035 | 0,216 | 0,096 |
| Acueducto | 0,008 | 0,008 | 0,171 | 0,063 |
| Zona | 0,034 | 0,035 | 0,052 | 0,040 |
| Ciclo de vida del jefe | 0,013 | 0,012 | 0,060 | 0,028 |

Importancia normalizada dentro de cada método (1 = la mayor). Correlación de
Spearman entre rankings: LASSO-Ridge 0,96; LASSO-SHAP 0,64; Ridge-SHAP 0,47.
Ninguna variable queda eliminada por LASSO.

**Efecto sobre la probabilidad de A/B (SHAP, media del valor absoluto):**
pisos 0,125; menores 0,076; alcantarillado 0,056; cuartos 0,036;
departamento 0,032; sexo del jefe 0,028; personas 0,028; paredes 0,027;
acueducto 0,025; ciclo de vida 0,007; zona 0,006. En la figura SHAP, un piso
de tierra sube la probabilidad de A/B hasta en 0,20 y un piso con acabado la
baja en cerca de 0,19; más menores y menos cuartos la suben; la jefatura
femenina la sube en ≈0,03.

| Modelo | Exactitud | F1 macro |
|---|---|---|
| LASSO | 0,547 | 0,536 |
| Ridge | 0,547 | 0,536 |
| Bosque aleatorio (base de SHAP) | 0,546 | 0,521 |
| Línea base (siempre B) | 0,337 | — |

## Rendimiento por grupo, confusión y calibración

| Grupo | LASSO: precisión / sensibilidad | Bosque: precisión / sensibilidad |
|---|---|---|
| A | 0,67 / 0,62 | 0,65 / 0,67 |
| B | 0,50 / 0,61 | 0,50 / 0,63 |
| C | 0,51 / 0,46 | 0,51 / 0,46 |
| D | 0,55 / **0,41** | 0,61 / **0,29** |

Los errores caen en el grupo vecino: con LASSO, el 35 % de los hogares A se
predicen B y el 38 % de los D se predicen C; de A a D, el 0,1 %. La
probabilidad media predicha coincide con la tasa de cada grupo (A: 0,260
frente a 0,261) y el Brier va de 0,09 (D) a 0,20 (B): bien calibrados en
promedio; el problema es separar grupos vecinos.

**Partición por municipio** (ningún municipio en entrenamiento y prueba,
bosque aleatorio): F1 macro de 0,521 a 0,502 y sensibilidad de D de 0,29 a
0,27. Parte del rendimiento viene de reconocer patrones locales.

## Cómo leerlo

- **El material de pisos es la variable sustantiva más importante** en los
  tres métodos (el departamento es un control: suma 33 columnas en los
  modelos lineales, por eso domina allí y no en SHAP).
- **El número de menores es la segunda**, por encima de las demás de
  vivienda. Entró a la celda del Hot-Deck el 2026-11-14 por la misma razón.
- **SHAP reordena el tercio medio:** personas, alcantarillado y cuartos
  pesan más en el bosque que en los modelos lineales; sugieren
  interacciones que la logística no capta. Por eso se corren los tres.
- **Exactitud de ≈55 % frente a 34 % de la línea base:** las variables
  comunes explican una parte real pero parcial de la clasificación; el
  resto está en lo que el Sisbén recoge y aquí no se usa.
- Se predice el grupo **asignado** por el Sisbén, no la pobreza: la
  correspondencia con la pobreza monetaria está en la celda (correlación de
  0,41 entre P(A/B | celda) y la pobreza, `RESULTADOS_HOTDECK.md`) y en las
  cotas de los errores (`RESULTADOS_ERRORES_FOCALIZACION_FRECHET.md`).

## Limitaciones

- Solo usa el esquema canónico (11 variables); el Sisbén recoge muchas más.
- Códigos del Sisbén en one-hot dentro de una sola fuente; paredes y pisos
  están verificados con la ficha (`docs/insumos/HOMOLOGACION_VIVIENDA_GEIH_SISBEN.md`).
- Submuestra de 150.000 hogares por costo de cómputo.
- Bosque con hiperparámetros fijos (300 árboles, profundidad 10, hoja mínima
  20), sin búsqueda.
- No es causal: una variable que predice el grupo no dice qué haría la
  política (`RESULTADOS_DML_ATE_ATT_ATU.md`).

## Cómo reproducirlo

```bash
poetry run python -m src.diagnostico.seleccion_variables_lasso_shap
poetry run python -m src.utils.figuras_tesis
```

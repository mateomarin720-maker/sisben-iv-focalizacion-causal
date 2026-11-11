# Carpeta: src/estimacion

---

**Estado actual:** la corrida oficial vive en `src/3_preprocesamiento.py`
(outcome IPM-GEIH reducido) y `src/5_estimacion.py` (ATE/ATT/ATU vía
`LinearDML`, CATE vía `CausalForestDML`), sobre el Hot-Deck con
`viv_cuartos` sumado a la celda. Resultados interpretados:
`docs/resultados/RESULTADOS_DML_ATE_ATT_ATU.md` y
`docs/resultados/RESULTADOS_CAUSALFOREST_CATE.md`.

Esta carpeta (`src/estimacion/`) contiene dos cosas distintas:
- La corrida de prueba del 21 de octubre (outcome provisional de empleo e
  ingreso laboral) se retiró del repositorio; queda en el historial de git. Su
  hallazgo, que el residuo no colapsaba con depto + edad, motivó sumar vivienda
  a la celda y construir el outcome real.
- `cotas_frechet_manski.py`: parte vigente del pipeline — cotas de
  robustez para el ATE que NO suponen independencia condicional (a
  diferencia del DML). Resultado: `docs/resultados/RESULTADOS_FRECHET_MANSKI.md`.
- `cotas_frechet_modelos.py`: una cota de Fréchet por cada parámetro de
  los modelos (ATE, ATT, ATU y CATE por subgrupo), en los cinco
  resultados, incluidos los continuos. Mismo documento de resultados.
- `errores_focalizacion_frechet.py`: errores de inclusión y exclusión del
  Sisbén con datos reales, como cotas de Fréchet por celda (nacional y
  por departamento). Resultado: `docs/resultados/RESULTADOS_ERRORES_FOCALIZACION_FRECHET.md`.
- `variables_candidatas_pobreza.py`: qué variables podría incorporar el
  Sisbén, con la pobreza de la GEIH como resultado. Predictivo, no causal.
  Resultado: `docs/resultados/RECOMENDACION_VARIABLES_POBREZA.md`.
- `incidencia_transferencias.py`: a quién llegan las ayudas declaradas en la
  GEIH, en hogares y personas. Descriptivo, no estima efectos.
- `seleccion_variables_lasso_shap.py`: parte vigente, pero de OE1, no del
  pipeline causal — LASSO/Ridge/SHAP sobre el Sisbén para ver qué
  variables del hogar predicen mejor el `Grupo` (A-D). No estima ningún
  efecto, es selección/importancia de variables. Resultado:
  `docs/resultados/RESULTADOS_SELECCION_VARIABLES_OE1.md`.

Lo que sigue documenta la corrida de prueba original, útil para entender
el razonamiento que llevó a la corrida oficial.

## Contenido

## Limitaciones (aplican a TODO lo que corre esta carpeta)

- El tratamiento es imputado por Hot-Deck, no observado — error de medición
  no aleatorio, concentrado cerca de fronteras entre grupos (ver
  "Consideraciones metodológicas" del documento de pipeline).
- No hay ajuste por diseño muestral de GEIH ni de Sisbén.
- El Sisbén solo cubre hogares inscritos — selección, no aleatoriedad.
- Falta DPS/RUI como confusores — el canal `elegibilidad -> participación
  DPS -> resultado` de la Figura 2 no tiene datos todavía (`dps`, estado
  `pendiente` en `data/catalogo.yaml`).
- `geo_zona`, `jefe_sexo`, `viv_paredes`, `viv_pisos` no están verificados
  contra la ficha oficial de cada fuente.

## Uso

```bash
poetry run python -m src.estimacion.cotas_frechet_manski
poetry run python -m src.estimacion.cotas_frechet_modelos
poetry run python -m src.estimacion.errores_focalizacion_frechet
poetry run python -m src.estimacion.seleccion_variables_lasso_shap
```

Requiere `econml>=0.17`, `shap>=0.51` y `scikit-learn>=1.9` (ver
`pyproject.toml`; `poetry.lock` ya está regenerado con estas versiones).

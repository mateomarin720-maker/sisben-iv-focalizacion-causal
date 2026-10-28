# Carpeta: src/estimacion

---

**Estado actual:** la corrida oficial vive en `src/3_preprocesamiento.py`
(outcome IPM-GEIH reducido) y `src/5_estimacion.py` (ATE/ATT/ATU vía
`LinearDML`, CATE vía `CausalForestDML`), sobre el Hot-Deck con
`viv_cuartos` sumado a la celda. Resultados interpretados:
`docs/resultados/RESULTADOS_DML_ATE_ATT_ATU.md` y
`docs/resultados/RESULTADOS_CAUSALFOREST_CATE.md`.

Esta carpeta (`src/estimacion/`) contiene dos cosas distintas:
- `preparar_outcome_prueba_empleo.py` + `prueba_ate_att_cate.py`: la
  corrida de prueba que precedió a la oficial — el outcome de
  empleo/ingreso de abajo NO es el oficial. Queda como registro: el
  hallazgo de que el residuo no colapsaba con depto+edad fue lo que
  motivó sumar vivienda a la celda y construir el outcome real.
- `cotas_frechet_manski.py`: parte vigente del pipeline — cotas de
  robustez para el ATE que NO suponen independencia condicional (a
  diferencia del DML). Resultado: `docs/resultados/RESULTADOS_FRECHET_MANSKI.md`.

Lo que sigue documenta la corrida de prueba original, útil para entender
el razonamiento que llevó a la corrida oficial.

## Contenido

- **`preparar_outcome_prueba_empleo.py`**
  Construye un outcome **provisional** (empleo e ingreso laboral del jefe
  de hogar) cruzando `caracteristicas_generales` + `ocupados` de GEIH mes a
  mes, porque el dataset fusionado del Hot-Deck (`geih_sisben_fusionado_2024.parquet`)
  no trae ningún outcome todavía. **No es el outcome oficial** del
  anteproyecto (ingreso per cápita / IPM / seguridad alimentaria) — es lo
  más simple que se puede derivar de los módulos crudos ya disponibles.
  Salida: `data/2_models/muestra_estimacion_prueba.parquet`.

- **`prueba_ate_att_cate.py`**
  Corre `LinearDML` (ATE), `LinearDRLearner` (ATT) y `CausalForestDML`
  (CATE) de `econml`, con `T = 1{Grupo_hotdeck ∈ {A,B}}` (elegibilidad A/B,
  igual que en el diseño principal del documento de pipeline). Cada modelo
  se corre **dos veces**: (a) controlando solo por `geo_zona`, `jefe_sexo`
  y vivienda; (b) agregando `geo_depto` + `jefe_edad` — la celda misma del
  Hot-Deck — como chequeo de validez: si el efecto de (a) no colapsa en
  (b), es señal de que geografía/edad se cuela por una puerta de atrás, no
  de que el Hot-Deck tenga información real más allá de su celda. Salida:
  `docs/reports/prueba_ate_att_cate_salida.txt`.

## Resultados (2026-10-21) y su lectura

| Outcome | ATE (a) sin depto/edad | ATE (b) con depto/edad | ¿Colapsa? |
|---|---|---|---|
| Jefe ocupado (0/1) | +0,41 p.p. | +0,02 p.p. | Sí |
| log(ingreso laboral) | -6,56 % | -2,30 % (IC excluye 0) | No del todo |

El residuo de -2,3 % en ingreso **no es una señal causal real todavía** —
el diseño principal (Figura 2 del documento de pipeline) define X como
`depto + edad + vivienda`, pero el Hot-Deck implementado solo arma la celda
con `depto + edad`. La prueba (b) controla por el X *implementado*, no por
el X *completo* que pide el diseño — por eso el residuo aparece justo en
las variables de vivienda (`viv_cuartos`, `viv_paredes`, las de mayor
importancia en el Causal Forest). Ver el análisis formal de d-separación en
`docs/resultados/IDENTIFICACION_CAUSAL.md`.

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
poetry run python -m src.estimacion.preparar_outcome_prueba_empleo
poetry run python -m src.estimacion.prueba_ate_att_cate
```

Requiere `econml>=0.17`, `shap>=0.51` y `scikit-learn>=1.9` (ver
`pyproject.toml`; `poetry.lock` ya está regenerado con estas versiones).

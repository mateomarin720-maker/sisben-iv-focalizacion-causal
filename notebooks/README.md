# Carpeta: notebooks
---
Cuadernos de Jupyter para la exploración interactiva, el prototipado
del DAG causal y la validación de estimadores.

## Propósito y artefactos

### 1. Exploración y descubrimiento
- Carga inicial de fuentes (GEIH, Sisbén IV, IPM y, si se obtiene, DPS).
- Descripción por subpoblación (zona, jefatura y ciclo de vida del hogar).
- Validación de cobertura y calidad de variables candidatas a
  confusores.

### 2. Prototipado causal
- Construcción iterativa del DAG.
- Pruebas de identificación (backdoor; discontinuidad sobre la frontera
  ordinal B/C del Sisbén IV).
- Ensayos de estimadores (DML, Causal Forest).
- Refutación: placebo, random common cause, subset aleatorio,
  sensibilidad.

## Nomenclatura sugerida

- `01_exploracion_fuentes.ipynb`
- `02_calidad_variables_confusoras.ipynb`
- `03_prototipo_dag.ipynb`
- `04_oe1_determinantes_y_validez.ipynb` (LASSO/Ridge, SHAP, error de inclusión/exclusión)
- `05_oe2_dml_causal_forest.ipynb` (incluye contraste con la discontinuidad B/C)
- `06_oe3_reglas_focalizacion_fgt1.ipynb`

## Buenas prácticas

- Un cuaderno debe contar una historia coherente, de principio a fin.
- Cuando una función se estabilice, **refactorízala a un módulo dentro
  de `/src`** para hacerla reutilizable y testeable.
- No dejes rutas absolutas dentro del cuaderno; usa rutas relativas o
  el archivo `data/catalogo.yaml`.

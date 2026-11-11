# Carpeta `src/diagnostico/`: diagnóstico con datos reales

Análisis sobre la GEIH y el Sisbén reales. Como las fuentes no tienen
llave común, nada de esta carpeta estima el efecto causal del Sisbén:
acota lo que los datos permiten decir, mide la incertidumbre del
emparejamiento o predice (sin lenguaje causal). La estimación con DML y
Causal Forest está en `src/5_estimacion.py`, y es un placebo del
emparejamiento.

| Script | Qué responde | Resultado |
|---|---|---|
| `cotas_frechet_manski.py` | Cota del ATE sin suponer el vínculo del Hot-Deck, y con supuestos de monotonía | `docs/resultados/2_diagnostico_datos_reales/RESULTADOS_FRECHET_MANSKI.md` |
| `cotas_frechet_modelos.py` | Una cota por cada parámetro de los modelos (ATE, ATT, ATU, CATE por subgrupo), en los cinco resultados | Mismo documento |
| `errores_focalizacion_frechet.py` | Errores de inclusión y exclusión del Sisbén, como cotas por celda, nacional y por departamento | `docs/resultados/2_diagnostico_datos_reales/RESULTADOS_ERRORES_FOCALIZACION_FRECHET.md` |
| `variabilidad_hotdeck.py` | Cuánto cambia un resultado al repetir el sorteo del Hot-Deck; combinación con reglas de Rubin | `docs/resultados/1_datos_y_enlace/RESULTADOS_VARIABILIDAD_HOTDECK.md` |
| `seleccion_variables_lasso_shap.py` | Qué variables del hogar predicen el grupo del Sisbén (OE1). Predice la clasificación, no la pobreza | `docs/resultados/2_diagnostico_datos_reales/RESULTADOS_SELECCION_VARIABLES_OE1.md` |
| `variables_candidatas_pobreza.py` | Qué variables, fuera del Sisbén, ayudan a identificar la pobreza de la GEIH | `docs/resultados/2_diagnostico_datos_reales/RECOMENDACION_VARIABLES_POBREZA.md` |
| `incidencia_transferencias.py` | A quién llegan las ayudas declaradas en la GEIH. Descriptivo | Mismo documento |

## Supuestos y limitaciones comunes

- El grupo del Sisbén se observa solo en los hogares registrados. Usar
  su proporción por celda como la de toda la celda es un supuesto
  (`IDENTIFICACION_CAUSAL.md`, diagrama de fusión de fuentes).
- La participación en programas no se observa: el canal elegibilidad →
  participación → resultado no tiene datos en el proyecto.
- `P(Y | celda)` de la GEIH se pondera con el factor de expansión;
  `P(T | celda)` del Sisbén, que es un registro y no una muestra, no.

## Uso

```bash
PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.diagnostico.cotas_frechet_manski
PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.diagnostico.cotas_frechet_modelos
PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.diagnostico.errores_focalizacion_frechet
PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.diagnostico.variabilidad_hotdeck 2
PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.diagnostico.seleccion_variables_lasso_shap
PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.diagnostico.variables_candidatas_pobreza 6
PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.diagnostico.incidencia_transferencias
```

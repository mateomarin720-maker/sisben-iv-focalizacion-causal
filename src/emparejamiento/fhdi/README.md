# Imputación fraccional (FHDI) sobre la celda del Hot-Deck

Alternativa al sorteo de un donante del Hot-Deck, **sin modificarlo**: la
carpeta importa la celda y la cadena de respaldos de
`emparejamiento_hotdeck_geih_sisben.py` y monta encima las reglas de la
imputación fraccional (*fractional hot-deck imputation*, Kim y Fuller,
2004). El Hot-Deck sigue siendo el enlace del pipeline; esta carpeta es un
módulo adicional que lo reutiliza.

## Qué cambia frente al Hot-Deck

| | Hot-Deck | FHDI |
|---|---|---|
| Celda y cadena de respaldos | Departamento, ciclo de vida, cuartos, pisos, personas, menores; 7 niveles | **Las mismas** (`claves_por_nivel`) |
| Donantes por hogar | 1, sorteado | 10, sorteados sin reemplazo y estratificados por grupo |
| Lo que recibe el hogar | Un grupo (A, B, C o D) | Una probabilidad de cada grupo |
| Ruido del sorteo | Sí: 47-53 % de la varianza de un contraste (100 sorteos y Rubin) | No: los pesos calibrados reproducen la distribución de la celda |
| Varianza | Reglas de Rubin sobre repeticiones | Jackknife en una sola corrida |

## Reglas (`reglas.py`)

1. **Nivel.** Cada hogar usa el primer nivel de la cadena con donantes
   (celda exacta → sin menores → sin personas → sin pisos → departamento y
   edad → departamento → todo el registro), igual que el Hot-Deck.
2. **Donantes.** M = 10 por hogar, sin reemplazo en esa celda,
   **estratificados por grupo**: uno de cada grupo presente en la celda y
   el resto según su proporción (mayores restos). Con un sorteo simple, en
   unos 4 de cada 10 hogares algún grupo poco frecuente no salía y la
   calibración no era exacta.
3. **Pesos.** Suman 1 por hogar y se calibran a la proporción de cada
   grupo en la celda, π_g: w_j = π_g(j) / n_g(j). Así la distribución por
   grupo de cada hogar es exactamente la de su celda.
4. **FEFI.** Todos los donantes de la celda: equivale a darle a cada hogar
   π de su celda. Con la calibración, la FHDI con 10 donantes da lo mismo
   que FEFI en toda cantidad que dependa del grupo.

## Qué no cambia

La FHDI no hace más exacto el enlace hogar por hogar: sin llave común, la
única información sobre el grupo de un hogar de la GEIH es su celda, y
ningún método que la use acierta más que la moda de la celda (78,2 % en
A/B dentro del Sisbén, frente a 70,9 % del sorteo). Tampoco cambia la
identificación: el contraste de grupos con efectos fijos de celda es 0
exacto (Proposición 1) y las cotas de Fréchet son las mismas. Lo que
cambia es que cada hogar lleva cuánto se sabe de su grupo, sin ruido.

## Archivos

| Archivo | Qué hace |
|---|---|
| `reglas.py` | Nivel de la cadena, donantes fraccionales calibrados, FEFI y contraste placebo con pesos |
| `varianza.py` | Jackknife de grupos eliminados para razones ponderadas |
| `validacion.py` | Acierto del enlace dentro del Sisbén (20 % de hogares con el grupo escondido): sorteo, moda, FHDI, FEFI |
| `enlace.py` | Paso del pipeline: guarda por hogar la probabilidad de cada grupo (`data/2_models/geih_sisben_fhdi_2024.parquet`) y la publica en Azure |
| `__main__.py` | Corrida con el banco de Azure (en memoria) y comparación con el Hot-Deck |

## Uso

```bash
PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.emparejamiento.fhdi > docs/reports/fhdi.txt 2>&1
```

Lee `2_models/muestra_estimacion_monetaria_2024.parquet` y
`2_models/sisben_estandarizado_2024_con_bogota.parquet` de Azure, y los
reportes de `variabilidad_hotdeck` y `errores_focalizacion_frechet` de
`docs/reports/`. Tarda unos 4 minutos. Salidas: `docs/reports/fhdi.txt`,
`fhdi_validacion.csv`, `fhdi_comparacion.csv`, `fhdi_placebo.csv`.
Resultados: `docs/resultados/1_datos_y_enlace/RESULTADOS_FHDI.md`.
Pruebas: `tests/test_fhdi.py`. Metodología completa, decisiones y plan por fases:
`docs/metodologia/METODOLOGIA_FHDI.md`.

El enlace por hogar se genera aparte:

```bash
PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.emparejamiento.fhdi.enlace --publicar
```

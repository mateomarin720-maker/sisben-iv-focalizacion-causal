# Carpeta `docs/anexos_tesis/`: apoyo al documento escrito

Material para las correcciones del documento final (guía de correcciones
del 10 de noviembre de 2026). Lo que es tabla o cifra se genera del
repositorio, así que no puede diferir de él.

| Archivo | Qué es | Cómo se regenera |
|---|---|---|
| [`ANEXO_TRAZABILIDAD.md`](ANEXO_TRAZABILIDAD.md) | Cada cifra de la tesis con el archivo de `docs/reports/` del que sale y el comando que lo produce | `python -m src.utils.anexo_trazabilidad` |
| [`CONTRATO_DATOS.md`](CONTRATO_DATOS.md) | Columnas, tipos y dominios que exige el módulo de simulación | `python -m src.utils.anexo_trazabilidad` (sale de `src/simulacion/contrato.py`) |
| [`PROPOSICIONES.md`](PROPOSICIONES.md) | Proposiciones 1 a 3 del enlace por celdas, con prueba, y la derivación del ancho de la cota de la sección 4.4 (1 + 2Δ = 1,40) | A mano; la comprobación numérica sale de `python -m src.diagnostico.proposiciones` |
| [`DECLARACION_USO_IA.md`](DECLARACION_USO_IA.md) | Uso del asistente de programación en el repositorio: en qué se usó, qué no hizo y qué controles lo respaldan | A mano |
| [`METODO_PREDICTIVO.md`](METODO_PREDICTIVO.md) | Modelo base, partición y factores de expansión de la recomendación de variables y de las reglas de focalización (Tabla 5) | A mano |
| [`BIBLIOGRAFIA_VERIFICADA.md`](BIBLIOGRAFIA_VERIFICADA.md) | Referencias verificadas, con DOI donde existe, y las que hay que retirar | A mano |
| [`figuras/`](figuras/) | Figuras para el documento (ver abajo) | `python -m src.utils.figuras_tesis` |

## Figuras

| Figura | Qué muestra | Fuente |
|---|---|---|
| `fig_arquitectura.png` | Flujo de datos y los tres componentes | Estructura del repositorio |
| `fig_cotas_por_celda.png` | Cota de Fréchet del efecto en pobreza monetaria, celda por celda, frente al IC del DML | `cotas_frechet_manski_pobre_monetario.csv`, `estimacion_ate_att_atu_cate.txt` |
| `fig_errores_por_departamento.png` | Cotas del error de exclusión por departamento y nacional | `errores_focalizacion_frechet.csv` |
| `fig_atenuacion.png` | La estimación\* cae en proporción a los hogares mal vinculados (Proposición 2) | `simulacion_semisintetica_resumen.csv` |
| `fig_estabilidad_hotdeck.png` | Por celda, la proporción A/B imputada reproduce la de los donantes; por hogar, dos sorteos coinciden en A/B el 62,7 % de las veces | `variabilidad_hotdeck_celdas.csv`, `variabilidad_hotdeck.txt` |
| `fig_importancia_variables_oe1.png` | Importancia de cada variable para predecir el grupo del Sisbén con LASSO, Ridge y SHAP (OE1) | `seleccion_variables_lasso_ridge_shap.csv` |
| `fig_dag_ignorabilidad.png` | DAG de la ignorabilidad condicional: el grupo imputado es independiente de Y dada la celda; la elegibilidad real no, por U. Formato APA, 300 dpi; número, título y nota en [`FIGURA_DAG_IGNORABILIDAD.md`](FIGURA_DAG_IGNORABILIDAD.md) | Grafo del módulo (sin datos); afirmaciones comprobadas con d-separación al generarla |
| `fig_propension_celda.png` | Propensión estimada frente a la empírica por celda, con la celda como indicadoras y como número | Muestra de estimación (`data/2_models/`, no versionada) |

Los DAG están en `docs/resultados/2_diagnostico_datos_reales/` y la
convergencia de la simulación en `docs/resultados/3_simulacion/`.

\* Resultado simulado.

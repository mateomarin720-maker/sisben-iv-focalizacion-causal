# Carpeta `docs/anexos_tesis/`: apoyo al documento escrito

Material para las correcciones del documento final (guía de correcciones
del 10 de noviembre de 2026). Lo que es tabla o cifra se genera del
repositorio, así que no puede diferir de él.

| Archivo | Qué es | Cómo se regenera |
|---|---|---|
| [`ANEXO_TRAZABILIDAD.md`](ANEXO_TRAZABILIDAD.md) | Cada cifra de la tesis con el archivo de `docs/reports/` del que sale y el comando que lo produce | `python -m src.utils.anexo_trazabilidad` |
| [`CONTRATO_DATOS.md`](CONTRATO_DATOS.md) | Columnas, tipos y dominios que exige el módulo de simulación | `python -m src.utils.anexo_trazabilidad` (sale de `src/simulacion/contrato.py`) |
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
| `fig_propension_celda.png` | Propensión estimada frente a la empírica por celda, con la celda como indicadoras y como número | Muestra de estimación (`data/2_models/`, no versionada) |

Los DAG están en `docs/resultados/2_diagnostico_datos_reales/` y la
convergencia de la simulación en `docs/resultados/3_simulacion/`.

\* Resultado simulado.

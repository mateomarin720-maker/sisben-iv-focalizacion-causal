# Resumen de Avances — Efecto Causal del Sisbén IV

Última actualización: 2026-11-11 | Rama de trabajo `main`.
Seguimiento consolidado para revisión: [`README.md`](README.md).
**Guía vigente de la tesis (enfoque del tutor y prioridades):**
[`SEGUIMIENTO_TESIS_2026-11-04.md`](SEGUIMIENTO_TESIS_2026-11-04.md).

**Versión consolidada.** Este documento se reescribió el 2026-11-02 para
que conviva una sola versión metodológica. Las cifras de corridas
anteriores, con sus errores, quedan en el historial de
`CHANGELOG_PENDIENTES.md` y en git, no aquí.

## 0. Estado en una frase

Las fuentes están integradas y los outcomes construidos (IPM-GEIH y
pobreza monetaria reconstruida, a 1,4 puntos de la cifra oficial y con
la misma clasificación que el DANE en el 93,9 % de los hogares). La
celda del Hot-Deck incluye pisos desde el 2026-11-02. Con
datos reales, el DML sobre el grupo Sisbén imputado da ≈0, que es lo
esperado: el Hot-Deck sortea al azar dentro de la celda y el contraste
es un placebo. Las cotas de Fréchet-Manski no fijan ni el signo del
efecto. **La evaluación semisintética** (guía del tutor del 2026-10-27)
corrió hasta la convergencia (432 repeticiones): con hogares reales y
efecto conocido, el Hot-Deck lleva cualquier estimación a ≈0, y solo una
discontinuidad con puntaje continuo y vínculo hogar por hogar recupera
el efecto cuando hay confusión no observada
(`docs/resultados/3_simulacion/SIMULACION_SEMISINTETICA.md`).

## 1. Fuentes de datos

| Fuente | Estado | Detalle |
|---|---|---|
| **IPM (DANE)** | ✅ 2024 | 77.568 hogares nacional / 85.387 departamental. |
| **GEIH (DANE)** | ✅ 12 meses | 290.968 hogares, 8 módulos por mes. Agosto se carga desde `.DTA` con el mismo formato de texto que el CSV. |
| **Sisbén IV nacional (DNP-ANDA)** | ✅ | 1.833.166 hogares, 1.098 municipios, corte mayo 2024. |
| **Sisbén IV Bogotá (SDP)** | ✅ | Registro continuo; se usan los vigentes al 31-dic-2024 (1.274.578 de 1.458.468). Reemplaza al municipio 11001 del nacional. |
| **Pobreza monetaria oficial (DANE, catálogo 874)** | ✅ 2026-11-02 | 275.057 hogares con llaves de GEIH, en `data/0_raw/pobreza_monetaria/` y Azure. 24 departamentos y Bogotá (sin los 9 nuevos). |
| **Víctimas MPMD (DANE, catálogo 874)** | ✅ 2026-11-02 | Marca de víctima y desplazado por persona con llaves de GEIH (`data/0_raw/victimas_mpmd/`). Sin usar todavía. |
| **Banco de datos** | ✅ Azure Blob Storage | `src/utils/publicar_banco_datos_azure.py` / `restaurar_banco_datos_azure.py`. |

## 2. Pipeline

| Etapa | Script | Estado |
|---|---|---|
| Ingesta, limpieza, armonización | `src/1_integracion.py`, `src/ingesta/`, `src/2_limpieza.py`, `src/armonizacion/` | ✅ |
| Hot-Deck GEIH ← Sisbén | `src/emparejamiento/emparejamiento_hotdeck_geih_sisben.py` | ✅ celda depto + ciclo de vida + cuartos + pisos |
| Comparación de celdas con pisos y paredes | `src/validacion/comparar_celdas_hotdeck_vivienda.py` | ✅ 2026-11-02 |
| DAG e identificación | `src/4_dag_identificacion.py` | ✅ |
| Outcome IPM-GEIH (8 de 15 privaciones) | `src/3_preprocesamiento.py` | ✅ |
| Outcome pobreza monetaria | `src/indicadores/pobreza_monetaria_geih.py` → `src/3b_preprocesamiento_monetario.py` | ✅ 2026-11-02 |
| Contraste con la base oficial | `src/validacion/comparar_pobreza_monetaria_oficial.py` | ✅ 2026-11-02 |
| DML y Causal Forest (diagnóstico placebo) | `src/5_estimacion.py` | ✅ corregido 2026-11-02 |
| Cotas de Fréchet-Manski | `src/diagnostico/cotas_frechet_manski.py` | ✅ |
| Representatividad del Sisbén | `src/validacion/verificar_representatividad_sisben.py` | ✅ |
| Selección de variables (OE1) | `src/diagnostico/seleccion_variables_lasso_shap.py` | ✅ con métricas por grupo |
| Simulación de identificación | `src/simulacion/simulacion_identificacion.py` | ✅ (datos sintéticos) |
| **Evaluación semisintética** | `src/simulacion/` (módulo del framework; antes `src/validacion/simulacion_semisintetica.py`) | ✅ 2026-11-03, hasta la convergencia |
| **Reglas de focalización (OE3)** | `src/focalizacion/reglas_focalizacion.py` | ✅ 2026-11-04 (simulado) |
| Pruebas | `tests/` (`pytest`; mapa en `tests/README.md`) | ✅ 269 pruebas; 59 de 59 errores documentados detectados por mutación (2026-11-11); corren solas en GitHub Actions en cada push y PR (2026-11-04) |

## 3. Resultados vigentes

### 3a. Hot-Deck

290.968 hogares GEIH, 3.106.489 donantes. Celda: departamento + ciclo de
vida del jefe + tramo de cuartos + nivel de pisos homologado
(`docs/insumos/HOMOLOGACION_VIVIENDA_GEIH_SISBEN.md`); 99,98 % en celda
exacta (993 celdas). Grupo asignado (ponderado): **A 14,2 · B 29,4 · C
34,4 · D 22,0 %**. Refleja a los hogares registrados en el Sisbén, no a
la población; válido solo a nivel poblacional.

**Pisos entró a la celda el 2026-11-02.** La correlación entre
P(T | celda) y la pobreza monetaria del receptor sube de 0,20 a 0,29 sin
costo de cobertura; paredes no agrega nada encima y no entra. La celda
sin pisos (A 22,0 · D 15,6 %) queda como sensibilidad. Detalle:
`docs/resultados/1_datos_y_enlace/RESULTADOS_HOTDECK.md`.

### 3b. Outcomes

- **IPM-GEIH:** 8 de las 15 privaciones oficiales; 17,1 % de hogares con
  `POBRE_GEIH` (score ≥ 3). `docs/insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md`.
- **Pobreza monetaria reconstruida** (unidad de gasto, líneas por
  dominio, hot-deck de no respuesta laboral, arriendo imputado; D1-D7
  cerradas): **33,2 %** de personas pobres frente a 31,8 % oficial;
  rural 41,3 % frente a 42,5 %; extrema 12,5 % frente a 11,7 %. Es una
  reconstrucción experimental, no la medición oficial (el DANE usa
  registros administrativos no públicos). La decisión que más pesa es el
  arriendo imputado (5,6 puntos). **Contraste con la base oficial del
  DANE:** sobre los 275.057 hogares que mide (24 departamentos y Bogotá),
  la reconstrucción clasifica igual al 93,9 %, con razón mediana de
  ingreso 1,00; las líneas oficiales por área explican 0,6 de los 1,4
  puntos de diferencia. `docs/resultados/1_datos_y_enlace/RESULTADOS_POBREZA_MONETARIA.md`.

### 3c. DML y Causal Forest: diagnóstico placebo

Con las categóricas como indicadoras en los modelos auxiliares
(corregido 2026-11-02) y la celda con pisos, siete de los ocho ATE
incluyen el cero y todos son despreciables:

| Outcome | ATE, W = celda exacta [IC 95 %] |
|---|---|
| `ipm_geih_score` | −0,0021 [−0,0092; +0,0051] |
| `POBRE_GEIH` | −0,0026 [−0,0049; −0,0002] |
| `log_ingreso_percapita` | +0,0006 [−0,0128; +0,0141] |
| `POBRE_MONETARIO` | −0,0002 [−0,0036; +0,0033] |

Es lo que predice la simulación: dentro de la celda el grupo imputado no
depende del hogar receptor, así que el contraste da ≈0 sea cual sea el
efecto verdadero. **No es una estimación del efecto del Sisbén.** Los
efectos que se reportaban antes (+0,0235 en IPM y +0,0158 en pobreza
monetaria, con IC sin el 0, y la afirmación de que los monetarios eran
"la evidencia de robustez más fuerte") venían de pasar la celda como
número a la propensión. `docs/resultados/2_diagnostico_datos_reales/DIAGNOSTICO_W_CELDA_EXACTA.md`.

### 3d. Cotas de Fréchet-Manski: el resultado de identificación con datos reales

| Outcome | Cota del ATE sin suponer independencia condicional |
|---|---|
| `POBRE_GEIH` | [−0,261; +0,380] |
| `POBRE_MONETARIO` | [−0,418; +0,648] |

Ninguna de las 921 celdas excluye el cero. Sin el supuesto del
Hot-Deck, los datos no determinan ni el signo del efecto. No es un
fracaso del modelo: es lo que dos fuentes sin llave común permiten
decir. `docs/resultados/2_diagnostico_datos_reales/RESULTADOS_FRECHET_MANSKI.md`.

### 3e. Representatividad

La cobertura del Sisbén frente a GEIH, sobre el mismo marco, va de 4,8 % (Valle)
a 26,9 % (Boyacá) en el archivo nacional; 16,8 % en el agregado (corregido el
2026-11-11: en 9 departamentos la GEIH solo cubre la capital). `docs/resultados/1_datos_y_enlace/RESULTADOS_REPRESENTATIVIDAD_SISBEN.md`.

### 3f. Selección de variables (OE1)

LASSO, Ridge y SHAP sobre 150.000 hogares del Sisbén: `viv_pisos` es la
variable más importante en los tres métodos. Exactitud ≈53 % (línea base
30 %), bien calibrada, pero desigual por grupo: sensibilidad 0,64 en A y
0,39 (LASSO) o 0,22 (RandomForest) en D, que se confunde con C. Con
partición por municipio el F1 macro cae de 0,50 a 0,44. Predice el grupo
asignado, no la pobreza real. `docs/resultados/2_diagnostico_datos_reales/RESULTADOS_SELECCION_VARIABLES_OE1.md`.

## 4. Pendientes, en orden

0. **Variabilidad de la imputación del Hot-Deck hecha el 2026-11-04**
   (prioridad 1 de la guía; `docs/resultados/1_datos_y_enlace/RESULTADOS_VARIABILIDAD_HOTDECK.md`):
   inestable por hogar (34 % de coincidencia de grupo entre sorteos),
   estable en agregados (CV nacional ≤ 0,007). La mitad de la varianza de
   un contraste viene del sorteo: las estimaciones con el grupo imputado
   deberían repetir el sorteo y combinar con Rubin.
0. **OE3 hecho el 2026-11-04** (`docs/resultados/4_focalizacion/RESULTADOS_REGLAS_FOCALIZACION.md`):
   un proxy de medios logra 82-85 % de la reducción ideal de la brecha;
   las reglas con CATE estimado son peores (72 % con vínculo, 44 % con
   Hot-Deck). Siguiente: presupuestos menores que la población pobre y
   heterogeneidad más fuerte.

1. **Evaluación semisintética: hecha hasta la convergencia 2026-11-03**
   (432 repeticiones; outcome de pobreza, efecto nulo, tres niveles de
   confusión no observada y regla de corte con RD incluidos).
   **Sensibilidad hecha 2026-11-04**
   (`src/simulacion/sensibilidad_semisintetica.py`): la pérdida por
   integración es proporcional al tamaño del efecto; la RD difusa (80 %
   de participación) recupera el efecto en el corte con vínculo (0,086
   frente a 0,090); el sesgo de LinearDML viene de la regularización de
   los modelos auxiliares. **Decisión (2026-11-11):** se conserva la
   regularización del proyecto, de la que salen las cifras publicadas; la
   casi nula queda como sensibilidad. La cadena de respaldos del
   Hot-Deck simulado quedó en el código el 2026-11-04 (paso 4 del
   módulo); las cifras se regeneraron con ella y con asterisco el
   2026-11-08 (paso 5), sin cambios en las conclusiones.
2. ~~Decidir el outcome monetario~~ **Resuelto 2026-11-02:** la
   reconstrucción es el outcome principal (todo el país) y la
   clasificación oficial (`POBRE_MONETARIO_OFICIAL`, 24 departamentos y
   Bogotá) la prueba de robustez; las conclusiones no cambian. Los 9
   departamentos no están en la base oficial con ningún otro código.
   Cómo completarla si el DANE entrega esos datos:
   `docs/resultados/1_datos_y_enlace/RESULTADOS_POBREZA_MONETARIA.md`.
3. **Fase 5 de pobreza monetaria:** comparación con IPM-GEIH y el grupo
   imputado, por celda (D6).
4. ~~Angostar las cotas con supuestos de monotonía~~ **Hecho
   2026-11-04:** con selección monótona, respuesta monótona y dependencia
   positiva, la cota del ATE en pobreza monetaria pasa de [−0,571; +0,829]
   a [−0,405; 0]. El signo lo fija el supuesto, no los datos.
5. Construir las 5 privaciones del IPM que faltan en GEIH; refinar
   `sin_cotizacion_pension_jefe`.
6. Confirmar en ANDA los cortes de `PER002`; 6 hogares de Bogotá con doble
   jefe y 227 con `Clasificacion` distinta entre miembros (SDP).
7. Evaluar la marca de víctimas del DANE (`victimas_mpmd`) como
   covariable, en lugar del RUI.
8. Actualizar el anteproyecto con el enfoque vigente.
9. Pruebas: medir cobertura (`tests/README.md`, "Pendiente"). La
   integración continua corre desde el 2026-11-04.
10. **Entrega del repositorio y del documento** (anotaciones del director
    sobre el borrador, 2026-11-11; los demás puntos ya están en
    `docs/anexos_tesis/`):
    - Generar el DOI en Zenodo (requiere la cuenta de un autor): entrar a
      zenodo.org con GitHub, activar el repositorio en la configuración de
      GitHub de Zenodo (debe ser público), publicar una versión en GitHub
      (por ejemplo `v1.0.0`) y agregar el DOI que asigna Zenodo a
      `CITATION.cff` y al documento. Conviene agregar antes el `LICENSE`,
      porque Zenodo publica la licencia con el DOI.
    - Agregar el archivo `LICENSE`: `pyproject.toml` declara MIT, pero el
      archivo no existe. Lo deciden los autores.
    - Declaración de uso de IA: la del repositorio está en
      `docs/anexos_tesis/DECLARACION_USO_IA.md`. Falta la del documento
      escrito (redacción, traducción del resumen, corrección de estilo),
      que solo pueden declarar los autores.
    - Armar la tabla de peticiones a las entidades (sección 8.2). Cada
      petición va atada a un resultado y se verifican las normas que se
      citen. Las de la hoja de notas del director son:
      - GEIH y Sisbén enlazados con llave seudonimizada en sala segura
        (DANE y DNP): sin enlace, el efecto estimado es cero
        (Proposición 1).
      - Puntaje continuo del Sisbén IV (DNP): solo la RD resiste la
        confusión no observada.
      - Tasas y calidad del enlace del Registro Social de Hogares (DNP):
        la señal cae en proporción al enlace faltante (Proposición 2).
      - Pregunta sobre el grupo Sisbén en la GEIH o la ECV (DANE).
      - Tabulados oficiales de grupo Sisbén por pobreza, por celda (DANE
        y DNP): estrechan las cotas sin entregar microdatos.
      - Registros de pagos efectivos (DPS): distinguen ser elegible de
        recibir el programa.

## 5. Errores encontrados y corregidos (los que cambiaron resultados)

| Fecha | Error | Efecto |
|---|---|---|
| 2026-10-10 | Edad del Sisbén en códigos de ciclo de vida, no años | Cobertura del Hot-Deck 10,8 % → 100 % |
| 2026-10-28 | `viv_paredes`/`viv_pisos`/`viv_cuartos` leían columnas GEIH equivocadas | Cambió la celda, el IPM-GEIH y la estimación |
| 2026-10-28 | Dos privaciones tautológicas con `X` | Retiradas; IPM-GEIH en 8 de 15 |
| 2026-11-02 | Agosto cargado desde `.DTA` con códigos `"1.0"` | Corregido en el parser; pipeline regenerado |
| 2026-11-02 | `INGLABO` descrito como imputado por el DANE | Es un consolidado sin imputar |
| 2026-11-02 | Celda y departamento como números en la propensión del DML | Los ATE pasaron a ≈0 |
| 2026-11-02 | `P6430` = 7 leído como sin remuneración (es jornalero) | Corregido en la reconstrucción monetaria |

## 6. Gestiones institucionales

| Solicitud | Estado |
|---|---|
| Sisbén IV (DNP-ANDA) | Resuelto |
| Sisbén Bogotá (SDP) | Resuelto (corte 03/08/2026) |
| Puntaje continuo del Sisbén (para RD) | **No se solicita (decisión del 2026-11-04):** la réplica usa solo las fuentes ya disponibles. La falta del puntaje queda como limitación; es lo único que recuperaría el efecto en la simulación |

## 7. Documentación de referencia

- `docs/resultados/README.md` — índice de resultados (empezar aquí)
- `docs/metodologia/pobreza_monetaria/` — auditoría (`00`) y decisiones y diccionario del ingreso (`01`)
- `docs/insumos/HOMOLOGACION_VIVIENDA_GEIH_SISBEN.md` — paredes y pisos entre fuentes
- `docs/insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md` — IPM-GEIH
- `docs/insumos/DICCIONARIO_GEIH_2024.xlsx`, `DICCIONARIO_SISBEN_2024.xlsx`, `FICHA_SISBEN_IV_FCS_2017.pdf`
- `docs/seguimiento/CHANGELOG_PENDIENTES.md` — historial

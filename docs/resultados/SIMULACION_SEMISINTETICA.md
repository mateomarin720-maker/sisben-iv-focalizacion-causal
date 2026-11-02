# Evaluación semisintética: recuperación de un efecto conocido sobre hogares reales

Generado 2026-11-02 por `src/validacion/simulacion_semisintetica.py`
(50 repeticiones, encuesta de 30.000 hogares por repetición; Causal
Forest en 10). Salida completa: `docs/reports/simulacion_semisintetica.txt`;
tabla resumen: `docs/reports/simulacion_semisintetica_resumen.csv`; cada
repetición: `docs/reports/simulacion_semisintetica.csv`.

Es el componente central que pidió el tutor (2026-10-27) y que detalla la
revisión externa (§9, "arquitectura semisintética"). A diferencia de
`SIMULACION_IDENTIFICACION.md` (mundo 100 % sintético), **las covariables,
la celda del Hot-Deck y el ingreso son los de los 290.968 hogares reales
de GEIH 2024**; solo se simulan el tratamiento y el efecto, así que la
verdad se conoce hogar por hogar.

## Diseño

```text
DATOS REALES     celda del Hot-Deck (993), X = {zona, sexo del jefe, paredes},
                 Y0 = log(1 + ingreso per cápita de la UG)
GENERADOR        U = parte del ingreso que la celda y X no explican (real, no observable)
                 T verdadero ~ Bernoulli(score), score = logit P_Sisbén(T | celda) + X·b + gamma·U
                 tau(X) = 0,10 + 0,05·rural − 0,03·jefa + 0,04·paredes precarias  (ATE ≈ 0,095)
                 Y = Y0 + tau(X)·T
ESCENARIOS       aleatoria / confusión observada / confusión no observada leve (gamma = 0,25)
                 y fuerte (gamma = 1) / solapamiento débil (score × 4)
INTEGRACIÓN      oráculo (T verdadero) / vínculo parcial (50 % recibe T de un donante)
                 / Hot-Deck (todos lo reciben de un donante de su celda)
ESTIMADORES      diferencia de medias, regresión con efectos fijos de celda,
                 LinearDML y CausalForestDML (los mismos de 5_estimacion.py, W = celda)
EVALUACIÓN       sesgo, RMSE, cobertura del IC 95 %, ancho, error del CATE (PEHE),
                 degradación = RMSE con integración − RMSE con oráculo
```

- **P(T | celda) sale del Sisbén real**, así que la asignación observada
  tiene la forma del sistema (tasa de tratados 46,7 % en todos los
  escenarios, calibrada).
- En cada repetición la población se parte en dos muestras **sin llave
  común**: la "encuesta" (X, Y) y el "registro" (X, T), como GEIH y
  Sisbén. **El T verdadero de la encuesta solo se usa para medir**; los
  estimadores reciben únicamente el T observado según la integración.
- El efecto es sobre log-ingreso: 0,095 ≈ 10 % más ingreso. Con 30.000
  hogares el IC 95 % de un estimador bien especificado mide ≈0,08.
- Para usarlo con otra fuente (registros administrativos de una entidad)
  basta una tabla con las columnas de `COLUMNAS` en el script.

## Resultados (media de 50 repeticiones; ATE verdadero = 0,095)

**Estimación media del ATE** (entre paréntesis, cobertura del IC 95 %):

| Escenario | Integración | Dif. de medias | Regresión EF celda | LinearDML | Causal Forest |
|---|---|---|---|---|---|
| Aleatoria | Oráculo | 0,095 (0,92) | 0,094 (0,98) | 0,092 (0,94) | 0,095 (1,0) |
| | Vínculo 50 % | 0,045 (0,30) | 0,044 (0,20) | 0,044 (0,20) | 0,042 (1,0) |
| | Hot-Deck | −0,001 (0) | −0,001 (0) | −0,001 (0) | +0,002 (0,7) |
| Confusión observada | Oráculo | −0,318 (0) | 0,092 (1,0) | 0,090 (0,94) | 0,085 (1,0) |
| | Vínculo 50 % | −0,346 (0) | 0,046 (0,44) | 0,044 (0,38) | 0,049 (1,0) |
| | Hot-Deck | −0,373 (0) | −0,001 (0) | −0,005 (0,02) | −0,001 (0,6) |
| Confusión no observada leve | Oráculo | −0,615 (0) | −0,291 (0) | −0,292 (0) | −0,290 (0) |
| | Hot-Deck | −0,367 (0) | +0,001 (0) | −0,005 (0) | −0,009 (0,9) |
| Confusión no observada fuerte | Oráculo | −0,972 (0) | −0,771 (0) | −0,770 (0) | −0,776 (0) |
| | Hot-Deck | −0,340 (0) | −0,003 (0) | −0,002 (0) | −0,010 (0,8) |
| Solapamiento débil | Oráculo | −0,579 (0) | 0,062 (0,86) | 0,080 (0,88) | 0,078 (1,0) |
| | Vínculo 50 % | −0,578 (0) | 0,027 (0,52) | 0,031 (0,62) | 0,034 (1,0) |
| | Hot-Deck | −0,575 (0) | +0,001 (0,20) | −0,008 (0,28) | −0,011 (1,0) |

## Lectura

1. **Con el tratamiento verdadero, los estimadores ajustados funcionan
   mientras la confusión sea observable.** Con asignación aleatoria todos
   recuperan 0,095. Con confusión por la celda y X, la regresión con
   efectos fijos, el DML y el Causal Forest la recuperan (sesgo ≤ 0,01,
   cobertura 0,94-1,0) y la diferencia de medias no (−0,32: los tratados
   son más pobres). Con solapamiento débil siguen cerca pero pierden
   precisión (sesgo −0,015 a −0,033, cobertura 0,86-0,88).

2. **Si la asignación depende de algo que no se observa, ningún
   estimador lo corrige, ni con el tratamiento verdadero**: −0,29 con
   confusión leve y −0,77 con fuerte, cuando la verdad es +0,095 (el
   signo se invierte). Es lo que expresan las cotas de Fréchet-Manski
   con datos reales: sin supuestos, el signo no está identificado.

3. **Con el tratamiento reconstruido por Hot-Deck, todo estimador que
   controla la celda devuelve ≈0, en los cinco escenarios** (−0,011 a
   +0,002). El sesgo es −0,095 = −ATE: se pierde el efecto completo. El
   donante se sortea dentro de la celda, así que su T no tiene relación
   con el hogar receptor más allá de la celda. Es el mismo ≈0 que da
   `5_estimacion.py` con datos reales (`DIAGNOSTICO_W_CELDA_EXACTA.md`),
   ahora con el efecto verdadero conocido: **ese ≈0 no informa sobre el
   efecto del Sisbén**.

4. **La degradación es proporcional a la fracción de hogares mal
   vinculados.** Con la mitad del T de un donante, el ATE estimado cae a
   la mitad (0,044 de 0,095) en los escenarios donde el oráculo funciona.
   El Hot-Deck es el extremo: 100 % de donantes.

5. **Sin controlar la celda, el Hot-Deck traslada la confusión entre
   celdas** (diferencia de medias −0,37 con confusión observada): un
   efecto distinto de cero con Hot-Deck sin la celda es geografía y
   composición, no efecto.

6. **La concordancia entre el T imputado y el verdadero no mide la
   calidad para estimar efectos.** El Hot-Deck acierta el T del 50-61 %
   de los hogares (83 % con solapamiento débil), y aun así el efecto es
   ≈0: los aciertos vienen de la celda, que es justo lo que se controla.

7. **Con confusión no observada la "degradación" sale negativa** (el
   Hot-Deck tiene menor RMSE que el oráculo). No es una mejora: el
   Hot-Deck lleva cualquier estimación a ≈0, y 0 queda más cerca de
   +0,095 que el −0,77 del oráculo confundido. Se pierden por igual el
   efecto y el sesgo.

8. **Causal Forest:** su IC del ATE es 3-9 veces más ancho que el del
   DML (0,20-0,72), por eso cubre aun cuando estima ≈0 con Hot-Deck: es
   conservador, no más acertado. El error del CATE (PEHE 0,05-0,07 con
   oráculo sin confusión no observada) es mayor que la variación real
   del efecto entre hogares (desviación de tau = 0,028): con 30.000
   hogares y el ruido del ingreso real, no recupera la heterogeneidad.

## Qué significa para la tesis

- **El Hot-Deck sirve para describir a nivel de celda, no para estimar
  efectos causales a nivel de hogar.** La simulación lo muestra con
  hogares reales y efecto conocido, para los cuatro estimadores y en
  todos los escenarios.
- Para recuperar el efecto hace falta **vincular hogar por hogar**
  (llave común) **y** un diseño que resuelva la confusión no observada
  (discontinuidad con puntaje continuo, como en
  `SIMULACION_IDENTIFICACION.md`). Con vínculo parcial, el efecto se
  atenúa en proporción a los hogares mal vinculados.
- Mensaje para una entidad que integre sus propios registros: medir la
  fracción de hogares bien vinculados antes de estimar; la concordancia
  del tratamiento imputado no sirve como indicador.

## Limitaciones

- El efecto es sobre log-ingreso y aditivo; no se simuló un outcome
  binario de pobreza.
- U se construye con el residuo del propio ingreso: es una confusión no
  observada realista en forma, pero su fuerza (gamma) es un supuesto. Por
  eso se reportan dos niveles.
- Sin ajuste por diseño muestral; T sigue una logística de la celda y de
  tres variables de X.
- El Hot-Deck simulado sortea en la celda exacta (respaldo: todo el
  registro), sin la cadena completa de respaldos del pipeline; con 993
  celdas y ≈260.000 donantes por repetición casi nunca se usa el respaldo.
- Causal Forest en 10 repeticiones (su cobertura y PEHE son menos
  precisos que las demás cifras).

## Para reproducir

```bash
PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.validacion.simulacion_semisintetica 50 30000 10 > docs/reports/simulacion_semisintetica.txt 2>&1
poetry run pytest tests/test_simulacion_semisintetica.py
```

Tarda unos 15 minutos: ≈45 s por repetición con Causal Forest y ≈8 s
sin él. Requiere
`muestra_estimacion_monetaria_2024.parquet` y el Sisbén estandarizado.

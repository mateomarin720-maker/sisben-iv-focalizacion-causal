# ¿Sirve el CATE para focalizar si el efecto varía más? (heterogeneidad ampliada)

Generado el 2026-11-09 y vuelto a correr el 2026-11-14 (IPM-GEIH corregido y dos reglas de control) el 2026-11-15 (celda del Hot-Deck con personas y menores, 3.721 celdas) y el 2026-11-21 (presupuesto de 13.567 hogares por muestra, con los donantes del Sisbén ponderados por `fex`) por `src/focalizacion/heterogeneidad_ampliada.py`.
Salidas: `docs/reports/heterogeneidad_{ampliado,complejo}{.csv,_resumen.csv,_config.json}`
y `docs/reports/heterogeneidad_ampliada.txt`. **Todas las cifras de esta
página son simuladas (\*).**

## La pregunta

Las reglas de focalización (`RESULTADOS_REGLAS_FOCALIZACION.md`)
concluyen que ordenar a los hogares por el CATE estimado empeora la
focalización. Pero en ese diseño el efecto varía poco entre hogares
(desviación 0,028\*) y solo por tres variables. Una revisión externa
preguntó si la conclusión se sostiene con una heterogeneidad más amplia o
más compleja.

## Diseño

Mismos hogares, misma asignación, mismas reglas y mismos dos presupuestos
(mismo número de hogares y mismo dinero). Solo cambia el efecto
verdadero tau(X):

| Nivel | Modificadores del efecto | Desviación de tau |
|---|---|---|
| Básico (el de las reglas) | zona, jefatura femenina, paredes precarias | 0,028\* |
| Ampliado | los anteriores + bajo logro educativo del jefe, jefe sin cotización a pensión, hogar de 5 o más personas, jefe de 60 años o más, piso de tierra | 0,060\* |
| Complejo | el ampliado + interacción rural × bajo logro, efecto no lineal del tamaño del hogar y diferencias entre departamentos | 0,059\* |

- En los niveles nuevos, tau = 0,095 + 0,06 · h(X) estandarizado, con un
  piso de 0,005. La media es la del nivel básico y la desviación es más
  del doble.
- **El Causal Forest ve todos los modificadores** (incluido el
  departamento en el complejo). Es el caso más favorable para el CATE:
  si aquí no sirve, difícilmente sirve con modificadores que no se
  observan.
- Los modificadores son una decisión de diseño. Cambian el efecto, no la
  asignación ni la confusión (`SIMULACION_SEMISINTETICA.md`, tabla del
  papel de cada variable).
- 300 repeticiones por nivel, igual que el básico.

## Resultados

**Error del CATE por hogar (PEHE) frente a la variación real del efecto**

| Nivel | ATE estimado, T verdadero | ATE estimado, T por Hot-Deck | PEHE, T verdadero | Desviación de tau | PEHE / desviación |
|---|---|---|---|---|---|
| Básico | +0,038 a +0,061\* | −0,034 a −0,058\* | 0,084 a 0,098\* | 0,028\* | 3,0 a 3,5\* |
| Ampliado | +0,063 a +0,071\* | −0,021 a −0,030\* | 0,153 a 0,183\* | 0,060\* | 2,6 a 3,1\* |
| Complejo | +0,067 a +0,075\* | −0,019 a −0,027\* | 0,142 a 0,192\* | 0,059\* | 2,4 a 3,3\* |

Efecto verdadero: +0,095\* en promedio. Los rangos van del efecto
proporcional al de monto fijo. El ATE estimado queda por debajo del
verdadero aun con el T verdadero: es el sesgo de los modelos auxiliares
con la celda de 3.721 valores y 30.000 hogares de entrenamiento
(`SIMULACION_SEMISINTETICA.md`, punto 8). Con la celda del 2026-11-02
era +0,083 a +0,088\*.

**% de la reducción ideal de la brecha (FGT1)**

| Regla | Básico | Ampliado | Complejo |
|---|---|---|---|
| *Proporcional, mismos hogares* | | | |
| PMT por ingreso | 83,1\* | 87,0\* | 85,7\* |
| PMT por brecha | 80,4\* | 84,5\* | 83,3\* |
| PMT + CATE (vínculo) | 67,2\* | 71,8\* | 74,1\* |
| *Control: efecto verdadero* | 83,5\* | 88,4\* | 88,7\* |
| *Control: CATE con LinearDML* | 68,7\* | 71,3\* | 68,0\* |
| PMT + CATE (Hot-Deck) | 33,2\* | 36,9\* | 38,4\* |
| Vigente (Hot-Deck) | 71,7\* | 73,2\* | 72,3\* |
| Aleatoria | 45,2\* | 45,2\* | 45,2\* |
| *Monto fijo, mismo dinero* | | | |
| PMT por ingreso | 85,1\* | 83,4\* | 83,9\* |
| PMT por brecha | 75,9\* | 78,1\* | 80,1\* |
| PMT + CATE (vínculo) | 61,7\* | 66,2\* | 67,6\* |
| *Control: efecto verdadero* | 84,8\* | 82,9\* | 83,4\* |
| *Control: CATE con LinearDML* | 62,7\* | 65,7\* | 63,6\* |
| PMT + CATE (Hot-Deck) | 30,0\* | 46,8\* | 45,9\* |
| Vigente (Hot-Deck) | 72,9\* | 74,4\* | 73,4\* |

**Diferencia pareada PMT + CATE (vínculo) menos PMT por brecha** (misma
repetición; puntos del % del ideal, error estándar ≈0,4-1,2)

| | Básico | Ampliado | Complejo |
|---|---|---|---|
| Proporcional, mismos hogares | −13,2\* | −12,8\* | −9,2\* |
| Monto fijo, mismos hogares | −14,9\* | −15,3\* | −15,0\* |
| Monto fijo, mismo dinero | −14,3\* | −11,9\* | −12,5\* |

**Controles (2026-11-14), diferencias pareadas** (puntos del % del ideal;
error estándar entre paréntesis)

| | Básico | Ampliado | Complejo |
|---|---|---|---|
| Efecto verdadero − PMT por ingreso, proporcional | +0,3\* (0,03) | +1,4\* (0,03) | +3,0\* (0,03) |
| Efecto verdadero − PMT por ingreso, monto fijo | +0,4\* (0,02) | +1,4\* (0,02) | +2,8\* (0,03) |
| Efecto verdadero − PMT por ingreso, mismo dinero | −0,2\* (0,02) | −0,6\* (0,02) | −0,4\* (0,02) |
| LinearDML − Causal Forest, proporcional | +1,5\* (0,34) | −0,5\* (0,45) | −6,1\* (0,35) |
| LinearDML − Causal Forest, monto fijo | +1,0\* (0,49) | −0,5\* (0,58) | −5,0\* (0,47) |
| LinearDML − Causal Forest, mismo dinero | +1,0\* (0,47) | −0,6\* (0,44) | −4,0\* (0,35) |

### Causal Forest dentro de la celda y enlace fraccional (2026-11-20)

La misma corrida con el Causal Forest ajustado dentro de la celda (Y, T y
controles sin la media de la celda, como en
`sensibilidad_semisintetica.py bosque_intra_celda`) y con las reglas del
enlace fraccional (fase 3 de `METODOLOGIA_FHDI.md`). Son los mismos
sorteos: las reglas vigentes recalculadas reproducen la corrida anterior
(diferencia máxima 1,4·10⁻¹⁴). Las tablas de arriba no cambian; estas
filas se suman a ellas. Cifras del 2026-11-21, con el presupuesto de 13.567
hogares por muestra (donantes del Sisbén ponderados por `fex`). El nivel básico es la corrida de
`reglas_ampliadas.py` (`RESULTADOS_REGLAS_FOCALIZACION.md`).

| Nivel | ATE dentro de la celda, T verdadero | ATE dentro de la celda, T por Hot-Deck | PEHE, T verdadero | Desviación de tau | PEHE / desviación |
|---|---|---|---|---|---|
| Básico | +0,091 a +0,093\* | ≈0\* | 0,066 a 0,080\* | 0,028\* | 2,4 a 2,9\* |
| Ampliado | +0,091 a +0,092\* | +0,001 a 0,000\* | 0,148 a 0,188\* | 0,060\* | 2,5 a 3,1\* |
| Complejo | +0,092 a +0,094\* | +0,001 a 0,000\* | 0,139 a 0,202\* | 0,059\* | 2,4 a 3,4\* |

**% de la reducción ideal de la brecha (FGT1)**

| Regla | Básico | Ampliado | Complejo |
|---|---|---|---|
| *Proporcional, mismos hogares* | | | |
| PMT + CATE dentro de la celda (vínculo) | 74,8\* | 75,9\* | 77,4\* |
| PMT + CATE dentro de la celda (Hot-Deck) | 48,5\* | 48,3\* | 48,1\* |
| Vigente con enlace fraccional | 72,0\* | 73,5\* | 72,5\* |
| *Monto fijo, mismos hogares* | | | |
| PMT + CATE dentro de la celda (vínculo) | 73,2\* | 74,0\* | 75,3\* |
| PMT + CATE dentro de la celda (Hot-Deck) | 48,5\* | 49,2\* | 49,0\* |
| Vigente con enlace fraccional | 73,2\* | 74,6\* | 73,7\* |
| *Monto fijo, mismo dinero* | | | |
| PMT + CATE dentro de la celda (vínculo) | 73,8\* | 69,7\* | 71,8\* |
| PMT + CATE dentro de la celda (Hot-Deck) | 50,3\* | 53,2\* | 52,3\* |
| Vigente con enlace fraccional | 73,2\* | 74,6\* | 73,7\* |

PMT + CATE con el enlace fraccional y sin vínculo: no identificable (el
tratamiento es función de la celda).

**Diferencias pareadas** (puntos del % del ideal; error estándar entre
paréntesis)

| | Básico | Ampliado | Complejo |
|---|---|---|---|
| CATE dentro − PMT por brecha, proporcional | −5,5\* (0,55) | −8,6\* (0,31) | −5,9\* (0,36) |
| CATE dentro − PMT por brecha, monto fijo | −2,3\* (1,36) | −10,8\* (0,72) | −9,5\* (0,58) |
| CATE dentro − PMT por brecha, mismo dinero | −2,1\* (1,23) | −8,4\* (0,47) | −8,3\* (0,43) |
| CATE dentro − CATE vigente, proporcional | +7,7\* (0,46) | +4,1\* (0,29) | +3,3\* (0,25) |
| CATE dentro − CATE vigente, monto fijo | +12,6\* (0,60) | +4,5\* (0,40) | +5,5\* (0,34) |
| CATE dentro − CATE vigente, mismo dinero | +12,2\* (0,60) | +3,5\* (0,29) | +4,2\* (0,26) |
| CATE dentro (Hot-Deck) − aleatoria, mismos hogares | +3,2 a +3,4\* | +3,0 a +4,1\* | +2,9 a +3,8\* |
| CATE dentro (Hot-Deck) − aleatoria, mismo dinero | +0,4\* (0,82) | −0,6\* (0,41) | 0,0\* (0,44) |

## Lectura

1. **Con el doble de heterogeneidad, el CATE sigue empeorando la
   focalización.** En todos los niveles y presupuestos, la regla con el
   CATE queda por debajo de la misma regla con un efecto constante (9 a
   15 puntos\*) y del PMT por ingreso (12 a 25 puntos\*). Las diferencias
   son de 13 a 32 errores estándar.
2. **La brecha se cierra, pero despacio.** Con efecto proporcional, la
   desventaja del CATE frente al efecto constante pasa de 13,2\* a 9,2\*
   puntos del nivel básico al complejo. Con una heterogeneidad todavía
   mayor el CATE podría llegar a servir; este diseño no muestra en qué
   punto.
3. **La razón es la misma en los tres niveles: el error del CATE crece
   con la heterogeneidad.** El PEHE se mantiene entre 2,4 y 3,5 veces la
   desviación real del efecto. Más variación verdadera da más señal, pero
   también más que estimar con los mismos 30.000 hogares. Además, el
   nivel del efecto sale sesgado hacia cero (ATE +0,04 a +0,08\* frente a
   +0,095\*), más en el nivel básico.
   *Actualización 2026-11-20:* el sesgo del nivel es de estimar la celda
   y desaparece dentro de ella (ATE +0,091 a +0,094\*), pero el PEHE no
   baja: sigue entre 2,4 y 3,4 veces la desviación del efecto. Lo que
   falla para ordenar hogares es la varianza del CATE por hogar, no el
   sesgo. Dentro de la celda el CATE mejora 3 a 13 puntos\* y aun así
   queda 6 a 11 puntos\* bajo el PMT por brecha en los niveles ampliado y
   complejo (2 a 6\* en el básico, con 2 errores estándar en monto fijo).
   La conclusión 1 se mantiene, con distancias menores.
4. **Con el tratamiento del Hot-Deck no hay nada que estimar.** El ATE
   estimado es negativo (−0,02 a −0,06\*) en todos los niveles y la regla
   con ese CATE queda por debajo del azar (27-47 %\* frente a 45-54 %\*).
   *Actualización 2026-11-20:* el ATE negativo y el quedar bajo el azar
   eran el sesgo de estimar la celda. Dentro de la celda el ATE es ≈0\* y
   la regla queda en el azar (48-53 %\*, entre −0,6 y +4,1 puntos\* de la
   aleatoria). La lectura es la misma: sin vínculo, el CATE no aporta.
   Con el enlace fraccional ni siquiera se puede estimar (no
   identificable), y la vigente con ese enlace da lo mismo que con el
   sorteo (72-75 %\*).
5. **El orden de las reglas no cambia** con ninguno de los dos
   presupuestos. La vigente imputada queda en 72-74 %\* en los tres
   niveles, entre el PMT y las reglas con CATE.
6. **Conocer el efecto vale más cuanto más varía, pero poco** (control
   positivo). Con el efecto verdadero, la regla supera al PMT por 0,3-0,4\*
   puntos en el nivel básico, 1,4\* en el ampliado y 2,8-3,0\* en el
   complejo. Es el techo de lo que podría aportar un CATE perfecto; el
   estimado queda 15 a 25 puntos\* por debajo de ese techo. Con el mismo
   dinero, ni el efecto verdadero supera al PMT (−0,2 a −0,6\*).
7. **El modelo importa según la forma del efecto** (modelo base lineal).
   En el nivel básico, el LinearDML, que tiene la forma correcta, queda 1
   a 1,5 puntos\* sobre el bosque; en el ampliado empatan; cuando el
   efecto tiene interacciones y no linealidades (complejo), el bosque
   queda 4 a 6 puntos\* arriba. Ninguno de los dos se acerca al PMT: la
   conclusión no depende de haber usado un Causal Forest.

Con la celda del 2026-11-02 (993 celdas), las conclusiones eran las
mismas con distancias menores: el CATE quedaba 4 a 11 puntos\* bajo el
efecto constante y la vigente en 60-63 %\*.

## Alcance

- Es una evaluación controlada: la amplitud (desviación 0,06) y la forma
  de la heterogeneidad las fija el diseño. Con un efecto mucho más
  variable, o concentrado justo en los hogares más pobres, el resultado
  podría ser otro.
- El resultado no dice que estas variables no importen: sirven para
  predecir quién es pobre (`RECOMENDACION_VARIABLES_POBREZA.md`), que es
  lo que hace el proxy de medios. Lo que no sirve, con este tamaño de
  muestra, es estimar el efecto de cada hogar para ordenar por él.
- Con 30.000 hogares de entrenamiento y 3.721 celdas en los modelos
  auxiliares (≈8 por celda), el nivel del efecto sale sesgado
  (`SIMULACION_SEMISINTETICA.md`, punto 8 y sensibilidad 4). Con más
  hogares las reglas con CATE mejorarían, pero el control positivo acota
  cuánto: no pasarían del PMT por más de 3 puntos\*.

## Error encontrado durante el ejercicio

La primera corrida dio un ATE de −0,25\* con el T verdadero, cuando el
efecto real es +0,095\*. El codificador de los modelos auxiliares del
bosque ubica las columnas por posición y estaba armado para las 3 X del
nivel básico. Con 8 o 9 X, la celda del Hot-Deck (el confusor) quedaba
fuera de los modelos auxiliares, sin dar error. Se corrigió
(`ajustar_bosque` en `reglas_focalizacion.py` arma el codificador con
las X que recibe) y se agregó la prueba que lo detecta
(`tests/test_heterogeneidad_ampliada.py`, con confusión por celda y X de
3 y de 9 columnas) y su mutación. Los resultados del nivel básico no
cambian (diferencia máxima 7·10⁻¹⁵).

## Para reproducir

```bash
PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.focalizacion.heterogeneidad_ampliada 6 > docs/reports/heterogeneidad_ampliada.txt 2>&1
poetry run pytest tests/test_heterogeneidad_ampliada.py
# Causal Forest dentro de la celda y enlace fraccional (2026-11-20; 40 a 65 minutos por nivel con 3 procesos)
PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.focalizacion.reglas_ampliadas heterogeneidad 3 > docs/reports/heterogeneidad_ampliadas.txt 2>&1
poetry run pytest tests/test_reglas_ampliadas.py
```

El primer argumento es el número de procesos; el segundo, opcional, un
solo nivel (`ampliado` o `complejo`). Tarda ≈50 minutos por nivel con 6
procesos y retoma desde el último lote guardado.

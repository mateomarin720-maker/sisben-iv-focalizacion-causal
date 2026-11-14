# ¿Sirve el CATE para focalizar si el efecto varía más? (heterogeneidad ampliada)

Generado el 2026-11-09 y vuelto a correr el 2026-11-14 (IPM-GEIH corregido y dos reglas de control) por `src/focalizacion/heterogeneidad_ampliada.py`.
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
| Básico | +0,083 a +0,087\* | −0,008 a −0,010\* | 0,066 a 0,072\* | 0,028\* | 2,3 a 2,6\* |
| Ampliado | +0,088\* | −0,003 a −0,004\* | 0,135 a 0,163\* | 0,060\* | 2,2 a 2,7\* |
| Complejo | +0,088\* | −0,003 a −0,004\* | 0,127 a 0,173\* | 0,059\* | 2,2 a 2,9\* |

Efecto verdadero: +0,095\* en promedio. Los rangos van del efecto
proporcional al de monto fijo.

**% de la reducción ideal de la brecha (FGT1)**

| Regla | Básico | Ampliado | Complejo |
|---|---|---|---|
| *Proporcional, mismos hogares* | | | |
| PMT por ingreso | 82,2\* | 86,5\* | 84,7\* |
| PMT por brecha | 79,7\* | 83,8\* | 82,4\* |
| PMT + CATE (vínculo) | 72,7\* | 77,7\* | 78,4\* |
| *Control: efecto verdadero* | 82,5\* | 88,1\* | 88,4\* |
| *Control: CATE con LinearDML* | 73,6\* | 78,6\* | 73,4\* |
| PMT + CATE (Hot-Deck) | 44,6\* | 47,1\* | 47,6\* |
| Vigente (Hot-Deck) | 59,7\* | 61,4\* | 60,2\* |
| Aleatoria | 46,6\* | 46,6\* | 46,6\* |
| *Monto fijo, mismo dinero* | | | |
| PMT por ingreso | 79,8\* | 76,4\* | 76,5\* |
| PMT por brecha | 77,4\* | 71,4\* | 72,4\* |
| PMT + CATE (vínculo) | 68,5\* | 64,9\* | 65,6\* |
| *Control: efecto verdadero* | 79,4\* | 76,1\* | 76,2\* |
| *Control: CATE con LinearDML* | 69,4\* | 66,9\* | 63,3\* |
| PMT + CATE (Hot-Deck) | 43,5\* | 48,1\* | 47,2\* |
| Vigente (Hot-Deck) | 60,8\* | 62,5\* | 61,2\* |

**Diferencia pareada PMT + CATE (vínculo) menos PMT por brecha** (misma
repetición; puntos del % del ideal, error estándar ≈0,2-0,5)

| | Básico | Ampliado | Complejo |
|---|---|---|---|
| Proporcional, mismos hogares | −7,0\* | −6,1\* | −4,0\* |
| Monto fijo, mismos hogares | −10,7\* | −8,9\* | −8,5\* |
| Monto fijo, mismo dinero | −8,9\* | −6,6\* | −6,8\* |

**Controles (2026-11-14), diferencias pareadas** (puntos del % del ideal;
error estándar entre paréntesis)

| | Básico | Ampliado | Complejo |
|---|---|---|---|
| Efecto verdadero − PMT por ingreso, proporcional | +0,4\* (0,03) | +1,6\* (0,03) | +3,7\* (0,03) |
| Efecto verdadero − PMT por ingreso, monto fijo | +0,4\* (0,02) | +1,5\* (0,03) | +3,5\* (0,03) |
| Efecto verdadero − PMT por ingreso, mismo dinero | −0,3\* (0,02) | −0,3\* (0,02) | −0,3\* (0,02) |
| LinearDML − Causal Forest, proporcional | +0,9\* (0,27) | +0,9\* (0,33) | −5,0\* (0,30) |
| LinearDML − Causal Forest, monto fijo | +1,2\* (0,39) | +1,9\* (0,44) | −4,1\* (0,40) |
| LinearDML − Causal Forest, mismo dinero | +0,9\* (0,30) | +2,0\* (0,29) | −2,3\* (0,26) |

## Lectura

1. **Con el doble de heterogeneidad, el CATE sigue empeorando la
   focalización.** En todos los niveles y presupuestos, la regla con el
   CATE queda por debajo de la misma regla con un efecto constante (4 a
   11 puntos\*) y del PMT por ingreso (6 a 13 puntos\*). Las diferencias
   son de 14 a 35 errores estándar.
2. **La brecha se cierra, pero despacio.** Con efecto proporcional, la
   desventaja del CATE pasa de 7,0\* a 4,0\* puntos del nivel básico al
   complejo. Con una heterogeneidad todavía mayor el CATE podría llegar a
   servir; este diseño no muestra en qué punto.
3. **La razón es la misma en los tres niveles: el error del CATE crece
   con la heterogeneidad.** El PEHE se mantiene entre 2,2 y 2,9 veces la
   desviación real del efecto. Más variación verdadera da más señal, pero
   también más que estimar con los mismos 30.000 hogares.
4. **Con el tratamiento del Hot-Deck no hay nada que estimar.** El ATE
   estimado es ≈0\* en todos los niveles y la regla con ese CATE queda al
   nivel del azar (47-48 %\* frente a 46,6 %\*).
5. **El orden de las reglas no cambia** con ninguno de los dos
   presupuestos.
6. **Conocer el efecto vale más cuanto más varía, pero poco** (control
   positivo). Con el efecto verdadero, la regla supera al PMT por 0,4\*
   puntos en el nivel básico, 1,6\* en el ampliado y 3,7\* en el
   complejo. Es el techo de lo que podría aportar un CATE perfecto; el
   estimado queda 10 a 14 puntos\* por debajo de ese techo. Con el mismo
   dinero, ni el efecto verdadero supera al PMT (−0,3\*).
7. **El modelo importa según la forma del efecto** (modelo base lineal).
   Cuando el efecto es lineal en las X (básico y ampliado), el LinearDML,
   que tiene la forma correcta, queda 1 a 2 puntos\* sobre el bosque;
   cuando tiene interacciones y no linealidades (complejo), el bosque
   queda 2 a 5 puntos\* arriba. Ninguno de los dos se acerca al PMT: la
   conclusión no depende de haber usado un Causal Forest.

## Alcance

- Es una evaluación controlada: la amplitud (desviación 0,06) y la forma
  de la heterogeneidad las fija el diseño. Con un efecto mucho más
  variable, o concentrado justo en los hogares más pobres, el resultado
  podría ser otro.
- El resultado no dice que estas variables no importen: sirven para
  predecir quién es pobre (`RECOMENDACION_VARIABLES_POBREZA.md`), que es
  lo que hace el proxy de medios. Lo que no sirve, con este tamaño de
  muestra, es estimar el efecto de cada hogar para ordenar por él.

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
```

El primer argumento es el número de procesos; el segundo, opcional, un
solo nivel (`ampliado` o `complejo`). Tarda ≈50 minutos por nivel con 6
procesos y retoma desde el último lote guardado.

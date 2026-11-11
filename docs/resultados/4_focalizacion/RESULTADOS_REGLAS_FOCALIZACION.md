# Reglas de focalización (P3/OE3)

Generado por `src/focalizacion/reglas_focalizacion.py`; corrida vigente:
2026-11-08, con la cadena de respaldos del Hot-Deck. 300
repeticiones, evaluación en 30.000 hogares reales por repetición. Salidas
en `docs/reports/`: `reglas_focalizacion.txt` (consola),
`reglas_focalizacion_resumen.csv` (métricas con su error Monte Carlo) y
`reglas_focalizacion.csv` (cada repetición).

**Pregunta del OE3:** ¿cuánto se reducirían los errores de inclusión y
exclusión y la brecha de pobreza (FGT1) con reglas de focalización
informadas por los efectos heterogéneos, frente a la clasificación
vigente?

**Cómo se responde.** Con los datos actuales el efecto del Sisbén no está
identificado (P2: `SIMULACION_SEMISINTETICA.md`, `RESULTADOS_FRECHET_MANSKI.md`).
Por eso el OE3 se evalúa en el mismo mundo semisintético: **hogares,
ingresos, líneas de pobreza y clasificación imputada reales** de GEIH
2024, y un programa con efecto conocido. **Las cifras son simuladas:**
dicen qué regla funcionaría mejor si el efecto fuera ese, no cuánto
reduce hoy la pobreza el Sisbén.

## Diseño

- **Presupuesto igual para todas las reglas:** cada una trata el mismo
  número de hogares, los que la clasificación vigente imputada deja en A/B
  (13.992 de 30.000 por muestra, 46,7 %).
- **Efecto del programa**, dos modelos (cambian qué hogares conviene
  tratar):
  - *proporcional*: +tau(X) en log-ingreso, el de P2 (≈ +10 % del
    ingreso). Da más pesos a quien más tiene y nada a un hogar sin ingreso.
  - *monto fijo*: una transferencia de tau(X) líneas de pobreza por
    persona (≈ 9,5 % de la línea en promedio), como un subsidio en dinero.
  - En los dos, tau(X) = 0,10 + 0,05·rural − 0,03·jefa + 0,04·paredes
    precarias.
- **Reglas:**

| Regla | Qué usa | ¿Factible hoy? |
|---|---|---|
| Vigente (Hot-Deck) | Grupos A/B imputados por Hot-Deck | Sí (es la clasificación que se puede observar en GEIH) |
| Aleatoria | Nada | Referencia |
| PMT por ingreso | Menor ingreso predicho por un proxy de medios (Ridge sobre celda, vivienda, servicios, tamaño del hogar y 6 privaciones; nunca el ingreso) | Sí: es la lógica del Sisbén IV |
| PMT por brecha | Mayor reducción esperada de la brecha, con efecto constante | Sí |
| PMT + CATE (vínculo) | Igual, con el CATE de un Causal Forest entrenado con el tratamiento verdadero | Solo con vínculo hogar por hogar |
| PMT + CATE (Hot-Deck) | Igual, con el CATE entrenado con el tratamiento imputado por Hot-Deck | Sí, con las fuentes actuales |
| Ideal | Ingreso y efecto verdaderos | No: es el techo |

- La reducción esperada de la brecha promedia sobre la distribución
  empírica del error del proxy de medios (no una normal: los hogares sin
  ingreso dan errores extremos). El proxy y el Causal Forest se entrenan
  en una muestra distinta de la de evaluación.
- **Métricas sobre personas**, con la pobreza medida antes del programa:
  error de inclusión (tratados no pobres / tratados), error de exclusión
  (pobres no tratados / pobres), FGT0 y FGT1 después del programa, y la
  reducción de FGT1 como porcentaje de la que logra la regla ideal.

## Resultados

Sin programa (datos reales): FGT0 = 33,2 %, FGT1 = 0,1350. \* Resultado simulado.

| Regla | Error de inclusión | Error de exclusión | Reducción de FGT1, proporcional | % del ideal | Reducción de FGT1, monto fijo | % del ideal |
|---|---|---|---|---|---|---|
| Vigente (Hot-Deck) | 58,1 %\* | 43,5 %\* | 0,0116\* | 59,7\* | 0,0199\* | 60,8\* |
| Aleatoria | 66,9 %\* | 53,3 %\* | 0,0091\* | 46,7\* | 0,0152\* | 46,6\* |
| PMT por ingreso | 48,5 %\* | 18,6 %\* | 0,0160\* | 82,1\* | 0,0276\* | 84,5\* |
| PMT por brecha | 48,4 %\* | 19,7 %\* | 0,0155\* | 79,7\* | 0,0270\* | 82,6\* |
| PMT + CATE (vínculo) | 51,8 %\* | 26,1 %\* | 0,0141\* | 72,6\* | 0,0235\* | 71,9\* |
| PMT + CATE (Hot-Deck) | 67,7 %\* | 54,9 %\* | 0,0087\* | 44,6\* | 0,0144\* | 44,1\* |
| Ideal | 34,3 %\* | 0 %\* | 0,0194\* | 100\* | 0,0327\* | 100\* |

Los errores de inclusión y exclusión son los del efecto proporcional.
Con monto fijo son iguales en las reglas sin CATE y cambian hasta 2
puntos en las reglas con CATE (exclusión 28,1 % con vínculo).

**Error de simulación.** Las reglas sin CATE convergieron: el error
estándar Monte Carlo es ≤ 0,0006 en las tasas y ≤ 0,07 puntos en el % del
ideal. Las dos reglas con CATE no convergieron en 300 repeticiones: su
resultado cambia mucho de una repetición a otra porque depende del ruido
de cada estimación del Causal Forest. Sus errores son ≤ 0,009 en las
tasas y ≤ 0,76 puntos en el % del ideal, suficientes para ordenar las
reglas, pero esa volatilidad es en sí un hallazgo (punto 3).

**Piso del error de inclusión.** El presupuesto (44,8 % de las personas)
es mayor que la población pobre (33,2 %), así que incluso la regla ideal
trata a no pobres: el error de inclusión mínimo posible es ≈ 34 %. Los
errores de inclusión se leen frente a ese piso.

### Mismo dinero (2026-11-09)

Con el mismo número de hogares, las reglas no gastan lo mismo: el PMT por
ingreso elige hogares más grandes y, con monto fijo, transfiere 13 %\*
más que la vigente. Para separar la mejor focalización del mayor gasto,
con monto fijo se repiten las reglas con **el mismo dinero que la
vigente**. Cada regla trata hogares en su orden hasta agotar ese
presupuesto. Las que ordenan por reducción esperada de la brecha pasan a
ordenar por reducción por peso. La columna `gasto_rel` del CSV es el
gasto de cada regla frente al de la vigente.

| Regla (monto fijo) | Gasto con los mismos hogares | % del ideal, mismos hogares | % del ideal, mismo dinero |
|---|---|---|---|
| Vigente (Hot-Deck) | 1,00\* | 60,8\* | 60,8\* |
| Aleatoria | 1,05\* | 46,6\* | 44,5\* |
| PMT por ingreso | 1,13\* | 84,5\* | 79,7\* |
| PMT por brecha | 1,13\* | 82,6\* | 77,4\* |
| PMT + CATE (vínculo) | 1,12\* | 71,9\* | 68,5\* |
| PMT + CATE (Hot-Deck) | 1,03\* | 44,1\* | 43,5\* |

Con el mismo dinero, el PMT por ingreso pierde unos 5 puntos, pero sigue
19\* por encima de la vigente, y su error de exclusión sube de 18,6 %\* a
24,4 %\*. **El orden de las reglas no cambia:** la ventaja del proxy de
medios no venía de gastar más. Con efecto proporcional no se repite,
porque el costo (lo que sube el ingreso) solo se conoce después de
transferir; ahí el PMT gasta 25 %\* menos que la vigente y aun así reduce
más la brecha.

Las filas con el mismo número de hogares no cambian al agregar este
presupuesto: el reparto con el mismo dinero usa su propio generador
aleatorio, y las cifras de la tabla de arriba se reproducen exactamente.

## Lectura

1. **Un proxy de medios con las variables del hogar focaliza mucho mejor
   que la clasificación imputada por celda.** Frente a la vigente
   (Hot-Deck), el PMT por ingreso baja el error de exclusión de 43,5 % a
   18,6 % y el de inclusión de 58,1 % a 48,5 %, y reduce la brecha un 38 %
   más (0,0160 frente a 0,0116; 39 % más con monto fijo). Logra 82-85 %
   de lo que lograría una regla con información perfecta.

2. **La clasificación vigente imputada apenas supera al azar** (60 %
   frente a 47 % del ideal). No es una evaluación del Sisbén real: el
   grupo imputado solo lleva la información de la celda (departamento,
   edad del jefe, cuartos, pisos), mientras que el Sisbén clasifica con
   los datos de cada hogar. Es lo que se puede observar en GEIH con el
   Hot-Deck, y su desempeño probablemente subestima el del Sisbén real.

3. **Usar los efectos heterogéneos estimados empeora la focalización.**
   Con el CATE de un Causal Forest entrenado con el tratamiento verdadero,
   la regla baja a 72-73 % del ideal, peor que el PMT sin CATE (80-85 %).
   La evaluación semisintética ya mostró por qué: el error del CATE por
   hogar (PEHE 0,05-0,07) es mayor que la variación real del efecto
   (0,028), así que el CATE agrega más ruido que información.

4. **Con el CATE estimado desde el Hot-Deck, la regla es peor que el
   azar** (44 % frente a 47 % del ideal, exclusión 55 %). Ese CATE es
   ruido alrededor de cero (ATE estimado −0,008 a −0,010 frente a +0,095) y a
   veces negativo, lo que invierte el orden de los hogares. Es la
   consecuencia práctica de P2: con las fuentes actuales no hay efectos
   heterogéneos utilizables para focalizar.

5. **Ordenar por la reducción esperada de la brecha no mejora sobre
   ordenar por ingreso predicho** (80-83 % frente a 82-85 %). Con este
   presupuesto, mayor que la población pobre, lo que importa es no dejar
   pobres por fuera, y el ingreso predicho ya lo hace bien.

6. **El modelo del efecto cambia la magnitud, no el orden.** Con monto
   fijo todas las reglas reducen más la brecha (la transferencia llega
   también a los hogares sin ingreso), pero el orden entre reglas es el
   mismo en los dos modelos.

## Respuesta al OE3

- **Errores de inclusión y exclusión:** pasar de la clasificación
  observable con Hot-Deck a un proxy de medios con variables del hogar
  los reduciría en 10 y 25 puntos. Informar la regla con efectos
  heterogéneos estimados no los reduce más: los aumenta (3-10 puntos con
  vínculo hogar por hogar, 19-37 puntos con Hot-Deck).
- **Brecha de pobreza (FGT1):** la mejor regla factible (PMT por
  ingreso) logra 82-85 % de la reducción ideal; la vigente imputada
  60 %; las informadas por CATE 72 % (con vínculo) y 44 % (con Hot-Deck).
- **Condición para que los efectos heterogéneos sirvan:** un CATE cuyo
  error sea menor que la variación real del efecto. Con 30.000 hogares,
  el ruido del ingreso real y la heterogeneidad simulada, el Causal
  Forest no llega; con el tratamiento imputado por Hot-Deck, no hay
  heterogeneidad que estimar.

### ¿Qué representa el CATE con monto fijo?

Con monto fijo, el planificador conoce cuánto transfiere. La regla con
CATE representa a un planificador que no conoce **cuánto sube el ingreso
de cada hogar** con esa transferencia: en el diseño coinciden, pero en la
realidad pueden diferir (cambios en el trabajo o en otras ayudas). Por
eso la regla con CATE se mantiene también con monto fijo, y la ideal usa
el efecto verdadero.

## Limitaciones

- Efecto simulado (dos modelos). Con el doble de heterogeneidad y el
  Causal Forest viendo todos los modificadores, el CATE sigue empeorando
  la focalización, aunque la desventaja se reduce
  (`RESULTADOS_HETEROGENEIDAD_AMPLIADA.md`). Con una heterogeneidad
  todavía mayor, o con más hogares, podría servir: la regla ideal muestra
  cuánto habría por ganar (15-18 puntos sobre el PMT).
- Los errores de inclusión y exclusión de esta página son simulados. Con
  datos reales solo se pueden acotar, celda por celda
  (`RESULTADOS_ERRORES_FOCALIZACION_FRECHET.md`).
- La regla vigente es la clasificación imputada por celda, no la del
  Sisbén real hogar por hogar (que GEIH no trae).
- Presupuesto fijo en el tamaño de A/B; con un presupuesto menor que la
  población pobre, el orden entre el PMT por ingreso y por brecha podría
  cambiar.
- Pobreza medida con la reconstrucción monetaria (33,2 % de personas
  frente a 31,8 % oficial).
- El proxy de medios usa una regresión Ridge sencilla; el Sisbén IV usa
  un modelo propio con más variables.

## Para reproducir

```bash
PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.focalizacion.reglas_focalizacion 3 > docs/reports/reglas_focalizacion.txt 2>&1
poetry run pytest tests/test_reglas_focalizacion.py
```

El argumento es el número de procesos en paralelo. Tarda ≈35 minutos
(lotes de 12 repeticiones, ≈80 s por lote). Si se interrumpe, retoma
desde el último lote guardado.

# Reglas de focalización (P3/OE3)

Generado por `src/focalizacion/reglas_focalizacion.py`; corrida vigente:
2026-11-15, con la celda del Hot-Deck que suma personas y menores de 18
años (3.721 celdas) y su cadena de respaldos, el IPM-GEIH corregido por
zona (el proxy de medios usa sus privaciones) y dos reglas de control. 300
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
  (14.085 de 30.000 por muestra, 47,0 %).
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
| *Control positivo* | Como PMT + CATE (vínculo), con el efecto verdadero de cada hogar en vez del estimado | No: es el techo de las reglas con CATE |
| *Modelo base lineal* | Como PMT + CATE (vínculo), con el CATE de un LinearDML (X en indicadoras, mismos modelos auxiliares) | Solo con vínculo hogar por hogar |

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
| Vigente (Hot-Deck) | 54,8 %\* | 27,8 %\* | 0,0145\* | 74,6\* | 0,0246\* | 75,4\* |
| Aleatoria | 66,9 %\* | 53,1 %\* | 0,0091\* | 46,9\* | 0,0153\* | 46,9\* |
| PMT por ingreso | 48,3 %\* | 16,3 %\* | 0,0164\* | 84,2\* | 0,0282\* | 86,4\* |
| PMT por brecha | 48,5 %\* | 17,8 %\* | 0,0159\* | 81,7\* | 0,0250\* | 76,7\* |
| PMT + CATE (vínculo) | 54,9 %\* | 30,2 %\* | 0,0133\* | 68,3\* | 0,0201\* | 61,4\* |
| PMT + CATE (Hot-Deck) | 75,7 %\* | 66,6 %\* | 0,0066\* | 34,0\* | 0,0089\* | 27,4\* |
| Ideal | 34,6 %\* | 0 %\* | 0,0194\* | 100\* | 0,0327\* | 100\* |
| *Control positivo* | 48,5 %\* | 16,1 %\* | 0,0164\* | 84,6\* | 0,0284\* | 87,0\* |
| *Modelo base lineal* | 54,6 %\* | 29,0 %\* | 0,0136\* | 69,8\* | 0,0204\* | 62,4\* |

Con la celda del 2026-11-02 (993 celdas), la vigente lograba 59,7-60,8 %
del ideal, con exclusión 43,5 %\* e inclusión 58,1 %\*; el PMT por
ingreso, 82,2-84,6; las reglas con CATE y vínculo, 72-73.

Los errores de inclusión y exclusión son los del efecto proporcional.
Con monto fijo son iguales en la vigente, la aleatoria y el proxy por
ingreso, que no dependen del modelo del efecto. Cambian en las que
ordenan por la reducción esperada de la brecha: exclusión 24,5 % en el
proxy por brecha y 37,8 % con CATE y vínculo.

**Error de simulación.** Las reglas que no usan una estimación del
efecto convergieron: el error estándar Monte Carlo es ≤ 0,0006 en las
tasas y ≤ 0,07 puntos en el % del ideal. Las que sí la usan no
convergieron en 300 repeticiones: las dos con CATE y el PMT por brecha,
que toma como efecto constante el ATE del Causal Forest. Su resultado
cambia mucho de una repetición a otra porque depende de cada estimación.
Sus errores son ≤ 0,013 en las tasas y ≤ 1,4 puntos en el % del ideal,
suficientes para ordenar las reglas, pero esa volatilidad es en sí un
hallazgo (punto 3).

**Piso del error de inclusión.** El presupuesto es mayor que la
población pobre (33,2 % de las personas), así que incluso la regla ideal
trata a no pobres: el error de inclusión mínimo posible es ≈ 35 %. Los
errores de inclusión se leen frente a ese piso.

### Mismo dinero (2026-11-09)

Con el mismo número de hogares, las reglas no gastan lo mismo: cada una
elige hogares de distinto tamaño, y con monto fijo la transferencia
depende de las personas del hogar. Para separar la mejor focalización del mayor gasto,
con monto fijo se repiten las reglas con **el mismo dinero que la
vigente**. Cada regla trata hogares en su orden hasta agotar ese
presupuesto. Las que ordenan por reducción esperada de la brecha pasan a
ordenar por reducción por peso. La columna `gasto_rel` del CSV es el
gasto de cada regla frente al de la vigente.

| Regla (monto fijo) | Gasto con los mismos hogares | % del ideal, mismos hogares | % del ideal, mismo dinero |
|---|---|---|---|
| Vigente (Hot-Deck) | 1,00\* | 75,4\* | 75,4\* |
| Aleatoria | 0,89\* | 46,9\* | 52,5\* |
| PMT por ingreso | 0,99\* | 86,4\* | 86,8\* |
| PMT por brecha | 0,97\* | 76,7\* | 78,0\* |
| PMT + CATE (vínculo) | 0,96\* | 61,4\* | 62,9\* |
| PMT + CATE (Hot-Deck) | 0,86\* | 27,4\* | 31,7\* |
| *Control positivo* | 1,02\* | 87,0\* | 86,7\* |
| *Modelo base lineal* | 0,96\* | 62,4\* | 64,0\* |

Con la celda nueva, la vigente elige hogares más grandes (el número de
personas entra a la celda) y el PMT por ingreso gasta lo mismo que ella
(0,99\*; con la celda anterior gastaba 13 %\* más). Con el mismo dinero,
el PMT queda en 86,8\*, 11 puntos sobre la vigente, con exclusión de
15,8 %\*. **El orden de las reglas no cambia:** la ventaja del proxy de
medios no viene de gastar más. Con efecto proporcional no se repite,
porque el costo (lo que sube el ingreso) solo se conoce después de
transferir; ahí el PMT gasta 25 %\* menos que la vigente y aun así reduce
más la brecha.

Las filas con el mismo número de hogares no cambian al agregar este
presupuesto: el reparto con el mismo dinero usa su propio generador
aleatorio, y las cifras de la tabla de arriba se reproducen exactamente.

### Controles: efecto verdadero y modelo base lineal (2026-11-14)

La lectura 3 de abajo (el CATE estimado empeora la focalización) admite
dos explicaciones: que el Causal Forest estime mal un efecto que sí
serviría, o que conocer el efecto aporte poco en este diseño. Dos reglas
de control las separan; eligen con su propio generador aleatorio, así
que las demás cifras no cambian por agregarlas.

| | Proporcional | Monto fijo | Monto fijo, mismo dinero | Error del CATE por hogar (PEHE): mediana; percentil 90 |
|---|---|---|---|---|
| PMT por ingreso (sin CATE) | 84,2\* | 86,4\* | 86,8\* | — |
| Control positivo (efecto verdadero) | 84,6\* | 87,0\* | 86,7\* | 0 |
| CATE con LinearDML | 69,8\* | 62,4\* | 64,0\* | 0,12\*; 0,22-0,33\* |
| CATE con Causal Forest | 68,3\* | 61,4\* | 62,9\* | 0,08-0,10\*; 0,11-0,13\* |

% de la reducción ideal de FGT1. La desviación del efecto verdadero entre
hogares es 0,028\*.

- **Conocer el efecto exacto casi no ayuda.** Con el efecto verdadero, la
  regla queda a 0,4-0,6 puntos del PMT por ingreso, y con el mismo dinero
  queda por debajo. Con esta heterogeneidad, lo que decide la
  focalización es el ingreso predicho, no el efecto.
- **El problema no es el bosque.** En este diseño el efecto es lineal en
  las X, así que el LinearDML tiene la forma correcta. Como regla queda
  ≈1 punto por encima del bosque, la misma distancia al techo: los dos
  pierden 14-24 puntos frente al PMT. Como estimador del efecto es peor y
  más inestable (en 45 de las 600 estimaciones su PEHE pasa de 0,3, con
  un máximo de 4,1), porque estima un coeficiente por material de paredes
  y algunos tienen pocos hogares.
- **Los dos estiman mal también el nivel del efecto.** Con el tratamiento
  verdadero, el ATE del Causal Forest es +0,061\* (mediana) frente a
  +0,095\*, y el del LinearDML +0,060\*. Es el sesgo de
  `SIMULACION_SEMISINTETICA.md` (punto 8): se entrenan con 30.000
  hogares y la celda de 3.721 valores en los modelos auxiliares, ≈8 por
  celda. Con la celda anterior el CATE ya empeoraba la focalización
  (72-73 % frente a 82-85 %); ahora la pérdida es mayor (61-70 % frente a
  84-87 %) por ese sesgo, que se suma al ruido.
- Responde a la pregunta del modelo base (`docs/anexos_tesis/METODO_PREDICTIVO.md`):
  la conclusión de la lectura 3 no depende de usar un Causal Forest.

## Lectura

1. **Un proxy de medios con las variables del hogar focaliza mejor que
   la clasificación imputada por celda.** Frente a la vigente (Hot-Deck),
   el PMT por ingreso baja el error de exclusión de 27,8 % a 16,3 % y el
   de inclusión de 54,8 % a 48,3 %, y reduce la brecha un 13 % más
   (0,0164 frente a 0,0145; 15 % más con monto fijo). Logra 84-87 % de lo
   que lograría una regla con información perfecta.

2. **La clasificación vigente imputada supera claramente al azar** (75 %
   frente a 47 % del ideal). Con la celda del 2026-11-02 apenas lo
   superaba (60 %): personas y menores llevan información sobre la
   pobreza del hogar, y el grupo imputado ahora la recoge. No es una
   evaluación del Sisbén real: el grupo imputado solo lleva la
   información de la celda, mientras que el Sisbén clasifica con los
   datos de cada hogar. Es lo que se puede observar en GEIH con el
   Hot-Deck, y su desempeño probablemente subestima el del Sisbén real.

3. **Usar los efectos heterogéneos estimados empeora la focalización.**
   Con el CATE de un Causal Forest entrenado con el tratamiento verdadero,
   la regla baja a 61-68 % del ideal, por debajo de la vigente (75 %) y
   del PMT sin CATE (84-87 %). Dos razones: el error del CATE por hogar
   (PEHE 0,08-0,10) es mayor que la variación real del efecto (0,028),
   así que agrega más ruido que información, y el nivel del efecto sale
   sesgado hacia cero (ATE +0,061 frente a +0,095) por las celdas con
   pocos hogares en la muestra de entrenamiento. Un LinearDML con la forma
   correcta del efecto da casi lo mismo (62-70 %), y el efecto verdadero
   apenas supera al PMT: ver los controles.

4. **Con el CATE estimado desde el Hot-Deck, la regla es mucho peor que
   el azar** (27-34 % frente a 47 % del ideal, exclusión 67 %). Ese CATE
   es ruido alrededor de un valor negativo (ATE estimado −0,034 a −0,057
   frente a +0,095), lo que invierte el orden de los hogares. Es la
   consecuencia práctica de P2: con las fuentes actuales no hay efectos
   heterogéneos utilizables para focalizar.

5. **Ordenar por la reducción esperada de la brecha no mejora sobre
   ordenar por ingreso predicho** (77-82 % frente a 84-86 %). Con este
   presupuesto, mayor que la población pobre, lo que importa es no dejar
   pobres por fuera, y el ingreso predicho ya lo hace bien. Además, esa
   regla usa el ATE estimado como efecto constante y hereda su
   inestabilidad.

6. **El modelo del efecto cambia la magnitud, no el orden.** Con monto
   fijo todas las reglas reducen más la brecha (la transferencia llega
   también a los hogares sin ingreso), pero el orden entre reglas es el
   mismo en los dos modelos.

## Respuesta al OE3

- **Errores de inclusión y exclusión:** pasar de la clasificación
  observable con Hot-Deck a un proxy de medios con variables del hogar
  los reduciría en 6 y 12 puntos. Informar la regla con efectos
  heterogéneos estimados no los reduce más: los aumenta (7-14 puntos con
  vínculo hogar por hogar, 27-50 puntos con Hot-Deck).
- **Brecha de pobreza (FGT1):** la mejor regla factible (PMT por
  ingreso) logra 84-87 % de la reducción ideal; la vigente imputada
  75 %; las informadas por CATE 61-68 % (con vínculo) y 27-34 % (con
  Hot-Deck).
- **Condición para que los efectos heterogéneos sirvan:** un CATE cuyo
  error sea menor que la variación real del efecto, y que no esté
  sesgado en su nivel. Con 30.000 hogares de entrenamiento, el ruido del
  ingreso real y la heterogeneidad simulada, el Causal Forest no llega, y
  tampoco un LinearDML con la forma correcta del efecto; con el
  tratamiento imputado por Hot-Deck, no hay heterogeneidad que estimar.
  Aun con el CATE perfecto, la ganancia sobre el PMT sería de menos de un
  punto con esta heterogeneidad.

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
  todavía mayor, o con más hogares, podría servir. La regla ideal queda
  13-16 puntos sobre el PMT, pero casi todo eso viene de conocer el
  ingreso, no el efecto: con el efecto verdadero y el ingreso predicho se
  gana menos de un punto (control positivo).
- El Causal Forest y el LinearDML se entrenan con 30.000 hogares y la
  celda de 3.721 valores en los modelos auxiliares (≈8 hogares por
  celda), lo que sesga el nivel del efecto (`SIMULACION_SEMISINTETICA.md`,
  punto 8 y sensibilidad 4). Con más hogares de entrenamiento las reglas
  con CATE mejorarían, pero el control positivo acota cuánto: no pasarían
  del PMT.
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

El argumento es el número de procesos en paralelo. Tarda ≈30 minutos
(lotes de 12 repeticiones, ≈70 s por lote). Si se interrumpe, retoma
desde el último lote guardado.

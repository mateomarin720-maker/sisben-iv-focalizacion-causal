# Simulación de identificación — ¿qué diseño puede recuperar el efecto de la elegibilidad?

Generado 2026-10-27 por `src/validacion/simulacion_identificacion.py`
(20 repeticiones, población de 150.000 hogares; salida completa en
`docs/reports/resultado_simulacion_identificacion.txt`). **Datos
sintéticos con efecto verdadero conocido**, no resultados sobre GEIH/Sisbén
reales: sirve para saber qué diseños *pueden* recuperar el efecto de P2/OE2,
antes de gastar datos reales en ellos.

## El mundo simulado
- El Sisbén es un índice **ruidoso de necesidad**. Elegible (A/B) = índice por encima de un corte.
- La necesidad depende de la celda del Hot-Deck (depto × ciclo de vida) y de un factor que la celda **no** captura (U, p. ej. calidad de vivienda).
- Resultado Y = privación del hogar (mayor = peor). El efecto verdadero de ser elegible se fija en 0, −0,15 o −0,30 (negativo = reduce la privación).
- Dos fuentes independientes sin llave común: una muestra tipo GEIH (X, Y) y otra tipo Sisbén (X, T).

## Resultado (media de 20 repeticiones; si el estimador funciona, debe coincidir con el efecto verdadero)

Celda con poder alto sobre la necesidad (`sd_celda = 0,8`):

| Estimador | Verdadero 0 | Verdadero −0,15 | Verdadero −0,30 |
|---|---|---|---|
| A. Hot-Deck + contraste dentro de la celda (lo que hace hoy el pipeline) | 0,000 | −0,004 | +0,002 |
| A′. Hot-Deck sin controlar por la celda | +0,933 | +0,893 | +0,876 |
| B. Vinculación perfecta (se observa T real) + control por la celda | +1,459 | +1,312 | +1,159 |
| C. Vinculación perfecta + discontinuidad de regresión (puntaje continuo) | +0,004 | −0,160 | −0,297 |
| D. Vinculación perfecta + solo grupos ordinales A–D (grupos vecinos B vs. C) | +0,806 | +0,662 | +0,516 |

Con celda de poder bajo (`sd_celda = 0,3`) el patrón es el mismo, con sesgos
menores en A′ (≈ +0,2); ver el archivo de salida.

## Lectura
1. **A (el pipeline actual) devuelve ≈ 0 sea cual sea el efecto verdadero.** El grupo imputado es independiente del resultado dentro de la celda, por construcción (el mismo hecho que muestra el DAG refinado de `IDENTIFICACION_CAUSAL.md`). Por eso un número pequeño en `5_estimacion.py` no se puede leer como «efecto del Sisbén»: es una **prueba placebo del emparejamiento**, no una estimación del efecto.
2. **A′ muestra de dónde sale un «efecto» espurio:** si no se controla bien por la celda, la geografía y la edad se cuelan como asociación. Es coherente con el residuo que quedó en los controles mal especificados (`VALIDACION_MODELOS.md`).
3. **B: tener una llave común no basta.** Con vinculación perfecta y control por la celda, el contraste queda muy sesgado (+1,1 a +1,5) porque ser elegible depende de la necesidad: los elegibles son más necesitados por construcción (selección sobre el índice). La independencia condicional dada la celda no se cumple.
4. **C: lo que sí recupera el efecto es la discontinuidad con puntaje continuo** (−0,286 vs. −0,30; −0,160 vs. −0,15; +0,004 vs. 0). Necesita el puntaje continuo **y** el resultado en el mismo archivo (o una llave).
5. **D: con grupos ordinales no basta** (sesgo +0,3 a +0,8): sin puntaje continuo, comparar grupos vecinos no aísla el corte.

## Alternativas para el objetivo principal (P2/OE2), de mayor a menor identificación

| # | Diseño | Qué necesita | Qué demuestra esta simulación | Estado en el repo |
|---|---|---|---|---|
| 1 | Discontinuidad de regresión en la frontera de elegibilidad | Puntaje continuo + resultado (llave o vínculo) | Recupera el efecto (C) | Bloqueado: la microdata no trae puntaje continuo; hay que solicitarlo (DNP/SDP) |
| 2 | Cambio metodológico Sisbén III → IV (diferencias en diferencias / event study) | Corte del Sisbén III + vínculo de hogares entre cortes | No simulado aquí; la fuente de variación es la reclasificación por el cambio de metodología, no la necesidad | Pendiente: falta el corte III |
| 3 | Vinculación con llave real (DPS/RUI) + RD o IV | Registros administrativos con identificador | B y C: con llave se puede hacer RD; sin diseño causal la llave sola no basta | Pendiente: sin acceso a DPS |
| 4 | Cotas de identificación parcial (Fréchet-Manski + supuestos de monotonía) | Solo lo que ya hay | Acota el efecto sin suponer CIA; más informativa con supuestos creíbles (los elegibles son más necesitados) | Fréchet-Manski ya implementado (`cotas_frechet_manski.py`); falta sumar monotonía |
| 5 | Sensibilidad a variables omitidas (Cinelli-Hazlett / E-value) | Solo lo que ya hay | Cuánto tendría que pesar un factor no observado para anular el resultado | No implementado |
| 6 | Hot-Deck + DML (actual) | Lo que ya hay | No identifica el efecto (A); sirve como prueba placebo y para P1 a nivel de celda | Implementado |

## Qué significa para cada objetivo
- **P2/OE2 (efecto causal):** con las fuentes actuales solo se pueden reportar **cotas** (#4) y el placebo (#6). Un efecto puntual exige conseguir puntaje continuo o una llave (#1, #3) o el corte III (#2). Conviene decirlo así en la tesis y en la reunión con el tutor, y pedir esos datos ahora.
- **P1/OE1 (validez de clasificación):** con Hot-Deck la concordancia entre clasificación y pobreza solo existe **a nivel de celda** (ecológica), porque el grupo imputado es independiente del hogar receptor dentro de la celda. Un AUC o una matriz de error de inclusión/exclusión por hogar no se puede obtener con este emparejamiento (no simulado aquí; sigue del punto 1 de la lectura).
- **P3/OE3 (política):** las reglas contrafactuales con FGT1 dependen de un CATE confiable, que hoy es placebo. Se pueden simular reglas con efectos conocidos para calibrar el método, pero no reportar ganancias reales hasta resolver P2.

## Limitaciones de la simulación
- RD «nítido» con cumplimiento perfecto; en el proyecto la cadena es elegibilidad → participación en programas → bienestar (RD «difuso»), con estimador de Wald (efecto sobre el resultado / salto en participación).
- Un solo factor no observado, errores normales, efecto constante. No incluye la selección de quién está inscrito en el Sisbén (ver `RESULTADOS_REPRESENTATIVIDAD_SISBEN.md`).

## Para reproducir
```
poetry run python -m src.validacion.simulacion_identificacion 20 150000
```
Tarda alrededor de 30 segundos. Solo usa `numpy` y `pandas`.

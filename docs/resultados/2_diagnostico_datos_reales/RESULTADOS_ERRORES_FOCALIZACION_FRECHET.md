# Resultados — Errores de inclusión y exclusión del Sisbén con datos reales

Generado el 2026-11-10 por `src/diagnostico/errores_focalizacion_frechet.py`;
regenerado el 2026-11-14 con la celda que suma personas del hogar y
menores de 18 años (las cifras con la celda anterior, entre paréntesis
donde ayudan a comparar).
Detalle nacional y por departamento: `docs/reports/errores_focalizacion_frechet.csv`;
salida de consola: `docs/reports/errores_focalizacion_frechet.txt`.

## La pregunta

¿Qué parte de los hogares pobres queda fuera de los grupos A y B del
Sisbén (error de exclusión), y qué parte de los A/B no es pobre (error de
inclusión)? Hasta ahora estas tasas solo se habían reportado en el mundo
simulado (`RESULTADOS_REGLAS_FOCALIZACION.md`). Con datos reales no se
pueden contar, porque ningún hogar está a la vez en la GEIH (que dice
quién es pobre) y en el Sisbén (que dice quién es A/B).

## Método (propuesto por el director)

En cada celda c del Hot-Deck (departamento, ciclo de vida del jefe,
cuartos, nivel de pisos, personas y menores; 3.721 celdas) se conocen la proporción de pobres
p (GEIH, con factor de expansión) y la proporción de elegibles e
(Sisbén). Sin suponer nada sobre cómo se relacionan dentro de la celda,
las cotas de Fréchet dan:

$$\max(0,\,p-e) \le P(\text{pobre}=1,\ \text{elegible}=0 \mid c) \le \min(p,\,1-e)$$

$$\max(0,\,e-p) \le P(\text{pobre}=0,\ \text{elegible}=1 \mid c) \le \min(1-p,\,e)$$

Sumando con los factores de expansión de la GEIH salen las tasas
nacionales y departamentales, con las mismas definiciones de las reglas
simuladas:

- error de exclusión = pobres no elegibles / pobres;
- error de inclusión = elegibles no pobres / elegibles.

Los denominadores se conocen (Σ w·p y Σ w·e), así que la cota de cada
tasa es la de su numerador dividida por él. Como referencia se da el
valor con independencia dentro de la celda, p·(1 − e), que es el que
produce el Hot-Deck al sortear el grupo al azar en la celda.

Elegible = grupos A y B (el tratamiento del resto del proyecto); como
robustez, A, B y C. Unidad: hogares.

## Resultado nacional

| Elegible | Pobreza | Error de exclusión | Con independencia | Error de inclusión | Con independencia |
|---|---|---|---|---|---|
| A-B | Monetaria | **[2,8 %; 57,7 %]** | 33,8 % | **[41,2 %; 74,4 %]** | 59,9 % |
| A-B | IPM-GEIH | [1,0 %; 56,0 %] | 28,3 % | [67,9 %; 85,7 %] | 76,8 % |
| A-B | Monetaria oficial (24 deptos.) | [2,4 %; 58,2 %] | 33,4 % | [43,6 %; 75,9 %] | 61,6 % |
| A-B-C | Monetaria | [0,0 %; 27,5 %] | 9,3 % | [65,6 %; 75,1 %] | 68,8 % |
| A-B-C | IPM-GEIH | [0,0 %; 28,0 %] | 8,4 % | [81,6 %; 86,7 %] | 83,1 % |

Con la celda del 2026-11-02 (993 celdas), A-B y pobreza monetaria daban
exclusión [0,9 %; 75,0 %] e inclusión [38,6 %; 84,5 %]: personas y
menores cierran la exclusión 19 puntos (17 por arriba) y la inclusión 13.

Pobreza monetaria: 27,0 % de los hogares; IPM-GEIH: 14,5 % (20,4 % antes de corregir la vivienda por zona, 2026-11-12); A/B: 44,7 % de los hogares
registrados, con el peso de la GEIH en cada celda (43,6 % con la celda
anterior). Las 3.721 celdas tienen hogares de las dos fuentes (100 % del
peso de la GEIH).

## Por departamento (pobreza monetaria, A-B)

Detalle completo en el CSV. Los casos que más se apartan:

| Departamento | Pobreza | A/B | Error de exclusión | Error de inclusión |
|---|---|---|---|---|
| 11 Bogotá | 15,2 % | 19,7 % | **[11,5 %; 87,8 %]** | [31,5 %; 90,6 %] |
| 25 Cundinamarca | 18,8 % | 29,7 % | [8,0 %; 85,5 %] | [41,7 %; 90,8 %] |
| 27 Chocó | 55,8 % | 76,8 % | [1,2 %; 26,4 %] | [28,2 %; 46,5 %] |
| 44 La Guajira | 61,2 % | 74,3 % | [2,0 %; 27,3 %] | [19,3 %; 40,1 %] |
| 86 Putumayo | 50,8 % | 43,9 % | **[26,0 %; 67,2 %]** | [14,4 %; 62,1 %] |
| 88 San Andrés | 12,8 % | 13,2 % | **[35,0 %; 96,8 %]** | [37,0 %; 96,9 %] |
| 95 Guaviare | 28,0 % | 44,8 % | [8,1 %; 66,2 %] | [42,6 %; 78,9 %] |

## Cómo leerlo

1. **El error de inclusión tiene un piso que no depende de ningún
   supuesto dentro de la celda: al menos 41 % de los hogares A/B no son
   pobres monetarios** (al menos 68 % no son pobres por IPM). La razón es
   aritmética: el Sisbén clasifica como A/B a más hogares (44,7 %) de los
   que son pobres (27,0 %), y pasa lo mismo en el 77 % de las celdas (83 %
   del peso de la GEIH). Ninguna forma de acoplar las dos fuentes elimina
   ese exceso.
2. **El error de exclusión no se puede acotar lejos de cero a nivel
   nacional.** Los datos son compatibles con que casi todos los pobres
   estén en A/B (2,8 % excluidos) o con que más de la mitad quede fuera
   (57,7 %). Con la celda más fina el techo baja de 75,0 % a 57,7 %: la
   celda separa mejor a los hogares pobres y a los A/B, y ya no es
   compatible con los datos que tres de cada cuatro pobres queden fuera. Es el mismo problema de identificación de las cotas
   del efecto (`RESULTADOS_FRECHET_MANSKI.md`), aplicado a la
   focalización.
3. **Donde hay menos A/B que pobres, la exclusión sí tiene piso.** En
   Putumayo al menos 26,0 % de los pobres quedan fuera de A/B, en San
   Andrés al menos 35,0 %, en Bogotá al menos 11,5 % y en Cundinamarca y
   Guaviare al menos 8 %. Son los únicos resultados de exclusión con datos
   reales que no dependen del emparejamiento. El piso sale de las celdas
   con más pobres que A/B (672); el 92 % de su peso está en celdas con al
   menos 10 hogares GEIH, así que no es un efecto de celdas diminutas.
4. **El Hot-Deck es un punto dentro de la cota, no la respuesta.** Con
   independencia dentro de la celda, la exclusión sería 33,8 % y la
   inclusión 59,9 % (44,3 % y 65,5 % con la celda anterior). Se parece a
   lo que da la regla vigente en la simulación (27,8 %\* y 54,8 %\*,
   sobre personas y no sobre hogares), porque esa regla también sortea el
   grupo en la celda.
5. **Ampliar a A-B-C cambia una tasa por la otra:** la exclusión baja a
   lo sumo a 27,5 % y el piso de inclusión sube a 66 %.

\* Resultado simulado (semisintético).

## Alcance y supuestos

- **e es la proporción de A/B entre los hogares registrados en el
  Sisbén** y se toma como la de toda la celda en la GEIH. Es el mismo
  supuesto del Hot-Deck. La cobertura del registro varía entre
  departamentos (`RESULTADOS_REPRESENTATIVIDAD_SISBEN.md`). Si los
  hogares no registrados se contaran como no elegibles, habría menos
  elegibles en cada celda, y la exclusión sería mayor y la inclusión
  menor que en estas cotas.
- Las tasas son de hogares. Las de las reglas simuladas son de personas,
  así que la comparación del punto 4 es aproximada.
- Las cotas son de las proporciones poblacionales. No incluyen el error
  de muestreo de p y e por celda.
- Pruebas: `tests/test_errores_focalizacion_frechet.py`, que verifica
  que las tasas verdaderas de poblaciones al azar (5 semillas, con
  dependencia arbitraria dentro de la celda) caen dentro de la cota, que
  las cotas se alcanzan y que las definiciones coinciden con las de las
  reglas simuladas. La mutación correspondiente está en `tests/mutaciones.py`.

# Resultados — ¿Representa el Sisbén a la misma población que GEIH?

Generado por `src/validacion/verificar_representatividad_sisben.py`.
Detalle completo por departamento:
`docs/reports/representatividad_sisben_por_depto.csv`.

## La pregunta

El Hot-Deck y las cotas de Fréchet-Manski asumen, cada uno a su manera,
que el registro del Sisbén dice algo útil sobre la población de GEIH. Pero
el Sisbén solo cubre hogares que se inscribieron — **no es una muestra
aleatoria de la población de GEIH, es un registro administrativo de
demanda**. Si la tasa de inscripción fuera pareja entre departamentos, el
supuesto de "cobertura parcial pero uniforme" sería razonable. Si varía
mucho, hay sesgo de cobertura y hay que tenerlo presente al interpretar
cualquier resultado que compare ambas fuentes.

## Resultado

Razón de cobertura = hogares registrados en el Sisbén (con `Clasificacion`
observada, el pool donante real del Hot-Deck) ÷ hogares de la GEIH en un
mes promedio (expandidos con `FEX_C18`), por departamento y **sobre el
mismo marco**: en los 9 departamentos de la Orinoquía, la Amazonía y San
Andrés (81, 85, 86, 88, 91, 94, 95, 97, 99) la GEIH solo encuesta la
cabecera de la capital, y el Sisbén se cuenta también solo ahí.

| | Razón de cobertura | Departamento (código DIVIPOLA) |
|---|---|---|
| Mínima | 2,2 % | 85 — Casanare (cabecera de Yopal) |
| Máxima | 41,5 % | 11 — Bogotá |
| Nacional (agregada) | 16,8 % | — |
| Departamentos completos sin Bogotá (23) | 4,8 % a 26,9 % | 76 — Valle del Cauca a 15 — Boyacá |
| Cabeceras de las capitales (9) | 2,2 % a 22,1 % | 85 — Casanare a 99 — Vichada |

**Corrección del 2026-11-11: el mismo marco en las dos fuentes.** Hasta
esa fecha, en esos 9 departamentos se dividía el Sisbén de todo el
departamento entre la GEIH de la capital, y la razón pasaba del 100 %
(Putumayo 154 %, Vichada 97 %), lo que no puede ser una cobertura. En la
GEIH todos sus hogares ahí son urbanos (`CLASE` 1, `AREA` igual al código
del departamento); en el Sisbén, entre la mitad y el 90 % de los
registrados de esos departamentos viven fuera de la cabecera de la
capital. Con el mismo marco ninguna razón pasa de 41,5 %. Prueba y
mutación en `tests/test_ingesta_y_validacion.py`.

**Corrección del 2026-11-10.** Hasta esa fecha el denominador sumaba los
factores de expansión de los 12 meses de la GEIH, y cada mes se expande a
toda la población: los hogares salían 12 veces más (214,9 millones en vez
de 17,9) y las coberturas 12 veces menores.

**Bogotá compara otra fuente.** Su registro es el del SDP, un registro
administrativo completo y vigente, no el archivo nacional del Sisbén; su
41,5 % no es comparable con el resto. Sin Bogotá, la cobertura nacional
es 11,7 %.

**Factor de variación: 18,6x** entre el mínimo y el máximo; **8,7x** entre
los 24 departamentos completos (con Bogotá) y **5,6x** entre los 23 del
archivo nacional. Las coberturas más bajas están en departamentos urbanos
y de mayores ingresos (76-Valle, 08-Atlántico, 66-Risaralda,
05-Antioquia) y en las capitales de Casanare y San Andrés; las más altas,
fuera de Bogotá, en Boyacá, Chocó, Sucre y Caquetá, y en las capitales de
Vichada y Vaupés.

## Cómo leerlo

**No es un error de los datos — es exactamente lo esperable de un
registro de demanda**, y confirma empíricamente, con cifras reales, el
supuesto que había quedado solo como advertencia narrativa hasta ahora:
la inscripción al Sisbén no es pareja respecto al tamaño de la población.
Departamentos con más pobreza estructural tienden a tener una fracción
mayor de sus hogares registrados que departamentos más urbanos y de
mayores ingresos — razonable, porque el Sisbén es más relevante para
quien aspira a un subsidio, pero significa que el pool donante del
Hot-Deck no es una muestra representativa de "todos los hogares de ese
departamento", sino de "los hogares de ese departamento que buscaron
registrarse".

**Consecuencia directa para el resto del pipeline:**
- El Hot-Deck ya usa `geo_depto` en su celda, así que este sesgo queda
  parcialmente absorbido (compara GEIH contra Sisbén *dentro* del mismo
  departamento, no a nivel nacional) — pero **dentro** de cada
  departamento, sigue sin garantía de que los hogares registrados sean
  representativos de los no registrados.
- Refuerza la lectura de `docs/resultados/2_diagnostico_datos_reales/RESULTADOS_FRECHET_MANSKI.md`:
  la cota tan ancha que se encontró ahí (sin suponer independencia
  condicional) es consistente con este sesgo de cobertura real, no
  solo con una posibilidad teórica.
- Para cualquier interpretación de "a quién representa" el grupo asignado
  por Hot-Deck, hay que ser explícito: representa a los hogares *con
  perfil similar a quienes se registraron*, no a la población general del
  departamento.

## Limitaciones

- La razón de cobertura usa el pool donante COMPLETO del Sisbén (nacional
  + Bogotá, filtro de vigencia) contra la población TOTAL de GEIH —no se
  excluyen los hogares de GEIH que, por nivel de ingreso, nunca
  calificarían para registrarse (no hay forma de saberlo sin la variable
  real de inscripción en GEIH, que no existe).
- No se intenta aquí estimar qué fracción de la población "debería"
  estar registrada — solo se documenta que la cobertura observada no es
  uniforme.

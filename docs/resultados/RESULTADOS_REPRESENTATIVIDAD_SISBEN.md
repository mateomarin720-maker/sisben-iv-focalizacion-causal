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
observada, el pool donante real del Hot-Deck) ÷ hogares expandidos de GEIH
(población total, ponderada por `FEX_C18`), por departamento.

| | Razón de cobertura | Departamento (código DIVIPOLA) |
|---|---|---|
| Mínima | 0,4 % | 76 — Valle del Cauca |
| Máxima | 12,8 % | 86 — Putumayo |
| Nacional (agregada) | 1,4 % | — |

**Factor de variación: 32,3x** entre el departamento con menor y mayor
cobertura relativa. Los departamentos con cobertura más baja son
urbanos/grandes (76-Valle, 08-Atlántico, 66-Risaralda, 05-Antioquia); los
de cobertura más alta son departamentos pequeños, rurales y con mayor
incidencia de pobreza históricamente reportada (86-Putumayo, 99-Vichada,
85-Casanare, 81-Arauca, 95-Guaviare).

## Cómo leerlo

**No es un error de los datos — es exactamente lo esperable de un
registro de demanda**, y confirma empíricamente, con cifras reales, el
supuesto que había quedado solo como advertencia narrativa hasta ahora:
la inscripción al Sisbén no es pareja respecto al tamaño de la población.
Departamentos con más pobreza estructural tienden a tener una fracción
mucho mayor de sus hogares registrados que departamentos más urbanos y de
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
- Refuerza la lectura de `docs/resultados/RESULTADOS_FRECHET_MANSKI.md`:
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

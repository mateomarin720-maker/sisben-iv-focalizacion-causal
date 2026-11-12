# Validación del IPM-GEIH contra la ECV y el IPM oficial

Generado por `src/validacion/validar_ipm_geih_ecv.py` (salida:
`docs/reports/validacion_ipm_geih_ecv*.{txt,csv}`). Responde a la
anotación del director: «proxy propio sin validar; o se valida contra la
ECV o se retira».

## Por qué se puede validar

El IPM oficial del DANE se calcula con la Encuesta Nacional de Calidad de
Vida (ECV), y la ECV usa los mismos códigos de pregunta que la GEIH para
las 8 privaciones del proxy (`P6160`, `P6090`, `P6920`, `P5010`,
acueducto y alcantarillado; el nivel educativo es `P8587` en la ECV y
`P3042` en la GEIH, con las mismas categorías; la asistencia escolar,
`P8586` frente a `P6170`). Las reglas del proxy están en un solo lugar
(`src/indicadores/ipm_proxy.py`) y las usan tanto la GEIH como la
validación: el proxy validado es exactamente el que se estima.

Dos comparaciones, con hogares ponderados por el factor de expansión:

- **A. Hogar por hogar, contra el IPM oficial 2024.** La base del IPM 2024
  (Azure, `0_raw/ipm/2024/`) sale de la misma ECV 2024: coinciden el 100 %
  de sus `DIRECTORIO` y de sus factores de expansión. Trae, para cada
  hogar, las respuestas crudas y la clasificación oficial (15
  privaciones, corte del 33 %). Se calcula el proxy en esos mismos
  hogares y se compara con `POBRE` oficial; la zona sale del módulo de
  vivienda de la ECV.
- **B. Mismo año, ECV 2024 frente a GEIH 2024.** El proxy en los módulos
  crudos de la ECV 2024 frente al de la GEIH 2024.

Todo se lee directo de Azure, sin copiarlo a `data/`. La base del IPM que
estaba en `data/0_raw/ipm/nacional/` es la de 2025 (`PERIODO` = 20250731;
sus factores no coinciden con la ECV 2024); se usa solo como contraste.

## A. El proxy frente a la clasificación oficial 2024, hogar por hogar

77.568 hogares. La tasa oficial de hogares pobres es 9,2 %.

| Corte K | Tasa del proxy | Concordancia | Sensibilidad | Especificidad | Kappa |
|---|---|---|---|---|---|
| 2 | 41,7 % | 65,9 % | 91,3 % | 63,3 % | 0,21 |
| **3 (adoptado)** | **18,7 %** | **85,6 %** | **73,5 %** | **86,8 %** | **0,41** |
| 4 | 7,5 % | 91,8 % | 46,4 % | 96,4 % | 0,47 |
| 5 | 1,9 % | 92,5 % | 19,6 % | 99,9 % | 0,30 |

Sensibilidad: de los hogares pobres según el IPM oficial, cuántos marca
el proxy. Especificidad: de los no pobres, cuántos deja fuera. La
correlación de rangos entre el puntaje del proxy (0 a 8) y el IPM oficial
es **0,72**. Con la base 2025 los resultados son casi iguales (proxy
18,3 %, oficial 8,1 %, concordancia 86,0 %, kappa 0,41).

### Por zona (K = 3)

| Zona | Proxy | Oficial | Concordancia | Sensibilidad | Kappa |
|---|---|---|---|---|---|
| Cabeceras | 6,5 % | 5,9 % | 93,8 % | 52,7 % | 0,47 |
| Centros poblados y rural disperso | 63,7 % | 21,5 % | 55,4 % | 94,4 % | 0,23 |

**Lectura.**
- El proxy ordena a los hogares como el IPM oficial (correlación 0,72;
  kappa moderado), pero **no reproduce su nivel**: con K = 3 marca como
  pobres al 18,7 % de los hogares, el doble del 9,2 % oficial.
- **La sobreestimación es rural.** En las cabeceras el proxy da casi la
  tasa oficial (6,5 % frente a 5,9 %); en la zona rural la triplica
  (63,7 % frente a 21,5 %). Ahí pesan dos privaciones definidas distinto
  que en el IPM: la falta de alcantarillado, que el proxy cuenta igual en
  lo rural, y la falta de cotización a pensión del jefe, casi universal
  en el campo.
- **El corte que reproduce la tasa oficial nacional es K = 4** (7,5 %
  frente a 9,2 %), con la mayor concordancia y el mayor kappa. K = 3 se
  había elegido por cercanía a un 13 % que era la tasa sin ponderar de la
  base 2025, no la oficial (`docs/insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md`).
  Cambiarlo mueve todos los resultados con `POBRE_GEIH`; queda como
  decisión del equipo.

### Cada privación frente a la oficial (base 2024)

| Privación del proxy | Oficial | Prevalencia proxy | Prevalencia oficial | Kappa |
|---|---|---|---|---|
| Analfabetismo (jefe) | Analfabetismo | 4,2 % | 7,1 % | 0,73 |
| Bajo logro educativo (jefe) | Bajo logro educativo | 31,4 % | 39,3 % | 0,70 |
| Inasistencia escolar (6-16 años) | Inasistencia escolar | 1,8 % | 1,8 % | 0,99 |
| Sin aseguramiento en salud (jefe) | Sin aseguramiento | 3,1 % | 6,0 % | 0,66 |
| Sin cotización a pensión (jefe) | Trabajo informal | 72,1 % | 70,7 % | 0,64 |
| Hacinamiento | Hacinamiento crítico | 3,0 % | 6,1 % | 0,64 |
| Sin alcantarillado | Sin alcantarillado | 22,8 % | 9,1 % | 0,50 |
| Sin acueducto | Sin acueducto | 9,0 % | 8,6 % | 0,88 |

Las diferencias vienen de la definición, no de los datos (son los mismos
hogares y las mismas respuestas): varias privaciones oficiales miran a
todos los miembros del hogar y el proxy solo al jefe, por lo que el proxy
marca menos analfabetismo, bajo logro y falta de aseguramiento; el
hacinamiento oficial usa otro umbral en la zona urbana. La de mayor
diferencia es alcantarillado (22,8 % frente a 9,1 %), porque la
definición oficial trata distinto la zona rural. Las definiciones
oficiales están en la metodología del IPM (Azure,
`0_raw/ipm/2024/docs_ipm/Metodologia_IPM.pdf`); conviene citarlas al
discutir esta tabla.

## B. ECV 2024 frente a GEIH 2024, el mismo proxy

| | ECV 2024 | GEIH 2024 |
|---|---|---|
| Hogares | 85.387 | 290.968 |
| `POBRE_GEIH` nacional | 19,6 % | 20,4 % |
| Cabeceras | 6,5 % | 7,1 % |
| Centros poblados y rural disperso | 64,9 % | 68,6 % |
| Puntaje medio (0 a 8) | 1,49 | 1,51 |

Por departamento, sobre el mismo marco:

| | Departamentos | Correlación | Diferencia media GEIH − ECV | Diferencia absoluta mediana |
|---|---|---|---|---|
| Departamento completo | 24 | 0,988 | +2,1 puntos | 2,2 puntos |
| Cabecera de la capital | 9 | 0,968 | −3,4 puntos | 4,6 puntos |

En los 9 departamentos de la Orinoquía, la Amazonía y San Andrés la GEIH
solo encuesta la cabecera de la capital; ahí la ECV se restringe a la
misma cabecera (municipio 001, `CLASE` 1). Las prevalencias de cada
privación coinciden entre las dos encuestas dentro de 1,5 puntos
(`validacion_ipm_geih_ecv_privaciones.csv`).

**Lectura.** Con las mismas reglas, la GEIH 2024 y la ECV 2024 dan el
mismo indicador: 0,8 puntos de diferencia nacional y correlación de 0,99
entre departamentos. El proxy no es un artefacto de la GEIH.

## Conclusión para el documento

1. **El proxy está validado como medida de privación** (mide lo mismo en
   la GEIH que en la ECV, la encuesta del IPM oficial) y **como
   ordenamiento** (correlación 0,72 con el IPM oficial 2024, hogar por
   hogar).
2. **No es el IPM oficial ni reproduce su tasa.** Con K = 3 duplica la
   incidencia oficial, por la zona rural; en las cabeceras la reproduce.
   Debe presentarse como «índice de privaciones con 8 de los 15
   indicadores, validado contra la ECV», no como IPM.
3. Para los resultados causales esto pesa poco: con el grupo imputado el
   DML es un placebo (Proposición 1) y da cero con cualquier medida de
   resultado; las cotas de Fréchet-Manski usan solo la proporción de
   pobres por celda.

## Reproducir

```bash
poetry run python -m src.validacion.validar_ipm_geih_ecv
```

Lee de Azure, en memoria: `0_raw/ipm/2024/BasesDatos-IMP-2024.zip` (IPM
2024), `0_raw/ipm/nacional/*.csv` (IPM 2025) y seis módulos de la ECV 2024
bajo `ecv/` (`Caracteristicas_composicion_hogar`, `Educacion`,
`Salud2024`, `Fuerza_trabajo`, `Servicios_hogar`, `Datos_vivienda`). Pide
las credenciales de Azure del `.env`.

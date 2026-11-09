# Pobreza monetaria con GEIH 2024: auditoría de variables y metodología propuesta

Estado: **Fase 1 revisada; decisiones D1-D7 cerradas el 2026-11-02.** La
construcción está en `01_diccionario_ingreso.md` y
`src/indicadores/pobreza_monetaria_geih.py`; los resultados, en
`docs/resultados/RESULTADOS_POBREZA_MONETARIA.md`. Este documento se
conserva como auditoría. **Corrección:** `P6430` = 7 es jornalero, no
"sin remuneración" (ver §1.1).

Insumos usados: microdatos GEIH 2024 (12 meses, 8 módulos,
`data/1_processed/geih/2024/`), diccionario oficial
`docs/insumos/DICCIONARIO_GEIH_2024.xlsx` y boletín técnico DANE *Pobreza
Monetaria en Colombia, año 2024* (`docs/insumos/DANE_boletin_PM_2024.pdf`).
Inventario reproducible: `src/indicadores/inventario_ingresos_geih.py` →
`docs/reports/inventario_ingresos_geih.csv` (46 variables, todas presentes
en el diccionario y en los datos).

---

## 0. Lo más importante

1. **La cifra oficial no es reproducible con los microdatos públicos de
   GEIH.** El boletín anota en cada cifra: *"Cruce GEIH – RR.AA. ayudas
   institucionales y PILA (Ministerio de Salud)"*. El ingreso oficial
   reemplaza o complementa lo declarado con registros administrativos de
   subsidios y de cotizaciones que no vienen en GEIH. Además, el paso 2
   de la metodología (modelo de imputación para corregir sesgos de
   reporte) no se publica. Cualquier agregado construido aquí es una
   **reconstrucción**, y así se va a nombrar.
2. **`INGLABO` NO está imputado por el DANE.** Documentación anterior del
   proyecto lo afirmaba (ver §8). La verificación con datos muestra que es
   un consolidado: ingreso principal + especie + segundo trabajo, y queda
   vacío justo donde falta el ingreso declarado.
3. **El outcome monetario actual (`3b_preprocesamiento_monetario.py`) tiene
   siete diferencias metodológicas** frente a lo que pide esta tarea
   (§7). Ninguna invalida lo hecho como aproximación, pero la nueva
   versión debe corregirlas antes de usarse.
4. **Recomendación previa a construir:** descargar del portal de
   microdatos del DANE la base anonimizada de *Medición de pobreza
   monetaria y desigualdad 2024*. El boletín dice que el DANE la pone a
   disposición. Si trae las llaves de GEIH (`DIRECTORIO`, `SECUENCIA_P`,
   `ORDEN`), se puede cruzar el ingreso per cápita oficial de la unidad de
   gasto hogar por hogar y usarlo como referencia exacta. Los nombres de
   sus variables hay que verificarlos al descargarla, no se asumen aquí.

---

## 1. Variables de ingreso disponibles (Fase 1, puntos 1-3)

Cobertura sobre los 12 meses apilados. Detalle completo y etiquetas
oficiales en el CSV del inventario. "% > 0" se mide sobre todas las filas
del módulo e incluye los códigos 98.

### 1.1 Agregado construido por el DANE dentro de GEIH

Solo uno: **`INGLABO`** ("Ingresos laborales", módulo Ocupados), con
94,9 % de ocupados con valor > 0. Se verificó en enero contra sus
componentes:

| Grupo | Comparación | Resultado |
|---|---|---|
| Asalariados (`P6430` ∈ {1,2}) | `INGLABO` = `P6500` | 92,6 % exacto, nunca menor |
| Asalariados con `INGLABO` > `P6500` | diferencia = especie (`P6590S1`-`P6620S1`) + segundo trabajo (`P7070`) | explica el 92,1 % |
| Cuenta propia (`P6430` = 4) | `INGLABO` = `P6750` | 94,4 % exacto |
| Horas extra declaradas aparte (`P6510S2` = 2) | ¿están en `INGLABO`? | No: en 343 casos `INGLABO` = `P6500` exacto |

Faltantes de `INGLABO` en enero: la mayoría son no respuesta real de
asalariados e independientes; los trabajadores familiares sin
remuneración (`P6430` = 6, 506 en enero, 100 % vacíos) valen 0.
**Corregido 2026-11-02:** esta sección decía `P6430` ∈ {6,7}. Los números
de `P6430` no siguen el orden de las letras del diccionario: el 7 es
jornalero o peón (99 % declara `P6500`) y sin remuneración son el 6 y el
8.

No existen en GEIH las variables de ingreso total, ingreso de la unidad
de gasto, número de personas de la unidad de gasto ni líneas de pobreza.

### 1.2 Inventario por componente

| Componente | Variables | Periodicidad | ¿En `INGLABO`? | Tratamiento propuesto |
|---|---|---|---|---|
| Salario y ganancia | `P6500`, `P6750`, `P7070` | mensual | sí | no sumar de nuevo |
| Especie de asalariados | `P6590S1`, `P6600S1`, `P6610S1`, `P6620S1` | mensual | sí | no sumar de nuevo |
| Horas extra, primas y bonificaciones mensuales | `P6510S1`, `P6545S1`, `P6580S1` | mensual | solo si el hogar dijo que estaban incluidas (`S2` = 1) | sumar si `S2` = 2 |
| Auxilios (alimentación, transporte, familiar, educativo) | `P6585S1A1`-`S4A1` | mensual | solo si `A2` = 1 | sumar si `A2` = 2 |
| Primas anuales (servicios, navidad, vacaciones, bonificación anual) | `P6630S1A1`-`S4A1` | **anual** | no | sumar ÷ 12 |
| Ganancia anual rural | `P550` (solo centros poblados y rural disperso) | anual | por verificar | decisión pendiente (§6, D4) |
| Bruto de independientes | `P3051`, `P3052` | mensual | no | **no sumar**: `P3052` ≥ `P6750` en el 99 % de los casos, es el bruto del mismo ingreso |
| Especie de independientes | `P3054S1`, `P3055S1` | mensual | por verificar | decisión pendiente |
| Trabajo de no ocupados | `P7422S1` | mensual | no | sumar |
| Arriendos, pensiones, pensión alimenticia | `P7500S1A1`, `S2A1`, `S3A1` | mensual | no | sumar |
| Transferencias de hogares y remesas | `P7510S1A1`, `S2A1` | anual | no | sumar ÷ 12 |
| Ayudas institucionales | `P7510S3A1` (total) | anual | no | sumar ÷ 12, **solo el total** |
| Detalle de ayudas | `P750S1A1`-`S3A1`, `P1661S1A1`-`S4A2` | anual | no | **no sumar**: anidadas (ver abajo) |
| Rendimientos de capital | `P7510S5A1` | anual | no | sumar ÷ 12 |
| Cesantías | `P7510S6A1` | anual | no | decisión pendiente (D5) |
| Ingresos ocasionales (loterías, indemnizaciones, venta de bienes) | `P7510S7A1` | anual | no | **excluir**: el boletín excluye ingresos ocasionales |
| Accidentes de trabajo | `P6630S6A1` | anual | no | decisión pendiente (D5) |
| Vivienda propia | `P5090` (tenencia), `P5130` (arriendo estimado), `P5100` (amortización) | mensual | no | ajuste por propiedad (D3) |

**Anidamiento verificado (enero, 100 % de los casos):**
`P7510S3A1` = `P750S1A1` + `P750S2A1` + `P750S3A1`, y
`P750S2A1` (gobierno) = suma de `P1661S*` (Más Familias en Acción, Jóvenes
en Acción, Colombia Mayor, otro). Sumar los niveles juntos duplicaría las
transferencias.

**Código 98** ("recibió pero no sabe el monto"): aparece en casi todos
los componentes, por ejemplo 4.493 casos en prima de servicios y 2.517
en transferencias de otros hogares. Es no respuesta, no $98.

---

## 2. Unidad de gasto (Fase 1, puntos 4-5)

El boletín (nota 1): *"la unidad de gasto excluye pensionistas y
empleados(as) domésticos(as) del hogar"*. En el lenguaje de hogares del
DANE, **pensionista es quien paga por alojamiento y comida en el hogar**,
no quien recibe una pensión de jubilación. No se debe confundir con
`P7500S2`.

Variable: `P6050` (parentesco con el jefe). **Inconsistencia documental:**
el texto del diccionario lista 9 categorías (a-i), pero los microdatos
traen 13 códigos (1-13). Las letras no se pueden mapear a los números.
Se corroboró con datos:

| Código | Personas (12 m) | Evidencia | Lectura |
|---|---|---|---|
| 10 | 1.378 | 102 de 108 ocupados en enero tienen `P6430` = 3 (empleado doméstico); 49 menores de 15 años | servicio doméstico **y sus parientes**: confirmado |
| 11 | 213 | enero: mediana de edad 21,5, nadie recibe pensión | pensionista o trabajador: **no se puede distinguir** |
| 12 | 82 | enero: mediana de edad 35,5 | pensionista o trabajador: **no se puede distinguir** |

Los códigos 10, 11 y 12 suman el 0,17 % de la población expandida. El
impacto en las tasas es despreciable, pero la regla debe quedar
documentada. Propuesta: excluir el 10 seguro y correr el 11 y el 12 como
sensibilidad (D2). Hace falta la lista oficial de códigos de `P6050` para
GEIH 2024 (la ficha de variables del portal de microdatos).

Llave de hogar: `DIRECTORIO` + `SECUENCIA_P` (+ `HOGAR`), normalizadas como
ya hace el proyecto (`_norm_llave`).

---

## 3. Líneas de pobreza 2024 (Fase 1, punto 6)

Fuente: boletín DANE 2024, tablas 1 y 4 (pesos corrientes, mensual per
cápita).

| Dominio | Línea de pobreza | Línea de pobreza extrema |
|---|---|---|
| Total nacional (solo referencia) | 460.198 | 227.220 |
| Cabeceras | 510.161 | 242.389 |
| Centros poblados y rural disperso | 291.998 | 176.154 |
| 13 ciudades y A.M. | 566.228 | 256.922 |
| Otras cabeceras | 434.323 | 222.730 |

El boletín aclara que estas son **líneas ponderadas por la población de
las áreas de cada dominio**. El DANE clasifica a cada persona con la línea
de su área (ciudad o resto), que es más fina. Esas líneas por área están
en los anexos estadísticos, que no están en el repositorio.

Asignación de dominio con GEIH, verificada en los 12 meses:

| Dominio | Regla | % de la población expandida |
|---|---|---|
| 13 ciudades y A.M. | `CLASE` = 1 y `AREA` ∈ {05, 08, 11, 13, 17, 23, 50, 52, 54, 66, 68, 73, 76} | 43,9 % |
| Otras cabeceras | `CLASE` = 1 y resto | 33,4 % |
| Centros poblados y rural disperso | `CLASE` = 2 | 22,7 % |

`AREA` nunca está diligenciada con `CLASE` = 2, así que no hay casos
ambiguos.

Propuesta: **versión A**, líneas por área de los anexos (preferida,
requiere el insumo); **versión B**, las tres líneas de dominio de la
tabla (disponible ya). En ningún caso se usa una línea nacional uniforme.
El outcome actual usa solo dos (cabecera y rural), lo que subestima la
línea de las 13 ciudades y sobreestima la de las otras cabeceras.

---

## 4. Factores de expansión, unidad de análisis y cobertura (Fase 3)

- **Factor:** `FEX_C18`. Cada mes expande por sí solo a la población
  total: entre 51,31 M (enero) y 51,79 M (diciembre). Para el agregado
  anual se usa **`FEX_C18 / 12`** (51,55 M de personas). Para tasas da lo
  mismo; para totales no.
- **Duplicados entre meses:** 0 `DIRECTORIO` repetidos entre cualquier par
  de meses (288.604 directorios en total). La muestra anual no es un
  panel, así que se apilan los 12 meses sin deduplicar.
- **Cobertura:** 12 de 12 meses y 829.683 personas. El tamaño mensual
  baja de 72.148 personas (febrero) a 64.627 (diciembre); el factor lo
  compensa.
- **Unidad de análisis:** el DANE calcula sobre **personas** (anexo FGT del
  boletín: *n* = número total de personas). Cada persona de la unidad de
  gasto hereda el ingreso per cápita de su unidad y se pondera con su
  propio factor. El outcome actual calcula tasas sobre hogares; ese es uno
  de sus sesgos (§7).

---

## 5. Metodología propuesta (Fases 2-5)

### 5.1 Construcción (Fase 2)

Se nombrará como reconstrucción: archivo
`muestra_pobreza_monetaria_reconstruida_2024.parquet`, columna
`FUENTE_PM = "reconstruccion_geih_publica"`. Variables canónicas:

| Variable | Definición propuesta |
|---|---|
| `INGRESO_CORRIENTE_UG` | Suma, sobre los miembros de la unidad de gasto, de: `INGLABO` (0 si no remunerado) + componentes laborales no incluidos (§1.2) + primas anuales ÷ 12 + `P7422S1` + `P7500S*` + transferencias anuales ÷ 12 + capital ÷ 12, **sin** ocasionales; más el ajuste por vivienda propia a nivel hogar (D3) |
| `PERSONAS_UG` | Personas del hogar sin `P6050` = 10 (y 11 o 12 según D2) |
| `INGRESO_PC_UG` | `INGRESO_CORRIENTE_UG / PERSONAS_UG` |
| `LP_2024`, `LI_2024` | Línea del dominio de la persona (versión B) o de su área (versión A) |
| `POBRE_MONETARIA` | `INGRESO_PC_UG < LP_2024` |
| `POBRE_EXTREMA` | `INGRESO_PC_UG < LI_2024` |
| `BRECHA_PM` | `max(0, (LP_2024 − INGRESO_PC_UG) / LP_2024)` |

**No respuesta** (`INGLABO` vacío en ocupados remunerados, códigos 98 y
99): tres variantes, para no esconder la decisión.

1. *Cero* (como el outcome actual): sesga hacia más pobreza.
2. *Hot-deck* dentro de celdas de sexo × edad × educación × posición
   ocupacional × rama × dominio, con donantes de la misma GEIH. **Nunca
   con variables del Sisbén.** Es la versión principal propuesta.
3. *Caso completo*: excluir los hogares con faltantes y reponderar.

El DANE imputa con su propio modelo (paso 2, no publicado). Nuestra
imputación es distinta y se documenta como tal.

### 5.2 Validación (Fase 3)

Comparación contra cifras del boletín disponibles hoy:

- Incidencia de pobreza y de pobreza extrema: nacional (31,8 / 11,7),
  cabeceras (28,6 / 8,7), centros poblados y rural disperso (42,5 / 21,8),
  13 ciudades y A.M. (24,0 / 5,9), otras cabeceras (34,8 / 12,4).
- Brecha de pobreza: nacional 12,6, cabeceras 11,0, rural 17,9, 13
  ciudades 8,9, otras cabeceras 13,9.
- Incidencia en las 23 ciudades capitales (gráfico 5 del boletín).
- Distribución: Gini nacional 0,551; cabeceras 0,530; centros poblados y
  rural disperso 0,482; 13 ciudades 0,522; otras cabeceras 0,490.
- Perfiles por jefe de hogar (tablas 2-5 del boletín).

**Departamentos** y **deciles del ingreso**: no están en el boletín, están
en los anexos estadísticos (insumo pendiente). Las diferencias se
documentan sin recalibrar los datos para forzar coincidencias.

### 5.3 Indicadores FGT (Fase 4)

FGT0, FGT1 y FGT2 sobre **personas**, ponderados por `FEX_C18 / 12`, para
nacional, los 4 dominios, las 23 ciudades (`AREA`) y los departamentos
(`DPTO`). Se reporta también la versión por hogares, rotulada aparte, para
comparar con el outcome anterior.

### 5.4 Comparación con Sisbén e IPM (Fase 5)

Matriz por persona (y por hogar, rotulada aparte) con:

- `POBRE_MONETARIA`, `POBRE_EXTREMA`;
- `POBRE_GEIH`: IPM-GEIH del proyecto, que cubre 8 de las 15 privaciones
  oficiales, así que no es el IPM oficial;
- `GRUPO_SISBEN_HOTDECK`: grupo **imputado** por Hot-Deck, nunca llamado
  "clasificación Sisbén observada".

Se calculan cuatro perfiles (pobre en ambos, solo monetario, solo
multidimensional, ninguno) y, tomando A/B del Hot-Deck como "focalizado":
errores de inclusión y exclusión, precisión, sensibilidad y brechas, por
grupo, zona y departamento.

**Advertencia de interpretación, a decidir antes de la Fase 5:** el
Hot-Deck sortea el donante al azar *dentro de la celda* (departamento ×
ciclo de vida × tramo de cuartos). Por construcción, el grupo imputado
solo varía con la celda, no con el ingreso del hogar receptor. Los
errores de inclusión y exclusión calculados así miden **qué tan bien
coincide la composición Sisbén de la celda con la pobreza de la celda**,
no los errores de focalización del Sisbén hogar por hogar. Comparar
tasas por celda puede ser más honesto que reportar precisión y
sensibilidad individuales (D6).

### 5.5 Productos (Fase 6)

| Producto | Ubicación propuesta | Estado |
|---|---|---|
| Inventario de variables | `docs/reports/inventario_ingresos_geih.csv` | ✅ |
| Diccionario de ingreso | `docs/metodologia/pobreza_monetaria/01_diccionario_ingreso.md` | después de la revisión |
| Script reproducible | `src/indicadores/pobreza_monetaria_geih.py` | después de la revisión |
| Parquet | `data/2_models/muestra_pobreza_monetaria_reconstruida_2024.parquet` | después de la revisión |
| Comparación oficial | `docs/reports/validacion_pobreza_monetaria.csv` | después de la revisión |
| Reporte metodológico y de resultados | `docs/resultados/RESULTADOS_POBREZA_MONETARIA.md` (reescrito) | después de la revisión |

---

## 6. Decisiones que requieren revisión

| # | Decisión | Propuesta |
|---|---|---|
| D1 | ¿Se consigue la base oficial de pobreza monetaria 2024 del DANE? | Sí, antes de construir: puede volver innecesaria buena parte de la reconstrucción |
| D2 | Pensionista: código 11 o 12 de `P6050` | Excluir 10; 11 y 12 como sensibilidad (295 personas, 0,04 % de la muestra) |
| D3 | Ajuste por vivienda propia: a quién (`P5090` = 1, 2, ¿4 usufructo?, ¿5 posesión?), con qué valor (`P5130` está 100 % diligenciado para esas tenencias) y si se descuenta la amortización (`P5100`) | Propietarios 1-2 con `P5130`; usufructo como sensibilidad. La regla exacta del DANE no está en el boletín |
| D4 | Rural: ¿`P6750` del mes o `P550` anual ÷ 12? | Verificar contra `INGLABO` cuál usa el DANE |
| D5 | Cesantías y pagos por accidente: ¿corrientes u ocasionales? | Excluir en la versión principal; incluir como sensibilidad |
| D6 | Fase 5: métricas individuales o por celda | Por celda como principal; individuales con advertencia |
| D7 | Líneas por área (versión A) | Conseguir los anexos estadísticos 2024 del boletín |

---

## 7. Diferencias del outcome actual (`3b_preprocesamiento_monetario.py`)

| # | Outcome actual | Lo que pide la metodología |
|---|---|---|
| 1 | Personas del hogar completo (`hog_num_personas`) | Unidad de gasto sin servicio doméstico ni pensionistas |
| 2 | Tasas FGT sobre hogares | Sobre personas |
| 3 | Dos líneas (cabecera y rural) | Líneas por dominio o área |
| 4 | Incluye `P7510S7A1` (ingresos ocasionales) | Excluirlos |
| 5 | Omite primas anuales, auxilios y extras no incluidos en `INGLABO` | Sumarlos |
| 6 | `INGLABO` vacío → 0 y código 98 → $98 | Tratarlos como no respuesta |
| 7 | Sin ajuste por vivienda propia | Ajustar |

Los puntos 1 y 2 cambian el numerador y el denominador del ingreso per
cápita de los hogares con servicio doméstico o pensionistas, y la base de
las tasas. Los puntos 5, 6 y 7 empujan hacia más
pobreza y explican parte de la sobreestimación de 5-6 puntos frente a la
cifra oficial. El punto 4 empuja en la dirección contraria. El resto de la
diferencia viene del cruce con registros administrativos y del modelo de
imputación del DANE, que no son reproducibles (§0).

---

## 8. Correcciones a la documentación previa del proyecto

Se escribió en varios documentos que `INGLABO` está "ya imputado por el
DANE" y que `P6500` tiene "47,7 % de no respuesta". Las dos afirmaciones
son incorrectas:

- `P6500` solo se le pregunta a asalariados. El 47,7 % de vacíos son
  independientes, que declaran su ingreso en `P6750`. No es no respuesta.
- `INGLABO` no está imputado: consolida el ingreso principal de cada tipo
  de ocupado. El primer intento de reconstrucción falló porque no tomaba
  `P6750` de los independientes, y `INGLABO` lo corrigió por eso, no por
  imputar.

Archivos con la afirmación: `src/3b_preprocesamiento_monetario.py`,
`src/README.md`, `docs/resultados/RESULTADOS_POBREZA_MONETARIA.md`,
`docs/resultados/README.md`, `docs/resultados/DIAGNOSTICO_W_CELDA_EXACTA.md`,
`docs/seguimiento/RESUMEN_AVANCES.md`,
`docs/seguimiento/CHANGELOG_PENDIENTES.md`. Se corrigen al construir la
nueva versión, que reemplaza ese texto. Mientras tanto,
`RESULTADOS_POBREZA_MONETARIA.md` lleva un aviso que remite a esta
sección.

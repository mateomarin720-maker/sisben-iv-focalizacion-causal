# Matriz de homologación GEIH ↔ Sisbén IV — 15 privaciones del IPM

*Generado por `src/indicadores/homologacion_ipm.py` — no editar a mano; cambiar `MATRIZ` y volver a correr.*

Regla oficial: DANE, *Metodología Índice de Pobreza Multidimensional (IPM)* ([met-IPM.pdf](https://www.dane.gov.co/files/operaciones/PM/met-IPM.pdf)), §3.2.1, pp. 15-26. Códigos GEIH: `docs/insumos/DICCIONARIO_GEIH_2024.xlsx`. Códigos Sisbén: `docs/insumos/DICCIONARIO_SISBEN_2024.xlsx` (solo Nombre/Etiqueta: las preguntas Sisbén se asocian por etiqueta; la regla con que el DNP calcula `I1`-`I15` no está documentada en el repositorio).

`I1`-`I15` y `H_5` del Sisbén son solo referencia conceptual: **nunca** se usan como outcome.

Interpretación y decisiones pendientes: [`00_auditoria_variables.md`](00_auditoria_variables.md).

## Resumen

| Id | Privación | Dimensión | Peso oficial | Variables GEIH | Preguntas Sisbén | Estado |
|---|---|---|---|---|---|---|
| I1 | Bajo logro educativo | Condiciones educativas | 0.10 | `P3042`, `P3042S1`, `P6040` | `PER017`, `PER002` | **homologable** |
| I2 | Analfabetismo | Condiciones educativas | 0.10 | `P6160`, `P6040` | `PER015`, `PER002` | **homologable** |
| I3 | Inasistencia escolar | Niñez y juventud | 0.05 | `P6170`, `P6040` | `PER016`, `PER002` | **homologable** |
| I4 | Rezago escolar | Niñez y juventud | 0.05 | `P3042`, `P3042S1`, `P6040` | `PER017`, `PER016`, `PER002` | **homologable** |
| I5 | Barreras a servicios de cuidado de la primera infancia | Niñez y juventud | 0.05 | `P6090`, `P6170`, `P6040` | `PER013`, `PER014`, `PER007`, `PER016`, `PER002` | **no disponible** |
| I6 | Trabajo infantil | Niñez y juventud | 0.05 | `OCI`, `P6040` | `PER019`, `PER002` | **parcialmente homologable** |
| I7 | Desempleo de larga duración | Trabajo | 0.10 | `FT`, `DSI`, `P7250`, `P6920`, `P7500S2` | `PER019` | **homologable** |
| I8 | Trabajo informal | Trabajo | 0.10 | `FT`, `OCI`, `DSI`, `P6920`, `P7500S2`, `P6040` | `PER018`, `PER020`, `PER019` | **homologable** |
| I9 | Sin aseguramiento en salud | Salud | 0.10 | `P6090`, `P6040` | `PER007`, `PER002` | **homologable** |
| I10 | Barreras de acceso a servicios de salud | Salud | 0.10 | — | `PER008`, `PER009`, `PER010` | **no disponible** |
| I11 | Sin acceso a fuente de agua mejorada | Vivienda y servicios públicos | 0.04 | `P4030S5`, `P5050`, `CLASE` | `viv008`, `hog007` | **homologable** |
| I12 | Inadecuada eliminación de excretas | Vivienda y servicios públicos | 0.04 | `P4030S3`, `P5020`, `CLASE` | `viv005`, `hog004` | **homologable** |
| I13 | Material inadecuado de pisos | Vivienda y servicios públicos | 0.04 | `P4020` | `viv003` | **homologable** |
| I14 | Material inadecuado de paredes exteriores | Vivienda y servicios públicos | 0.04 | `P4010`, `CLASE` | `viv002` | **homologable** |
| I15 | Hacinamiento crítico | Vivienda y servicios públicos | 0.04 | `P6008`, `P5010`, `CLASE` | `hog003`, `hog027` | **homologable** |

## Detalle por privación

### I1. Bajo logro educativo — *homologable*

| Campo | Contenido |
|---|---|
| Dimensión (peso oficial) | Condiciones educativas (0.10) |
| Variable GEIH original | `P3042`, `P3042S1`, `P6040` |
| Variable armonizada del proyecto | — (no existe; `bajo_logro_educativo_jefe` de 3_preprocesamiento es otro concepto) |
| Código Sisbén de referencia | `I1` (preguntas de la ficha: `PER017`, `PER002`) |
| Regla oficial (DANE) | Años de escolaridad aprobados desde 1º de primaria; promedio de las personas mayores de 15 años del hogar < 9 años -> privado. Hogares sin personas mayores de 15 años -> privados (met-IPM p. 17). |
| Regla reproducible con GEIH | Años aprobados = 0 si P3042 ∈ {1 Ninguno, 2 Preescolar}; P3042S1 si 3 Primaria; 5 + P3042S1 si 4 Secundaria; 9 + P3042S1 si 5-6 Media; >= 11 si 7-13 (normalista y superior). Promedio sobre personas con P6040 >= 15; privado si < 9. |
| Diferencias de definición | GEIH pregunta el último grado *o semestre* aprobado: para educación superior P3042S1 viene en semestres, no en años. No cambia quién supera 9 años individualmente, pero sí el promedio del hogar. |
| Población de referencia | Personas de 15 años y más; agregación: promedio del hogar. |
| Disponibilidad y calidad | `P3042` (15+): n = 657,803, vacío 0.00 %, no sabe 0.00 %; `P3042S1` (15+): n = 657,803, vacío 0.00 %, no sabe 0.00 % — 12 meses de GEIH 2024 apilados. |
| En `IPM_GEIH_BASE` (actual) | `bajo_logro_educativo_jefe`: solo el jefe, nivel < secundaria (P3042 < 4). No es la regla oficial. |
| Supuestos | Conversión de educación superior a años (11 + semestres/2) y '15 años y más' inclusive (el texto dice 'mayores de 15', el glosario de analfabetismo dice '15 años y más'). |
| Decisiones pendientes | Confirmar la conversión de P3042S1 en educación superior. P3042 = 99 (no sabe) -> faltante. |

### I2. Analfabetismo — *homologable*

| Campo | Contenido |
|---|---|
| Dimensión (peso oficial) | Condiciones educativas (0.10) |
| Variable GEIH original | `P6160`, `P6040` |
| Variable armonizada del proyecto | — (`analfabetismo` de 3_preprocesamiento usa solo al jefe) |
| Código Sisbén de referencia | `I2` (preguntas de la ficha: `PER015`, `PER002`) |
| Regla oficial (DANE) | Al menos una persona de 15 años y más que no sabe leer y escribir -> privado. Hogares sin personas mayores de 15 años -> privados (met-IPM p. 18). |
| Regla reproducible con GEIH | Privado si alguna persona con P6040 >= 15 tiene P6160 = 2. |
| Diferencias de definición | Ninguna de fondo: la pregunta es la misma (P6160 también aparece en el diccionario del IPM). |
| Población de referencia | Personas de 15 años y más; agregación: al menos una. |
| Disponibilidad y calidad | `P6160` (15+): n = 657,803, vacío 0.00 %, no sabe 0.00 % — 12 meses de GEIH 2024 apilados. |
| En `IPM_GEIH_BASE` (actual) | `analfabetismo`: solo el jefe de hogar. |
| Supuestos | — |
| Decisiones pendientes | — |

### I3. Inasistencia escolar — *homologable*

| Campo | Contenido |
|---|---|
| Dimensión (peso oficial) | Niñez y juventud (0.05) |
| Variable GEIH original | `P6170`, `P6040` |
| Variable armonizada del proyecto | `inasistencia_escolar_menores` (3_preprocesamiento) |
| Código Sisbén de referencia | `I3` (preguntas de la ficha: `PER016`, `PER002`) |
| Regla oficial (DANE) | Al menos un niño de 6 a 16 años que no asiste a una institución educativa -> privado. Hogares sin niños de 6-16 no están privados (met-IPM pp. 19-20). |
| Regla reproducible con GEIH | Privado si alguna persona con 6 <= P6040 <= 16 tiene P6170 = 2. |
| Diferencias de definición | Ninguna de fondo. |
| Población de referencia | Personas de 6 a 16 años; agregación: al menos una. |
| Disponibilidad y calidad | `P6170` (6-16): n = 141,391, vacío 0.00 %, no sabe 0.00 % — 12 meses de GEIH 2024 apilados. |
| En `IPM_GEIH_BASE` (actual) | `inasistencia_escolar_menores`: misma regla oficial. |
| Supuestos | — |
| Decisiones pendientes | — |

### I4. Rezago escolar — *homologable*

| Campo | Contenido |
|---|---|
| Dimensión (peso oficial) | Niñez y juventud (0.05) |
| Variable GEIH original | `P3042`, `P3042S1`, `P6040` |
| Variable armonizada del proyecto | — (no existe) |
| Código Sisbén de referencia | `I4` (preguntas de la ficha: `PER017`, `PER016`, `PER002`) |
| Regla oficial (DANE) | Al menos una persona de 7 a 17 años con años aprobados inferiores a la norma por edad (7 años y < 1, 8 y < 2, 9 y < 3 ... 17 y < 11) -> privado. Hogares sin personas de 7-17 no están privados (met-IPM p. 19). |
| Regla reproducible con GEIH | Años aprobados como en I1; privado si alguna persona con 7 <= P6040 <= 17 tiene años < P6040 - 6. |
| Diferencias de definición | Ninguna de fondo; usa la misma conversión de años que I1. |
| Población de referencia | Personas de 7 a 17 años; agregación: al menos una. |
| Disponibilidad y calidad | `P3042` (7-17): n = 143,187, vacío 0.00 %, no sabe 0.00 %; `P3042S1` (7-17): n = 143,187, vacío 0.00 %, no sabe 0.00 % — 12 meses de GEIH 2024 apilados. |
| En `IPM_GEIH_BASE` (actual) | No incluida. |
| Supuestos | La norma 'edad - 6' se generaliza de los casos que lista el documento (7->1, 8->2, 9->3, 17->11); los casos intermedios aparecen como '...' en el PDF. |
| Decisiones pendientes | — |

### I5. Barreras a servicios de cuidado de la primera infancia — *no disponible*

| Campo | Contenido |
|---|---|
| Dimensión (peso oficial) | Niñez y juventud (0.05) |
| Variable GEIH original | `P6090`, `P6170`, `P6040` |
| Variable armonizada del proyecto | — (no existe) |
| Código Sisbén de referencia | `I5` (preguntas de la ficha: `PER013`, `PER014`, `PER007`, `PER016`, `PER002`) |
| Regla oficial (DANE) | Niño de 0-4 privado si no está asegurado en salud, o pasa la mayor parte del tiempo con el padre/madre en el trabajo, solo o al cuidado de un menor de 18, o asiste a jardín sin desayuno/almuerzo gratuito o simbólico. Niño de 5 privado si no está asegurado, no asiste a institución educativa o asiste sin alimentación gratuita o simbólica. Hogar privado si al menos un niño de 0-5 lo está; sin niños de 0-5 no privado (met-IPM p. 20). |
| Regla reproducible con GEIH | No reproducible: GEIH no pregunta dónde o con quién permanece el niño ni si recibe alimentación en el plantel (P51/P55/P6180 del IPM no existen en GEIH 2024). Solo hay aseguramiento (P6090) y asistencia (P6170, desde los 3 años). |
| Diferencias de definición | Faltan los componentes de cuidado y nutrición; solo el de salud es observable. |
| Población de referencia | Niños de 0 a 5 años; agregación: al menos uno. |
| Disponibilidad y calidad | `P6090` (0-5): n = 57,774, vacío 0.00 %, no sabe 0.05 % — 12 meses de GEIH 2024 apilados. |
| En `IPM_GEIH_BASE` (actual) | No incluida. |
| Supuestos | — |
| Decisiones pendientes | ¿Incluir en IPM_GEIH_ALT una versión parcial (niño 0-5 sin aseguramiento, o de 5 años sin asistir)? Subestimaría la privación oficial por construcción. |

### I6. Trabajo infantil — *parcialmente homologable*

| Campo | Contenido |
|---|---|
| Dimensión (peso oficial) | Niñez y juventud (0.05) |
| Variable GEIH original | `OCI`, `P6040` |
| Variable armonizada del proyecto | — (no existe) |
| Código Sisbén de referencia | `I6` (preguntas de la ficha: `PER019`, `PER002`) |
| Regla oficial (DANE) | Al menos una persona de 12 a 17 años ocupada (trabajó, tuvo actividad paga, tenía trabajo o trabajó sin pago en negocio familiar la semana pasada) -> privado (met-IPM p. 21). |
| Regla reproducible con GEIH | Privado si alguna persona con 15 <= P6040 <= 17 aparece como ocupada (OCI = 1, módulo Ocupados). |
| Diferencias de definición | Los módulos de fuerza de trabajo de GEIH 2024 solo cubren personas de 15 años y más (verificado: edad mínima 15 en Fuerza de trabajo, Ocupados y No ocupados). Los niños de 12-14 no se pueden observar: la privación queda subestimada. |
| Población de referencia | Oficial 12-17 años; observable en GEIH solo 15-17. |
| Disponibilidad y calidad | `OCI` (12-17): n = 80,258, vacío 96.88 % (vacío = no ocupado, o de 12-14 años y por eso fuera de los módulos laborales), no sabe 0.00 % — 12 meses de GEIH 2024 apilados. |
| En `IPM_GEIH_BASE` (actual) | No incluida. |
| Supuestos | — |
| Decisiones pendientes | ¿Incluirla con la cobertura 15-17 en IPM_GEIH_15, o dejarla solo en IPM_GEIH_ALT? |

### I7. Desempleo de larga duración — *homologable*

| Campo | Contenido |
|---|---|
| Dimensión (peso oficial) | Trabajo (0.10) |
| Variable GEIH original | `FT`, `DSI`, `P7250`, `P6920`, `P7500S2` |
| Variable armonizada del proyecto | — (no existe) |
| Código Sisbén de referencia | `I7` (preguntas de la ficha: `PER019`) |
| Regla oficial (DANE) | PEA = mayores de 12 años ocupados o desocupados. Privado si alguna persona de la PEA lleva más de 12 meses buscando trabajo. Hogares sin PEA -> privados; hogares solo de pensionados -> privados (met-IPM pp. 23-24). |
| Regla reproducible con GEIH | PEA = FT = 1 (Fuerza de trabajo). Privado si alguna persona con DSI = 1 tiene P7250 > 52 semanas. Hogar sin ninguna persona con FT = 1 -> privado. Pensionado: P6920 = 3 (ocupados) o P7500S2 = 1 (otros ingresos). |
| Diferencias de definición | PEA desde 15 años (no 12). P7250 trae códigos 998/999 que el diccionario no documenta (60 casos en enero): se tratan como faltante. GEIH no tiene una pregunta directa de 'pensionado' para todas las personas: se identifica por las dos vías indicadas. |
| Población de referencia | PEA (15 años y más en GEIH); agregación: al menos una. |
| Disponibilidad y calidad | `FT` (15+): n = 657,803, vacío 39.03 % (vacío = inactivo, fuera de la fuerza de trabajo), no sabe 0.00 %; `P7250` (15+, DSI=1): n = 47,395, vacío 0.00 %, no sabe 1.45 % — 12 meses de GEIH 2024 apilados. |
| En `IPM_GEIH_BASE` (actual) | No incluida. |
| Supuestos | P7250 >= 998 = no sabe/no informa (código no documentado). 'Más de 12 meses' = más de 52 semanas. |
| Decisiones pendientes | Validar la identificación de pensionados (P6920 = 3, P7500S2 = 1). |

### I8. Trabajo informal — *homologable*

| Campo | Contenido |
|---|---|
| Dimensión (peso oficial) | Trabajo (0.10) |
| Variable GEIH original | `FT`, `OCI`, `DSI`, `P6920`, `P7500S2`, `P6040` |
| Variable armonizada del proyecto | — (`sin_cotizacion_pension_jefe` de 3_preprocesamiento es otro concepto) |
| Código Sisbén de referencia | `I8` (preguntas de la ficha: `PER018`, `PER020`, `PER019`) |
| Regla oficial (DANE) | Nueva PEA = PEA sin ocupados menores de 18 ni desempleados de larga duración. Formal = ocupado de la nueva PEA afiliado a pensiones o pensionado. Privado si el número de formales es distinto del tamaño de la nueva PEA (algún informal o desocupado), o si no hay nueva PEA. Hogares solo de pensionados no están privados (met-IPM pp. 24-25). |
| Regla reproducible con GEIH | Nueva PEA = FT = 1, excluyendo ocupados con P6040 < 18 y a quienes cumplen I7. Formal = OCI = 1 y P6920 ∈ {1 Sí cotiza, 3 Ya es pensionado}. Privado si #formales < #nueva PEA o si la nueva PEA está vacía. |
| Diferencias de definición | GEIH pregunta si 'está cotizando actualmente' (no 'afiliado'); el diccionario del IPM usa la misma pregunta P6920. La regla de 'solo pensionados' contradice la de I7 en el documento oficial (privados en I7, no privados en I8): se reproducen tal cual. |
| Población de referencia | Nueva PEA (18 años y más ocupados, más desocupados); agregación: todos formales. |
| Disponibilidad y calidad | `P6920` (18+, OCI=1): n = 351,164, vacío 0.00 %, no sabe 0.00 % — 12 meses de GEIH 2024 apilados. |
| En `IPM_GEIH_BASE` (actual) | `sin_cotizacion_pension_jefe`: solo el jefe, y lo marca privado si no es ocupado (mezcla informalidad con desempleo e inactividad). |
| Supuestos | — |
| Decisiones pendientes | — |

### I9. Sin aseguramiento en salud — *homologable*

| Campo | Contenido |
|---|---|
| Dimensión (peso oficial) | Salud (0.10) |
| Variable GEIH original | `P6090`, `P6040` |
| Variable armonizada del proyecto | — (`sin_aseguramiento_salud` de 3_preprocesamiento usa solo al jefe) |
| Código Sisbén de referencia | `I9` (preguntas de la ficha: `PER007`, `PER002`) |
| Regla oficial (DANE) | Al menos una persona mayor de 5 años no asegurada en salud -> privado; 'no sabe/no informa' cuenta como no asegurada (met-IPM p. 22 y nota 6). |
| Regla reproducible con GEIH | Privado si alguna persona con P6040 >= 6 tiene P6090 ∈ {2 No, 9 No sabe}. |
| Diferencias de definición | Ninguna de fondo: la pregunta es la misma (P6090 también aparece en el diccionario del IPM). |
| Población de referencia | Personas de 6 años y más; agregación: al menos una. |
| Disponibilidad y calidad | `P6090` (6+): n = 771,909, vacío 0.00 %, no sabe 0.08 % — 12 meses de GEIH 2024 apilados. |
| En `IPM_GEIH_BASE` (actual) | `sin_aseguramiento_salud`: solo el jefe, y P6090 = 9 cuenta como asegurado. |
| Supuestos | — |
| Decisiones pendientes | — |

### I10. Barreras de acceso a servicios de salud — *no disponible*

| Campo | Contenido |
|---|---|
| Dimensión (peso oficial) | Salud (0.10) |
| Variable GEIH original | — |
| Variable armonizada del proyecto | — (no existe) |
| Código Sisbén de referencia | `I10` (preguntas de la ficha: `PER008`, `PER009`, `PER010`) |
| Regla oficial (DANE) | Al menos una persona que en los últimos 30 días tuvo un problema de salud sin hospitalización y no acudió a médico, odontólogo, terapista o institución de salud -> privado. Sin problemas de salud en el hogar -> no privado (met-IPM pp. 22-23). |
| Regla reproducible con GEIH | No reproducible: GEIH 2024 no pregunta por problemas de salud recientes ni por la atención recibida (P5665/P8563 del IPM no existen en GEIH). |
| Diferencias de definición | Sin insumos. |
| Población de referencia | Personas con un problema de salud en los últimos 30 días. |
| Disponibilidad y calidad | Sin insumos en GEIH 2024. |
| En `IPM_GEIH_BASE` (actual) | No incluida. |
| Supuestos | — |
| Decisiones pendientes | — |

### I11. Sin acceso a fuente de agua mejorada — *homologable*

| Campo | Contenido |
|---|---|
| Dimensión (peso oficial) | Vivienda y servicios públicos (0.04) |
| Variable GEIH original | `P4030S5`, `P5050`, `CLASE` |
| Variable armonizada del proyecto | `viv_acueducto` (armonizar_geih_hogar_2024) |
| Código Sisbén de referencia | `I11` (preguntas de la ficha: `viv008`, `hog007`) |
| Regla oficial (DANE) | Urbano: sin servicio público de acueducto. Rural: obtiene el agua para preparar alimentos de pozo sin bomba, agua lluvia, río, manantial, carrotanque, aguatero o agua embotellada o en bolsa (met-IPM p. 25; el glosario agrega 'u otra fuente'). |
| Regla reproducible con GEIH | Urbano (CLASE = 1): P4030S5 = 2. Rural (CLASE = 2): P5050 ∈ {4 pozo sin bomba, 5 aguas lluvias, 6 río/manantial, 8 carrotanque, 9 aguatero, 10 embotellada o en bolsa}. |
| Diferencias de definición | GEIH pregunta por el agua 'para consumo humano', no 'para preparar los alimentos'. Las categorías 2 (otra fuente por tubería) y 7 (pila pública) no están en la lista oficial: no privan, salvo que se lea 'u otra fuente' del glosario. |
| Población de referencia | Hogares; regla distinta por zona. |
| Disponibilidad y calidad | `P4030S5` (hogares, CLASE=1): n = 253,377, vacío 0.00 %, no sabe 0.00 %; `P5050` (hogares, CLASE=2): n = 37,591, vacío 0.00 %, no sabe 0.00 % — 12 meses de GEIH 2024 apilados. |
| En `IPM_GEIH_BASE` (actual) | `sin_acueducto`: aplica la regla urbana (P4030S5 = 2) también a los hogares rurales. |
| Supuestos | — |
| Decisiones pendientes | ¿'u otra fuente' (glosario) incluye otra fuente por tubería y pila pública? |

### I12. Inadecuada eliminación de excretas — *homologable*

| Campo | Contenido |
|---|---|
| Dimensión (peso oficial) | Vivienda y servicios públicos (0.04) |
| Variable GEIH original | `P4030S3`, `P5020`, `CLASE` |
| Variable armonizada del proyecto | `viv_alcantarillado` (armonizar_geih_hogar_2024) |
| Código Sisbén de referencia | `I12` (preguntas de la ficha: `viv005`, `hog004`) |
| Regla oficial (DANE) | Urbano: sin servicio público de alcantarillado. Rural: inodoro sin conexión, bajamar o sin servicio sanitario (met-IPM p. 25). |
| Regla reproducible con GEIH | Urbano (CLASE = 1): P4030S3 = 2. Rural (CLASE = 2): P5020 ∈ {3 inodoro sin conexión, 5 bajamar, 6 no tiene}. |
| Diferencias de definición | Ninguna de fondo. La letrina (P5020 = 4) no priva en zona rural según el texto oficial. |
| Población de referencia | Hogares; regla distinta por zona. |
| Disponibilidad y calidad | `P4030S3` (hogares, CLASE=1): n = 253,377, vacío 0.00 %, no sabe 0.00 %; `P5020` (hogares, CLASE=2): n = 37,591, vacío 0.00 %, no sabe 0.00 % — 12 meses de GEIH 2024 apilados. |
| En `IPM_GEIH_BASE` (actual) | `sin_alcantarillado`: aplica la regla urbana (P4030S3 = 2) también a los hogares rurales. |
| Supuestos | — |
| Decisiones pendientes | — |

### I13. Material inadecuado de pisos — *homologable*

| Campo | Contenido |
|---|---|
| Dimensión (peso oficial) | Vivienda y servicios públicos (0.04) |
| Variable GEIH original | `P4020` |
| Variable armonizada del proyecto | `viv_pisos` (armonizar_geih_hogar_2024) |
| Código Sisbén de referencia | `I13` (preguntas de la ficha: `viv003`) |
| Regla oficial (DANE) | Pisos en tierra -> privado (met-IPM p. 26). |
| Regla reproducible con GEIH | P4020 = 1 (tierra, arena). |
| Diferencias de definición | Ninguna de fondo. |
| Población de referencia | Hogares. |
| Disponibilidad y calidad | `P4020` (hogares): n = 290,968, vacío 0.00 %, no sabe 0.00 % — 12 meses de GEIH 2024 apilados. |
| En `IPM_GEIH_BASE` (actual) | No incluida. |
| Supuestos | — |
| Decisiones pendientes | `viv_pisos` (P4020) entra a la celda del Hot-Deck desde el 2026-11-02 (y a `W` en 5_estimacion.py): si entra al outcome, el outcome queda definido en parte por la celda que sortea el tratamiento, como la tautología que retiró esta privación el 2026-10-28. Decidir si se incluye en IPM_GEIH_15. |

### I14. Material inadecuado de paredes exteriores — *homologable*

| Campo | Contenido |
|---|---|
| Dimensión (peso oficial) | Vivienda y servicios públicos (0.04) |
| Variable GEIH original | `P4010`, `CLASE` |
| Variable armonizada del proyecto | `viv_paredes` (armonizar_geih_hogar_2024) |
| Código Sisbén de referencia | `I14` (preguntas de la ficha: `viv002`) |
| Regla oficial (DANE) | Urbano: madera burda, tabla, tablón, guadua, otro vegetal, zinc, tela, cartón, desechos o sin paredes. Rural: guadua, otro vegetal, zinc, tela, cartón, desechos o sin paredes (met-IPM p. 26). |
| Regla reproducible con GEIH | Urbano (CLASE = 1): P4010 ∈ {5 madera burda, 6 guadua, 7 caña/esterilla/vegetal, 8 zinc/tela/cartón/latas/desechos/plástico, 9 sin paredes}. Rural (CLASE = 2): P4010 ∈ {6, 7, 8, 9}. |
| Diferencias de definición | La categoría 8 de GEIH agrega 'latas' y 'plástico' a la lista oficial; se toman como equivalentes. |
| Población de referencia | Hogares; regla distinta por zona. |
| Disponibilidad y calidad | `P4010` (hogares): n = 290,968, vacío 0.00 %, no sabe 0.00 % — 12 meses de GEIH 2024 apilados. |
| En `IPM_GEIH_BASE` (actual) | No incluida. |
| Supuestos | — |
| Decisiones pendientes | Misma tautología que I13 con `viv_paredes` (P4010) en X. |

### I15. Hacinamiento crítico — *homologable*

| Campo | Contenido |
|---|---|
| Dimensión (peso oficial) | Vivienda y servicios públicos (0.04) |
| Variable GEIH original | `P6008`, `P5010`, `CLASE` |
| Variable armonizada del proyecto | `hog_num_personas`, `viv_cuartos_dormir` (armonizar_geih_hogar_2024) |
| Código Sisbén de referencia | `I15` (preguntas de la ficha: `hog003`, `hog027`) |
| Regla oficial (DANE) | Urbano: 3 o más personas por cuarto. Rural: más de 3 personas por cuarto (met-IPM p. 26). |
| Regla reproducible con GEIH | Personas = P6008; cuartos = P5010 (para dormir). Urbano: P6008 / P5010 >= 3. Rural: > 3. |
| Diferencias de definición | El texto oficial dice 'por cuarto' sin precisar; se usan cuartos para dormir porque es la variable de cuartos que lista el diccionario del IPM (P5010). P5010 trae 98/99 (no sabe): faltante. |
| Población de referencia | Hogares; regla distinta por zona. |
| Disponibilidad y calidad | `P6008` (hogares): n = 290,968, vacío 0.00 %, no sabe 0.00 %; `P5010` (hogares): n = 290,968, vacío 0.00 %, no sabe 0.00 % — 12 meses de GEIH 2024 apilados. |
| En `IPM_GEIH_BASE` (actual) | `hacinamiento`: > 3 personas por cuarto para dormir en ambas zonas (sin la regla urbana >= 3). |
| Supuestos | 'Cuarto' = cuarto para dormir (P5010), por el diccionario del IPM. |
| Decisiones pendientes | — |

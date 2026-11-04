# Solicitud de información: puntaje continuo del Sisbén IV con fines de investigación

> **BORRADOR para revisión del equipo y del tutor (2026-11-04). No enviado.**
> Completar los campos entre corchetes, elegir el destinatario (Variante A,
> Secretaría Distrital de Planeación; Variante B, Departamento Nacional de
> Planeación) y revisar con el tutor antes de radicar. Al enviarla,
> registrar la fecha y el radicado en `docs/seguimiento/RESUMEN_AVANCES.md`
> (§6, Gestiones institucionales).

---

[Ciudad], [fecha]

Señores
**[Variante A: Secretaría Distrital de Planeación de Bogotá — Dirección de
Información, Cartografía y Estadística / Sisbén Bogotá]**
**[Variante B: Departamento Nacional de Planeación — Subdirección de
Desarrollo Social / Grupo Sisbén]**
[Dirección o canal de radicación]

**Asunto:** Solicitud de microdatos anonimizados del Sisbén IV con el
puntaje continuo, para una investigación académica de maestría.

Respetados señores:

Somos estudiantes de la Maestría en Ciencia de Datos de la Universidad
Santo Tomás y desarrollamos el trabajo de grado *«Focalización del Sisbén
IV y pobreza monetaria en hogares colombianos usando un enfoque de
inferencia causal»*, bajo la dirección de [nombre del tutor]. [Variante A:
Agradecemos la entrega del registro del Sisbén IV de Bogotá recibida el 3
de agosto de 2026, que ya forma parte del análisis.] [Variante B:
Trabajamos con el extracto anonimizado del Sisbén IV publicado en ANDA,
corte mayo de 2024.]

### Por qué solicitamos el puntaje continuo

El objetivo es estimar si la clasificación en los grupos A y B mejora el
bienestar de los hogares. Con la información disponible hoy (grupo y
subgrupo, sin puntaje) ese efecto no se puede identificar: lo demostramos
con una simulación sobre 290.968 hogares reales de la Gran Encuesta
Integrada de Hogares, en la que ningún método estadístico recupera un
efecto conocido a partir de los grupos.

El único diseño que sí lo recupera, incluso cuando la clasificación
depende de características que no se observan, es una **discontinuidad
de regresión** en el punto de corte entre grupos: comparar hogares con
puntajes casi iguales, a uno y otro lado del corte. Ese diseño requiere el
**puntaje continuo** y, para el mismo hogar, alguna medida de su situación
**posterior** a la clasificación.

### Información solicitada

Microdatos anonimizados, sin nombres, documentos de identidad,
direcciones ni ningún otro dato que permita identificar a las personas:

1. **Puntaje continuo** de cada hogar y el grupo y subgrupo resultantes.
2. **Fecha de la encuesta** a la que corresponde ese puntaje.
3. **Registros anteriores del mismo hogar** cuando haya sido encuestado
   más de una vez (por actualización o nueva solicitud), con su puntaje,
   su fecha y las variables de la ficha de cada visita, enlazados mediante
   un identificador **anónimo** del hogar generado por la entidad. Esto
   permite medir la situación del hogar después de su primera
   clasificación.
4. Las variables de la ficha ya incluidas en la entrega anterior
   [Variante A] / en el extracto de ANDA [Variante B].

Si entregar el puntaje exacto no fuera posible, cualquiera de estas
alternativas también permitiría el análisis:

- el puntaje solo para los hogares cercanos a los puntos de corte entre
  grupos, o centrado en el corte (distancia al corte, sin el valor
  absoluto);
- el puntaje redondeado o agrupado en intervalos pequeños;
- el procesamiento en las instalaciones de la entidad, o en una sala
  segura, sin que los microdatos salgan de ella, con entrega únicamente de
  resultados agregados.

### Uso y protección de la información

- Uso exclusivamente académico, para el trabajo de grado mencionado.
- Tratamiento conforme a la Ley 1581 de 2012 y a las condiciones que la
  entidad establezca; aceptamos firmar el acuerdo de confidencialidad o de
  uso que se requiera.
- Ningún resultado publicado permitirá identificar hogares ni personas:
  solo se reportarán estimaciones agregadas.
- Los datos se almacenan en un repositorio con acceso restringido al
  equipo de investigación y no se comparten con terceros. Los eliminaremos
  al terminar la investigación o cuando la entidad lo indique.
- Compartiremos con la entidad los resultados y la metodología, que
  pueden ser útiles para la evaluación de la focalización.

Quedamos atentos a cualquier requisito adicional, formato de solicitud o
acuerdo que la entidad requiera.

Cordialmente,

[Firma]
**Juan Sebastián Fonseca Arévalo**
[Documento] · [correo institucional]

[Firma]
**José Mateo Roncancio Marín**
[Documento] · [correo institucional]

[Firma]
**[Nombre del tutor]**
Director del trabajo de grado · [cargo y correo]

Maestría en Ciencia de Datos, Universidad Santo Tomás

---

## Nota interna (no forma parte de la carta)

- **Qué alternativa sirve más.** Con la Variante A, los hogares de Bogotá
  encuestados más de una vez permiten una discontinuidad con datos de una
  sola fuente: puntaje de la primera clasificación y resultado en la
  visita posterior. Es la vía más corta, porque el SDP ya entregó el
  registro. El resultado posterior es una variable de la ficha del Sisbén
  (por ejemplo, el ingreso del hogar o las privaciones de la vivienda);
  no se puede usar `I1`-`I15` ni `H_5` como resultado (CLAUDE.md,
  circularidad), salvo como privaciones medidas en la visita posterior y
  documentando por qué no son circulares en ese diseño.
- **Qué no pedir.** Datos personales o un cruce con la GEIH: la GEIH es
  anónima y el DANE no la entrega con identificadores.
- **Respaldo técnico.** `docs/resultados/SIMULACION_SEMISINTETICA.md`
  (escenario «regla de corte»: la RD recupera +0,086 frente a +0,090 en el
  corte con el tratamiento vinculado; cualquier otro estimador da −1,7) y
  `src/validacion/sensibilidad_semisintetica.py` (RD difusa, cuando no
  todos los elegibles participan).

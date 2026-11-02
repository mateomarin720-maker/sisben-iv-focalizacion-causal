"""Matriz de homologación GEIH ↔ Sisbén IV para las 15 privaciones del IPM
(Fase 2 de la comparación de proxies, ver
`docs/metodologia/comparacion_proxies/01_matriz_homologacion.md`).

La matriz (`MATRIZ`) es la fuente única: el documento .md y el CSV se
generan desde aquí, y `tests/test_homologacion_ipm.py` verifica que cada
código GEIH y Sisbén citado exista en su diccionario oficial — para no
inventar variables ni equivalencias.

Fuentes de cada columna de la matriz:
  - Regla oficial: DANE, "Metodología Índice de Pobreza Multidimensional
    (IPM)", `https://www.dane.gov.co/files/operaciones/PM/met-IPM.pdf`,
    §3.2.1 "Diseño de indicadores", pp. 15-26, y glosario pp. 29-31.
    Ponderación: cada dimensión pesa 1/5 y, dentro de ella, las variables
    pesan lo mismo; pobre si el índice ponderado es >= 5/15 (p. 15 y 26).
  - Códigos GEIH: `docs/insumos/DICCIONARIO_GEIH_2024.xlsx`.
  - Códigos Sisbén: `docs/insumos/DICCIONARIO_SISBEN_2024.xlsx`. El
    diccionario trae solo Nombre/Etiqueta: la columna `preguntas_sisben`
    lista las preguntas de la ficha cuya etiqueta corresponde a cada
    privación, NO la regla con que el DNP calcula `I1`-`I15`. Esa regla no
    está documentada en el repositorio (pendiente conseguir el documento
    metodológico del DNP).

Las `I1`-`I15` y `H_5` del Sisbén son solo REFERENCIA conceptual aquí —
nunca se usan como outcome (circularidad, ver `CLAUDE.md`).

El diagnóstico de insumos (`diagnosticar_insumos`) mide, sobre los 12
meses de GEIH 2024, cuántas personas u hogares caen en la población de
referencia de cada privación y qué % de sus insumos viene vacío o con
código de "no sabe". No construye privaciones (eso es la Fase 3, pendiente
de revisión de esta matriz).

Uso:
    poetry run python -m src.indicadores.homologacion_ipm
Salidas:
    docs/metodologia/comparacion_proxies/01_matriz_homologacion.md
    docs/metodologia/comparacion_proxies/01_matriz_homologacion.csv
    docs/reports/diagnostico_insumos_homologacion.csv
"""
from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

GEIH_DIR = Path("data/1_processed/geih/2024")
OUT_MATRIZ = Path("docs/metodologia/comparacion_proxies/01_matriz_homologacion.csv")
OUT_DIAGNOSTICO = Path("docs/reports/diagnostico_insumos_homologacion.csv")
MESES = [f"{m:02d}" for m in range(1, 13)]
K3 = ["DIRECTORIO", "SECUENCIA_P", "HOGAR"]
K4 = [*K3, "ORDEN"]

HOMOLOGABLE = "homologable"
PARCIAL = "parcialmente homologable"
NO_DISPONIBLE = "no disponible"
ESTADOS = (HOMOLOGABLE, PARCIAL, NO_DISPONIBLE)

# Peso oficial = (1/5 por dimensión) / (número de variables de la dimensión).
DIMENSIONES = {
    "Condiciones educativas": 2,
    "Niñez y juventud": 4,
    "Trabajo": 2,
    "Salud": 2,
    "Vivienda y servicios públicos": 5,
}
UMBRAL_POBRE_OFICIAL = 5 / 15


@dataclass(frozen=True)
class Privacion:
    id: str
    nombre: str
    dimension: str
    geih_original: tuple[str, ...]
    variable_armonizada: str
    codigo_sisben: str
    preguntas_sisben: tuple[str, ...]
    regla_oficial: str
    regla_geih: str
    diferencias: str
    poblacion_referencia: str
    estado: str
    supuestos: str = ""
    decisiones_pendientes: str = ""
    en_ipm_geih_base: str = ""
    peso_oficial: float = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "peso_oficial", round(0.2 / DIMENSIONES[self.dimension], 4))


MATRIZ: list[Privacion] = [
    Privacion(
        id="I1", nombre="Bajo logro educativo", dimension="Condiciones educativas",
        geih_original=("P3042", "P3042S1", "P6040"),
        variable_armonizada="— (no existe; `bajo_logro_educativo_jefe` de 3_preprocesamiento es otro concepto)",
        codigo_sisben="I1", preguntas_sisben=("PER017", "PER002"),
        regla_oficial=("Años de escolaridad aprobados desde 1º de primaria; promedio de las personas mayores "
                       "de 15 años del hogar < 9 años -> privado. Hogares sin personas mayores de 15 años -> "
                       "privados (met-IPM p. 17)."),
        regla_geih=("Años aprobados = 0 si P3042 ∈ {1 Ninguno, 2 Preescolar}; P3042S1 si 3 Primaria; 5 + P3042S1 "
                    "si 4 Secundaria; 9 + P3042S1 si 5-6 Media; >= 11 si 7-13 (normalista y superior). "
                    "Promedio sobre personas con P6040 >= 15; privado si < 9."),
        diferencias=("GEIH pregunta el último grado *o semestre* aprobado: para educación superior P3042S1 viene en "
                     "semestres, no en años. No cambia quién supera 9 años individualmente, pero sí el promedio del "
                     "hogar."),
        poblacion_referencia="Personas de 15 años y más; agregación: promedio del hogar.",
        estado=HOMOLOGABLE,
        supuestos=("Conversión de educación superior a años (11 + semestres/2) y '15 años y más' inclusive "
                   "(el texto dice 'mayores de 15', el glosario de analfabetismo dice '15 años y más')."),
        decisiones_pendientes="Confirmar la conversión de P3042S1 en educación superior. P3042 = 99 (no sabe) -> faltante.",
        en_ipm_geih_base="`bajo_logro_educativo_jefe`: solo el jefe, nivel < secundaria (P3042 < 4). No es la regla oficial.",
    ),
    Privacion(
        id="I2", nombre="Analfabetismo", dimension="Condiciones educativas",
        geih_original=("P6160", "P6040"),
        variable_armonizada="— (`analfabetismo` de 3_preprocesamiento usa solo al jefe)",
        codigo_sisben="I2", preguntas_sisben=("PER015", "PER002"),
        regla_oficial=("Al menos una persona de 15 años y más que no sabe leer y escribir -> privado. Hogares sin "
                       "personas mayores de 15 años -> privados (met-IPM p. 18)."),
        regla_geih="Privado si alguna persona con P6040 >= 15 tiene P6160 = 2.",
        diferencias="Ninguna de fondo: la pregunta es la misma (P6160 también aparece en el diccionario del IPM).",
        poblacion_referencia="Personas de 15 años y más; agregación: al menos una.",
        estado=HOMOLOGABLE,
        en_ipm_geih_base="`analfabetismo`: solo el jefe de hogar.",
    ),
    Privacion(
        id="I3", nombre="Inasistencia escolar", dimension="Niñez y juventud",
        geih_original=("P6170", "P6040"),
        variable_armonizada="`inasistencia_escolar_menores` (3_preprocesamiento)",
        codigo_sisben="I3", preguntas_sisben=("PER016", "PER002"),
        regla_oficial=("Al menos un niño de 6 a 16 años que no asiste a una institución educativa -> privado. "
                       "Hogares sin niños de 6-16 no están privados (met-IPM pp. 19-20)."),
        regla_geih="Privado si alguna persona con 6 <= P6040 <= 16 tiene P6170 = 2.",
        diferencias="Ninguna de fondo.",
        poblacion_referencia="Personas de 6 a 16 años; agregación: al menos una.",
        estado=HOMOLOGABLE,
        en_ipm_geih_base="`inasistencia_escolar_menores`: misma regla oficial.",
    ),
    Privacion(
        id="I4", nombre="Rezago escolar", dimension="Niñez y juventud",
        geih_original=("P3042", "P3042S1", "P6040"),
        variable_armonizada="— (no existe)",
        codigo_sisben="I4", preguntas_sisben=("PER017", "PER016", "PER002"),
        regla_oficial=("Al menos una persona de 7 a 17 años con años aprobados inferiores a la norma por edad "
                       "(7 años y < 1, 8 y < 2, 9 y < 3 ... 17 y < 11) -> privado. Hogares sin personas de "
                       "7-17 no están privados (met-IPM p. 19)."),
        regla_geih="Años aprobados como en I1; privado si alguna persona con 7 <= P6040 <= 17 tiene años < P6040 - 6.",
        diferencias="Ninguna de fondo; usa la misma conversión de años que I1.",
        poblacion_referencia="Personas de 7 a 17 años; agregación: al menos una.",
        estado=HOMOLOGABLE,
        supuestos=("La norma 'edad - 6' se generaliza de los casos que lista el documento (7->1, 8->2, 9->3, "
                   "17->11); los casos intermedios aparecen como '...' en el PDF."),
    ),
    Privacion(
        id="I5", nombre="Barreras a servicios de cuidado de la primera infancia", dimension="Niñez y juventud",
        geih_original=("P6090", "P6170", "P6040"),
        variable_armonizada="— (no existe)",
        codigo_sisben="I5", preguntas_sisben=("PER013", "PER014", "PER007", "PER016", "PER002"),
        regla_oficial=("Niño de 0-4 privado si no está asegurado en salud, o pasa la mayor parte del tiempo con el "
                       "padre/madre en el trabajo, solo o al cuidado de un menor de 18, o asiste a jardín sin "
                       "desayuno/almuerzo gratuito o simbólico. Niño de 5 privado si no está asegurado, no asiste a "
                       "institución educativa o asiste sin alimentación gratuita o simbólica. Hogar privado si al "
                       "menos un niño de 0-5 lo está; sin niños de 0-5 no privado (met-IPM p. 20)."),
        regla_geih=("No reproducible: GEIH no pregunta dónde o con quién permanece el niño ni si recibe alimentación "
                    "en el plantel (P51/P55/P6180 del IPM no existen en GEIH 2024). Solo hay aseguramiento (P6090) "
                    "y asistencia (P6170, desde los 3 años)."),
        diferencias="Faltan los componentes de cuidado y nutrición; solo el de salud es observable.",
        poblacion_referencia="Niños de 0 a 5 años; agregación: al menos uno.",
        estado=NO_DISPONIBLE,
        decisiones_pendientes=("¿Incluir en IPM_GEIH_ALT una versión parcial (niño 0-5 sin aseguramiento, o de 5 años "
                               "sin asistir)? Subestimaría la privación oficial por construcción."),
    ),
    Privacion(
        id="I6", nombre="Trabajo infantil", dimension="Niñez y juventud",
        geih_original=("OCI", "P6040"),
        variable_armonizada="— (no existe)",
        codigo_sisben="I6", preguntas_sisben=("PER019", "PER002"),
        regla_oficial=("Al menos una persona de 12 a 17 años ocupada (trabajó, tuvo actividad paga, tenía trabajo "
                       "o trabajó sin pago en negocio familiar la semana pasada) -> privado (met-IPM p. 21)."),
        regla_geih="Privado si alguna persona con 15 <= P6040 <= 17 aparece como ocupada (OCI = 1, módulo Ocupados).",
        diferencias=("Los módulos de fuerza de trabajo de GEIH 2024 solo cubren personas de 15 años y más "
                     "(verificado: edad mínima 15 en Fuerza de trabajo, Ocupados y No ocupados). Los niños de 12-14 "
                     "no se pueden observar: la privación queda subestimada."),
        poblacion_referencia="Oficial 12-17 años; observable en GEIH solo 15-17.",
        estado=PARCIAL,
        decisiones_pendientes="¿Incluirla con la cobertura 15-17 en IPM_GEIH_15, o dejarla solo en IPM_GEIH_ALT?",
    ),
    Privacion(
        id="I7", nombre="Desempleo de larga duración", dimension="Trabajo",
        geih_original=("FT", "DSI", "P7250", "P6920", "P7500S2"),
        variable_armonizada="— (no existe)",
        codigo_sisben="I7", preguntas_sisben=("PER019",),
        regla_oficial=("PEA = mayores de 12 años ocupados o desocupados. Privado si alguna persona de la PEA lleva "
                       "más de 12 meses buscando trabajo. Hogares sin PEA -> privados; hogares solo de pensionados "
                       "-> privados (met-IPM pp. 23-24)."),
        regla_geih=("PEA = FT = 1 (Fuerza de trabajo). Privado si alguna persona con DSI = 1 tiene P7250 > 52 semanas. "
                    "Hogar sin ninguna persona con FT = 1 -> privado. Pensionado: P6920 = 3 (ocupados) o "
                    "P7500S2 = 1 (otros ingresos)."),
        diferencias=("PEA desde 15 años (no 12). P7250 trae códigos 998/999 que el diccionario no documenta "
                     "(60 casos en enero): se tratan como faltante. GEIH no tiene una pregunta directa de "
                     "'pensionado' para todas las personas: se identifica por las dos vías indicadas."),
        poblacion_referencia="PEA (15 años y más en GEIH); agregación: al menos una.",
        estado=HOMOLOGABLE,
        supuestos="P7250 >= 998 = no sabe/no informa (código no documentado). 'Más de 12 meses' = más de 52 semanas.",
        decisiones_pendientes="Validar la identificación de pensionados (P6920 = 3, P7500S2 = 1).",
    ),
    Privacion(
        id="I8", nombre="Trabajo informal", dimension="Trabajo",
        geih_original=("FT", "OCI", "DSI", "P6920", "P7500S2", "P6040"),
        variable_armonizada="— (`sin_cotizacion_pension_jefe` de 3_preprocesamiento es otro concepto)",
        codigo_sisben="I8", preguntas_sisben=("PER018", "PER020", "PER019"),
        regla_oficial=("Nueva PEA = PEA sin ocupados menores de 18 ni desempleados de larga duración. Formal = "
                       "ocupado de la nueva PEA afiliado a pensiones o pensionado. Privado si el número de formales "
                       "es distinto del tamaño de la nueva PEA (algún informal o desocupado), o si no hay nueva PEA. "
                       "Hogares solo de pensionados no están privados (met-IPM pp. 24-25)."),
        regla_geih=("Nueva PEA = FT = 1, excluyendo ocupados con P6040 < 18 y a quienes cumplen I7. Formal = OCI = 1 "
                    "y P6920 ∈ {1 Sí cotiza, 3 Ya es pensionado}. Privado si #formales < #nueva PEA o si la nueva "
                    "PEA está vacía."),
        diferencias=("GEIH pregunta si 'está cotizando actualmente' (no 'afiliado'); el diccionario del IPM usa la "
                     "misma pregunta P6920. La regla de 'solo pensionados' contradice la de I7 en el documento "
                     "oficial (privados en I7, no privados en I8): se reproducen tal cual."),
        poblacion_referencia="Nueva PEA (18 años y más ocupados, más desocupados); agregación: todos formales.",
        estado=HOMOLOGABLE,
        en_ipm_geih_base=("`sin_cotizacion_pension_jefe`: solo el jefe, y lo marca privado si no es ocupado "
                          "(mezcla informalidad con desempleo e inactividad)."),
    ),
    Privacion(
        id="I9", nombre="Sin aseguramiento en salud", dimension="Salud",
        geih_original=("P6090", "P6040"),
        variable_armonizada="— (`sin_aseguramiento_salud` de 3_preprocesamiento usa solo al jefe)",
        codigo_sisben="I9", preguntas_sisben=("PER007", "PER002"),
        regla_oficial=("Al menos una persona mayor de 5 años no asegurada en salud -> privado; 'no sabe/no informa' "
                       "cuenta como no asegurada (met-IPM p. 22 y nota 6)."),
        regla_geih="Privado si alguna persona con P6040 >= 6 tiene P6090 ∈ {2 No, 9 No sabe}.",
        diferencias="Ninguna de fondo: la pregunta es la misma (P6090 también aparece en el diccionario del IPM).",
        poblacion_referencia="Personas de 6 años y más; agregación: al menos una.",
        estado=HOMOLOGABLE,
        en_ipm_geih_base="`sin_aseguramiento_salud`: solo el jefe, y P6090 = 9 cuenta como asegurado.",
    ),
    Privacion(
        id="I10", nombre="Barreras de acceso a servicios de salud", dimension="Salud",
        geih_original=(),
        variable_armonizada="— (no existe)",
        codigo_sisben="I10", preguntas_sisben=("PER008", "PER009", "PER010"),
        regla_oficial=("Al menos una persona que en los últimos 30 días tuvo un problema de salud sin "
                       "hospitalización y no acudió a médico, odontólogo, terapista o institución de salud -> "
                       "privado. Sin problemas de salud en el hogar -> no privado (met-IPM pp. 22-23)."),
        regla_geih=("No reproducible: GEIH 2024 no pregunta por problemas de salud recientes ni por la atención "
                    "recibida (P5665/P8563 del IPM no existen en GEIH)."),
        diferencias="Sin insumos.",
        poblacion_referencia="Personas con un problema de salud en los últimos 30 días.",
        estado=NO_DISPONIBLE,
    ),
    Privacion(
        id="I11", nombre="Sin acceso a fuente de agua mejorada", dimension="Vivienda y servicios públicos",
        geih_original=("P4030S5", "P5050", "CLASE"),
        variable_armonizada="`viv_acueducto` (armonizar_geih_hogar_2024)",
        codigo_sisben="I11", preguntas_sisben=("viv008", "hog007"),
        regla_oficial=("Urbano: sin servicio público de acueducto. Rural: obtiene el agua para preparar alimentos "
                       "de pozo sin bomba, agua lluvia, río, manantial, carrotanque, aguatero o agua embotellada o "
                       "en bolsa (met-IPM p. 25; el glosario agrega 'u otra fuente')."),
        regla_geih=("Urbano (CLASE = 1): P4030S5 = 2. Rural (CLASE = 2): P5050 ∈ {4 pozo sin bomba, 5 aguas lluvias, "
                    "6 río/manantial, 8 carrotanque, 9 aguatero, 10 embotellada o en bolsa}."),
        diferencias=("GEIH pregunta por el agua 'para consumo humano', no 'para preparar los alimentos'. Las "
                     "categorías 2 (otra fuente por tubería) y 7 (pila pública) no están en la lista oficial: no "
                     "privan, salvo que se lea 'u otra fuente' del glosario."),
        poblacion_referencia="Hogares; regla distinta por zona.",
        estado=HOMOLOGABLE,
        decisiones_pendientes="¿'u otra fuente' (glosario) incluye otra fuente por tubería y pila pública?",
        en_ipm_geih_base="`sin_acueducto`: aplica la regla urbana (P4030S5 = 2) también a los hogares rurales.",
    ),
    Privacion(
        id="I12", nombre="Inadecuada eliminación de excretas", dimension="Vivienda y servicios públicos",
        geih_original=("P4030S3", "P5020", "CLASE"),
        variable_armonizada="`viv_alcantarillado` (armonizar_geih_hogar_2024)",
        codigo_sisben="I12", preguntas_sisben=("viv005", "hog004"),
        regla_oficial=("Urbano: sin servicio público de alcantarillado. Rural: inodoro sin conexión, bajamar o sin "
                       "servicio sanitario (met-IPM p. 25)."),
        regla_geih="Urbano (CLASE = 1): P4030S3 = 2. Rural (CLASE = 2): P5020 ∈ {3 inodoro sin conexión, 5 bajamar, 6 no tiene}.",
        diferencias="Ninguna de fondo. La letrina (P5020 = 4) no priva en zona rural según el texto oficial.",
        poblacion_referencia="Hogares; regla distinta por zona.",
        estado=HOMOLOGABLE,
        en_ipm_geih_base="`sin_alcantarillado`: aplica la regla urbana (P4030S3 = 2) también a los hogares rurales.",
    ),
    Privacion(
        id="I13", nombre="Material inadecuado de pisos", dimension="Vivienda y servicios públicos",
        geih_original=("P4020",),
        variable_armonizada="`viv_pisos` (armonizar_geih_hogar_2024)",
        codigo_sisben="I13", preguntas_sisben=("viv003",),
        regla_oficial="Pisos en tierra -> privado (met-IPM p. 26).",
        regla_geih="P4020 = 1 (tierra, arena).",
        diferencias="Ninguna de fondo.",
        poblacion_referencia="Hogares.",
        estado=HOMOLOGABLE,
        decisiones_pendientes=("`viv_pisos` (P4020) es covariable X en 5_estimacion.py: si entra al outcome se repite "
                               "la tautología que retiró esta privación el 2026-10-28. Decidir si se incluye en "
                               "IPM_GEIH_15 o si se saca de X en los modelos que usen este outcome."),
    ),
    Privacion(
        id="I14", nombre="Material inadecuado de paredes exteriores", dimension="Vivienda y servicios públicos",
        geih_original=("P4010", "CLASE"),
        variable_armonizada="`viv_paredes` (armonizar_geih_hogar_2024)",
        codigo_sisben="I14", preguntas_sisben=("viv002",),
        regla_oficial=("Urbano: madera burda, tabla, tablón, guadua, otro vegetal, zinc, tela, cartón, desechos o "
                       "sin paredes. Rural: guadua, otro vegetal, zinc, tela, cartón, desechos o sin paredes "
                       "(met-IPM p. 26)."),
        regla_geih=("Urbano (CLASE = 1): P4010 ∈ {5 madera burda, 6 guadua, 7 caña/esterilla/vegetal, 8 zinc/tela/"
                    "cartón/latas/desechos/plástico, 9 sin paredes}. Rural (CLASE = 2): P4010 ∈ {6, 7, 8, 9}."),
        diferencias="La categoría 8 de GEIH agrega 'latas' y 'plástico' a la lista oficial; se toman como equivalentes.",
        poblacion_referencia="Hogares; regla distinta por zona.",
        estado=HOMOLOGABLE,
        decisiones_pendientes="Misma tautología que I13 con `viv_paredes` (P4010) en X.",
    ),
    Privacion(
        id="I15", nombre="Hacinamiento crítico", dimension="Vivienda y servicios públicos",
        geih_original=("P6008", "P5010", "CLASE"),
        variable_armonizada="`hog_num_personas`, `viv_cuartos_dormir` (armonizar_geih_hogar_2024)",
        codigo_sisben="I15", preguntas_sisben=("hog003", "hog027"),
        regla_oficial="Urbano: 3 o más personas por cuarto. Rural: más de 3 personas por cuarto (met-IPM p. 26).",
        regla_geih="Personas = P6008; cuartos = P5010 (para dormir). Urbano: P6008 / P5010 >= 3. Rural: > 3.",
        diferencias=("El texto oficial dice 'por cuarto' sin precisar; se usan cuartos para dormir porque es la "
                     "variable de cuartos que lista el diccionario del IPM (P5010). P5010 trae 98/99 (no sabe): "
                     "faltante."),
        poblacion_referencia="Hogares; regla distinta por zona.",
        estado=HOMOLOGABLE,
        supuestos="'Cuarto' = cuarto para dormir (P5010), por el diccionario del IPM.",
        en_ipm_geih_base="`hacinamiento`: > 3 personas por cuarto para dormir en ambas zonas (sin la regla urbana >= 3).",
    ),
]


# Insumos a diagnosticar: (privación, módulo, variable, edad mínima, edad máxima,
# filtro adicional como (columna, valor) o None, códigos de "no sabe").
INSUMOS = [
    ("I1", "personas", "P3042", 15, None, None, ("99",)),
    ("I1", "personas", "P3042S1", 15, None, None, ()),
    ("I2", "personas", "P6160", 15, None, None, ()),
    ("I3", "personas", "P6170", 6, 16, None, ()),
    ("I4", "personas", "P3042", 7, 17, None, ("99",)),
    ("I4", "personas", "P3042S1", 7, 17, None, ()),
    ("I5", "personas", "P6090", 0, 5, None, ("9",)),
    ("I6", "personas", "OCI", 12, 17, None, ()),
    ("I7", "personas", "FT", 15, None, None, ()),
    ("I7", "personas", "P7250", 15, None, ("DSI", "1"), ("998", "999")),
    ("I8", "personas", "P6920", 18, None, ("OCI", "1"), ()),
    ("I9", "personas", "P6090", 6, None, None, ("9",)),
    ("I11", "hogares", "P4030S5", None, None, ("CLASE", "1"), ()),
    ("I11", "hogares", "P5050", None, None, ("CLASE", "2"), ()),
    ("I12", "hogares", "P4030S3", None, None, ("CLASE", "1"), ()),
    ("I12", "hogares", "P5020", None, None, ("CLASE", "2"), ()),
    ("I13", "hogares", "P4020", None, None, None, ()),
    ("I14", "hogares", "P4010", None, None, None, ()),
    ("I15", "hogares", "P6008", None, None, None, ()),
    ("I15", "hogares", "P5010", None, None, None, ("98", "99")),
]

# Variables cuyo "vacío" es el flujo del cuestionario, no un faltante.
VACIO_ESTRUCTURAL = {
    "FT": "vacío = inactivo, fuera de la fuerza de trabajo",
    "OCI": "vacío = no ocupado, o de 12-14 años y por eso fuera de los módulos laborales",
}


def _leer(mes: str, modulo: str, columnas: list[str]) -> pd.DataFrame:
    df = pd.read_parquet(GEIH_DIR / mes / f"{modulo}.parquet", columns=columnas).replace("", pd.NA)
    for c in K4:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
    for c in df.columns.difference(K4):
        df[c] = df[c].astype("string").str.strip()
    return df


def _tablas_mes(mes: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Una tabla de personas (con edad y zona) y una de hogares, para un mes."""
    hog = _leer(mes, "hogar_vivienda", [*K3, "CLASE", "P4010", "P4020", "P4030S3", "P4030S5",
                                         "P5010", "P5020", "P5050", "P6008"])
    per = _leer(mes, "caracteristicas_generales", [*K4, "P6040", "P6050", "P3042", "P3042S1",
                                                    "P6160", "P6170", "P6090"])
    per = per.merge(_leer(mes, "fuerza_trabajo", [*K4, "FT"]), on=K4, how="left")
    per = per.merge(_leer(mes, "ocupados", [*K4, "OCI", "P6920"]), on=K4, how="left")
    per = per.merge(_leer(mes, "no_ocupados", [*K4, "DSI", "P7250"]), on=K4, how="left")
    per = per.merge(hog[[*K3, "CLASE"]], on=K3, how="left")
    per["edad"] = pd.to_numeric(per["P6040"], errors="coerce")
    return per, hog


def diagnosticar_insumos() -> pd.DataFrame:
    acum: dict[tuple, dict[str, int]] = {}
    for mes in MESES:
        if not (GEIH_DIR / mes / "hogar_vivienda.parquet").exists():
            logger.warning("GEIH %s: falta hogar_vivienda — se omite", mes)
            continue
        per, hog = _tablas_mes(mes)
        for priv, nivel, var, e_min, e_max, filtro, ns in INSUMOS:
            df = per if nivel == "personas" else hog
            m = pd.Series(True, index=df.index)
            if e_min is not None:
                m &= df["edad"] >= e_min
            if e_max is not None:
                m &= df["edad"] <= e_max
            if filtro is not None:
                m &= df[filtro[0]] == filtro[1]
            s = df.loc[m, var]
            etiqueta_filtro = f"{filtro[0]}={filtro[1]}" if filtro else ""
            a = acum.setdefault((priv, nivel, var, e_min, e_max, etiqueta_filtro), dict(n=0, na=0, ns=0, hog=0))
            a["n"] += len(s)
            a["na"] += int(s.isna().sum())
            a["ns"] += int(s.isin(ns).sum())
            a["hog"] += len(df.loc[m, K3].drop_duplicates()) if nivel == "personas" else len(s)
        logger.info("GEIH %s: diagnóstico de insumos listo", mes)

    filas = []
    for (priv, nivel, var, e_min, e_max, filtro), a in acum.items():
        rango = "" if e_min is None else (f"{e_min}+" if e_max is None else f"{e_min}-{e_max}")
        filas.append(dict(privacion=priv, nivel=nivel, variable=var, edades=rango, filtro=filtro,
                          n_universo=a["n"], hogares_con_universo=a["hog"],
                          pct_vacio=round(100 * a["na"] / a["n"], 2) if a["n"] else None,
                          pct_no_sabe=round(100 * a["ns"] / a["n"], 2) if a["n"] else None))
    return pd.DataFrame(filas)


def matriz_dataframe() -> pd.DataFrame:
    df = pd.DataFrame([asdict(p) for p in MATRIZ])
    for c in ("geih_original", "preguntas_sisben"):
        df[c] = df[c].map(", ".join)
    return df


def matriz_markdown(diag: pd.DataFrame) -> str:
    """Documento de la matriz, generado desde `MATRIZ` y el diagnóstico de insumos."""
    lineas = [
        "# Matriz de homologación GEIH ↔ Sisbén IV — 15 privaciones del IPM",
        "",
        "*Generado por `src/indicadores/homologacion_ipm.py` — no editar a mano; cambiar `MATRIZ` y volver a correr.*",
        "",
        "Regla oficial: DANE, *Metodología Índice de Pobreza Multidimensional (IPM)* "
        "([met-IPM.pdf](https://www.dane.gov.co/files/operaciones/PM/met-IPM.pdf)), §3.2.1, pp. 15-26. "
        "Códigos GEIH: `docs/insumos/DICCIONARIO_GEIH_2024.xlsx`. Códigos Sisbén: "
        "`docs/insumos/DICCIONARIO_SISBEN_2024.xlsx` (solo Nombre/Etiqueta: las preguntas Sisbén se asocian "
        "por etiqueta; la regla con que el DNP calcula `I1`-`I15` no está documentada en el repositorio).",
        "",
        "`I1`-`I15` y `H_5` del Sisbén son solo referencia conceptual: **nunca** se usan como outcome.",
        "",
        "Interpretación y decisiones pendientes: [`00_auditoria_variables.md`](00_auditoria_variables.md).",
        "",
        "## Resumen",
        "",
        "| Id | Privación | Dimensión | Peso oficial | Variables GEIH | Preguntas Sisbén | Estado |",
        "|---|---|---|---|---|---|---|",
    ]
    for p in MATRIZ:
        lineas.append(f"| {p.id} | {p.nombre} | {p.dimension} | {p.peso_oficial:.2f} | "
                      f"{', '.join(f'`{c}`' for c in p.geih_original) or '—'} | "
                      f"{', '.join(f'`{c}`' for c in p.preguntas_sisben)} | **{p.estado}** |")
    lineas += ["", "## Detalle por privación", ""]
    for p in MATRIZ:
        d = diag[diag["privacion"] == p.id]
        if d.empty:
            disponibilidad = "Sin insumos en GEIH 2024."
        else:
            disponibilidad = "; ".join(
                f"`{r.variable}` ({r.edades or 'hogares'}{', ' + r.filtro if r.filtro else ''}): "
                f"n = {r.n_universo:,}, vacío {r.pct_vacio:.2f} %"
                f"{' (' + VACIO_ESTRUCTURAL[r.variable] + ')' if r.variable in VACIO_ESTRUCTURAL else ''}"
                f", no sabe {r.pct_no_sabe:.2f} %"
                for r in d.itertuples()
            ) + " — 12 meses de GEIH 2024 apilados."
        lineas += [
            f"### {p.id}. {p.nombre} — *{p.estado}*",
            "",
            "| Campo | Contenido |",
            "|---|---|",
            f"| Dimensión (peso oficial) | {p.dimension} ({p.peso_oficial:.2f}) |",
            f"| Variable GEIH original | {', '.join(f'`{c}`' for c in p.geih_original) or '—'} |",
            f"| Variable armonizada del proyecto | {p.variable_armonizada} |",
            f"| Código Sisbén de referencia | `{p.codigo_sisben}` (preguntas de la ficha: "
            f"{', '.join(f'`{c}`' for c in p.preguntas_sisben)}) |",
            f"| Regla oficial (DANE) | {p.regla_oficial} |",
            f"| Regla reproducible con GEIH | {p.regla_geih} |",
            f"| Diferencias de definición | {p.diferencias} |",
            f"| Población de referencia | {p.poblacion_referencia} |",
            f"| Disponibilidad y calidad | {disponibilidad} |",
            f"| En `IPM_GEIH_BASE` (actual) | {p.en_ipm_geih_base or 'No incluida.'} |",
            f"| Supuestos | {p.supuestos or '—'} |",
            f"| Decisiones pendientes | {p.decisiones_pendientes or '—'} |",
            "",
        ]
    return "\n".join(lineas)


def main() -> None:
    matriz = matriz_dataframe()
    OUT_MATRIZ.parent.mkdir(parents=True, exist_ok=True)
    matriz.to_csv(OUT_MATRIZ, index=False, encoding="utf-8")

    diag = diagnosticar_insumos()
    OUT_DIAGNOSTICO.parent.mkdir(parents=True, exist_ok=True)
    diag.to_csv(OUT_DIAGNOSTICO, index=False, encoding="utf-8")
    OUT_MATRIZ.with_suffix(".md").write_text(matriz_markdown(diag), encoding="utf-8")

    print("\n=== Matriz de homologación GEIH ↔ Sisbén (15 privaciones) ===")
    print(matriz[["id", "nombre", "dimension", "peso_oficial", "estado"]].to_string(index=False))
    print("\nPor estado:", matriz["estado"].value_counts().to_dict())
    print("\n=== Diagnóstico de insumos (GEIH 2024, 12 meses) ===")
    print(diag.to_string(index=False))
    print(f"\nGuardado: {OUT_MATRIZ}")
    print(f"Guardado: {OUT_MATRIZ.with_suffix('.md')}")
    print(f"Guardado: {OUT_DIAGNOSTICO}")


if __name__ == "__main__":
    main()

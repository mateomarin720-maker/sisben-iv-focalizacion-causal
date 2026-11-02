# Pobreza monetaria: decisiones cerradas y diccionario del ingreso

Fase 2 de la metodología (`00_auditoria_y_metodologia.md`). Decisiones
cerradas el 2026-11-02 tras la revisión de D1-D7. Implementación:
`src/indicadores/pobreza_monetaria_geih.py`; resultados:
`docs/resultados/RESULTADOS_POBREZA_MONETARIA.md`.

## Decisiones D1-D7

| # | Decisión | Qué se hizo | Evidencia |
|---|---|---|---|
| D1 | Base oficial anonimizada | Descargada el 2026-11-02 (`data/0_raw/pobreza_monetaria/`). Trae las llaves de GEIH: la reconstrucción clasifica igual al 93,9 % de los hogares comunes. Cubre 24 departamentos y Bogotá (no los 9 nuevos) | `src/validacion/comparar_pobreza_monetaria_oficial.py` |
| D2 | Pensionista en `P6050` | Base: excluir solo el 10 (servicio doméstico y sus parientes). 11 y 12: sensibilidad | No mueve las tasas (33,2 % en los dos casos) |
| D3 | Ajuste por vivienda propia | Base: `P5130` (arriendo estimado) para `P5090` ∈ {1, 2, 4}: propietarios y usufructuarios. Sensibilidades sin ajuste y solo propietarios | La ficha del catálogo 874 dice "arriendo imputado para propietarios y usufructuarios" |
| D4 | Ganancia rural | Base: `P6750` del mes, como `INGLABO`. Sensibilidad con `P550` ÷ 12 | `INGLABO` = `P6750` en el 94,5 % de quienes declaran `P550` (enero) |
| D5 | Cesantías y accidentes | Base: excluidos. Sensibilidad: incluidos | No mueven las tasas |
| D6 | Comparación con el Sisbén | Por celda, no hogar por hogar | El grupo imputado no varía dentro de la celda |
| D7 | Líneas | Versión B: tres líneas de dominio. Versión A (por área y semestre) disponible en la base oficial (`lp`, `li`); con ella la reconstrucción baja de 33,2 % a 32,6 % | Boletín DANE 2024, tablas 1 y 4; base oficial |

Decisiones adicionales verificadas con los datos:
- **No respuesta laboral:** hot-deck dentro de GEIH para ocupados
  remunerados con `INGLABO` vacío o 0 ("falso cero"), igual que el DANE
  (la ficha 874 menciona hot-deck para faltantes, extremos y falsos
  ceros). Celdas: sexo × edad × educación × posición × rama (1 dígito) ×
  dominio, con respaldo a celdas más gruesas. 12.163 personas imputadas
  (3,5 % de los remunerados), todas con donante.
- **Trabajadores sin remuneración:** `P6430` ∈ {6, 8}. El 7 es jornalero:
  el 99 % declara `P6500`, con una mediana de $1.000.000 (enero). La
  auditoría lo tenía mal.
- **Especie de independientes** (`P3054S1`, `P3055S1`): se suma. `INGLABO`
  no la trae (igual a `P6750` en el 96 % de quienes la declaran).
- **Montos 98/99** ("recibió, no sabe cuánto"): no cuentan como monto
  (12.843 casos en el año). No se imputan.

## Diccionario del ingreso de la persona (mensual)

| Componente | Variables | Regla |
|---|---|---|
| Laboral principal | `INGLABO` | Hot-deck si falta en un remunerado; 0 si no es remunerado |
| Laboral no incluido | `P6510S1`, `P6545S1`, `P6580S1`, `P6585S1A1`-`S4A1` | Solo si `S2`/`A2` = 2 (no incluido en lo declarado) |
| Primas anuales | `P6630S1A1`-`S4A1` | ÷ 12, si `P6630Sk` = 1 |
| Especie de independientes | `P3054S1`, `P3055S1` | Si `P6430` ∈ {4, 5, 9} |
| Trabajo de no ocupados | `P7422S1` | Si `P7422` = 1 |
| Arriendos, pensiones, pensión alimenticia | `P7500S1A1`-`S3A1` | Si `P7500Sk` = 1 |
| Transferencias, ayudas (total), capital | `P7510S1A1`, `S2A1`, `S3A1`, `S5A1` | ÷ 12, si `P7510Sk` = 1. Ayudas solo el total (`S3`), el detalle está anidado |
| Excluidos | `P7510S7A1` (ocasionales); `P7510S6A1`, `P6630S6A1` (sensibilidad) | — |

**Hogar:** ingreso de la UG = suma de las personas de la UG + arriendo
imputado. **Per cápita:** ÷ personas de la UG. Cada persona hereda el per
cápita de su UG y se pondera con `FEX_C18 / 12`.

**Dominio:** rural si `CLASE` = 2; 13 ciudades si `AREA` ∈ {05, 08, 11,
13, 17, 23, 50, 52, 54, 66, 68, 73, 76}; si no, otras cabeceras.

## Variables de salida

| Variable | Definición |
|---|---|
| `ingreso_pc_ug` | Ingreso corriente mensual per cápita de la unidad de gasto |
| `personas_ug` | Personas de la unidad de gasto |
| `LP_2024`, `LI_2024` | Línea de pobreza y de pobreza extrema del dominio |
| `POBRE_MONETARIA`, `POBRE_EXTREMA` | `ingreso_pc_ug` < línea |
| `BRECHA_PM`, `BRECHA_PE` | max(0, (línea − ingreso) / línea) |
| `FUENTE_PM` | `"reconstruccion_geih_publica"` |

En la muestra de estimación (`3b`) se renombran a `ingreso_percapita`,
`POBRE_MONETARIO`, `POBRE_EXTREMO_MONETARIO`, `brecha_pobreza_monetaria`
y `brecha_pobreza_extrema`.

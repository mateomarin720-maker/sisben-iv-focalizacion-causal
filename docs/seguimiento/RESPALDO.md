# Versión de respaldo

El repositorio guarda **un solo respaldo**: la etiqueta de git
`respaldo/ipm-geih-regla-urbana`, en el commit `24ca996` del 11 de
noviembre de 2026. Las demás versiones se recuperan desde la historia de
`main` (`git log`), sin etiqueta.

## Qué es

La última versión antes de corregir las privaciones de vivienda del
IPM-GEIH por zona (commit `74b8891`, 11-nov, y regeneración de los
modelos en `936d96c`, 12-nov). Tiene ya la organización por componentes,
los anexos de la tesis, las proposiciones y la validación contra la ECV;
lo único que cambia frente a `main` es el indicador IPM-GEIH y lo que
depende de él.

## Para qué sirve

1. **Cotejar las cifras del borrador revisado por el director** (10 y
   11 de noviembre), que se calcularon con esta versión.
2. **Volver atrás si la corrección por zona tuviera que revertirse.**

## Qué cambia frente a `main`

| | Respaldo (regla urbana en todo el país) | `main` (definición oficial por zona) |
|---|---|---|
| `POBRE_GEIH`, hogares ponderados | 20,4 % | 14,5 % |
| Proxy frente al IPM oficial 2024 (hogar por hogar) | 18,7 % frente a 9,2 %; kappa 0,41 | 13,8 % frente a 9,2 %; kappa 0,51 |
| Zona rural frente al oficial | 63,7 % frente a 21,5 % | 37,0 % frente a 21,5 % |
| DML con la celda exacta, `POBRE_GEIH` | −0,0026 [−0,0049; −0,0002] | −0,0021 [−0,0045; +0,0004] |
| Cota de Fréchet-Manski, `POBRE_GEIH` | [−0,261; +0,380] | [−0,256; +0,278] |

No cambian el Hot-Deck, la pobreza monetaria, la simulación semisintética
ni las conclusiones. Detalle: entradas 42 a 44 de
[`CHANGELOG_PENDIENTES.md`](CHANGELOG_PENDIENTES.md).

## Cómo usarlo

Ver los archivos de esa versión sin tocar la copia de trabajo:

```bash
git fetch --tags
git worktree add ../sisben_causal_respaldo respaldo/ipm-geih-regla-urbana
```

En GitHub: selector de ramas, pestaña *Tags*, `respaldo/ipm-geih-regla-urbana`.

Los datos no se versionan: para reproducir las cifras del respaldo hay que
correr, desde esa versión, `src/3_preprocesamiento.py` y la secuencia de
`CLAUDE.md` (el banco de Azure tiene las fuentes, no las muestras
intermedias de cada versión).

Revertir solo la corrección del IPM-GEIH en `main` (solo si el equipo lo
decide): `git revert 936d96c 74b8891` deshace esos dos commits sin
reescribir la historia ni tocar lo posterior; después, volver a correr
la secuencia de `CLAUDE.md` para regenerar los reportes.

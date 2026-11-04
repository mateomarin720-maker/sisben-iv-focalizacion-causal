"""Módulo de simulación del framework: evaluación semisintética de
estimadores e integración de fuentes, reutilizable por otras
instituciones con las columnas canónicas (`contrato.py`).

Diseño: `docs/metodologia/DISENO_MODULO_SIMULACION.md`. Resultados con
los hogares de la GEIH 2024: `docs/resultados/SIMULACION_SEMISINTETICA.md`.

    contrato     columnas exigidas por tabla, dominios y validar()
    base         tabla canónica -> tabla de trabajo (celda, X, Y0, U, tau)
    escenarios   escenarios, vínculos, efecto verdadero, convergencia
    asignacion   T verdadero, puntaje y corte
    vinculo      Hot-Deck simulado por celda
    estimadores  diferencia de medias, efectos fijos, DML, RD nítida y difusa
    evaluacion   una repetición, resumen con MCSE, bucle de convergencia
    reportes     tablas y figura
"""

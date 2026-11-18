"""Imputación fraccional (FHDI) sobre la celda del Hot-Deck.

Alternativa al sorteo de un donante, sin modificar el Hot-Deck: reutiliza
su celda y su cadena de respaldos (`emparejamiento_hotdeck_geih_sisben`).

  reglas.py      donantes fraccionales calibrados, FEFI y contraste placebo
  varianza.py    jackknife de grupos eliminados
  validacion.py  acierto del enlace por celda dentro del Sisbén
  __main__.py    corrida con el banco de Azure y comparación con el Hot-Deck

Ver `README.md` de esta carpeta.
"""

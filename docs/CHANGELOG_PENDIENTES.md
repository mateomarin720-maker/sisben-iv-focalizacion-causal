# Changelog — commits pendientes y realizados

## Pendientes de subir (esta sesión, rama `hotdeck-azure-avances`)

- [ ] `src/preprocesamiento/estandarizar_geih.py` — estandarización 12 meses GEIH
- [ ] `src/preprocesamiento/estandarizar_sisben.py` — estandarización Sisbén + fix bug jefes duplicados
- [ ] `src/hotdeck/hotdeck_estandarizado.py` — Hot-Deck validado con datos reales
- [ ] `src/utils/azure_storage.py` — conexión Azure Blob Storage
- [ ] `docs/DICCIONARIO_HOTDECK.md` — actualizado con variables de jefe de hogar y zona
- [ ] `docs/RESUMEN_AVANCES.md` — estado general del proyecto
- [ ] `pyproject.toml` — nombre del proyecto actualizado
- [ ] `.gitignore` — confirmar que incluye `.env`

## Ya realizados en sesiones anteriores (rama `main`)

- [x] Ingesta IPM, GEIH (12 meses), Sisbén IV
- [x] Limpieza IPM (Hogares/Personas/Viviendas)
- [x] Diccionario de datos general (`DICCIONARIO_DATOS.md`)
- [x] Corrección IPM a año de referencia 2024
- [x] `package-mode = false` fix en `pyproject.toml`

## Comando sugerido para el commit de esta sesión

```powershell
git checkout -b hotdeck-azure-avances
git add -A
git commit -m "Estandarizacion GEIH/Sisben, Hot-Deck validado, conexion Azure, diccionario actualizado"
git push -u origin hotdeck-azure-avances
```

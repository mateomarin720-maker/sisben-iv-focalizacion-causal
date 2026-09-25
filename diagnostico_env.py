import os
from dotenv import load_dotenv, find_dotenv

ruta_encontrada = find_dotenv()
print('Ruta del .env que dotenv encontro:', repr(ruta_encontrada))

load_dotenv()
valor = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
print('Variable encontrada:', valor is not None)
print('Longitud del valor (si existe):', len(valor) if valor else 0)

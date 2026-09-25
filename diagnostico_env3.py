import os
from dotenv import load_dotenv
load_dotenv()
valor = os.getenv('AZURE_STORAGE_CONNECTION_STRING')

print('Longitud total:', len(valor) if valor else 0)
print('Contiene DefaultEndpointsProtocol=https:', 'DefaultEndpointsProtocol=https' in valor)
print('Contiene AccountName=:', 'AccountName=' in valor)
print('Contiene AccountKey=:', 'AccountKey=' in valor)
print('Contiene EndpointSuffix=:', 'EndpointSuffix=' in valor)
print('Numero de segmentos separados por ;:', valor.count(';') + 1 if valor else 0)
print('Primeros 25 caracteres:', valor[:25] if valor else None)
print('Ultimos 10 caracteres:', valor[-10:] if valor else None)

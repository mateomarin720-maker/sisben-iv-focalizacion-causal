with open('.env', 'rb') as f:
    contenido = f.read()

print('Bytes totales:', len(contenido))
print('Primeros 5 bytes (hex):', contenido[:5].hex())
print('Numero de lineas:', contenido.count(b'\n') + 1)

texto = contenido.decode('utf-8', errors='replace')
lineas = texto.splitlines()
for i, linea in enumerate(lineas):
    nombre_var = linea.split('=')[0] if '=' in linea else linea
    print(f'Linea {i}: empieza con [{nombre_var!r}], longitud total de la linea: {len(linea)}')

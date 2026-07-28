# Cómo repartir el trabajo de scraping de URLs de ayuntamientos

Este proyecto necesita rellenar la columna `url_ayuntamiento` de la tabla
`municipios` (Supabase) para las 52 provincias de España. El trabajo está
dividido por provincia para que varias sesiones (tuyas o de otros asistentes
de IA) puedan trabajar en paralelo sin pisarse.

## Antes de empezar

1. Lee `docs/estado_fuentes_provincias.md`. Ahí está la lista de las 52
   provincias, su URL fuente, su tipo (A/B/C/D/E) y su estado actual.
2. Elige una fila cuyo estado sea `pendiente`. Si ya no lo es, elige otra —
   significa que otra sesión ya la cogió.
3. **Antes de escribir ningún código**, edita ese fichero y cambia el estado
   de esa provincia a `en_progreso`. Sube ese cambio (commit) inmediatamente.
   Esto es lo único que evita que dos sesiones trabajen la misma provincia
   a la vez — no hay otro mecanismo de bloqueo.

## El patrón a seguir

Usa `scripts/provincias/castellon.py` como plantilla de referencia. La
estructura general de cualquier script de provincia es:

1. Descargar o recorrer la fuente de esa provincia (la URL está en
   `docs/estado_fuentes_provincias.md`).
2. Si es tipo A (dataset descargable): descargar el CSV/JSON/GeoJSON
   directamente.
   Si es tipo B (listado estático): hacer scraping simple del HTML para
   extraer pares (nombre del municipio, URL).
   Si es tipo C (buscador/herramienta interactiva): investigar primero cómo
   devuelve resultados (parámetros de URL, paginación, API interna) antes
   de escribir el script — esto puede requerir más exploración manual.
   Si es tipo D: revisar primero si la URL realmente es un directorio de
   municipios; si no lo es, buscar la fuente correcta antes de escribir
   nada, y anotar lo que se encuentre en la columna Notas.
3. **Ser defensivo con los nombres de columnas o la estructura**: imprimir
   por consola (`print`) lo que se ha encontrado antes de intentar
   procesarlo, para poder diagnosticar rápido si algo no encaja (así se
   hizo en el script de Castellón).
4. Cruzar cada resultado con la tabla `municipios` por `nombre` +
   `provincia` (o por `codigo_ine` si la fuente lo aporta, que es más
   fiable que el nombre).
5. Actualizar la columna `url_ayuntamiento` de esa fila en Supabase.
6. Imprimir un resumen al final (cuántos se actualizaron, de cuántos
   totales).

## Ficheros a crear por cada provincia

- `scripts/provincias/<nombre_provincia>.py` — el script en sí (sin
  espacios ni acentos en el nombre del fichero, ej. `castellon.py`,
  `la_rioja.py`).
- `.github/workflows/poblar_urls_<nombre_provincia>.yml` — el workflow que
  lo ejecuta, con `on: workflow_dispatch` (manual), replicando la
  estructura del de Castellón.

## Credenciales

El script necesita `SUPABASE_URL` y `SUPABASE_SERVICE_KEY`, que ya están
guardadas como Secrets del repositorio — no hace falta pedirlas ni
crearlas de nuevo, el workflow ya las inyecta como variables de entorno.

## Al terminar

1. Lanza el workflow manualmente (pestaña Actions → nombre del workflow →
   "Run workflow") y confirma en el log que se han actualizado filas.
2. Si funciona: vuelve a `docs/estado_fuentes_provincias.md` y cambia el
   estado de esa provincia a `hecho`, añadiendo el nombre del script en la
   columna Notas.
3. Si no funciona: deja el estado en `en_progreso` y anota en Notas qué
   problema encontraste, para que la siguiente sesión que lo revise sepa
   por dónde continuar en vez de empezar de cero.

   ## Caso especial: municipios con artículo (Los/Las/La/El...)

En la tabla `municipios`, los nombres que empiezan por artículo están
guardados con el formato oficial del INE, que coloca el artículo al final
separado por coma — ej. `Altos, Los` en vez de `Los Altos`. Muchas fuentes
externas (CSV, webs de diputaciones) sí usan la forma natural ("Los Altos").

Al cruzar nombres, si el emparejamiento directo falla para un municipio que
empieza por "Los", "Las", "La" o "El", prueba también la forma alternativa
"Resto, Artículo" antes de darlo por no encontrado. Ejemplo de lógica (ver
`scripts/provincias/burgos.py` para la implementación completa):

```python
for articulo in ["los ", "las ", "la ", "el "]:
    if clave.startswith(articulo):
        clave_alternativa = f"{clave[len(articulo):]}, {articulo.strip()}"
        # probar clave_alternativa en el diccionario de municipios

import csv
import io
import re
import unicodedata
import requests
from supabase import create_client
import os

# Configuración de Supabase
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

# URL del dataset descargable (la que funciona en el móvil)
FUENTE_URL = "https://datosabiertos.diputacionalicante.es/resource/csv/directorio-local"

# Configuración de la provincia
PROVINCIA = "Alicante/Alacant"

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def normalizar(texto):
    texto = texto.strip().lower()
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("utf-8")
    texto = re.sub(r"\s+", " ", texto)
    texto = re.sub(r"\s+,", ",", texto)
    return texto


def sin_articulo_final(texto):
    return re.sub(r",\s*(el|la|los|las)$", "", texto).strip()


def obtener_indice_municipios():
    indice = {}
    inicio = 0
    tamano_pagina = 1000

    while True:
        resp = (
            supabase.table("municipios")
            .select("id, nombre")
            .eq("provincia", PROVINCIA)
            .range(inicio, inicio + tamano_pagina - 1)
            .execute()
        )
        if not resp.data:
            break

        for m in resp.data:
            claves = set()
            base = normalizar(m["nombre"])
            claves.add(base)
            claves.add(sin_articulo_final(base))

            for parte in m["nombre"].split("/"):
                p = normalizar(parte)
                claves.add(p)
                claves.add(sin_articulo_final(p))

            for c in claves:
                indice.setdefault(c, m)

        if len(resp.data) < tamano_pagina:
            break
        inicio += tamano_pagina

    return indice


def extraer_municipios_desde_csv(contenido):
    """Lee el CSV y extrae pares (nombre, web) intentando detectar columnas."""
    # Usar el delimitador correcto (punto y coma o coma)
    try:
        lector = csv.DictReader(io.StringIO(contenido), delimiter=';')
        filas = list(lector)
        if not filas:
            lector = csv.DictReader(io.StringIO(contenido), delimiter=',')
            filas = list(lector)
        if not filas:
            print("No se pudo leer el CSV con ; o ,")
            return []
    except Exception as e:
        print(f"Error al leer el CSV: {e}")
        return []

    columnas = list(filas[0].keys())
    print(f"Columnas detectadas: {columnas}")

    # Buscar columna de nombre y web
    col_nombre = None
    col_web = None
    candidatos_nombre = ["denominacion", "nombre", "municipio", "localidad", "poblacion", "ayuntamiento"]
    candidatos_web = ["web", "url", "pagina_web", "direccion_web", "sitio_web"]

    for col in columnas:
        col_lower = col.lower().strip()
        if col_nombre is None and any(c in col_lower for c in candidatos_nombre):
            col_nombre = col
        if col_web is None and any(c in col_lower for c in candidatos_web):
            col_web = col

    if not col_nombre or not col_web:
        print(f"No se encontraron columnas clave. nombre: {col_nombre}, web: {col_web}")
        # Listar columnas para depuración
        print("Columnas disponibles:", columnas)
        return []

    municipios = []
    for fila in filas:
        nombre = fila.get(col_nombre, "").strip()
        url = fila.get(col_web, "").strip()
        if nombre and url:
            # Limpiar URL si es necesario
            if not url.startswith("http"):
                url = "http://" + url
            municipios.append({"nombre": nombre, "url": url})

    return municipios


def buscar_municipio(indice, nombre_csv):
    base = normalizar(nombre_csv)
    candidatos = {base, sin_articulo_final(base)}

    for parte in nombre_csv.split("/"):
        p = normalizar(parte)
        candidatos.add(p)
        candidatos.add(sin_articulo_final(p))

    for c in candidatos:
        if c in indice:
            return indice[c]

    return None


def main():
    print(f"📥 Descargando dataset de {FUENTE_URL}...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        respuesta = requests.get(FUENTE_URL, headers=headers, timeout=60)
        respuesta.raise_for_status()
        contenido = respuesta.text
    except Exception as e:
        print(f"❌ Error al descargar el dataset: {e}")
        return

    municipios_origen = extraer_municipios_desde_csv(contenido)

    if not municipios_origen:
        print("⚠️ No se encontraron municipios en el CSV.")
        return

    print(f"✅ Encontrados {len(municipios_origen)} municipios en el dataset.")

    indice = obtener_indice_municipios()
    print(f"📊 {len(indice)} municipios en la base de datos para {PROVINCIA}.")

    actualizados = 0
    no_emparejados = []

    for item in municipios_origen:
        nombre = item["nombre"]
        url = item["url"]

        municipio = buscar_municipio(indice, nombre)

        if municipio:
            supabase.table("municipios").update({
                "url_ayuntamiento": url
            }).eq("id", municipio["id"]).execute()
            actualizados += 1
            print(f"✅ Actualizado: {nombre} -> {url}")
        else:
            no_emparejados.append(nombre)
            print(f"⚠️ No emparejado: {nombre}")

    print("\n" + "="*50)
    print(f"📈 Total actualizados: {actualizados} de {len(municipios_origen)}")
    print(f"❌ No emparejados ({len(no_emparejados)}): {no_emparejados[:10]}" + ("..." if len(no_emparejados) > 10 else ""))
    print("="*50)


if __name__ == "__main__":
    main()

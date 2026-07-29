import csv
import io
import os
import re
import unicodedata
import requests
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

DATASET_URL = (
    "https://datosabiertos.dipcas.es/api/explore/v2.1/catalog/"
    "datasets/ayuntamientos/exports/csv?lang=es&timezone=Europe%2FMadrid&delimiter=%3B"
)

CANDIDATOS_NOMBRE = ["nombre_poblacion", "nombre_municipio", "municipio", "nombre", "poblacion"]
CANDIDATOS_WEB = ["web", "pagina_web", "url", "url_web", "sitio_web", "website", "web_ayuntamiento"]

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def normalizar(texto):
    texto = texto.strip().lower()
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("utf-8")
    texto = re.sub(r"\s+", " ", texto)
    texto = re.sub(r"\s+,", ",", texto)
    return texto


def detectar_columna(columnas, candidatos):
    for c in candidatos:
        if c in columnas:
            return c
    return None


def obtener_indice_municipios():
    resp = supabase.table("municipios").select("id, nombre").execute()
    indice = {}
    for m in resp.data:
        indice[normalizar(m["nombre"])] = m
        for parte in m["nombre"].split("/"):
            indice.setdefault(normalizar(parte), m)
    return indice


def main():
    resp = requests.get(DATASET_URL)
    resp.raise_for_status()
    filas = list(csv.DictReader(io.StringIO(resp.text), delimiter=";"))

    if not filas:
        print("El dataset vino vacío. Revisar la URL.")
        return

    columnas = list(filas[0].keys())
    print("Columnas encontradas en el dataset:", columnas)

    col_nombre = detectar_columna(columnas, CANDIDATOS_NOMBRE)
    col_web = detectar_columna(columnas, CANDIDATOS_WEB)

    if not col_nombre or not col_web:
        print(f"No se pudo emparejar automáticamente. nombre={col_nombre}, web={col_web}")
        print("Revisa la lista de columnas de arriba y ajusta CANDIDATOS_NOMBRE/CANDIDATOS_WEB.")
        return

    indice = obtener_indice_municipios()

    actualizados = 0
    no_emparejados = []

    for fila in filas:
        nombre = fila.get(col_nombre, "").strip()
        web = fila.get(col_web, "").strip()
        if not nombre or not web:
            continue

        municipio = indice.get(normalizar(nombre))
        if municipio:
            supabase.table("municipios").update({"url_ayuntamiento": web}).eq("id", municipio["id"]).execute()
            actualizados += 1
            print(f"Actualizado: {nombre} -> {web}")
        else:
            no_emparejados.append(nombre)

    print(f"\nTotal actualizados: {actualizados} de {len(filas)} filas del dataset")
    print(f"Sin emparejar ({len(no_emparejados)}): {no_emparejados}")


if __name__ == "__main__":
    main()

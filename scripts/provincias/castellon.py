import csv
import io
import os
import requests
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

DATASET_URL = (
    "https://datosabiertos.dipcas.es/api/explore/v2.1/catalog/"
    "datasets/ayuntamientos/exports/csv?lang=es&timezone=Europe%2FMadrid&delimiter=%3B"
)

# Nombres candidatos de columna, por si el real no coincide exacto
CANDIDATOS_NOMBRE = ["nombre_poblacion", "nombre_municipio", "municipio", "nombre", "poblacion"]
CANDIDATOS_WEB = ["web", "pagina_web", "url", "url_web", "sitio_web", "website", "web_ayuntamiento"]
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def detectar_columna(columnas, candidatos):
    for c in candidatos:
        if c in columnas:
            return c
    return None


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

    actualizados = 0
    for fila in filas:
        nombre = fila.get(col_nombre, "").strip()
        web = fila.get(col_web, "").strip()
        if not nombre or not web:
            continue

        resp = (
            supabase.table("municipios")
            .update({"url_ayuntamiento": web})
            .eq("nombre", nombre)
            .eq("provincia", "Castellón")
            .execute()
        )
        if resp.data:
            actualizados += 1
            print(f"Actualizado: {nombre} -> {web}")

    print(f"Total actualizados: {actualizados} de {len(filas)} filas del dataset")


if __name__ == "__main__":
    main()

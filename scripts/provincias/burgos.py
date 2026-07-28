import csv
import os
import unicodedata
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

RUTA_CSV = "scripts/provincias/data/burgos_urls.csv"
PROVINCIA = "Burgos"

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def normalizar(texto):
    texto = texto.strip().lower()
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("utf-8")
    return texto


def obtener_municipios_provincia():
    resp = supabase.table("municipios").select("id, nombre").eq("provincia", PROVINCIA).execute()
    return {normalizar(m["nombre"]): m for m in resp.data}


def main():
    with open(RUTA_CSV, encoding="utf-8") as f:
        filas = list(csv.DictReader(f))

    print(f"Filas en el CSV: {len(filas)}")

    municipios = obtener_municipios_provincia()
    print(f"Municipios de {PROVINCIA} en la base de datos: {len(municipios)}")

    actualizados = 0
    no_emparejados = []

    for fila in filas:
        nombre = fila["Municipio"].strip()
        web = fila["URL oficial"].strip()
        if not web:
            continue

        clave = normalizar(nombre)
        municipio = municipios.get(clave)

        if municipio:
            supabase.table("municipios").update({"url_ayuntamiento": web}).eq("id", municipio["id"]).execute()
            actualizados += 1
        else:
            no_emparejados.append(nombre)

    print(f"\nTotal actualizados: {actualizados} de {len(filas)} filas del CSV")
    print(f"Sin emparejar ({len(no_emparejados)}): {no_emparejados}")


if __name__ == "__main__":
    main()

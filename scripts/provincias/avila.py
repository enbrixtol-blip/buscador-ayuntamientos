import csv
import os
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

RUTA_CSV = "scripts/provincias/data/avila_urls.csv"

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def main():
    with open(RUTA_CSV, encoding="utf-8") as f:
        filas = list(csv.DictReader(f))

    print(f"Filas en el CSV: {len(filas)}")

    actualizados = 0
    sin_url = []

    for fila in filas:
        id_municipio = fila["id"].strip()
        web = fila["url_ayuntamiento"].strip()
        if not web:
            sin_url.append(fila["nombre"])
            continue

        supabase.table("municipios").update({"url_ayuntamiento": web}).eq("id", id_municipio).execute()
        actualizados += 1

    print(f"\nTotal actualizados: {actualizados} de {len(filas)} filas del CSV")
    print(f"Sin URL en el CSV ({len(sin_url)}): {sin_url}")


if __name__ == "__main__":
    main()

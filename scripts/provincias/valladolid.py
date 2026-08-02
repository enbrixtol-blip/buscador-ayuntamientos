import csv
import os
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

RUTA_CSV = "scripts/provincias/data/valladolid_urls.csv"

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def main():
    with open(RUTA_CSV, encoding="utf-8") as f:
        filas = list(csv.DictReader(f))

    print(f"Filas en el CSV: {len(filas)}")

    actualizados = 0
    no_encontrados = []

    for fila in filas:
        codigo_ine = fila["codigo_ine"].strip()
        nombre = fila["nombre"].strip()
        web = fila["url_ayuntamiento"].strip()

        if not web:
            continue

        resp = (
            supabase.table("municipios")
            .update({"url_ayuntamiento": web})
            .eq("codigo_ine", codigo_ine)
            .execute()
        )
        if resp.data:
            actualizados += 1
        else:
            no_encontrados.append(f"{nombre} ({codigo_ine})")

    print(f"\nTotal actualizados: {actualizados} de {len(filas)} filas del CSV")
    print(f"No encontrados por codigo_ine ({len(no_encontrados)}): {no_encontrados}")


if __name__ == "__main__":
    main()

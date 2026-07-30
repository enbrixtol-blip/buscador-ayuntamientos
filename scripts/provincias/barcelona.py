import csv
import os
import re
import unicodedata
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

RUTA_CSV = "scripts/provincias/data/barcelona_urls.csv"
PROVINCIA = "Barcelona"

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def normalizar(texto):
    texto = texto.strip().lower()
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("utf-8")
    texto = re.sub(r"\s+", " ", texto)
    texto = re.sub(r"\s+,", ",", texto)
    return texto


def sin_articulo_final(texto):
    return re.sub(r",\s*(el|la|los|las|els|les|l')$", "", texto).strip()


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
    with open(RUTA_CSV, encoding="utf-8") as f:
        filas = list(csv.DictReader(f))

    print(f"Filas en el CSV: {len(filas)}")

    indice = obtener_indice_municipios()
    print(f"Municipios de {PROVINCIA} en la base de datos: {len(indice)} claves indexadas")

    actualizados = 0
    no_emparejados = []

    for fila in filas:
        nombre = fila["Municipio"].strip()
        web = fila["URL oficial"].strip()
        if not web:
            continue

        municipio = buscar_municipio(indice, nombre)
        if municipio:
            supabase.table("municipios").update({"url_ayuntamiento": web}).eq("id", municipio["id"]).execute()
            actualizados += 1
        else:
            no_emparejados.append(nombre)

    print(f"\nTotal actualizados: {actualizados} de {len(filas)} filas del CSV")
    print(f"Sin emparejar ({len(no_emparejados)}): {no_emparejados}")


if __name__ == "__main__":
    main()

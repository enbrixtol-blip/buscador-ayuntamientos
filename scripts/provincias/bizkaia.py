import csv
import os
import re
import unicodedata
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

RUTA_CSV = "scripts/provincias/data/bizkaia_urls.csv"
PROVINCIA = "Bizkaia"  # AJUSTA esto según el resultado de la consulta SQL de arriba

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def normalizar(texto):
    texto = texto.strip().lower()
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("utf-8")
    texto = re.sub(r"\s+", " ", texto)
    texto = re.sub(r"\s+,", ",", texto)
    return texto


PATRON_ART_PARENTESIS = r"\((l'|d'|el|la|los|las|els)\)"


def extraer_articulo_y_normalizar(texto):
    texto = normalizar(texto)
    m = re.search(PATRON_ART_PARENTESIS, texto)
    if m:
        articulo = m.group(1)
        resto = re.sub(PATRON_ART_PARENTESIS, "", texto).strip()
        texto = f"{resto}, {articulo}"
    else:
        for articulo in ["los ", "las ", "els ", "la ", "el "]:
            if texto.startswith(articulo):
                resto = texto[len(articulo):].strip()
                texto = f"{resto}, {articulo.strip()}"
                break
    texto = re.sub(r"\s+", " ", texto)
    texto = re.sub(r"\s+,", ",", texto)
    texto = re.sub(r",\s*,\s*", ", ", texto)
    return texto


def sin_articulo_final(texto):
    return re.sub(r",\s*(el|la|los|las|els|les|l'|d')$", "", texto).strip()


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
            nombre = m["nombre"]
            base = normalizar(nombre)
            claves.add(base)
            claves.add(sin_articulo_final(base))
            claves.add(extraer_articulo_y_normalizar(nombre))
            for parte in nombre.split("/"):
                p = normalizar(parte)
                claves.add(p)
                claves.add(sin_articulo_final(p))
                claves.add(extraer_articulo_y_normalizar(parte))
            for c in claves:
                indice.setdefault(c, m)
        if len(resp.data) < tamano_pagina:
            break
        inicio += tamano_pagina
    return indice


def buscar_municipio(indice, nombre_csv):
    candidatos = {normalizar(nombre_csv), extraer_articulo_y_normalizar(nombre_csv)}
    for parte in nombre_csv.split("/"):
        candidatos.add(normalizar(parte))
        candidatos.add(extraer_articulo_y_normalizar(parte))
    for c in list(candidatos):
        candidatos.add(sin_articulo_final(c))
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

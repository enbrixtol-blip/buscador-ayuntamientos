import csv
import io
import os
import re
import unicodedata
import requests
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

DATASET_URL = "https://zenodo.org/records/17573972/files/municipios_Aragon.csv?download=1"

CANDIDATOS_NOMBRE = ["municipio", "nombre", "nombre_municipio", "poblacion"]
CANDIDATOS_WEB = ["sitio_web_oficial", "sitio web oficial", "web", "pagina_web", "url"]
CANDIDATOS_PROVINCIA = ["provincia"]

PROVINCIAS_ARAGON = ["Huesca", "Zaragoza", "Teruel"]

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def normalizar(texto):
    texto = texto.strip().lower()
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("utf-8")
    texto = re.sub(r"\s+", " ", texto)
    texto = re.sub(r"\s+,", ",", texto)
    return texto


def sin_articulo_final(texto):
    return re.sub(r",\s*(el|la|los|las)$", "", texto).strip()


def detectar_columna(columnas, candidatos):
    for c in candidatos:
        if c in columnas:
            return c
    return None


def obtener_indice_municipios():
    indice = {}
    inicio = 0
    tamano_pagina = 1000
    while True:
        resp = (
            supabase.table("municipios")
            .select("id, nombre, provincia")
            .in_("provincia", PROVINCIAS_ARAGON)
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
    resp = requests.get(DATASET_URL)
    resp.raise_for_status()
    filas = list(csv.DictReader(io.StringIO(resp.text)))

    if not filas:
        print("El dataset vino vacío. Revisar la URL.")
        return

    columnas = list(filas[0].keys())
    print("Columnas encontradas en el dataset:", columnas)

    col_nombre = detectar_columna(columnas, CANDIDATOS_NOMBRE)
    col_web = detectar_columna(columnas, CANDIDATOS_WEB)

    if not col_nombre or not col_web:
        print(f"No se pudo emparejar automáticamente. nombre={col_nombre}, web={col_web}")
        print("Ajusta CANDIDATOS_NOMBRE/CANDIDATOS_WEB según la lista de columnas de arriba.")
        return

    indice = obtener_indice_municipios()
    print(f"Municipios de Aragón en la base de datos: {len(indice)} claves indexadas")

    actualizados = 0
    no_emparejados = []

    for fila in filas:
        nombre = fila.get(col_nombre, "").strip()
        web = fila.get(col_web, "").strip()
        if not nombre or not web:
            continue

        municipio = buscar_municipio(indice, nombre)
        if municipio:
            supabase.table("municipios").update({"url_ayuntamiento": web}).eq("id", municipio["id"]).execute()
            actualizados += 1
            print(f"Actualizado: {nombre} ({municipio['provincia']}) -> {web}")
        else:
            no_emparejados.append(nombre)

    print(f"\nTotal actualizados: {actualizados} de {len(filas)} filas del dataset")
    print(f"Sin emparejar ({len(no_emparejados)}): {no_emparejados}")


if __name__ == "__main__":
    main()

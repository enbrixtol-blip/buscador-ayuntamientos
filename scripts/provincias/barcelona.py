import os
import re
import unicodedata
import requests
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

DATASET_URL = "http://do.diba.cat/api/dataset/municipis/format/json2"
PROVINCIA = "Barcelona"

CANDIDATOS_NOMBRE = ["nom", "nombre", "municipi", "municipio"]
CANDIDATOS_WEB = ["web", "url", "pagina_web", "sitio_web"]

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def normalizar(texto):
    texto = texto.strip().lower()
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("utf-8")
    texto = re.sub(r"\s+", " ", texto)
    texto = re.sub(r"\s+,", ",", texto)
    return texto


def sin_articulo_final(texto):
    return re.sub(r",\s*(el|la|los|las|l'|els|les)$", "", texto).strip()


def detectar_campo(registro, candidatos):
    for c in candidatos:
        if c in registro:
            return c
    return None


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


def buscar_municipio(indice, nombre_fuente):
    base = normalizar(nombre_fuente)
    candidatos = {base, sin_articulo_final(base)}
    for parte in nombre_fuente.split("/"):
        p = normalizar(parte)
        candidatos.add(p)
        candidatos.add(sin_articulo_final(p))
    for c in candidatos:
        if c in indice:
            return indice[c]
    return None


def main():
    resp = requests.get(DATASET_URL, timeout=30)
    resp.raise_for_status()
    datos = resp.json()

    # La estructura exacta del JSON puede variar; se maneja de forma flexible.
    registros = datos if isinstance(datos, list) else datos.get("data", datos.get("results", []))

    if not registros:
        print("No se han encontrado registros. Estructura del JSON recibido:")
        print(str(datos)[:1000])
        return

    print(f"Registros recibidos: {len(registros)}")
    print("Campos de ejemplo del primer registro:", list(registros[0].keys()))

    col_nombre = detectar_campo(registros[0], CANDIDATOS_NOMBRE)
    col_web = detectar_campo(registros[0], CANDIDATOS_WEB)

    if not col_nombre or not col_web:
        print(f"No se pudo emparejar automáticamente. nombre={col_nombre}, web={col_web}")
        print("Ajusta CANDIDATOS_NOMBRE/CANDIDATOS_WEB según los campos de arriba.")
        return

    indice = obtener_indice_municipios()
    print(f"Municipios de Barcelona en la base de datos indexados: {len(indice)} claves")

    actualizados = 0
    no_emparejados = []

    for registro in registros:
        nombre = str(registro.get(col_nombre, "")).strip()
        web = str(registro.get(col_web, "")).strip()
        if not nombre or not web or web.lower() == "none":
            continue

        municipio = buscar_municipio(indice, nombre)
        if municipio:
            supabase.table("municipios").update({"url_ayuntamiento": web}).eq("id", municipio["id"]).execute()
            actualizados += 1
            print(f"Actualizado: {nombre} -> {web}")
        else:
            no_emparejados.append(nombre)

    print(f"\nTotal actualizados: {actualizados} de {len(registros)} registros")
    print(f"Sin emparejar ({len(no_emparejados)}): {no_emparejados}")


if __name__ == "__main__":
    main()

import csv
import io
import os
import time
import requests
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

CSV_MUNICIPIOS_URL = "https://raw.githubusercontent.com/codeforspain/datosine/master/municipios.csv"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS_NOMINATIM = {"User-Agent": "buscador-ayuntamientos/1.0 (proyecto personal)"}

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def obtener_municipios():
    resp = requests.get(CSV_MUNICIPIOS_URL)
    resp.raise_for_status()
    lector = csv.DictReader(io.StringIO(resp.text))
    return list(lector)


def geocodificar(nombre, provincia):
    params = {
        "q": f"{nombre}, {provincia}, España",
        "format": "json",
        "limit": 1,
    }
    resp = requests.get(NOMINATIM_URL, params=params, headers=HEADERS_NOMINATIM)
    resp.raise_for_status()
    resultados = resp.json()
    if resultados:
        return float(resultados[0]["lat"]), float(resultados[0]["lon"])
    return None, None


def ya_existe(codigo_ine):
    resp = supabase.table("municipios").select("id").eq("codigo_ine", codigo_ine).execute()
    return len(resp.data) > 0


def main():
    municipios = obtener_municipios()
    print(f"Total municipios a procesar: {len(municipios)}")

    for i, m in enumerate(municipios):
        codigo_ine = m["codigo_ine"]
        nombre = m["nombre"]
        provincia = m["provincia"]
        ccaa = m["ccaa"]

        if ya_existe(codigo_ine):
            continue  # permite reanudar si el workflow se corta a mitad

        lat, lon = geocodificar(nombre, provincia)

        supabase.table("municipios").insert({
            "nombre": nombre,
            "provincia": provincia,
            "ccaa": ccaa,
            "codigo_ine": codigo_ine,
            "latitud": lat,
            "longitud": lon,
        }).execute()

        print(f"[{i+1}/{len(municipios)}] {nombre} -> lat={lat}, lon={lon}")
        time.sleep(1)  # obligatorio por la política de uso de Nominatim


if __name__ == "__main__":
    main()

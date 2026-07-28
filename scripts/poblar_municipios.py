import csv
import io
import os
import time
import requests
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

CSV_MUNICIPIOS_URL = "https://raw.githubusercontent.com/codeforspain/ds-organizacion-administrativa/master/data/municipios.csv"
CSV_PROVINCIAS_URL = "https://raw.githubusercontent.com/codeforspain/ds-organizacion-administrativa/master/data/provincias.csv"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS_NOMINATIM = {"User-Agent": "buscador-ayuntamientos/1.0 (proyecto personal)"}

# Relación fija provincia -> comunidad autónoma (no cambia, no viene en el CSV)
PROVINCIA_A_CCAA = {
    "01": "País Vasco", "02": "Castilla-La Mancha", "03": "Comunidad Valenciana",
    "04": "Andalucía", "05": "Castilla y León", "06": "Extremadura",
    "07": "Illes Balears", "08": "Cataluña", "09": "Castilla y León",
    "10": "Extremadura", "11": "Andalucía", "12": "Comunidad Valenciana",
    "13": "Castilla-La Mancha", "14": "Andalucía", "15": "Galicia",
    "16": "Castilla-La Mancha", "17": "Cataluña", "18": "Andalucía",
    "19": "Castilla-La Mancha", "20": "País Vasco", "21": "Andalucía",
    "22": "Aragón", "23": "Andalucía", "24": "Castilla y León",
    "25": "Cataluña", "26": "La Rioja", "27": "Galicia",
    "28": "Comunidad de Madrid", "29": "Andalucía", "30": "Región de Murcia",
    "31": "Comunidad Foral de Navarra", "32": "Galicia", "33": "Principado de Asturias",
    "34": "Castilla y León", "35": "Canarias", "36": "Galicia",
    "37": "Castilla y León", "38": "Canarias", "39": "Cantabria",
    "40": "Castilla y León", "41": "Andalucía", "42": "Castilla y León",
    "43": "Cataluña", "44": "Aragón", "45": "Castilla-La Mancha",
    "46": "Comunidad Valenciana", "47": "Castilla y León", "48": "País Vasco",
    "49": "Castilla y León", "50": "Aragón", "51": "Ceuta", "52": "Melilla",
}

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def descargar_csv(url):
    resp = requests.get(url)
    resp.raise_for_status()
    return list(csv.DictReader(io.StringIO(resp.text)))


def obtener_provincias():
    filas = descargar_csv(CSV_PROVINCIAS_URL)
    return {f["provincia_id"]: f["nombre"] for f in filas}


def obtener_municipios():
    return descargar_csv(CSV_MUNICIPIOS_URL)


def geocodificar(nombre, provincia):
    params = {"q": f"{nombre}, {provincia}, España", "format": "json", "limit": 1}
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
    provincias = obtener_provincias()
    municipios = obtener_municipios()
    print(f"Total municipios a procesar: {len(municipios)}")

    for i, m in enumerate(municipios):
        codigo_ine = m["municipio_id"]
        nombre = m["nombre"]
        provincia_id = m["provincia_id"]
        provincia = provincias.get(provincia_id, "")
        ccaa = PROVINCIA_A_CCAA.get(provincia_id, "")

        if ya_existe(codigo_ine):
            continue

        lat, lon = geocodificar(nombre, provincia)

        supabase.table("municipios").insert({
            "nombre": nombre,
            "provincia": provincia,
            "ccaa": ccaa,
            "codigo_ine": codigo_ine,
            "latitud": lat,
            "longitud": lon,
        }).execute()

        print(f"[{i+1}/{len(municipios)}] {nombre} ({provincia}) -> lat={lat}, lon={lon}")
        time.sleep(1)


if __name__ == "__main__":
    main()

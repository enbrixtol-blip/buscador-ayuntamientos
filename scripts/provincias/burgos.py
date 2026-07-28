import os
import unicodedata
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

URL_FUENTE = "https://www.burgos.es/provincia/geografia/municipios"
NOMBRE_PROVINCIA = "Castilla y León"  # ccaa, no usado para filtrar; ver PROVINCIA abajo
PROVINCIA = "Burgos"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; buscador-ayuntamientos/1.0)"}

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def normalizar(texto):
    texto = texto.strip().lower()
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("utf-8")
    return texto


def obtener_municipios_provincia():
    resp = supabase.table("municipios").select("id, nombre").eq("provincia", PROVINCIA).execute()
    return {normalizar(m["nombre"]): m for m in resp.data}


def extraer_enlaces_externos(html, dominio_fuente):
    soup = BeautifulSoup(html, "html.parser")
    candidatos = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        texto = a.get_text(strip=True)
        if not texto or not href.startswith("http"):
            continue
        dominio_enlace = urlparse(href).netloc
        if dominio_enlace and dominio_enlace != dominio_fuente:
            candidatos.append((texto, href))
    return candidatos


def main():
    resp = requests.get(URL_FUENTE, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    dominio_fuente = urlparse(URL_FUENTE).netloc
    candidatos = extraer_enlaces_externos(resp.text, dominio_fuente)
    print(f"Enlaces externos encontrados en la página: {len(candidatos)}")

    municipios = obtener_municipios_provincia()
    print(f"Municipios de {PROVINCIA} en la base de datos: {len(municipios)}")

    actualizados = 0
    no_emparejados = []

    for texto, href in candidatos:
        clave = normalizar(texto)
        municipio = municipios.get(clave)
        if municipio:
            supabase.table("municipios").update({"url_ayuntamiento": href}).eq("id", municipio["id"]).execute()
            actualizados += 1
            print(f"Actualizado: {texto} -> {href}")
        else:
            no_emparejados.append(texto)

    print(f"\nTotal actualizados: {actualizados}")
    print(f"Enlaces sin emparejar ({len(no_emparejados)}): {no_emparejados[:20]}")


if __name__ == "__main__":
    main()

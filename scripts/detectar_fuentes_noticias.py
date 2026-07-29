import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; buscador-ayuntamientos/1.0)"}
TIMEOUT = 10
RUTAS_CANDIDATAS = ["/rss", "/feed", "/feed.xml", "/rss.xml", "/noticias/rss", "/actualidad/rss"]

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def obtener_pendientes():
    pendientes = []
    inicio = 0
    tamano_pagina = 1000
    while True:
        resp = (
            supabase.table("municipios")
            .select("id, nombre, url_ayuntamiento")
            .not_.is_("url_ayuntamiento", "null")
            .is_("tipo_fuente", "null")
            .range(inicio, inicio + tamano_pagina - 1)
            .execute()
        )
        if not resp.data:
            break
        pendientes.extend(resp.data)
        if len(resp.data) < tamano_pagina:
            break
        inicio += tamano_pagina
    return pendientes


def normalizar_url(url):
    if not url.startswith("http"):
        url = "http://" + url
    return url


def buscar_rss_en_head(html, url_base):
    soup = BeautifulSoup(html, "html.parser")
    for link in soup.find_all("link", rel="alternate"):
        tipo = link.get("type", "")
        if "rss" in tipo or "atom" in tipo:
            href = link.get("href")
            if href:
                return urljoin(url_base, href)
    return None


def parece_feed(texto):
    inicio = texto.strip()[:200].lower()
    return "<rss" in inicio or "<feed" in inicio or "<?xml" in inicio


def probar_rutas_candidatas(url_base):
    for ruta in RUTAS_CANDIDATAS:
        url_intento = urljoin(url_base, ruta)
        try:
            resp = requests.get(url_intento, headers=HEADERS, timeout=TIMEOUT)
            if resp.status_code == 200 and parece_feed(resp.text):
                return url_intento
        except requests.RequestException:
            continue
    return None


def main():
    pendientes = obtener_pendientes()
    print(f"Municipios pendientes de detectar fuente: {len(pendientes)}")

    contador = {"rss": 0, "scraping": 0, "error": 0}

    for m in pendientes:
        url_base = normalizar_url(m["url_ayuntamiento"])
        rss_encontrado = None

        try:
            resp = requests.get(url_base, headers=HEADERS, timeout=TIMEOUT)
            if resp.status_code == 200:
                rss_encontrado = buscar_rss_en_head(resp.text, url_base)
        except requests.RequestException as e:
            print(f"[error portada] {m['nombre']}: {e}")

        if not rss_encontrado:
            rss_encontrado = probar_rutas_candidatas(url_base)

        if rss_encontrado:
            supabase.table("municipios").update({
                "tipo_fuente": "rss",
                "url_fuente_noticias": rss_encontrado,
            }).eq("id", m["id"]).execute()
            contador["rss"] += 1
            print(f"RSS encontrado: {m['nombre']} -> {rss_encontrado}")
        else:
            supabase.table("municipios").update({
                "tipo_fuente": "scraping",
            }).eq("id", m["id"]).execute()
            contador["scraping"] += 1
            print(f"Sin RSS (pendiente de scraping manual): {m['nombre']}")

    print(f"\nResumen: {contador}")


if __name__ == "__main__":
    main()

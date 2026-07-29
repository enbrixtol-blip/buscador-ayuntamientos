import os
import re
import unicodedata
import feedparser
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Categorías por orden de prioridad: la primera que coincida gana.
# "otros" es un cajón de sastre genérico, se comprueba el último.
PALABRAS_CLAVE = {
    "fiestas_patronales": [
        "fiestas patronales", "fiesta patronal", "festes majors", "festa major",
        "fiestas populares", "verbena", "romeria", "jaiak", "en honor a san",
        "en honor a santa", "patron del municipio", "patrona del municipio",
    ],
    "concierto": [
        "concierto", "actuacion musical", "orquesta", "festival de musica",
        "recital", "grupo musical", "banda de musica",
    ],
    "feria": [
        "feria medieval", "mercado medieval", "feria del libro",
        "feria de muestras", "mercadillo artesanal", "feria de",
    ],
    "otros": [
        "programacion de actos", "actos festivos", "agenda de eventos",
        "programa de fiestas",
    ],
}


def normalizar(texto):
    texto = texto.lower()
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("utf-8")
    texto = re.sub(r"\s+", " ", texto)
    return texto


def clasificar(titulo, resumen):
    texto = normalizar(f"{titulo} {resumen}")
    for categoria, palabras in PALABRAS_CLAVE.items():
        for palabra in palabras:
            if palabra in texto:
                return categoria
    return None


def obtener_municipios_con_rss():
    municipios = []
    inicio = 0
    tamano_pagina = 1000
    while True:
        resp = (
            supabase.table("municipios")
            .select("id, nombre, url_fuente_noticias")
            .eq("tipo_fuente", "rss")
            .range(inicio, inicio + tamano_pagina - 1)
            .execute()
        )
        if not resp.data:
            break
        municipios.extend(resp.data)
        if len(resp.data) < tamano_pagina:
            break
        inicio += tamano_pagina
    return municipios


def main():
    municipios = obtener_municipios_con_rss()
    print(f"Municipios con RSS a revisar: {len(municipios)}")

    guardados = 0
    revisadas = 0

    for m in municipios:
        try:
            feed = feedparser.parse(m["url_fuente_noticias"])
        except Exception as e:
            print(f"[error feed] {m['nombre']}: {e}")
            continue

        for entrada in feed.entries:
            revisadas += 1
            titulo = entrada.get("title", "").strip()
            resumen = entrada.get("summary", "").strip()
            enlace = entrada.get("link", "").strip()
            if not titulo or not enlace:
                continue

            categoria = clasificar(titulo, resumen)
            if not categoria:
                continue  # no interesa, se descarta

            resumen_corto = resumen[:280] if resumen else None

            supabase.table("eventos").upsert({
                "municipio_id": m["id"],
                "categoria": categoria,
                "titulo": titulo,
                "resumen": resumen_corto,
                "url_noticia": enlace,
                "estado": "vigente",
            }, on_conflict="url_noticia").execute()

            guardados += 1
            print(f"[{categoria}] {m['nombre']}: {titulo}")

    print(f"\nNoticias revisadas: {revisadas}")
    print(f"Guardadas como eventos: {guardados}")


if __name__ == "__main__":
    main()

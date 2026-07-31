import re
import unicodedata
import requests
from bs4 import BeautifulSoup
from supabase import create_client
import os

# Configuración de Supabase
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

# URL de la fuente (la que tienes en tu tabla)
FUENTE_URL = "https://datosabiertos.diputacionalicante.es/resource/csv/directorio-local"

# Configuración de la provincia
PROVINCIA = "Alicante/Alacant"

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def normalizar(texto):
    """Normaliza texto: minúsculas, sin tildes, sin espacios extra."""
    texto = texto.strip().lower()
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("utf-8")
    texto = re.sub(r"\s+", " ", texto)
    texto = re.sub(r"\s+,", ",", texto)
    return texto


def sin_articulo_final(texto):
    """Elimina artículos finales ('el', 'la', 'los', 'las') para emparejamiento."""
    return re.sub(r",\s*(el|la|los|las)$", "", texto).strip()


def obtener_indice_municipios():
    """Construye un índice de municipios de la provincia desde Supabase."""
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

            # Manejar nombres con "/" (ej: "Sant Joan d'Alacant" / "San Juan de Alicante")
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


def extraer_municipios_desde_html(html):
    """Extrae los municipios y sus URLs del HTML de la fuente."""
    soup = BeautifulSoup(html, "html.parser")
    municipios = []

    # Buscar la tabla o lista que contiene los municipios
    # (Esto es un ejemplo, habrá que ajustarlo según la estructura real)
    # Posibles contenedores: tabla, lista desordenada (ul), o enlaces directos

    # Estrategia: buscar todos los enlaces que parezcan municipios
    for enlace in soup.find_all("a", href=True):
        texto = enlace.get_text(strip=True)
        url = enlace["href"]

        # Filtrar para quedarnos solo con enlaces que parezcan municipios
        # (Estos filtros se ajustarán al analizar la página real)
        if texto and "http" in url and len(texto) > 2:
            # Evitar enlaces genéricos (ej: "Inicio", "Contacto")
            if not any(palabra in texto.lower() for palabra in ["inicio", "contacto", "mapa", "web", "email"]):
                municipios.append({
                    "nombre": texto,
                    "url": url
                })

    return municipios


def buscar_municipio(indice, nombre_csv):
    """Busca un municipio en el índice usando diferentes variantes del nombre."""
    base = normalizar(nombre_csv)

    # Probar todas las variantes
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
    print(f"📥 Obteniendo datos de {FUENTE_URL}...")

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        respuesta = requests.get(FUENTE_URL, headers=headers, timeout=30)
        respuesta.raise_for_status()
        html = respuesta.text
    except Exception as e:
        print(f"❌ Error al obtener la página: {e}")
        return

    # Extraer municipios del HTML
    municipios_origen = extraer_municipios_desde_html(html)

    if not municipios_origen:
        print("⚠️ No se encontraron municipios en la página.")
        print("   Puede que la estructura haya cambiado o requiera JavaScript.")
        print("   Sugerencia: revisar manualmente y ajustar el selector.")
        return

    print(f"✅ Encontrados {len(municipios_origen)} municipios en la fuente.")

    # Obtener índice de municipios de Supabase
    indice = obtener_indice_municipios()
    print(f"📊 {len(indice)} municipios en la base de datos para {PROVINCIA}.")

    # Actualizar cada municipio
    actualizados = 0
    no_emparejados = []

    for item in municipios_origen:
        nombre = item["nombre"]
        url = item["url"]

        # Asegurar que la URL es absoluta
        if url.startswith("/"):
            url = "https://documentacion.diputacionalicante.es" + url

        municipio = buscar_municipio(indice, nombre)

        if municipio:
            supabase.table("municipios").update({
                "url_ayuntamiento": url
            }).eq("id", municipio["id"]).execute()
            actualizados += 1
            print(f"✅ Actualizado: {nombre} -> {url}")
        else:
            no_emparejados.append(nombre)
            print(f"⚠️ No emparejado: {nombre}")

    # Resumen final
    print("\n" + "="*50)
    print(f"📈 Total actualizados: {actualizados} de {len(municipios_origen)}")
    print(f"❌ No emparejados ({len(no_emparejados)}): {no_emparejados[:10]}" + ("..." if len(no_emparejados) > 10 else ""))
    print("="*50)


if __name__ == "__main__":
    main()

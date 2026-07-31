import csv
import re
import unicodedata
from supabase import create_client
import os

# Configuración de Supabase
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

# Ruta al archivo CSV local (subido al repositorio)
RUTA_CSV = "scripts/provincias/data/alicante_urls.csv"

# Configuración de la provincia
PROVINCIA = "Alicante/Alacant"

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def normalizar(texto):
    """Normalización básica (sin tildes, minúsculas, sin espacios extra)."""
    texto = texto.strip().lower()
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("utf-8")
    texto = re.sub(r"\s+", " ", texto)
    texto = re.sub(r"\s+,", ",", texto)
    return texto


def normalizar_para_busqueda(texto):
    """Normalización avanzada para buscar en el índice."""
    texto = texto.strip().lower()
    
    # Quitar tildes
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("utf-8")
    
    # Eliminar todo lo que esté entre paréntesis
    texto = re.sub(r"\([^)]*\)", "", texto).strip()
    
    # Manejar artículos delante (ej: "La Romana" -> "Romana, la")
    for articulo in ["los ", "las ", "la ", "el "]:
        if texto.startswith(articulo):
            resto = texto[len(articulo):].strip()
            texto = f"{resto}, {articulo.strip()}"
            break
    
    # Limpiar espacios y comas
    texto = re.sub(r"\s+", " ", texto)
    texto = re.sub(r"\s+,", ",", texto)
    
    return texto


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
            base = normalizar_para_busqueda(m["nombre"])
            claves.add(base)
            claves.add(normalizar(m["nombre"]))

            # Añadir también el nombre original limpio
            for parte in m["nombre"].split("/"):
                p = normalizar_para_busqueda(parte)
                claves.add(p)

            for c in claves:
                indice.setdefault(c, m)

        if len(resp.data) < tamano_pagina:
            break
        inicio += tamano_pagina

    return indice


def extraer_municipios_desde_csv(ruta_csv):
    try:
        with open(ruta_csv, 'r', encoding='utf-8') as f:
            contenido = f.read()
    except FileNotFoundError:
        print(f"❌ No se encontró el archivo en: {ruta_csv}")
        return []

    try:
        lector = csv.DictReader(contenido.splitlines(), delimiter=';')
        filas = list(lector)
        if not filas:
            lector = csv.DictReader(contenido.splitlines(), delimiter=',')
            filas = list(lector)
        if not filas:
            print("No se pudo leer el CSV con ; o ,")
            return []
    except Exception as e:
        print(f"Error al leer el CSV: {e}")
        return []

    columnas = list(filas[0].keys())
    print(f"Columnas detectadas: {columnas}")

    col_nombre = None
    col_web = None
    candidatos_nombre = ["mu_nombre", "denominacion", "nombre", "municipio", "localidad"]
    candidatos_web = ["dl_web", "web", "url", "pagina_web", "direccion_web"]

    for col in columnas:
        col_lower = col.lower().strip()
        if col_nombre is None and any(c in col_lower for c in candidatos_nombre):
            col_nombre = col
        if col_web is None and any(c in col_lower for c in candidatos_web):
            col_web = col

    if not col_nombre or not col_web:
        print(f"No se encontraron columnas clave. nombre: {col_nombre}, web: {col_web}")
        print("Columnas disponibles:", columnas)
        return []

    municipios = []
    for fila in filas:
        nombre = fila.get(col_nombre, "").strip()
        url = fila.get(col_web, "").strip()
        if nombre and url:
            if not url.startswith("http"):
                url = "http://" + url
            municipios.append({"nombre": nombre, "url": url})

    print(f"✅ Extraídos {len(municipios)} municipios del CSV.")
    return municipios


def buscar_municipio(indice, nombre_csv):
    """Busca usando la nueva normalización avanzada."""
    base = normalizar_para_busqueda(nombre_csv)
    candidatos = {base, normalizar(nombre_csv)}
    
    for parte in nombre_csv.split("/"):
        p = normalizar_para_busqueda(parte)
        candidatos.add(p)
    
    for c in candidatos:
        if c in indice:
            return indice[c]
    
    return None


def main():
    print(f"📥 Leyendo dataset desde {RUTA_CSV}...")

    municipios_origen = extraer_municipios_desde_csv(RUTA_CSV)

    if not municipios_origen:
        print("⚠️ No se encontraron municipios en el CSV.")
        return

    print(f"✅ Encontrados {len(municipios_origen)} municipios en el dataset.")

    indice = obtener_indice_municipios()
    print(f"📊 {len(indice)} municipios en la base de datos para {PROVINCIA}.")

    actualizados = 0
    no_emparejados = []

    for item in municipios_origen:
        nombre = item["nombre"]
        url = item["url"]

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

    print("\n" + "="*50)
    print(f"📈 Total actualizados: {actualizados} de {len(municipios_origen)}")
    print(f"❌ No emparejados ({len(no_emparejados)}): {no_emparejados[:10]}" + ("..." if len(no_emparejados) > 10 else ""))
    print("="*50)


if __name__ == "__main__":
    main()

import csv
import re
import unicodedata
from supabase import create_client
import os

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

RUTA_CSV = "scripts/provincias/data/alicante_urls.csv"
PROVINCIA = "Alicante/Alacant"

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def normalizar(texto):
    """Normalización básica: minúsculas, sin tildes, sin espacios extra."""
    texto = texto.strip().lower()
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("utf-8")
    texto = re.sub(r"\s+", " ", texto)
    texto = re.sub(r"\s+,", ",", texto)
    return texto


def extraer_y_mover_articulo(texto):
    """
    Detecta artículos (el, la, los, las, l', d') y los mueve al final.
    Ej: "Atzúbia (L')" -> "atzubia, l'"
        "La Romana" -> "romana, la"
        "Castell de Guadalest (El)" -> "castell de guadalest, el"
    """
    texto_original = texto
    texto = texto.strip().lower()
    
    # 1. Quitar tildes
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("utf-8")
    
    # 2. Extraer artículo entre paréntesis: (L'), (El), (La), (Los), (Las)
    #    y también (l'), (el), (la), (los), (las)
    patron_par = re.search(r'\(([lL]\'|[dD]\'|[eE]l|[lL]a|[lL]os|[lL]as)\)', texto)
    if patron_par:
        articulo = patron_par.group(1).lower()
        # Mapear apóstrofes a su forma normalizada
        if articulo == "l'":
            articulo = "el"  # Normalizamos para comparar
        elif articulo == "d'":
            articulo = "de"
        # Quitar el paréntesis y el artículo del nombre
        texto = re.sub(r'\s*\([lL]\'|[dD]\'|[eE]l|[lL]a|[lL]os|[lL]as\)', '', texto).strip()
        # Añadir artículo al final
        texto = f"{texto}, {articulo}"
    else:
        # 3. Si no hay paréntesis, buscar artículo al principio
        for articulo in ["los ", "las ", "la ", "el "]:
            if texto.startswith(articulo):
                resto = texto[len(articulo):].strip()
                texto = f"{resto}, {articulo.strip()}"
                break
    
    # 4. Limpiar espacios y comas
    texto = re.sub(r"\s+", " ", texto)
    texto = re.sub(r"\s+,", ",", texto)
    texto = re.sub(r",\s*,\s*", ", ", texto)  # Eliminar comas dobles
    
    return texto


def obtener_indice_municipios():
    """Construye un índice con múltiples variantes del nombre para cada municipio."""
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
            
            # 1. El nombre original normalizado
            claves.add(normalizar(nombre))
            
            # 2. El nombre con artículo movido (por si ya está normalizado)
            claves.add(extraer_y_mover_articulo(nombre))
            
            # 3. Cada parte del nombre (para nombres con /)
            for parte in nombre.split("/"):
                p = normalizar(parte)
                claves.add(p)
                claves.add(extraer_y_mover_articulo(parte))
            
            # 4. Versión sin artículo al final (para casos como "San Isidro")
            for clave in list(claves):
                if "," in clave:
                    sin_articulo = re.sub(r",\s*(el|la|los|las|l'|d')$", "", clave).strip()
                    claves.add(sin_articulo)
            
            for c in claves:
                indice.setdefault(c, m)

        if len(resp.data) < tamano_pagina:
            break
        inicio += tamano_pagina

    return indice


def extraer_municipios_desde_csv(ruta_csv):
    """Lee el CSV y extrae pares (nombre, web)."""
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
    """Busca el municipio normalizando el nombre del CSV con la misma lógica."""
    # Generar todas las variantes posibles del nombre del CSV
    candidatos = set()
    
    # 1. Normalización básica
    candidatos.add(normalizar(nombre_csv))
    
    # 2. Mover artículo (si lo tiene)
    candidatos.add(extraer_y_mover_articulo(nombre_csv))
    
    # 3. Cada parte del nombre (para nombres con /)
    for parte in nombre_csv.split("/"):
        candidatos.add(normalizar(parte))
        candidatos.add(extraer_y_mover_articulo(parte))
    
    # 4. Versión sin artículo al final
    for c in list(candidatos):
        if "," in c:
            sin_articulo = re.sub(r",\s*(el|la|los|las|l'|d')$", "", c).strip()
            candidatos.add(sin_articulo)
    
    # Buscar en el índice
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
    print(f"📊 {len(indice)} claves en el índice para {PROVINCIA}.")

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

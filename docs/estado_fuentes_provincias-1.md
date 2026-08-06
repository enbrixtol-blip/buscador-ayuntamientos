# Estado de fuentes de URLs de ayuntamientos por provincia

Leyenda de tipo:
- A: dataset abierto descargable (sin scraping real)
- B: listado estático de municipios (scraping simple)
- C: buscador/herramienta interactiva (scraping más complejo)
- D: la URL no parece ser un directorio de municipios (revisar antes de empezar)
- E: ciudad autónoma de un solo municipio (no aplica directorio)

Estado: pendiente / en_progreso / hecho

| Provincia | URL fuente | Tipo | Estado | Notas |
|---|---|---|---|---|
| Alacant/Alicante | https://documentacion.diputacionalicante.es/dlocal.asp | B | hecho | 141/143 (CSV manual, scripts/provincias/alicante.py). Xara y Jesús Pobre excluidos: son pedanías de Dénia, no municipios independientes. Casos de cambio de nombre oficial resueltos a mano: Facheca→Fageca (2021), Alcocer de Planes→Alcosser. |
| Araba/Álava | https://www.araba.eus/elva/Nomenclator/ELVA5003NomMuni.asp | C | hecho | 51/51, CSV manual (scripts/provincias/alava.py) |
| Albacete | https://www.albacete.es/es | D | hecho | Enlaza solo a la capital, no a un directorio |
| Almería | http://www.dipalme.org/ | B | pendiente | |
| Asturias | http://www.facc.info/?page_id=341 | B | pendiente | |
| Ávila | https://www.diputacionavila.es/la-provincia/nuestros-pueblos/ | B | hecho | |
| Badajoz | http://www.dip-badajoz.es/municipios/municipio_dinamico/index.php | C | pendiente | |
| Barcelona | http://www.diba.es/es/web/municipis | B | hecho | 311/311, CSV manual (scripts/provincias/barcelona.py); API oficial http://do.diba.cat/api/dataset/municipis/format/json2 no se usó por incompatibilidad de estructura |
| Burgos | http://www.burgos.es/provincia/geografia/municipios | B | hecho | 371/371, resuelto con CSV manual (scripts/provincias/data/burgos_urls.csv), no scraping — la web de la diputación requiere JavaScript |
| Cáceres | https://www.provinciadecaceres.es/mapa-de-ayuntamientos | B | pendiente | |
| Cádiz | https://www.dipucadiz.es/diputacion/ | B | hecho | 45/45, CSV manual (scripts/provincias/cadiz.py) |
| Cantabria | http://administracionlocal.cantabria.es/municipios | B | pendiente | |
| Castelló/Castellón | https://datosabiertos.dipcas.es/explore/dataset/ayuntamientos/table/ | A | hecho | 135/136 (Ballestar excluido, es pedanía de Pobla de Benifassà, no municipio). Dataset descargable directo |
| Ceuta | http://www.ceuta.es/ | E | — | Ciudad única |
| Ciudad Real | https://www.dipucr.es/municipios | B | pendiente | |
| Córdoba | https://www.famp.es/es/entidades-locales/entidades-adheridas/index.html?idcategoria=Ayuntamiento&idprovincia=3 | C | pendiente | |
| Coruña, A | https://www.dacoruna.gal/direct/directorio-concellos | B | pendiente | |
| Cuenca | https://www.dipucuenca.es/municipios1 | B | pendiente | |
| Girona/Gerona | (por revisar) | D | pendiente | El PAG enlaza por error a la URL de A Coruña; buscar fuente correcta |
| Granada | https://www.granada.org/ | D | pendiente | Enlaza solo a la capital, no a un directorio |
| Guadalajara | http://www.dguadalajara.es/web/guest/municipios | B | pendiente | |
| Gipuzkoa/Guipúzcoa | https://www.gipuzkoa.eus/es/web/ogasuna/catastro/herramientas-gestion/planos-parcelarios/listado-municipios | D | pendiente | Parece herramienta de catastro, no directorio de webs |
| Huelva | https://www.diphuelva.es/servicios/municipios/ | B | pendiente | |
| Huesca | https://www.dphuesca.es/municipios | A | hecho | Parte del dataset conjunto de Aragón (Huesca+Zaragoza+Teruel): 578/731 en total. https://zenodo.org/records/17573972/files/municipios_Aragon.csv?download=1 |
| Illes Balears/Islas Baleares | https://www.caib.es/sites/cedomu/es/paginas_webs_de_los_consejos_insulares-25829/ | B | pendiente | Enlaza a consejos insulares, revisar si llega a nivel municipio |
| Jaén | http://www.dipujaen.es/municipios/directorio.html | B | pendiente | |
| León | https://www.dipuleon.es/municipios/ayuntamientos-de-la-provincia/ | B | pendiente | |
| Lleida/Lerida | http://www.diputaciolleida.cat/231-municipis/cercador-de-municipis/ | C | pendiente | |
| Lugo | https://deputacionlugo.gal/es/ayuntamientos/a-provincia | B | pendiente | |
| Madrid | https://www.comunidad.madrid/servicios/municipios/municipios-comunidad-madrid | B | hecho | 178/179, CSV manual (scripts/provincias/madrid.py). San Antonio de la Florida excluido, es un barrio de Madrid capital, no un municipio |
| Málaga | http://www.malaga.es/turismo/mapa/?tpl=3 | D | pendiente | Parece mapa turístico de la capital, no directorio provincial |
| Melilla | https://www.melilla.es/melillaPortal/index.jsp | E | — | Ciudad única |
| Murcia | https://www.regmurcia.com/servlet/s.Sl?METHOD=SELECCION_COMARCA&sit=c,372 | C | hecho | 45/45, CSV manual (scripts/provincias/murcia.py) |
| Navarra | http://www.navarra.es/home_es/Navarra/272+Municipios/ | B | pendiente | |
| Ourense/Orense | https://www.depourense.gal/es/concellos/directorio | B | pendiente | |
| Palencia | https://aytos.dip-palencia.es/lista-de-municipios/ | B | hecho | |
| Palmas, Las | https://cabildo.grancanaria.com/asociaciones-y-ayuntamientos | B | hecho | 34/34, CSV manual corregido y verificado (scripts/provincias/las_palmas.py) |
| Pontevedra | https://www.depo.gal/es/concellos | B | pendiente | |
| Rioja, La | http://www.larioja.org/npRioja/default/defaultpage.jsp?idtab=559068&id_str=6&id_ele=854&id_opt=0 | C | pendiente | |
| Salamanca | http://www.dipsanet.es/Aplicaciones/GestorInter.jsp?prestacion=Cipublico&funcion=MuestraMunicipios&codProvincia=37 | C | en_progreso | Recopilando CSV manual (como Burgos) |
| Santa Cruz de Tenerife | https://www.tenerife.es/municipios | B | hecho | 53/53, CSV manual (scripts/provincias/santacruzdetenerife.py) |
| Segovia | https://www.dipsegovia.es/la-provincia/municipios | B | hecho | |
| Sevilla | http://www.dipusevilla.es/municipios/ | B | pendiente | |
| Soria | http://www.dipsoria.com/index.php/mod.municipios/mem.listado/relcategoria.208/relmenu.135 | B | pendiente | |
| Tarragona | https://www.dipta.cat/municipi | B | pendiente | |
| Teruel | https://www.dpteruel.es/DPTweb/municipios/ | A | hecho | Parte del dataset conjunto de Aragón (Huesca+Zaragoza+Teruel): 578/731 en total. https://zenodo.org/records/17573972/files/municipios_Aragon.csv?download=1 |
| Toledo | https://www.diputoledo.es/global/11/50/169/dir_municipios | B | hecho | |
| València/Valencia | http://www.dival.es/es/content/entidades-locales | B | pendiente | |
| Valladolid | http://www.ayuntamientosdevalladolid.es/ | B | hecho | |
| Bizkaia/Vizcaya | http://www.bizkaia.net/home2/ca_index.asp | C | hecho | |
| Zamora | https://www.diputaciondezamora.es/opencms/provincia/nuestros-ayuntamientos/nuestros-ayuntamientos/ | B | pendiente | |
| Zaragoza | http://www.dpz.es/municipio | A | hecho | Parte del dataset conjunto de Aragón (Huesca+Zaragoza+Teruel): 578/731 en total. https://zenodo.org/records/17573972/files/municipios_Aragon.csv?download=1 |

## Cómo coger una provincia para trabajar
1. Elige una fila en estado `pendiente`.
2. Cámbiala a `en_progreso` en un commit (para que otra sesión no la coja a la vez).
3. Crea `scripts/provincias/<nombre_provincia>.py` con el scraper de esa fuente.
4. El script debe actualizar `url_ayuntamiento` en la tabla `municipios` de Supabase, cruzando por nombre (y provincia) o por `codigo_ine` si la fuente lo aporta.
5. Cuando funcione, cambia el estado a `hecho` y añade el nombre del fichero en la columna Notas.

## Casos frecuentes al cruzar nombres de municipios

- **Artículo al final con coma**: en la tabla `municipios`, los nombres que empiezan por artículo se guardan como "Resto, Artículo" (ej. "Altos, Los", "Palmas, Las"). Muchas fuentes externas usan la forma natural ("Los Altos", "Las Palmas"). Al cruzar nombres, comprobar ambas formas antes de dar un municipio por no encontrado — ver `scripts/provincias/las_palmas.py` para la función `mover_articulo_al_final` que resuelve esto en ambas direcciones.
- **Nombres bilingües con "/"**: comparar cada mitad del nombre por separado contra la tabla, no solo el texto completo.
- **Pedanías o entidades menores**: algunas fuentes incluyen núcleos de población que no son municipios independientes (ej. "Ballestar" en Castellón). Es correcto que queden sin emparejar.
- **Diferencias reales de nombre o grafía** (ej. variantes vascas con "tz"): no generalizar la lógica, resolver con una excepción manual en el script o directamente por SQL si es un caso aislado.
- **Verificar el nombre exacto de la provincia antes de escribir el script**: puede estar invertido (`Palmas, Las` en vez de `Las Palmas`) o con formato distinto al esperado. Comprobar con `select distinct provincia from municipios where provincia ilike '%...%'` antes de fijar el valor en el script.

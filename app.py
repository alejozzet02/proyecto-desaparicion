import os
import json
import re
import mimetypes
from pathlib import Path
from flask import Flask, jsonify, send_from_directory, send_file, request

app = Flask(__name__, static_folder='static')

RUTA_PROYECTO = Path(__file__).parent
RUTA_MATERIAL = RUTA_PROYECTO / 'material'
RUTA_CACHE = RUTA_PROYECTO / 'cache'

# ---------------------------------------------------------------------------
# Cargar datos IA (si existen)
# ---------------------------------------------------------------------------
MODULOS_IA = []
TIMELINE_IA = []
ESTADISTICAS_IA = {}

def _cargar_cache(nombre):
    ruta = RUTA_CACHE / nombre
    if ruta.exists():
        try:
            with open(ruta, encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    return None

_MOD_IA = _cargar_cache('modulos_ia.json')
if _MOD_IA:
    MODULOS_IA = _MOD_IA
_TL_IA = _cargar_cache('timeline_ia.json')
if _TL_IA:
    TIMELINE_IA = _TL_IA
_EST_IA = _cargar_cache('estadisticas.json')
if _EST_IA:
    ESTADISTICAS_IA = _EST_IA

# ---------------------------------------------------------------------------
# Metadatos de módulos
# ---------------------------------------------------------------------------
INFO_MODULOS = {
    'modulo1': {'titulo': 'Fundamentos teóricos', 'subtitulo': 'Genocidio, desaparición y memoria', 'descripcion': 'Bases conceptuales para entender la desaparición forzada como fenómeno histórico y político en América Latina.', 'epoca': 'Siglo XX - Teoría crítica'},
    'modulo2': {'titulo': 'Dictaduras y derechos humanos', 'subtitulo': 'El terrorismo de Estado en el Cono Sur', 'descripcion': 'Análisis de la desaparición forzada como herramienta de gobierno durante las dictaduras militares.', 'epoca': '1970-1990'},
    'modulo3': {'titulo': 'Concepto y experiencia', 'subtitulo': 'La desaparición como categoría', 'descripcion': 'Evolución del concepto de desaparición forzada en contextos contemporáneos como la migración.', 'epoca': '1980 - Actualidad'},
    'modulo4': {'titulo': 'Búsqueda y justicia', 'subtitulo': 'Obstáculos y caminos hacia la verdad', 'descripcion': 'Los desafíos de los familiares en la búsqueda de personas desaparecidas.', 'epoca': '1990 - Actualidad'},
    'modulo5': {'titulo': 'Antropología forense', 'subtitulo': 'Ciencia, verdad y memoria', 'descripcion': 'La antropología forense en la identificación de restos y la construcción de memoria.', 'epoca': '1990 - Actualidad'},
    'modulo 6': {'titulo': 'Colombia: el drama contemporáneo', 'subtitulo': 'Cuerpo, territorio y violencia', 'descripcion': 'La desaparición forzada en el conflicto colombiano.', 'epoca': '2000 - Actualidad'},
    'modulo7': {'titulo': 'Casos y jurisprudencia', 'subtitulo': 'Derecho internacional y luchas locales', 'descripcion': 'Casos emblemáticos y jurisprudencia en desaparición forzada.', 'epoca': '2000 - Actualidad'},
    'modulo8': {'titulo': 'Narrativas y testimonio', 'subtitulo': 'La palabra como resistencia', 'descripcion': 'Testimonio, imagen y narrativa como herramientas de denuncia y memoria.', 'epoca': '1980 - Actualidad'},
    'modulo9': {'titulo': 'Evidencia y búsqueda', 'subtitulo': 'Documentar para no olvidar', 'descripcion': 'Construcción de evidencia por víctimas y familiares.', 'epoca': '2000 - Actualidad'},
    'adicionales': {'titulo': 'Material complementario', 'subtitulo': 'Lecturas de apoyo transversal', 'descripcion': 'Documentos que proveen las bases conceptuales y contextuales para todos los módulos del diplomado. Su lectura es transversal al recorrido formativo.', 'epoca': 'Variada'}
}

# ---------------------------------------------------------------------------
# Línea de tiempo enriquecida con periodos históricos
# ---------------------------------------------------------------------------
LINEA_TIEMPO_BASE = [
    # PERIODO 1: Antecedentes
    {'id': 1, 'periodo': '1954-1970 — Semillas del autoritarismo', 'evento': 'Golpe de Estado en Paraguay (Stroessner)', 'descripcion': 'Inicio de la dictadura más longeva del Cono Sur, con 35 años de régimen de terror y desapariciones sistemáticas.', 'año': 1954, 'paises': ['Paraguay'], 'tipo': 'dictadura', 'icono': 'government'},
    {'id': 2, 'periodo': '1954-1970 — Semillas del autoritarismo', 'evento': 'Golpe militar en Brasil', 'descripcion': 'La dictadura brasileña (1964-1985) instaura la doctrina de seguridad nacional, dejando más de 400 desaparecidos.', 'año': 1964, 'paises': ['Brasil'], 'tipo': 'dictadura', 'icono': 'government'},
    {'id': 3, 'periodo': '1954-1970 — Semillas del autoritarismo', 'evento': 'Masacre de Tlatelolco', 'descripcion': 'El Estado mexicano reprime violentamente una manifestación estudiantil. Cientos de desaparecidos marcan el inicio de la "guerra sucia" en México.', 'año': 1968, 'paises': ['México'], 'tipo': 'conflicto', 'icono': 'warning'},
    # PERIODO 2: Dictaduras del Cono Sur
    {'id': 4, 'periodo': '1970-1980 — Dictaduras del Cono Sur', 'evento': 'Dictadura cívico-militar en Uruguay', 'descripcion': 'Entre 1973 y 1985, Uruguay sufre una dictadura que deja aproximadamente 200 desaparecidos y una sistemática violación de DDHH.', 'año': 1973, 'paises': ['Uruguay'], 'tipo': 'dictadura', 'icono': 'government'},
    {'id': 5, 'periodo': '1970-1980 — Dictaduras del Cono Sur', 'evento': 'Golpe de Estado en Chile', 'descripcion': 'Pinochet derroca a Allende. Se estiman 3.200 ejecutados y desaparecidos. La Caravana de la Muerte y el Estadio Nacional se convierten en símbolos del horror.', 'año': 1973, 'paises': ['Chile'], 'tipo': 'dictadura', 'icono': 'government'},
    {'id': 6, 'periodo': '1970-1980 — Dictaduras del Cono Sur', 'evento': 'Operación Cóndor', 'descripcion': 'Coordinación represiva entre dictaduras del Cono Sur (Argentina, Chile, Uruguay, Paraguay, Bolivia, Brasil) para perseguir y desaparecer opositores más allá de las fronteras nacionales.', 'año': 1975, 'paises': ['Argentina', 'Chile', 'Uruguay', 'Paraguay', 'Bolivia', 'Brasil'], 'tipo': 'dictadura', 'icono': 'government'},
    {'id': 7, 'periodo': '1970-1980 — Dictaduras del Cono Sur', 'evento': 'Golpe de Estado en Argentina', 'descripcion': 'Inicio de la última dictadura cívico-militar. 30.000 desaparecidos, vuelos de la muerte, apropiación de bebés. El terrorismo de Estado alcanza su máxima expresión.', 'año': 1976, 'paises': ['Argentina'], 'tipo': 'dictadura', 'icono': 'warning'},
    # PERIODO 3: Guerra sucia y conflictos internos
    {'id': 8, 'periodo': '1980-1995 — Conflictos armados y guerra sucia', 'evento': 'Conflicto armado interno en Perú', 'descripcion': 'Sendero Luminoso y el Estado peruano se enfrentan en una guerra que deja 69.000 víctimas, 20.000 desaparecidos. El Informe de la CVR documenta atrocidades de ambos bandos.', 'año': 1980, 'paises': ['Perú'], 'tipo': 'conflicto', 'icono': 'warning'},
    {'id': 9, 'periodo': '1980-1995 — Conflictos armados y guerra sucia', 'evento': 'Guerra civil en El Salvador', 'descripcion': '12 años de guerra civil dejan 75.000 muertos y 8.000 desaparecidos. Las masacres de El Mozote y los jesuitas de la UCA marcan la memoria del país.', 'año': 1980, 'paises': ['El Salvador'], 'tipo': 'conflicto', 'icono': 'warning'},
    {'id': 10, 'periodo': '1980-1995 — Conflictos armados y guerra sucia', 'evento': 'Conflicto armado en Guatemala', 'descripcion': 'Genocidio contra pueblos mayas. 200.000 víctimas, 45.000 desaparecidos. La Comisión de Esclarecimiento Histórico documenta que el 93% de las violaciones fueron cometidas por el Estado.', 'año': 1982, 'paises': ['Guatemala'], 'tipo': 'conflicto', 'icono': 'warning'},
    {'id': 11, 'periodo': '1980-1995 — Conflictos armados y guerra sucia', 'evento': 'Caída de las dictaduras y comisiones de verdad', 'descripcion': 'Argentina (CONADEP, 1983), Chile (Comisión Rettig, 1990) y Uruguay crean comisiones de verdad. Por primera vez, la sociedad conoce la magnitud de las desapariciones.', 'año': 1983, 'paises': ['Argentina', 'Chile', 'Uruguay'], 'tipo': 'legislacion', 'icono': 'scale'},
    # PERIODO 4: Colombia y la desaparición contemporánea
    {'id': 12, 'periodo': '1995-2010 — Colombia y la crisis contemporánea', 'evento': 'Masacre de Mapiripán (Colombia)', 'descripcion': 'Paramilitares y Fuerzas Armadas colombianas perpetran una masacre emblemática. 49 víctimas. Inicio de la arremetida paramilitar que multiplicó las desapariciones.', 'año': 1997, 'paises': ['Colombia'], 'tipo': 'conflicto', 'icono': 'warning'},
    {'id': 13, 'periodo': '1995-2010 — Colombia y la crisis contemporánea', 'evento': 'Plan Colombia', 'descripcion': 'Iniciativa de EE.UU. que militariza la lucha antinarcóticos. El conflicto se intensifica y las desapariciones forzadas se convierten en práctica sistemática en todo el territorio.', 'año': 2000, 'paises': ['Colombia', 'Estados Unidos'], 'tipo': 'conflicto', 'icono': 'warning'},
    {'id': 14, 'periodo': '1995-2010 — Colombia y la crisis contemporánea', 'evento': 'Ley de Justicia y Paz (Colombia)', 'descripcion': 'Primer marco legal que obliga a paramilitares a confesar crímenes. Surgen las primeras versiones libres que revelan fosas comunes y patrones de desaparición.', 'año': 2005, 'paises': ['Colombia'], 'tipo': 'legislacion', 'icono': 'scale'},
    {'id': 15, 'periodo': '1995-2010 — Colombia y la crisis contemporánea', 'evento': 'Guerra contra el narcotráfico en México', 'descripcion': 'Felipe Calderón declara la guerra al narco. Más de 100.000 desaparecidos y 350.000 homicidios. Las fosas clandestinas se multiplican por todo el país.', 'año': 2006, 'paises': ['México'], 'tipo': 'conflicto', 'icono': 'warning'},
    # PERIODO 5: Actualidad
    {'id': 16, 'periodo': '2010-2025 — Actualidad: búsqueda y resistencia', 'evento': 'Caso Ayotzinapa (México)', 'descripcion': '43 estudiantes normalistas desaparecidos en Iguala. El caso se convierte en símbolo internacional de la impunidad y la desaparición forzada en México. "Fue el Estado".', 'año': 2014, 'paises': ['México'], 'tipo': 'movimiento_social', 'icono': 'gavel'},
    {'id': 17, 'periodo': '2010-2025 — Actualidad: búsqueda y resistencia', 'evento': 'Acuerdo de Paz Colombia-FARC', 'descripcion': 'El acuerdo crea la Jurisdicción Especial para la Paz (JEP) y la Unidad de Búsqueda de Personas dadas por Desaparecidas. Por primera vez se prioriza la búsqueda humanitaria.', 'año': 2016, 'paises': ['Colombia'], 'tipo': 'legislacion', 'icono': 'scale'},
    {'id': 18, 'periodo': '2010-2025 — Actualidad: búsqueda y resistencia', 'evento': 'Estallido social y crisis humanitaria', 'descripcion': 'Chile, Colombia, Perú y Ecuador enfrentan crisis políticas y sociales. Las desapariciones en contextos de protesta suman nuevas víctimas a las ya existentes.', 'año': 2019, 'paises': ['Chile', 'Colombia', 'Perú', 'Ecuador'], 'tipo': 'movimiento_social', 'icono': 'gavel'},
    {'id': 19, 'periodo': '2010-2025 — Actualidad: búsqueda y resistencia', 'evento': 'Búsqueda humanitaria y madres buscadoras', 'descripcion': 'Colectivos de familias buscadoras en México, Colombia y Centroamérica demuestran que la sociedad civil asume la tarea que el Estado abandona. Cada hallazgo es un acto de resistencia.', 'año': 2023, 'paises': ['México', 'Colombia', 'Guatemala', 'El Salvador'], 'tipo': 'movimiento_social', 'icono': 'gavel'},
]

# ---------------------------------------------------------------------------
# Conexiones narrativas entre módulos
# ---------------------------------------------------------------------------
CONEXIONES_MODULOS = [
    {'de': 'modulo1', 'a': 'modulo2', 'narrativa': '¿Cómo las estructuras de genocidio analizadas en el módulo 1 se materializan en políticas de Estado durante las dictaduras? El módulo 2 responde explorando el terrorismo de Estado en el Cono Sur.'},
    {'de': 'modulo2', 'a': 'modulo3', 'narrativa': 'Las experiencias traumáticas de las dictaduras obligan a repensar el concepto mismo de desaparición. El módulo 3 traza esa evolución conceptual desde una perspectiva crítica.'},
    {'de': 'modulo3', 'a': 'modulo4', 'narrativa': 'Definir la desaparición no es un ejercicio teórico: tiene consecuencias jurídicas directas. El módulo 4 muestra cómo las familias enfrentan los obstáculos procesales para buscar justicia.'},
    {'de': 'modulo4', 'a': 'modulo5', 'narrativa': 'Cuando la justicia tradicional falla, la ciencia forense se convierte en herramienta de verdad. El módulo 5 explora cómo la antropología forense da nombre y rostro a los desaparecidos.'},
    {'de': 'modulo5', 'a': 'modulo 6', 'narrativa': 'La ciencia forense en Colombia enfrenta el desafío más grande del continente: miles de cuerpos, fosas comunes y un conflicto que se transforma constantemente.'},
    {'de': 'modulo 6', 'a': 'modulo7', 'narrativa': 'De los casos colombianos surgen precedentes jurídicos que transforman el derecho internacional. El módulo 7 analiza cómo estos casos construyen jurisprudencia.'},
    {'de': 'modulo7', 'a': 'modulo8', 'narrativa': 'Pero la ley no basta: las narrativas y testimonios mantienen viva la memoria. El módulo 8 muestra el poder de la palabra como resistencia contra el olvido.'},
    {'de': 'modulo8', 'a': 'modulo9', 'narrativa': 'Las narrativas se convierten en evidencia. El módulo 9 explora cómo las víctimas documentan su propia búsqueda cuando el Estado no lo hace.'},
]

# ---------------------------------------------------------------------------
# Estadísticas históricas impactantes (hardcodeadas)
# ---------------------------------------------------------------------------
DATOS_HISTORICOS = {
    'desaparecidos_por_pais': [
        {'pais': 'Argentina', 'cifra': 30000, 'periodo': '1976-1983', 'fuente': 'Organismos de DDHH', 'contexto': 'Dictadura cívico-militar. Vuelos de la muerte, apropiación de bebés.'},
        {'pais': 'Guatemala', 'cifra': 45000, 'periodo': '1960-1996', 'fuente': 'Comisión de Esclarecimiento Histórico', 'contexto': 'Conflicto armado interno. Genocidio contra pueblos mayas.'},
        {'pais': 'Colombia', 'cifra': 50000, 'periodo': '1990-2025', 'fuente': 'Unidad de Búsqueda de Personas Desaparecidas', 'contexto': 'Conflicto armado, paramilitarismo y narcotráfico.'},
        {'pais': 'México', 'cifra': 111000, 'periodo': '2006-2025', 'fuente': 'Registro Nacional de Personas Desaparecidas', 'contexto': 'Guerra contra el narcotráfico. Cifra actualizada a 2024.'},
        {'pais': 'Perú', 'cifra': 20000, 'periodo': '1980-2000', 'fuente': 'Comisión de la Verdad y Reconciliación', 'contexto': 'Conflicto armado interno (Sendero Luminoso + Estado).'},
        {'pais': 'Chile', 'cifra': 3200, 'periodo': '1973-1990', 'fuente': 'Comisión Nacional de Verdad y Reconciliación', 'contexto': 'Dictadura de Pinochet. Caravana de la Muerte.'},
        {'pais': 'El Salvador', 'cifra': 8000, 'periodo': '1980-1992', 'fuente': 'Comisión de la Verdad', 'contexto': 'Guerra civil. Masacres de la Fuerza Armada.'},
        {'pais': 'Brasil', 'cifra': 434, 'periodo': '1964-1985', 'fuente': 'Comisión Nacional de la Verdad', 'contexto': 'Dictadura militar.'},
    ],
    'tendencia_por_decada': [
        {'decada': '1960', 'eventos': 2, 'desaparecidos_estimados': 500, 'descripcion': 'Inicio de dictaduras y guerra sucia en México'},
        {'decada': '1970', 'eventos': 5, 'desaparecidos_estimados': 35000, 'descripcion': 'Dictaduras del Cono Sur. Operación Cóndor.'},
        {'decada': '1980', 'eventos': 4, 'desaparecidos_estimados': 20000, 'descripcion': 'Conflictos armados en Centroamérica y Perú.'},
        {'decada': '1990', 'eventos': 3, 'desaparecidos_estimados': 15000, 'descripcion': 'Paramilitarismo en Colombia. Comisiones de verdad.'},
        {'decada': '2000', 'eventos': 4, 'desaparecidos_estimados': 60000, 'descripcion': 'Plan Colombia. Guerra en México. Crisis humanitaria.'},
        {'decada': '2010', 'eventos': 4, 'desaparecidos_estimados': 80000, 'descripcion': 'Ayotzinapa. Búsqueda humanitaria. Crisis venezolana.'},
        {'decada': '2020', 'eventos': 3, 'desaparecidos_estimados': 50000, 'descripcion': 'Madres buscadoras. Nuevos gobiernos. Crisis migratoria.'},
    ],
    'datos_clave': [
        {'categoria': 'Total estimado de desaparecidos', 'valor': '+300,000', 'contexto': 'Suma de registros oficiales en 8 países de LATAM'},
        {'categoria': 'Fosas clandestinas (México)', 'valor': '+5,000', 'contexto': 'Descubiertas entre 2006 y 2024, muchas aún sin procesar'},
        {'categoria': 'Cuerpos sin identificar (Colombia)', 'valor': '+50,000', 'contexto': 'En el Servicio Médico Legal y fosas comunes'},
        {'categoria': 'Niños apropiados (Argentina)', 'valor': '500', 'contexto': 'Hijos de desaparecidos sustraídos durante la dictadura'},
        {'categoria': 'Años de impunidad promedio', 'valor': '25+', 'contexto': 'Tiempo que tardan los familiares en obtener respuestas'},
    ],
    'cifras_mundo': [
        {'pais': 'México', 'cifra': 111000},
        {'pais': 'Colombia', 'cifra': 50000},
        {'pais': 'Guatemala', 'cifra': 45000},
        {'pais': 'Argentina', 'cifra': 30000},
        {'pais': 'Perú', 'cifra': 20000},
        {'pais': 'El Salvador', 'cifra': 8000},
        {'pais': 'Chile', 'cifra': 3200},
        {'pais': 'Brasil', 'cifra': 434},
    ]
}

# ---------------------------------------------------------------------------
# Helper: obtener timeline
# ---------------------------------------------------------------------------
def obtener_timeline():
    if TIMELINE_IA:
        return [{
            'id': i + 1, 'evento': ev['evento'], 'descripcion': ev['descripcion'],
            'año': ev.get('año', ''), 'paises': ev.get('paises', []),
            'tipo': ev.get('tipo', ''), 'periodo': ev.get('periodo', ''), 'icono': ev.get('icono', 'book'),
            'modulos': []
        } for i, ev in enumerate(TIMELINE_IA)]
    return LINEA_TIEMPO_BASE


def obtener_conexiones():
    return CONEXIONES_MODULOS


def obtener_datos_historicos():
    return DATOS_HISTORICOS


# ---------------------------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------------------------
def limpiar_nombre_archivo(nombre):
    nombre = nombre.replace('.pdf', '').replace('.PDF', '')
    nombre = re.sub(r'^[\d\.\-\s]+', '', nombre)
    nombre = nombre.replace('_', ' ').replace('-', ' ')
    return re.sub(r'\s+', ' ', nombre).strip()


def _generar_conceptos_desde_titulos(documentos):
    palabras = {
        'genocidio', 'memoria', 'dictadura', 'derechos', 'testimonio', 'narrativa',
        'forense', 'violencia', 'justicia', 'busqueda', 'evidencia', 'cuerpo',
        'migrante', 'verdad', 'resistencia', 'politica', 'gobierno', 'familia',
        'victima', 'desaparecido', 'historia', 'concepto', 'experiencia', 'politizado',
        'crueldad', 'autopsia', 'cronica', 'jurisprudencia', 'invisibilizacion'
    }
    encontradas = set()
    for doc in documentos:
        t = doc['titulo'].lower()
        for p in palabras:
            if p in t:
                encontradas.add(p.capitalize())
    return list(encontradas)[:6]


def _generar_resumen_modulo(nombre_modulo, info, documentos):
    if info.get('descripcion') and info['descripcion'] != 'Módulo del diplomado sobre desaparición y búsqueda de personas.':
        return info['descripcion']
    paises = {'Chile', 'Argentina', 'Colombia', 'Mexico', 'Brasil', 'Peru', 'Uruguay', 'El Salvador', 'Guatemala'}
    paises_mod = set()
    temas = set()
    for doc in documentos:
        t = doc['titulo'].lower()
        for p in paises:
            if p.lower() in t:
                paises_mod.add(p)
        for palabra in ['genocidio', 'dictadura', 'busqueda', 'forense', 'testimonio', 'memoria', 'justicia', 'narrativa', 'evidencia', 'cuerpo', 'migrante', 'conflicto']:
            if palabra in t:
                temas.add(palabra)
    desc = info.get('subtitulo', '') or f"Módulo sobre {info['titulo'].lower()}"
    if paises_mod:
        desc += f" Aborda casos de {', '.join(sorted(paises_mod)[:3])}."
    if temas:
        desc += f" Temas: {', '.join(sorted(temas)[:4])}."
    desc += f" Incluye {len(documentos)} documento{'s' if len(documentos) != 1 else ''} académico{'s' if len(documentos) != 1 else ''}."
    return desc


def _generar_reflexion_modulo(titulo, documentos):
    conceptos = _generar_conceptos_desde_titulos(documentos)
    if conceptos:
        return f"El estudio de {titulo.lower()} —a través de temas como {', '.join(conceptos[:3]).lower()}— permite comprender las múltiples dimensiones de la desaparición forzada y las estrategias de resistencia y memoria que han surgido en la región."
    return f"La exploración de {titulo.lower()} invita a reflexionar sobre las dimensiones políticas, sociales y humanitarias de la desaparición forzada en América Latina."


def _generar_datos_numericos(documentos):
    datos = []
    grandes = [d for d in documentos if d['tamano_kb'] > 1000]
    pequenos = [d for d in documentos if d['tamano_kb'] < 300]
    if grandes:
        datos.append({"categoria": "Documentos extensos", "valor": str(len(grandes)), "contexto": "Más de 1 MB cada uno"})
    if pequenos:
        datos.append({"categoria": "Documentos breves", "valor": str(len(pequenos)), "contexto": "Menos de 300 KB cada uno"})
    datos.append({"categoria": "Total documentos", "valor": str(len(documentos)), "contexto": "En este módulo"})
    tam_total = sum(d['tamano_kb'] for d in documentos)
    datos.append({"categoria": "Peso total", "valor": f"{round(tam_total/1024, 1)} MB", "contexto": "Suma de todos los documentos"})
    return datos


# ---------------------------------------------------------------------------
# Escanear módulos
# ---------------------------------------------------------------------------
def escanear_modulos():
    modulos = []
    if not RUTA_MATERIAL.exists():
        return modulos
    ia_index = {m['id']: m for m in MODULOS_IA}
    for carpeta in sorted(RUTA_MATERIAL.iterdir()):
        if not carpeta.is_dir():
            continue
        nombre_modulo = carpeta.name
        info = INFO_MODULOS.get(nombre_modulo, {'titulo': limpiar_nombre_archivo(nombre_modulo), 'subtitulo': '', 'descripcion': 'Módulo del diplomado sobre desaparición y búsqueda de personas.', 'epoca': ''})
        ia_data = ia_index.get(nombre_modulo, {})
        documentos = []
        for archivo in sorted(carpeta.iterdir()):
            if archivo.suffix.lower() == '.pdf':
                documentos.append({
                    'id': archivo.stem, 'nombre': archivo.name,
                    'titulo': limpiar_nombre_archivo(archivo.name),
                    'ruta_relativa': str(archivo.relative_to(RUTA_MATERIAL)),
                    'tamano_bytes': archivo.stat().st_size,
                    'tamano_kb': round(archivo.stat().st_size / 1024, 1)
                })
        es_comp = nombre_modulo == 'adicionales'
        modulos.append({
            'id': nombre_modulo, 'nombre': nombre_modulo,
            'titulo': ia_data.get('titulo') or info['titulo'],
            'subtitulo': ia_data.get('subtitulo') or info['subtitulo'],
            'descripcion': ia_data.get('descripcion') or _generar_resumen_modulo(nombre_modulo, info, documentos),
            'epoca': info['epoca'],
            'es_complementario': es_comp,
            'conceptos_clave': ia_data.get('conceptos_clave', []) or _generar_conceptos_desde_titulos(documentos),
            'reflexion': ia_data.get('reflexion', '') or _generar_reflexion_modulo(ia_data.get('titulo') or info['titulo'], documentos),
            'hechos_historicos': ia_data.get('hechos_historicos', []),
            'datos_numericos': ia_data.get('datos_numericos', []) or _generar_datos_numericos(documentos),
            'documentos': documentos, 'total_docs': len(documentos)
        })
    return modulos


# ---------------------------------------------------------------------------
# Rutas API
# ---------------------------------------------------------------------------
@app.route('/')
def servir_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/modulos')
def api_modulos():
    try:
        modulos = escanear_modulos()
        tiene_ia = bool(MODULOS_IA)
        principales = [m for m in modulos if not m.get('es_complementario')]
        return jsonify({
            'total_modulos': len(principales),
            'total_documentos': sum(m['total_docs'] for m in modulos),
            'modulos': modulos,
            'ia_enhanced': tiene_ia
        })
    except Exception as e:
        return jsonify({'error': f'Error al leer módulos: {str(e)}'}), 500

@app.route('/api/modulo/<path:modulo_id>')
def api_modulo(modulo_id):
    try:
        modulos = escanear_modulos()
        mapa = {m['id']: m for m in modulos}
        modulo = mapa.get(modulo_id)
        if not modulo:
            return jsonify({'error': 'Módulo no encontrado'}), 404
        return jsonify(modulo)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/timeline')
def api_timeline():
    try:
        return jsonify(obtener_timeline())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/conexiones')
def api_conexiones():
    try:
        modulos = escanear_modulos()
        mapa = {m['id']: m for m in modulos}
        conexiones = []
        for c in obtener_conexiones():
            mod_de = mapa.get(c['de'], {})
            mod_a = mapa.get(c['a'], {})
            conexiones.append({
                'de': c['de'], 'de_titulo': mod_de.get('titulo', c['de']),
                'a': c['a'], 'a_titulo': mod_a.get('titulo', c['a']),
                'narrativa': c['narrativa']
            })
        return jsonify(conexiones)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def docs_por_modulo():
    modulos = escanear_modulos()
    result = []
    for m in modulos:
        if m.get('es_complementario'):
            continue
        result.append({'modulo': m['titulo'], 'cantidad': m['total_docs']})
    return result

@app.route('/api/estadisticas')
def api_estadisticas():
    try:
        if ESTADISTICAS_IA:
            base = dict(ESTADISTICAS_IA)
            base['datos_historicos'] = DATOS_HISTORICOS
            base['fuente'] = 'ia'
            return jsonify(base)
        return jsonify({'fuente': 'filesystem', 'datos_historicos': DATOS_HISTORICOS, 'docs_por_modulo': docs_por_modulo()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/documento/<path:ruta_relativa>')
def api_documento(ruta_relativa):
    try:
        ruta_pdf = (RUTA_MATERIAL / ruta_relativa).resolve()
        if str(RUTA_MATERIAL.resolve()) not in str(ruta_pdf.parent):
            return jsonify({'error': 'Acceso denegado'}), 403
        if not ruta_pdf.exists():
            return jsonify({'error': 'Documento no encontrado'}), 404
        if ruta_pdf.suffix.lower() != '.pdf':
            return jsonify({'error': 'El archivo no es un PDF'}), 400
        import fitz
        doc = fitz.open(str(ruta_pdf))
        texto = "".join(pagina.get_text() for pagina in doc)
        doc.close()
        return jsonify({'ruta': ruta_relativa, 'texto': texto[:100000], 'texto_completo': len(texto) > 100000, 'tamano_caracteres': len(texto)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/pdf/<path:ruta_relativa>')
def api_servir_pdf(ruta_relativa):
    try:
        ruta_pdf = (RUTA_MATERIAL / ruta_relativa).resolve()
        if str(RUTA_MATERIAL.resolve()) not in str(ruta_pdf.parent):
            return jsonify({'error': 'Acceso denegado'}), 403
        if not ruta_pdf.exists():
            return jsonify({'error': 'PDF no encontrado'}), 404
        mime, _ = mimetypes.guess_type(str(ruta_pdf))
        return send_file(str(ruta_pdf), mimetype=mime or 'application/pdf')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/buscar')
def api_buscar():
    try:
        q = request.args.get('q', '').lower().strip()
        if not q:
            return jsonify({'resultados': []})
        resultados = []
        for m in escanear_modulos():
            for d in m['documentos']:
                if q in d['titulo'].lower() or q in d['nombre'].lower():
                    resultados.append({**d, 'modulo_id': m['id'], 'modulo_titulo': m['titulo']})
        return jsonify({'resultados': resultados, 'total': len(resultados)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/status')
def api_status():
    return jsonify({
        'modulos_ia': len(MODULOS_IA) > 0,
        'timeline_ia': len(TIMELINE_IA) > 0,
        'estadisticas_ia': bool(ESTADISTICAS_IA),
        'modulos_cache': [m['id'] for m in MODULOS_IA] if MODULOS_IA else [],
        'total_pdfs': sum(1 for _ in RUTA_MATERIAL.rglob('*.pdf')) if RUTA_MATERIAL.exists() else 0
    })


if __name__ == '__main__':
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug, host='0.0.0.0', port=5000, use_reloader=False)

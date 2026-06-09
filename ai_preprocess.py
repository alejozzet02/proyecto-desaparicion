"""
ai_preprocess.py — Preprocesamiento con IA (OpenAI / Gemini)

Ejecuta UNA VEZ antes de iniciar el servidor:
    python3 ai_preprocess.py

Lee los PDFs, llama a la IA configurada en .env, y genera cache/
con descripciones enriquecidas, línea de tiempo histórica y estadísticas.
"""

import os
import json
import re
import sys
from pathlib import Path

RUTA_PROYECTO = Path(__file__).parent
RUTA_MATERIAL = RUTA_PROYECTO / 'material'
RUTA_CACHE = RUTA_PROYECTO / 'cache'
RUTA_ENV = RUTA_PROYECTO / '.env'

# ---------------------------------------------------------------------------
# Cargar configuración desde .env
# ---------------------------------------------------------------------------
def cargar_config():
    if RUTA_ENV.exists():
        with open(RUTA_ENV) as f:
            for linea in f:
                linea = linea.strip()
                if linea and not linea.startswith('#'):
                    partes = linea.split('=', 1)
                    if len(partes) == 2:
                        os.environ.setdefault(partes[0].strip(), partes[1].strip())

    proveedor = os.environ.get('IA_PROVIDER', '').lower().strip()

    if proveedor == 'gemini':
        api_key = os.environ.get('GEMINI_API_KEY', '')
        modelo = os.environ.get('GEMINI_MODEL', 'gemini-2.0-flash')
    elif proveedor == 'openai':
        api_key = os.environ.get('OPENAI_API_KEY', '')
        modelo = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')
    else:
        # Detección automática por variable presente
        if os.environ.get('OPENAI_API_KEY', ''):
            proveedor = 'openai'
            api_key = os.environ.get('OPENAI_API_KEY', '')
            modelo = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')
        elif os.environ.get('GEMINI_API_KEY', ''):
            proveedor = 'gemini'
            api_key = os.environ.get('GEMINI_API_KEY', '')
            modelo = os.environ.get('GEMINI_MODEL', 'gemini-2.0-flash')
        else:
            print("""
⚠️  No se encontró configuración de IA.

Copia .env.example como .env y configura tu proveedor:
    cp .env.example .env

Para Gemini (gratuito):
    IA_PROVIDER=gemini
    GEMINI_API_KEY=tu-api-key-de-google-ai-studio

Para OpenAI:
    IA_PROVIDER=openai
    OPENAI_API_KEY=sk-tu-api-key
""")
            sys.exit(1)

    if not api_key:
        print(f"✗ No se encontró API key para {proveedor}. Revisa tu .env")
        sys.exit(1)

    return proveedor, api_key, modelo


# ---------------------------------------------------------------------------
# Llamada a la IA según proveedor
# ---------------------------------------------------------------------------
def llamar_ia(proveedor, api_key, modelo, system_prompt, prompt, formato_json=True, max_reintentos=3):
    """
    Envía un prompt a la IA con reintentos automáticos si falla por cuota.
    Soporta: gemini, openai
    """
    import time
    ultimo_error = None
    for intento in range(1, max_reintentos + 1):
        try:
            if proveedor == 'gemini':
                return _llamar_gemini(api_key, modelo, system_prompt, prompt, formato_json)
            else:
                return _llamar_openai(api_key, modelo, system_prompt, prompt, formato_json)
        except Exception as e:
            mensaje = str(e).lower()
            ultimo_error = e
            # Reintentar si es error de cuota (429) o límite de tasa
            if '429' in mensaje or 'quota' in mensaje or 'resource_exhausted' in mensaje or 'rate_limit' in mensaje:
                espera = int(intento * 15)
                print(f"  ⏳ Cuota excedida, reintentando en {espera}s (intento {intento}/{max_reintentos})...", end=' ', flush=True)
                time.sleep(espera)
            else:
                # Error diferente, no reintentar
                print(f"  ⚠️  Error en llamada a {proveedor}: {e}")
                return None
    print(f"  ✗ Falló tras {max_reintentos} reintentos: {ultimo_error}")
    return None


def _llamar_gemini(api_key, modelo, system_prompt, prompt, formato_json):
    from google import genai
    client = genai.Client(api_key=api_key)

    config = {
        "temperature": 0.3,
        "max_output_tokens": 4096,
        "system_instruction": system_prompt,
    }
    if formato_json:
        config["response_mime_type"] = "application/json"

    respuesta = client.models.generate_content(
        model=modelo,
        contents=prompt,
        config=config,
    )
    return respuesta.text


def _llamar_openai(api_key, modelo, system_prompt, prompt, formato_json):
    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    kwargs = {
        "model": modelo,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
    }
    if formato_json:
        kwargs["response_format"] = {"type": "json_object"}

    respuesta = client.chat.completions.create(**kwargs)
    return respuesta.choices[0].message.content


# ---------------------------------------------------------------------------
# Extraer texto de PDFs
# ---------------------------------------------------------------------------
def extraer_texto_pdf(ruta_pdf, max_chars=3000):
    import fitz
    try:
        doc = fitz.open(ruta_pdf)
        texto = ""
        for pagina in doc:
            texto += pagina.get_text()
            if len(texto) >= max_chars:
                break
        doc.close()
        return texto.strip()[:max_chars] or "[PDF sin texto extraíble]"
    except Exception as e:
        return f"[Error al leer PDF: {str(e)}]"


def limpiar_nombre_archivo(nombre):
    nombre = nombre.replace('.pdf', '').replace('.PDF', '')
    nombre = re.sub(r'^[\d\.\-\s]+', '', nombre)
    nombre = nombre.replace('_', ' ').replace('-', ' ')
    return re.sub(r'\s+', ' ', nombre).strip()


# ---------------------------------------------------------------------------
# Metadatos de módulos
# ---------------------------------------------------------------------------
INFO_MODULOS = {
    'modulo1': {'titulo': 'Fundamentos teóricos', 'subtitulo': 'Genocidio, desaparición y memoria'},
    'modulo2': {'titulo': 'Dictaduras y derechos humanos', 'subtitulo': 'El terrorismo de Estado en el Cono Sur'},
    'modulo3': {'titulo': 'Concepto y experiencia', 'subtitulo': 'La desaparición como categoría'},
    'modulo4': {'titulo': 'Búsqueda y justicia', 'subtitulo': 'Obstáculos y caminos hacia la verdad'},
    'modulo5': {'titulo': 'Antropología forense', 'subtitulo': 'Ciencia, verdad y memoria'},
    'modulo 6': {'titulo': 'Colombia: el drama contemporáneo', 'subtitulo': 'Cuerpo, territorio y violencia'},
    'modulo7': {'titulo': 'Casos y jurisprudencia', 'subtitulo': 'Derecho internacional y luchas locales'},
    'modulo8': {'titulo': 'Narrativas y testimonio', 'subtitulo': 'La palabra como resistencia'},
    'modulo9': {'titulo': 'Evidencia y búsqueda', 'subtitulo': 'Documentar para no olvidar'},
    'adicionales': {'titulo': 'Material complementario', 'subtitulo': 'Lecturas adicionales y recursos de apoyo'},
}


def escanear_modulos():
    modulos = []
    if not RUTA_MATERIAL.exists():
        return modulos

    for carpeta in sorted(RUTA_MATERIAL.iterdir()):
        if not carpeta.is_dir():
            continue
        nombre_modulo = carpeta.name
        info = INFO_MODULOS.get(nombre_modulo, {
            'titulo': limpiar_nombre_archivo(nombre_modulo),
            'subtitulo': ''
        })
        documentos = []
        textos = []
        for archivo in sorted(carpeta.iterdir()):
            if archivo.suffix.lower() == '.pdf':
                texto = extraer_texto_pdf(str(archivo))
                titulo = limpiar_nombre_archivo(archivo.name)
                documentos.append({
                    'nombre': archivo.name,
                    'titulo': titulo,
                    'tamano_bytes': archivo.stat().st_size,
                })
                textos.append(f"--- Documento: {titulo} ---\n{texto}")
        if documentos:
            modulos.append({
                'id': nombre_modulo,
                'titulo': info['titulo'],
                'subtitulo': info['subtitulo'],
                'total_docs': len(documentos),
                'documentos': documentos,
                'texto_completo': '\n\n'.join(textos)
            })
    return modulos


def fallback_modulo(mod):
    return {
        'id': mod['id'],
        'titulo': mod['titulo'],
        'subtitulo': mod['subtitulo'],
        'total_docs': mod['total_docs'],
        'documentos': mod['documentos'],
        'descripcion': f"Módulo sobre {mod['titulo'].lower()} en el contexto de la desaparición forzada.",
        'conceptos_clave': [],
        'reflexion': '',
        'hechos_historicos': [],
        'datos_numericos': []
    }


# ---------------------------------------------------------------------------
# 1. Descripciones de cada módulo
# ---------------------------------------------------------------------------
def generar_descripciones_modulos(proveedor, api_key, modelo, modulos):
    print("\n=== 1. Enriqueciendo descripciones de módulos con IA ===\n")

    system_prompt = (
        "Eres un analista académico especializado en derechos humanos y desaparición forzada en América Latina. "
        "Responde SIEMPRE en formato JSON válido, sin markdown, sin explicaciones adicionales."
    )

    resultados = []
    for mod in modulos:
        print(f"  Procesando: {mod['titulo']} ({mod['total_docs']} docs)...", end=' ', flush=True)

        prompt = f"""Analiza los siguientes textos académicos sobre "{mod['titulo']}" ({mod['subtitulo']}).

Devuelve un JSON con esta estructura exacta:
{{
    "descripcion": "Resumen del módulo en 2-3 oraciones para público general",
    "conceptos_clave": ["Concepto 1: breve explicación", "Concepto 2: breve explicación"],
    "reflexion": "Reflexión final sobre la importancia de este tema (1-2 oraciones)",
    "hechos_historicos": [
        {{"año": "aaaa", "evento": "descripción breve", "paises": ["país1", "país2"]}}
    ],
    "datos_numericos": [
        {{"categoria": "ej: Víctimas", "valor": "cifra o dato", "contexto": "breve explicación"}}
    ]
}}

Textos del módulo:
{mod['texto_completo']}"""

        respuesta = llamar_ia(proveedor, api_key, modelo, system_prompt, prompt)
        if respuesta:
            try:
                datos = json.loads(respuesta)
                resultados.append({
                    'id': mod['id'],
                    'titulo': mod['titulo'],
                    'subtitulo': mod['subtitulo'],
                    'total_docs': mod['total_docs'],
                    'documentos': mod['documentos'],
                    **datos
                })
                print("✓")
            except json.JSONDecodeError:
                print("✗ (error parsing JSON)")
                resultados.append(fallback_modulo(mod))
        else:
            print("✗")
            resultados.append(fallback_modulo(mod))
    return resultados


# ---------------------------------------------------------------------------
# 2. Línea de tiempo histórica
# ---------------------------------------------------------------------------
def generar_timeline_ia(proveedor, api_key, modelo, modulos):
    print("\n=== 2. Generando línea de tiempo histórica con IA ===\n")

    texto_global = ""
    for mod in modulos:
        texto_global += f"\n=== {mod['titulo']} ===\n{mod['texto_completo'][:1500]}\n"

    print(f"  Texto total: ~{len(texto_global)} caracteres...", flush=True)

    system_prompt = (
        "Eres un historiador especializado en derechos humanos y desaparición forzada en América Latina. "
        "Responde SIEMPRE en formato JSON válido, sin markdown."
    )

    prompt = f"""Basado en estos textos académicos, genera una línea de tiempo de eventos históricos clave sobre la desaparición forzada en América Latina.

Devuelve un JSON con esta estructura exacta:
{{
    "eventos": [
        {{
            "año": 1976,
            "evento": "Nombre del evento",
            "descripcion": "Descripción breve en 1-2 oraciones",
            "paises": ["País1", "País2"],
            "tipo": "dictadura | conflicto | legislación | movimiento_social | forensic | testimonio"
        }}
    ]
}}

Incluye eventos desde 1950 hasta la actualidad. Máximo 25 eventos. Prioriza eventos reales y verificables.

Textos de referencia:
{texto_global[:25000]}"""

    respuesta = llamar_ia(proveedor, api_key, modelo, system_prompt, prompt)
    eventos = []
    if respuesta:
        try:
            datos = json.loads(respuesta)
            eventos = datos.get('eventos', [])
            print(f"  ✓ {len(eventos)} eventos generados")
        except json.JSONDecodeError:
            print("  ✗ Error al parsear JSON")
    else:
        print("  ✗ No se recibió respuesta")
    return eventos


# ---------------------------------------------------------------------------
# 3. Estadísticas para gráficas
# ---------------------------------------------------------------------------
def generar_estadisticas(proveedor, api_key, modelo, modulos):
    print("\n=== 3. Generando estadísticas y datos para gráficas ===\n")

    texto_global = ""
    for mod in modulos:
        texto_global += f"\n=== {mod['titulo']} ===\n{mod['texto_completo'][:1200]}\n"

    system_prompt = (
        "Eres un analista de datos especializado en derechos humanos. "
        "Responde SIEMPRE en formato JSON válido, sin markdown."
    )

    prompt = f"""Basado en estos textos sobre desaparición forzada, extrae datos estadísticos.

Devuelve un JSON con esta estructura exacta:
{{
    "paises_mencionados": [
        {{"pais": "Argentina", "frecuencia": 15, "contexto": "Dictadura 1976-1983"}}
    ],
    "victimas_estimadas": [
        {{"pais": "Argentina", "cifra": "30.000", "fuente": "organismos de DDHH", "periodo": "1976-1983"}}
    ],
    "periodos_historicos": [
        {{"nombre": "Dictaduras del Cono Sur", "inicio": 1964, "fin": 1990, "descripcion": "..."}}
    ],
    "temas_principales": [
        {{"tema": "Memoria", "relevancia": 0.85, "modulos": ["modulo1", "modulo8"]}}
    ],
    "distribucion_temporal": [
        {{"decada": "1970s", "eventos": 8, "descripcion": "contexto"}}
    ]
}}

Usa datos reales mencionados en los textos. Si no hay datos exactos, omite esa sección.

Textos de referencia:
{texto_global[:20000]}"""

    respuesta = llamar_ia(proveedor, api_key, modelo, system_prompt, prompt)
    if respuesta:
        try:
            datos = json.loads(respuesta)
            paises = len(datos.get('paises_mencionados', []))
            cifras = len(datos.get('victimas_estimadas', []))
            periodos = len(datos.get('periodos_historicos', []))
            print(f"  ✓ {paises} países, {cifras} cifras, {periodos} periodos")
            return datos
        except json.JSONDecodeError:
            print("  ✗ Error al parsear JSON")
    else:
        print("  ✗ No se recibió respuesta")
    return {}


def guardar_cache(nombre, datos):
    RUTA_CACHE.mkdir(exist_ok=True)
    ruta = RUTA_CACHE / nombre
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    print(f"  💾 Guardado: cache/{nombre}")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    print("╔══════════════════════════════════════════════════════╗")
    print("║  Preprocesamiento con IA para Dashboard Narrativo   ║")
    print("║  Desaparición y Búsqueda de Personas en LATAM       ║")
    print("╚══════════════════════════════════════════════════════╝")

    proveedor, api_key, modelo = cargar_config()
    print(f"\n🤖 Proveedor: {proveedor.upper()} | Modelo: {modelo}")

    modulos = escanear_modulos()
    if not modulos:
        print("✗ No se encontraron módulos con PDFs en material/")
        sys.exit(1)

    total_docs = sum(m['total_docs'] for m in modulos)
    print(f"📚 {len(modulos)} módulos, {total_docs} PDFs encontrados\n")

    # 1. Descripciones enriquecidas
    modulos_ia = generar_descripciones_modulos(proveedor, api_key, modelo, modulos)
    guardar_cache('modulos_ia.json', modulos_ia)

    # 2. Línea de tiempo
    eventos = generar_timeline_ia(proveedor, api_key, modelo, modulos)
    guardar_cache('timeline_ia.json', eventos)

    # 3. Estadísticas
    estadisticas = generar_estadisticas(proveedor, api_key, modelo, modulos)
    guardar_cache('estadisticas.json', estadisticas)

    print(f"""
╔══════════════════════════════════════════════════════╗
║  ✅  Preprocesamiento completado                    ║
║  Archivos en cache/:                                ║
║    • modulos_ia.json  — {len(modulos_ia)} módulos
║    • timeline_ia.json — {len(eventos)} eventos
║    • estadisticas.json — datos para gráficas        ║
║                                                     ║
║  Ahora ejecuta:  python3 app.py                     ║
╚══════════════════════════════════════════════════════╝
""")


if __name__ == '__main__':
    main()

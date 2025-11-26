# =============================================================================
# AnalyzeChapter/__init__.py - DEPLOY 3.0
# =============================================================================
# CAMBIOS:
#   - Safety settings: formato diccionario (correcto para google-generativeai)
#   - Modelo: models/gemini-2.5-flash (confirmado disponible)
# =============================================================================

import logging
import json
import os
import re
import time as time_module
import google.generativeai as genai
from google.api_core import exceptions
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logging.getLogger('tenacity').setLevel(logging.WARNING)

# --- 1. MÉTRICAS (simplificadas - quitamos redundancias) ---
ANALYZE_CHAPTER_METRICS = """
MÉTRICAS A EXTRAER:

1. ESTRUCTURA: total_palabras, total_oraciones, total_parrafos
2. COMPOSICIÓN: lineas_dialogo, porcentaje_dialogo, escenas_accion, escenas_reflexion
3. RITMO: eventos_por_mil_palabras, clasificacion (RAPIDO|MEDIO|LENTO)
4. TIEMPO: referencias_explicitas, transcurrido_estimado
5. CALIDAD: instancias_tell_no_show, repeticiones_detectadas
"""

# --- 2. PROMPT (sin duplicación de estructura JSON) ---
ANALYZE_CHAPTER_PROMPT_TEMPLATE = """
Actúa como Analista Literario Forense. Extrae datos OBJETIVOS y MEDIBLES.

CONTEXTO:
- Título: {{CHAPTER_TITLE}}
- Título Original: {{PARENT_CHAPTER}}
- Tipo: {{SECTION_TYPE}}
- ID: {{CHAPTER_ID}}
- Es fragmento: {{IS_FRAGMENT}}

TEXTO:
{{CHAPTER_CONTENT}}

INSTRUCCIONES:
{{METRICS_INSTRUCTIONS}}

Extrae también:
- Personajes que aparecen (nombre, rol, estado emocional, acciones clave)
- Eventos en orden (descripción breve, tipo, nivel de tensión 1-10)
- Lugar, tiempo narrativo, atmósfera, conflicto presente, gancho final
- Problemas potenciales y fortalezas del capítulo

RESPONDE SOLO JSON (sin markdown):
{
  "chapter_id": "{{CHAPTER_ID}}",
  "titulo_capitulo": "{{PARENT_CHAPTER}}",
  "reparto_local": [{"nombre": "", "rol_en_capitulo": "", "estado_emocional": "", "acciones_clave": [], "dialogos_count": 0}],
  "eventos": [{"evento": "", "tipo": "", "tension": 0}],
  "metricas": {
    "estructura": {"total_palabras": 0, "total_oraciones": 0, "total_parrafos": 0},
    "composicion": {"lineas_dialogo": 0, "porcentaje_dialogo": 0, "escenas_accion": 0, "escenas_reflexion": 0},
    "ritmo": {"eventos_por_mil_palabras": 0, "clasificacion": "MEDIO"},
    "tiempo": {"referencias_explicitas": [], "transcurrido_estimado": ""}
  },
  "elementos_narrativos": {"lugar": "", "tiempo_narrativo": "", "atmosfera": "", "conflicto_presente": false, "gancho_final": false},
  "señales_edicion": {"instancias_tell_no_show": [], "repeticiones": [], "fortalezas": [], "problemas_potenciales": []}
}
"""

# --- 3. REINTENTOS ---
retry_strategy = retry(
    retry=retry_if_exception_type((
        exceptions.ResourceExhausted, 
        exceptions.ServiceUnavailable, 
        exceptions.DeadlineExceeded
    )),
    wait=wait_exponential(multiplier=1.5, min=2, max=30),
    stop=stop_after_attempt(5),
    reraise=True
)

@retry_strategy
def call_gemini_with_retry(model, prompt):
    """Llamada con reintentos y safety settings CORREGIDOS"""
    return model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.2,
            "max_output_tokens": 8192,
            "response_mime_type": "application/json"
        },
        request_options={'timeout': 90},
        # ✅ FORMATO CORRECTO: diccionario
        safety_settings={
            "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
        }
    )


def main(chapter_json) -> dict:
    """Analiza un capítulo con Gemini 2.5 Flash"""
    chapter_id = "Desconocido"
    display_title = "Sin título"
    parent_context_title = "Sin título"
    
    try:
        # A. Parseo de entrada
        if isinstance(chapter_json, str):
            try:
                chapter = json.loads(chapter_json)
            except json.JSONDecodeError:
                chapter = {"id": 0, "title": "Error Decode", "content": ""}
        else:
            chapter = chapter_json

        # B. Extraer campos
        chapter_id = str(chapter.get('id', 0))
        is_fragment = str(chapter.get('is_fragment', False))
        display_title = chapter.get('title', 'Sin título')
        parent_context_title = chapter.get('original_title') or display_title
        section_type = chapter.get('section_type', 'CHAPTER')
        content = chapter.get('content', '')
        content_clean = re.sub(r'\n+', '\n', content)

        # C. Configurar Gemini
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return {"error": "No API Key", "chapter_id": chapter_id}

        genai.configure(api_key=api_key)
        
        # ✅ MODELO CONFIRMADO DISPONIBLE
        model = genai.GenerativeModel('models/gemini-2.5-flash')

        # D. Construir prompt
        prompt = ANALYZE_CHAPTER_PROMPT_TEMPLATE.replace("{{CHAPTER_TITLE}}", display_title)
        prompt = prompt.replace("{{PARENT_CHAPTER}}", parent_context_title)
        prompt = prompt.replace("{{SECTION_TYPE}}", section_type)
        prompt = prompt.replace("{{CHAPTER_ID}}", chapter_id)
        prompt = prompt.replace("{{IS_FRAGMENT}}", is_fragment)
        prompt = prompt.replace("{{METRICS_INSTRUCTIONS}}", ANALYZE_CHAPTER_METRICS)
        prompt = prompt.replace("{{CHAPTER_CONTENT}}", content_clean)
        
        # E. Llamar a Gemini
        start_gemini = time_module.time()
        logging.info(f"🚀 Analizando {parent_context_title} (ID: {chapter_id})...")
        
        response = call_gemini_with_retry(model, prompt)
        
        gemini_elapsed = time_module.time() - start_gemini
        logging.info(f"⏱️ Análisis completado en {gemini_elapsed:.2f}s")
        
        if not response.candidates:
            raise ValueError("Respuesta vacía o bloqueada")

        analysis = json.loads(response.text)
        
        # F. Metadata
        analysis['chapter_id'] = chapter_id
        analysis['titulo_real'] = parent_context_title
        analysis['section_type'] = section_type
        analysis['_metadata'] = {
            'status': 'success', 
            'model': 'gemini-2.5-flash',
            'processing_time_seconds': round(gemini_elapsed, 2)
        }
        
        return analysis

    except Exception as e:
        error_msg = str(e)
        logging.error(f"💥 Error en ID {chapter_id}: {error_msg}")
        
        status = "fatal_error"
        if "429" in error_msg or "ResourceExhausted" in error_msg:
            status = "rate_limit_exhausted"
        
        return {
            "chapter_id": chapter_id, 
            "titulo_real": parent_context_title,
            "error": error_msg, 
            "status": status,
            "reparto_local": [],
            "analisis_narrativo": {"resumen_denso": "FALLO DE ANÁLISIS"}
        }
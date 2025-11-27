# =============================================================================
# AnalyzeChapter/__init__.py - SYLPHRENA 4.0
# =============================================================================
# CAMBIOS DESDE 3.1:
#   - Recibe y procesa metadatos jerárquicos completos
#   - Prompt contextualizado según posición del fragmento
#   - Advertencias específicas para fragmentos intermedios/finales
#   - Métricas expandidas para análisis de Capa 2 y 3
# =============================================================================

import logging
import json
import os
import re
import time as time_module
import google.generativeai as genai
from google.api_core import exceptions
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logging.basicConfig(level=logging.INFO)
logging.getLogger('tenacity').setLevel(logging.WARNING)

# =============================================================================
# PROMPT DE ANÁLISIS CONTEXTUALIZADO (CAPA 1)
# =============================================================================

ANALYZE_CHAPTER_PROMPT_TEMPLATE = """
Actúa como un Analista Literario Forense. Tu trabajo es extraer datos OBJETIVOS y MEDIBLES de este fragmento de texto.

═══════════════════════════════════════════════════════════════════════════════
CONTEXTO ESTRUCTURAL JERÁRQUICO
═══════════════════════════════════════════════════════════════════════════════
- ID del Fragmento: {{FRAGMENT_ID}}
- Capítulo Padre: {{PARENT_CHAPTER}} (ID: {{PARENT_CHAPTER_ID}})
- Posición: Fragmento {{FRAGMENT_INDEX}} de {{TOTAL_FRAGMENTS}}
- Tipo de Sección: {{SECTION_TYPE}}
- Es primer fragmento del capítulo: {{IS_FIRST}}
- Es último fragmento del capítulo: {{IS_LAST}}

{{CONTEXT_WARNING}}

═══════════════════════════════════════════════════════════════════════════════
TEXTO A ANALIZAR
═══════════════════════════════════════════════════════════════════════════════

{{CHAPTER_CONTENT}}

═══════════════════════════════════════════════════════════════════════════════
INSTRUCCIONES DE EXTRACCIÓN
═══════════════════════════════════════════════════════════════════════════════

1. PERSONAJES: Para cada personaje que aparece, extrae:
   - Nombre (o descriptor si no tiene nombre)
   - Rol en este fragmento (protagonista, antagonista, secundario, mencionado)
   - Estado emocional predominante
   - Acciones clave que ejecuta (verbos de acción física)
   - Número de líneas de diálogo
   - Primera aparición vs última aparición en el fragmento

2. EVENTOS: Lista cada evento narrativo significativo:
   - Descripción breve del evento
   - Tipo: ACCION_FISICA | REVELACION | DECISION | CAMBIO_UBICACION | INTRODUCCION_PERSONAJE | CAMBIO_EMOCIONAL | DIALOGO_CLAVE
   - Nivel de tensión (1-10)
   - Personajes involucrados

3. MÉTRICAS ESTRUCTURALES:
   - Total de palabras
   - Total de oraciones
   - Total de párrafos
   - Líneas de diálogo
   - Porcentaje de diálogo vs narración
   - Escenas de acción vs reflexión

4. ANÁLISIS DE RITMO:
   - Densidad de eventos (eventos por cada 1000 palabras)
   - Clasificación: RAPIDO | MEDIO | LENTO
   - Justificación del ritmo

5. MARCADORES TEMPORALES:
   - Referencias temporales explícitas ("al día siguiente", "tres horas después")
   - Tiempo narrativo estimado transcurrido en este fragmento

6. ELEMENTOS NARRATIVOS:
   - Lugar/escenario principal
   - Tiempo del día/época
   - Atmósfera dominante
   - ¿Hay conflicto presente? (true/false)
   - ¿Termina con gancho hacia siguiente escena? (true/false)

7. SEÑALES DE EDICIÓN (para Capa 2 y 3):
   - Instancias de "tell" en lugar de "show"
   - Repeticiones de palabras/frases
   - Posibles inconsistencias internas
   - Fortalezas narrativas del fragmento

RESPONDE ÚNICAMENTE CON JSON VÁLIDO (sin markdown, sin comentarios):
{
  "fragment_id": {{FRAGMENT_ID}},
  "parent_chapter_id": {{PARENT_CHAPTER_ID}},
  "titulo_capitulo": "{{PARENT_CHAPTER}}",
  "fragment_index": {{FRAGMENT_INDEX}},
  "total_fragments": {{TOTAL_FRAGMENTS}},
  "reparto_local": [
    {
      "nombre": "string",
      "rol_en_fragmento": "protagonista|antagonista|secundario|mencionado",
      "estado_emocional": "string",
      "acciones_clave": ["string"],
      "dialogos_count": 0,
      "primera_aparicion_linea": 0,
      "ultima_aparicion_linea": 0
    }
  ],
  "eventos": [
    {
      "evento": "string",
      "tipo": "ACCION_FISICA|REVELACION|DECISION|CAMBIO_UBICACION|INTRODUCCION_PERSONAJE|CAMBIO_EMOCIONAL|DIALOGO_CLAVE",
      "tension": 0,
      "personajes_involucrados": ["string"],
      "posicion_relativa": "inicio|medio|final"
    }
  ],
  "metricas": {
    "estructura": {
      "total_palabras": 0,
      "total_oraciones": 0,
      "total_parrafos": 0
    },
    "composicion": {
      "lineas_dialogo": 0,
      "porcentaje_dialogo": 0,
      "escenas_accion": 0,
      "escenas_reflexion": 0
    },
    "ritmo": {
      "eventos_por_mil_palabras": 0.0,
      "clasificacion": "RAPIDO|MEDIO|LENTO",
      "justificacion": "string"
    },
    "tiempo": {
      "referencias_explicitas": ["string"],
      "transcurrido_estimado": "string"
    }
  },
  "elementos_narrativos": {
    "lugar": "string",
    "tiempo_narrativo": "string",
    "atmosfera": "string",
    "conflicto_presente": true,
    "gancho_final": false
  },
  "senales_edicion": {
    "instancias_tell_no_show": [
      {"texto": "string", "sugerencia": "string"}
    ],
    "repeticiones": [
      {"palabra": "string", "frecuencia": 0}
    ],
    "inconsistencias_internas": ["string"],
    "fortalezas": ["string"],
    "problemas_potenciales": ["string"]
  },
  "contexto_fragmentacion": {
    "continua_desde_anterior": false,
    "continua_en_siguiente": false,
    "escena_incompleta": false,
    "notas_contexto": "string"
  }
}
"""

# Advertencias contextuales según posición del fragmento
CONTEXT_WARNINGS = {
    'first_of_many': """
⚠️ ADVERTENCIA DE CONTEXTO:
Este es el PRIMER fragmento de un capítulo que está dividido en {{TOTAL_FRAGMENTS}} partes.
- Este fragmento establece el inicio del capítulo
- Eventos y descripciones pueden continuar en fragmentos posteriores
- Marca si detectas que una escena queda incompleta al final
""",
    'middle': """
⚠️ ADVERTENCIA DE CONTEXTO:
Este es un fragmento INTERMEDIO ({{FRAGMENT_INDEX}} de {{TOTAL_FRAGMENTS}}) de un capítulo dividido.
- El fragmento puede comenzar en medio de una escena o diálogo
- NO marques como error elementos que parecen carecer de contexto inicial
- Ese contexto puede estar en el fragmento previo
- Marca si el fragmento parece comenzar o terminar en medio de una escena
""",
    'last_of_many': """
⚠️ ADVERTENCIA DE CONTEXTO:
Este es el ÚLTIMO fragmento de un capítulo dividido en {{TOTAL_FRAGMENTS}} partes.
- El fragmento puede comenzar en medio de una escena
- Evalúa si proporciona cierre apropiado para el capítulo completo
- El gancho final aquí es el gancho del capítulo completo
""",
    'atomic': """
ℹ️ CONTEXTO:
Este es un capítulo ATÓMICO (no fragmentado).
- Representa el capítulo completo
- Evalúa su estructura como unidad narrativa completa
"""
}


def get_context_warning(fragment: dict) -> str:
    """Genera la advertencia contextual apropiada según la posición del fragmento."""
    
    total = fragment.get('total_fragments', 1)
    index = fragment.get('fragment_index', 1)
    is_first = fragment.get('is_first_fragment', True)
    is_last = fragment.get('is_last_fragment', True)
    
    if total == 1:
        return CONTEXT_WARNINGS['atomic']
    elif is_first:
        warning = CONTEXT_WARNINGS['first_of_many']
    elif is_last:
        warning = CONTEXT_WARNINGS['last_of_many']
    else:
        warning = CONTEXT_WARNINGS['middle']
    
    return warning.replace('{{TOTAL_FRAGMENTS}}', str(total)).replace('{{FRAGMENT_INDEX}}', str(index))


# Estrategia de reintentos
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
    """Llamada a Gemini con reintentos y safety settings."""
    return model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.2,
            "max_output_tokens": 8192,
            "response_mime_type": "application/json"
        },
        request_options={'timeout': 90},
        safety_settings={
            "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
        }
    )


def build_analysis_prompt(fragment: dict) -> str:
    """Construye el prompt de análisis con contexto jerárquico completo."""
    
    context_warning = get_context_warning(fragment)
    
    prompt = ANALYZE_CHAPTER_PROMPT_TEMPLATE
    prompt = prompt.replace("{{FRAGMENT_ID}}", str(fragment.get('id', 0)))
    prompt = prompt.replace("{{PARENT_CHAPTER}}", fragment.get('original_title', 'Sin título'))
    prompt = prompt.replace("{{PARENT_CHAPTER_ID}}", str(fragment.get('parent_chapter_id', 0)))
    prompt = prompt.replace("{{FRAGMENT_INDEX}}", str(fragment.get('fragment_index', 1)))
    prompt = prompt.replace("{{TOTAL_FRAGMENTS}}", str(fragment.get('total_fragments', 1)))
    prompt = prompt.replace("{{SECTION_TYPE}}", fragment.get('section_type', 'CHAPTER'))
    prompt = prompt.replace("{{IS_FIRST}}", "Sí" if fragment.get('is_first_fragment', True) else "No")
    prompt = prompt.replace("{{IS_LAST}}", "Sí" if fragment.get('is_last_fragment', True) else "No")
    prompt = prompt.replace("{{CONTEXT_WARNING}}", context_warning)
    prompt = prompt.replace("{{CHAPTER_CONTENT}}", fragment.get('content', ''))
    
    return prompt


def main(fragment_json) -> dict:
    """
    Analiza un fragmento con Gemini 2.5 Flash, preservando contexto jerárquico.
    
    Input: Fragmento con metadatos jerárquicos completos
    Output: Análisis de Capa 1 con toda la información estructurada
    """
    fragment_id = "Desconocido"
    parent_chapter = "Sin título"
    
    try:
        # A. Parseo de entrada
        if isinstance(fragment_json, str):
            try:
                fragment = json.loads(fragment_json)
            except json.JSONDecodeError:
                fragment = {"id": 0, "title": "Error Decode", "content": ""}
        else:
            fragment = fragment_json

        # B. Extraer campos
        fragment_id = str(fragment.get('id', 0))
        parent_chapter_id = fragment.get('parent_chapter_id', 0)
        parent_chapter = fragment.get('original_title', 'Sin título')
        fragment_index = fragment.get('fragment_index', 1)
        total_fragments = fragment.get('total_fragments', 1)
        section_type = fragment.get('section_type', 'CHAPTER')
        
        logging.info(f"🔍 Analizando fragmento {fragment_id} | Cap: {parent_chapter} | Frag {fragment_index}/{total_fragments}")

        # C. Configurar Gemini
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return {"error": "No API Key", "fragment_id": fragment_id}

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('models/gemini-2.5-flash-preview-05-20')

        # D. Construir prompt contextualizado
        prompt = build_analysis_prompt(fragment)
        
        # E. Llamar a Gemini
        start_gemini = time_module.time()
        response = call_gemini_with_retry(model, prompt)
        gemini_elapsed = time_module.time() - start_gemini
        
        logging.info(f"⏱️ Análisis completado en {gemini_elapsed:.2f}s")
        
        if not response.candidates:
            raise ValueError("Respuesta vacía o bloqueada")

        # F. Parsear respuesta
        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        analysis = json.loads(response_text.strip())
        
        # G. Asegurar campos jerárquicos en el resultado
        analysis['fragment_id'] = int(fragment_id)
        analysis['parent_chapter_id'] = parent_chapter_id
        analysis['titulo_capitulo'] = parent_chapter
        analysis['fragment_index'] = fragment_index
        analysis['total_fragments'] = total_fragments
        analysis['section_type'] = section_type
        analysis['is_first_fragment'] = fragment.get('is_first_fragment', True)
        analysis['is_last_fragment'] = fragment.get('is_last_fragment', True)
        
        # H. Metadata
        analysis['_metadata'] = {
            'status': 'success', 
            'model': 'gemini-2.5-flash',
            'processing_time_seconds': round(gemini_elapsed, 2),
            'analysis_layer': 1
        }
        
        return analysis

    except Exception as e:
        error_msg = str(e)
        logging.error(f"💥 Error en fragmento {fragment_id}: {error_msg}")
        
        status = "fatal_error"
        if "429" in error_msg or "ResourceExhausted" in error_msg:
            status = "rate_limit_exhausted"
        
        return {
            "fragment_id": int(fragment_id) if fragment_id.isdigit() else 0,
            "parent_chapter_id": fragment.get('parent_chapter_id', 0) if isinstance(fragment, dict) else 0,
            "titulo_capitulo": parent_chapter,
            "error": error_msg, 
            "status": status,
            "reparto_local": [],
            "eventos": [],
            "_metadata": {"status": "error", "analysis_layer": 1}
        }

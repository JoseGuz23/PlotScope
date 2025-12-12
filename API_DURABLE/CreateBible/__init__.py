# =============================================================================
# CreateBible/__init__.py - LYA 7.0 (TUNED & UNLEASHED)
# =============================================================================
# OPTIMIZACIÓN AVANZADA:
# 1. System Instruction separado: Rol inmutable.
# 2. Top-P = 0.8: Reducción de alucinaciones para precisión técnica.
# 3. Scratchpad: Campo de razonamiento interno forzado en el JSON.
# =============================================================================

import logging
import json
import os
import time
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logging.basicConfig(level=logging.INFO)

# -----------------------------------------------------------------------------
# 1. SYSTEM INSTRUCTION (Rol Inmutable)
# -----------------------------------------------------------------------------
SYSTEM_ROLE = """Eres el ARQUITECTO NARRATIVO de una editorial de prestigio.
Tu única función es crear la "Fuente de Verdad" (Biblia Narrativa) de una novela basada estrictamente en los análisis proporcionados.
No inventes. No asumas. Si los datos muestran una contradicción, documéntala."""

# -----------------------------------------------------------------------------
# 2. USER PROMPT (Instrucciones de Tarea + Datos)
# -----------------------------------------------------------------------------
BIBLE_TASK_PROMPT = """
TIENES ACCESO A LOS SIGUIENTES DATOS DE ANÁLISIS MASIVOS:

1. ANÁLISIS HOLÍSTICO:
{holistic_analysis}

2. ANÁLISIS DE CAUSALIDAD:
{causality_summary}

3. RADIOGRAFÍA DETALLADA POR CAPÍTULO:
{chapters_detail_dump}

═══════════════════════════════════════════════════════════════════════════════
TU TAREA
═══════════════════════════════════════════════════════════════════════════════
Genera la BIBLIA NARRATIVA en formato JSON.

IMPORTANTE: Para asegurar la máxima calidad, el primer campo del JSON debe ser "_razonamiento_arquitecto", donde debes explicar brevemente los patrones mayores que has detectado antes de llenar los campos estructurados.

ESTRUCTURA JSON REQUERIDA:
{{
  "_razonamiento_arquitecto": "Análisis interno de 200-300 palabras detectando el arco macro y los problemas raíz...",
  
  "identidad_obra": {{
    "genero": "string",
    "subgenero": "string",
    "tono_predominante": "string",
    "tema_central": "string",
    "logline": "string",
    "estilo_narrativo": "string"
  }},
  
  "arco_narrativo": {{
    "estructura_detectada": "string",
    "puntos_clave": {{
      "gancho_inicial": {{"capitulo": 0, "descripcion": "string"}},
      "inciting_incident": {{"capitulo": 0, "descripcion": "string"}},
      "primer_giro": {{"capitulo": 0, "descripcion": "string"}},
      "punto_medio": {{"capitulo": 0, "descripcion": "string"}},
      "climax": {{"capitulo": 0, "descripcion": "string"}},
      "resolucion": {{"capitulo": 0, "descripcion": "string"}}
    }},
    "evaluacion_arco": {{
      "coherencia": 0,
      "comentarios": "string"
    }}
  }},
  
  "reparto_completo": {{
    "protagonistas": [
      {{
        "nombre": "string",
        "rol": "string",
        "arco": "string",
        "motivacion": "string",
        "conflicto_interno": "string",
        "capitulos_clave": [0]
      }}
    ],
    "antagonistas": [],
    "secundarios": []
  }},
  
  "voz_del_autor": {{
    "estilo": "string",
    "recursos_frecuentes": ["string"],
    "NO_CORREGIR": ["string - Elementos sagrados del estilo"]
  }},
  
  "problemas_priorizados": {{
    "criticos": [
      {{
        "id": "CRIT-001",
        "tipo": "string",
        "descripcion": "string",
        "capitulos_afectados": [0]
      }}
    ]
  }},
  
  "metricas_globales": {{
    "total_palabras": 0,
    "score_global": 0
  }}
}}
"""

@retry(
    retry=retry_if_exception_type((Exception,)),
    wait=wait_exponential(multiplier=2, min=4, max=90),
    stop=stop_after_attempt(3),
    reraise=True
)
def call_gemini_pro_tuned(client, prompt, system_instruction):
    """
    Llamada a Gemini 3 Pro con parámetros de precisión (Nucleus Sampling).
    """
    return client.models.generate_content(
        model='gemini-3-pro-preview',
        contents=prompt,
        config=types.GenerateContentConfig(
            # VARIABLE CLAVE 1: System Instruction fuera del prompt de usuario
            system_instruction=system_instruction,
            
            # VARIABLE CLAVE 2: Temperatura baja para análisis factual
            temperature=0.2, 
            
            # VARIABLE CLAVE 3: Top-P ajustado (0.8) para evitar alucinaciones creativas
            # Le dice al modelo: "Solo considera el 80% de probabilidades más altas".
            # Elimina las opciones "locas" o poco probables.
            top_p=0.8,
            
            max_output_tokens=32000,
            response_mime_type="application/json",
            
            safety_settings=[
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
            ]
        )
    )

def prepare_chapters_detail_dump(chapters_consolidated: list) -> str:
    """Volcado completo sin recortes."""
    dump = []
    try:
        chapters_sorted = sorted(chapters_consolidated, key=lambda x: int(x.get('chapter_id', 0)))
    except:
        chapters_sorted = chapters_consolidated

    for chapter in chapters_sorted:
        l1 = chapter.get('layer1_factual', {})
        l2 = chapter.get('layer2_structural', {})
        l3 = chapter.get('layer3_qualitative', {})
        
        ch_data = {
            'id': chapter.get('chapter_id'),
            'titulo': chapter.get('titulo'),
            'resumen': l1.get('summary', ''),
            'personajes': l1.get('characters', []), 
            'estructura': {
                'funcion': l2.get('narrative_function'),
                'tension': l2.get('tension_level')
            },
            'calidad': {
                'score': l3.get('evaluacion_global', {}).get('score', 0),
                'problemas': chapter.get('senales_edicion', {}).get('problemas_potenciales', [])
            }
        }
        dump.append(ch_data)
    
    return json.dumps(dump, indent=2, ensure_ascii=False)

def prepare_causality_full(causality_analysis: dict) -> str:
    if not causality_analysis: return "{}"
    return json.dumps(causality_analysis, indent=2, ensure_ascii=False)

def main(bible_input_json) -> dict:
    bible_input_raw = bible_input_json 
    try:
        if isinstance(bible_input_raw, str):
            try: bible_input = json.loads(bible_input_raw)
            except: return {}
        else: bible_input = bible_input_raw

        start_time = time.time()
        logging.info("📜 Generando Biblia Narrativa (TUNED PARAMETERS)...")
        
        # 1. Extracción
        holistic_analysis = bible_input.get('holistic_analysis', {})
        causality_analysis = bible_input.get('analisis_causalidad') or bible_input.get('causality_analysis', {})
        if 'chapter_analyses' in bible_input:
            chapters_consolidated = bible_input['chapter_analyses']
        else:
            chapters_consolidated = bible_input.get('chapters_consolidated', [])
            
        if not chapters_consolidated and not holistic_analysis:
             return {'error': 'Input vacío'}

        # 2. Preparación (Flood Context)
        holistic_json = json.dumps(holistic_analysis, indent=2, ensure_ascii=False)
        chapters_dump = prepare_chapters_detail_dump(chapters_consolidated)
        causality_json = prepare_causality_full(causality_analysis)
        
        # 3. Prompt de Tarea (Solo datos + estructura)
        prompt = BIBLE_TASK_PROMPT.format(
            holistic_analysis=holistic_json,
            causality_summary=causality_json,
            chapters_detail_dump=chapters_dump
        )
        
        logging.info(f" 🧮 Prompt Size: {len(prompt)} chars. Enviando a Gemini 3 Pro...")

        # 4. Llamada API Optimizada
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key: raise ValueError("GEMINI_API_KEY falta")
        
        client = genai.Client(api_key=api_key)
        
        # Pasamos SYSTEM_ROLE por separado
        response = call_gemini_pro_tuned(client, prompt, SYSTEM_ROLE)
        
        elapsed = time.time() - start_time
        
        if not response.text: raise ValueError("Respuesta vacía")
        
        response_text = response.text.strip()
        if response_text.startswith("```json"): response_text = response_text[7:]
        if response_text.startswith("```"): response_text = response_text[3:]
        if response_text.endswith("```"): response_text = response_text[:-3]
        
        bible = json.loads(response_text.strip())
        
        # Metadata
        bible['_metadata'] = {
            'status': 'success',
            'version': '7.0-tuned',
            'model': 'gemini-3-pro-preview',
            'params': {'top_p': 0.8, 'temperature': 0.2},
            'processing_time': round(elapsed, 2)
        }
        
        logging.info(f"✅ Biblia generada en {elapsed:.1f}s")
        return bible
        
    except Exception as e:
        logging.error(f"❌ Error: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return {'error': str(e), 'status': 'error'}
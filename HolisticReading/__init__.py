# =============================================================================
# HolisticReading/__init__.py - DEPLOY 3.0
# =============================================================================
# CAMBIOS:
#   - Safety settings: formato diccionario
#   - Modelo: models/gemini-2.5-pro (mejor para texto largo)
#   - Prompt: optimizado, removidos campos que CreateBible no usa
# =============================================================================

import logging
import json
import os
import time
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logging.basicConfig(level=logging.INFO)

@retry(
    retry=retry_if_exception_type((Exception,)),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(3),
    reraise=True
)
def call_gemini_pro(model, prompt):
    """Llamada a Gemini Pro con safety settings CORREGIDOS"""
    return model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.2,
            "max_output_tokens": 8192,
            "response_mime_type": "application/json"
        },
        # ✅ FORMATO CORRECTO: diccionario
        safety_settings={
            "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
        }
    )


# Prompt OPTIMIZADO - Solo campos que CreateBible realmente usa
HOLISTIC_READING_PROMPT = """
Eres un LECTOR EXPERTO. Tu trabajo es COMPRENDER esta obra antes de que otros la editen.

NOVELA COMPLETA:
{full_book_text}

ANÁLISIS REQUERIDO:

1. GÉNERO: Principal, subgénero, convenciones seguidas/rotas, contrato con lector

2. ARCO NARRATIVO: Identifica capítulo y descripción de:
   - Gancho inicial, Inciting incident, Primer giro
   - Punto medio, Crisis, Clímax, Resolución

3. RITMO POR CAPÍTULO: Para cada capítulo indica:
   - Clasificación: RAPIDO|MEDIO|LENTO
   - Si es INTENCIONAL o CUESTIONABLE
   - Justificación breve

4. VOZ DEL AUTOR:
   - Estilo de prosa (minimalista/equilibrado/barroco)
   - Longitud de oraciones predominante
   - Densidad de diálogo
   - Lista de elementos que NO deben corregirse (son voz del autor)

5. TEMAS: Tema central y motivos recurrentes

6. ADVERTENCIAS PARA EDITOR: Lista de cosas que podrían malinterpretarse:
   - Ritmo lento intencional
   - Inconsistencias intencionales  
   - Estilo "incorrecto" que es voz del autor

RESPONDE JSON:
{
  "genero": {
    "principal": "",
    "subgenero": "",
    "convenciones_seguidas": [],
    "convenciones_rotas_intencionalmente": [],
    "contrato_con_lector": ""
  },
  "arco_narrativo": {
    "gancho_inicial": {"capitulo": 0, "descripcion": ""},
    "inciting_incident": {"capitulo": 0, "descripcion": ""},
    "primer_giro": {"capitulo": 0, "descripcion": ""},
    "punto_medio": {"capitulo": 0, "descripcion": ""},
    "crisis": {"capitulo": 0, "descripcion": ""},
    "climax": {"capitulo": 0, "descripcion": ""},
    "resolucion": {"capitulo": 0, "descripcion": ""}
  },
  "analisis_ritmo": {
    "patron_general": "",
    "por_capitulo": [
      {"capitulo": 0, "titulo": "", "ritmo": "MEDIO", "intencion": "INTENCIONAL", "justificacion": ""}
    ]
  },
  "voz_autor": {
    "estilo_prosa": "",
    "longitud_oraciones": {"predominante": "", "patron": ""},
    "densidad_dialogo": "",
    "recursos_distintivos": [],
    "advertencia_editorial": ""
  },
  "temas": {
    "tema_central": "",
    "motivos_recurrentes": []
  },
  "advertencias_para_editor": [
    {"tipo": "", "ubicacion": "", "descripcion": "", "razon_es_intencional": ""}
  ]
}
"""


def main(full_book_text: str) -> dict:
    """Lectura Holística del libro completo"""
    try:
        start_time = time.time()
        
        word_count = len(full_book_text.split())
        token_estimate = int(word_count * 1.33)
        logging.info(f"📖 Lectura Holística: {word_count:,} palabras (~{token_estimate:,} tokens)")
        
        # Configurar Gemini
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY no configurada")
        
        genai.configure(api_key=api_key)
        
        # ✅ MODELO CONFIRMADO DISPONIBLE
        model = genai.GenerativeModel('models/gemini-3.0-pro-preview')
        
        # Construir prompt (usando .replace para evitar problemas con {})
        prompt = HOLISTIC_READING_PROMPT.replace("{full_book_text}", full_book_text)
        
        logging.info("🧠 Gemini Pro leyendo libro completo...")
        response = call_gemini_pro(model, prompt)
        
        elapsed = time.time() - start_time
        logging.info(f"⏱️ Lectura completada en {elapsed:.1f}s")
        
        if not response.candidates:
            raise ValueError("Respuesta vacía o bloqueada")
        
        response_text = response.text.strip()
        
        # Limpiar markdown si existe
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        elif response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        holistic_analysis = json.loads(response_text.strip())
        
        # Metadata
        holistic_analysis["_metadata"] = {
            "status": "success",
            "palabras_analizadas": word_count,
            "tokens_estimados": token_estimate,
            "tiempo_segundos": round(elapsed, 1),
            "modelo": "gemini-3.0-pro"
        }
        
        logging.info(f"✅ ADN extraído - Género: {holistic_analysis.get('genero', {}).get('principal', 'N/A')}")
        
        return holistic_analysis
        
    except json.JSONDecodeError as e:
        logging.error(f"Error parseando JSON: {e}")
        raise
    except Exception as e:
        logging.error(f"Error en Lectura Holística: {str(e)}")
        raise
# =============================================================================
# CreateBible/__init__.py - DEPLOY 3.0
# =============================================================================
# CAMBIOS:
#   - Safety settings: formato diccionario
#   - Modelo: models/gemini-2.5-pro (confirmado disponible)
# =============================================================================

import logging
import json
import os
import time as time_module
from collections import defaultdict
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.api_core import exceptions

logging.basicConfig(level=logging.INFO)
logging.getLogger('tenacity').setLevel(logging.WARNING)

# Reintentos
retry_strategy = retry(
    retry=retry_if_exception_type((
        exceptions.ResourceExhausted,
        exceptions.ServiceUnavailable,
        exceptions.DeadlineExceeded
    )),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(3),
    reraise=True
)

@retry_strategy
def call_gemini_pro(model, prompt):
    """Llamada con safety settings CORREGIDOS"""
    return model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.1,
            "max_output_tokens": 16384,
            "response_mime_type": "application/json"
        },
        request_options={'timeout': 180},
        # ✅ FORMATO CORRECTO: diccionario
        safety_settings={
            "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
        }
    )


def agrupar_fragmentos(analyses):
    """Agrupa fragmentos por capítulo padre"""
    capitulos_consolidados = defaultdict(lambda: {
        "titulo": "",
        "section_type": "UNKNOWN",
        "fragmentos": [],
        "metadata_agregada": {"ids_involucrados": []}
    })

    for analysis in analyses:
        clean_title = (
            analysis.get("titulo_real") or 
            analysis.get("original_title") or 
            analysis.get("parent_chapter") or 
            "Sin Título"
        )
        
        capitulos_consolidados[clean_title]["titulo"] = clean_title
        
        section_type = analysis.get("section_type")
        if section_type:
             capitulos_consolidados[clean_title]["section_type"] = section_type
             
        capitulos_consolidados[clean_title]["fragmentos"].append(analysis)
        capitulos_consolidados[clean_title]["metadata_agregada"]["ids_involucrados"].append(
            analysis.get("id") or analysis.get("chapter_id", "?")
        )

    resultado = list(capitulos_consolidados.values())
    logging.info(f"📦 Agrupación: {len(analyses)} fragmentos → {len(resultado)} capítulos")
    return resultado


CREATE_BIBLE_PROMPT_TEMPLATE = """
Eres el EDITOR JEFE del Proyecto Sylphrena. Crea la BIBLIA NARRATIVA DEFINITIVA.

Tienes DOS fuentes:
1. ANÁLISIS HOLÍSTICO: Visión de quien leyó el libro COMPLETO
2. ANÁLISIS DETALLADOS: Métricas precisas de cada capítulo

═══════════════════════════════════════════════════════════════════════════════
FUENTE 1: ANÁLISIS HOLÍSTICO
═══════════════════════════════════════════════════════════════════════════════
{{HOLISTIC_DATA}}

═══════════════════════════════════════════════════════════════════════════════
FUENTE 2: ANÁLISIS POR CAPÍTULO
═══════════════════════════════════════════════════════════════════════════════
{{CHAPTERS_DATA}}

═══════════════════════════════════════════════════════════════════════════════
INSTRUCCIONES
═══════════════════════════════════════════════════════════════════════════════
1. IDENTIDAD: Usa holístico como base, confirma con métricas
2. REPARTO: Fusiona apariciones, deduplica nombres
3. ARCO: Usa arco holístico, valida con curvas de tensión
4. RITMO: Cruza ritmo detectado vs intencionalidad
5. VOZ: Protege estilo del autor
6. PROBLEMAS: Prioriza agujeros de trama sobre errores de estilo

RESPONDE JSON:
{
  "metadata_biblia": {"version": "3.0"},
  
  "identidad_obra": {
    "genero": "",
    "subgenero": "",
    "tono_predominante": "",
    "tema_central": "",
    "contrato_con_lector": ""
  },
  
  "arco_narrativo": {
    "estructura_detectada": "",
    "puntos_clave": {
      "gancho": {"capitulo": 0, "descripcion": ""},
      "inciting_incident": {"capitulo": 0, "descripcion": ""},
      "primer_giro": {"capitulo": 0, "descripcion": ""},
      "punto_medio": {"capitulo": 0, "descripcion": ""},
      "crisis": {"capitulo": 0, "descripcion": ""},
      "climax": {"capitulo": 0, "descripcion": ""},
      "resolucion": {"capitulo": 0, "descripcion": ""}
    },
    "evaluacion": "SOLIDO"
  },
  
  "reparto_completo": {
    "protagonistas": [{"nombre": "", "aliases": [], "rol_arquetipo": "", "arco_personaje": "", "capitulos_aparicion": [], "consistencia": "CONSISTENTE"}],
    "antagonistas": [],
    "secundarios": []
  },
  
  "mapa_de_ritmo": {
    "patron_global": "",
    "capitulos": [{"numero": 0, "titulo": "", "clasificacion": "MEDIO", "es_intencional": true, "justificacion": "", "posicion_en_arco": ""}],
    "alertas_pacing": []
  },
  
  "voz_del_autor": {
    "estilo_detectado": "",
    "caracteristicas": {"longitud_oraciones": "", "densidad_dialogo": ""},
    "NO_CORREGIR": []
  },
  
  "reglas_del_mundo": [],
  
  "problemas_priorizados": {
    "criticos": [{"id": "", "tipo": "", "descripcion": "", "capitulos_afectados": [], "sugerencia": ""}],
    "medios": [],
    "menores": []
  },
  
  "guia_para_claude": {
    "instrucciones_globales": [],
    "capitulos_especiales": [],
    "patrones_a_mantener": []
  }
}
"""


def main(bible_input_json) -> dict:
    """Fusiona análisis detallados + lectura holística"""
    try:
        # Parseo
        if isinstance(bible_input_json, str):
            try:
                bible_input = json.loads(bible_input_json)
            except json.JSONDecodeError:
                bible_input = {}
        else:
            bible_input = bible_input_json
        
        chapter_analyses = bible_input.get('chapter_analyses', [])
        holistic_analysis = bible_input.get('holistic_analysis', {})
        has_holistic = bool(holistic_analysis and holistic_analysis.get('genero'))
        
        logging.info(f"📚 CreateBible v3.0 - {len(chapter_analyses)} análisis")
        
        # Agrupación
        capitulos_estructurados = agrupar_fragmentos(chapter_analyses)
        
        # Configurar Gemini
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY no configurada")
            
        genai.configure(api_key=api_key)
        
        # ✅ MODELO CONFIRMADO DISPONIBLE
        model = genai.GenerativeModel('models/gemini-3.0-pro-preview')
        
        # Construir prompt
        str_holistic = json.dumps(holistic_analysis, indent=2, ensure_ascii=False) if has_holistic else "NO DISPONIBLE"
        str_chapters = json.dumps(capitulos_estructurados, indent=2, ensure_ascii=False)
        
        prompt = CREATE_BIBLE_PROMPT_TEMPLATE.replace("{{HOLISTIC_DATA}}", str_holistic)
        prompt = prompt.replace("{{CHAPTERS_DATA}}", str_chapters)
        
        # Llamar
        start_time = time_module.time()
        logging.info("🧠 Construyendo Biblia v3.0...")
        
        response = call_gemini_pro(model, prompt)
        
        elapsed = time_module.time() - start_time
        logging.info(f"⏱️ Biblia creada en {elapsed:.2f}s")
        
        if not response.candidates:
            raise ValueError("Respuesta vacía o bloqueada")
        
        # Parsear
        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        elif response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        bible = json.loads(response_text.strip())
        
        # Metadata
        bible['_metadata'] = {
            'status': 'success',
            'version': '3.0',
            'modelo': 'gemini-3.0-pro',
            'tiempo_segundos': round(elapsed, 2),
            'capitulos_procesados': len(capitulos_estructurados),
            'tiene_holistic': has_holistic
        }
        
        problemas = bible.get('problemas_priorizados', {})
        logging.info(f"✅ Biblia lista. Problemas críticos: {len(problemas.get('criticos', []))}")
        
        return bible
            
    except Exception as e:
        logging.error(f"💥 Error en CreateBible: {str(e)}")
        return {
            "metadata_biblia": {"error": True},
            "identidad_obra": {"genero": "Error", "tema_central": f"Fallo: {str(e)}"},
            "problemas_priorizados": {"criticos": [], "medios": [], "menores": []},
            "_metadata": {"status": "error", "error_msg": str(e)}
        }
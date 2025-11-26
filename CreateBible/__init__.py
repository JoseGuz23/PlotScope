# =============================================================================
# CreateBible/__init__.py - DEPLOY 3.1 (SDK UPDATE)
# =============================================================================
# CAMBIOS:
#   - Actualizado a SDK 'google-genai' (v1.0).
#   - LÓGICA PRESERVADA: Prompt de Biblia, Agrupación, Tenacity, Metadata.
# =============================================================================

import logging
import json
import os
import time as time_module
from collections import defaultdict
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logging.basicConfig(level=logging.INFO)
logging.getLogger('tenacity').setLevel(logging.WARNING)

# Reintentos (Tu configuración original)
retry_strategy = retry(
    retry=retry_if_exception_type((Exception,)), # Simplificado para atrapar errores del nuevo SDK
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(3),
    reraise=True
)

@retry_strategy
def call_gemini_pro_new(client, prompt):
    """Llamada a Gemini Pro con SDK Nuevo y tus settings"""
    return client.models.generate_content(
        model='models/gemini-3-pro-preview', # Usamos 3 Pro
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=8192, # Ajustado a un valor seguro estándar
            response_mime_type="application/json",
            safety_settings=[
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
            ]
        )
    )

def agrupar_fragmentos(analyses):
    """Agrupa fragmentos por capítulo padre (TU LÓGICA ORIGINAL)"""
    capitulos_consolidados = defaultdict(lambda: {
        "titulo": "",
        "section_type": "UNKNOWN",
        "fragmentos": [],
        "metadata_agregada": {"ids_involucrados": []}
    })

    for analysis in analyses:
        if not analysis: continue
        
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

# (TU PROMPT ORIGINAL INTACTO)
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
    """Fusiona análisis detallados + lectura holística (SDK Nuevo)"""
    try:
        # 1. Parseo (Tu lógica original)
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
        
        logging.info(f"📚 CreateBible v3.1 - {len(chapter_analyses)} análisis")
        
        # 2. Agrupación (Tu función)
        capitulos_estructurados = agrupar_fragmentos(chapter_analyses)
        
        # 3. Cliente Nuevo
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY no configurada")
            
        client = genai.Client(api_key=api_key)
        
        # 4. Construir Prompt (Tu lógica)
        str_holistic = json.dumps(holistic_analysis, indent=2, ensure_ascii=False) if has_holistic else "NO DISPONIBLE"
        str_chapters = json.dumps(capitulos_estructurados, indent=2, ensure_ascii=False)
        # Recorte de seguridad por si es gigante
        str_chapters = str_chapters[:3000000]
        
        prompt = CREATE_BIBLE_PROMPT_TEMPLATE.replace("{{HOLISTIC_DATA}}", str_holistic)
        prompt = prompt.replace("{{CHAPTERS_DATA}}", str_chapters)
        
        start_time = time_module.time()
        logging.info("🧠 Construyendo Biblia v3.1...")
        
        # 5. Llamada
        response = call_gemini_pro_new(client, prompt)
        
        elapsed = time_module.time() - start_time
        logging.info(f"⏱️ Biblia creada en {elapsed:.2f}s")
        
        if not response.text:
            raise ValueError("Respuesta vacía o bloqueada")
        
        # 6. Parseo (Limpieza Markdown)
        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        elif response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        bible = json.loads(response_text.strip())
        
        # 7. Metadata (Original)
        bible['_metadata'] = {
            'status': 'success',
            'version': '3.1',
            'modelo': 'models/gemini-3-pro-preview',
            'tiempo_segundos': round(elapsed, 2),
            'capitulos_procesados': len(capitulos_estructurados),
            'tiene_holistic': has_holistic
        }
        
        problemas = bible.get('problemas_priorizados', {})
        logging.info(f"✅ Biblia lista. Problemas críticos: {len(problemas.get('criticos', []))}")
        
        return bible
            
    except Exception as e:
        logging.error(f"💥 Error en CreateBible: {str(e)}")
        # Estructura de error para no romper orquestador
        return {
            "metadata_biblia": {"error": True},
            "identidad_obra": {"genero": "Error", "tema_central": f"Fallo: {str(e)}"},
            "problemas_priorizados": {"criticos": [], "medios": [], "menores": []},
            "_metadata": {"status": "error", "error_msg": str(e)}
        }
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

# --- 1. CONFIGURACIÓN ROBUSTA DE REINTENTOS ---
retry_strategy = retry(
    retry=retry_if_exception_type((
        exceptions.ResourceExhausted,
        exceptions.ServiceUnavailable,
        exceptions.DeadlineExceeded
    )),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(3), # Bajamos a 3 para evitar timeouts de Azure
    reraise=True
)

@retry_strategy
def call_gemini_pro(model, prompt):
    """Llamada a Gemini Pro con reintentos"""
    return model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.1,
            "max_output_tokens": 16384, # Output largo permitido
            "response_mime_type": "application/json"
        },
        request_options={'timeout': 180}, # Damos 3 minutos por intento a Gemini
        safety_settings=[
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    )

def agrupar_fragmentos(analyses):
    """
    Middleware: Agrupa fragmentos por capítulo padre.
    Se actualiza para capturar el nuevo campo 'section_type'.
    """
    capitulos_consolidados = defaultdict(lambda: {
        "titulo": "",
        "section_type": "UNKNOWN", # Nuevo campo para el tipo estandarizado
        "fragmentos": [],
        "metadata_agregada": {"ids_involucrados": []}
    })

    for analysis in analyses:
        # Usamos 'titulo_real' (el título limpio inyectado por analize_chapter)
        # como la clave de agrupación principal.
        clean_title = (
            analysis.get("titulo_real") or 
            analysis.get("original_title") or 
            analysis.get("parent_chapter") or 
            "Sin Título"
        )
        
        capitulos_consolidados[clean_title]["titulo"] = clean_title
        
        # Propagamos el tipo de sección (asumimos que es consistente en todos los fragmentos)
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

# --- 2. PLANTILLA DEL PROMPT (SIN f-strings, SIN dobles llaves confusas) ---
CREATE_BIBLE_PROMPT_TEMPLATE = """
Eres el EDITOR JEFE del Proyecto Sylphrena. Tu misión es crear la BIBLIA NARRATIVA DEFINITIVA.

Tienes acceso a DOS fuentes de información complementarias:

1. **ANÁLISIS HOLÍSTICO**: La visión de alguien que leyó el libro COMPLETO.
2. **ANÁLISIS DETALLADOS**: Métricas precisas de cada capítulo.

Tu trabajo: FUSIONAR ambas perspectivas y PRIORIZAR problemas.

═══════════════════════════════════════════════════════════════════════════════
FUENTE 1: ANÁLISIS HOLÍSTICO (Visión Global)
═══════════════════════════════════════════════════════════════════════════════
{{HOLISTIC_DATA}}

═══════════════════════════════════════════════════════════════════════════════
FUENTE 2: ANÁLISIS POR CAPÍTULO (Datos Detallados)
═══════════════════════════════════════════════════════════════════════════════
{{CHAPTERS_DATA}}

═══════════════════════════════════════════════════════════════════════════════
INSTRUCCIONES DE FUSIÓN
═══════════════════════════════════════════════════════════════════════════════
1. IDENTIDAD: Usa el holístico como base. Confirma con métricas.
2. REPARTO: Fusiona apariciones. Deduplica nombres (Juan = Juanito).
3. ARCO: Usa el arco holístico. Valida con curvas de tensión de capítulos.
4. RITMO: Cruza ritmo detectado vs intencionalidad holística.
5. VOZ: Protege el estilo del autor definido en el holístico.
6. PROBLEMAS: Prioriza agujeros de trama sobre errores de estilo.

═══════════════════════════════════════════════════════════════════════════════
RESPONDE CON ESTE JSON EXACTO:
═══════════════════════════════════════════════════════════════════════════════
{
  "metadata_biblia": {
    "version": "2.0",
    "resumen": "Generado por Sylphrena Orchestrator"
  },
  
  "identidad_obra": {
    "genero": "...",
    "subgenero": "...",
    "tono_predominante": "...",
    "tema_central": "...",
    "contrato_con_lector": "..."
  },
  
  "arco_narrativo": {
    "estructura_detectada": "...",
    "puntos_clave": {
      "gancho": {"capitulo": 0, "descripcion": "..."},
      "inciting_incident": {"capitulo": 0, "descripcion": "..."},
      "primer_giro": {"capitulo": 0, "descripcion": "..."},
      "punto_medio": {"capitulo": 0, "descripcion": "..."},
      "crisis": {"capitulo": 0, "descripcion": "..."},
      "climax": {"capitulo": 0, "descripcion": "..."},
      "resolucion": {"capitulo": 0, "descripcion": "..."}
    },
    "evaluacion": "SOLIDO|NECESITA_AJUSTES"
  },
  
  "reparto_completo": {
    "protagonistas": [
      {
        "nombre": "...",
        "aliases": [],
        "rol_arquetipo": "...",
        "arco_personaje": "...",
        "capitulos_aparicion": [1, 5],
        "consistencia": "CONSISTENTE"
      }
    ],
    "antagonistas": [],
    "secundarios": []
  },
  
  "mapa_de_ritmo": {
    "patron_global": "...",
    "capitulos": [
      {
        "numero": 1,
        "titulo": "...",
        "clasificacion": "RAPIDO|MEDIO|LENTO",
        "es_intencional": true,
        "justificacion": "...",
        "posicion_en_arco": "setup"
      }
    ],
    "alertas_pacing": []
  },
  
  "voz_del_autor": {
    "estilo_detectado": "...",
    "caracteristicas": {
      "longitud_oraciones": "...",
      "densidad_dialogo": "..."
    },
    "NO_CORREGIR": [
      "Lista de elementos sagrados del estilo"
    ]
  },
  
  "reglas_del_mundo": [],
  
  "problemas_priorizados": {
    "criticos": [
      {
        "id": "CRIT-001",
        "tipo": "...",
        "descripcion": "...",
        "capitulos_afectados": [],
        "sugerencia": "..."
      }
    ],
    "medios": [],
    "menores": []
  },
  
  "guia_para_claude": {
    "instrucciones_globales": ["..."],
    "capitulos_especiales": [],
    "patrones_a_mantener": []
  }
}
"""

def main(bible_input_json) -> dict:
    """
    Fase REDUCE v2.0: Fusiona análisis detallados + lectura holística
    """
    try:
        # A. Parseo de Input
        if isinstance(bible_input_json, str):
            try:
                bible_input = json.loads(bible_input_json)
            except json.JSONDecodeError:
                logging.error("bible_input_json inválido")
                bible_input = {}
        else:
            bible_input = bible_input_json
        
        chapter_analyses = bible_input.get('chapter_analyses', [])
        holistic_analysis = bible_input.get('holistic_analysis', {})
        has_holistic = bool(holistic_analysis and holistic_analysis.get('genero'))
        
        logging.info(f"📚 CreateBible v2.0 iniciando...")
        logging.info(f"   - Análisis de capítulos: {len(chapter_analyses)}")
        
        # B. Agrupación
        capitulos_estructurados = agrupar_fragmentos(chapter_analyses)
        
        # C. Configuración Gemini
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY no configurada")
            
        genai.configure(api_key=api_key)
        # Usamos 1.5 Pro por su enorme ventana de contexto y estabilidad
        model = genai.GenerativeModel('gemini-3.0-pro-preview') # Usando el modelo de preview por defecto
        
        # D. Construcción del Prompt (SEGURO con .replace)
        str_holistic = json.dumps(holistic_analysis, indent=2, ensure_ascii=False) if has_holistic else "NO DISPONIBLE - Inferir de detalles"
        str_chapters = json.dumps(capitulos_estructurados, indent=2, ensure_ascii=False)
        
        prompt = CREATE_BIBLE_PROMPT_TEMPLATE.replace("{{HOLISTIC_DATA}}", str_holistic)
        prompt = prompt.replace("{{CHAPTERS_DATA}}", str_chapters)
        
        # E. Llamada a IA
        start_time = time_module.time()
        logging.info("🧠 Gemini Pro está construyendo la Biblia v2.0...")
        
        response = call_gemini_pro(model, prompt)
        
        elapsed = time_module.time() - start_time
        logging.info(f"⏱️ Gemini Pro tardó {elapsed:.2f}s")
        
        if not response.candidates:
            raise ValueError("Respuesta vacía o bloqueada por seguridad")
        
        # F. Parseo de Respuesta
        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        elif response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        bible = json.loads(response_text.strip())
        
        # G. Metadata
        prompt_tokens = len(prompt.split()) * 1.3
        output_tokens = len(response_text.split()) * 1.3
        
        bible['_metadata'] = {
            'status': 'success',
            'version': '2.0',
            'modelo': 'gemini-3.0-pro-preview',
            'tiempo_segundos': round(elapsed, 2),
            'capitulos_procesados': len(capitulos_estructurados),
            'tiene_holistic': has_holistic,
            'costo_estimado_usd': 0 # Calcular según pricing actual
        }
        
        problemas = bible.get('problemas_priorizados', {})
        logging.info(f"✅ Biblia creada. Problemas críticos: {len(problemas.get('criticos', []))}")
        
        return bible
            
    except Exception as e:
        logging.error(f"💥 Error fatal en CreateBible: {str(e)}")
        # Estructura de fallo segura
        return {
            "metadata_biblia": {"error": True},
            "identidad_obra": {"genero": "Error", "tema_central": f"Fallo: {str(e)}"},
            "problemas_priorizados": {"criticos": [], "medios": [], "menores": []},
            "_metadata": {"status": "error", "error_msg": str(e)}
        }
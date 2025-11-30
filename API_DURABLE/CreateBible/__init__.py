# =============================================================================
# CreateBible/__init__.py - SYLPHRENA 4.0 (CORREGIDO)
# =============================================================================
# CORRECCIÓN:
#   - Soluciona el bug de "Inputs: 0" mapeando correctamente la entrada
#     del Orchestrator v4 ('chapter_analyses').
# =============================================================================

import logging
import json
import os
import time
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logging.basicConfig(level=logging.INFO)

# =============================================================================
# PROMPT DE SÍNTESIS DE BIBLIA (Intacto)
# =============================================================================

BIBLE_SYNTHESIS_PROMPT = """
Eres un EDITOR JEFE sintetizando todos los análisis de una novela en una BIBLIA NARRATIVA definitiva.

═══════════════════════════════════════════════════════════════════════════════
ANÁLISIS HOLÍSTICO (Lectura completa del libro)
═══════════════════════════════════════════════════════════════════════════════
{holistic_analysis}

═══════════════════════════════════════════════════════════════════════════════
ANÁLISIS DE CAPÍTULOS CONSOLIDADOS (Capa 1)
═══════════════════════════════════════════════════════════════════════════════
{chapters_summary}

═══════════════════════════════════════════════════════════════════════════════
ANÁLISIS ESTRUCTURAL POR CAPÍTULO (Capa 2)
═══════════════════════════════════════════════════════════════════════════════
{structural_summary}

═══════════════════════════════════════════════════════════════════════════════
EVALUACIONES CUALITATIVAS (Capa 3)
═══════════════════════════════════════════════════════════════════════════════
{qualitative_summary}

═══════════════════════════════════════════════════════════════════════════════
ANÁLISIS DE CAUSALIDAD
═══════════════════════════════════════════════════════════════════════════════
{causality_summary}

═══════════════════════════════════════════════════════════════════════════════
TU TAREA: GENERAR BIBLIA NARRATIVA DEFINITIVA
═══════════════════════════════════════════════════════════════════════════════

Sintetiza TODA la información en una Biblia Narrativa coherente que servirá como fuente de verdad para la edición.

RESPONDE CON JSON VÁLIDO:
{{
  "identidad_obra": {{
    "genero": "string",
    "subgenero": "string",
    "tono_predominante": "string",
    "tema_central": "string",
    "contrato_con_lector": "string",
    "estilo_narrativo": "PRIMERA_PERSONA|TERCERA_LIMITADA|TERCERA_OMNISCIENTE|MULTIPLE"
  }},
  
  "arco_narrativo": {{
    "estructura_detectada": "TRES_ACTOS|VIAJE_HEROE|EPISODICA|OTRO",
    "puntos_clave": {{
      "gancho_inicial": {{"capitulo": 0, "descripcion": "string"}},
      "inciting_incident": {{"capitulo": 0, "descripcion": "string"}},
      "primer_giro": {{"capitulo": 0, "descripcion": "string"}},
      "punto_medio": {{"capitulo": 0, "descripcion": "string"}},
      "crisis": {{"capitulo": 0, "descripcion": "string"}},
      "climax": {{"capitulo": 0, "descripcion": "string"}},
      "resolucion": {{"capitulo": 0, "descripcion": "string"}}
    }},
    "evaluacion_arco": {{
      "fortalezas": ["string"],
      "debilidades": ["string"],
      "score": 0
    }}
  }},
  
  "reparto_completo": {{
    "protagonistas": [
      {{
        "nombre": "string",
        "aliases": ["string"],
        "rol_arquetipo": "string",
        "arco_personaje": "string",
        "motivacion_principal": "string",
        "consistencia": "CONSISTENTE|CUESTIONABLE|INCONSISTENTE",
        "notas_inconsistencia": ["string"],
        "capitulos_clave": [0]
      }}
    ],
    "antagonistas": [],
    "secundarios": []
  }},
  
  "voz_del_autor": {{
    "estilo_detectado": "MINIMALISTA|EQUILIBRADO|BARROCO|POETICO",
    "longitud_oraciones": "CORTAS|MEDIAS|LARGAS|MIXTAS",
    "densidad_dialogo": "ALTA|MEDIA|BAJA",
    "recursos_distintivos": ["string"],
    "NO_CORREGIR": [
      "string - elementos que son voz del autor y NO deben modificarse"
    ]
  }},
  
  "mapa_de_ritmo": {{
    "patron_global": "string",
    "capitulos": [
      {{
        "numero": 0,
        "titulo": "string",
        "clasificacion": "RAPIDO|MEDIO|LENTO",
        "es_intencional": true,
        "justificacion": "string",
        "posicion_en_arco": "string"
      }}
    ]
  }},
  
  "problemas_priorizados": {{
    "criticos": [
      {{
        "id": "CRIT-001",
        "tipo": "CAUSALIDAD|CONTINUIDAD|CARACTERIZACION|ESTRUCTURA",
        "descripcion": "string",
        "capitulos_afectados": [0],
        "sugerencia": "string"
      }}
    ],
    "medios": [],
    "menores": []
  }},
  
  "guia_para_claude": {{
    "instrucciones_globales": ["string"],
    "patrones_a_mantener": ["string"],
    "capitulos_especiales": [
      {{
        "capitulo": 0,
        "instruccion": "string"
      }}
    ]
  }},
  
  "metricas_globales": {{
    "total_palabras": 0,
    "total_capitulos": 0,
    "score_coherencia_personajes": 0,
    "score_logica_causal": 0,
    "score_estructura": 0,
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
def call_gemini_pro(client, prompt):
    """Llamada a Gemini Pro para síntesis de Biblia."""
    return client.models.generate_content(
        model='gemini-3-pro-preview',
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=16384,
            response_mime_type="application/json",
            safety_settings=[
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
            ]
        )
    )


def prepare_chapters_summary(chapters_consolidated: list) -> str:
    """Prepara resumen de capítulos consolidados para el prompt."""
    
    summary = []
    
    # Ordenar por chapter_id si es posible para asegurar orden cronológico
    try:
        chapters_sorted = sorted(chapters_consolidated, key=lambda x: int(x.get('chapter_id', 0)))
    except:
        chapters_sorted = chapters_consolidated

    for chapter in chapters_sorted:  # Aumentado límite a 50
        ch_summary = {
            'id': chapter.get('chapter_id'),
            'titulo': chapter.get('titulo'),
            'personajes': [p.get('nombre') for p in chapter.get('reparto_completo', [])[:5]],
            'eventos_clave': len(chapter.get('secuencia_eventos', [])),
            'ritmo': chapter.get('metricas_agregadas', {}).get('ritmo', {}).get('clasificacion', 'MEDIO'),
            'problemas': chapter.get('senales_edicion', {}).get('problemas_potenciales', [])[:2]
        }
        summary.append(ch_summary)
    
    return json.dumps(summary, indent=2, ensure_ascii=False)


def prepare_structural_summary(structural_analyses: list) -> str:
    """Prepara resumen de análisis estructurales."""
    
    summary = []
    
    for analysis in structural_analyses:
        if not analysis or analysis.get('error'):
            continue
        
        struct_summary = {
            'chapter_id': analysis.get('chapter_id'),
            'tiene_catalizador': analysis.get('evento_catalizador', {}).get('presente', False),
            'tiene_escalada': analysis.get('escalada_conflicto', {}).get('presente', False),
            'tiene_giro': analysis.get('punto_de_giro', {}).get('presente', False),
            'tipo_cierre': analysis.get('resolucion_gancho', {}).get('tipo', 'N/A'),
            'tipo_capitulo': analysis.get('clasificacion_estructural', {}).get('tipo_capitulo', 'N/A'),
            'score': analysis.get('score_estructural_global', {}).get('score', 0)
        }
        summary.append(struct_summary)
    
    return json.dumps(summary, indent=2, ensure_ascii=False)


def prepare_qualitative_summary(qualitative_analyses: list) -> str:
    """Prepara resumen de evaluaciones cualitativas."""
    
    summary = []
    
    for analysis in qualitative_analyses:
        if not analysis or analysis.get('error'):
            continue
        
        qual_summary = {
            'chapter_id': analysis.get('chapter_id'),
            'coherencia_personajes': analysis.get('coherencia_personajes', {}).get('score', 0),
            'logica_causal': analysis.get('logica_causal', {}).get('score', 0),
            'integracion': analysis.get('integracion_elementos', {}).get('score', 0),
            'nivel_calidad': analysis.get('evaluacion_global', {}).get('nivel_calidad', 'N/A'),
            'problemas_criticos': analysis.get('evaluacion_global', {}).get('problemas_criticos', [])[:2]
        }
        summary.append(qual_summary)
    
    return json.dumps(summary, indent=2, ensure_ascii=False)


def prepare_causality_summary(causality_analysis: dict) -> str:
    """Prepara resumen de análisis de causalidad."""
    
    if not causality_analysis or causality_analysis.get('error'):
        return json.dumps({'error': 'No causality analysis available'})
    
    metrics = causality_analysis.get('metricas_causalidad', {})
    problems = causality_analysis.get('problemas_detectados', {})
    
    summary = {
        'total_eventos': metrics.get('total_eventos', 0),
        'conectividad': metrics.get('porcentaje_conectividad', 0),
        'score_causalidad': metrics.get('score_coherencia_causal', 0),
        'eventos_huerfanos': len(problems.get('eventos_huerfanos', [])),
        'cadenas_rotas': len(problems.get('cadenas_rotas', [])),
        'contradicciones': len(problems.get('contradicciones', [])),
        'problemas_criticos': [
            p.get('descripcion') for p in problems.get('eventos_huerfanos', [])
            if p.get('severidad') == 'CRITICO'
        ][:3]
    }
    
    return json.dumps(summary, indent=2, ensure_ascii=False)


def main(bible_input_json) -> dict:
    """
    Genera la Biblia Narrativa.
    """
    bible_input_raw = bible_input_json 
    
    try:
        # --- BLOQUE DE SEGURIDAD ---
        if isinstance(bible_input_raw, str):
            try:
                bible_input = json.loads(bible_input_raw)
            except json.JSONDecodeError:
                return {}
        else:
            bible_input = bible_input_raw
        # ---------------------------

        start_time = time.time()
        logging.info("📜 Generando Biblia Narrativa...")
        
        # =========================================================================
        # 1. EXTRACCIÓN Y MAPEO DE DATOS (CORREGIDO)
        # =========================================================================
        
        holistic_analysis = bible_input.get('holistic_analysis', {})
        causality_analysis = bible_input.get('analisis_causalidad') or bible_input.get('causality_analysis', {})
        
        # Verificar si viene del Orchestrator v4 (formato anidado)
        if 'chapter_analyses' in bible_input:
            # Lista maestra que contiene Capa 1 + Capa 2 + Capa 3
            main_list = bible_input['chapter_analyses']
            
            chapters_consolidated = main_list # Capa 1 es el objeto base
            
            # Extraer capas anidadas
            structural_analyses = [ch.get('layer2_structural', {}) for ch in main_list]
            qualitative_analyses = [ch.get('layer3_qualitative', {}) for ch in main_list]
            
            logging.info("   🔄 Detectado formato Orchestrator v4 (lista unificada)")
            
        else:
            # Formato legacy (listas separadas)
            chapters_consolidated = bible_input.get('chapters_consolidated', [])
            structural_analyses = bible_input.get('structural_analyses', [])
            qualitative_analyses = bible_input.get('qualitative_analyses', [])
            logging.info("   🔄 Detectado formato Legacy (listas separadas)")

        # =========================================================================
        
        logging.info(f"   📊 Inputs: {len(chapters_consolidated)} capítulos consolidados")
        logging.info(f"   📊 {len([s for s in structural_analyses if s])} análisis estructurales")
        logging.info(f"   📊 {len([q for q in qualitative_analyses if q])} evaluaciones cualitativas")
        
        # Validar si hay datos reales
        if not chapters_consolidated and not holistic_analysis:
             return {'error': 'Input vacío: No hay capítulos ni análisis holístico'}

        # Configurar cliente
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY no configurada")
        
        client = genai.Client(api_key=api_key)
        
        # Preparar resúmenes
        holistic_json = json.dumps(holistic_analysis, indent=2, ensure_ascii=False)[:15000]
        chapters_summary = prepare_chapters_summary(chapters_consolidated)
        structural_summary = prepare_structural_summary(structural_analyses)
        qualitative_summary = prepare_qualitative_summary(qualitative_analyses)
        causality_summary = prepare_causality_summary(causality_analysis)
        
        # Construir prompt
        prompt = BIBLE_SYNTHESIS_PROMPT.format(
            holistic_analysis=holistic_json,
            chapters_summary=chapters_summary,
            structural_summary=structural_summary,
            qualitative_summary=qualitative_summary,
            causality_summary=causality_summary
        )
        
        # Llamar a Gemini Pro
        logging.info("   🧠 Sintetizando con Gemini Pro...")
        response = call_gemini_pro(client, prompt)
        
        elapsed = time.time() - start_time
        
        if not response.text:
            raise ValueError("Respuesta vacía o bloqueada")
        
        # Parsear respuesta
        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        bible = json.loads(response_text.strip())
        
        # Calcular métricas globales si no existen
        if 'metricas_globales' not in bible or not bible['metricas_globales'].get('total_palabras'):
            
            # Helper de seguridad
            def safe_get_score(obj, keys, default=5):
                try:
                    val = obj
                    for k in keys:
                        val = val.get(k, {})
                    return float(val) if not isinstance(val, dict) else default
                except:
                    return default

            total_words = sum(
                int(ch.get('metricas_agregadas', {}).get('estructura', {}).get('total_palabras', 0) or 0)
                for ch in chapters_consolidated
            )
            
            coherencia_scores = [safe_get_score(q, ['coherencia_personajes', 'score']) for q in qualitative_analyses if q]
            logica_scores = [safe_get_score(q, ['logica_causal', 'score']) for q in qualitative_analyses if q]
            estructura_scores = [safe_get_score(s, ['score_estructural_global', 'score']) for s in structural_analyses if s]
            
            # Promedios seguros
            def avg(lst): return round(sum(lst)/max(len(lst), 1), 1)
            
            bible['metricas_globales'] = {
                'total_palabras': total_words,
                'total_capitulos': len(chapters_consolidated),
                'score_coherencia_personajes': avg(coherencia_scores),
                'score_logica_causal': avg(logica_scores),
                'score_estructura': avg(estructura_scores),
                'score_causalidad': safe_get_score(causality_analysis, ['metricas_causalidad', 'score_coherencia_causal'])
            }
            
            # Score global
            metrics = bible['metricas_globales']
            scores = [
                metrics['score_coherencia_personajes'], 
                metrics['score_logica_causal'], 
                metrics['score_estructura']
            ]
            metrics['score_global'] = avg(scores)
        
        # Metadata
        bible['_metadata'] = {
            'status': 'success',
            'version': '4.0',
            'processing_time_seconds': round(elapsed, 2),
            'inputs_processed': {
                'chapters': len(chapters_consolidated),
                'structural': len(structural_analyses),
                'qualitative': len(qualitative_analyses)
            }
        }
        
        score = bible.get('metricas_globales', {}).get('score_global', 'N/A')
        logging.info(f"✅ Biblia generada en {elapsed:.1f}s | Score global: {score}")
        
        return bible
        
    except Exception as e:
        logging.error(f"❌ Error generando Biblia: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return {
            'error': str(e),
            '_metadata': {
                'status': 'error'
            }
        }
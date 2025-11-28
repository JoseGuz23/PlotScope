# =============================================================================
# QualitativeEffectivenessAnalysis/__init__.py - SYLPHRENA 4.0
# =============================================================================
# NUEVA FUNCIÓN - CAPA 3:
#   - Evaluación cualitativa de efectividad dramática
#   - Usa Gemini 3.0 Pro con capacidad de razonamiento profundo
#   - Evalúa: Coherencia de personajes, Lógica causal, Integración de elementos
#   - Genera scores y justificaciones detalladas
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
# PROMPT DE EVALUACIÓN CUALITATIVA (CAPA 3)
# =============================================================================

QUALITATIVE_ANALYSIS_PROMPT = """
Actúa como un EDITOR DE DESARROLLO EXPERIMENTADO evaluando la efectividad dramática de este capítulo.

Tienes acceso a tres fuentes de información:
1. ANÁLISIS FACTUAL (Capa 1): Datos objetivos de personajes, eventos y diálogos
2. ANÁLISIS ESTRUCTURAL (Capa 2): Componentes narrativos identificados
3. CONTEXTO GLOBAL: Información de capítulos previos y arcos establecidos

═══════════════════════════════════════════════════════════════════════════════
INFORMACIÓN DEL CAPÍTULO
═══════════════════════════════════════════════════════════════════════════════
Título: {chapter_title}
ID: {chapter_id}
Posición en el libro: Capítulo {chapter_position} de {total_chapters}
Tipo de sección: {section_type}

═══════════════════════════════════════════════════════════════════════════════
DATOS DE CAPA 1 (Factual)
═══════════════════════════════════════════════════════════════════════════════
PERSONAJES:
{characters_json}

EVENTOS PRINCIPALES:
{events_json}

SEÑALES DE EDICIÓN DETECTADAS:
{editorial_signals_json}

═══════════════════════════════════════════════════════════════════════════════
DATOS DE CAPA 2 (Estructural)
═══════════════════════════════════════════════════════════════════════════════
{structural_analysis_json}

═══════════════════════════════════════════════════════════════════════════════
CONTEXTO GLOBAL (Biblia Parcial)
═══════════════════════════════════════════════════════════════════════════════
Género detectado: {genero}
Tono predominante: {tono}
Tema central: {tema}

Personajes principales del libro:
{main_characters_json}

Eventos clave de capítulos anteriores relevantes:
{previous_context}

═══════════════════════════════════════════════════════════════════════════════
TU TAREA: EVALUACIÓN CUALITATIVA PROFUNDA
═══════════════════════════════════════════════════════════════════════════════

Evalúa la CALIDAD DE EJECUCIÓN en tres dimensiones críticas:

## DIMENSIÓN 1: COHERENCIA DE PERSONAJES

Para cada personaje que toma una decisión o acción significativa en este capítulo:
- ¿Es esa acción CONSISTENTE con su caracterización previa?
- Si un personaje ha sido establecido como cauteloso pero actúa impulsivamente, ¿existe justificación narrativa?
- ¿Las emociones mostradas son apropiadas para la situación?
- ¿El diálogo suena auténtico para ese personaje?

Si no existe justificación para un cambio de comportamiento, márcalo como INCONSISTENCIA DE CARACTERIZACIÓN.

## DIMENSIÓN 2: LÓGICA CAUSAL DE EVENTOS

Examina la secuencia de eventos:
- ¿Cada evento es CONSECUENCIA lógica de eventos anteriores o decisiones de personajes?
- ¿Hay eventos que ocurren sin causa aparente (coincidencias extremas)?
- ¿Las revelaciones están plantadas previamente o se sienten arbitrarias?
- ¿Los personajes tienen la información necesaria para tomar sus decisiones?

Si un evento requiere una coincidencia improbable, márcalo como PROBLEMA DE CAUSALIDAD.

## DIMENSIÓN 3: INTEGRACIÓN DE ELEMENTOS NARRATIVOS

Si el capítulo introduce subtramas o elementos nuevos:
- ¿Están conectados TEMÁTICA o CAUSALMENTE con la trama principal?
- ¿Avanzan el desarrollo de personajes o trama?
- ¿Se sienten como digresiones o relleno?

Evalúa también:
- ¿El ritmo del capítulo es apropiado para su función en la estructura?
- ¿El nivel de tensión es coherente con la posición en el arco narrativo?
- ¿El capítulo cumple su función dramática identificada en Capa 2?

═══════════════════════════════════════════════════════════════════════════════
FORMATO DE RESPUESTA
═══════════════════════════════════════════════════════════════════════════════

Para cada dimensión, proporciona:
- SCORE (1-10): 1=extremadamente problemático, 10=excelente ejecución
- JUSTIFICACIÓN: Explicación detallada citando evidencia específica
- PROBLEMAS: Lista de problemas identificados
- SUGERENCIAS: Cómo podría mejorarse

RESPONDE ÚNICAMENTE CON JSON VÁLIDO:
{{
  "chapter_id": {chapter_id},
  "chapter_title": "{chapter_title}",
  
  "coherencia_personajes": {{
    "score": 0,
    "evaluacion_general": "string",
    "personajes_evaluados": [
      {{
        "nombre": "string",
        "acciones_evaluadas": ["string"],
        "consistencia": "CONSISTENTE|CUESTIONABLE|INCONSISTENTE",
        "justificacion": "string",
        "problemas": ["string"]
      }}
    ],
    "inconsistencias_detectadas": ["string"],
    "fortalezas": ["string"]
  }},
  
  "logica_causal": {{
    "score": 0,
    "evaluacion_general": "string",
    "cadena_causal": {{
      "es_solida": true,
      "eslabones_debiles": ["string"],
      "eventos_sin_causa": ["string"]
    }},
    "coincidencias_problematicas": ["string"],
    "revelaciones": {{
      "bien_plantadas": ["string"],
      "arbitrarias": ["string"]
    }}
  }},
  
  "integracion_elementos": {{
    "score": 0,
    "evaluacion_general": "string",
    "elementos_bien_integrados": ["string"],
    "elementos_desconectados": ["string"],
    "ritmo_apropiado": true,
    "tension_coherente": true,
    "cumple_funcion_dramatica": true,
    "justificacion": "string"
  }},
  
  "evaluacion_global": {{
    "score_promedio": 0.0,
    "nivel_calidad": "EXCELENTE|BUENO|ACEPTABLE|NECESITA_TRABAJO|PROBLEMATICO",
    "resumen_ejecutivo": "string",
    "problemas_criticos": ["string"],
    "problemas_menores": ["string"],
    "fortalezas_destacadas": ["string"],
    "recomendaciones_prioritarias": ["string"]
  }},
  
  "_metadata": {{
    "analysis_layer": 3,
    "model": "gemini-3-pro-preview",
    "deep_think_enabled": true
  }}
}}
"""


@retry(
    retry=retry_if_exception_type((Exception,)),
    wait=wait_exponential(multiplier=2, min=4, max=90),
    stop=stop_after_attempt(3),
    reraise=True
)
def call_gemini_pro_deep_think(client, prompt):
    """
    Llamada a Gemini Pro con configuración optimizada para razonamiento profundo.
    """
    return client.models.generate_content(
        model='gemini-3-pro-preview',
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.4,  # Ligeramente más alto para razonamiento creativo
            max_output_tokens=8192,  # Más espacio para análisis detallado
            response_mime_type="application/json",
            safety_settings=[
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
            ]
        )
    )


def main(analysis_input: dict) -> dict:
    """
    Ejecuta análisis de Capa 3.
    CORRECCIÓN: Busca datos en múltiples ubicaciones posibles.
    """
    # 1. Recuperar el análisis consolidado (Capa 1)
    # Intentamos con ambos nombres posibles
    chapter_consolidated = analysis_input.get('chapter_consolidated') or \
                           analysis_input.get('chapter_analysis') or \
                           {}
    
    # 2. Recuperar el análisis estructural (Capa 2)
    # Puede venir en el root O anidado dentro del capítulo (como lo envía el Orchestrator v4)
    structural_analysis = analysis_input.get('structural_analysis') or \
                          chapter_consolidated.get('layer2_structural') or \
                          {}

    # 3. Recuperar resto de datos
    bible_partial = analysis_input.get('bible_partial', {})
    chapter_position = analysis_input.get('chapter_position', 1)
    total_chapters = analysis_input.get('total_chapters', 1)
    
    # Validación básica
    if not chapter_consolidated:
        logging.warning("⚠️ QualitativeEffectivenessAnalysis recibió input vacío o malformado.")
        return {'error': 'No input data found'}

    chapter_id = chapter_consolidated.get('chapter_id', 0)
    chapter_title = chapter_consolidated.get('titulo', f'Capítulo {chapter_id}')
    
    try:
        start_time = time.time()
        
        logging.info(f"🎭 Evaluación Cualitativa (Capa 3): {chapter_title}")
        
        # Configurar cliente
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY no configurada")
        
        client = genai.Client(api_key=api_key)
        
        # Extraer datos de Capa 1
        characters = chapter_consolidated.get('reparto_completo', [])
        events = chapter_consolidated.get('secuencia_eventos', [])
        editorial_signals = chapter_consolidated.get('senales_edicion', {})
        section_type = chapter_consolidated.get('section_type', 'CHAPTER')
        
        # Preparar JSONs
        characters_json = json.dumps(characters[:8], indent=2, ensure_ascii=False)
        events_json = json.dumps(events[:20], indent=2, ensure_ascii=False)
        editorial_signals_json = json.dumps(editorial_signals, indent=2, ensure_ascii=False)
        structural_analysis_json = json.dumps({
            k: v for k, v in structural_analysis.items() 
            if k not in ['_metadata', 'chapter_id', 'chapter_title']
        }, indent=2, ensure_ascii=False)
        
        # Extraer contexto global de la Biblia parcial
        identidad = bible_partial.get('identidad_obra', {})
        genero = identidad.get('genero', 'No detectado')
        tono = identidad.get('tono_predominante', 'No detectado')
        tema = identidad.get('tema_central', 'No detectado')
        
        # Personajes principales del libro
        reparto = bible_partial.get('reparto_completo', {})
        main_chars = []
        for categoria in ['protagonistas', 'antagonistas']:
            for char in reparto.get(categoria, []):
                main_chars.append({
                    'nombre': char.get('nombre'),
                    'rol': char.get('rol_arquetipo'),
                    'arco': char.get('arco_personaje', '')[:100]
                })
        main_characters_json = json.dumps(main_chars[:5], indent=2, ensure_ascii=False)
        
        # Contexto de capítulos anteriores (simplificado)
        previous_context = bible_partial.get('contexto_capitulos_previos', 'No disponible')
        if isinstance(previous_context, list):
            previous_context = json.dumps(previous_context[:3], indent=2, ensure_ascii=False)
        
        # Construir prompt
        prompt = QUALITATIVE_ANALYSIS_PROMPT.format(
            chapter_title=chapter_title,
            chapter_id=chapter_id,
            chapter_position=chapter_position,
            total_chapters=total_chapters,
            section_type=section_type,
            characters_json=characters_json,
            events_json=events_json,
            editorial_signals_json=editorial_signals_json,
            structural_analysis_json=structural_analysis_json,
            genero=genero,
            tono=tono,
            tema=tema,
            main_characters_json=main_characters_json,
            previous_context=previous_context if isinstance(previous_context, str) else "No disponible"
        )
        
        # Llamar a Gemini Pro con Deep Think
        response = call_gemini_pro_deep_think(client, prompt)
        
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
        
        qualitative_analysis = json.loads(response_text.strip())
        
        # Asegurar campos y metadata
        qualitative_analysis['chapter_id'] = chapter_id
        qualitative_analysis['chapter_title'] = chapter_title
        qualitative_analysis['_metadata'] = {
            'status': 'success',
            'analysis_layer': 3,
            'model': 'gemini-3-pro-preview',
            'deep_think_enabled': True,
            'processing_time_seconds': round(elapsed, 2)
        }
        
        # Calcular score promedio si no existe
        if 'evaluacion_global' not in qualitative_analysis:
            # --- CORRECCIÓN: Conversión segura de scores ---
            def safe_score(val):
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return 5.0  # Valor neutral por defecto

            s1 = safe_score(qualitative_analysis.get('coherencia_personajes', {}).get('score', 5))
            s2 = safe_score(qualitative_analysis.get('logica_causal', {}).get('score', 5))
            s3 = safe_score(qualitative_analysis.get('integracion_elementos', {}).get('score', 5))
            
            scores = [s1, s2, s3]
            # -----------------------------------------------
            
            avg_score = sum(scores) / len(scores)
            qualitative_analysis['evaluacion_global'] = {
                'score_promedio': round(avg_score, 1),
                'nivel_calidad': get_quality_level(avg_score)
            }
        
        nivel = qualitative_analysis.get('evaluacion_global', {}).get('nivel_calidad', 'N/A')
        score = qualitative_analysis.get('evaluacion_global', {}).get('score_promedio', 'N/A')
        
        logging.info(f"✅ Evaluación cualitativa completada en {elapsed:.1f}s | Nivel: {nivel} | Score: {score}")
        
        return qualitative_analysis
        
    except Exception as e:
        logging.error(f"❌ Error en evaluación cualitativa de {chapter_title}: {e}")
        return {
            'chapter_id': chapter_id,
            'chapter_title': chapter_title,
            'error': str(e),
            'evaluacion_global': {
                'score_promedio': 0,
                'nivel_calidad': 'ERROR'
            },
            '_metadata': {
                'status': 'error',
                'analysis_layer': 3
            }
        }


def get_quality_level(score: float) -> str:
    """Convierte score numérico a nivel de calidad."""
    if score >= 8.5:
        return 'EXCELENTE'
    elif score >= 7:
        return 'BUENO'
    elif score >= 5.5:
        return 'ACEPTABLE'
    elif score >= 4:
        return 'NECESITA_TRABAJO'
    else:
        return 'PROBLEMATICO'

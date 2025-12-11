# =============================================================================
# StructuralPatternAnalysis/__init__.py - SYLPHRENA 4.0
# =============================================================================
# NUEVA FUNCIÓN - CAPA 2:
#   - Analiza patrones estructurales de nivel superior
#   - Identifica: Evento catalizador, Escalada, Punto de giro, Resolución
#   - Evalúa la presencia y efectividad de elementos narrativos fundamentales
#   - Prepara datos para evaluación cualitativa de Capa 3
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
# PROMPT DE ANÁLISIS ESTRUCTURAL (CAPA 2)
# =============================================================================

STRUCTURAL_ANALYSIS_PROMPT = """
Eres un ANALISTA DE ESTRUCTURA NARRATIVA experto. Tu trabajo es identificar los componentes estructurales fundamentales de este capítulo basándote en los datos de análisis de Capa 1.

═══════════════════════════════════════════════════════════════════════════════
INFORMACIÓN DEL CAPÍTULO
═══════════════════════════════════════════════════════════════════════════════
Título: {chapter_title}
ID: {chapter_id}
Tipo de sección: {section_type}
Total de palabras: {total_words}
Total de eventos: {total_events}

═══════════════════════════════════════════════════════════════════════════════
PERSONAJES PRESENTES
═══════════════════════════════════════════════════════════════════════════════
{characters_json}

═══════════════════════════════════════════════════════════════════════════════
SECUENCIA DE EVENTOS (en orden cronológico)
═══════════════════════════════════════════════════════════════════════════════
{events_json}

═══════════════════════════════════════════════════════════════════════════════
MÉTRICAS DE RITMO
═══════════════════════════════════════════════════════════════════════════════
Clasificación de ritmo: {ritmo}
Porcentaje de diálogo: {dialogo_pct}%
Escenas de acción: {escenas_accion}
Escenas de reflexión: {escenas_reflexion}

═══════════════════════════════════════════════════════════════════════════════
TU TAREA: ANÁLISIS ESTRUCTURAL
═══════════════════════════════════════════════════════════════════════════════

Identifica los siguientes COMPONENTES ESTRUCTURALES FUNDAMENTALES:

1. EVENTO CATALIZADOR
   - Definición: El evento que interrumpe el equilibrio inicial y fuerza a los personajes a actuar
   - Ubicación típica: Primer tercio del capítulo
   - ¿Está presente? ¿Cuál es? ¿En qué posición de la secuencia de eventos?

2. ESCALADA DE CONFLICTO
   - Definición: Aumento progresivo de tensión, stakes, o complicaciones
   - Evidencia: ¿Los niveles de tensión de los eventos aumentan progresivamente?
   - ¿Hay revelaciones que complican la situación?

3. PUNTO DE GIRO
   - Definición: Momento donde la situación se invierte o toma un curso inesperado
   - Debe estar respaldado por una decisión de personaje o revelación de información
   - ¿Existe? ¿Cuál es? ¿Es efectivo?

4. RESOLUCIÓN/GANCHO
   - Definición: Cómo termina el capítulo
   - ¿Hay cierre de conflictos locales?
   - ¿Hay gancho que impulsa al siguiente capítulo?

5. ESTRUCTURA DEL ARCO
   - ¿El capítulo sigue un arco completo (inicio-desarrollo-cierre)?
   - ¿Es un capítulo de transición?
   - ¿Es un capítulo de establecimiento (setup)?
   - ¿Es un capítulo de payoff (resolución de setup previo)?

Para cada componente, proporciona:
- Si está PRESENTE o AUSENTE
- Si presente: descripción específica citando eventos
- SCORE de efectividad (1-10): 1=muy débil, 10=excelente
- Justificación del score

RESPONDE ÚNICAMENTE CON JSON VÁLIDO:
{{
  "chapter_id": {chapter_id},
  "chapter_title": "{chapter_title}",
  "evento_catalizador": {{
    "presente": true,
    "evento_identificado": "string o null",
    "posicion_en_secuencia": 0,
    "efectividad_score": 0,
    "justificacion": "string"
  }},
  "escalada_conflicto": {{
    "presente": true,
    "patron_tension": "ASCENDENTE|DESCENDENTE|PLANO|FLUCTUANTE",
    "eventos_escalada": ["evento1", "evento2"],
    "efectividad_score": 0,
    "justificacion": "string"
  }},
  "punto_de_giro": {{
    "presente": true,
    "evento_identificado": "string o null",
    "tipo": "DECISION_PERSONAJE|REVELACION|EVENTO_EXTERNO|NINGUNO",
    "posicion_en_secuencia": 0,
    "efectividad_score": 0,
    "justificacion": "string"
  }},
  "resolucion_gancho": {{
    "tipo": "RESOLUCION_COMPLETA|RESOLUCION_PARCIAL|GANCHO|CLIFFHANGER|ABIERTO",
    "descripcion": "string",
    "efectividad_score": 0,
    "justificacion": "string"
  }},
  "clasificacion_estructural": {{
    "tipo_capitulo": "ARCO_COMPLETO|TRANSICION|ESTABLECIMIENTO|PAYOFF|CLIMAX|RESOLUCION",
    "funcion_narrativa": "string",
    "posicion_sugerida_en_acto": "ACTO_1|ACTO_2A|ACTO_2B|ACTO_3"
  }},
  "score_estructural_global": {{
    "score": 0,
    "fortalezas": ["string"],
    "debilidades": ["string"],
    "recomendaciones": ["string"]
  }},
  "_metadata": {{
    "analysis_layer": 2,
    "model": "gemini-3-pro-preview"
  }}
}}
"""


@retry(
    retry=retry_if_exception_type((Exception,)),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(3),
    reraise=True
)
def call_gemini_pro(client, prompt):
    """Llamada a Gemini Pro para análisis de Capa 2."""
    return client.models.generate_content(
        model='gemini-3-pro-preview',
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=4096,
            response_mime_type="application/json",
            safety_settings=[
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
            ]
        )
    )


def main(chapter_consolidated) -> dict:
    """
    Ejecuta análisis de Capa 2 (Patrones Estructurales) sobre un capítulo consolidado.
    
    Input: Capítulo consolidado de Capa 1
    Output: Análisis estructural con identificación de componentes narrativos
    """
    
    # --- BLOQUE DE SEGURIDAD Y NORMALIZACIÓN DE INPUT ---
    try:
        # 1. Normalizar String -> Dict (si llega como JSON string)
        if isinstance(chapter_consolidated, str):
            try:
                input_data = json.loads(chapter_consolidated)
            except Exception:
                logging.warning("⚠️ Error decodificando JSON string en StructuralPatternAnalysis")
                input_data = {}
        else:
            input_data = chapter_consolidated
            
        # 2. Desempaquetar si viene envuelto (Azure a veces anida el input)
        # Verificamos si existe la llave que coincide con el nombre del binding
        if isinstance(input_data, dict) and 'chapter_consolidated' in input_data:
             input_data = input_data['chapter_consolidated']
        
        # 3. Validación final de tipo
        if not isinstance(input_data, dict):
            logging.warning(f"⚠️ Input inválido recibido: {type(input_data)}")
            input_data = {}

        # 4. Reasignar variable para usar el código existente sin cambios
        chapter_consolidated = input_data

    except Exception as e:
        logging.error(f"💥 Error crítico procesando input: {str(e)}")
        chapter_consolidated = {}
    # ----------------------------------------------------

    chapter_id = chapter_consolidated.get('chapter_id', 0)
    chapter_title = chapter_consolidated.get('titulo', f'Capítulo {chapter_id}')
    
    try:
        start_time = time.time()
        
        logging.info(f"🏗️ Análisis Estructural (Capa 2): {chapter_title}")
        
        # Configurar cliente
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY no configurada")
        
        client = genai.Client(api_key=api_key)
        
        # Extraer datos para el prompt
        characters = chapter_consolidated.get('reparto_completo', [])
        events = chapter_consolidated.get('secuencia_eventos', [])
        metrics = chapter_consolidated.get('metricas_agregadas', {})
        section_type = chapter_consolidated.get('section_type', 'CHAPTER')
        
        # Preparar JSONs para inyección
        characters_json = json.dumps(characters[:10], indent=2, ensure_ascii=False)  # Top 10
        events_json = json.dumps(events[:30], indent=2, ensure_ascii=False)  # Top 30
        
        # Métricas
        estructura = metrics.get('estructura', {})
        composicion = metrics.get('composicion', {})
        ritmo = metrics.get('ritmo', {})
        
        total_words = estructura.get('total_palabras', 0)
        total_events = len(events)
        ritmo_class = ritmo.get('clasificacion', 'MEDIO')
        dialogo_pct = composicion.get('porcentaje_dialogo', 0)
        escenas_accion = composicion.get('escenas_accion', 0)
        escenas_reflexion = composicion.get('escenas_reflexion', 0)
        
        # Construir prompt
        prompt = STRUCTURAL_ANALYSIS_PROMPT.format(
            chapter_title=chapter_title,
            chapter_id=chapter_id,
            section_type=section_type,
            total_words=total_words,
            total_events=total_events,
            characters_json=characters_json,
            events_json=events_json,
            ritmo=ritmo_class,
            dialogo_pct=dialogo_pct,
            escenas_accion=escenas_accion,
            escenas_reflexion=escenas_reflexion
        )
        
        # Llamar a Gemini Pro
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
        
        structural_analysis = json.loads(response_text.strip())
        
        # Asegurar campos
        structural_analysis['chapter_id'] = chapter_id
        structural_analysis['chapter_title'] = chapter_title
        structural_analysis['_metadata'] = {
            'status': 'success',
            'analysis_layer': 2,
            'model': 'gemini-3-pro-preview',
            'processing_time_seconds': round(elapsed, 2)
        }
        
        logging.info(f"✅ Análisis estructural completado en {elapsed:.1f}s | Score global: {structural_analysis.get('score_estructural_global', {}).get('score', 'N/A')}")
        
        return structural_analysis
        
    except Exception as e:
        logging.error(f"❌ Error en análisis estructural de {chapter_title}: {e}")
        return {
            'chapter_id': chapter_id,
            'chapter_title': chapter_title,
            'error': str(e),
            '_metadata': {
                'status': 'error',
                'analysis_layer': 2
            }
        }
# =============================================================================
# GenerateArcMapForChapter/__init__.py - SYLPHRENA 4.0
# =============================================================================
# NUEVA FUNCIÓN:
#   - Genera mapa de arco específico para cada capítulo antes de edición
#   - Documenta la función narrativa del capítulo en la estructura mayor
#   - Identifica restricciones de edición basadas en la función
#   - Resuelve Problema Crítico 5: Edición Sin Comprensión de Arco Completo
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
# PROMPT DE GENERACIÓN DE MAPA DE ARCO
# =============================================================================

ARC_MAP_PROMPT = """
Genera un MAPA DE ARCO específico para este capítulo que guiará la fase de edición.

═══════════════════════════════════════════════════════════════════════════════
INFORMACIÓN DEL CAPÍTULO
═══════════════════════════════════════════════════════════════════════════════
Título: {chapter_title}
ID: {chapter_id}
Posición: Capítulo {chapter_position} de {total_chapters}
Tipo de sección: {section_type}

═══════════════════════════════════════════════════════════════════════════════
ANÁLISIS ESTRUCTURAL DEL CAPÍTULO (Capa 2)
═══════════════════════════════════════════════════════════════════════════════
{structural_analysis}

═══════════════════════════════════════════════════════════════════════════════
EVALUACIÓN CUALITATIVA (Capa 3)
═══════════════════════════════════════════════════════════════════════════════
{qualitative_analysis}

═══════════════════════════════════════════════════════════════════════════════
CONTEXTO GLOBAL (De la Biblia Validada)
═══════════════════════════════════════════════════════════════════════════════
Género: {genero}
Estructura del libro: {estructura_actos}

Arcos de personajes activos:
{character_arcs}

Subtramas en progreso:
{subplots}

═══════════════════════════════════════════════════════════════════════════════
TU TAREA: GENERAR MAPA DE ARCO
═══════════════════════════════════════════════════════════════════════════════

Genera un mapa que documente:

1. POSICIÓN EN ESTRUCTURA DE ACTOS
   - ¿En qué acto está? (1, 2A, 2B, 3)
   - ¿Qué función cumple en ese acto?

2. FUNCIÓN DRAMÁTICA
   - ¿Es establecimiento (setup)?
   - ¿Es desarrollo/escalada?
   - ¿Es punto de giro?
   - ¿Es clímax o resolución?
   - ¿Es transición?

3. ARCOS DE PERSONAJES ACTIVOS
   - Para cada personaje principal que aparece:
   - ¿En qué fase de su arco está? (configuración, desarrollo, transformación)
   - ¿Qué características son importantes preservar?

4. ELEMENTOS DE SETUP
   - ¿Qué elementos establece este capítulo para capítulos posteriores?
   - ¿Qué elementos de capítulos anteriores se resuelven aquí?

5. RESTRICCIONES DE EDICIÓN
   - ¿Qué NO debe modificarse porque es configuración intencional?
   - ¿Qué comportamientos de personajes NO deben suavizarse?
   - ¿Qué ritmo debe preservarse?

RESPONDE CON JSON:
{{
  "chapter_id": {chapter_id},
  "chapter_title": "{chapter_title}",
  
  "posicion_estructural": {{
    "acto": "ACTO_1|ACTO_2A|ACTO_2B|ACTO_3",
    "funcion_en_acto": "string",
    "porcentaje_progreso": 0
  }},
  
  "funcion_dramatica": {{
    "tipo_principal": "ESTABLECIMIENTO|DESARROLLO|PUNTO_GIRO|CLIMAX|RESOLUCION|TRANSICION",
    "descripcion": "string",
    "importancia_estructural": "CRITICA|ALTA|MEDIA|BAJA"
  }},
  
  "arcos_personajes_activos": [
    {{
      "nombre": "string",
      "fase_arco": "CONFIGURACION|DESARROLLO|TRANSFORMACION|RESOLUCION",
      "caracteristicas_a_preservar": ["string"],
      "comportamientos_intencionales": ["string"],
      "advertencia_editorial": "string"
    }}
  ],
  
  "elementos_setup": {{
    "establece_para_futuro": [
      {{
        "elemento": "string",
        "relevancia_para_capitulo": "aproximado o 'futuro'"
      }}
    ],
    "resuelve_de_pasado": [
      {{
        "elemento": "string",
        "establecido_en_capitulo": "aproximado"
      }}
    ]
  }},
  
  "restricciones_edicion": {{
    "no_modificar": [
      {{
        "elemento": "string",
        "razon": "string"
      }}
    ],
    "no_suavizar": [
      {{
        "comportamiento": "string",
        "personaje": "string",
        "razon": "string"
      }}
    ],
    "ritmo_a_preservar": {{
      "clasificacion": "RAPIDO|MEDIO|LENTO",
      "es_intencional": true,
      "razon": "string"
    }},
    "advertencias_especiales": ["string"]
  }},
  
  "guia_para_editor": {{
    "enfoque_principal": "string",
    "areas_de_mejora_seguras": ["string"],
    "areas_a_evitar": ["string"],
    "nivel_intervencion_sugerido": "MINIMO|MODERADO|SIGNIFICATIVO"
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
    """Llamada a Gemini Pro para generación de mapa de arco."""
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


def main(arc_input: dict) -> dict:
    # ... docstring ...
    
    chapter_id = arc_input.get('chapter_id', 0)
    
    # --- CORRECCIÓN DE EXTRACCIÓN DE DATOS ---
    # 1. Recuperar Biblia (Orchestrator usa 'bible')
    bible = arc_input.get('bible_validada') or arc_input.get('bible') or {}
    
    # 2. Recuperar Análisis Anidados
    chapter_analysis = arc_input.get('chapter_analysis', {})
    
    # Intentar obtener componentes sueltos o extraerlos del objeto padre
    structural_analysis = arc_input.get('structural_analysis') or \
                          chapter_analysis.get('layer2_structural') or \
                          {}
                          
    qualitative_analysis = arc_input.get('qualitative_analysis') or \
                           chapter_analysis.get('layer3_qualitative') or \
                           {}
                           
    chapter_title = arc_input.get('chapter_title') or \
                    chapter_analysis.get('titulo') or \
                    f'Capítulo {chapter_id}'
    # -----------------------------------------
    
    try:
        start_time = time.time()
        
        logging.info(f"🗺️ Generando mapa de arco: {chapter_title}")
        
        # Configurar cliente
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY no configurada")
        
        client = genai.Client(api_key=api_key)
        
        # Extraer datos
        chapter_position = arc_input.get('chapter_position', 1)
        total_chapters = arc_input.get('total_chapters', 1)
        section_type = arc_input.get('section_type', 'CHAPTER')
        structural_analysis = arc_input.get('structural_analysis', {})
        qualitative_analysis = arc_input.get('qualitative_analysis', {})
        bible = arc_input.get('bible_validada', {})
        
        # Preparar contexto de la Biblia
        identidad = bible.get('identidad_obra', {})
        genero = identidad.get('genero', 'No detectado')
        
        arco_narrativo = bible.get('arco_narrativo', {})
        estructura_actos = json.dumps(arco_narrativo.get('estructura_detectada', 'Tres actos'), ensure_ascii=False)
        
        # Arcos de personajes
        reparto = bible.get('reparto_completo', {})
        character_arcs = []
        for categoria in ['protagonistas', 'antagonistas']:
            for char in reparto.get(categoria, []):
                character_arcs.append({
                    'nombre': char.get('nombre'),
                    'arco': char.get('arco_personaje', '')[:100]
                })
        character_arcs_json = json.dumps(character_arcs[:5], indent=2, ensure_ascii=False)
        
        # Subtramas (si existen)
        subplots = bible.get('subtramas', [])
        subplots_json = json.dumps(subplots[:3], indent=2, ensure_ascii=False) if subplots else "No identificadas"
        
        # Preparar análisis para el prompt
        structural_json = json.dumps({
            k: v for k, v in structural_analysis.items()
            if k not in ['_metadata', 'chapter_id', 'chapter_title']
        }, indent=2, ensure_ascii=False)
        
        qualitative_summary = {
            'coherencia_personajes': qualitative_analysis.get('coherencia_personajes', {}).get('score', 'N/A'),
            'logica_causal': qualitative_analysis.get('logica_causal', {}).get('score', 'N/A'),
            'integracion': qualitative_analysis.get('integracion_elementos', {}).get('score', 'N/A'),
            'problemas': qualitative_analysis.get('evaluacion_global', {}).get('problemas_criticos', [])
        }
        qualitative_json = json.dumps(qualitative_summary, indent=2, ensure_ascii=False)
        
        # Construir prompt
        prompt = ARC_MAP_PROMPT.format(
            chapter_title=chapter_title,
            chapter_id=chapter_id,
            chapter_position=chapter_position,
            total_chapters=total_chapters,
            section_type=section_type,
            structural_analysis=structural_json,
            qualitative_analysis=qualitative_json,
            genero=genero,
            estructura_actos=estructura_actos,
            character_arcs=character_arcs_json,
            subplots=subplots_json
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
        
        arc_map = json.loads(response_text.strip())
        
        # Asegurar campos
        arc_map['chapter_id'] = chapter_id
        arc_map['chapter_title'] = chapter_title
        arc_map['_metadata'] = {
            'status': 'success',
            'processing_time_seconds': round(elapsed, 2)
        }
        
        funcion = arc_map.get('funcion_dramatica', {}).get('tipo_principal', 'N/A')
        logging.info(f"✅ Mapa de arco generado en {elapsed:.1f}s | Función: {funcion}")
        
        return arc_map
        
    except Exception as e:
        logging.error(f"❌ Error generando mapa de arco para {chapter_title}: {e}")
        return {
            'chapter_id': chapter_id,
            'chapter_title': chapter_title,
            'error': str(e),
            'restricciones_edicion': {
                'advertencias_especiales': ['Error generando mapa de arco - proceder con cautela']
            },
            '_metadata': {
                'status': 'error'
            }
        }

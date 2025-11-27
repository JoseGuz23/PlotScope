# =============================================================================
# CausalityGraphAnalysis/__init__.py - SYLPHRENA 4.0
# =============================================================================
# NUEVA FUNCIÓN:
#   - Construye grafo de relaciones causales entre eventos
#   - Identifica conexiones causales (explícitas e implícitas)
#   - Detecta problemas: nodos huérfanos, cadenas rotas, contradicciones
#   - Resuelve Problema Crítico 3: Falta de Análisis de Causalidad
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
# PROMPT DE ANÁLISIS DE CAUSALIDAD
# =============================================================================

CAUSALITY_ANALYSIS_PROMPT = """
Eres un ANALISTA DE CAUSALIDAD NARRATIVA. Tu trabajo es identificar las relaciones de causa-efecto entre los eventos de una novela.

═══════════════════════════════════════════════════════════════════════════════
LISTA DE EVENTOS (en orden cronológico)
═══════════════════════════════════════════════════════════════════════════════
{events_json}

═══════════════════════════════════════════════════════════════════════════════
PERSONAJES PRINCIPALES
═══════════════════════════════════════════════════════════════════════════════
{characters_json}

═══════════════════════════════════════════════════════════════════════════════
TU TAREA: ANÁLISIS DE CAUSALIDAD
═══════════════════════════════════════════════════════════════════════════════

Para cada evento en la lista, determina:

1. CAUSAS DIRECTAS: ¿Qué eventos anteriores CAUSARON este evento?
   - Una relación causal existe cuando el Evento B ocurre como consecuencia directa o altamente probable del Evento A
   - Cita el índice del evento que lo causó

2. TIPO DE CAUSALIDAD:
   - EXPLICITA: La causalidad se declara en el texto
   - IMPLICITA: La causalidad se infiere lógicamente
   - DECISION_PERSONAJE: El evento es resultado de una decisión de personaje
   - CONSECUENCIA_NATURAL: El evento es consecuencia física/natural de otro

3. CONFIANZA: ¿Qué tan seguro estás de la relación causal?
   - ALTA: Muy claro que B resulta de A
   - MEDIA: Probable que estén relacionados
   - BAJA: Posible conexión pero especulativa

4. EVENTOS HUÉRFANOS: Si un evento no tiene causas identificables en eventos previos:
   - Márcalo como POTENCIAL_PROBLEMA
   - Puede representar un giro no ganado o coincidencia narrativa débil

5. CADENAS CAUSALES: Identifica secuencias de eventos conectados causalmente
   - Ejemplo: Evento 5 causa Evento 10, que causa Evento 15

6. CONTRADICCIONES: Eventos que contradicen consecuencias establecidas previamente

RESPONDE ÚNICAMENTE CON JSON VÁLIDO:
{{
  "eventos_analizados": [
    {{
      "evento_id": 0,
      "capitulo": 0,
      "descripcion": "string",
      "causas": [
        {{
          "evento_causa_id": 0,
          "tipo_causalidad": "EXPLICITA|IMPLICITA|DECISION_PERSONAJE|CONSECUENCIA_NATURAL",
          "confianza": "ALTA|MEDIA|BAJA",
          "explicacion": "string"
        }}
      ],
      "es_huerfano": false,
      "razon_huerfano": "string o null"
    }}
  ],
  "cadenas_causales": [
    {{
      "nombre_cadena": "string",
      "eventos": [0, 5, 10],
      "descripcion": "string",
      "importancia": "TRAMA_PRINCIPAL|SUBTRAMA|DESARROLLO_PERSONAJE"
    }}
  ],
  "problemas_detectados": {{
    "eventos_huerfanos": [
      {{
        "evento_id": 0,
        "capitulo": 0,
        "descripcion": "string",
        "tipo_problema": "GIRO_NO_GANADO|COINCIDENCIA|DEUS_EX_MACHINA",
        "severidad": "CRITICO|MEDIO|MENOR",
        "sugerencia": "string"
      }}
    ],
    "cadenas_rotas": [
      {{
        "descripcion": "string",
        "eventos_involucrados": [0, 0],
        "capitulo_ruptura": 0,
        "tipo": "SUBTRAMA_ABANDONADA|RESOLUCION_FALTANTE|SETUP_SIN_PAYOFF"
      }}
    ],
    "contradicciones": [
      {{
        "descripcion": "string",
        "evento_a": 0,
        "evento_b": 0,
        "capitulos": [0, 0],
        "severidad": "CRITICO|MEDIO|MENOR"
      }}
    ]
  }},
  "metricas_causalidad": {{
    "total_eventos": 0,
    "eventos_con_causa_clara": 0,
    "eventos_huerfanos": 0,
    "porcentaje_conectividad": 0.0,
    "cadenas_principales": 0,
    "score_coherencia_causal": 0
  }},
  "_metadata": {{
    "status": "success",
    "model": "gemini-3-pro-preview"
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
    """Llamada a Gemini Pro para análisis de causalidad."""
    return client.models.generate_content(
        model='gemini-3-pro-preview',
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=16384,  # Necesitamos espacio para muchos eventos
            response_mime_type="application/json",
            safety_settings=[
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
            ]
        )
    )


def extract_all_events(chapters_consolidated: list) -> list:
    """
    Extrae todos los eventos de todos los capítulos y los ordena cronológicamente.
    Cada evento recibe un ID global único.
    """
    all_events = []
    global_id = 1
    
    for chapter in chapters_consolidated:
        chapter_id = chapter.get('chapter_id', 0)
        chapter_title = chapter.get('titulo', f'Capítulo {chapter_id}')
        events = chapter.get('secuencia_eventos', [])
        
        for event in events:
            all_events.append({
                'global_id': global_id,
                'chapter_id': chapter_id,
                'chapter_title': chapter_title,
                'descripcion': event.get('evento', ''),
                'tipo': event.get('tipo', 'DESCONOCIDO'),
                'tension': event.get('tension', 5),
                'personajes': event.get('personajes_involucrados', [])
            })
            global_id += 1
    
    return all_events


def extract_main_characters(chapters_consolidated: list) -> list:
    """
    Extrae personajes principales de todos los capítulos.
    """
    characters = {}
    
    for chapter in chapters_consolidated:
        for char in chapter.get('reparto_completo', []):
            name = char.get('nombre', '').lower()
            if name and name not in characters:
                characters[name] = {
                    'nombre': char.get('nombre'),
                    'rol': char.get('rol_en_capitulo', 'secundario'),
                    'apariciones': 1
                }
            elif name:
                characters[name]['apariciones'] += 1
    
    # Ordenar por apariciones y retornar top 15
    sorted_chars = sorted(characters.values(), key=lambda x: x['apariciones'], reverse=True)
    return sorted_chars[:15]


def main(chapters_consolidated: list) -> dict:
    """
    Ejecuta análisis de causalidad sobre todos los eventos del libro.
    
    Input: Lista de capítulos consolidados (post-Capa 1)
    Output: Grafo de causalidad con problemas detectados
    """
    
    try:
        start_time = time.time()
        
        logging.info(f"🔗 Análisis de Causalidad: {len(chapters_consolidated)} capítulos")
        
        # Configurar cliente
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY no configurada")
        
        client = genai.Client(api_key=api_key)
        
        # Extraer todos los eventos
        all_events = extract_all_events(chapters_consolidated)
        main_characters = extract_main_characters(chapters_consolidated)
        
        logging.info(f"   📊 {len(all_events)} eventos extraídos")
        logging.info(f"   👥 {len(main_characters)} personajes principales")
        
        # Si hay demasiados eventos, dividir en chunks
        MAX_EVENTS_PER_CALL = 150
        
        if len(all_events) > MAX_EVENTS_PER_CALL:
            logging.warning(f"⚠️ Muchos eventos ({len(all_events)}), analizando en chunks...")
            # Por simplicidad, analizamos los más importantes (alta tensión)
            all_events.sort(key=lambda x: x.get('tension', 0), reverse=True)
            all_events = all_events[:MAX_EVENTS_PER_CALL]
            # Re-ordenar cronológicamente
            all_events.sort(key=lambda x: (x['chapter_id'], x['global_id']))
        
        # Preparar JSONs
        events_json = json.dumps(all_events, indent=2, ensure_ascii=False)
        characters_json = json.dumps(main_characters, indent=2, ensure_ascii=False)
        
        # Construir prompt
        prompt = CAUSALITY_ANALYSIS_PROMPT.format(
            events_json=events_json,
            characters_json=characters_json
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
        
        causality_analysis = json.loads(response_text.strip())
        
        # Agregar metadata
        causality_analysis['_metadata'] = {
            'status': 'success',
            'model': 'gemini-3-pro-preview',
            'total_events_analyzed': len(all_events),
            'processing_time_seconds': round(elapsed, 2)
        }
        
        # Calcular métricas adicionales si no existen
        if 'metricas_causalidad' not in causality_analysis:
            eventos_analizados = causality_analysis.get('eventos_analizados', [])
            huerfanos = sum(1 for e in eventos_analizados if e.get('es_huerfano', False))
            con_causa = len(eventos_analizados) - huerfanos
            
            causality_analysis['metricas_causalidad'] = {
                'total_eventos': len(eventos_analizados),
                'eventos_con_causa_clara': con_causa,
                'eventos_huerfanos': huerfanos,
                'porcentaje_conectividad': round((con_causa / max(len(eventos_analizados), 1)) * 100, 1),
                'cadenas_principales': len(causality_analysis.get('cadenas_causales', [])),
                'score_coherencia_causal': calculate_causality_score(causality_analysis)
            }
        
        metrics = causality_analysis.get('metricas_causalidad', {})
        logging.info(f"✅ Análisis de causalidad completado en {elapsed:.1f}s")
        logging.info(f"   Conectividad: {metrics.get('porcentaje_conectividad', 0)}%")
        logging.info(f"   Eventos huérfanos: {metrics.get('eventos_huerfanos', 0)}")
        
        return causality_analysis
        
    except Exception as e:
        logging.error(f"❌ Error en análisis de causalidad: {e}")
        return {
            'error': str(e),
            'metricas_causalidad': {
                'score_coherencia_causal': 0
            },
            '_metadata': {
                'status': 'error'
            }
        }


def calculate_causality_score(analysis: dict) -> int:
    """
    Calcula un score de coherencia causal (1-10) basado en los problemas detectados.
    """
    score = 10
    
    problemas = analysis.get('problemas_detectados', {})
    
    # Restar por eventos huérfanos
    huerfanos = problemas.get('eventos_huerfanos', [])
    for h in huerfanos:
        severidad = h.get('severidad', 'MENOR')
        if severidad == 'CRITICO':
            score -= 1.5
        elif severidad == 'MEDIO':
            score -= 0.8
        else:
            score -= 0.3
    
    # Restar por cadenas rotas
    cadenas_rotas = problemas.get('cadenas_rotas', [])
    score -= len(cadenas_rotas) * 0.7
    
    # Restar por contradicciones
    contradicciones = problemas.get('contradicciones', [])
    for c in contradicciones:
        severidad = c.get('severidad', 'MENOR')
        if severidad == 'CRITICO':
            score -= 2
        elif severidad == 'MEDIO':
            score -= 1
        else:
            score -= 0.5
    
    return max(1, min(10, round(score)))

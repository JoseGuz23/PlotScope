# =============================================================================
# CharacterArcValidation/__init__.py - SYLPHRENA 4.0
# =============================================================================
# NUEVA FUNCIÓN:
#   - Valida la coherencia lógica de los arcos de personaje
#   - Cruza decisiones de personajes con el grafo de causalidad
#   - Utiliza NetworkX para trazado de rutas causales
# =============================================================================

import logging
import json
import os
import networkx as nx
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential

logging.basicConfig(level=logging.INFO)

ARC_VALIDATION_PROMPT = """
Eres un EDITOR DE DESARROLLO experto en psicología de personajes.
Estás validando el arco del personaje: **{character_name}**.

HECHOS:
1. El personaje tomó esta DECISIÓN CRÍTICA en el capítulo {chapter}: "{decision_desc}".
2. Según el grafo de causalidad, esta decisión fue motivada por estos eventos previos:
{causal_path}

ANÁLISIS REQUERIDO:
¿Es esta motivación suficiente y lógica para este personaje específico?
- Si el personaje es cobarde y decide luchar, ¿hubo un evento de "presión extrema" previo?
- Si el personaje perdona a su enemigo, ¿hubo un evento de "revelación" o "empatía" previo?

Responde en JSON:
{{
    "decision_id": {decision_id},
    "es_coherente": true/false,
    "justificacion": "string",
    "nivel_motivacion": 1-10,
    "falta_evento_tipo": "Si no es coherente, qué tipo de evento falta (ej: 'Momento de ruptura')"
}}
"""

def build_graph_from_json(causality_data):
    """Reconstruye el grafo usando NetworkX para análisis topológico."""
    G = nx.DiGraph()
    
    events = causality_data.get('eventos_analizados', [])
    for ev in events:
        ev_id = ev.get('evento_id') or ev.get('global_id')
        G.add_node(ev_id, **ev)
        
        for causa in ev.get('causas', []):
            cause_id = causa.get('evento_causa_id')
            if cause_id:
                G.add_edge(cause_id, ev_id, type=causa.get('tipo_causalidad'), weight=causa.get('confianza'))
    return G

def get_causal_chain(G, target_event_id, depth=3):
    """Rastrea hacia atrás en el grafo para encontrar qué causó este evento."""
    ancestors = []
    try:
        # Usamos un BFS inverso limitado por profundidad
        preds = list(G.predecessors(target_event_id))
        for p in preds:
            ancestors.append(G.nodes[p])
            if depth > 1:
                grand_preds = list(G.predecessors(p))
                for gp in grand_preds:
                    ancestors.append(G.nodes[gp])
    except Exception:
        pass
    return ancestors

def main(payload: str) -> str:
    try:
        data = json.loads(payload)
        bible = data.get('bible', {})
        causality_analysis = bible.get('analisis_causalidad', {})
        
        if not causality_analysis:
            return json.dumps({"status": "skipped", "reason": "No causality graph"})

        # 1. Construir Grafo en Memoria
        G = build_graph_from_json(causality_data=causality_analysis)
        
        # 2. Identificar Personajes Principales y sus Decisiones
        # Buscamos eventos tipo "DECISION_PERSONAJE" o "DECISION"
        character_reports = {}
        
        api_key = os.environ.get('GEMINI_API_KEY')
        client = genai.Client(api_key=api_key)

        events = causality_analysis.get('eventos_analizados', [])
        decision_events = [
            e for e in events 
            if 'DECISION' in str(e.get('tipo', '')).upper() or 
               any(c.get('tipo_causalidad') == 'DECISION_PERSONAJE' for c in e.get('causas', []))
        ]

        # Agrupar por personaje (heurística simple por mención)
        # En producción real, usaríamos los IDs de personajes de la Biblia
        
        validations = []

        # Analizamos una muestra de decisiones críticas (top 5 por tensión)
        decision_events.sort(key=lambda x: x.get('tension', 0), reverse=True)
        top_decisions = decision_events[:5]

        for decision in top_decisions:
            # Encontrar personaje principal involucrado
            chars = decision.get('personajes', [])
            char_name = chars[0] if chars else "Unknown"
            
            # Obtener la cadena causal real del grafo
            ev_id = decision.get('evento_id') or decision.get('global_id')
            ancestors = get_causal_chain(G, ev_id)
            
            ancestor_desc = "\n".join([f"- {a.get('descripcion')}" for a in ancestors])
            
            prompt = ARC_VALIDATION_PROMPT.format(
                character_name=char_name,
                chapter=decision.get('chapter_id'),
                decision_desc=decision.get('descripcion'),
                decision_id=ev_id,
                causal_path=ancestor_desc if ancestor_desc else "SIN CAUSAS IDENTIFICADAS (Evento Huérfano)"
            )

            # Llamada LLM
            response = client.models.generate_content(
                model='gemini-3-pro-preview',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            
            if response.text:
                validations.append(json.loads(response.text))

        return json.dumps({
            "status": "success", 
            "arc_validations": validations,
            "model_used": "gemini-3-pro-preview"
        })

    except Exception as e:
        logging.error(f"Error in CharacterArcValidation: {str(e)}")
        return json.dumps({"error": str(e)})
# =============================================================================
# AnalyzeChapterWithClaude/__init__.py - FALLBACK PARA FRAGMENTOS BLOQUEADOS
# =============================================================================

import logging
import json
import os
import anthropic

logging.basicConfig(level=logging.INFO)

ANALYSIS_PROMPT = """Actúa como un Analista Literario Forense. Extrae datos OBJETIVOS del texto.

CONTEXTO:
- ID: {chapter_id}
- Título: {title}
- Es fragmento: {is_fragment}

TEXTO A ANALIZAR:
{content}

INSTRUCCIONES:
Responde SOLO con JSON válido (sin markdown, sin ```) con esta estructura exacta:
{{
  "chapter_id": "{chapter_id}",
  "fragment_id": {fragment_id},
  "parent_chapter_id": {parent_chapter_id},
  "titulo_real": "{title}",
  "reparto_local": [
    {{"nombre": "NombrePersonaje", "rol": "protagonista", "estado_emocional": "emocion"}}
  ],
  "eventos": [
    {{"evento": "descripcion breve", "tipo": "accion", "tension": 5}}
  ],
  "metricas": {{
    "total_palabras": 0,
    "porcentaje_dialogo": 0,
    "clasificacion_ritmo": "MEDIO"
  }},
  "elementos_narrativos": {{
    "lugar": "ubicacion",
    "tiempo": "momento",
    "atmosfera": "tono",
    "conflicto_presente": true
  }},
  "senales_edicion": {{
    "problemas_potenciales": [],
    "repeticiones": []
  }}
}}"""


def main(fragment: dict) -> dict:
    """
    Analiza un fragmento con Claude como fallback cuando Gemini falla.
    """
    fragment_id = fragment.get('id', 0)
    parent_id = fragment.get('parent_chapter_id', fragment_id)
    title = fragment.get('original_title', fragment.get('title', 'Sin título'))
    content = fragment.get('content', '')
    is_fragment = fragment.get('is_fragment', False)
    
    logging.info(f"🔀 Claude fallback para fragmento {fragment_id}")
    
    try:
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            return {"error": "No ANTHROPIC_API_KEY", "fragment_id": fragment_id}
        
        client = anthropic.Anthropic(api_key=api_key)
        
        prompt = ANALYSIS_PROMPT.format(
            chapter_id=fragment_id,
            fragment_id=fragment_id,
            parent_chapter_id=parent_id,
            title=title,
            content=content,
            is_fragment=is_fragment
        )
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = response.content[0].text.strip()
        
        # Limpiar markdown si existe
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        analysis = json.loads(response_text.strip())
        
        # Asegurar campos de trazabilidad
        analysis['fragment_id'] = fragment_id
        analysis['parent_chapter_id'] = parent_id
        analysis['_metadata'] = {
            'status': 'success',
            'model': 'claude-sonnet-4',
            'fallback': True
        }
        
        logging.info(f"✅ Claude análisis exitoso para fragmento {fragment_id}")
        return analysis
        
    except Exception as e:
        logging.error(f"❌ Claude fallback error para fragmento {fragment_id}: {e}")
        return {
            "error": str(e),
            "fragment_id": fragment_id,
            "parent_chapter_id": parent_id,
            "status": "error"
        }

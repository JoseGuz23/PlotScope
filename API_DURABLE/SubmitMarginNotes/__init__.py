# =============================================================================
# SubmitMarginNotes/__init__.py - LYA 6.0 (Vertex AI Migration)
# =============================================================================
# MIGRACIÓN VERTEX AI: Generación de notas de margen usando Vertex AI Batch.
# Adapta prompts para incluir identificación explícita en el output.
# =============================================================================

import logging
import json
import os
import sys
import uuid
from typing import Dict, List, Any

# Agregar directorio padre para importar vertex_utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
try:
    from vertex_utils import submit_vertex_batch_job, upload_jsonl_to_gcs, format_claude_vertex_request
    from config_models import CLAUDE_SONNET_MODEL
except ImportError:
    from API_DURABLE.vertex_utils import submit_vertex_batch_job, upload_jsonl_to_gcs, format_claude_vertex_request
    from API_DURABLE.config_models import CLAUDE_SONNET_MODEL

logging.basicConfig(level=logging.INFO)

# -----------------------------------------------------------------------------
# PROMPTS
# -----------------------------------------------------------------------------

STATIC_SYSTEM_INSTRUCTIONS = """Eres un EDITOR PROFESIONAL. Tu tarea es generar NOTAS DE MARGEN para el libro "{libro}".

═══════════════════════════════════════════════════════════════════════════════
CONTEXTO EDITORIAL (de la carta editorial):
═══════════════════════════════════════════════════════════════════════════════
{contexto_editorial}

═══════════════════════════════════════════════════════════════════════════════
TIPOS DE NOTAS A GENERAR:
═══════════════════════════════════════════════════════════════════════════════
1. **PACING**: Donde el ritmo no funciona (muy lento/rápido).
2. **PERSONAJE**: Inconsistencias o falta de profundidad.
3. **DIALOGO**: Problemas de naturalidad o "infodumping".
4. **CLARIDAD**: Confusión espacial o temporal.
5. **EMOCION**: Falta de impacto emocional requerido.
6. **VOZ**: Inconsistencias de tono.
7. **TENSION**: Falta de conflicto o resolución fácil.
8. **SHOW_TELL**: Explicar en lugar de mostrar.

═══════════════════════════════════════════════════════════════════════════════
INSTRUCCIONES DE SALIDA:
═══════════════════════════════════════════════════════════════════════════════
1. Lee el fragmento proporcionado por el usuario.
2. Identifica 5-15 puntos de mejora crítica.
3. Prioriza notas con IMPACTO REAL en la narrativa.
4. RESPONDE ÚNICAMENTE CON JSON VÁLIDO con el siguiente formato:

{{
    "id_referencia": "DEBE_COINCIDIR_CON_INPUT",
    "notas_margen": [
        {{
            "nota_id": "chID-nota-001",
            "parrafo_aprox": N,
            "texto_referencia": "Primeras 10-15 palabras...",
            "tipo": "categoria",
            "severidad": "alta|media|baja",
            "nota": "Problema...",
            "sugerencia": "Solución...",
            "impacto_si_no_se_corrige": "Consecuencia..."
        }}
    ],
    "resumen_capitulo": {{
        "fortaleza_principal": "...",
        "problema_principal": "...",
        "prioridad_revision": "alta|media|baja"
    }}
}}
"""

CHAPTER_USER_PROMPT = """Analiza el siguiente capítulo basándote en las instrucciones.

IMPORTANTE: En tu respuesta JSON, el campo "id_referencia" DEBE SER EXACTAMENTE: "{chapter_id}"

INFORMACIÓN DEL CAPÍTULO:
- Título: {titulo}
- ID Referencia: {chapter_id}
- Función narrativa prevista: {funcion}
- Personajes presentes: {personajes}

TEXTO DEL CAPÍTULO:
═══════════════════════════════════════════════════════════════════════════════
{contenido}
═══════════════════════════════════════════════════════════════════════════════
"""

def main(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Envía capítulos a Vertex AI Batch.
    """
    try:
        chapters = input_data.get('chapters', [])
        carta = input_data.get('carta_editorial', {})
        bible = input_data.get('bible', {})
        book_metadata = input_data.get('book_metadata', {})
        
        libro_titulo = book_metadata.get('title', bible.get('identidad_obra', {}).get('titulo', 'Sin título'))
        
        logging.info(f"📝 Preparando notas de margen (Vertex AI) para {len(chapters)} capítulos.")
        
        batch_requests = []
        chapter_metadata = {}
        
        # 1. Preparar el contenido estático
        contexto_editorial_str = extraer_contexto_editorial(carta, bible)
        
        system_content = STATIC_SYSTEM_INSTRUCTIONS.format(
            libro=libro_titulo,
            contexto_editorial=contexto_editorial_str
        )

        # 2. Iterar capítulos y construir requests
        for chapter in chapters:
            ch_id = str(chapter.get('id', chapter.get('chapter_id', '?')))
            parent_id = chapter.get('parent_chapter_id', ch_id)
            
            chapter_metadata[ch_id] = {
                'fragment_id': chapter.get('id', 0),
                'parent_chapter_id': parent_id,
                'original_title': chapter.get('title', chapter.get('original_title', 'Sin título')),
                'content': chapter.get('content', '') # Para fallback
            }
            
            # Datos dinámicos
            notas_cap = ""
            for nota in carta.get('notas_por_capitulo', []):
                if str(nota.get('capitulo')) == str(parent_id):
                    notas_cap = f"Función: {nota.get('funcion', '')}. Mejorar: {nota.get('que_mejorar', '')}"
                    break
            
            personajes = extraer_personajes_capitulo(bible, parent_id)
            
            user_content = CHAPTER_USER_PROMPT.format(
                titulo=chapter.get('title', chapter.get('original_title', 'Sin título')),
                chapter_id=ch_id,
                funcion=notas_cap or "No especificada",
                personajes=", ".join(personajes) if personajes else "No especificados",
                contenido=chapter.get('content', '')
            )
            
            request = format_claude_vertex_request(
                messages=[{"role": "user", "content": user_content}],
                system=system_content,
                max_tokens=4000,
                temperature=0.5
            )
            batch_requests.append(request)
        
        logging.info(f"📦 Subiendo {len(batch_requests)} requests a GCS")
        
        batch_filename = f"claude_notes_batch_{uuid.uuid4()}.jsonl"
        source_uri = upload_jsonl_to_gcs(batch_requests, batch_filename)
        
        timestamp = uuid.uuid4().hex[:8]
        destination_prefix = f"claude_notes_results_{timestamp}"
        
        # Submit Job
        model_name = CLAUDE_SONNET_MODEL
        job_id = submit_vertex_batch_job(
            model_name=model_name,
            source_uri=source_uri,
            destination_uri_prefix=destination_prefix,
            job_display_name=f"lya-notes-{timestamp}"
        )
        
        logging.info(f"✅ Batch Vertex AI iniciado: {job_id}")
        
        return {
            "batch_id": job_id,
            "chapters_count": len(chapters),
            "status": "submitted",
            "chapter_metadata": chapter_metadata,
            "provider": "vertex_ai"
        }
        
    except Exception as e:
        logging.error(f"❌ Error crítico: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return {"error": str(e), "status": "error"}


def extraer_contexto_editorial(carta: Dict, bible: Dict) -> str:
    """Extrae contexto relevante de la carta editorial."""
    contexto = []
    areas = carta.get('areas_de_oportunidad', [])
    if areas:
        contexto.append("PROBLEMAS PRINCIPALES DEL LIBRO:")
        for area in areas[:5]:
            if area.get('prioridad') in ['ALTA', 'MEDIA']:
                cat = area.get('categoria', '').upper()
                prob = area.get('problema', '')[:120]
                contexto.append(f"- [{cat}] {prob}")
    
    voz = bible.get('voz_del_autor', {})
    if voz.get('NO_CORREGIR'):
        contexto.append("\nELEMENTOS A PRESERVAR (VOZ):")
        for item in voz['NO_CORREGIR'][:3]:
            contexto.append(f"- {item}")
    
    contexto.append(f"\nESTILO GENERAL: {voz.get('estilo_detectado', 'Estándar')}")
    
    return "\n".join(contexto)


def extraer_personajes_capitulo(bible: Dict, chapter_id) -> List[str]:
    """Extrae personajes relevantes para un capítulo."""
    personajes = []
    reparto = bible.get('reparto_completo', {})
    try:
        ch_num = int(chapter_id)
    except:
        ch_num = 0
    for tipo in ['protagonistas', 'antagonistas', 'secundarios']:
        for p in reparto.get(tipo, []):
            caps = p.get('capitulos_clave', [])
            if not caps or ch_num in caps:
                personajes.append(p.get('nombre', 'Personaje'))
    return personajes[:6]

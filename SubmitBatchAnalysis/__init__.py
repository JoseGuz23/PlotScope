# =============================================================================
# SubmitBatchAnalysis/__init__.py
# =============================================================================
# 
# USA LA GEMINI BATCH API (50% descuento)
# Solo necesita: GEMINI_API_KEY (ya lo tienes)
#
# NO necesita:
#   - Google Cloud Storage
#   - Service Account JSON
#   - GCP_PROJECT_ID
#
# =============================================================================

import logging
import json
import os

def main(chapters: list) -> dict:
    """
    Envía todos los capítulos a Gemini Batch API.
    
    Input: Lista de capítulos [{id, title, content}, ...]
    Output: {batch_job_name, chapters_count, status}
    """
    try:
        from google import genai
        
        # ─────────────────────────────────────────────────────────────────
        # A. CONFIGURACIÓN
        # ─────────────────────────────────────────────────────────────────
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return {"error": "GEMINI_API_KEY no configurada", "status": "config_error"}
        
        logging.info(f"📦 Preparando batch de {len(chapters)} capítulos...")
        
        # Crear cliente
        client = genai.Client(api_key=api_key)

        # 🆕 GUARDAR ORDEN DE IDs
        ordered_ids = [str(ch.get('id', '?')) for ch in chapters]
        logging.info(f"📋 IDs en orden: {ordered_ids[:5]}...")
        
        # ─────────────────────────────────────────────────────────────────
        # B. PREPARAR REQUESTS INLINE
        # ─────────────────────────────────────────────────────────────────
        batch_requests = []
        
        for chapter in chapters:
            chapter_id = chapter.get('id', 0)
            title = chapter.get('title', 'Sin título')
            content = chapter.get('content', '')
            is_fragment = chapter.get('is_fragment', False)
            
            prompt = build_analysis_prompt(chapter_id, title, content, is_fragment)
            
            # Formato para Batch API inline
            request = {
                "contents": [{
                    "parts": [{"text": prompt}],
                    "role": "user"
                }]
            }
            batch_requests.append(request)
        
        logging.info(f"📝 {len(batch_requests)} requests preparados")
        
        # ─────────────────────────────────────────────────────────────────
        # C. CREAR BATCH JOB
        # ─────────────────────────────────────────────────────────────────
        import time
        timestamp = int(time.time())
        
        logging.info("🚀 Enviando a Gemini Batch API...")
        
        batch_job = client.batches.create(
            model="models/gemini-2.5-flash",
            src=batch_requests,
            config={
                "display_name": f"sylphrena-{timestamp}",
            }
        )
        
        logging.info(f"✅ Batch Job creado: {batch_job.name}")
        logging.info(f"   Estado: {batch_job.state}")
        
        return {
            "batch_job_name": batch_job.name,
            "chapters_count": len(chapters),
            "status": "submitted",
            "state": str(batch_job.state) if batch_job.state else "PENDING",
            "id_map": ordered_ids  # 🆕 MAPA DE IDs
        }
    
    except ImportError as e:
        logging.error(f"❌ SDK no instalado: {e}")
        return {
            "error": "Instala: pip install google-genai",
            "status": "import_error"
        }
    except Exception as e:
        logging.error(f"❌ Error creando batch: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return {
            "error": str(e),
            "status": "error"
        }


def build_analysis_prompt(chapter_id, title, content, is_fragment):
    """Construye el prompt de análisis para un capítulo."""
    return f"""Actúa como un Analista Literario Forense. Extrae datos OBJETIVOS del texto.

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
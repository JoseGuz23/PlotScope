# =============================================================================
# SubmitBatchAnalysis/__init__.py - SYLPHRENA 4.0
# =============================================================================
import logging
import json
import os
import time
import tempfile
from google import genai

logging.basicConfig(level=logging.INFO)

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


def main(chapters: list) -> dict:
    """
    Envía todos los fragmentos a Gemini Batch API mediante archivo JSONL.
    """
    try:
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return {"error": "GEMINI_API_KEY no configurada", "status": "config_error"}
        
        logging.info(f"📦 Preparando batch de {len(chapters)} fragmentos...")
        
        client = genai.Client(api_key=api_key)
        
        jsonl_lines = []
        id_map = []
        
        for chapter in chapters:
            fragment_id = chapter.get('id', 'ID_NULO')
            parent_id = chapter.get('parent_chapter_id', 'PARENT_NULO')
            title = chapter.get('original_title', chapter.get('title', 'Sin título'))
            content = chapter.get('content', '')
            is_fragment = chapter.get('is_fragment', False)
            
            # Usamos "key" para correlación (estándar Google GenAI)
            key = f"frag_{fragment_id}_parent_{parent_id}"
            
            prompt = build_analysis_prompt(fragment_id, title, content, is_fragment)
            
            jsonl_entry = {
                "key": key,
                "request": {
                    "contents": [
                        {
                            "role": "user",
                            "parts": [{"text": prompt}]
                        }
                    ],
                    "generationConfig": {
                        "responseMimeType": "application/json"
                    }
                }
            }
            
            jsonl_lines.append(json.dumps(jsonl_entry, ensure_ascii=False))
            
            id_map.append({
                'key': key,
                'fragment_id': fragment_id,
                'parent_chapter_id': parent_id
            })
        
        logging.info(f"📝 {len(jsonl_lines)} requests preparados en formato JSONL")
        
        timestamp = int(time.time())
        temp_dir = tempfile.gettempdir()
        temp_filename = os.path.join(temp_dir, f"batch_requests_{timestamp}.jsonl")
        
        with open(temp_filename, 'w', encoding='utf-8') as f:
            for line in jsonl_lines:
                f.write(line + "\n")
        
        logging.info(f"📄 Archivo JSONL creado en: {temp_filename}")
        
        logging.info("☁️ Subiendo archivo a Google Files API...")
        
        uploaded_file = client.files.upload(
            file=temp_filename,
            config={
                'display_name': f"sylphrena-batch-{timestamp}",
                'mime_type': "application/jsonl"
            }
        )
        
        logging.info(f"✅ Archivo subido: {uploaded_file.name}")
        
        logging.info("🚀 Creando Batch Job...")
        
        # USO MODELO CONFIRMADO POR EL USUARIO: gemini-2.5-flash
        batch_job = client.batches.create(
            model="models/gemini-2.5-flash",
            src=uploaded_file.name,
            config={
                'display_name': f"sylphrena-analysis-{timestamp}"
            }
        )
        
        logging.info(f"✅ Batch Job creado: {batch_job.name}")
        logging.info(f"📊 Estado inicial: {batch_job.state}")
        
        try:
            os.remove(temp_filename)
        except:
            pass
        
        return {
            "batch_job_name": batch_job.name,
            "uploaded_file_name": uploaded_file.name,
            "chapters_count": len(chapters),
            "status": "submitted",
            "state": str(batch_job.state),
            "id_map": id_map
        }
    
    except Exception as e:
        logging.error(f"❌ Error creando batch: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return {
            "error": str(e),
            "status": "error"
        }
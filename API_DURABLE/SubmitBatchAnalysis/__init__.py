# =============================================================================
# SubmitBatchAnalysis/__init__.py - LYA 7.0 (GEMINI FLASH BATCH)
# =============================================================================
# OPTIMIZACIÓN:
# - Uso de Gemini 2.5 Flash para máxima velocidad/costo en Batch.
# - Prompt estructurado con System Instruction implícito para mejor JSON.
# - Filtrado de capítulos vacíos para no gastar tokens inútiles.
# =============================================================================

import logging
import json
import os
import time
import tempfile
from google import genai
from google.genai import types

logging.basicConfig(level=logging.INFO)

# =============================================================================
# CONSTANTES DE MODELO
# =============================================================================
BATCH_MODEL_ID = "models/gemini-2.5-flash"

SYSTEM_INSTRUCTION_TEXT = """Actúa como un Analista Literario Forense.
Tu objetivo es extraer datos OBJETIVOS del texto proporcionado.
No opines, solo clasifica y cuenta.

Salida requerida: JSON crudo (sin bloques de código markdown)."""

ANALYSIS_TASK_TEMPLATE = """
CONTEXTO DEL FRAGMENTO:
- ID Referencia: {chapter_id}
- Título: {title}
- Tipo: {tipo_fragmento}

TEXTO A ANALIZAR:
{content}

---
INSTRUCCIONES DE EXTRACCIÓN:
Genera un objeto JSON con esta estructura exacta:
{{
  "chapter_id": "{chapter_id}",
  "titulo_real": "{title}",
  "reparto_local": [
    {{"nombre": "Nombre", "rol": "protagonista|antagonista|secundario", "estado_emocional": "breve descripción"}}
  ],
  "eventos": [
    {{"evento": "qué pasó", "tipo": "accion|dialogo|reflexion", "tension": 1-10}}
  ],
  "metricas": {{
    "total_palabras": 0, // Estimado
    "porcentaje_dialogo": 0, // Estimado 0-100
    "clasificacion_ritmo": "RAPIDO|MEDIO|LENTO"
  }},
  "elementos_narrativos": {{
    "lugar": "dónde ocurre",
    "tiempo": "cuándo ocurre",
    "atmosfera": "mood",
    "conflicto_presente": boolean,
    "gancho_final": boolean
  }},
  "senales_edicion": {{
    "problemas_potenciales": ["lista de problemas obvios"],
    "repeticiones": ["palabras repetidas excesivamente"],
    "instancias_tell_no_show": ["frases abstractas detectadas"]
  }}
}}
"""

def main(chapters: list) -> dict:
    """
    Envía fragmentos a Gemini Batch API (JSONL).
    """
    try:
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return {"error": "GEMINI_API_KEY no configurada", "status": "config_error"}
        
        # Filtrar capítulos vacíos para ahorrar dinero
        valid_chapters = [c for c in chapters if len(c.get('content', '')) > 50]
        if not valid_chapters:
            return {"error": "No hay capítulos válidos para analizar", "status": "empty_input"}

        logging.info(f"📦 Preparando batch para {len(valid_chapters)} fragmentos (Gemini Flash)...")
        
        client = genai.Client(api_key=api_key)
        
        jsonl_lines = []
        id_map = []
        
        for chapter in valid_chapters:
            fragment_id = str(chapter.get('id', 'ID_NULO'))
            parent_id = str(chapter.get('parent_chapter_id', fragment_id))
            title = chapter.get('original_title', chapter.get('title', 'Sin título'))
            content = chapter.get('content', '')
            is_fragment = chapter.get('is_fragment', False)
            tipo_frag = "Fragmento de Capítulo" if is_fragment else "Capítulo Completo"
            
            # Key única para correlación posterior
            key = f"frag_{fragment_id}_parent_{parent_id}"
            
            prompt = ANALYSIS_TASK_TEMPLATE.format(
                chapter_id=fragment_id,
                title=title,
                tipo_fragmento=tipo_frag,
                content=content
            )
            
            # Construcción del request para Batch
            # Nota: Batch API a veces prefiere system_instruction dentro del request
            jsonl_entry = {
                "key": key,
                "request": {
                    "contents": [
                        {"role": "user", "parts": [{"text": SYSTEM_INSTRUCTION_TEXT + "\n\n" + prompt}]}
                    ],
                    "generationConfig": {
                        "responseMimeType": "application/json",
                        "temperature": 0.1 # Determinista para datos factuales
                    }
                }
            }
            
            jsonl_lines.append(json.dumps(jsonl_entry, ensure_ascii=False))
            
            id_map.append({
                'key': key,
                'fragment_id': fragment_id,
                'parent_chapter_id': parent_id
            })
        
        # Crear archivo temporal JSONL
        timestamp = int(time.time())
        temp_dir = tempfile.gettempdir()
        temp_filename = os.path.join(temp_dir, f"lya_batch_{timestamp}.jsonl")
        
        with open(temp_filename, 'w', encoding='utf-8') as f:
            for line in jsonl_lines:
                f.write(line + "\n")
        
        logging.info(f"☁️ Subiendo {len(jsonl_lines)} items a Google Files...")
        
        uploaded_file = client.files.upload(
            file=temp_filename,
            config={'mime_type': "application/jsonl"}
        )
        
        logging.info(f"🚀 Iniciando Batch Job en {BATCH_MODEL_ID}...")
        
        batch_job = client.batches.create(
            model=BATCH_MODEL_ID,
            src=uploaded_file.name,
            config={
                'display_name': f"lya-analysis-{timestamp}"
            }
        )
        
        logging.info(f"✅ Batch Job ID: {batch_job.name}")
        
        # Limpieza
        try:
            os.remove(temp_filename)
        except:
            pass
        
        return {
            "batch_job_name": batch_job.name,
            "chapters_count": len(valid_chapters),
            "status": "submitted",
            "state": str(batch_job.state),
            "id_map": id_map,
            "model_used": BATCH_MODEL_ID
        }
    
    except Exception as e:
        logging.error(f"❌ Error en SubmitBatchAnalysis: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return {"error": str(e), "status": "error"}
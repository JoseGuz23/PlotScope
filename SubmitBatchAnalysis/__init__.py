# =============================================================================
# SubmitBatchAnalysis/__init__.py
# =============================================================================
# 
# REQUISITOS PARA QUE ESTO FUNCIONE:
# 
# 1. GOOGLE CLOUD PLATFORM:
#    - Crear proyecto en console.cloud.google.com
#    - Habilitar "Vertex AI API" y "Cloud Storage API"
#    - Crear bucket en Cloud Storage (ej: "sylphrena-batch-jobs")
#
# 2. CREDENCIALES:
#    - Crear Service Account con roles:
#      * "Vertex AI User"
#      * "Storage Object Admin"
#    - Descargar JSON de credenciales
#    - Subir a Azure Function App como variable de entorno
#
# 3. VARIABLES DE ENTORNO EN AZURE:
#    - GCP_PROJECT_ID: tu-proyecto-id
#    - GCP_BUCKET_NAME: sylphrena-batch-jobs
#    - GOOGLE_APPLICATION_CREDENTIALS_JSON: (contenido del JSON de credenciales)
#
# =============================================================================

import logging
import json
import os
import time

# Estas librerías necesitan instalarse:
# pip install google-cloud-storage google-cloud-aiplatform

def main(chapters: list) -> dict:
    """
    Envía todos los capítulos a Gemini Batch API.
    
    Input: Lista de capítulos [{id, title, content}, ...]
    Output: {batch_job_id, output_uri, chapters_count, status}
    """
    try:
        # ─────────────────────────────────────────────────────────────────
        # A. CONFIGURACIÓN
        # ─────────────────────────────────────────────────────────────────
        project_id = os.environ.get('GCP_PROJECT_ID')
        bucket_name = os.environ.get('GCP_BUCKET_NAME', f'{project_id}-sylphrena-batch')
        
        if not project_id:
            return {"error": "GCP_PROJECT_ID no configurado", "status": "config_error"}
        
        # Configurar credenciales desde variable de entorno
        creds_json = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_JSON')
        if creds_json:
            # Escribir credenciales a archivo temporal
            creds_path = '/tmp/gcp_credentials.json'
            with open(creds_path, 'w') as f:
                f.write(creds_json)
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        
        logging.info(f"📦 Preparando batch de {len(chapters)} capítulos...")
        logging.info(f"   Project: {project_id}")
        logging.info(f"   Bucket: {bucket_name}")
        
        # ─────────────────────────────────────────────────────────────────
        # B. IMPORTAR LIBRERÍAS DE GCP (después de configurar credenciales)
        # ─────────────────────────────────────────────────────────────────
        from google.cloud import storage
        from google.cloud import aiplatform
        
        # ─────────────────────────────────────────────────────────────────
        # C. PREPARAR ARCHIVO JSONL CON REQUESTS
        # ─────────────────────────────────────────────────────────────────
        requests_lines = []
        
        for chapter in chapters:
            chapter_id = chapter.get('id', 0)
            title = chapter.get('title', 'Sin título')
            content = chapter.get('content', '')
            is_fragment = chapter.get('is_fragment', False)
            
            prompt = build_analysis_prompt(chapter_id, title, content, is_fragment)
            
            # Formato JSONL para Batch API
            request = {
                "request": {
                    "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.2,
                        "maxOutputTokens": 8192,
                        "responseMimeType": "application/json"
                    }
                },
                "metadata": {
                    "chapter_id": str(chapter_id),
                    "title": title
                }
            }
            requests_lines.append(json.dumps(request, ensure_ascii=False))
        
        jsonl_content = '\n'.join(requests_lines)
        
        # ─────────────────────────────────────────────────────────────────
        # D. SUBIR A CLOUD STORAGE
        # ─────────────────────────────────────────────────────────────────
        storage_client = storage.Client(project=project_id)
        bucket = storage_client.bucket(bucket_name)
        
        timestamp = int(time.time())
        input_filename = f"inputs/batch-{timestamp}.jsonl"
        output_prefix = f"outputs/batch-{timestamp}/"
        
        blob = bucket.blob(input_filename)
        blob.upload_from_string(jsonl_content, content_type='application/jsonl')
        
        input_uri = f"gs://{bucket_name}/{input_filename}"
        output_uri = f"gs://{bucket_name}/{output_prefix}"
        
        logging.info(f"📤 Archivo subido: {input_uri}")
        
        # ─────────────────────────────────────────────────────────────────
        # E. CREAR BATCH JOB EN VERTEX AI
        # ─────────────────────────────────────────────────────────────────
        aiplatform.init(project=project_id, location="us-central1")
        
        # Usar BatchPredictionJob de Vertex AI
        batch_job = aiplatform.BatchPredictionJob.create(
            job_display_name=f"sylphrena-analysis-{timestamp}",
            model_name="publishers/google/models/gemini-1.5-flash",  # o gemini-2.5-flash cuando esté disponible
            gcs_source=input_uri,
            gcs_destination_prefix=output_uri,
            sync=False  # No esperar, retornar inmediatamente
        )
        
        logging.info(f"🚀 Batch Job creado: {batch_job.resource_name}")
        
        return {
            "batch_job_id": batch_job.resource_name,
            "batch_job_name": batch_job.display_name,
            "input_uri": input_uri,
            "output_uri": output_uri,
            "chapters_count": len(chapters),
            "status": "submitted"
        }
        
    except ImportError as e:
        logging.error(f"❌ Librerías de GCP no instaladas: {e}")
        return {
            "error": f"Instala: pip install google-cloud-storage google-cloud-aiplatform",
            "status": "import_error"
        }
    except Exception as e:
        logging.error(f"❌ Error creando batch: {str(e)}")
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
Responde SOLO con JSON válido con esta estructura:
{{
  "chapter_id": "{chapter_id}",
  "titulo_real": "{title}",
  "reparto_local": [
    {{"nombre": "...", "rol": "protagonista|secundario|mencionado", "estado_emocional": "..."}}
  ],
  "eventos": [
    {{"evento": "...", "tipo": "accion|dialogo|reflexion", "tension": 1-10}}
  ],
  "metricas": {{
    "total_palabras": 0,
    "porcentaje_dialogo": 0,
    "clasificacion_ritmo": "RAPIDO|MEDIO|LENTO"
  }},
  "elementos_narrativos": {{
    "lugar": "...",
    "tiempo": "...",
    "atmosfera": "...",
    "conflicto_presente": true/false
  }},
  "senales_edicion": {{
    "problemas_potenciales": ["..."],
    "repeticiones": ["..."]
  }}
}}"""
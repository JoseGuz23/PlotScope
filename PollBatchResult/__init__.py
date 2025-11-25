# =============================================================================
# PollBatchResult/__init__.py
# =============================================================================

import logging
import json
import os

def main(batch_info: dict) -> dict:
    """
    Consulta el estado de un Batch Job y descarga resultados si completó.
    
    Input: {batch_job_id, output_uri, ...}
    Output: 
        - Si completó: Lista de análisis JSON
        - Si procesando: {status: "processing", state: "..."}
        - Si falló: {status: "failed", error: "..."}
    """
    try:
        # ─────────────────────────────────────────────────────────────────
        # A. CONFIGURACIÓN
        # ─────────────────────────────────────────────────────────────────
        project_id = os.environ.get('GCP_PROJECT_ID')
        
        # Configurar credenciales
        creds_json = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_JSON')
        if creds_json:
            creds_path = '/tmp/gcp_credentials.json'
            with open(creds_path, 'w') as f:
                f.write(creds_json)
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        
        batch_job_id = batch_info.get('batch_job_id')
        output_uri = batch_info.get('output_uri')
        
        if not batch_job_id:
            return {"status": "error", "error": "No batch_job_id provided"}
        
        logging.info(f"🔄 Consultando batch: {batch_job_id}")
        
        # ─────────────────────────────────────────────────────────────────
        # B. IMPORTAR LIBRERÍAS
        # ─────────────────────────────────────────────────────────────────
        from google.cloud import aiplatform
        from google.cloud import storage
        
        aiplatform.init(project=project_id, location="us-central1")
        
        # ─────────────────────────────────────────────────────────────────
        # C. CONSULTAR ESTADO DEL JOB
        # ─────────────────────────────────────────────────────────────────
        job = aiplatform.BatchPredictionJob(batch_job_id)
        job_state = job.state.name
        
        logging.info(f"📊 Estado del job: {job_state}")
        
        # Estados posibles: PENDING, RUNNING, SUCCEEDED, FAILED, CANCELLED
        if job_state == "JOB_STATE_SUCCEEDED":
            # ─────────────────────────────────────────────────────────────
            # D. DESCARGAR RESULTADOS
            # ─────────────────────────────────────────────────────────────
            logging.info(f"✅ Job completado, descargando resultados...")
            
            storage_client = storage.Client(project=project_id)
            
            # Parsear URI: gs://bucket/path/
            bucket_name = output_uri.replace("gs://", "").split("/")[0]
            prefix = "/".join(output_uri.replace("gs://", "").split("/")[1:])
            
            bucket = storage_client.bucket(bucket_name)
            blobs = list(bucket.list_blobs(prefix=prefix))
            
            results = []
            for blob in blobs:
                if blob.name.endswith('.jsonl'):
                    content = blob.download_as_text()
                    for line in content.strip().split('\n'):
                        if line:
                            try:
                                response_obj = json.loads(line)
                                # Extraer la respuesta generada
                                generated_text = (
                                    response_obj.get('response', {})
                                    .get('candidates', [{}])[0]
                                    .get('content', {})
                                    .get('parts', [{}])[0]
                                    .get('text', '{}')
                                )
                                # Parsear el JSON de análisis
                                analysis = json.loads(generated_text)
                                results.append(analysis)
                            except json.JSONDecodeError as e:
                                logging.warning(f"Error parseando resultado: {e}")
                                continue
            
            logging.info(f"📥 Descargados {len(results)} análisis")
            return results  # Lista de análisis
            
        elif job_state == "JOB_STATE_FAILED":
            error_msg = str(job.error) if job.error else "Unknown error"
            logging.error(f"❌ Job falló: {error_msg}")
            return {"status": "failed", "error": error_msg}
            
        elif job_state == "JOB_STATE_CANCELLED":
            return {"status": "failed", "error": "Job was cancelled"}
            
        else:
            # PENDING o RUNNING
            return {
                "status": "processing",
                "state": job_state,
                "batch_job_id": batch_job_id
            }
            
    except ImportError as e:
        logging.error(f"❌ Librerías no instaladas: {e}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        logging.error(f"❌ Error consultando batch: {str(e)}")
        return {"status": "error", "error": str(e)}
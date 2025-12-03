# =============================================================================
# PollGeminiProBatchResult/__init__.py - DEBUG EDITION
# =============================================================================
import logging
import json
import os
import requests
from google import genai

logging.basicConfig(level=logging.INFO)

def main(batch_info: dict) -> dict:
    """
    Activity Function: Consulta estado de Batch Job.
    VERSIÓN ROBUSTA: Maneja errores de atributos y loguea la estructura real.
    """
    try:
        job_name = batch_info.get('batch_job_name')
        id_map = batch_info.get('id_map', [])
        
        if not job_name:
            return {'status': 'error', 'error': 'No batch_job_name provided'}

        api_key = os.environ.get('GEMINI_API_KEY')
        client = genai.Client(api_key=api_key)

        logging.info(f"🔍 Consultando: {job_name}")
        
        # 1. Obtener Job
        try:
            job = client.batches.get(name=job_name)
        except Exception as api_err:
            logging.error(f"❌ Error conectando con Google API: {api_err}")
            # Si falla la conexión, decimos 'processing' para que reintente luego
            return {'status': 'processing', 'batch_job_name': job_name, 'id_map': id_map}

        # Recuperar estado de forma segura
        state = getattr(job, 'state', None)
        if hasattr(state, 'name'): state = state.name # Si es un Enum, sacar el nombre
        
        logging.info(f"📊 Estado Google: {state}")

        # --- LÓGICA DE ESTADOS ---

        # CASO A: Aún trabajando (o estado desconocido que tratamos como espera)
        if state in ["JOB_STATE_NEW", "JOB_STATE_PENDING", "JOB_STATE_PROCESSING", None]:
            return {
                'status': 'processing', 
                'batch_job_name': job_name,
                'id_map': id_map
            }

        # CASO B: Fallo definitivo
        if state in ["JOB_STATE_FAILED", "JOB_STATE_CANCELLED"]:
            return {
                'status': 'failed',
                'error': f"Google Batch falló con estado: {state}"
            }

        # CASO C: Éxito -> Descargar resultados
        if state == "JOB_STATE_SUCCEEDED":
            logging.info("✅ Batch completado. Buscando archivo de salida...")
            
            # --- DEBUGGING EXTREMO (Para ver por qué fallaba) ---
            logging.info(f"🕵️ OBJETO JOB RAW: {job}")
            logging.info(f"🕵️ ATRIBUTOS DISPONIBLES: {dir(job)}")
            # -----------------------------------------------------

            # Intentar obtener el nombre del archivo de varias formas
            output_file_name = getattr(job, 'output_file', None)
            
            # Si no está como atributo, buscar en diccionario (si aplica)
            if not output_file_name and hasattr(job, 'to_dict'):
                 output_file_name = job.to_dict().get('output_file')
            
            # Si sigue vacío, lanzar error pero con info útil
            if not output_file_name:
                raise Exception(f"El job terminó pero no encuentro 'output_file'. Revisa los logs 'ATRIBUTOS DISPONIBLES'.")

            logging.info(f"📥 Descargando archivo: {output_file_name}")
            
            # Descargar contenido
            file_content_bytes = client.files.content(name=output_file_name)
            content_str = file_content_bytes.decode('utf-8')
            
            results = []
            
            for line in content_str.strip().split('\n'):
                if not line.strip(): continue
                try:
                    row = json.loads(line)
                    custom_id = row.get('custom_id')
                    
                    # Extraer body con seguridad
                    response_part = row.get('response', {})
                    # A veces viene en 'body', a veces directo, depende del modelo
                    resp_body = response_part.get('body', {})
                    
                    # Si es string JSON, parsearlo
                    if isinstance(resp_body, str):
                         try:
                             resp_body = json.loads(resp_body)
                         except:
                             pass # Dejarlo como string si falla
                    
                    # Unir con metadatos
                    meta = next((x for x in id_map if x['key'] == custom_id), {})
                    
                    # Si resp_body es dict, hacemos merge. Si no, lo asignamos a un campo 'result'
                    if isinstance(resp_body, dict):
                        final_item = {**meta, **resp_body}
                    else:
                        final_item = {**meta, 'raw_result': resp_body}
                        
                    results.append(final_item)
                    
                except Exception as parse_e:
                    logging.error(f"⚠️ Error línea JSONL: {parse_e}")

            logging.info(f"✅ {len(results)} resultados procesados.")
            return {
                'status': 'success',
                'total': len(results),
                'results': results
            }

        return {'status': 'unknown', 'state': str(state)}

    except Exception as e:
        logging.error(f"❌ Error Crítico en Poll: {str(e)}")
        # Importante: Retornar 'failed' para que el orquestador aborte y no se quede esperando eternamente
        return {'status': 'failed', 'error': str(e)}
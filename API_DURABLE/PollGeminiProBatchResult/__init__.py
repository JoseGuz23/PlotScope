# =============================================================================
# PollGeminiProBatchResult/__init__.py
# =============================================================================
import logging
import json
import os
import requests
from google import genai

logging.basicConfig(level=logging.INFO)

def main(batch_info: dict) -> dict:
    """
    Activity Function que consulta el estado de un Batch Job en Google.
    
    Retorna:
      - {'status': 'processing'}: Si sigue trabajando.
      - {'status': 'success', 'results': [...]}: Si terminó bien.
      - {'status': 'failed', 'error': ...}: Si falló.
    """
    try:
        # Recuperar info del input
        job_name = batch_info.get('batch_job_name')
        id_map = batch_info.get('id_map', [])  # Mapa clave para saber qué ID es qué
        
        if not job_name:
            return {'status': 'error', 'error': 'No batch_job_name provided'}

        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return {'status': 'error', 'error': 'GEMINI_API_KEY not found'}

        client = genai.Client(api_key=api_key)

        logging.info(f"🔍 Consultando estado de batch: {job_name}")
        
        # 1. Llamada a la API de Google para ver el estado
        job = client.batches.get(name=job_name)
        state = job.state.name 
        logging.info(f"📊 Estado actual Google: {state}")

        # --- LÓGICA DE ESTADOS ---

        # CASO A: Aún trabajando
        if state in ["JOB_STATE_NEW", "JOB_STATE_PENDING", "JOB_STATE_PROCESSING"]:
            return {
                'status': 'processing', 
                'batch_job_name': job_name,
                'id_map': id_map,
                'google_state': state
            }

        # CASO B: Fallo definitivo
        if state in ["JOB_STATE_FAILED", "JOB_STATE_CANCELLED"]:
            return {
                'status': 'failed',
                'error': f"Google Batch falló con estado: {state}"
            }

        # CASO C: Éxito -> Descargar resultados
        if state == "JOB_STATE_SUCCEEDED":
            logging.info("✅ Batch completado en Google. Iniciando descarga...")
            
            # La propiedad output_file tiene el nombre del recurso (ej. files/xxxx)
            output_file_name = job.output_file
            
            # Descargar el contenido del archivo .jsonl
            file_content_bytes = client.files.content(name=output_file_name)
            content_str = file_content_bytes.decode('utf-8')
            
            results = []
            
            # Procesar línea por línea el JSONL
            for line in content_str.strip().split('\n'):
                if not line.strip(): continue
                
                try:
                    row = json.loads(line)
                    
                    # 'custom_id' es lo que usamos para enlazar la respuesta con la pregunta
                    custom_id = row.get('custom_id')
                    
                    # Extraer el cuerpo de la respuesta del modelo
                    # La estructura de Google Batch suele ser: response -> body
                    response_payload = row.get('response', {}).get('body', {})
                    
                    # A veces el modelo devuelve el JSON como string dentro del campo
                    if isinstance(response_payload, str):
                         response_payload = json.loads(response_payload)
                    
                    # Buscar los metadatos originales (titulo, ids, etc) usando el custom_id
                    # Esto es crucial para saber a qué capítulo pertenece este análisis
                    meta = next((x for x in id_map if x['key'] == custom_id), {})
                    
                    # Combinar todo en un solo objeto limpio
                    final_item = {**meta, **response_payload}
                    results.append(final_item)
                    
                except Exception as parse_e:
                    logging.error(f"⚠️ Error parseando una línea del batch: {parse_e}")

            logging.info(f"✅ Resultados procesados: {len(results)}")
            return {
                'status': 'success',
                'total': len(results),
                'results': results
            }

        # Estado desconocido
        return {'status': 'unknown', 'state': state}

    except Exception as e:
        logging.error(f"❌ Error Crítico en Poll: {str(e)}")
        return {'status': 'error', 'error': str(e)}
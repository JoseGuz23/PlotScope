# =============================================================================
# PollBatchResult/__init__.py - SYLPHRENA 4.0 (CORREGIDO FINAL)
# =============================================================================
# 
# CORRECCIÓN CRÍTICA: 
# - Resultado está en: batch_job.dest.file_name
# - Descarga con: client.files.download(file=file_name)
# - Google usa "key" en respuesta, NO "custom_id"
#
# Documentación: https://ai.google.dev/gemini-api/docs/batch-api
# =============================================================================

import logging
import json
import os
import traceback

logging.basicConfig(level=logging.INFO)


def main(batch_info: dict) -> dict:
    """
    Consulta el estado del batch job y extrae resultados cuando complete.
    """
    try:
        from google import genai
        
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return {"status": "error", "error": "No API Key"}
        
        batch_job_name = batch_info.get('batch_job_name')
        if not batch_job_name:
            return {"status": "error", "error": "No Job Name"}
        
        # Mapa de IDs (ahora usa "key" en lugar de "custom_id")
        id_map_list = batch_info.get('id_map', [])
        id_map_lookup = {item['key']: item for item in id_map_list if item.get('key')}
        
        logging.info(f"🔍 Consultando estado de: {batch_job_name}")
        logging.info(f"📋 Mapa de IDs tiene {len(id_map_lookup)} entradas")
        
        client = genai.Client(api_key=api_key)
        
        # Consultar estado
        job = client.batches.get(name=batch_job_name)
        
        # Obtener estado como string
        if hasattr(job.state, 'name'):
            job_state = job.state.name
        else:
            job_state = str(job.state)
        
        logging.info(f"📊 Estado del job: {job_state}")
        
        # ============ JOB SUCCEEDED ============
        if job_state == 'JOB_STATE_SUCCEEDED' or 'SUCCEEDED' in job_state:
            logging.info("✅ Job completado exitosamente!")
            
            # CORRECCIÓN: El archivo está en job.dest.file_name
            result_file_name = None
            
            if job.dest:
                if hasattr(job.dest, 'file_name') and job.dest.file_name:
                    result_file_name = job.dest.file_name
                    logging.info(f"📄 Archivo de resultados: {result_file_name}")
            
            if not result_file_name:
                # Debug: mostrar qué tiene job.dest
                logging.error(f"❌ No se encontró archivo de salida")
                logging.info(f"🔍 job.dest = {job.dest}")
                if job.dest:
                    logging.info(f"🔍 dir(job.dest) = {[a for a in dir(job.dest) if not a.startswith('_')]}")
                return {"status": "error", "error": "No output file found in job.dest"}
            
            # Descargar archivo de resultados
            logging.info(f"⬇️ Descargando resultados...")
            
            try:
                file_content_bytes = client.files.download(file=result_file_name)
                text_content = file_content_bytes.decode('utf-8')
                logging.info(f"📥 Descargados {len(text_content)} bytes")
            except Exception as download_error:
                logging.error(f"❌ Error descargando archivo: {download_error}")
                return {"status": "error", "error": f"Download failed: {str(download_error)}"}
            
            # Procesar JSONL de resultados
            results = []
            error_count = 0
            
            for line_num, line in enumerate(text_content.splitlines(), 1):
                if not line.strip():
                    continue
                
                try:
                    result_item = json.loads(line)
                except json.JSONDecodeError as e:
                    logging.warning(f"⚠️ Línea {line_num} no es JSON válido: {e}")
                    error_count += 1
                    continue
                
                # Google usa "key" en la respuesta
                key = result_item.get('key')
                
                if not key:
                    logging.warning(f"⚠️ Línea {line_num} sin 'key'")
                    error_count += 1
                    continue
                
                if key not in id_map_lookup:
                    logging.warning(f"⚠️ Key '{key}' no está en el mapa de IDs")
                    error_count += 1
                    continue
                
                original_meta = id_map_lookup[key]
                
                # Extraer respuesta del modelo
                response_obj = result_item.get('response', {})
                text = None
                
                try:
                    # Estructura: response.candidates[0].content.parts[0].text
                    candidates = response_obj.get('candidates', [])
                    if candidates:
                        content = candidates[0].get('content', {})
                        parts = content.get('parts', [])
                        if parts:
                            text = parts[0].get('text')
                except Exception as e:
                    logging.warning(f"⚠️ Error extrayendo texto de respuesta: {e}")
                
                if not text:
                    logging.warning(f"⚠️ Key '{key}' sin texto en respuesta")
                    error_count += 1
                    continue
                
                # Limpiar y parsear JSON del modelo
                text = text.replace('```json', '').replace('```', '').strip()
                
                try:
                    analysis = json.loads(text)
                    
                    # Estampar metadatos de trazabilidad
                    analysis['fragment_id'] = original_meta['fragment_id']
                    analysis['parent_chapter_id'] = original_meta['parent_chapter_id']
                    
                    results.append(analysis)
                    
                except json.JSONDecodeError as e:
                    logging.warning(f"⚠️ Key '{key}' - respuesta no es JSON válido: {e}")
                    error_count += 1
            
            logging.info(f"✅ Procesados {len(results)} resultados exitosamente")
            if error_count > 0:
                logging.warning(f"⚠️ {error_count} items con errores")
            
            # Limpiar archivos (best effort)
            try:
                client.files.delete(name=result_file_name)
                logging.info(f"🗑️ Archivo de resultados eliminado")
            except:
                pass
            
            try:
                uploaded_file = batch_info.get('uploaded_file_name')
                if uploaded_file:
                    client.files.delete(name=uploaded_file)
                    logging.info(f"🗑️ Archivo de entrada eliminado")
            except:
                pass
            
            # Retornar lista de análisis
            return results
        
        # ============ JOB FAILED ============
        elif 'FAILED' in job_state or 'CANCELLED' in job_state:
            error_msg = "Unknown error"
            if hasattr(job, 'error') and job.error:
                error_msg = str(job.error)
            
            logging.error(f"❌ Job falló: {error_msg}")
            return {
                "status": "failed",
                "error": error_msg,
                "state": job_state
            }
        
        # ============ JOB STILL PROCESSING ============
        else:
            logging.info(f"⏳ Job aún procesando: {job_state}")
            return {
                "status": "processing",
                "state": job_state,
                "batch_job_name": batch_job_name,
                "id_map": id_map_list
            }
    
    except Exception as e:
        logging.error(f"❌ Error fatal en PollBatchResult: {str(e)}")
        logging.error(traceback.format_exc())
        return {"status": "error", "error": str(e)}
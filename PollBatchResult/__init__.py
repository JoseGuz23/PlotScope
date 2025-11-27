# =============================================================================
# PollBatchResult/__init__.py - SYLPHRENA 4.0
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
        
        id_map_list = batch_info.get('id_map', [])
        id_map_lookup = {item['key']: item for item in id_map_list if item.get('key')}
        
        logging.info(f"🔍 Consultando estado de: {batch_job_name}")
        
        client = genai.Client(api_key=api_key)
        
        job = client.batches.get(name=batch_job_name)
        
        if hasattr(job.state, 'name'):
            job_state = job.state.name
        else:
            job_state = str(job.state)
        
        logging.info(f"📊 Estado del job: {job_state}")
        
        # ============ JOB SUCCEEDED ============
        if job_state == 'JOB_STATE_SUCCEEDED' or 'SUCCEEDED' in job_state:
            logging.info("✅ Job completado exitosamente!")
            
            result_file_name = None
            
            if job.dest:
                if hasattr(job.dest, 'file_name') and job.dest.file_name:
                    result_file_name = job.dest.file_name
                    logging.info(f"📄 Archivo de resultados: {result_file_name}")
            
            if not result_file_name:
                logging.error(f"❌ No se encontró archivo de salida en job.dest")
                return {"status": "error", "error": "No output file found in job.dest"}
            
            logging.info(f"⬇️ Descargando resultados...")
            
            try:
                file_content_bytes = client.files.download(file=result_file_name)
                text_content = file_content_bytes.decode('utf-8')
                logging.info(f"📥 Descargados {len(text_content)} bytes")
            except Exception as download_error:
                logging.error(f"❌ Error descargando archivo: {download_error}")
                return {"status": "error", "error": f"Download failed: {str(download_error)}"}
            
            results = []
            error_count = 0
            
            for line_num, line in enumerate(text_content.splitlines(), 1):
                if not line.strip():
                    continue
                
                try:
                    result_item = json.loads(line)
                except json.JSONDecodeError:
                    error_count += 1
                    continue
                
                key = result_item.get('key')
                if not key or key not in id_map_lookup:
                    error_count += 1
                    continue
                
                original_meta = id_map_lookup[key]
                
                response_obj = result_item.get('response', {})
                text = None
                
                try:
                    candidates = response_obj.get('candidates', [])
                    if candidates:
                        content = candidates[0].get('content', {})
                        parts = content.get('parts', [])
                        if parts:
                            text = parts[0].get('text')
                except Exception:
                    pass
                
                if not text:
                    error_count += 1
                    continue
                
                text = text.replace('```json', '').replace('```', '').strip()
                
                try:
                    analysis = json.loads(text)
                    analysis['fragment_id'] = original_meta['fragment_id']
                    analysis['parent_chapter_id'] = original_meta['parent_chapter_id']
                    results.append(analysis)
                    
                except json.JSONDecodeError:
                    error_count += 1
            
            logging.info(f"✅ Procesados {len(results)} resultados exitosamente")
            
            # Limpieza
            try:
                client.files.delete(name=result_file_name)
                uploaded_file = batch_info.get('uploaded_file_name')
                if uploaded_file:
                    client.files.delete(name=uploaded_file)
            except:
                pass
            
            return results
        
        # ============ JOB FAILED ============
        elif 'FAILED' in job_state or 'CANCELLED' in job_state:
            error_msg = str(getattr(job, 'error', 'Unknown error'))
            logging.error(f"❌ Job falló: {error_msg}")
            return {
                "status": "failed",
                "error": error_msg,
                "state": job_state
            }
        
        # ============ JOB STILL PROCESSING ============
        else:
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
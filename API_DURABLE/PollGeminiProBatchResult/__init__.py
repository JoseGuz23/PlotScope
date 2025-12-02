# =============================================================================
# PollGeminiProBatchResult/__init__.py - POLL GENÉRICO GEMINI PRO BATCH
# =============================================================================

import logging
import json
import os
import re
from google import genai

logging.basicConfig(level=logging.INFO)


def clean_json_response(text: str) -> dict:
    """Limpia y parsea respuesta JSON."""
    if not text:
        return {}
    
    clean = text.strip()
    clean = re.sub(r'^[\s]*```(?:json)?[\s]*\n?', '', clean)
    clean = re.sub(r'\n?[\s]*```[\s]*$', '', clean)
    clean = clean.strip()
    
    try:
        return json.loads(clean)
    except:
        pass
    
    start = clean.find('{')
    end = clean.rfind('}')
    if start != -1 and end > start:
        try:
            return json.loads(clean[start:end+1])
        except:
            pass
    
    return {}


def main(batch_info: dict) -> dict:
    """
    Consulta estado del batch y extrae resultados.
    """
    try:
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return {"status": "error", "error": "No API Key"}
        
        batch_job_name = batch_info.get('batch_job_name')
        analysis_type = batch_info.get('analysis_type', 'unknown')
        id_map_list = batch_info.get('id_map', [])
        
        if not batch_job_name:
            return {"status": "error", "error": "No Job Name"}
        
        id_map_lookup = {item['key']: item for item in id_map_list}
        
        logging.info(f"🔍 Consultando batch {analysis_type}: {batch_job_name}")
        
        client = genai.Client(api_key=api_key)
        job = client.batches.get(name=batch_job_name)
        
        job_state = job.state.name if hasattr(job.state, 'name') else str(job.state)
        
        logging.info(f"📊 Estado: {job_state}")
        
        # EN PROGRESO
        if 'RUNNING' in job_state or 'PENDING' in job_state or 'PROCESSING' in job_state:
            return {
                "status": "processing",
                "batch_job_name": batch_job_name,
                "analysis_type": analysis_type,
                "id_map": id_map_list
            }
        
        # COMPLETADO
        if 'SUCCEEDED' in job_state:
            logging.info(f"✅ Batch completado, descargando...")
            
            result_file_name = None
            if job.dest and hasattr(job.dest, 'file_name'):
                result_file_name = job.dest.file_name
            
            if not result_file_name:
                return {"status": "error", "error": "No output file found"}
            
            file_content = client.files.download(file=result_file_name)
            text_content = file_content.decode('utf-8')
            
            results = []
            errors = 0
            
            for line in text_content.splitlines():
                if not line.strip():
                    continue
                
                try:
                    result_item = json.loads(line)
                    request_key = result_item.get('key', '')
                    
                    mapping = id_map_lookup.get(request_key, {})
                    chapter_id = mapping.get('chapter_id', 0)
                    
                    response = result_item.get('response', {})
                    candidates = response.get('candidates', [])
                    
                    if candidates:
                        content = candidates[0].get('content', {})
                        parts = content.get('parts', [])
                        if parts:
                            text = parts[0].get('text', '')
                            parsed = clean_json_response(text)
                            
                            if parsed:
                                parsed['chapter_id'] = chapter_id
                                parsed['_metadata'] = {
                                    'status': 'success',
                                    'analysis_type': analysis_type,
                                    'source': 'gemini_batch'
                                }
                                results.append(parsed)
                            else:
                                errors += 1
                                results.append({
                                    'chapter_id': chapter_id,
                                    'error': 'JSON parse failed',
                                    '_metadata': {'status': 'error'}
                                })
                    else:
                        errors += 1
                        results.append({
                            'chapter_id': chapter_id,
                            'error': 'No candidates',
                            '_metadata': {'status': 'error'}
                        })
                
                except Exception as e:
                    errors += 1
                    logging.warning(f"⚠️ Error procesando línea: {e}")
            
            logging.info(f"📊 Resultados: {len(results)} total, {errors} errores")
            
            return {
                "status": "success",
                "analysis_type": analysis_type,
                "results": results,
                "total": len(results),
                "errors": errors
            }
        
        # FALLÓ
        if 'FAILED' in job_state or 'CANCELLED' in job_state:
            return {
                "status": "failed",
                "error": f"Batch job {job_state}",
                "analysis_type": analysis_type
            }
        
        # OTRO ESTADO
        return {
            "status": "processing",
            "batch_job_name": batch_job_name,
            "analysis_type": analysis_type,
            "id_map": id_map_list
        }
        
    except Exception as e:
        logging.error(f"❌ Error en PollGeminiProBatchResult: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return {"status": "error", "error": str(e)}
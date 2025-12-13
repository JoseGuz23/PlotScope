# =============================================================================
# PollClaudeBatchResult/__init__.py - LYA 6.0 (Vertex AI Migration)
# =============================================================================
# MIGRACIÓN VERTEX AI: Polling de jobs de Vertex AI Batch.
# Parsea resultados y los empareja usando 'id_referencia' en el JSON de salida.
# =============================================================================

import logging
import json
import os
import sys
import re

# Agregar directorio padre para importar vertex_utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
try:
    from vertex_utils import get_batch_job_status, get_batch_job_results
except ImportError:
    from API_DURABLE.vertex_utils import get_batch_job_status, get_batch_job_results

logging.basicConfig(level=logging.INFO)


def clean_json_response(response_text: str) -> tuple:
    """
    Limpieza BLINDADA de respuesta JSON.
    """
    if not response_text:
        return {}, False
    
    clean = response_text.strip()
    
    # Limpieza de markdown
    clean = re.sub(r'^[\s]*```(?:json)?[\s]*\n?', '', clean)
    clean = re.sub(r'\n?[\s]*```[\s]*$', '', clean)
    clean = clean.strip()
    
    try:
        parsed = json.loads(clean)
        return parsed, True
    except json.JSONDecodeError:
        pass
    
    # Extracción entre { }
    start_idx = clean.find('{')
    end_idx = clean.rfind('}')
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        json_str = clean[start_idx : end_idx + 1]
        try:
            parsed = json.loads(json_str)
            return parsed, True
        except json.JSONDecodeError:
            pass
    
    return {}, False


def main(batch_info: dict) -> object:
    try:
        batch_id = batch_info.get('batch_id')
        if not batch_id:
            return {"status": "error", "error": "No batch_id provided"}
        
        fragment_metadata_map = batch_info.get('fragment_metadata_map', {})
        
        # Consultar estado en Vertex AI
        job_status = get_batch_job_status(batch_id)
        state = job_status.get('state')
        
        logging.info(f"🤖 Vertex Batch Status: [{state}] - ID: {batch_id}")
        
        if state in ["JOB_STATE_RUNNING", "JOB_STATE_PENDING", "JOB_STATE_QUEUED", "JOB_STATE_UNSPECIFIED"]:
            return {
                "status": "processing",
                "processing_status": state,
                "batch_id": batch_id,
                "fragment_metadata_map": fragment_metadata_map,
                "state": state
            }
            
        elif state == "JOB_STATE_FAILED" or state == "JOB_STATE_CANCELLED":
             return {
                "status": "failed",
                "error": job_status.get('error', 'Unknown error'),
                "batch_id": batch_id
            }
            
        elif state in ["JOB_STATE_SUCCEEDED", "JOB_STATE_PARTIALLY_SUCCEEDED"]:
            logging.info(f"✅ Batch finalizado. Descargando resultados...")
            
            raw_results = get_batch_job_results(batch_id)
            
            results = []
            processed_ids = set()
            parse_failures = 0
            
            for item in raw_results:
                # La estructura de 'item' depende de Vertex AI Batch output para Claude
                # Generalmente contiene 'prediction' o similar.
                # Claude output format: content text is in prediction['content'][0]['text'] or similar
                # Asumimos que get_batch_job_results devuelve el objeto JSON de cada línea
                
                # Intentar encontrar el contenido de la respuesta
                response_text = ""
                usage = {}
                
                # Caso 1: Estructura prediction
                if 'prediction' in item:
                    pred = item['prediction']
                    # Claude vertex output structure
                    if 'content' in pred:
                        # content is usually a list of parts
                        parts = pred.get('content', [])
                        if parts and 'text' in parts[0]:
                            response_text = parts[0]['text']
                    elif 'text' in pred:
                         response_text = pred['text']
                         
                    if 'usage' in pred:
                        usage = pred['usage']
                else:
                    # Caso 2: Directo (menos probable en batch)
                    if 'content' in item:
                        parts = item.get('content', [])
                        if parts and 'text' in parts[0]:
                            response_text = parts[0]['text']
                
                if not response_text:
                    logging.warning(f"⚠️ No text found in item: {str(item)[:100]}")
                    continue
                
                # Parsing
                parsed, parse_success = clean_json_response(response_text)
                
                # Identificar capítulo
                # Buscamos 'id_referencia' en el JSON parseado
                chapter_id = None
                if parse_success:
                    chapter_id = parsed.get('id_referencia')
                
                # Fallback: intentar regex si el parsing falló o no tiene ID
                if not chapter_id:
                    match = re.search(r'"id_referencia"\s*:\s*"([^"]+)"', response_text)
                    if match:
                        chapter_id = match.group(1)
                
                if not chapter_id:
                    logging.warning(f"⚠️ No se pudo identificar id_referencia en respuesta. Saltando.")
                    continue
                
                processed_ids.add(chapter_id)
                fragment_meta = fragment_metadata_map.get(chapter_id, {})
                
                if parse_success and parsed:
                     final_content = parsed.get('capitulo_editado', '')
                     cambios = parsed.get('cambios_realizados', [])
                     notas = parsed.get('notas_editor', '')
                     
                     if not final_content or final_content.strip().startswith('{'):
                         logging.warning(f"⚠️ {chapter_id}: Contenido inválido, usando original")
                         final_content = fragment_meta.get('content', '')
                         parse_failures += 1
                else:
                    logging.warning(f"⚠️ {chapter_id}: Parsing falló, usando original")
                    final_content = fragment_meta.get('content', '')
                    cambios = []
                    notas = "FALLBACK: Parsing falló"
                    parse_failures += 1
                
                # Costos (estimado)
                input_tokens = usage.get('input_tokens', 0)
                output_tokens = usage.get('output_tokens', 0)
                total_cost = (input_tokens * 3.00 / 1_000_000) + (output_tokens * 15.00 / 1_000_000)
                
                result_item = {
                    'chapter_id': chapter_id,
                    'fragment_id': fragment_meta.get('fragment_id', chapter_id),
                    'parent_chapter_id': fragment_meta.get('parent_chapter_id', chapter_id),
                    'original_title': fragment_meta.get('original_title', 'Sin título'),
                    'contenido_editado': final_content,
                    'contenido_original': fragment_meta.get('content', ''),
                    'cambios_realizados': cambios,
                    'notas_editor': notas,
                    'metadata': {
                        'status': 'success' if (parse_success and final_content) else 'fallback_used',
                        'costo_usd': round(total_cost, 4),
                        'tokens_in': input_tokens,
                        'tokens_out': output_tokens,
                        'parse_success': parse_success
                    }
                }
                results.append(result_item)
            
            # Verificar faltantes
            all_ids = set(fragment_metadata_map.keys())
            missing_ids = all_ids - processed_ids
            if missing_ids:
                logging.warning(f"⚠️ {len(missing_ids)} capítulos no encontrados en resultados Batch: {missing_ids}")
                # Agregar fallbacks para los faltantes
                for mid in missing_ids:
                    meta = fragment_metadata_map.get(mid, {})
                    results.append({
                        'chapter_id': mid,
                        'fragment_id': meta.get('fragment_id', mid),
                        'contenido_editado': meta.get('content', ''),
                        'contenido_original': meta.get('content', ''),
                        'cambios_realizados': [],
                        'notas_editor': "ERROR: No encontrado en resultados Batch",
                        'metadata': {'status': 'missing_in_batch'}
                    })

            logging.info(f"📊 Resultados procesados: {len(results)}")
            
            return {
                "status": "success",
                "results": results,
                "batch_id": batch_id,
                "total_processed": len(results)
            }
            
        else:
            return {
                "status": "unknown",
                "processing_status": state,
                "batch_id": batch_id,
                "fragment_metadata_map": fragment_metadata_map
            }

    except Exception as e:
        logging.error(f"❌ Error en PollClaudeBatchResult: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return {"status": "error", "error": str(e)}

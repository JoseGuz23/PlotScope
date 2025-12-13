# =============================================================================
# PollMarginNotesBatch/__init__.py - LYA 6.0 (Vertex AI Migration)
# =============================================================================
# MIGRACIÓN VERTEX AI: Polling de notas de margen.
# =============================================================================

import logging
import json
import os
import sys
import re

# Agregar directorio padre
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
try:
    from vertex_utils import get_batch_job_status, get_batch_job_results
except ImportError:
    from API_DURABLE.vertex_utils import get_batch_job_status, get_batch_job_results

logging.basicConfig(level=logging.INFO)


def main(batch_info: dict) -> dict:
    try:
        batch_id = batch_info.get('batch_id')
        chapter_metadata = batch_info.get('chapter_metadata', {})
        
        if not batch_id:
            return {"error": "batch_id no proporcionado", "status": "error"}
        
        # Consultar estado
        job_status = get_batch_job_status(batch_id)
        state = job_status.get('state')
        
        logging.info(f"📊 Vertex Batch Notes Status [{state}] - ID: {batch_id}")
        
        if state in ["JOB_STATE_RUNNING", "JOB_STATE_PENDING", "JOB_STATE_QUEUED", "JOB_STATE_UNSPECIFIED"]:
            return {
                "status": "processing",
                "processing_status": state,
                "batch_id": batch_id,
                "chapter_metadata": chapter_metadata,
                "state": state
            }
            
        elif state == "JOB_STATE_FAILED" or state == "JOB_STATE_CANCELLED":
             return {
                "status": "failed",
                "error": job_status.get('error', 'Unknown error'),
                "batch_id": batch_id
            }
        
        # Batch completado
        logging.info(f"✅ Batch notas completado. Descargando resultados...")
        
        raw_results = get_batch_job_results(batch_id)
        
        results = []
        all_notes = []
        processed_ids = set()
        
        for item in raw_results:
            # Extracción del contenido (igual que en PollClaudeBatchResult)
            response_text = ""
            if 'prediction' in item:
                pred = item['prediction']
                if 'content' in pred:
                    parts = pred.get('content', [])
                    if parts and 'text' in parts[0]:
                        response_text = parts[0]['text']
                elif 'text' in pred:
                     response_text = pred['text']
            elif 'content' in item:
                parts = item.get('content', [])
                if parts and 'text' in parts[0]:
                    response_text = parts[0]['text']
            
            if not response_text:
                continue
            
            # Parsear
            parsed = parse_margin_notes_response(response_text)
            
            # Identificar ID
            ch_id = parsed.get('id_referencia')
            if not ch_id:
                # Regex fallback
                match = re.search(r'"id_referencia"\s*:\s*"([^"]+)"', response_text)
                if match:
                    ch_id = match.group(1)
            
            if not ch_id:
                logging.warning(f"⚠️ No se pudo identificar capítulo en respuesta")
                continue
                
            processed_ids.add(ch_id)
            metadata = chapter_metadata.get(ch_id, {})
            
            chapter_result = {
                "chapter_id": metadata.get('parent_chapter_id', ch_id),
                "fragment_id": metadata.get('fragment_id', ch_id),
                "original_title": metadata.get('original_title', 'Sin título'),
                "notas_margen": parsed.get('notas_margen', []),
                "resumen_capitulo": parsed.get('resumen_capitulo', {}),
                "status": "success"
            }
            
            results.append(chapter_result)
            all_notes.extend(parsed.get('notas_margen', []))
        
        # Estadísticas
        stats = calcular_estadisticas_notas(all_notes)
        
        logging.info(f"📊 Total notas generadas: {len(all_notes)}")
        
        return {
            "status": "success",
            "results": results,
            "all_notes": all_notes,
            "statistics": stats,
            "total": len(results),
            "errors": 0 # Simplificado
        }
        
    except Exception as e:
        logging.error(f"❌ Error en poll: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return {"error": str(e), "status": "error"}


def parse_margin_notes_response(content: str) -> dict:
    """Parsea la respuesta de Claude para notas de margen."""
    try:
        # Limpieza básica
        clean = content.strip()
        clean = re.sub(r'^[\s]*```(?:json)?[\s]*\n?', '', clean)
        clean = re.sub(r'\n?[\s]*```[\s]*$', '', clean)
        
        return json.loads(clean)
    except json.JSONDecodeError:
        pass
    
    # Nivel 2: Extraer JSON del texto
    try:
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            return json.loads(json_match.group())
    except:
        pass
    
    return {"notas_margen": [], "resumen_capitulo": {}}


def calcular_estadisticas_notas(notas: list) -> dict:
    """Calcula estadísticas de las notas generadas."""
    
    por_tipo = {}
    por_severidad = {"alta": 0, "media": 0, "baja": 0}
    
    for nota in notas:
        tipo = nota.get('tipo', 'otro')
        severidad = nota.get('severidad', 'media')
        
        por_tipo[tipo] = por_tipo.get(tipo, 0) + 1
        if severidad in por_severidad:
            por_severidad[severidad] += 1
    
    return {
        "total": len(notas),
        "por_tipo": por_tipo,
        "por_severidad": por_severidad
    }

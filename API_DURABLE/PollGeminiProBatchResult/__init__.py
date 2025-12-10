# =============================================================================
# PollGeminiProBatchResult/__init__.py - SYLPHRENA 4.0.1 CORREGIDO
# =============================================================================
# CORRECCIONES:
#   - job.dest.file_name en vez de job.output_file
#   - client.files.download() en vez de client.files.content()
#   - row.get('key') en vez de row.get('custom_id')
#   - Estructura de respuesta correcta (candidates/content/parts)
# =============================================================================

import logging
import json
import os
import traceback
from google import genai

logging.basicConfig(level=logging.INFO)


def main(batch_info: dict) -> dict:
    """
    Activity Function: Consulta estado de Batch Job de Gemini Pro.
    Extrae resultados de layer2, layer3, o arc_maps.
    """
    try:
        job_name = batch_info.get('batch_job_name')
        id_map = batch_info.get('id_map', [])
        analysis_type = batch_info.get('analysis_type', 'unknown')
        
        if not job_name:
            return {'status': 'error', 'error': 'No batch_job_name provided'}

        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return {'status': 'error', 'error': 'GEMINI_API_KEY no configurada'}
        
        client = genai.Client(api_key=api_key)

        logging.info(f"🔍 Consultando Gemini Pro Batch: {job_name}")
        logging.info(f"📋 Tipo de análisis: {analysis_type}")
        
        # =======================================================
        # 1. OBTENER JOB
        # =======================================================
        try:
            job = client.batches.get(name=job_name)
        except Exception as api_err:
            logging.error(f"❌ Error conectando con Google API: {api_err}")
            return {'status': 'processing', 'batch_job_name': job_name, 'id_map': id_map, 'analysis_type': analysis_type}

        # Recuperar estado de forma segura
        state = getattr(job, 'state', None)
        if hasattr(state, 'name'):
            state = state.name
        
        logging.info(f"📊 Estado: {state}")

        # =======================================================
        # CASO A: AÚN PROCESANDO
        # =======================================================
        if state in ["JOB_STATE_NEW", "JOB_STATE_PENDING", "JOB_STATE_PROCESSING", "JOB_STATE_RUNNING", None]:
            return {
                'status': 'processing',
                'batch_job_name': job_name,
                'id_map': id_map,
                'analysis_type': analysis_type,
                'state': str(state)
            }

        # =======================================================
        # CASO B: FALLÓ
        # =======================================================
        if state in ["JOB_STATE_FAILED", "JOB_STATE_CANCELLED"]:
            error_msg = str(getattr(job, 'error', 'Unknown error'))
            logging.error(f"❌ Batch falló: {error_msg}")
            return {
                'status': 'failed',
                'error': f"Google Batch falló: {state} - {error_msg}",
                'analysis_type': analysis_type
            }

        # =======================================================
        # CASO C: COMPLETADO - DESCARGAR RESULTADOS
        # =======================================================
        if state == "JOB_STATE_SUCCEEDED":
            logging.info("✅ Batch completado. Descargando resultados...")
            
            # ─────────────────────────────────────────────────────
            # FIX #1: Usar job.dest.file_name (NO job.output_file)
            # ─────────────────────────────────────────────────────
            result_file_name = None
            
            if job.dest:
                if hasattr(job.dest, 'file_name') and job.dest.file_name:
                    result_file_name = job.dest.file_name
                    logging.info(f"📄 Archivo de resultados: {result_file_name}")
            
            if not result_file_name:
                logging.error(f"❌ No se encontró archivo en job.dest")
                logging.error(f"🕵️ job.dest = {job.dest}")
                logging.error(f"🕵️ Atributos: {dir(job)}")
                return {'status': 'error', 'error': 'No output file found in job.dest'}
            
            # ─────────────────────────────────────────────────────
            # FIX #2: Usar client.files.download() (NO .content())
            # ─────────────────────────────────────────────────────
            try:
                file_content_bytes = client.files.download(file=result_file_name)
                content_str = file_content_bytes.decode('utf-8')
                logging.info(f"📥 Descargados {len(content_str)} bytes")
            except Exception as download_error:
                logging.error(f"❌ Error descargando: {download_error}")
                return {'status': 'error', 'error': f'Download failed: {str(download_error)}'}
            
            # ─────────────────────────────────────────────────────
            # PARSEAR RESULTADOS JSONL
            # ─────────────────────────────────────────────────────
            # Crear lookup para id_map
            id_map_lookup = {item['key']: item for item in id_map if item.get('key')}
            
            results = []
            error_count = 0
            
            for line_num, line in enumerate(content_str.strip().split('\n'), 1):
                if not line.strip():
                    continue
                
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    logging.warning(f"⚠️ Línea {line_num}: JSON inválido")
                    error_count += 1
                    continue
                
                # ─────────────────────────────────────────────────
                # FIX #3: Usar 'key' (NO 'custom_id')
                # ─────────────────────────────────────────────────
                key = row.get('key')
                if not key:
                    logging.warning(f"⚠️ Línea {line_num}: Sin 'key'")
                    error_count += 1
                    continue
                
                # Buscar metadatos originales
                meta = id_map_lookup.get(key, {})
                chapter_id = meta.get('chapter_id', 0)
                
                # ─────────────────────────────────────────────────
                # FIX #4: Estructura correcta de respuesta Gemini
                # candidates[0].content.parts[0].text
                # ─────────────────────────────────────────────────
                response_obj = row.get('response', {})
                text = None
                
                try:
                    candidates = response_obj.get('candidates', [])
                    if candidates:
                        content = candidates[0].get('content', {})
                        parts = content.get('parts', [])
                        if parts:
                            text = parts[0].get('text')
                except Exception as extract_err:
                    logging.warning(f"⚠️ Línea {line_num}: Error extrayendo texto: {extract_err}")
                
                if not text:
                    logging.warning(f"⚠️ {key}: Sin texto en respuesta")
                    error_count += 1
                    continue
                
                # Limpiar markdown de JSON
                text = text.replace('```json', '').replace('```', '').strip()
                
                # Parsear JSON del análisis
                try:
                    analysis = json.loads(text)
                    
                    # Agregar metadatos
                    analysis['chapter_id'] = chapter_id
                    analysis['analysis_type'] = analysis_type
                    
                    results.append(analysis)
                    
                except json.JSONDecodeError as je:
                    logging.warning(f"⚠️ {key}: JSON de análisis inválido: {je}")
                    error_count += 1
                    continue
            
            logging.info(f"✅ Procesados {len(results)} resultados, {error_count} errores")
            
            # ─────────────────────────────────────────────────────
            # LIMPIEZA DE ARCHIVOS
            # ─────────────────────────────────────────────────────
            try:
                client.files.delete(name=result_file_name)
                logging.info(f"🗑️ Archivo de resultados eliminado")
            except Exception as cleanup_err:
                logging.warning(f"⚠️ No se pudo eliminar archivo: {cleanup_err}")
            
            return {
                'status': 'success',
                'analysis_type': analysis_type,
                'total': len(results),
                'errors': error_count,
                'results': results
            }

        # =======================================================
        # CASO D: ESTADO DESCONOCIDO
        # =======================================================
        logging.warning(f"⚠️ Estado desconocido: {state}")
        return {
            'status': 'processing',
            'state': str(state),
            'batch_job_name': job_name,
            'id_map': id_map,
            'analysis_type': analysis_type
        }

    except Exception as e:
        logging.error(f"❌ Error Crítico en PollGeminiProBatchResult: {str(e)}")
        logging.error(traceback.format_exc())
        return {'status': 'failed', 'error': str(e)}
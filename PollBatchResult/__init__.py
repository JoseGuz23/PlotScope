# =============================================================================
# PollBatchResult/__init__.py
# =============================================================================
# 
# Consulta el estado de un Batch Job y obtiene resultados
# Solo necesita: GEMINI_API_KEY
#
# =============================================================================

import logging
import json
import os

def main(batch_info: dict) -> dict:
    """
    Consulta el estado de un Batch Job y descarga resultados si completó.
    
    Input: {batch_job_name, ...}
    Output: 
        - Si completó: Lista de análisis JSON
        - Si procesando: {status: "processing", state: "..."}
        - Si falló: {status: "failed", error: "..."}
    """
    try:
        from google import genai
        
        # ─────────────────────────────────────────────────────────────────
        # A. CONFIGURACIÓN
        # ─────────────────────────────────────────────────────────────────
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return {"status": "error", "error": "GEMINI_API_KEY no configurada"}
        
        batch_job_name = batch_info.get('batch_job_name')
        if not batch_job_name:
            return {"status": "error", "error": "No batch_job_name provided"}
        
        id_map = batch_info.get('id_map', [])
        logging.info(f"📋 Mapa de IDs recuperado: {len(id_map)} elementos")
        
        logging.info(f"🔄 Consultando batch: {batch_job_name}")
        
        # Crear cliente
        client = genai.Client(api_key=api_key)
        
        # ─────────────────────────────────────────────────────────────────
        # B. CONSULTAR ESTADO DEL JOB
        # ─────────────────────────────────────────────────────────────────
        job = client.batches.get(name=batch_job_name)
        
        job_state = str(job.state) if job.state else "UNKNOWN"
        logging.info(f"📊 Estado: {job_state}")
        
        # Estados posibles: JOB_STATE_PENDING, JOB_STATE_RUNNING, 
        #                   JOB_STATE_SUCCEEDED, JOB_STATE_FAILED, JOB_STATE_CANCELLED
        
        if "SUCCEEDED" in job_state:
            logging.info(f"✅ Job completado, extrayendo resultados...")
            
            results = []
            idx = 0  # 🆕 Contador para el mapa
            
            # Extraer respuestas
            if hasattr(job, 'response') and job.response:
                for resp in job.response:
                    try:
                        if hasattr(resp, 'candidates') and resp.candidates:
                            candidate = resp.candidates[0]
                            if hasattr(candidate, 'content') and candidate.content:
                                text = candidate.content.parts[0].text
                                
                                # Limpiar markdown
                                text = text.replace('```json', '').replace('```', '').strip()
                                
                                # Parsear JSON
                                analysis = json.loads(text)
                                
                                # 🆕 ESTAMPAR ID CORRECTO POR POSICIÓN
                                if idx < len(id_map):
                                    analysis['chapter_id'] = id_map[idx]
                                    logging.info(f"✅ Resultado {idx} → ID: {id_map[idx]}")
                                else:
                                    analysis['chapter_id'] = f"unknown_{idx}"
                                    logging.warning(f"⚠️ Resultado {idx} fuera de rango")
                                
                                results.append(analysis)
                                idx += 1
                                
                    except Exception as e:
                        logging.warning(f"⚠️ Error procesando resultado {idx}: {e}")
                        idx += 1  # IMPORTANTE: avanzar aunque falle
                        continue
            
            logging.info(f"🔥 Extraídos {len(results)} análisis con IDs correctos")
            
            if results:
                return results
            else:
                return {
                    "status": "completed_no_results",
                    "job_name": batch_job_name,
                    "message": "Job completó pero no se pudieron extraer resultados"
                }
            
        elif "FAILED" in job_state or "CANCELLED" in job_state:
            error_msg = str(job.error) if hasattr(job, 'error') and job.error else "Unknown error"
            logging.error(f"❌ Job falló: {error_msg}")
            return {"status": "failed", "error": error_msg, "state": job_state}
            
        else:
            # PENDING o RUNNING
            logging.info(f"⏳ Job aún procesando...")
            return {
                "status": "processing",
                "state": job_state,
                "batch_job_name": batch_job_name
            }
            
    except ImportError as e:
        logging.error(f"❌ SDK no instalado: {e}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        logging.error(f"❌ Error consultando batch: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return {"status": "error", "error": str(e)}
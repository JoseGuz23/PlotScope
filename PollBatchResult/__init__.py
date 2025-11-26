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
            # ─────────────────────────────────────────────────────────────
            # C. EXTRAER RESULTADOS
            # ─────────────────────────────────────────────────────────────
            logging.info(f"✅ Job completado, extrayendo resultados...")
            
            results = []
            
            # Los resultados vienen en job.dest o inline_response dependiendo del tipo
            if hasattr(job, 'dest') and job.dest:
                # Resultados en archivo
                logging.info(f"   Destino: {job.dest}")
                # Aquí habría que descargar del destino
                # Por ahora, verificar si hay inline_response
            
            # Para requests inline, los resultados vienen en response
            if hasattr(job, 'response') and job.response:
                for resp in job.response:
                    try:
                        # Extraer el texto generado
                        if hasattr(resp, 'candidates') and resp.candidates:
                            text = resp.candidates[0].content.parts[0].text
                            # Intentar parsear como JSON
                            analysis = json.loads(text)
                            results.append(analysis)
                        elif hasattr(resp, 'text'):
                            analysis = json.loads(resp.text)
                            results.append(analysis)
                    except (json.JSONDecodeError, AttributeError, IndexError) as e:
                        logging.warning(f"   Error parseando respuesta: {e}")
                        continue
            
            # Alternativa: verificar inline_responses
            if not results and hasattr(job, 'inline_responses'):
                for resp in job.inline_responses:
                    try:
                        if hasattr(resp, 'response'):
                            text = resp.response.candidates[0].content.parts[0].text
                            # Limpiar posibles backticks
                            text = text.strip()
                            if text.startswith("```json"):
                                text = text[7:]
                            if text.startswith("```"):
                                text = text[3:]
                            if text.endswith("```"):
                                text = text[:-3]
                            analysis = json.loads(text.strip())
                            results.append(analysis)
                    except Exception as e:
                        logging.warning(f"   Error en inline_response: {e}")
                        continue
            
            logging.info(f"📥 Extraídos {len(results)} análisis")
            
            if results:
                return results  # Lista de análisis
            else:
                # Si no pudimos extraer resultados, devolver info del job
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
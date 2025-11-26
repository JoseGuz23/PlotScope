# =============================================================================
# PollBatchResult/__init__.py
# =============================================================================

import logging
import json
import os
import traceback

def main(batch_info: dict) -> dict:
    """
    Consulta el estado de un Batch Job de Google Gemini y descarga resultados si completó.
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
        
        client = genai.Client(api_key=api_key)
        
        # ─────────────────────────────────────────────────────────────────
        # B. CONSULTAR ESTADO DEL JOB
        # ─────────────────────────────────────────────────────────────────
        job = client.batches.get(name=batch_job_name)
        
        job_state = str(job.state) if job.state else "UNKNOWN"
        logging.info(f"📊 Estado: {job_state}")
        
        if "SUCCEEDED" in job_state:
            logging.info(f"✅ Job completado, extrayendo resultados...")
            
            # ═══════════════════════════════════════════════════════════
            # 🔍 DEBUG: Ver estructura del objeto job
            # ═══════════════════════════════════════════════════════════
            logging.info(f"🔍 DEBUG - Tipo: {type(job)}")
            
            # Verificar ubicaciones posibles
            has_response = hasattr(job, 'response') and job.response
            has_inline = hasattr(job, 'inline_responses') and job.inline_responses
            has_dest = hasattr(job, 'dest') and job.dest
            has_results = hasattr(job, 'results') and job.results
            
            logging.info(f"🔍 DEBUG - job.dest existe: {has_dest}")
            
            # ═══════════════════════════════════════════════════════════
            # C. EXTRAER RESULTADOS (CORREGIDO)
            # ═══════════════════════════════════════════════════════════
            results = []
            idx = 0
            
            # 🆕 INTENTO PRIORITARIO: job.dest.inlined_responses
            # Esta es la ubicación confirmada por tus logs para Gemini 2.5 Flash Batch
            if has_dest and hasattr(job.dest, 'inlined_responses') and job.dest.inlined_responses:
                logging.info(f"📦 Extrayendo de job.dest.inlined_responses...")
                for resp in job.dest.inlined_responses:
                    result = extract_from_response(resp, idx, id_map)
                    if result:
                        results.append(result)
                    idx += 1

            # INTENTO 2: job.response (Legacy / Estructuras planas)
            elif has_response:
                logging.info(f"📦 Extrayendo de job.response...")
                for resp in job.response:
                    result = extract_from_response(resp, idx, id_map)
                    if result:
                        results.append(result)
                    idx += 1
            
            # INTENTO 3: job.inline_responses (Variante SDK)
            elif not results and has_inline:
                logging.info(f"📦 Extrayendo de job.inline_responses...")
                for resp in job.inline_responses:
                    result = extract_from_response(resp, idx, id_map)
                    if result:
                        results.append(result)
                    idx += 1
            
            # INTENTO 4: job.results (Otra variante)
            elif not results and has_results:
                logging.info(f"📦 Extrayendo de job.results...")
                for resp in job.results:
                    result = extract_from_response(resp, idx, id_map)
                    if result:
                        results.append(result)
                    idx += 1
            
            # INTENTO 5: Iterar directamente sobre el job (FALLBACK SEGURO)
            if not results:
                logging.info(f"📦 Intentando iterar sobre job directamente (fallback)...")
                try:
                    # Verificamos si es iterable y NO es un diccionario/string
                    if hasattr(job, '__iter__') and not isinstance(job, (str, dict)):
                        temp_idx = 0
                        for resp in job:
                            # 🛡️ Protección contra iteración de atributos (Tuplas)
                            # Si devuelve ('count', 1) o similar, lo saltamos
                            if isinstance(resp, tuple) and len(resp) == 2 and isinstance(resp[0], str):
                                continue 
                            
                            result = extract_from_response(resp, temp_idx, id_map)
                            if result:
                                results.append(result)
                            temp_idx += 1
                except TypeError:
                    logging.info(f"⚠️ job no es iterable de forma estándar")
                except Exception as e:
                    logging.warning(f"⚠️ Error en iteración fallback: {e}")
            
            logging.info(f"🔥 Extraídos {len(results)} análisis con IDs correctos")
            
            if results:
                return results
            else:
                return {
                    "status": "completed_no_results",
                    "job_name": batch_job_name,
                    "message": "Job completó pero no se pudieron extraer resultados",
                    "debug_attrs": [a for a in dir(job) if not a.startswith('_')]
                }
            
        elif "FAILED" in job_state or "CANCELLED" in job_state:
            error_msg = str(job.error) if hasattr(job, 'error') and job.error else "Unknown error"
            logging.error(f"❌ Job falló: {error_msg}")
            return {"status": "failed", "error": error_msg, "state": job_state}
            
        else:
            logging.info(f"⏳ Job aún procesando...")
            return {
                "status": "processing",
                "state": job_state,
                "batch_job_name": batch_job_name,
                "id_map": id_map
            }
            
    except Exception as e:
        logging.error(f"❌ Error: {str(e)}")
        logging.error(traceback.format_exc())
        return {"status": "error", "error": str(e)}


def extract_from_response(resp, idx, id_map):
    """Intenta extraer un análisis de diferentes estructuras de respuesta."""
    try:
        text = None
        
        # Estructura 1: Objeto InlinedResponse (resp.response.candidates...)
        # Esta es la que se usa dentro de job.dest.inlined_responses
        if hasattr(resp, 'response'):
            inner = resp.response
            if hasattr(inner, 'candidates') and inner.candidates:
                candidate = inner.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        text = candidate.content.parts[0].text

        # Estructura 2: Objeto Response directo (resp.candidates...)
        if not text and hasattr(resp, 'candidates') and resp.candidates:
            candidate = resp.candidates[0]
            if hasattr(candidate, 'content') and candidate.content:
                if hasattr(candidate.content, 'parts') and candidate.content.parts:
                    text = candidate.content.parts[0].text
        
        # Estructura 3: resp.text directamente
        if not text and hasattr(resp, 'text'):
            text = resp.text
        
        # Estructura 4: resp es string (JSON directo)
        if not text and isinstance(resp, str):
            text = resp
        
        if not text:
            # Solo logueamos advertencia si NO es una tupla de atributos internos
            if not (isinstance(resp, tuple) and len(resp) > 0 and isinstance(resp[0], str)):
                logging.warning(f"⚠️ No se encontró texto en resultado {idx}")
                logging.warning(f"   Tipo: {type(resp)}")
            return None
        
        # Limpiar markdown
        text = text.replace('```json', '').replace('```', '').strip()
        
        # Parsear JSON
        analysis = json.loads(text)
        
        # Estampar ID correcto
        if idx < len(id_map):
            analysis['chapter_id'] = id_map[idx]
        else:
            analysis['chapter_id'] = f"unknown_{idx}"
        
        return analysis
        
    except Exception as e:
        logging.warning(f"⚠️ Error procesando resultado {idx}: {e}")
        return None
# =============================================================================
# PollClaudeBatchResult/__init__.py
# =============================================================================
# 
# Consulta el estado de un Claude Batch Job y obtiene resultados
# Necesita: ANTHROPIC_API_KEY
#
# =============================================================================

import logging
import json
import os

logging.basicConfig(level=logging.INFO)


def main(batch_info: dict) -> dict:
    """
    Consulta el estado de un Claude Batch Job y descarga resultados si completó.
    
    Input: {batch_id, id_map, ...}
    Output: 
        - Si completó: Lista de capítulos editados
        - Si procesando: {status: "processing", ...}
        - Si falló: {status: "failed", error: "..."}
    """
    try:
        from anthropic import Anthropic
        
        # ─────────────────────────────────────────────────────────────────
        # A. CONFIGURACIÓN
        # ─────────────────────────────────────────────────────────────────
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            return {"status": "error", "error": "ANTHROPIC_API_KEY no configurada"}
        
        batch_id = batch_info.get('batch_id')
        if not batch_id:
            return {"status": "error", "error": "No batch_id provided"}
        
        # Recuperar mapa de IDs
        id_map = batch_info.get('id_map', [])
        logging.info(f"📋 Mapa de IDs recuperado: {len(id_map)} elementos")
        
        logging.info(f"🔄 Consultando Claude batch: {batch_id}")
        
        # Crear cliente
        client = Anthropic(api_key=api_key)
        
        # ─────────────────────────────────────────────────────────────────
        # B. CONSULTAR ESTADO DEL BATCH
        # ─────────────────────────────────────────────────────────────────
        message_batch = client.messages.batches.retrieve(batch_id)
        
        status = message_batch.processing_status
        logging.info(f"📊 Estado: {status}")
        
        # Estados posibles: in_progress, canceling, ended
        
        if status == "ended":
            # ─────────────────────────────────────────────────────────────
            # C. EXTRAER RESULTADOS
            # ─────────────────────────────────────────────────────────────
            logging.info(f"✅ Batch completado, extrayendo resultados...")
            
            results = []
            
            # Iterar sobre los resultados
            for entry in client.messages.batches.results(batch_id):
                try:
                    custom_id = entry.custom_id  # "chapter-1", "chapter-2", etc.
                    
                    if entry.result.type == "succeeded":
                        # Extraer el texto de la respuesta
                        message = entry.result.message
                        response_text = message.content[0].text
                        
                        # Extraer el ID del custom_id
                        chapter_id = custom_id.replace("chapter-", "")
                        
                        # Limpiar y parsear JSON
                        clean_response = response_text.strip()
                        if clean_response.startswith("```json"):
                            clean_response = clean_response[7:]
                        elif clean_response.startswith("```"):
                            clean_response = clean_response[3:]
                        if clean_response.endswith("```"):
                            clean_response = clean_response[:-3]
                        clean_response = clean_response.strip()
                        
                        try:
                            edit_result = json.loads(clean_response)
                            edited_content = edit_result.get('capitulo_editado', response_text)
                            cambios = edit_result.get('cambios_realizados', [])
                            problemas_corregidos = edit_result.get('problemas_corregidos', [])
                            notas = edit_result.get('notas_editor', '')
                        except json.JSONDecodeError:
                            edited_content = response_text
                            cambios = []
                            problemas_corregidos = []
                            notas = "Respuesta no estructurada"
                        
                        # Calcular costo (aproximado)
                        input_tokens = message.usage.input_tokens
                        output_tokens = message.usage.output_tokens
                        # Precios Batch: 50% de los normales
                        cost_input = input_tokens * 1.50 / 1_000_000  # $1.50 por 1M (batch)
                        cost_output = output_tokens * 7.50 / 1_000_000  # $7.50 por 1M (batch)
                        total_cost = cost_input + cost_output
                        
                        results.append({
                            'chapter_id': chapter_id,
                            'contenido_editado': edited_content,
                            'cambios_realizados': cambios,
                            'problemas_corregidos': problemas_corregidos,
                            'notas_editor': notas,
                            'metadata': {
                                'status': 'success',
                                'modelo': 'claude-sonnet-4-5-20250929',
                                'modo': 'batch',
                                'costo_usd': round(total_cost, 4)
                            }
                        })
                        
                        logging.info(f"✅ {custom_id} procesado | Costo: ${total_cost:.4f}")
                        
                    elif entry.result.type == "errored":
                        error_msg = str(entry.result.error) if hasattr(entry.result, 'error') else "Unknown error"
                        chapter_id = custom_id.replace("chapter-", "")
                        results.append({
                            'chapter_id': chapter_id,
                            'contenido_editado': '',
                            'error': error_msg,
                            'metadata': {'status': 'error'}
                        })
                        logging.warning(f"⚠️ {custom_id} falló: {error_msg}")
                        
                except Exception as e:
                    logging.warning(f"⚠️ Error procesando entrada: {e}")
                    continue
            
            logging.info(f"📥 Extraídos {len(results)} capítulos editados")
            
            if results:
                return results
            else:
                return {
                    "status": "completed_no_results",
                    "batch_id": batch_id,
                    "message": "Batch completó pero no se pudieron extraer resultados"
                }
            
        elif status == "canceling":
            logging.warning(f"⚠️ Batch cancelándose...")
            return {"status": "canceling", "batch_id": batch_id}
            
        else:
            # in_progress
            counts = message_batch.request_counts
            logging.info(f"⏳ Batch procesando... ({counts.processing} pendientes, {counts.succeeded} OK)")
            return {
                "status": "processing",
                "processing_status": status,
                "batch_id": batch_id,
                "request_counts": {
                    "processing": counts.processing,
                    "succeeded": counts.succeeded,
                    "errored": counts.errored,
                    "canceled": counts.canceled,
                    "expired": counts.expired
                },
                "id_map": id_map  # Mantener para siguiente poll
            }
            
    except ImportError as e:
        logging.error(f"❌ SDK no instalado: {e}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        logging.error(f"❌ Error consultando batch: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return {"status": "error", "error": str(e)}
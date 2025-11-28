# =============================================================================
# PollClaudeBatchResult/__init__.py
# =============================================================================
import logging
import json
import os

logging.basicConfig(level=logging.INFO)

def main(batch_info: dict) -> object:
    """
    Consulta el estado de un Claude Batch Job.
    
    LÓGICA BLINDADA:
    - Si status está en progreso -> Devuelve diccionario (Orchestrator sigue esperando).
    - Si status == 'ended' -> Descarga y devuelve lista (Orchestrator avanza).
    """
    
    try:
        from anthropic import Anthropic
        
        # A. CONFIGURACIÓN
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            return {"status": "error", "error": "ANTHROPIC_API_KEY no configurada"}
        
        batch_id = batch_info.get('batch_id')
        if not batch_id:
            return {"status": "error", "error": "No batch_id provided"}
            
        client = Anthropic(api_key=api_key)
        
        # B. CONSULTAR ESTADO
        message_batch = client.messages.batches.retrieve(batch_id)
        status = message_batch.processing_status
        
        counts = message_batch.request_counts
        succeeded = counts.succeeded if counts else 0
        processing = counts.processing if counts else 0
        
        logging.info(f"🤖 Claude Status: [{status.upper()}] - ID: {batch_id}")
        logging.info(f"📊 Métricas: {succeeded} OK | {processing} Pendientes")

        # ─────────────────────────────────────────────────────────────────
        # CASO A: AÚN PROCESANDO (O CANCELANDO) -> DEVOLVER DICCIONARIO
        # ─────────────────────────────────────────────────────────────────
        if status in ['in_progress', 'canceling']:
            return {
                "status": "processing", # Esto le dice al orquestador que espere
                "processing_status": status,
                "batch_id": batch_id,
                "request_counts": {
                    "succeeded": succeeded,
                    "processing": processing,
                    "errored": counts.errored if counts else 0,
                    "canceled": counts.canceled if counts else 0,
                    "expired": counts.expired if counts else 0
                },
                "id_map": batch_info.get('id_map', [])
            }

        # ─────────────────────────────────────────────────────────────────
        # CASO B: TERMINÓ -> DESCARGAR RESULTADOS
        # ─────────────────────────────────────────────────────────────────
        elif status == "ended":
            logging.info(f"✅ Batch finalizado. Descargando resultados...")
            
            results = []
            for entry in client.messages.batches.results(batch_id):
                try:
                    if entry.result.type == "succeeded":
                        # Extraer contenido
                        custom_id = entry.custom_id
                        chapter_id = custom_id.replace("chapter-", "")
                        message = entry.result.message
                        response_text = message.content[0].text
                        
                        # Parsear JSON (Limpieza de markdown)
                        clean_response = response_text.strip()
                        if clean_response.startswith("```json"): clean_response = clean_response[7:]
                        if clean_response.startswith("```"): clean_response = clean_response[3:]
                        if clean_response.endswith("```"): clean_response = clean_response[:-3]
                        
                        try:
                            edit_data = json.loads(clean_response.strip())
                            
                            # Calcular costo (TU LÓGICA ORIGINAL)
                            input_tokens = message.usage.input_tokens
                            output_tokens = message.usage.output_tokens
                            cost_input = input_tokens * 1.50 / 1_000_000 
                            cost_output = output_tokens * 7.50 / 1_000_000
                            total_cost = cost_input + cost_output

                            # Estructura final
                            item = {
                                'chapter_id': chapter_id,
                                'contenido_editado': edit_data.get('capitulo_editado', response_text),
                                'cambios_realizados': edit_data.get('cambios_realizados', []),
                                'problemas_corregidos': edit_data.get('problemas_corregidos', []),
                                'notas_editor': edit_data.get('notas_editor', ''),
                                'metadata': {
                                    'status': 'success',
                                    'costo_usd': round(total_cost, 4),
                                    'tokens_in': input_tokens,
                                    'tokens_out': output_tokens
                                }
                            }
                            results.append(item)
                            logging.info(f"✅ {custom_id} procesado | Costo: ${total_cost:.4f}")

                        except json.JSONDecodeError:
                            results.append({
                                'chapter_id': chapter_id,
                                'contenido_editado': response_text,
                                'metadata': {'status': 'error_parse'}
                            })
                            
                    elif entry.result.type == "errored":
                        error_msg = str(entry.result.error) if hasattr(entry.result, 'error') else "Unknown error"
                        logging.warning(f"⚠️ Error en item {entry.custom_id}: {error_msg}")
                        
                except Exception as inner_e:
                    logging.error(f"❌ Error procesando item individual: {inner_e}")
                    continue

            if not results:
                return {"status": "completed_no_results", "batch_id": batch_id}
            
            logging.info(f"📥 {len(results)} capítulos descargados correctamente.")
            return results # DEVOLVER LISTA -> ESTO ROMPE EL BUCLE DEL ORQUESTADOR

        # ─────────────────────────────────────────────────────────────────
        # CASO C: ESTADO DESCONOCIDO
        # ─────────────────────────────────────────────────────────────────
        else:
            return {"status": "error", "error": f"Estado desconocido o expirado: {status}"}

    except ImportError as e:
        logging.error(f"❌ SDK no instalado: {e}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        logging.error(f"❌ Error crítico en PollClaude: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return {"status": "error", "error": str(e)}
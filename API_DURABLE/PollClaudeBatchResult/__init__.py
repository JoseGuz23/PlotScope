# =============================================================================
# PollClaudeBatchResult/__init__.py
# =============================================================================
import logging
import json
import os

logging.basicConfig(level=logging.INFO)

def main(batch_info: dict) -> object:
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
        
        # CASO A: PROCESANDO
        if status in ['in_progress', 'canceling']:
            return {
                "status": "processing",
                "processing_status": status,
                "batch_id": batch_id,
                "request_counts": {"succeeded": succeeded, "processing": processing},
                "id_map": batch_info.get('id_map', [])
            }

        # CASO B: TERMINADO
        elif status == "ended":
            logging.info(f"✅ Batch finalizado. Descargando resultados...")
            
            results = []
            for entry in client.messages.batches.results(batch_id):
                try:
                    if entry.result.type == "succeeded":
                        # 1. Extraer texto crudo
                        custom_id = entry.custom_id
                        chapter_id = custom_id.replace("chapter-", "")
                        message = entry.result.message
                        response_text = message.content[0].text
                        
                        # 2. LÓGICA BLINDADA DE LIMPIEZA
                        clean_response = response_text.strip()
                        start_idx = clean_response.find('{')
                        end_idx = clean_response.rfind('}')
                        
                        edit_data = {}
                        parse_success = False
                        
                        # Intentar extraer JSON puro entre llaves
                        if start_idx != -1 and end_idx != -1:
                            json_str = clean_response[start_idx : end_idx + 1]
                            try:
                                edit_data = json.loads(json_str)
                                parse_success = True
                            except json.JSONDecodeError:
                                logging.warning(f"⚠️ JSON decode falló en {custom_id} incluso tras limpieza.")
                        
                        # 3. Determinar contenido final
                        final_content = response_text # Fallback por defecto
                        if parse_success:
                            # Si hay JSON, sacamos el campo limpio
                            final_content = edit_data.get('capitulo_editado', response_text)
                            # Log para confirmar que el fix funcionó
                            if start_idx > 0 or end_idx < len(clean_response) - 1:
                                logging.info(f"🧹 JSON limpiado exitosamente en {custom_id}")
                        else:
                            logging.warning(f"⚠️ Usando TEXTO CRUDO para {custom_id} (No se detectó JSON válido)")

                        # 4. Calcular Costos
                        input_tokens = message.usage.input_tokens
                        output_tokens = message.usage.output_tokens
                        total_cost = (input_tokens * 1.50 / 1_000_000) + (output_tokens * 7.50 / 1_000_000)

                        # 5. Construir Item Final
                        item = {
                            'chapter_id': chapter_id,
                            'contenido_editado': final_content, # ¡AQUÍ ESTÁ LA CLAVE!
                            'cambios_realizados': edit_data.get('cambios_realizados', []),
                            'problemas_corregidos': edit_data.get('problemas_corregidos', []),
                            'notas_editor': edit_data.get('notas_editor', ''),
                            'metadata': {
                                'status': 'success',
                                'costo_usd': round(total_cost, 4),
                                'parsed_json': parse_success
                            }
                        }
                        results.append(item)
                            
                    elif entry.result.type == "errored":
                        logging.error(f"❌ Item error: {entry.custom_id}")
                        
                except Exception as inner_e:
                    logging.error(f"❌ Error procesando item: {inner_e}")
                    continue

            return results

        else:
            return {"status": "error", "error": f"Estado: {status}"}

    except Exception as e:
        logging.error(f"❌ Error crítico: {str(e)}")
        return {"status": "error", "error": str(e)}
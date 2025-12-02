# =============================================================================
# PollClaudeBatchResult/__init__.py - SYLPHRENA 4.0.1
# =============================================================================
# 
# CORRECCIONES v4.0.1:
#   - Fallback NUNCA devuelve JSON crudo
#   - Si el parsing falla completamente, busca contenido original
#   - Logging mejorado para diagnóstico
#
# =============================================================================

import logging
import json
import os
import re

logging.basicConfig(level=logging.INFO)


def clean_json_response(response_text: str) -> tuple:
    """
    Limpieza BLINDADA de respuesta JSON.
    
    Estrategia de 3 niveles:
    1. Limpieza de markdown con regex
    2. Extracción entre { y } si lo anterior falla
    3. Retorna (json_dict, success_flag)
    
    NUNCA devuelve JSON crudo como fallback.
    """
    if not response_text:
        return {}, False
    
    clean = response_text.strip()
    
    # ===========================================
    # NIVEL 1: Limpieza de markdown con regex
    # ===========================================
    clean = re.sub(r'^[\s]*```(?:json)?[\s]*\n?', '', clean)
    clean = re.sub(r'\n?[\s]*```[\s]*$', '', clean)
    clean = clean.strip()
    
    # Intentar parsear después de limpieza de markdown
    try:
        parsed = json.loads(clean)
        return parsed, True
    except json.JSONDecodeError:
        pass
    
    # ===========================================
    # NIVEL 2: Extracción entre llaves { }
    # ===========================================
    start_idx = clean.find('{')
    end_idx = clean.rfind('}')
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        json_str = clean[start_idx : end_idx + 1]
        try:
            parsed = json.loads(json_str)
            return parsed, True
        except json.JSONDecodeError:
            pass
    
    # ===========================================
    # NIVEL 3: Intentar con texto original
    # ===========================================
    try:
        parsed = json.loads(response_text.strip())
        return parsed, True
    except json.JSONDecodeError:
        pass
    
    return {}, False


def extract_edited_content_safe(response_text: str, custom_id: str) -> str:
    """
    Extrae el contenido editado de forma SEGURA.
    
    NUNCA devuelve JSON crudo - si todo falla, devuelve string vacío
    para que la capa de reconstrucción use el contenido original.
    """
    parsed, success = clean_json_response(response_text)
    
    if success and parsed:
        # Extraer campo de contenido editado
        edited_content = parsed.get('capitulo_editado', '')
        
        # Validación: si está vacío o parece JSON, es problema
        if edited_content and not edited_content.strip().startswith('{'):
            logging.info(f"✅ {custom_id}: capitulo_editado extraído correctamente")
            return edited_content
        else:
            logging.warning(f"⚠️ {custom_id}: capitulo_editado vacío o inválido")
    
    # Si el parsing falló completamente, NO devolver JSON crudo
    # Mejor devolver vacío y que ReconstructManuscript use original
    logging.warning(f"⚠️ {custom_id}: Parsing falló, se usará contenido original en reconstrucción")
    return ""


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
            parse_failures = 0
            
            for entry in client.messages.batches.results(batch_id):
                try:
                    if entry.result.type == "succeeded":
                        # 1. Extraer texto crudo
                        custom_id = entry.custom_id
                        chapter_id = custom_id.replace("chapter-", "")
                        message = entry.result.message
                        response_text = message.content[0].text
                        
                        # 2. PARSING BLINDADO
                        parsed, parse_success = clean_json_response(response_text)
                        
                        if parse_success and parsed:
                            # Extraer contenido editado
                            final_content = parsed.get('capitulo_editado', '')
                            cambios = parsed.get('cambios_realizados', [])
                            elementos_preservados = parsed.get('elementos_preservados', [])
                            problemas_corregidos = parsed.get('problemas_corregidos', [])
                            notas = parsed.get('notas_editor', '')
                            
                            # Validación: si capitulo_editado está vacío o es JSON
                            if not final_content or final_content.strip().startswith('{'):
                                logging.warning(f"⚠️ {custom_id}: capitulo_editado vacío/inválido")
                                final_content = ""  # Se usará original en reconstrucción
                                parse_failures += 1
                            else:
                                logging.info(f"✅ {custom_id}: Parseado correctamente")
                        else:
                            # Parsing falló - NO usar JSON crudo
                            logging.warning(f"⚠️ {custom_id}: Parsing falló completamente")
                            final_content = ""
                            cambios = []
                            elementos_preservados = []
                            problemas_corregidos = []
                            notas = "ERROR: Parsing de respuesta falló"
                            parse_failures += 1

                        # 3. Calcular Costos
                        input_tokens = message.usage.input_tokens
                        output_tokens = message.usage.output_tokens
                        # Costos de Claude Sonnet 4.5
                        total_cost = (input_tokens * 3.00 / 1_000_000) + (output_tokens * 15.00 / 1_000_000)

                        # 4. Construir Item Final
                        item = {
                            'chapter_id': chapter_id,
                            'contenido_editado': final_content,
                            'cambios_realizados': cambios,
                            'elementos_preservados': elementos_preservados,
                            'problemas_corregidos': problemas_corregidos,
                            'notas_editor': notas,
                            'metadata': {
                                'status': 'success' if final_content else 'parse_failed',
                                'costo_usd': round(total_cost, 4),
                                'tokens_in': input_tokens,
                                'tokens_out': output_tokens,
                                'parse_success': parse_success and bool(final_content)
                            }
                        }
                        results.append(item)
                    
                    else:
                        # Error en el procesamiento
                        error_type = entry.result.type
                        logging.warning(f"⚠️ {entry.custom_id}: Resultado tipo '{error_type}'")
                        results.append({
                            'chapter_id': entry.custom_id.replace("chapter-", ""),
                            'contenido_editado': '',
                            'error': f'Batch result type: {error_type}',
                            'metadata': {'status': 'error'}
                        })
                
                except Exception as e:
                    logging.error(f"❌ Error procesando entrada: {e}")
                    continue
            
            # Log resumen
            logging.info(f"📊 Resultados: {len(results)} total, {parse_failures} fallos de parsing")
            
            if parse_failures > 0:
                logging.warning(f"⚠️ {parse_failures} fragmentos tendrán contenido vacío - ReconstructManuscript usará original")
            
            return {
                "status": "success",
                "results": results,
                "batch_id": batch_id,
                "total_processed": len(results),
                "parse_failures": parse_failures
            }

        else:
            logging.warning(f"⚠️ Estado inesperado: {status}")
            return {
                "status": "unknown",
                "processing_status": status,
                "batch_id": batch_id
            }

    except Exception as e:
        logging.error(f"❌ Error en PollClaudeBatchResult: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return {"status": "error", "error": str(e)}
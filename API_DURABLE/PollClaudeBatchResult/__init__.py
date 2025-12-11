# =============================================================================
# PollClaudeBatchResult/__init__.py - LYA 4.0.2 CORREGIDO
# =============================================================================
# 
# CORRECCIONES v4.0.2:
#   - USA fragment_metadata_map para enriquecer resultados con metadatos jerárquicos
#   - Pasa fragment_metadata_map en respuestas "processing" para no perderlo
#   - Incluye contenido original para que ReconstructManuscript pueda hacer diff
#   - Fallback: si parsing falla, usa contenido original
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


def main(batch_info: dict) -> object:
    try:
        from anthropic import Anthropic
        
        # =====================================================================
        # A. CONFIGURACIÓN
        # =====================================================================
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            return {"status": "error", "error": "ANTHROPIC_API_KEY no configurada"}
        
        batch_id = batch_info.get('batch_id')
        if not batch_id:
            return {"status": "error", "error": "No batch_id provided"}
        
        # =====================================================================
        # FIX v4.0.2: Obtener fragment_metadata_map para enriquecer resultados
        # =====================================================================
        fragment_metadata_map = batch_info.get('fragment_metadata_map', {})
        
        client = Anthropic(api_key=api_key)
        
        # =====================================================================
        # B. CONSULTAR ESTADO
        # =====================================================================
        message_batch = client.messages.batches.retrieve(batch_id)
        status = message_batch.processing_status
        
        counts = message_batch.request_counts
        succeeded = counts.succeeded if counts else 0
        processing = counts.processing if counts else 0
        
        logging.info(f"🤖 Claude Status: [{status.upper()}] - ID: {batch_id}")
        
        # =====================================================================
        # CASO A: PROCESANDO
        # =====================================================================
        if status in ['in_progress', 'canceling']:
            return {
                "status": "processing",
                "processing_status": status,
                "batch_id": batch_id,
                "request_counts": {"succeeded": succeeded, "processing": processing},
                "id_map": batch_info.get('id_map', []),
                # ─────────────────────────────────────────────────────────────
                # FIX v4.0.2: Pasar metadata para no perderla entre iteraciones
                # ─────────────────────────────────────────────────────────────
                "fragment_metadata_map": fragment_metadata_map
            }

        # =====================================================================
        # CASO B: TERMINADO
        # =====================================================================
        elif status == "ended":
            logging.info(f"✅ Batch finalizado. Descargando resultados...")
            
            results = []
            parse_failures = 0
            
            for entry in client.messages.batches.results(batch_id):
                try:
                    if entry.result.type == "succeeded":
                        # 1. Extraer identificadores
                        custom_id = entry.custom_id
                        chapter_id = custom_id.replace("chapter-", "")
                        
                        # ─────────────────────────────────────────────────────
                        # FIX v4.0.2: Obtener metadatos jerárquicos
                        # ─────────────────────────────────────────────────────
                        fragment_meta = fragment_metadata_map.get(chapter_id, {})
                        
                        # 2. Extraer respuesta
                        message = entry.result.message
                        response_text = message.content[0].text
                        
                        # 3. PARSING BLINDADO
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
                                logging.warning(f"⚠️ {custom_id}: capitulo_editado vacío/inválido, usando original")
                                final_content = fragment_meta.get('content', '')
                                parse_failures += 1
                            else:
                                logging.info(f"✅ {custom_id}: Parseado correctamente")
                        else:
                            # Parsing falló - usar contenido original como fallback
                            logging.warning(f"⚠️ {custom_id}: Parsing falló, usando contenido original")
                            final_content = fragment_meta.get('content', '')
                            cambios = []
                            elementos_preservados = []
                            problemas_corregidos = []
                            notas = "FALLBACK: Se usó contenido original porque parsing falló"
                            parse_failures += 1

                        # 4. Calcular Costos
                        input_tokens = message.usage.input_tokens
                        output_tokens = message.usage.output_tokens
                        total_cost = (input_tokens * 3.00 / 1_000_000) + (output_tokens * 15.00 / 1_000_000)

                        # ─────────────────────────────────────────────────────
                        # FIX v4.0.2: Construir Item con TODOS los metadatos
                        # ─────────────────────────────────────────────────────
                        item = {
                            # Identificadores jerárquicos
                            'chapter_id': chapter_id,
                            'fragment_id': fragment_meta.get('fragment_id', chapter_id),
                            'parent_chapter_id': fragment_meta.get('parent_chapter_id', chapter_id),
                            'fragment_index': fragment_meta.get('fragment_index', 1),
                            'total_fragments': fragment_meta.get('total_fragments', 1),
                            
                            # Metadatos del capítulo
                            'original_title': fragment_meta.get('original_title', 'Sin título'),
                            'titulo_original': fragment_meta.get('original_title', 'Sin título'),
                            'section_type': fragment_meta.get('section_type', 'CHAPTER'),
                            'is_first_fragment': fragment_meta.get('is_first_fragment', True),
                            'is_last_fragment': fragment_meta.get('is_last_fragment', True),
                            
                            # Contenido
                            'contenido_editado': final_content,
                            'contenido_original': fragment_meta.get('content', ''),
                            
                            # Análisis editorial
                            'cambios_realizados': cambios,
                            'elementos_preservados': elementos_preservados,
                            'problemas_corregidos': problemas_corregidos,
                            'notas_editor': notas,
                            
                            # Metadata técnica
                            'metadata': {
                                'status': 'success' if (parse_success and final_content) else 'fallback_used',
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
                        chapter_id = entry.custom_id.replace("chapter-", "")
                        fragment_meta = fragment_metadata_map.get(chapter_id, {})
                        
                        logging.warning(f"⚠️ {entry.custom_id}: Resultado tipo '{error_type}'")
                        
                        # Usar contenido original como fallback
                        results.append({
                            'chapter_id': chapter_id,
                            'fragment_id': fragment_meta.get('fragment_id', chapter_id),
                            'parent_chapter_id': fragment_meta.get('parent_chapter_id', chapter_id),
                            'fragment_index': fragment_meta.get('fragment_index', 1),
                            'total_fragments': fragment_meta.get('total_fragments', 1),
                            'original_title': fragment_meta.get('original_title', 'Sin título'),
                            'section_type': fragment_meta.get('section_type', 'CHAPTER'),
                            'contenido_editado': fragment_meta.get('content', ''),
                            'contenido_original': fragment_meta.get('content', ''),
                            'cambios_realizados': [],
                            'notas_editor': f'ERROR: Batch result type: {error_type}',
                            'metadata': {'status': 'error', 'error_type': error_type}
                        })
                        parse_failures += 1
                
                except Exception as e:
                    logging.error(f"❌ Error procesando entrada: {e}")
                    continue
            
            # Log resumen
            logging.info(f"📊 Resultados: {len(results)} total, {parse_failures} fallbacks")
            
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
                "batch_id": batch_id,
                "fragment_metadata_map": fragment_metadata_map
            }

    except Exception as e:
        logging.error(f"❌ Error en PollClaudeBatchResult: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return {"status": "error", "error": str(e)}
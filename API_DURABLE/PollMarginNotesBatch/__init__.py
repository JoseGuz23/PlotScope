# =============================================================================
# PollMarginNotesBatch/__init__.py - LYA 5.0
# =============================================================================
# NUEVA FUNCIÓN: Poll de resultados del batch de notas de margen
# =============================================================================

import logging
import json
import os
import re

logging.basicConfig(level=logging.INFO)


def main(batch_info: dict) -> dict:
    """
    Poll del estado del batch de notas de margen.
    
    Input:
        - batch_id: ID del batch de Claude
        - chapter_metadata: Mapa de metadata por capítulo
    
    Output:
        - status: 'processing' | 'success' | 'failed'
        - results: Lista de notas por capítulo (si success)
    """
    
    try:
        from anthropic import Anthropic
        
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            return {"error": "ANTHROPIC_API_KEY no configurada", "status": "config_error"}
        
        batch_id = batch_info.get('batch_id')
        chapter_metadata = batch_info.get('chapter_metadata', {})
        
        if not batch_id:
            return {"error": "batch_id no proporcionado", "status": "error"}
        
        client = Anthropic(api_key=api_key)
        
        # Consultar estado
        batch = client.messages.batches.retrieve(batch_id)
        status = batch.processing_status
        
        logging.info(f"📊 Estado batch notas [{batch_id}]: {status}")
        
        if status in ['in_progress', 'canceling']:
            return {
                "status": "processing",
                "batch_id": batch_id,
                "state": status,
                "chapter_metadata": chapter_metadata
            }
        
        if status == 'canceled':
            return {"status": "failed", "error": "Batch cancelado"}
        
        if status != 'ended':
            return {
                "status": "processing",
                "batch_id": batch_id,
                "state": status,
                "chapter_metadata": chapter_metadata
            }
        
        # Batch completado - procesar resultados
        logging.info(f"✅ Batch notas completado. Descargando resultados...")
        
        results = []
        all_notes = []
        
        for result in client.messages.batches.results(batch_id):
            custom_id = result.custom_id  # "margin-{ch_id}"
            ch_id = custom_id.replace("margin-", "")
            
            # Obtener metadata
            metadata = chapter_metadata.get(ch_id, {})
            
            if result.result.type == "succeeded":
                message = result.result.message
                content = message.content[0].text if message.content else ""
                
                # Parsear JSON
                parsed = parse_margin_notes_response(content, ch_id)
                
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
                
                logging.info(f"  ✓ Cap {ch_id}: {len(parsed.get('notas_margen', []))} notas")
            else:
                logging.warning(f"  ✗ Cap {ch_id}: {result.result.type}")
                results.append({
                    "chapter_id": metadata.get('parent_chapter_id', ch_id),
                    "fragment_id": ch_id,
                    "notas_margen": [],
                    "status": "failed",
                    "error": str(result.result.type)
                })
        
        # Estadísticas
        stats = calcular_estadisticas_notas(all_notes)
        
        logging.info(f"📊 Total notas generadas: {len(all_notes)}")
        logging.info(f"📊 Por tipo: {stats['por_tipo']}")
        
        return {
            "status": "success",
            "results": results,
            "all_notes": all_notes,
            "statistics": stats,
            "total": len(results),
            "errors": len([r for r in results if r.get('status') == 'failed'])
        }
        
    except ImportError as e:
        logging.error(f"❌ SDK no instalado: {e}")
        return {"error": str(e), "status": "import_error"}
    except Exception as e:
        logging.error(f"❌ Error en poll: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return {"error": str(e), "status": "error"}


def parse_margin_notes_response(content: str, chapter_id: str) -> dict:
    """Parsea la respuesta de Claude para notas de margen."""
    
    # Nivel 1: JSON directo
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    
    # Nivel 2: Extraer JSON del texto
    try:
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            return json.loads(json_match.group())
    except:
        pass
    
    # Nivel 3: Buscar array de notas
    try:
        array_match = re.search(r'\[[\s\S]*\]', content)
        if array_match:
            notas = json.loads(array_match.group())
            return {"notas_margen": notas, "resumen_capitulo": {}}
    except:
        pass
    
    # Fallback: Sin notas
    logging.warning(f"⚠️ No se pudo parsear respuesta para cap {chapter_id}")
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

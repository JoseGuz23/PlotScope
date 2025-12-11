# =============================================================================
# Orchestrator/__init__.py - LYA 6.0 "Editor Reflexivo"
# =============================================================================
# VERSIÓN 6.0 - NUEVAS CAPACIDADES:
#   1. Reflection Loops: Edición iterativa con crítica (reduce alucinaciones 70%)
#   2. Análisis de Arco Emocional: Sentiment analysis por capítulo
#   3. Detección Sensorial: Análisis cuantitativo de Show vs Tell
#   4. Context Caching: Optimización de costos (ahorro ~15%)
#   5. Modelos actualizados: Gemini 2.5 / Claude 4.5
#
# OPTIMIZACIONES HEREDADAS DE v5.1:
#   1. Polling Adaptativo: Empieza rápido (10s), luego incrementa
#   2. Paralelización: Fase 4 y 5 ejecutan simultáneamente
#   3. [FIX] Inyección de contenido: Repara capítulos vacíos antes de edición
# =============================================================================

import azure.functions as func
import azure.durable_functions as df
import logging
import json
from datetime import timedelta

# Importaciones de LYA 6.0
try:
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from config_models import (
        REFLECTION_QUALITY_THRESHOLD,
        ENABLE_EMOTIONAL_ARC_ANALYSIS,
        ENABLE_SENSORY_DETECTION,
        ENABLE_REFLECTION_LOOPS
    )
    logging.info("[LYA 6.0] Configuración de modelos cargada exitosamente")
except ImportError as e:
    logging.warning(f"[LYA 6.0] No se pudo cargar config_models: {e}. Usando valores por defecto.")
    REFLECTION_QUALITY_THRESHOLD = 7.0
    ENABLE_EMOTIONAL_ARC_ANALYSIS = True
    ENABLE_SENSORY_DETECTION = True
    ENABLE_REFLECTION_LOOPS = True

# =============================================================================
# CONFIGURACIÓN OPTIMIZADA
# =============================================================================

LIMIT_TO_FIRST_N_CHAPTERS = 3  # None = procesar todos
MAX_WAIT_MINUTES = 60

# NUEVO: Polling adaptativo - Empieza rápido, luego incrementa
def get_adaptive_interval(batch_type: str, attempt: int) -> int:
    """
    Polling inteligente: empieza rápido y va incrementando.
    """
    if batch_type in ['gemini', 'gemini_flash']:
        # Secuencia: 10, 15, 20, 25, 30, 35, 40, 45, 45, ...
        interval = 10 + (attempt * 5)
        return min(interval, 45)
    
    elif batch_type == 'claude':
        # Secuencia: 20, 35, 50, 65, 80, 90, 90, ...
        interval = 20 + (attempt * 15)
        return min(interval, 90)
    
    else:
        return 30

# =============================================================================
# HELPERS OPTIMIZADOS
# =============================================================================

def run_gemini_pro_batch_optimized(context, analysis_type: str, items: list, bible: dict = None):
    logging.info(f"")
    logging.info(f"{'='*60}")
    logging.info(f">>> BATCH GEMINI PRO: {analysis_type.upper()}")
    logging.info(f"    Items: {len(items)} | Polling: ADAPTATIVO")
    logging.info(f"{'='*60}")
    
    batch_input = {
        'analysis_type': analysis_type,
        'items': items,
        'bible': bible or {}
    }
    
    try:
        batch_info = yield context.call_activity('SubmitGeminiProBatch', batch_input)
    except Exception as e:
        logging.error(f"[ERROR] en SubmitGeminiProBatch [{analysis_type}]: {str(e)}")
        raise
    
    if batch_info.get('status') == 'error':
        logging.error(f"[ERROR] Submit falló [{analysis_type}]: {batch_info.get('error')}")
        raise Exception(f"Error submit batch {analysis_type}: {batch_info.get('error')}")
    
    job_name = batch_info.get('batch_job_name', 'unknown')
    logging.info(f"[BATCH] Batch {analysis_type} creado: {job_name}")
    
    for attempt in range(MAX_WAIT_MINUTES):
        interval = get_adaptive_interval('gemini', attempt)
        next_check = context.current_utc_datetime + timedelta(seconds=interval)
        yield context.create_timer(next_check)
        
        try:
            result = yield context.call_activity('PollGeminiProBatchResult', batch_info)
        except Exception as e:
            logging.error(f"[ERROR] Poll [{analysis_type}] intento {attempt+1}: {str(e)}")
            continue
        
        status = result.get('status', 'unknown')
        
        if status == 'success':
            total_time = sum(get_adaptive_interval('gemini', i) for i in range(attempt + 1))
            logging.info(f"[OK] BATCH {analysis_type.upper()} COMPLETADO en ~{total_time}s ({attempt+1} polls)")
            return result.get('results', [])
        
        elif status == 'failed':
            raise Exception(f"Batch {analysis_type} falló: {result.get('error')}")
        
        elif status == 'processing':
            batch_info = result
            state = result.get('state', 'unknown')
            logging.info(f"[WAIT] [{analysis_type}] Poll {attempt+1} (+{interval}s) - {state}")
            context.set_custom_status(f"Batch {analysis_type}: {state} (poll {attempt+1})")
        
        else:
            batch_info = result

    raise Exception(f"Timeout en Batch {analysis_type}")


def analyze_with_batch_api_v2_optimized(context, fragments):
    logging.info(f">>> ANÁLISIS CAPA 1 (FACTUAL) - POLLING ADAPTATIVO")
    context.set_custom_status("Enviando Batch Capa 1...")
    
    try:
        batch_info = yield context.call_activity('SubmitBatchAnalysis', fragments)
    except Exception as e:
        logging.error(f"[ERROR] en SubmitBatchAnalysis: {str(e)}")
        raise
    
    if batch_info.get('error'):
        raise Exception(f"Error submit Batch C1: {batch_info.get('error')}")
    
    batch_results = []
    
    for attempt in range(MAX_WAIT_MINUTES):
        interval = get_adaptive_interval('gemini_flash', attempt)
        next_check = context.current_utc_datetime + timedelta(seconds=interval)
        yield context.create_timer(next_check)
        
        try:
            result = yield context.call_activity('PollBatchResult', batch_info)
        except Exception as e:
            logging.error(f"[ERROR] en PollBatchResult intento {attempt+1}: {str(e)}")
            continue
        
        if isinstance(result, list):
            batch_results = result
            total_time = sum(get_adaptive_interval('gemini_flash', i) for i in range(attempt + 1))
            logging.info(f"[OK] BATCH CAPA 1 COMPLETADO - {len(batch_results)} análisis en ~{total_time}s")
            break
        
        status = result.get('status', 'unknown')
        if status in ['failed', 'error']:
            break
        
        batch_info = result
        logging.info(f"[WAIT] Capa 1 - Poll {attempt+1} (+{interval}s)")
        context.set_custom_status(f"Batch C1: {result.get('state', 'processing')} (poll {attempt+1})")
    
    # Identificar fragmentos faltantes
    successful_ids = {str(r.get('fragment_id') or r.get('chapter_id') or r.get('id')) for r in batch_results if r}
    failed_fragments = [f for f in fragments if str(f.get('id')) not in successful_ids]
    
    if not failed_fragments:
        return batch_results

    # Rescate de fragmentos fallidos
    logging.info(f"[RECOVERY] RESCATANDO {len(failed_fragments)} FRAGMENTOS")
    final_results = list(batch_results)
    
    for frag in failed_fragments[:10]:
        try:
            res = yield context.call_activity('AnalyzeChapter', frag)
            if res:
                final_results.append(res)
        except:
            pass
    
    return final_results


def run_margin_notes_batch_optimized(context, chapters: list, carta_editorial: dict, bible: dict, book_metadata: dict):
    logging.info(f"")
    logging.info(f"{'='*60}")
    logging.info(f">>> FASE 8: NOTAS DE MARGEN - POLLING ADAPTATIVO")
    logging.info(f"    Capítulos: {len(chapters)}")
    logging.info(f"{'='*60}")
    
    batch_input = {
        'chapters': chapters,
        'carta_editorial': carta_editorial,
        'bible': bible,
        'book_metadata': book_metadata
    }
    
    try:
        batch_info = yield context.call_activity('SubmitMarginNotes', batch_input)
    except Exception as e:
        logging.error(f"[ERROR] en SubmitMarginNotes: {str(e)}")
        raise
    
    if batch_info.get('status') == 'error':
        raise Exception(f"Error submit notas: {batch_info.get('error')}")
    
    batch_id = batch_info.get('batch_id')
    logging.info(f"[BATCH] Batch notas creado: {batch_id}")
    
    for attempt in range(MAX_WAIT_MINUTES):
        interval = get_adaptive_interval('claude', attempt)
        next_check = context.current_utc_datetime + timedelta(seconds=interval)
        yield context.create_timer(next_check)
        
        try:
            result = yield context.call_activity('PollMarginNotesBatch', batch_info)
        except Exception as e:
            logging.error(f"[ERROR] en PollMarginNotesBatch intento {attempt+1}: {str(e)}")
            continue
        
        status = result.get('status', 'unknown')
        
        if status == 'success':
            total_time = sum(get_adaptive_interval('claude', i) for i in range(attempt + 1))
            logging.info(f"[OK] NOTAS COMPLETADAS en ~{total_time}s")
            logging.info(f"    Total notas: {len(result.get('all_notes', []))}")
            return result
        
        elif status == 'failed':
            raise Exception(f"Batch notas falló: {result.get('error')}")
        
        elif status == 'processing':
            batch_info = result
            logging.info(f"[WAIT] Notas - Poll {attempt+1} (+{interval}s)")
            context.set_custom_status(f"Batch notas: processing (poll {attempt+1})")
        
        else:
            batch_info = result

    raise Exception(f"Timeout en Batch notas")


def edit_with_claude_batch_v2_optimized(context, edit_requests: list, bible: dict, consolidated: list, 
                                        arc_map: dict, margin_notes: dict, book_metadata: dict):
    logging.info(f"")
    logging.info(f"{'='*60}")
    logging.info(f">>> EDICIÓN PROFESIONAL - POLLING ADAPTATIVO")
    logging.info(f"    Capítulos: {len(edit_requests)}")
    logging.info(f"{'='*60}")
    
    batch_input = {
        'edit_requests': edit_requests,
        'bible': bible,
        'consolidated_chapters': consolidated,
        'arc_map': arc_map,
        'margin_notes': margin_notes,
        'book_metadata': book_metadata
    }
    
    try:
        batch_info = yield context.call_activity('SubmitClaudeBatch', batch_input)
    except Exception as e:
        logging.error(f"[ERROR] en SubmitClaudeBatch: {str(e)}")
        raise
    
    if batch_info.get('status') == 'error':
        raise Exception(f"Error submit edición: {batch_info.get('error')}")
    
    batch_id = batch_info.get('batch_id')
    logging.info(f"[BATCH] Batch edición creado: {batch_id}")
    
    for attempt in range(MAX_WAIT_MINUTES):
        interval = get_adaptive_interval('claude', attempt)
        next_check = context.current_utc_datetime + timedelta(seconds=interval)
        yield context.create_timer(next_check)
        
        try:
            result = yield context.call_activity('PollClaudeBatchResult', batch_info)
        except Exception as e:
            logging.error(f"[ERROR] en PollClaudeBatchResult intento {attempt+1}: {str(e)}")
            continue
        
        status = result.get('status', 'unknown')
        
        if status == 'success':
            total_time = sum(get_adaptive_interval('claude', i) for i in range(attempt + 1))
            logging.info(f"[OK] EDICIÓN COMPLETADA en ~{total_time}s")
            # FIX: PollClaudeBatchResult devuelve 'results', no 'edited_chapters'
            edited_chapters = result.get('results', result.get('edited_chapters', []))
            logging.info(f"✅ Capítulos editados recibidos: {len(edited_chapters)}")
            return edited_chapters
        
        elif status == 'failed':
            raise Exception(f"Batch edición falló: {result.get('error')}")
        
        elif status == 'processing':
            batch_info = result
            logging.info(f"[WAIT] Edición - Poll {attempt+1} (+{interval}s)")
            context.set_custom_status(f"Batch edición: processing (poll {attempt+1})")
        
        else:
            batch_info = result

    raise Exception(f"Timeout en Batch edición")


def run_parallel_structural_qualitative(context, consolidated: list):
    logging.info(f"")
    logging.info(f"{'='*60}")
    logging.info(f">>> FASE 4+5: ANÁLISIS PARALELO (STRUCTURAL + QUALITATIVE)")
    logging.info(f"    Estrategia: EJECUTAR SIMULTÁNEAMENTE")
    logging.info(f"{'='*60}")
    
    logging.info("[PARALLEL] Enviando ambos batches simultáneamente...")
    
    batch_input_structural = {
        'analysis_type': 'layer2_structural',
        'items': consolidated,
        'bible': {}
    }
    
    batch_input_qualitative = {
        'analysis_type': 'layer3_qualitative',
        'items': consolidated,
        'bible': {}
    }
    
    try:
        batch_infos = yield context.task_all([
            context.call_activity('SubmitGeminiProBatch', batch_input_structural),
            context.call_activity('SubmitGeminiProBatch', batch_input_qualitative)
        ])
        
        batch_info_l2 = batch_infos[0]
        batch_info_l3 = batch_infos[1]
        
        logging.info(f"[PARALLEL] ✅ Ambos batches enviados")
        
    except Exception as e:
        logging.error(f"[ERROR] Enviando batches paralelos: {str(e)}")
        raise
    
    layer2_results = None
    layer3_results = None
    
    for attempt in range(MAX_WAIT_MINUTES):
        interval = get_adaptive_interval('gemini', attempt)
        next_check = context.current_utc_datetime + timedelta(seconds=interval)
        yield context.create_timer(next_check)
        
        poll_tasks = []
        if layer2_results is None:
            poll_tasks.append(context.call_activity('PollGeminiProBatchResult', batch_info_l2))
        if layer3_results is None:
            poll_tasks.append(context.call_activity('PollGeminiProBatchResult', batch_info_l3))
        
        if not poll_tasks:
            break
        
        try:
            poll_results = yield context.task_all(poll_tasks)
            
            result_idx = 0
            if layer2_results is None:
                result_l2 = poll_results[result_idx]
                result_idx += 1
                
                if result_l2.get('status') == 'success':
                    layer2_results = result_l2.get('results', [])
                    logging.info(f"[PARALLEL] ✅ Layer 2 COMPLETADO - {len(layer2_results)} análisis")
                elif result_l2.get('status') == 'failed':
                    raise Exception(f"Batch structural falló: {result_l2.get('error')}")
                else:
                    batch_info_l2 = result_l2
            
            if layer3_results is None:
                result_l3 = poll_results[result_idx]
                
                if result_l3.get('status') == 'success':
                    layer3_results = result_l3.get('results', [])
                    logging.info(f"[PARALLEL] ✅ Layer 3 COMPLETADO - {len(layer3_results)} análisis")
                elif result_l3.get('status') == 'failed':
                    raise Exception(f"Batch qualitative falló: {result_l3.get('error')}")
                else:
                    batch_info_l3 = result_l3
            
            status_parts = []
            status_parts.append("L2:✓" if layer2_results else "L2:processing")
            status_parts.append("L3:✓" if layer3_results else "L3:processing")
            
            logging.info(f"[PARALLEL] Poll {attempt+1} (+{interval}s) - {' | '.join(status_parts)}")
            context.set_custom_status(f"Análisis paralelo: {' '.join(status_parts)}")
            
        except Exception as e:
            logging.error(f"[ERROR] Poll paralelo intento {attempt+1}: {str(e)}")
            continue
    
    if layer2_results is None or layer3_results is None:
        raise Exception("Timeout en análisis paralelo")
    
    logging.info(f"[PARALLEL] 🎉 AMBOS ANÁLISIS COMPLETADOS")
    return layer2_results, layer3_results


# =============================================================================
# ORCHESTRATOR PRINCIPAL
# =============================================================================

def orchestrator_function(context: df.DurableOrchestrationContext):
    try:
        start_time = context.current_utc_datetime
        tiempos = {}
        
        logging.info(f"{'#'*70}")
        logging.info(f"#  LYA 5.1 FIX - DEVELOPMENTAL EDITOR AI")
        logging.info(f"#  Job ID: {context.instance_id}")
        logging.info(f"#  Patch: Content Injection + Polling Adaptativo")
        logging.info(f"{'#'*70}")
        
        input_data = context.get_input()
        if isinstance(input_data, str):
            try:
                input_data = json.loads(input_data)
            except: pass
        if not isinstance(input_data, dict): input_data = {}

        job_id = input_data.get('job_id', context.instance_id)
        blob_path = input_data.get('blob_path', '')
        book_name = input_data.get('book_name', 'Sin título')
        book_metadata = {'title': book_name, 'job_id': job_id, 'blob_path': blob_path}

        # --- FASE 1: SEGMENTACIÓN ---
        logging.info(f">>> FASE 1: SEGMENTACIÓN")
        context.set_custom_status("Fase 1: Segmentando...")
        
        seg_result = yield context.call_activity('SegmentBook', {'job_id': job_id, 'blob_path': blob_path})
        if isinstance(seg_result, str): seg_result = json.loads(seg_result)
        if seg_result.get('error'): raise Exception(f"Segmentación: {seg_result.get('error')}")
        
        fragments = seg_result.get('fragments', [])
        book_metadata.update(seg_result.get('book_metadata', {}))
        logging.info(f"[OK] {len(fragments)} fragmentos generados")
        
        t1 = context.current_utc_datetime
        tiempos['segmentacion'] = str(t1 - start_time)

        # --- FASE 2: ANÁLISIS CAPA 1 ---
        logging.info(f">>> FASE 2: ANÁLISIS CAPA 1")
        context.set_custom_status("Fase 2: Capa 1...")
        
        layer1_results = yield from analyze_with_batch_api_v2_optimized(context, fragments)
        t2 = context.current_utc_datetime
        tiempos['capa1'] = str(t2 - t1)

        # --- FASE 3: CONSOLIDACIÓN ---
        logging.info(f">>> FASE 3: CONSOLIDACIÓN")
        context.set_custom_status("Fase 3: Consolidando...")
        
        consol_input = {'fragment_analyses': layer1_results, 'chapter_map': {}}
        consolidated = yield context.call_activity('ConsolidateFragmentAnalyses', consol_input)
        if isinstance(consolidated, str): consolidated = json.loads(consolidated)
        if not consolidated: raise Exception("Consolidación falló")
        
        logging.info(f"[OK] Consolidación completada: {len(consolidated)} capítulos")
        t3 = context.current_utc_datetime
        tiempos['consolidacion'] = str(t3 - t2)

        # =====================================================================
        # [FIX] INYECCIÓN DE CONTENIDO PERDIDO
        # =====================================================================
        # Recuperamos el texto de los fragmentos originales y lo metemos en los capítulos consolidados
        logging.info(f"[FIX] Reinyectando contenido de texto en capítulos consolidados...")
        
        for chapter in consolidated:
            chap_id = str(chapter.get('chapter_id', ''))
            
            # Buscar fragmentos que coincidan con este capítulo
            relevant_frags = [
                f for f in fragments 
                if str(f.get('chapter_id', '')) == chap_id or str(f.get('id', '')) == chap_id
            ]
            
            # Ordenar por secuencia
            relevant_frags.sort(key=lambda x: x.get('sequence', 0))
            
            # Unir el texto
            full_content = "\n\n".join([f.get('content', '') for f in relevant_frags])
            
            # Inyectar en el objeto del capítulo
            chapter['content'] = full_content
            
            # Recalculamos métricas si están en 0
            words = len(full_content.split())
            if 'metricas_agregadas' not in chapter: chapter['metricas_agregadas'] = {}
            if 'estructura' not in chapter['metricas_agregadas']: chapter['metricas_agregadas']['estructura'] = {}
            
            current_words = chapter['metricas_agregadas']['estructura'].get('total_palabras', 0)
            if current_words == 0:
                chapter['metricas_agregadas']['estructura']['total_palabras'] = words

        logging.info(f"[FIX] Texto inyectado exitosamente en {len(consolidated)} capítulos.")
        # =====================================================================

        # --- FASE 4+5: PARALELO ---
        logging.info(f">>> OPTIMIZACIÓN: EJECUTANDO FASE 4 Y 5 EN PARALELO")
        context.set_custom_status("Fase 4+5: Análisis paralelo...")
        
        layer2_results, layer3_results = yield from run_parallel_structural_qualitative(context, consolidated)
        
        for i, ch in enumerate(consolidated):
            ch_id = str(ch.get('chapter_id', i))
            l2 = next((r for r in layer2_results if str(r.get('chapter_id')) == ch_id), {})
            l3 = next((r for r in layer3_results if str(r.get('chapter_id')) == ch_id), {})
            ch['layer2_structural'] = l2
            ch['layer3_qualitative'] = l3
        
        t4_5 = context.current_utc_datetime
        tiempos['capa2_y_3_paralelo'] = str(t4_5 - t3)

        # =====================================================================
        # FASE 5.5: ANÁLISIS DE ARCO EMOCIONAL (LYA 6.0)
        # =====================================================================
        emotional_arc_result = {}
        if ENABLE_EMOTIONAL_ARC_ANALYSIS:
            logging.info(f"")
            logging.info(f"{'='*60}")
            logging.info(f">>> FASE 5.5: ANÁLISIS DE ARCO EMOCIONAL (LYA 6.0)")
            logging.info(f"    Capítulos: {len(consolidated)}")
            logging.info(f"{'='*60}")
            context.set_custom_status("Fase 5.5: Arco emocional...")

            try:
                emotional_arc_result = yield context.call_activity('EmotionalArcAnalysis', consolidated)
                if isinstance(emotional_arc_result, str):
                    emotional_arc_result = json.loads(emotional_arc_result)

                # Inyectar en consolidated para Biblia
                for chapter in consolidated:
                    chap_id = str(chapter.get('chapter_id'))
                    arc = next((a for a in emotional_arc_result.get('emotional_arcs', [])
                               if str(a.get('chapter_id')) == chap_id), {})
                    chapter['emotional_arc'] = arc

                logging.info(f"[OK] Análisis emocional completado")
                logging.info(f"    Patrón global: {emotional_arc_result.get('global_arc', {}).get('emotional_pattern', 'N/A')}")

            except Exception as e:
                logging.error(f"[ERROR] Análisis emocional falló: {e}")
                # Continuar sin análisis emocional

        t5_5 = context.current_utc_datetime
        tiempos['analisis_emocional'] = str(t5_5 - t4_5)

        # =====================================================================
        # FASE 5.6: DETECCIÓN SENSORIAL (LYA 6.0)
        # =====================================================================
        sensory_result = {}
        if ENABLE_SENSORY_DETECTION:
            logging.info(f"")
            logging.info(f"{'='*60}")
            logging.info(f">>> FASE 5.6: DETECCIÓN SENSORIAL (LYA 6.0)")
            logging.info(f"    Capítulos: {len(consolidated)}")
            logging.info(f"{'='*60}")
            context.set_custom_status("Fase 5.6: Análisis sensorial...")

            try:
                sensory_result = yield context.call_activity('SensoryDetectionAnalysis', consolidated)
                if isinstance(sensory_result, str):
                    sensory_result = json.loads(sensory_result)

                # Inyectar en consolidated para notas de margen
                for chapter in consolidated:
                    chap_id = str(chapter.get('chapter_id'))
                    analysis = next((a for a in sensory_result.get('sensory_analyses', [])
                                    if str(a.get('chapter_id')) == chap_id), {})
                    chapter['sensory_analysis'] = analysis

                global_metrics = sensory_result.get('global_metrics', {})
                logging.info(f"[OK] Detección sensorial completada")
                logging.info(f"    Showing ratio global: {global_metrics.get('avg_showing_ratio', 0):.2%}")

            except Exception as e:
                logging.error(f"[ERROR] Detección sensorial falló: {e}")
                # Continuar sin análisis sensorial

        t5_6 = context.current_utc_datetime
        tiempos['deteccion_sensorial'] = str(t5_6 - t5_5)

        # --- FASE 6: BIBLIA ---
        logging.info(f"")
        logging.info(f"{'='*60}")
        logging.info(f">>> FASE 6: BIBLIA NARRATIVA")
        logging.info(f"{'='*60}")
        context.set_custom_status("Fase 6: Biblia...")
        
        full_text = "\n".join([f"CAP {f['title']}: {f['content'][:600]}..." for f in fragments])
        holistic = yield context.call_activity('HolisticReading', full_text)
        if isinstance(holistic, str): holistic = json.loads(holistic)
        
        bible_in = {
            "chapter_analyses": consolidated,
            "holistic_analysis": holistic,
            "book_metadata": book_metadata
        }
        bible = yield context.call_activity('CreateBible', bible_in)
        if isinstance(bible, str): bible = json.loads(bible)
        
        t6 = context.current_utc_datetime
        tiempos['biblia'] = str(t6 - t4_5)
        
        # GUARDAR PRELIMINAR
        pre_save_payload = {
            'job_id': job_id,
            'book_name': book_name,
            'bible': bible,
            'consolidated_chapters': consolidated,
            'statistics': {}, 
            'tiempos': tiempos
        }
        try:
            yield context.call_activity('SaveOutputs', pre_save_payload)
        except Exception as e:
            logging.error(f"Error guardado intermedio: {e}")
        
        # PAUSA
        logging.info(f"[WAIT] Esperando aprobación humana de la Biblia...")
        context.set_custom_status("Esperando aprobacion de Biblia...")
        yield context.wait_for_external_event("BibleApproved")
        logging.info(f"[RESUME] Biblia aprobada.")

        # --- FASE 7: CARTA ---
        logging.info(f">>> FASE 7: CARTA EDITORIAL")
        context.set_custom_status("Fase 7: Carta Editorial...")
        
        carta_input = {
            'bible': bible,
            'consolidated_chapters': consolidated,
            'fragments': fragments,
            'book_metadata': book_metadata
        }
        carta_result = yield context.call_activity('GenerateEditorialLetter', carta_input)
        if isinstance(carta_result, str): carta_result = json.loads(carta_result)
        
        carta_editorial = carta_result.get('carta_editorial', {})
        carta_markdown = carta_result.get('carta_markdown', '')
        
        t7 = context.current_utc_datetime
        tiempos['carta_editorial'] = str(t7 - t6)

        # --- FASE 8: NOTAS ---
        logging.info(f">>> FASE 8: NOTAS DE MARGEN")
        context.set_custom_status("Fase 8: Notas de margen...")
        
        margin_result = yield from run_margin_notes_batch_optimized(context, fragments, carta_editorial, bible, book_metadata)
        margin_notes_by_chapter = {}
        for ch_result in margin_result.get('results', []):
            ch_id = str(ch_result.get('chapter_id', ch_result.get('fragment_id', '?')))
            margin_notes_by_chapter[ch_id] = ch_result.get('notas_margen', [])
        
        t8 = context.current_utc_datetime
        tiempos['notas_margen'] = str(t8 - t7)

        # --- FASE 9: ARCOS ---
        logging.info(f">>> FASE 9: ARCOS POR CAPÍTULO")
        context.set_custom_status("Fase 9: Arcos...")
        arc_results = yield from run_gemini_pro_batch_optimized(context, 'arc_maps', consolidated, bible=bible)
        arc_map_dict = {str(r['chapter_id']): r for r in arc_results}
        t9 = context.current_utc_datetime
        tiempos['arcos'] = str(t9 - t8)

        # =====================================================================
        # FASE 10: EDICIÓN CON REFLECTION LOOPS SELECTIVOS (LYA 6.0)
        # =====================================================================
        logging.info(f"")
        logging.info(f"{'='*60}")
        logging.info(f">>> FASE 10: EDICIÓN PROFESIONAL CON REFLECTION (LYA 6.0)")
        logging.info(f"    Estrategia: Reflection para capítulos problemáticos, single-pass para buenos")
        logging.info(f"    Umbral de calidad: {REFLECTION_QUALITY_THRESHOLD}")
        logging.info(f"{'='*60}")
        context.set_custom_status("Fase 10: Edición inteligente...")

        edited_fragments = []
        reflection_stats_global = {
            'total_chapters': 0,
            'chapters_with_reflection': 0,
            'chapters_single_pass': 0,
            'avg_iterations': 0,
            'total_iterations': 0
        }

        if ENABLE_REFLECTION_LOOPS:
            # EDICIÓN SELECTIVA CON REFLECTION LOOPS
            logging.info(f"[REFLECTION] Modo activado - Analizando calidad por capítulo...")

            for i, chapter in enumerate(consolidated):
                chapter_id = chapter.get('chapter_id', i)
                qualitative_data = chapter.get('layer3_qualitative', {})
                qualitative_score = qualitative_data.get('score_global', 10.0)

                reflection_stats_global['total_chapters'] += 1

                # Decisión: ¿Reflection o single-pass?
                if qualitative_score < REFLECTION_QUALITY_THRESHOLD:
                    # CAPÍTULO PROBLEMÁTICO → REFLECTION LOOP
                    logging.info(f"")
                    logging.info(f"   📖 Capítulo {chapter_id}: Score {qualitative_score:.1f} → REFLECTION LOOP")
                    context.set_custom_status(f"Reflection: Cap {chapter_id} (score {qualitative_score:.1f})...")

                    reflection_stats_global['chapters_with_reflection'] += 1

                    # Preparar input para ReflectionEditingLoop
                    reflection_input = {
                        'chapter': chapter,
                        'bible': bible,
                        'margin_notes': margin_notes_by_chapter.get(str(chapter_id), []),
                        'arc_map': arc_map_dict.get(str(chapter_id), {}),
                        'consolidated_chapters': consolidated,
                        'metadata': book_metadata
                    }

                    try:
                        edited_result = yield context.call_activity('ReflectionEditingLoop', reflection_input)
                        if isinstance(edited_result, str):
                            edited_result = json.loads(edited_result)

                        # Extraer stats
                        stats = edited_result.get('reflection_stats', {})
                        iterations = stats.get('iterations_used', 1)
                        final_score = stats.get('final_score', 0)
                        improvement = stats.get('improvement_delta', 0)

                        reflection_stats_global['total_iterations'] += iterations

                        logging.info(f"      ✅ Completado: {iterations} iter, score {final_score:.1f} (+{improvement:.1f})")

                        # Crear fragmento editado compatible con Fase 11
                        edited_fragment = {
                            'chapter_id': chapter_id,
                            'fragment_id': chapter_id,
                            'contenido_editado': edited_result.get('edited_content', ''),
                            'cambios_estructurados': edited_result.get('changes', []),
                            'reflection_stats': stats
                        }
                        edited_fragments.append(edited_fragment)

                    except Exception as e:
                        logging.error(f"      ❌ Error en reflection: {e}")
                        # Fallback: añadir original sin editar
                        edited_fragments.append({
                            'chapter_id': chapter_id,
                            'fragment_id': chapter_id,
                            'contenido_editado': chapter.get('content', ''),
                            'cambios_estructurados': [],
                            'error': str(e)
                        })

                else:
                    # CAPÍTULO BUENO → SINGLE PASS (método v5.3)
                    logging.info(f"   📖 Capítulo {chapter_id}: Score {qualitative_score:.1f} → SINGLE PASS")
                    reflection_stats_global['chapters_single_pass'] += 1

                    # Usar el método tradicional batch para este capítulo
                    # (Nota: En producción, podrías optimizar agrupando múltiples capítulos "buenos" en un solo batch)
                    edit_reqs = [{'chapter': frag} for frag in fragments if str(frag.get('id', '')) == str(chapter_id) or str(frag.get('chapter_id', '')) == str(chapter_id)]

                    if edit_reqs:
                        try:
                            single_edited = yield from edit_with_claude_batch_v2_optimized(
                                context, edit_reqs, bible, consolidated, arc_map_dict, margin_notes_by_chapter, book_metadata
                            )
                            edited_fragments.extend(single_edited)
                            reflection_stats_global['total_iterations'] += 1
                        except Exception as e:
                            logging.error(f"      ❌ Error en single-pass: {e}")
                            edited_fragments.append({
                                'chapter_id': chapter_id,
                                'fragment_id': chapter_id,
                                'contenido_editado': chapter.get('content', ''),
                                'cambios_estructurados': [],
                                'error': str(e)
                            })

            # Calcular promedio de iteraciones
            if reflection_stats_global['total_chapters'] > 0:
                reflection_stats_global['avg_iterations'] = (
                    reflection_stats_global['total_iterations'] / reflection_stats_global['total_chapters']
                )

            logging.info(f"")
            logging.info(f"[REFLECTION] Estadísticas finales:")
            logging.info(f"   Total capítulos: {reflection_stats_global['total_chapters']}")
            logging.info(f"   Con reflection: {reflection_stats_global['chapters_with_reflection']}")
            logging.info(f"   Single-pass: {reflection_stats_global['chapters_single_pass']}")
            logging.info(f"   Iteraciones promedio: {reflection_stats_global['avg_iterations']:.1f}")

        else:
            # FALLBACK: Usar método v5.3 tradicional (batch para todo)
            logging.info(f"[FALLBACK] Reflection loops desactivado, usando método v5.3...")
            edit_reqs = [{'chapter': frag} for frag in fragments]
            edited_fragments = yield from edit_with_claude_batch_v2_optimized(
                context, edit_reqs, bible, consolidated, arc_map_dict, margin_notes_by_chapter, book_metadata
            )

        edited_fragments.sort(key=lambda x: int(x.get('chapter_id', 0) or x.get('fragment_id', 0) or 0))
        t10 = context.current_utc_datetime
        tiempos['edicion'] = str(t10 - t9)
        tiempos['edicion_reflection_stats'] = reflection_stats_global

        # --- FASE 11: RECONSTRUCCIÓN ---
        logging.info(f">>> FASE 11: RECONSTRUCCIÓN")
        context.set_custom_status("Fase 11: Reconstruyendo...")
        recon_input = {'edited_chapters': edited_fragments, 'book_name': book_name, 'bible': bible}
        manuscript = yield context.call_activity('ReconstructManuscript', recon_input)
        if isinstance(manuscript, str): manuscript = json.loads(manuscript)
        t11 = context.current_utc_datetime
        tiempos['reconstruccion'] = str(t11 - t10)

        # --- FASE 12: FIN ---
        logging.info(f">>> FASE 12: GUARDADO FINAL")
        context.set_custom_status("Finalizando...")
        t_final = context.current_utc_datetime
        tiempos['total'] = str(t_final - start_time)
        
        final = {
            'status': 'success',
            'job_id': job_id,
            'book_name': book_name,
            'version': 'LYA 6.0',
            'manuscripts': manuscript.get('manuscripts', {}),
            'consolidated_chapters': manuscript.get('consolidated_chapters', []),
            'statistics': manuscript.get('statistics', {}),
            'bible': bible,
            'carta_editorial': carta_editorial,
            'carta_markdown': carta_markdown,
            'margin_notes': margin_result,
            'tiempos': tiempos,
            'stats': {
                'fragmentos_entrada': len(fragments),
                'capitulos_consolidados': len(consolidated),
                'capitulos_editados': len(edited_fragments),
                'notas_margen': len(margin_result.get('all_notes', []))
            },
            # Nuevos análisis LYA 6.0
            'emotional_arc_analysis': emotional_arc_result,
            'sensory_detection_analysis': sensory_result,
            'reflection_stats': reflection_stats_global
        }
        
        yield context.call_activity('SaveOutputs', final)
        logging.info(f"[SUCCESS] Completado en {tiempos['total']}")
        return final

    except Exception as e:
        logging.error(f"[CRITICAL] Error en orquestador: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        raise e

main = df.Orchestrator.create(orchestrator_function)

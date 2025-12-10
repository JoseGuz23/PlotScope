# =============================================================================
# Orchestrator/__init__.py - SYLPHRENA 5.0
# =============================================================================
# NUEVA VERSIÓN: Flujo completo de developmental editing
#   - Fase 7: Carta Editorial
#   - Fase 8: Notas de Margen
#   - Fase 9: Edición con criterios expandidos
# =============================================================================

import azure.functions as func
import azure.durable_functions as df
import logging
import json
from datetime import timedelta

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

LIMIT_TO_FIRST_N_CHAPTERS = None  # None = procesar todos
GEMINI_POLL_INTERVAL = 60   
CLAUDE_POLL_INTERVAL = 120
MAX_WAIT_MINUTES = 60

# =============================================================================
# HELPERS
# =============================================================================

def run_gemini_pro_batch(context, analysis_type: str, items: list, bible: dict = None):
    """Helper para batches de Gemini Pro."""
    logging.info(f"")
    logging.info(f"{'='*60}")
    logging.info(f">>> INICIANDO BATCH GEMINI PRO: {analysis_type.upper()}")
    logging.info(f"    Items a procesar: {len(items)}")
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
        next_check = context.current_utc_datetime + timedelta(seconds=GEMINI_POLL_INTERVAL)
        yield context.create_timer(next_check)
        
        try:
            result = yield context.call_activity('PollGeminiProBatchResult', batch_info)
        except Exception as e:
            logging.error(f"[ERROR] en PollGeminiProBatchResult [{analysis_type}] intento {attempt+1}: {str(e)}")
            continue
        
        status = result.get('status', 'unknown')
        
        if status == 'success':
            logging.info(f"[OK] BATCH {analysis_type.upper()} COMPLETADO")
            return result.get('results', [])
        
        elif status == 'failed':
            raise Exception(f"Batch {analysis_type} falló: {result.get('error')}")
        
        elif status == 'processing':
            batch_info = result
            state = result.get('state', 'unknown')
            logging.info(f"[WAIT] [{analysis_type}] Poll {attempt+1}/{MAX_WAIT_MINUTES} - Estado: {state}")
            context.set_custom_status(f"Batch {analysis_type}: {state} ({attempt+1}/{MAX_WAIT_MINUTES})")
        
        else:
            batch_info = result

    raise Exception(f"Timeout en Batch {analysis_type}")


def analyze_with_batch_api_v2(context, fragments):
    """Análisis Capa 1 (Factual) con Gemini Flash Batch."""
    logging.info(f">>> INICIANDO ANÁLISIS CAPA 1 (FACTUAL)")
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
        next_check = context.current_utc_datetime + timedelta(seconds=GEMINI_POLL_INTERVAL)
        yield context.create_timer(next_check)
        
        try:
            result = yield context.call_activity('PollBatchResult', batch_info)
        except Exception as e:
            logging.error(f"[ERROR] en PollBatchResult intento {attempt+1}: {str(e)}")
            continue
        
        if isinstance(result, list):
            batch_results = result
            logging.info(f"[OK] BATCH CAPA 1 COMPLETADO - {len(batch_results)} análisis")
            break
        
        status = result.get('status', 'unknown')
        if status in ['failed', 'error']:
            break
        
        batch_info = result
        context.set_custom_status(f"Batch C1: {result.get('state', 'processing')} ({attempt+1}/{MAX_WAIT_MINUTES})")
    
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


def run_margin_notes_batch(context, chapters: list, carta_editorial: dict, bible: dict, book_metadata: dict):
    """
    NUEVO 5.0: Genera notas de margen con Claude Batch.
    """
    logging.info(f"")
    logging.info(f"{'='*60}")
    logging.info(f">>> FASE 8: NOTAS DE MARGEN")
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
        next_check = context.current_utc_datetime + timedelta(seconds=CLAUDE_POLL_INTERVAL)
        yield context.create_timer(next_check)
        
        try:
            result = yield context.call_activity('PollMarginNotesBatch', batch_info)
        except Exception as e:
            logging.error(f"[ERROR] en PollMarginNotesBatch intento {attempt+1}: {str(e)}")
            continue
        
        status = result.get('status', 'unknown')
        
        if status == 'success':
            logging.info(f"[OK] NOTAS DE MARGEN COMPLETADAS")
            logging.info(f"    Total notas: {len(result.get('all_notes', []))}")
            return result
        
        elif status == 'failed':
            raise Exception(f"Batch notas falló: {result.get('error')}")
        
        elif status == 'processing':
            batch_info = result
            logging.info(f"[WAIT] [Notas] Poll {attempt+1}/{MAX_WAIT_MINUTES}")
            context.set_custom_status(f"Generando notas de margen ({attempt+1}/{MAX_WAIT_MINUTES})")
        
        else:
            batch_info = result

    raise Exception("Timeout en Batch de notas de margen")


def edit_with_claude_batch_v2(context, edit_requests: list, bible: dict, analyses: list, arc_maps: dict, margin_notes: dict = None, book_metadata: dict = None):
    """
    ACTUALIZADO 5.0: Edición con notas de margen y criterios expandidos.
    """
    logging.info(f"")
    logging.info(f"{'='*60}")
    logging.info(f">>> FASE 9: EDICIÓN PROFESIONAL")
    logging.info(f"    Capítulos: {len(edit_requests)}")
    logging.info(f"{'='*60}")
    
    chapters = [req.get('chapter', req) for req in edit_requests]
    
    batch_input = {
        'chapters': chapters,
        'bible': bible,
        'analyses': analyses,
        'margin_notes': margin_notes or {},  # NUEVO: notas de margen
        'book_metadata': book_metadata or {}
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
        next_check = context.current_utc_datetime + timedelta(seconds=CLAUDE_POLL_INTERVAL)
        yield context.create_timer(next_check)
        
        try:
            result = yield context.call_activity('PollClaudeBatchResult', batch_info)
        except Exception as e:
            logging.error(f"[ERROR] en PollClaudeBatchResult intento {attempt+1}: {str(e)}")
            continue
        
        status = result.get('status', 'unknown')
        
        if status == 'success':
            total = result.get('total', 0)
            errors = result.get('errors', 0)
            logging.info(f"[OK] EDICIÓN COMPLETADA")
            logging.info(f"    Capítulos: {total}, Errores: {errors}")
            return result.get('results', [])
        
        elif status == 'failed':
            raise Exception(f"Batch edición falló: {result.get('error')}")
        
        elif status == 'processing':
            batch_info = result
            logging.info(f"[WAIT] [Edición] Poll {attempt+1}/{MAX_WAIT_MINUTES}")
            context.set_custom_status(f"Claude editando ({attempt+1}/{MAX_WAIT_MINUTES})")
        
        else:
            batch_info = result

    raise Exception("Timeout en Batch de edición")


# =============================================================================
# ORQUESTADOR PRINCIPAL
# =============================================================================

def orchestrator_function(context: df.DurableOrchestrationContext):
    """
    SYLPHRENA 5.0 - Flujo completo de Developmental Editing.
    """
    
    try:
        start_time = context.current_utc_datetime
        tiempos = {}
        
        logging.info(f"")
        logging.info(f"{'#'*70}")
        logging.info(f"#  SYLPHRENA 5.0 - DEVELOPMENTAL EDITOR AI")
        logging.info(f"#  Job ID: {context.instance_id}")
        logging.info(f"{'#'*70}")
        
        input_data = context.get_input()
        job_id = input_data.get('job_id', context.instance_id)
        blob_path = input_data.get('blob_path', '')
        book_name = input_data.get('book_name', 'Sin título')
        book_metadata = {'title': book_name, 'job_id': job_id, 'blob_path': blob_path}

        # ---------------------------------------------------------------------
        # FASE 1: SEGMENTACIÓN
        # ---------------------------------------------------------------------
        logging.info(f">>> FASE 1: SEGMENTACIÓN")
        context.set_custom_status("Fase 1: Segmentando...")
        
        seg_result = yield context.call_activity('SegmentBook', {'job_id': job_id, 'blob_path': blob_path})
        
        if seg_result.get('error'):
            raise Exception(f"Segmentación: {seg_result.get('error')}")
        
        fragments = seg_result.get('fragments', [])
        
        if LIMIT_TO_FIRST_N_CHAPTERS:
            fragments = fragments[:LIMIT_TO_FIRST_N_CHAPTERS]
        
        logging.info(f"[OK] {len(fragments)} fragmentos generados")
        t1 = context.current_utc_datetime
        tiempos['segmentacion'] = str(t1 - start_time)

        # ---------------------------------------------------------------------
        # FASE 2: ANÁLISIS CAPA 1 (FACTUAL)
        # ---------------------------------------------------------------------
        logging.info(f">>> FASE 2: ANÁLISIS CAPA 1")
        context.set_custom_status("Fase 2: Capa 1...")
        
        layer1_results = yield from analyze_with_batch_api_v2(context, fragments)
        
        t2 = context.current_utc_datetime
        tiempos['capa1'] = str(t2 - t1)

        # ---------------------------------------------------------------------
        # FASE 3: CONSOLIDACIÓN
        # ---------------------------------------------------------------------
        logging.info(f">>> FASE 3: CONSOLIDACIÓN")
        context.set_custom_status("Fase 3: Consolidando...")
        
        consol_input = {'fragments': fragments, 'analyses': layer1_results}
        consolidated = yield context.call_activity('ConsolidateFragmentAnalyses', json.dumps(consol_input))
        
        t3 = context.current_utc_datetime
        tiempos['consolidacion'] = str(t3 - t2)

        # ---------------------------------------------------------------------
        # FASE 4: ANÁLISIS CAPA 2 (ESTRUCTURAL)
        # ---------------------------------------------------------------------
        logging.info(f">>> FASE 4: ANÁLISIS CAPA 2")
        context.set_custom_status("Fase 4: Capa 2...")
        
        layer2_results = yield from run_gemini_pro_batch(context, 'structural', consolidated)
        
        # Fusionar
        for i, ch in enumerate(consolidated):
            ch_id = str(ch.get('chapter_id', i))
            l2 = next((r for r in layer2_results if str(r.get('chapter_id')) == ch_id), {})
            ch['layer2'] = l2
        
        t4 = context.current_utc_datetime
        tiempos['capa2'] = str(t4 - t3)

        # ---------------------------------------------------------------------
        # FASE 5: ANÁLISIS CAPA 3 (CUALITATIVO)
        # ---------------------------------------------------------------------
        logging.info(f">>> FASE 5: ANÁLISIS CAPA 3")
        context.set_custom_status("Fase 5: Capa 3...")
        
        layer3_results = yield from run_gemini_pro_batch(context, 'qualitative', consolidated)
        
        for i, ch in enumerate(consolidated):
            ch_id = str(ch.get('chapter_id', i))
            l3 = next((r for r in layer3_results if str(r.get('chapter_id')) == ch_id), {})
            ch['layer3'] = l3
        
        t5 = context.current_utc_datetime
        tiempos['capa3'] = str(t5 - t4)

        # ---------------------------------------------------------------------
        # FASE 6: BIBLIA NARRATIVA
        # ---------------------------------------------------------------------
        logging.info(f">>> FASE 6: BIBLIA NARRATIVA")
        context.set_custom_status("Fase 6: Biblia...")
        
        full_text = "\n".join([f"CAP {f['title']}: {f['content'][:600]}..." for f in fragments])
        
        holistic = yield context.call_activity('HolisticReading', full_text)
        
        bible_in = {
            "chapter_analyses": consolidated,
            "holistic_analysis": holistic,
            "book_metadata": book_metadata
        }
        
        bible = yield context.call_activity('CreateBible', json.dumps(bible_in))
        
        t6 = context.current_utc_datetime
        tiempos['biblia'] = str(t6 - t5)
        
        # GUARDAR BIBLIA ANTES DE PAUSA
        logging.info(f"[SAVE] Guardando biblia preliminar...")
        
        pre_save_payload = {
            'job_id': context.instance_id,
            'book_name': book_name,
            'bible': bible,
            'consolidated_chapters': consolidated,
            'statistics': {}, 
            'tiempos': tiempos
        }
        
        try:
            yield context.call_activity('SaveOutputs', pre_save_payload)
        except Exception as e:
            logging.error(f"[ERROR] Guardado intermedio: {str(e)}")
        
        # =====================================================================
        # PAUSA PARA APROBACIÓN DE BIBLIA
        # =====================================================================
        logging.info(f"[WAIT] Esperando aprobación humana de la Biblia...")
        context.set_custom_status("Esperando aprobacion de Biblia...")
        
        yield context.wait_for_external_event("BibleApproved")
        
        logging.info(f"[RESUME] Biblia aprobada. Continuando...")

        # =====================================================================
        # FASE 7: CARTA EDITORIAL (NUEVO 5.0)
        # =====================================================================
        logging.info(f"")
        logging.info(f"{'='*60}")
        logging.info(f">>> FASE 7: CARTA EDITORIAL")
        logging.info(f"{'='*60}")
        context.set_custom_status("Fase 7: Carta Editorial...")
        
        carta_input = {
            'bible': bible,
            'consolidated_chapters': consolidated,
            'fragments': fragments,
            'book_metadata': book_metadata
        }
        
        carta_result = yield context.call_activity('GenerateEditorialLetter', carta_input)
        carta_editorial = carta_result.get('carta_editorial', {})
        carta_markdown = carta_result.get('carta_markdown', '')
        
        logging.info(f"[OK] Carta Editorial generada")
        
        t7 = context.current_utc_datetime
        tiempos['carta_editorial'] = str(t7 - t6)

        # =====================================================================
        # FASE 8: NOTAS DE MARGEN (NUEVO 5.0)
        # =====================================================================
        logging.info(f">>> FASE 8: NOTAS DE MARGEN")
        context.set_custom_status("Fase 8: Notas de margen...")
        
        margin_result = yield from run_margin_notes_batch(
            context, fragments, carta_editorial, bible, book_metadata
        )
        
        # Organizar notas por capítulo para la fase de edición
        margin_notes_by_chapter = {}
        for ch_result in margin_result.get('results', []):
            ch_id = str(ch_result.get('chapter_id', ch_result.get('fragment_id', '?')))
            margin_notes_by_chapter[ch_id] = ch_result.get('notas_margen', [])
        
        logging.info(f"[OK] {len(margin_result.get('all_notes', []))} notas generadas")
        
        t8 = context.current_utc_datetime
        tiempos['notas_margen'] = str(t8 - t7)

        # ---------------------------------------------------------------------
        # FASE 9: ARCOS POR CAPÍTULO
        # ---------------------------------------------------------------------
        logging.info(f">>> FASE 9: ARCOS POR CAPÍTULO")
        context.set_custom_status("Fase 9: Arcos...")
        
        arc_results = yield from run_gemini_pro_batch(context, 'arc_maps', consolidated, bible=bible)
        arc_map_dict = {str(r['chapter_id']): r for r in arc_results}
        
        t9 = context.current_utc_datetime
        tiempos['arcos'] = str(t9 - t8)

        # =====================================================================
        # FASE 10: EDICIÓN PROFESIONAL (ACTUALIZADO 5.0)
        # =====================================================================
        logging.info(f">>> FASE 10: EDICIÓN PROFESIONAL")
        context.set_custom_status("Fase 10: Edición...")
        
        edit_reqs = [{'chapter': frag} for frag in fragments]
        
        edited_fragments = yield from edit_with_claude_batch_v2(
            context, 
            edit_reqs, 
            bible, 
            consolidated, 
            arc_map_dict,
            margin_notes=margin_notes_by_chapter,  # NUEVO: pasar notas
            book_metadata=book_metadata
        )
        
        edited_fragments.sort(key=lambda x: int(x.get('chapter_id', 0) or x.get('fragment_id', 0) or 0))
        
        t10 = context.current_utc_datetime
        tiempos['edicion'] = str(t10 - t9)

        # ---------------------------------------------------------------------
        # FASE 11: RECONSTRUCCIÓN
        # ---------------------------------------------------------------------
        logging.info(f">>> FASE 11: RECONSTRUCCIÓN")
        context.set_custom_status("Fase 11: Reconstruyendo...")
        
        recon_input = {
            'edited_chapters': edited_fragments,
            'book_name': book_name,
            'bible': bible
        }
        
        manuscript = yield context.call_activity('ReconstructManuscript', recon_input)
        
        t11 = context.current_utc_datetime
        tiempos['reconstruccion'] = str(t11 - t10)

        # ---------------------------------------------------------------------
        # FASE 12: GUARDAR Y FINALIZAR
        # ---------------------------------------------------------------------
        logging.info(f">>> FASE 12: GUARDADO FINAL")
        context.set_custom_status("Finalizando...")
        
        t_final = context.current_utc_datetime
        tiempos['total'] = str(t_final - start_time)
        
        final = {
            'status': 'success',
            'job_id': context.instance_id,
            'book_name': book_name,
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
            }
        }
        
        try:
            yield context.call_activity('SaveOutputs', final)
        except Exception as e:
            logging.error(f"[ERROR] en SaveOutputs: {str(e)}")
        
        # RESUMEN FINAL
        logging.info(f"")
        logging.info(f"{'#'*70}")
        logging.info(f"#  [SUCCESS] SYLPHRENA 5.0 - COMPLETADO")
        logging.info(f"{'#'*70}")
        logging.info(f"#  Libro: {book_name}")
        logging.info(f"#  Fragmentos: {len(fragments)}")
        logging.info(f"#  Capítulos editados: {len(edited_fragments)}")
        logging.info(f"#  Notas de margen: {len(margin_result.get('all_notes', []))}")
        logging.info(f"#")
        logging.info(f"#  TIEMPOS:")
        for fase, tiempo in tiempos.items():
            logging.info(f"#     {fase}: {tiempo}")
        logging.info(f"{'#'*70}")
        
        return final

    except Exception as e:
        logging.error(f"")
        logging.error(f"{'!'*70}")
        logging.error(f"!  [CRITICAL] ERROR FATAL EN ORQUESTADOR")
        logging.error(f"{'!'*70}")
        logging.error(f"!  Error: {str(e)}")
        
        import traceback
        tb = traceback.format_exc()
        for line in tb.split('\n'):
            if line.strip():
                logging.error(f"!  {line}")
        
        logging.error(f"{'!'*70}")
        raise e

main = df.Orchestrator.create(orchestrator_function)

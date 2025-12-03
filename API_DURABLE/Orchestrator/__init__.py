# =============================================================================
# Orchestrator/__init__.py - SYLPHRENA 4.0 (FINAL CLEAN)
# =============================================================================

import azure.functions as func
import azure.durable_functions as df
import logging
import json
from datetime import timedelta

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

# Límite de capítulos (None = Todo el libro, Entero = Primeros N)
LIMIT_TO_FIRST_N_CHAPTERS = 2   

# Tiempos de espera para Polling (Segundos)
# Usamos Timers de Durable Functions, así que esto no gasta cómputo
GEMINI_POLL_INTERVAL = 60   
CLAUDE_POLL_INTERVAL = 120
MAX_WAIT_MINUTES = 60

# =============================================================================
# HELPERS (Gestión de Batch y Fallbacks)
# =============================================================================

def run_gemini_pro_batch(context, analysis_type: str, items: list, bible: dict = None):
    """
    Helper genérico para ejecutar batches de Gemini Pro (Capas 2, 3, Arcos).
    Ciclo: Submit -> Timer -> Poll -> Success/Fail
    """
    batch_input = {
        'analysis_type': analysis_type,
        'items': items,
        'bible': bible or {}
    }
    
    # 1. Submit
    batch_info = yield context.call_activity('SubmitGeminiProBatch', batch_input)
    
    if batch_info.get('status') == 'error':
        raise Exception(f"❌ Error submit batch {analysis_type}: {batch_info.get('error')}")
    
    job_name = batch_info.get('batch_job_name')
    logging.info(f"📦 Batch {analysis_type} iniciado: {job_name}")
    
    # 2. Wait Loop
    for attempt in range(MAX_WAIT_MINUTES):
        # Dormir (Timer)
        next_check = context.current_utc_datetime + timedelta(seconds=GEMINI_POLL_INTERVAL)
        yield context.create_timer(next_check)
        
        # Poll
        result = yield context.call_activity('PollGeminiProBatchResult', batch_info)
        status = result.get('status')
        
        if status == 'success':
            logging.info(f"✅ Batch {analysis_type} completado ({result.get('total')} items).")
            return result.get('results', [])
        
        elif status == 'failed':
            raise Exception(f"❌ Batch {analysis_type} falló: {result.get('error')}")
            
        # Si es 'processing', el bucle continúa y vuelve a dormir
        context.set_custom_status(f"⏳ Batch {analysis_type}: Procesando... ({attempt+1}/{MAX_WAIT_MINUTES})")

    raise Exception(f"⏱️ Timeout en Batch {analysis_type}")


def analyze_with_batch_api_v2(context, fragments):
    """
    Maneja el Análisis de Capa 1 (Factual).
    Estrategia: Batch Principal -> Retry Individual (Gemini) -> Fallback (Claude)
    """
    # 1. Submit Batch Inicial
    context.set_custom_status("📤 Enviando Batch Capa 1...")
    batch_info = yield context.call_activity('SubmitBatchAnalysis', fragments)
    
    if batch_info.get('error'):
        raise Exception(f"Error submit Batch C1: {batch_info.get('error')}")
    
    # 2. Wait Loop Batch
    batch_results = []
    batch_failed = False
    
    for attempt in range(MAX_WAIT_MINUTES):
        next_check = context.current_utc_datetime + timedelta(seconds=GEMINI_POLL_INTERVAL)
        yield context.create_timer(next_check)
        
        result = yield context.call_activity('PollBatchResult', batch_info)
        
        if isinstance(result, list): # Éxito, devuelve lista
            batch_results = result
            break
        
        if result.get('status') == 'failed':
            logging.warning("⚠️ Batch C1 falló completamente. Pasando a Fallback.")
            batch_failed = True
            break
            
        context.set_custom_status(f"⏳ Batch C1: Procesando... ({attempt+1}/{MAX_WAIT_MINUTES})")
    
    # 3. Identificar fallos (items que faltan en el resultado)
    successful_ids = set()
    for res in batch_results:
        # Intentar varios campos de ID posibles
        fid = res.get('fragment_id') or res.get('chapter_id') or res.get('id')
        if fid: successful_ids.add(str(fid))
        
    failed_fragments = [f for f in fragments if str(f.get('id')) not in successful_ids]
    
    if not failed_fragments:
        return batch_results

    # 4. Lógica de Rescate (Retry + Fallback)
    # Limitamos rescates para no eternizar
    MAX_RETRIES = 10
    if len(failed_fragments) > MAX_RETRIES:
        logging.warning(f"⚠️ Muchos fallos ({len(failed_fragments)}). Rescatando solo primeros {MAX_RETRIES}.")
        failed_fragments = failed_fragments[:MAX_RETRIES]

    final_results = list(batch_results)
    
    for i, frag in enumerate(failed_fragments):
        frag_id = frag.get('id')
        context.set_custom_status(f"🚑 Rescatando frag {frag_id} ({i+1}/{len(failed_fragments)})")
        
        # A) Reintento con Gemini Standard (Activity)
        try:
            retry_res = yield context.call_activity('AnalyzeChapter', frag)
            if retry_res and not retry_res.get('error'):
                logging.info(f"✅ Retry Gemini OK: Frag {frag_id}")
                final_results.append(retry_res)
                continue # Éxito, siguiente
        except:
            pass # Falló Gemini, seguimos a Claude

        # B) Fallback a Claude (Activity)
        try:
            logging.info(f"🔀 Fallback Claude: Frag {frag_id}")
            claude_res = yield context.call_activity('AnalyzeChapterWithClaude', frag)
            if claude_res and not claude_res.get('error'):
                logging.info(f"✅ Fallback Claude OK: Frag {frag_id}")
                final_results.append(claude_res)
            else:
                logging.error(f"❌ Fallback Claude falló: Frag {frag_id}")
        except Exception as e:
             logging.error(f"❌ Error fatal en fallback: {e}")

    return final_results


def edit_with_claude_batch_v2(context, edit_requests, bible, analyses, arc_maps):
    """
    Maneja la Edición usando Claude Batch.
    Ciclo: Submit -> Timer -> Poll
    """
    # Preparar input simple
    chapters_only = [req['chapter'] for req in edit_requests]
    
    batch_request = {
        'chapters': chapters_only,
        'bible': bible,
        'analyses': analyses,
        'arc_maps': arc_maps
    }
    
    # 1. Submit
    batch_info = yield context.call_activity('SubmitClaudeBatch', batch_request)
    if batch_info.get('error'):
        raise Exception(f"Error submit Claude Batch: {batch_info.get('error')}")
    
    logging.info(f"📦 Claude Batch iniciado: {batch_info.get('batch_id')}")

    # 2. Wait Loop
    for attempt in range(120): # Claude tarda más, damos 2 horas max
        next_check = context.current_utc_datetime + timedelta(seconds=CLAUDE_POLL_INTERVAL)
        yield context.create_timer(next_check)
        
        result = yield context.call_activity('PollClaudeBatchResult', batch_info)
        
        if isinstance(result, list):
            logging.info(f"✅ Claude Batch completado ({len(result)} editados).")
            return result
            
        if result.get('status') == 'error':
            raise Exception(f"Claude Batch falló: {result.get('error')}")
            
        context.set_custom_status(f"⏳ Claude Batch: Procesando... ({attempt+1}/120)")
        # Actualizar info para siguiente poll (ej. contadores)
        batch_info = result 

    raise Exception("⏱️ Timeout en Claude Batch")


# =============================================================================
# ORQUESTADOR PRINCIPAL
# =============================================================================

def orchestrator_function(context: df.DurableOrchestrationContext):
    try:
        # --- SETUP ---
        input_data = context.get_input()
        book_path = input_data if isinstance(input_data, str) else input_data.get('book_path', '')
        book_name = book_path.split('/')[-1].split('.')[0] if book_path else "libro"
        start_time = context.current_utc_datetime
        tiempos = {}

        logging.info(f"🎬 ORQUESTADOR V4 INICIADO: {book_name}")

        # ---------------------------------------------------------------------
        # FASE 1: SEGMENTACIÓN
        # ---------------------------------------------------------------------
        context.set_custom_status("📚 Fase 1: Segmentando...")
        
        segment_payload = {
            'book_path': book_path,
            'limit_chapters': LIMIT_TO_FIRST_N_CHAPTERS  
        }
        
        # Llamada y parseo
        segment_json = yield context.call_activity('SegmentBook', segment_payload)
        segment_res = json.loads(segment_json)
        
        fragments = segment_res.get('fragments', [])
        book_metadata = segment_res.get('book_metadata', {})
        chapter_map = segment_res.get('chapter_map', {})
        
        t1 = context.current_utc_datetime
        tiempos['segmentacion'] = str(t1 - start_time)
        
        if not fragments:
            return {"status": "completed", "message": "Libro vacío."}

        # ---------------------------------------------------------------------
        # FASE 2: ANÁLISIS CAPA 1 (FACTUAL + FALLBACKS)
        # ---------------------------------------------------------------------
        context.set_custom_status("🔍 Fase 2: Análisis Capa 1...")
        
        # Usamos la versión V2 con timers y fallback
        fragment_analyses = yield from analyze_with_batch_api_v2(context, fragments)
        
        # Ordenar resultados
        fragment_analyses.sort(key=lambda x: int(x.get('id', 0) or 0))

        t2 = context.current_utc_datetime
        tiempos['capa1'] = str(t2 - t1)

        # ---------------------------------------------------------------------
        # FASE 3: CONSOLIDACIÓN
        # ---------------------------------------------------------------------
        context.set_custom_status("🔧 Fase 3: Consolidando...")
        
        consolidated = yield context.call_activity(
            'ConsolidateFragmentAnalyses',
            {'fragment_analyses': fragment_analyses, 'chapter_map': chapter_map}
        )
        
        t3 = context.current_utc_datetime
        tiempos['consolidacion'] = str(t3 - t2)

        # ---------------------------------------------------------------------
        # FASE 4: ANÁLISIS CAPA 2 (ESTRUCTURAL - BATCH)
        # ---------------------------------------------------------------------
        context.set_custom_status("📊 Fase 4: Estructura (Batch)...")

        layer2_results = yield from run_gemini_pro_batch(
            context, 'layer2_structural', consolidated
        )
        
        # Merge
        l2_map = {r['chapter_id']: r for r in layer2_results}
        for c in consolidated:
            c['layer2_structural'] = l2_map.get(c['chapter_id'], {})

        t4 = context.current_utc_datetime
        tiempos['capa2'] = str(t4 - t3)

        # ---------------------------------------------------------------------
        # FASE 5: ANÁLISIS CAPA 3 (CUALITATIVO - BATCH)
        # ---------------------------------------------------------------------
        context.set_custom_status("🧠 Fase 5: Cualitativo (Batch)...")
        
        # Añadir contexto de posición
        total_chaps = len(consolidated)
        for i, c in enumerate(consolidated):
            c['chapter_position'] = i + 1
            c['total_chapters'] = total_chaps

        layer3_results = yield from run_gemini_pro_batch(
            context, 'layer3_qualitative', consolidated
        )
        
        # Merge
        l3_map = {r['chapter_id']: r for r in layer3_results}
        for c in consolidated:
            c['layer3_qualitative'] = l3_map.get(c['chapter_id'], {})

        t5 = context.current_utc_datetime
        tiempos['capa3'] = str(t5 - t4)

        # ---------------------------------------------------------------------
        # FASE 6: BIBLIA & HOLÍSTICO
        # ---------------------------------------------------------------------
        context.set_custom_status("📜 Fase 6: Biblia...")
        
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

        # ---------------------------------------------------------------------
        # FASE 10: ARCOS (BATCH) - (Saltamos 8 y 9 para simplificar hoy)
        # ---------------------------------------------------------------------
        context.set_custom_status("🗺️ Fase 10: Arcos...")
        
        arc_results = yield from run_gemini_pro_batch(
            context, 'arc_maps', consolidated, bible=bible
        )
        arc_map_dict = {str(r['chapter_id']): r for r in arc_results}
        
        t10 = context.current_utc_datetime
        tiempos['arcos'] = str(t10 - t6)

        # ---------------------------------------------------------------------
        # FASE 11: EDICIÓN (CLAUDE BATCH)
        # ---------------------------------------------------------------------
        context.set_custom_status("✏️ Fase 11: Edición...")
        
        # Preparar requests
        edit_reqs = []
        for frag in fragments:
            pid = str(frag.get('parent_chapter_id'))
            # Buscar análisis del capítulo padre
            analysis = next((c for c in consolidated if str(c['chapter_id']) == pid), {})
            
            edit_reqs.append({
                'chapter': frag,
                # Los helpers ya no se pasan aquí, se pasan en bloque a la func batch
            })
            
        # Ejecutar Edición Batch V2
        edited_fragments = yield from edit_with_claude_batch_v2(
            context, edit_reqs, bible, consolidated, arc_map_dict
        )
        
        # Ordenar
        edited_fragments.sort(key=lambda x: int(x.get('id', 0)))
        
        t11 = context.current_utc_datetime
        tiempos['edicion'] = str(t11 - t10)

        # ---------------------------------------------------------------------
        # FASE 12/13: RECONSTRUCCIÓN Y FINAL
        # ---------------------------------------------------------------------
        context.set_custom_status("💾 Finalizando...")
        
        recon_input = {
            'edited_chapters': edited_fragments,
            'book_name': book_name,
            'bible': bible
        }
        manuscript = yield context.call_activity('ReconstructManuscript', recon_input)
        
        final = {
            'job_id': context.instance_id,
            'book_name': book_name,
            'manuscript': manuscript,
            'tiempos': tiempos
        }
        
        yield context.call_activity('SaveOutputs', final)
        
        logging.info("✅✅ FINALIZADO CON ÉXITO ✅✅")
        return final

    except Exception as e:
        logging.error(f"💥 ERROR FATAL: {e}")
        raise e

main = df.Orchestrator.create(orchestrator_function)
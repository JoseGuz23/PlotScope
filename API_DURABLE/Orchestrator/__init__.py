# =============================================================================
# Orchestrator/__init__.py - SYLPHRENA 4.0.2 (LOGGING MEJORADO)
# =============================================================================
# CAMBIOS v4.0.2:
#   - Logging detallado en cada fase con métricas
#   - Corrección bug Claude Batch (dict vs list)
#   - Actualización de batch_info en loops
#   - Logging de errores con contexto completo
#   - Resumen final con estadísticas
# =============================================================================

import azure.functions as func
import azure.durable_functions as df
import logging
import json
from datetime import timedelta

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

LIMIT_TO_FIRST_N_CHAPTERS = 2   
GEMINI_POLL_INTERVAL = 60   
CLAUDE_POLL_INTERVAL = 120
MAX_WAIT_MINUTES = 60

# =============================================================================
# HELPERS
# =============================================================================

def run_gemini_pro_batch(context, analysis_type: str, items: list, bible: dict = None):
    """
    Helper para batches de Gemini Pro (Capas 2, 3, Arcos).
    """
    logging.info(f"")
    logging.info(f"{'='*60}")
    logging.info(f"🚀 INICIANDO BATCH GEMINI PRO: {analysis_type.upper()}")
    logging.info(f"   Items a procesar: {len(items)}")
    logging.info(f"{'='*60}")
    
    batch_input = {
        'analysis_type': analysis_type,
        'items': items,
        'bible': bible or {}
    }
    
    # 1. Submit
    try:
        batch_info = yield context.call_activity('SubmitGeminiProBatch', batch_input)
    except Exception as e:
        logging.error(f"❌ ERROR en SubmitGeminiProBatch [{analysis_type}]: {str(e)}")
        raise
    
    if batch_info.get('status') == 'error':
        logging.error(f"❌ Submit falló [{analysis_type}]: {batch_info.get('error')}")
        raise Exception(f"Error submit batch {analysis_type}: {batch_info.get('error')}")
    
    job_name = batch_info.get('batch_job_name', 'unknown')
    logging.info(f"📦 Batch {analysis_type} creado: {job_name}")
    logging.info(f"   Requests enviados: {batch_info.get('total_requests', '?')}")
    
    # 2. Wait Loop
    for attempt in range(MAX_WAIT_MINUTES):
        next_check = context.current_utc_datetime + timedelta(seconds=GEMINI_POLL_INTERVAL)
        yield context.create_timer(next_check)
        
        try:
            result = yield context.call_activity('PollGeminiProBatchResult', batch_info)
        except Exception as e:
            logging.error(f"❌ ERROR en PollGeminiProBatchResult [{analysis_type}] intento {attempt+1}: {str(e)}")
            # Continuar intentando
            continue
        
        status = result.get('status', 'unknown')
        
        if status == 'success':
            total = result.get('total', 0)
            errors = result.get('errors', 0)
            logging.info(f"")
            logging.info(f"✅ BATCH {analysis_type.upper()} COMPLETADO")
            logging.info(f"   Resultados: {total} exitosos, {errors} errores")
            logging.info(f"   Intentos de polling: {attempt + 1}")
            return result.get('results', [])
        
        elif status == 'failed':
            logging.error(f"❌ BATCH {analysis_type} FALLÓ: {result.get('error')}")
            raise Exception(f"Batch {analysis_type} falló: {result.get('error')}")
        
        elif status == 'processing':
            # Actualizar batch_info para siguiente iteración
            batch_info = result
            state = result.get('state', 'unknown')
            logging.info(f"⏳ [{analysis_type}] Poll {attempt+1}/{MAX_WAIT_MINUTES} - Estado: {state}")
            context.set_custom_status(f"⏳ Batch {analysis_type}: {state} ({attempt+1}/{MAX_WAIT_MINUTES})")
        
        else:
            logging.warning(f"⚠️ [{analysis_type}] Estado inesperado: {status}")
            batch_info = result

    logging.error(f"⏱️ TIMEOUT en Batch {analysis_type} después de {MAX_WAIT_MINUTES} intentos")
    raise Exception(f"Timeout en Batch {analysis_type}")


def analyze_with_batch_api_v2(context, fragments):
    """
    Análisis Capa 1 (Factual) con Gemini Flash Batch.
    """
    logging.info(f"")
    logging.info(f"{'='*60}")
    logging.info(f"🔍 INICIANDO ANÁLISIS CAPA 1 (FACTUAL)")
    logging.info(f"   Fragmentos a analizar: {len(fragments)}")
    logging.info(f"{'='*60}")
    
    # 1. Submit
    context.set_custom_status("📤 Enviando Batch Capa 1...")
    
    try:
        batch_info = yield context.call_activity('SubmitBatchAnalysis', fragments)
    except Exception as e:
        logging.error(f"❌ ERROR en SubmitBatchAnalysis: {str(e)}")
        raise
    
    if batch_info.get('error'):
        logging.error(f"❌ Submit Capa 1 falló: {batch_info.get('error')}")
        raise Exception(f"Error submit Batch C1: {batch_info.get('error')}")
    
    job_name = batch_info.get('batch_job_name', 'unknown')
    logging.info(f"📦 Batch Capa 1 creado: {job_name}")
    logging.info(f"   Fragmentos: {batch_info.get('chapters_count', '?')}")
    
    # 2. Wait Loop
    batch_results = []
    
    for attempt in range(MAX_WAIT_MINUTES):
        next_check = context.current_utc_datetime + timedelta(seconds=GEMINI_POLL_INTERVAL)
        yield context.create_timer(next_check)
        
        try:
            result = yield context.call_activity('PollBatchResult', batch_info)
        except Exception as e:
            logging.error(f"❌ ERROR en PollBatchResult intento {attempt+1}: {str(e)}")
            continue
        
        # PollBatchResult devuelve lista directamente cuando tiene éxito
        if isinstance(result, list):
            batch_results = result
            logging.info(f"")
            logging.info(f"✅ BATCH CAPA 1 COMPLETADO")
            logging.info(f"   Análisis obtenidos: {len(batch_results)}")
            logging.info(f"   Intentos de polling: {attempt + 1}")
            break
        
        status = result.get('status', 'unknown')
        
        if status == 'failed':
            logging.error(f"❌ Batch Capa 1 FALLÓ: {result.get('error')}")
            break
        
        if status == 'error':
            logging.error(f"❌ Error en Batch Capa 1: {result.get('error')}")
            break
        
        # Actualizar batch_info y continuar
        batch_info = result
        state = result.get('state', 'processing')
        logging.info(f"⏳ [Capa1] Poll {attempt+1}/{MAX_WAIT_MINUTES} - Estado: {state}")
        context.set_custom_status(f"⏳ Batch C1: {state} ({attempt+1}/{MAX_WAIT_MINUTES})")
    
    # 3. Identificar fragmentos faltantes
    successful_ids = set()
    for res in batch_results:
        fid = res.get('fragment_id') or res.get('chapter_id') or res.get('id')
        if fid: 
            successful_ids.add(str(fid))
    
    failed_fragments = [f for f in fragments if str(f.get('id')) not in successful_ids]
    
    logging.info(f"")
    logging.info(f"📊 RESUMEN CAPA 1:")
    logging.info(f"   Exitosos: {len(batch_results)}/{len(fragments)}")
    logging.info(f"   Fallidos: {len(failed_fragments)}")
    
    if not failed_fragments:
        return batch_results

    # 4. Rescate de fragmentos fallidos
    logging.info(f"")
    logging.info(f"🚑 INICIANDO RESCATE DE {len(failed_fragments)} FRAGMENTOS")
    
    MAX_RETRIES = 10
    if len(failed_fragments) > MAX_RETRIES:
        logging.warning(f"⚠️ Limitando rescate a {MAX_RETRIES} de {len(failed_fragments)} fragmentos")
        failed_fragments = failed_fragments[:MAX_RETRIES]

    final_results = list(batch_results)
    rescued = 0
    failed_rescue = 0
    
    for i, frag in enumerate(failed_fragments):
        frag_id = frag.get('id', '?')
        logging.info(f"🚑 Rescatando fragmento {frag_id} ({i+1}/{len(failed_fragments)})")
        context.set_custom_status(f"🚑 Rescatando {frag_id} ({i+1}/{len(failed_fragments)})")
        
        # A) Reintento Gemini
        try:
            retry_res = yield context.call_activity('AnalyzeChapter', frag)
            if retry_res and not retry_res.get('error'):
                logging.info(f"   ✅ Gemini retry exitoso para {frag_id}")
                final_results.append(retry_res)
                rescued += 1
                continue
            else:
                logging.warning(f"   ⚠️ Gemini retry falló para {frag_id}: {retry_res.get('error', 'unknown')}")
        except Exception as e:
            logging.warning(f"   ⚠️ Gemini retry excepción para {frag_id}: {str(e)}")

        # B) Fallback Claude
        try:
            logging.info(f"   🔀 Intentando fallback Claude para {frag_id}")
            claude_res = yield context.call_activity('AnalyzeChapterWithClaude', frag)
            if claude_res and not claude_res.get('error'):
                logging.info(f"   ✅ Claude fallback exitoso para {frag_id}")
                final_results.append(claude_res)
                rescued += 1
            else:
                logging.error(f"   ❌ Claude fallback falló para {frag_id}")
                failed_rescue += 1
        except Exception as e:
            logging.error(f"   ❌ Claude fallback excepción para {frag_id}: {str(e)}")
            failed_rescue += 1

    logging.info(f"")
    logging.info(f"📊 RESUMEN RESCATE:")
    logging.info(f"   Rescatados: {rescued}")
    logging.info(f"   No rescatados: {failed_rescue}")
    logging.info(f"   Total final: {len(final_results)}/{len(fragments)}")
    
    return final_results


def edit_with_claude_batch_v2(context, edit_requests, bible, analyses, arc_maps):
    """
    Edición con Claude Batch API.
    FIX: Manejo correcto de respuesta (dict con 'results', no lista)
    """
    logging.info(f"")
    logging.info(f"{'='*60}")
    logging.info(f"✏️ INICIANDO EDICIÓN CON CLAUDE BATCH")
    logging.info(f"   Capítulos a editar: {len(edit_requests)}")
    logging.info(f"{'='*60}")
    
    chapters_only = [req['chapter'] for req in edit_requests]
    
    batch_request = {
        'chapters': chapters_only,
        'bible': bible,
        'analyses': analyses,
        'arc_maps': arc_maps
    }
    
    # 1. Submit
    context.set_custom_status("📤 Enviando Batch Claude...")
    
    try:
        batch_info = yield context.call_activity('SubmitClaudeBatch', batch_request)
    except Exception as e:
        logging.error(f"❌ ERROR en SubmitClaudeBatch: {str(e)}")
        raise
    
    if batch_info.get('error'):
        logging.error(f"❌ Submit Claude falló: {batch_info.get('error')}")
        raise Exception(f"Error submit Claude Batch: {batch_info.get('error')}")
    
    batch_id = batch_info.get('batch_id', 'unknown')
    logging.info(f"📦 Claude Batch creado: {batch_id}")
    logging.info(f"   Capítulos: {batch_info.get('chapters_count', '?')}")
    
    metrics = batch_info.get('metrics', {})
    if metrics:
        logging.info(f"   Tokens estimados: {metrics.get('estimated_input_tokens', '?'):,}")
        logging.info(f"   Costo estimado: ${metrics.get('estimated_input_cost_usd', 0):.4f}")

    # 2. Wait Loop
    for attempt in range(120):  # 2 horas max
        next_check = context.current_utc_datetime + timedelta(seconds=CLAUDE_POLL_INTERVAL)
        yield context.create_timer(next_check)
        
        try:
            result = yield context.call_activity('PollClaudeBatchResult', batch_info)
        except Exception as e:
            logging.error(f"❌ ERROR en PollClaudeBatchResult intento {attempt+1}: {str(e)}")
            continue
        
        status = result.get('status', 'unknown')
        
        # ─────────────────────────────────────────────────────────────
        # FIX: PollClaudeBatchResult devuelve dict con 'results'
        # ─────────────────────────────────────────────────────────────
        if status == 'success':
            results_list = result.get('results', [])
            total = result.get('total_processed', len(results_list))
            parse_failures = result.get('parse_failures', 0)
            
            logging.info(f"")
            logging.info(f"✅ CLAUDE BATCH COMPLETADO")
            logging.info(f"   Editados: {total}")
            logging.info(f"   Fallos de parsing: {parse_failures}")
            logging.info(f"   Intentos de polling: {attempt + 1}")
            
            if parse_failures > 0:
                logging.warning(f"⚠️ {parse_failures} capítulos usaron contenido original como fallback")
            
            return results_list
        
        elif status == 'error' or status == 'failed':
            logging.error(f"❌ CLAUDE BATCH FALLÓ: {result.get('error')}")
            raise Exception(f"Claude Batch falló: {result.get('error')}")
        
        elif status == 'processing':
            # Actualizar batch_info para preservar fragment_metadata_map
            batch_info = result
            
            # Mostrar progreso
            counts = result.get('request_counts', {})
            succeeded = counts.get('succeeded', 0)
            processing = counts.get('processing', 0)
            
            logging.info(f"⏳ [Claude] Poll {attempt+1}/120 - Completados: {succeeded}, Procesando: {processing}")
            context.set_custom_status(f"⏳ Claude: {succeeded} listos, {processing} procesando ({attempt+1}/120)")
        
        else:
            logging.warning(f"⚠️ [Claude] Estado inesperado: {status}")
            batch_info = result

    logging.error(f"⏱️ TIMEOUT en Claude Batch después de 120 intentos (2 horas)")
    raise Exception("Timeout en Claude Batch (2 horas)")


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
        
        logging.info(f"")
        logging.info(f"{'#'*70}")
        logging.info(f"#  🎬 SYLPHRENA 4.0.2 - ORQUESTADOR INICIADO")
        logging.info(f"#  📚 Libro: {book_name}")
        logging.info(f"#  ⏰ Inicio: {start_time.isoformat()}")
        logging.info(f"#  🔢 Límite capítulos: {LIMIT_TO_FIRST_N_CHAPTERS or 'Sin límite'}")
        logging.info(f"{'#'*70}")

        # ---------------------------------------------------------------------
        # FASE 1: SEGMENTACIÓN
        # ---------------------------------------------------------------------
        logging.info(f"")
        logging.info(f"{'='*60}")
        logging.info(f"📚 FASE 1: SEGMENTACIÓN")
        logging.info(f"{'='*60}")
        context.set_custom_status("📚 Fase 1: Segmentando...")
        
        segment_payload = {
            'book_path': book_path,
            'limit_chapters': LIMIT_TO_FIRST_N_CHAPTERS  
        }
        
        try:
            segment_json = yield context.call_activity('SegmentBook', segment_payload)
            segment_res = json.loads(segment_json)
        except Exception as e:
            logging.error(f"❌ ERROR en SegmentBook: {str(e)}")
            raise
        
        fragments = segment_res.get('fragments', [])
        book_metadata = segment_res.get('book_metadata', {})
        chapter_map = segment_res.get('chapter_map', {})
        
        t1 = context.current_utc_datetime
        tiempos['segmentacion'] = str(t1 - start_time)
        
        logging.info(f"✅ Segmentación completada en {tiempos['segmentacion']}")
        logging.info(f"   Fragmentos: {len(fragments)}")
        logging.info(f"   Capítulos únicos: {len(chapter_map)}")
        logging.info(f"   Metadata: {book_metadata.get('title', 'N/A')}")
        
        if not fragments:
            logging.warning(f"⚠️ No se encontraron fragmentos. Terminando.")
            return {"status": "completed", "message": "Libro vacío."}

        # ---------------------------------------------------------------------
        # FASE 2: ANÁLISIS CAPA 1
        # ---------------------------------------------------------------------
        context.set_custom_status("🔍 Fase 2: Análisis Capa 1...")
        
        fragment_analyses = yield from analyze_with_batch_api_v2(context, fragments)
        fragment_analyses.sort(key=lambda x: int(x.get('id', 0) or 0))

        t2 = context.current_utc_datetime
        tiempos['capa1'] = str(t2 - t1)
        logging.info(f"⏱️ Tiempo Capa 1: {tiempos['capa1']}")

        # ---------------------------------------------------------------------
        # FASE 3: CONSOLIDACIÓN
        # ---------------------------------------------------------------------
        logging.info(f"")
        logging.info(f"{'='*60}")
        logging.info(f"🔧 FASE 3: CONSOLIDACIÓN")
        logging.info(f"{'='*60}")
        context.set_custom_status("🔧 Fase 3: Consolidando...")
        
        try:
            consolidated = yield context.call_activity(
                'ConsolidateFragmentAnalyses',
                {'fragment_analyses': fragment_analyses, 'chapter_map': chapter_map}
            )
        except Exception as e:
            logging.error(f"❌ ERROR en ConsolidateFragmentAnalyses: {str(e)}")
            raise
        
        t3 = context.current_utc_datetime
        tiempos['consolidacion'] = str(t3 - t2)
        
        logging.info(f"✅ Consolidación completada en {tiempos['consolidacion']}")
        logging.info(f"   Capítulos consolidados: {len(consolidated)}")

        # ---------------------------------------------------------------------
        # FASE 4: CAPA 2 (ESTRUCTURAL)
        # ---------------------------------------------------------------------
        context.set_custom_status("📊 Fase 4: Estructura...")

        layer2_results = yield from run_gemini_pro_batch(
            context, 'layer2_structural', consolidated
        )
        
        l2_map = {r['chapter_id']: r for r in layer2_results}
        for c in consolidated:
            c['layer2_structural'] = l2_map.get(c['chapter_id'], {})

        t4 = context.current_utc_datetime
        tiempos['capa2'] = str(t4 - t3)
        logging.info(f"⏱️ Tiempo Capa 2: {tiempos['capa2']}")

        # ---------------------------------------------------------------------
        # FASE 5: CAPA 3 (CUALITATIVO)
        # ---------------------------------------------------------------------
        context.set_custom_status("🧠 Fase 5: Cualitativo...")
        
        total_chaps = len(consolidated)
        for i, c in enumerate(consolidated):
            c['chapter_position'] = i + 1
            c['total_chapters'] = total_chaps

        layer3_results = yield from run_gemini_pro_batch(
            context, 'layer3_qualitative', consolidated
        )
        
        l3_map = {r['chapter_id']: r for r in layer3_results}
        for c in consolidated:
            c['layer3_qualitative'] = l3_map.get(c['chapter_id'], {})

        t5 = context.current_utc_datetime
        tiempos['capa3'] = str(t5 - t4)
        logging.info(f"⏱️ Tiempo Capa 3: {tiempos['capa3']}")

        # ---------------------------------------------------------------------
        # FASE 6: BIBLIA & HOLÍSTICO
        # ---------------------------------------------------------------------
        logging.info(f"")
        logging.info(f"{'='*60}")
        logging.info(f"📜 FASE 6: BIBLIA NARRATIVA")
        logging.info(f"{'='*60}")
        context.set_custom_status("📜 Fase 6: Biblia...")
        
        full_text = "\n".join([f"CAP {f['title']}: {f['content'][:600]}..." for f in fragments])
        
        try:
            holistic = yield context.call_activity('HolisticReading', full_text)
            logging.info(f"✅ Lectura holística completada")
        except Exception as e:
            logging.error(f"❌ ERROR en HolisticReading: {str(e)}")
            raise
        
        bible_in = {
            "chapter_analyses": consolidated,
            "holistic_analysis": holistic,
            "book_metadata": book_metadata
        }
        
        try:
            bible = yield context.call_activity('CreateBible', json.dumps(bible_in))
            logging.info(f"✅ Biblia narrativa creada")
        except Exception as e:
            logging.error(f"❌ ERROR en CreateBible: {str(e)}")
            raise
        
        t6 = context.current_utc_datetime
        tiempos['biblia'] = str(t6 - t5)
        logging.info(f"⏱️ Tiempo Biblia: {tiempos['biblia']}")

        # ---------------------------------------------------------------------
        # FASE 10: ARCOS
        # ---------------------------------------------------------------------
        context.set_custom_status("🗺️ Fase 10: Arcos...")
        
        arc_results = yield from run_gemini_pro_batch(
            context, 'arc_maps', consolidated, bible=bible
        )
        arc_map_dict = {str(r['chapter_id']): r for r in arc_results}
        
        t10 = context.current_utc_datetime
        tiempos['arcos'] = str(t10 - t6)
        logging.info(f"⏱️ Tiempo Arcos: {tiempos['arcos']}")

        # ---------------------------------------------------------------------
        # FASE 11: EDICIÓN
        # ---------------------------------------------------------------------
        context.set_custom_status("✏️ Fase 11: Edición...")
        
        edit_reqs = []
        for frag in fragments:
            edit_reqs.append({'chapter': frag})
            
        edited_fragments = yield from edit_with_claude_batch_v2(
            context, edit_reqs, bible, consolidated, arc_map_dict
        )
        
        edited_fragments.sort(key=lambda x: int(x.get('chapter_id', 0) or x.get('fragment_id', 0) or 0))
        
        t11 = context.current_utc_datetime
        tiempos['edicion'] = str(t11 - t10)
        logging.info(f"⏱️ Tiempo Edición: {tiempos['edicion']}")

        # ---------------------------------------------------------------------
        # FASE 12/13: RECONSTRUCCIÓN
        # ---------------------------------------------------------------------
        logging.info(f"")
        logging.info(f"{'='*60}")
        logging.info(f"💾 FASE 12: RECONSTRUCCIÓN DE MANUSCRITO")
        logging.info(f"{'='*60}")
        context.set_custom_status("💾 Finalizando...")
        
        recon_input = {
            'edited_chapters': edited_fragments,
            'book_name': book_name,
            'bible': bible
        }
        
        try:
            manuscript = yield context.call_activity('ReconstructManuscript', recon_input)
            logging.info(f"✅ Manuscrito reconstruido")
        except Exception as e:
            logging.error(f"❌ ERROR en ReconstructManuscript: {str(e)}")
            raise
        
        t_final = context.current_utc_datetime
        tiempos['reconstruccion'] = str(t_final - t11)
        tiempos['total'] = str(t_final - start_time)
        
        # ---------------------------------------------------------------------
        # GUARDAR Y FINALIZAR
        # ---------------------------------------------------------------------
        final = {
            'status': 'success',
            'job_id': context.instance_id,
            'book_name': book_name,
            'manuscript': manuscript,
            'tiempos': tiempos,
            'stats': {
                'fragmentos_entrada': len(fragments),
                'capitulos_consolidados': len(consolidated),
                'capitulos_editados': len(edited_fragments)
            }
        }
        
        try:
            yield context.call_activity('SaveOutputs', final)
        except Exception as e:
            logging.error(f"❌ ERROR en SaveOutputs: {str(e)}")
            # No re-raise, el resultado ya está listo
        
        # RESUMEN FINAL
        logging.info(f"")
        logging.info(f"{'#'*70}")
        logging.info(f"#  ✅✅ SYLPHRENA 4.0.2 - COMPLETADO EXITOSAMENTE ✅✅")
        logging.info(f"{'#'*70}")
        logging.info(f"#  📚 Libro: {book_name}")
        logging.info(f"#  🔢 Fragmentos procesados: {len(fragments)}")
        logging.info(f"#  📖 Capítulos editados: {len(edited_fragments)}")
        logging.info(f"#")
        logging.info(f"#  ⏱️ TIEMPOS:")
        for fase, tiempo in tiempos.items():
            logging.info(f"#     {fase}: {tiempo}")
        logging.info(f"#")
        logging.info(f"#  💰 Job ID: {context.instance_id}")
        logging.info(f"{'#'*70}")
        
        return final

    except Exception as e:
        logging.error(f"")
        logging.error(f"{'!'*70}")
        logging.error(f"!  💥 ERROR FATAL EN ORQUESTADOR")
        logging.error(f"{'!'*70}")
        logging.error(f"!  Error: {str(e)}")
        logging.error(f"!  Tipo: {type(e).__name__}")
        
        import traceback
        tb = traceback.format_exc()
        for line in tb.split('\n'):
            if line.strip():
                logging.error(f"!  {line}")
        
        logging.error(f"{'!'*70}")
        raise e

main = df.Orchestrator.create(orchestrator_function)
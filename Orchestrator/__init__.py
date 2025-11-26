# =============================================================================
# Orchestrator/__init__.py - VERSIÓN 3.1 COMPLETA (CORREGIDA)
# =============================================================================
import azure.functions as func
import azure.durable_functions as df
import logging
import json
from datetime import timedelta

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

USE_BATCH_API = True
USE_LANGUAGETOOL = False  # Desactivado (rate limit + poco beneficio)

ANALYSIS_BATCH_SIZE = 5
EDIT_BATCH_SIZE = 3

BATCH_POLL_INTERVAL_SECONDS = 60
BATCH_MAX_WAIT_MINUTES = 30

CLAUDE_BATCH_MAX_WAIT_MINUTES = 120
CLAUDE_BATCH_POLL_INTERVAL_SECONDS = 120


def orchestrator_function(context: df.DurableOrchestrationContext):
    try:
        book_path = context.get_input()
        start_time = context.current_utc_datetime
        instance_id = context.instance_id
        
        # Extraer nombre del libro
        book_name = book_path.split('/')[-1].split('.')[0] if book_path else "libro"
        
        # =================================================================
        # 1. SEGMENTACIÓN
        # =================================================================
        context.set_custom_status("📚 Segmentando libro...")
        logging.info("🎬 Iniciando Sylphrena v3.1")
        
        chapters = yield context.call_activity('SegmentBook', book_path)
        
        seg_time = context.current_utc_datetime
        if not chapters:
            raise ValueError("La segmentación no devolvió capítulos.")

        total_chapters = len(chapters)
        seg_seconds = (seg_time - start_time).total_seconds()
        logging.info(f"✅ Segmentación: {total_chapters} capítulos en {seg_seconds:.1f}s")
        
        # =================================================================
        # 2. ANÁLISIS
        # =================================================================
        if USE_BATCH_API:
            chapter_analyses = yield from analyze_with_batch_api(context, chapters)
        else:
            chapter_analyses = yield from analyze_with_simple_batches(context, chapters)
        
        analysis_time = context.current_utc_datetime
        analysis_seconds = (analysis_time - seg_time).total_seconds()
        logging.info(f"✅ Análisis completado en {analysis_seconds:.1f}s")
        
        # =================================================================
        # 3. LECTURA HOLÍSTICA
        # =================================================================
        context.set_custom_status("📖 Lectura holística del libro...")
        
        full_book_text = "\n\n---\n\n".join([
            f"CAPÍTULO: {ch['title']}\n\n{ch['content']}" 
            for ch in chapters
        ])
        
        word_count = len(full_book_text.split())
        logging.info(f"📖 Enviando {word_count:,} palabras a lectura holística...")
        
        holistic_analysis = yield context.call_activity('HolisticReading', full_book_text)
        
        holistic_time = context.current_utc_datetime
        holistic_seconds = (holistic_time - analysis_time).total_seconds()
        logging.info(f"✅ Lectura holística en {holistic_seconds:.1f}s")

        # =================================================================
        # 4. CREAR BIBLIA
        # =================================================================
        context.set_custom_status("📜 Construyendo Biblia Narrativa...")
        
        bible_input = {
            "chapter_analyses": chapter_analyses,
            "holistic_analysis": holistic_analysis
        }
        
        bible = yield context.call_activity('CreateBible', json.dumps(bible_input))
        
        bible_time = context.current_utc_datetime
        bible_seconds = (bible_time - holistic_time).total_seconds()
        logging.info(f"✅ Biblia creada en {bible_seconds:.1f}s")

        # =================================================================
        # 5. CORRECCIÓN MECÁNICA (opcional)
        # =================================================================
        if USE_LANGUAGETOOL:
            context.set_custom_status("🔧 Corrección mecánica...")
            corrected_chapters = yield from apply_mechanical_corrections(context, chapters)
            mechanical_seconds = (context.current_utc_datetime - bible_time).total_seconds()
        else:
            corrected_chapters = chapters
            mechanical_seconds = 0
            logging.info("⏭️ LanguageTool deshabilitado")

        # =================================================================
        # 6. EDICIÓN CON CLAUDE BATCH API (LÓGICA CORREGIDA AQUI ABAJO)
        # =================================================================
        context.set_custom_status("✏️ Edición con Claude Batch...")
        pre_edit_time = context.current_utc_datetime
        
        edited_chapters = yield from edit_with_claude_batch(context, corrected_chapters, chapter_analyses, bible)

        edit_time = context.current_utc_datetime
        edit_seconds = (edit_time - pre_edit_time).total_seconds()
        logging.info(f"✅ Edición completada en {edit_seconds:.1f}s")

        # =================================================================
        # 7. GUARDAR OUTPUTS ORGANIZADOS
        # =================================================================
        context.set_custom_status("💾 Guardando resultados...")
        
        tiempos = {
            'segmentacion': f"{seg_seconds:.1f}s",
            'analisis': f"{analysis_seconds:.1f}s",
            'holistica': f"{holistic_seconds:.1f}s",
            'biblia': f"{bible_seconds:.1f}s",
            'mecanica': f"{mechanical_seconds:.1f}s",
            'edicion': f"{edit_seconds:.1f}s",
            'total': f"{(edit_time - start_time).total_seconds()/60:.1f} min"
        }
        
        save_input = {
            'job_id': instance_id,
            'book_name': book_name,
            'bible': bible,
            'edited_chapters': edited_chapters,
            'original_chapters': chapters,
            'tiempos': tiempos
        }
        
        save_result = yield context.call_activity('SaveOutputs', save_input)
        
        logging.info(f"💾 Outputs guardados: {save_result.get('status')}")

        # =================================================================
        # 8. RESULTADO FINAL CON COSTOS
        # =================================================================
        context.set_custom_status("✅ Completado")
        
        total_seconds = (edit_time - start_time).total_seconds()
        tokens_libro = int(word_count * 1.33)
        
        # Calcular costos estimados
        costos = {
            'segmentacion': round(tokens_libro * 0.10 / 1_000_000, 4),
            'analisis_batch': round(tokens_libro * 0.05 / 1_000_000, 4),
            'holistica': round(tokens_libro * 1.25 / 1_000_000 + 5000 * 5.00 / 1_000_000, 4),
            'biblia': round(len(chapter_analyses) * 300 * 1.25 / 1_000_000 + 8000 * 5.00 / 1_000_000, 4),
            'edicion_input': round(tokens_libro * 2 * 1.50 / 1_000_000, 4),
            'edicion_output': round(tokens_libro * 1.1 * 7.50 / 1_000_000, 4),
            'infraestructura': 0.05
        }
        costos['total'] = round(sum(costos.values()), 2)
        
        logging.info(f"💰 COSTO TOTAL ESTIMADO: ${costos['total']:.2f}")
        
        return {
            'status': 'completed',
            'version': 'v3.1',
            'job_id': instance_id,
            'book_name': book_name,
            'palabras': word_count,
            'total_chapters': total_chapters,
            'chapters_analyzed': len(chapter_analyses),
            'chapters_edited': len(edited_chapters),
            'tiempos': tiempos,
            'costos': costos,
            'outputs': save_result.get('urls', {}),
            'outputs_container': save_result.get('container', 'sylphrena-outputs'),
            'outputs_path': save_result.get('base_path', instance_id),
        }
        
    except Exception as e:
        logging.error(f"💥 Error fatal: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        
        return {
            'status': 'error',
            'message': str(e)
        }


# =============================================================================
# ANÁLISIS CON LOTES SIMPLES
# =============================================================================

def analyze_with_simple_batches(context, chapters):
    """Analiza capítulos en lotes pequeños (sin Batch API)."""
    total_chapters = len(chapters)
    total_batches = (total_chapters + ANALYSIS_BATCH_SIZE - 1) // ANALYSIS_BATCH_SIZE
    
    logging.info(f"📊 Modo LOTES SIMPLES: {total_batches} lotes de {ANALYSIS_BATCH_SIZE}")
    
    all_analyses = []
    failed = []
    
    for batch_num, i in enumerate(range(0, total_chapters, ANALYSIS_BATCH_SIZE), 1):
        batch = chapters[i:i + ANALYSIS_BATCH_SIZE]
        batch_ids = [ch.get('id', '?') for ch in batch]
        
        context.set_custom_status(f"🔍 Analizando lote {batch_num}/{total_batches}")
        logging.info(f"🔍 Lote {batch_num}/{total_batches}: IDs {batch_ids}")
        
        try:
            tasks = [context.call_activity('AnalyzeChapter', ch) for ch in batch]
            results = yield context.task_all(tasks)
            
            for result in results:
                if result.get('error') or result.get('status') == 'fatal_error':
                    failed.append(result)
                else:
                    all_analyses.append(result)
            
            logging.info(f"✅ Lote {batch_num} completado")
            
        except Exception as e:
            logging.error(f"❌ Error en lote {batch_num}: {e}")
            for ch in batch:
                failed.append({'chapter_id': ch.get('id'), 'error': str(e)})
    
    logging.info(f"📊 Análisis: {len(all_analyses)} OK, {len(failed)} fallidos")
    return all_analyses


# =============================================================================
# ANÁLISIS CON BATCH API
# =============================================================================

def analyze_with_batch_api(context, chapters):
    """Analiza capítulos usando Gemini Batch API."""
    logging.info(f"📦 Modo BATCH API: {len(chapters)} capítulos")
    
    context.set_custom_status("📤 Enviando a Gemini Batch API...")
    
    batch_info = yield context.call_activity('SubmitBatchAnalysis', chapters)
    
    if batch_info.get('error'):
        raise Exception(f"Error creando batch: {batch_info.get('error')}")
    
    logging.info(f"📦 Batch Job creado: {batch_info.get('batch_job_name', 'N/A')}")
    
    for attempt in range(BATCH_MAX_WAIT_MINUTES):
        context.set_custom_status(f"⏳ Esperando Batch API... ({attempt + 1}/{BATCH_MAX_WAIT_MINUTES} min)")
        
        next_check = context.current_utc_datetime + timedelta(seconds=BATCH_POLL_INTERVAL_SECONDS)
        yield context.create_timer(next_check)
        
        result = yield context.call_activity('PollBatchResult', batch_info)
        
        if isinstance(result, list):
            logging.info(f"✅ Batch completado: {len(result)} análisis")
            return result
        
        if result.get('status') == 'failed':
            raise Exception(f"Batch falló: {result.get('error')}")
        
        batch_info = result
        logging.info(f"⏳ Batch aún procesando... (intento {attempt + 1})")
    
    raise Exception(f"Batch no completó en {BATCH_MAX_WAIT_MINUTES} minutos")


# =============================================================================
# CORRECCIÓN MECÁNICA
# =============================================================================

def apply_mechanical_corrections(context, chapters):
    """Aplica corrección mecánica a todos los capítulos."""
    logging.info(f"🔧 Aplicando corrección mecánica a {len(chapters)} capítulos...")
    context.set_custom_status("🔧 Corrección mecánica (LanguageTool)")
    
    corrected_chapters = []
    total_corrections = 0
    
    MECHANICAL_BATCH_SIZE = 5
    
    for i in range(0, len(chapters), MECHANICAL_BATCH_SIZE):
        batch = chapters[i:i + MECHANICAL_BATCH_SIZE]
        
        tasks = [context.call_activity('MechanicalCorrection', ch) for ch in batch]
        results = yield context.task_all(tasks)
        
        for result in results:
            corrected_chapters.append(result)
            total_corrections += result.get('corrections_count', 0)
    
    logging.info(f"✅ Corrección mecánica: {total_corrections} correcciones totales")
    return corrected_chapters


# =============================================================================
# EDICIÓN CON CLAUDE BATCH API
# =============================================================================

def edit_with_claude_batch(context, chapters, chapter_analyses, bible):
    """Edita capítulos usando Claude Batch API (50% descuento)."""
    
    chapters_to_edit = []
    for chapter in chapters:
        ch_id = str(chapter.get('id'))
        analysis = next(
            (a for a in chapter_analyses if str(a.get('chapter_id')) == ch_id),
            None
        )
        if analysis:
            chapters_to_edit.append(chapter)
    
    total_to_edit = len(chapters_to_edit)
    logging.info(f"✏️ Enviando {total_to_edit} capítulos a Claude Batch API")
    
    if total_to_edit == 0:
        logging.warning("⚠️ No hay capítulos para editar")
        return []
    
    context.set_custom_status("📤 Enviando a Claude Batch API...")
    
    edit_request = {
        'chapters': chapters_to_edit,
        'bible': bible,
        'analyses': chapter_analyses
    }
    
    batch_info = yield context.call_activity('SubmitClaudeBatch', edit_request)
    
    if batch_info.get('error'):
        raise Exception(f"Error creando Claude batch: {batch_info.get('error')}")
    
    batch_id = batch_info.get('batch_id')
    logging.info(f"📦 Claude Batch creado: {batch_id}")
    
    for attempt in range(CLAUDE_BATCH_MAX_WAIT_MINUTES):
        context.set_custom_status(f"⏳ Esperando Claude Batch... ({attempt + 1}/{CLAUDE_BATCH_MAX_WAIT_MINUTES} min)")
        
        # Esperar
        next_check = context.current_utc_datetime + timedelta(seconds=CLAUDE_BATCH_POLL_INTERVAL_SECONDS)
        yield context.create_timer(next_check)
        
        # Consultar
        result = yield context.call_activity('PollClaudeBatchResult', batch_info)
        
        # === 🛡️ LOGGING DE DIAGNÓSTICO (PARA VERIFICAR QUE NO ESTÁ VACÍO) ===
        res_type = "LISTA" if isinstance(result, list) else "DICT"
        res_status = result.get('status', 'N/A') if isinstance(result, dict) else 'COMPLETADO'
        logging.info(f"🕵️ DEBUG Claude Poll: Tipo={res_type}, Status={res_status}, Attempt={attempt}")
        # ===================================================================

        if isinstance(result, list):
            if not result and attempt < 2:
                 logging.warning("⚠️ ALERTA: Claude devolvió lista vacía muy rápido.")
            
            logging.info(f"✅ Claude Batch completado: {len(result)} capítulos editados")
            return result
        
        if result.get('status') == 'error':
            raise Exception(f"Claude Batch falló: {result.get('error')}")
        
        if result.get('status') == 'completed_no_results':
            logging.warning("⚠️ Claude Batch completó pero sin resultados")
            return []
        
        # Actualizar info para siguiente poll
        batch_info = result
        
        counts = result.get('request_counts', {})
        logging.info(f"⏳ Claude procesando... ({counts.get('succeeded', 0)} OK, {counts.get('processing', 0)} pendientes)")
    
    raise Exception(f"Claude Batch no completó en {CLAUDE_BATCH_MAX_WAIT_MINUTES} minutos")


main = df.Orchestrator.create(orchestrator_function)
# =============================================================================
# Orchestrator/__init__.py - VERSIÓN COMPLETA v2.5
# =============================================================================
# 
# DOS MODOS DE OPERACIÓN:
#   1. LOTES SIMPLES (default) - Funciona YA, sin configuración extra
#   2. BATCH API - Requiere GCP configurado (más barato, más robusto)
#
# Para cambiar de modo, modifica USE_BATCH_API abajo.
# =============================================================================

import azure.functions as func
import azure.durable_functions as df
import logging
import json
from datetime import timedelta

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

# Cambiar a True cuando tengas GCP configurado
USE_BATCH_API = True

# Tamaños de lote para modo simple
ANALYSIS_BATCH_SIZE = 5    # Capítulos a analizar con Gemini (simultáneos)
EDIT_BATCH_SIZE = 3        # Capítulos a editar con Claude (simultáneos)

# Configuración de Batch API (solo si USE_BATCH_API = True)
BATCH_POLL_INTERVAL_SECONDS = 60
BATCH_MAX_WAIT_MINUTES = 30

# ─────────────────────────────────────────────────────────────────
# CONFIGURACIÓN CLAUDE BATCH
# ─────────────────────────────────────────────────────────────────
CLAUDE_BATCH_MAX_WAIT_MINUTES = 120  # 2 horas máximo (normalmente es menos)
CLAUDE_BATCH_POLL_INTERVAL_SECONDS = 120  # Cada 2 minutos
USE_LANGUAGETOOL = True  # Habilitar corrección mecánica


def orchestrator_function(context: df.DurableOrchestrationContext):
    try:
        book_path = context.get_input()
        start_time = context.current_utc_datetime
        
        # =================================================================
        # 1. SEGMENTACIÓN
        # =================================================================
        context.set_custom_status("📚 Segmentando libro...")
        logging.info("🎬 Iniciando Sylphrena v2.5")
        
        chapters = yield context.call_activity('SegmentBook', book_path)
        
        seg_time = context.current_utc_datetime
        if not chapters:
            raise ValueError("La segmentación no devolvió capítulos.")

        total_chapters = len(chapters)
        seg_seconds = (seg_time - start_time).total_seconds()
        logging.info(f"✅ Segmentación: {total_chapters} capítulos en {seg_seconds:.1f}s")
        
        # =================================================================
        # 2. ANÁLISIS - Elegir modo
        # =================================================================
        if USE_BATCH_API:
            # ─────────────────────────────────────────────────────────────
            # MODO BATCH API (requiere GCP)
            # ─────────────────────────────────────────────────────────────
            chapter_analyses = yield from analyze_with_batch_api(context, chapters)
        else:
            # ─────────────────────────────────────────────────────────────
            # MODO LOTES SIMPLES (funciona ya)
            # ─────────────────────────────────────────────────────────────
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
        # 5A. CORRECCIÓN MECÁNICA (LanguageTool)
        # =================================================================
        context.set_custom_status("🔧 Corrección mecánica...")
        corrected_chapters = yield from apply_mechanical_corrections(context, chapters)

        mechanical_time = context.current_utc_datetime
        mechanical_seconds = (mechanical_time - bible_time).total_seconds()
        logging.info(f"✅ Corrección mecánica completada en {mechanical_seconds:.1f}s")

        # =================================================================
        # 5B. EDICIÓN CON CLAUDE BATCH API
        # =================================================================
        context.set_custom_status("✏️ Edición con Claude Batch...")
        edited_chapters = yield from edit_with_claude_batch(context, corrected_chapters, chapter_analyses, bible)

        edit_time = context.current_utc_datetime
        edit_seconds = (edit_time - mechanical_time).total_seconds() # Tiempo solo para 5B
        total_seconds = (edit_time - start_time).total_seconds() # Tiempo desde el inicio (PASO 1)
        
        logging.info(f"✅ Edición con Claude completada en {edit_seconds:.1f}s")
        logging.info(f"⏱️ TIEMPO TOTAL DEL ORCHESTRATOR: {total_seconds/60:.1f} minutos")

        # =================================================================
        # 6. RESULTADO FINAL
        # =================================================================
        context.set_custom_status("✅ Completado")
        
        return {
            'status': 'completed',
            'version': 'v2.5',
            'mode': 'batch_api' if USE_BATCH_API else 'simple_batches',
            'total_chapters': total_chapters,
            'chapters_analyzed': len(chapter_analyses),
            'chapters_edited': len(edited_chapters),
            'tiempos': {
                'segmentacion': f"{seg_seconds:.1f}s",
                'analisis': f"{analysis_seconds:.1f}s",
                'holistica': f"{holistic_seconds:.1f}s",
                'biblia': f"{bible_seconds:.1f}s",
                'mecanica': f"{mechanical_seconds:.1f}s",  # 🆕
                'edicion': f"{edit_seconds:.1f}s",
                'total': f"{total_seconds/60:.1f} min"
            },
            'bible_metadata': bible.get('_metadata', {}),
            'edited_chapter_ids': [e.get('chapter_id') for e in edited_chapters]
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
# MODO 1: LOTES SIMPLES (funciona ya, sin GCP)
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
# MODO 2: BATCH API (requiere GCP configurado)
# =============================================================================

def analyze_with_batch_api(context, chapters):
    """Analiza capítulos usando Gemini Batch API."""
    logging.info(f"📦 Modo BATCH API: {len(chapters)} capítulos")
    
    context.set_custom_status("📤 Enviando a Gemini Batch API...")
    
    # Enviar batch
    batch_info = yield context.call_activity('SubmitBatchAnalysis', chapters)
    
    if batch_info.get('error'):
        raise Exception(f"Error creando batch: {batch_info.get('error')}")
    
    logging.info(f"📦 Batch Job creado: {batch_info.get('batch_job_id', 'N/A')}")
    
    # Polling hasta completar
    for attempt in range(BATCH_MAX_WAIT_MINUTES):
        context.set_custom_status(f"⏳ Esperando Batch API... ({attempt + 1}/{BATCH_MAX_WAIT_MINUTES} min)")
        
        # Timer de Durable Functions (no bloquea el orquestador)
        next_check = context.current_utc_datetime + timedelta(seconds=BATCH_POLL_INTERVAL_SECONDS)
        yield context.create_timer(next_check)
        
        # Consultar estado
        result = yield context.call_activity('PollBatchResult', batch_info)
        
        if isinstance(result, list):
            # ¡Completado! Tenemos los análisis
            logging.info(f"✅ Batch completado: {len(result)} análisis")
            return result
        
        if result.get('status') == 'failed':
            raise Exception(f"Batch falló: {result.get('error')}")
        
        # Sigue procesando, continuar polling
        logging.info(f"⏳ Batch aún procesando... (intento {attempt + 1})")
    
    raise Exception(f"Batch no completó en {BATCH_MAX_WAIT_MINUTES} minutos")


# =============================================================================
# EDICIÓN CON CLAUDE (siempre en lotes)
# =============================================================================

# =============================================================================
# CORRECCIÓN MECÁNICA CON LANGUAGETOOL
# =============================================================================

def apply_mechanical_corrections(context, chapters):
    """Aplica corrección mecánica a todos los capítulos."""
    if not USE_LANGUAGETOOL:
        logging.info("⏭️ LanguageTool deshabilitado, saltando corrección mecánica")
        return chapters
    
    logging.info(f"🔧 Aplicando corrección mecánica a {len(chapters)} capítulos...")
    context.set_custom_status("🔧 Corrección mecánica (LanguageTool)")
    
    corrected_chapters = []
    total_corrections = 0
    
    # Procesar en lotes pequeños para no saturar
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
    
    # Emparejar capítulos con sus análisis
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
    
    # ─────────────────────────────────────────────────────────────────
    # 1. ENVIAR BATCH
    # ─────────────────────────────────────────────────────────────────
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
    
    # ─────────────────────────────────────────────────────────────────
    # 2. POLLING HASTA COMPLETAR
    # ─────────────────────────────────────────────────────────────────
    for attempt in range(CLAUDE_BATCH_MAX_WAIT_MINUTES):
        context.set_custom_status(f"⏳ Esperando Claude Batch... ({attempt + 1}/{CLAUDE_BATCH_MAX_WAIT_MINUTES} min)")
        
        # Timer de Durable Functions
        next_check = context.current_utc_datetime + timedelta(seconds=CLAUDE_BATCH_POLL_INTERVAL_SECONDS)
        yield context.create_timer(next_check)
        
        # Consultar estado
        result = yield context.call_activity('PollClaudeBatchResult', batch_info)
        
        if isinstance(result, list):
            # ¡Completado! Tenemos los capítulos editados
            logging.info(f"✅ Claude Batch completado: {len(result)} capítulos editados")
            return result
        
        if result.get('status') == 'error':
            raise Exception(f"Claude Batch falló: {result.get('error')}")
        
        if result.get('status') == 'completed_no_results':
            logging.warning("⚠️ Claude Batch completó pero sin resultados extraíbles")
            return []
        
        # Sigue procesando, actualizar batch_info con id_map
        batch_info = result
        
        counts = result.get('request_counts', {})
        logging.info(f"⏳ Claude Batch procesando... ({counts.get('succeeded', 0)} OK, {counts.get('processing', 0)} pendientes)")
    
    raise Exception(f"Claude Batch no completó en {CLAUDE_BATCH_MAX_WAIT_MINUTES} minutos")


main = df.Orchestrator.create(orchestrator_function)
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
        # 5. EDICIÓN CON CLAUDE (en lotes)
        # =================================================================
        edited_chapters = yield from edit_with_batches(context, chapters, chapter_analyses, bible)
        
        edit_time = context.current_utc_datetime
        edit_seconds = (edit_time - bible_time).total_seconds()
        total_seconds = (edit_time - start_time).total_seconds()
        
        logging.info(f"✅ Edición completada en {edit_seconds:.1f}s")
        logging.info(f"⏱️ TIEMPO TOTAL: {total_seconds/60:.1f} minutos")

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
    
    batch_job_name = batch_info.get('batch_job_name')
    logging.info(f"📦 Batch Job creado: {batch_job_name}")
    
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
        
        if result.get('status') == 'completed_no_results':
            logging.warning("⚠️ Batch completó pero sin resultados extraíbles")
            return []
        
        # Sigue procesando, continuar polling
        logging.info(f"⏳ Batch aún procesando... (intento {attempt + 1})")
    
    raise Exception(f"Batch no completó en {BATCH_MAX_WAIT_MINUTES} minutos")


# =============================================================================
# EDICIÓN CON CLAUDE (siempre en lotes)
# =============================================================================

def edit_with_batches(context, chapters, chapter_analyses, bible):
    """Edita capítulos en lotes con Claude."""
    
    # Emparejar capítulos con sus análisis
    chapters_to_edit = []
    for chapter in chapters:
        ch_id = str(chapter.get('id'))
        analysis = next(
            (a for a in chapter_analyses if str(a.get('chapter_id')) == ch_id),
            None
        )
        if analysis:
            chapters_to_edit.append({'chapter': chapter, 'analysis': analysis})
    
    total_to_edit = len(chapters_to_edit)
    total_batches = (total_to_edit + EDIT_BATCH_SIZE - 1) // EDIT_BATCH_SIZE
    
    logging.info(f"✏️ Editando {total_to_edit} capítulos en {total_batches} lotes")
    
    all_edited = []
    failed = []
    
    for batch_num, i in enumerate(range(0, total_to_edit, EDIT_BATCH_SIZE), 1):
        batch = chapters_to_edit[i:i + EDIT_BATCH_SIZE]
        
        context.set_custom_status(f"✏️ Editando lote {batch_num}/{total_batches}")
        logging.info(f"✏️ Lote edición {batch_num}/{total_batches}")
        
        try:
            tasks = []
            for item in batch:
                edit_input = {
                    'chapter': item['chapter'],
                    'bible': bible,
                    'analysis': item['analysis']
                }
                tasks.append(context.call_activity('EditChapter', edit_input))
            
            results = yield context.task_all(tasks)
            
            for result in results:
                if result.get('status') == 'error':
                    failed.append(result)
                else:
                    all_edited.append(result)
                    
        except Exception as e:
            logging.error(f"❌ Error en lote edición {batch_num}: {e}")
    
    logging.info(f"✏️ Edición: {len(all_edited)} OK, {len(failed)} fallidos")
    return all_edited


main = df.Orchestrator.create(orchestrator_function)
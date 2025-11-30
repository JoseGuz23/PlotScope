# =============================================================================
# Orchestrator/__init__.py - SYLPHRENA 4.0 (OPTIMIZED)
# =============================================================================
# CAMBIOS APLICADOS:
#   - Modo Prueba (Limit to 5 chapters)
#   - Fix de Ordenamiento (Sort by ID)
#   - Paralelización de Fases 4, 5 y 10 (Task.all)
# =============================================================================

import azure.functions as func
import azure.durable_functions as df
import logging
import json
from datetime import timedelta

# =============================================================================
# CONFIGURACIÓN SYLPHRENA 4.0
# =============================================================================

# Modos de procesamiento
USE_BATCH_API = True                    # Usar Gemini Batch API (50% descuento)
USE_CLAUDE_BATCH = True                 # Usar Claude Batch API (50% descuento)
ENABLE_IMPACT_VALIDATION = True         # Validar impacto de ediciones
ENABLE_CAUSALITY_ANALYSIS = True        # Análisis de causalidad narrativa
ENABLE_CROSS_VALIDATION = True          # Validación cruzada de Biblia

# --- MODO DE PRUEBA (BOTÓN DE PÁNICO) ---
LIMIT_TO_FIRST_5_CHAPTERS = True        # <--- CAMBIAR A FALSE EN PRODUCCIÓN
# ----------------------------------------

# Límites de concurrencia (Ignorados por Batch API, usados para fallback)
ANALYSIS_BATCH_SIZE = 5
EDIT_BATCH_SIZE = 3

# Tiempos de espera para Batch APIs
BATCH_POLL_INTERVAL_SECONDS = 60
BATCH_MAX_WAIT_MINUTES = 45
CLAUDE_BATCH_MAX_WAIT_MINUTES = 120
CLAUDE_BATCH_POLL_INTERVAL_SECONDS = 120


def orchestrator_function(context: df.DurableOrchestrationContext):
    """
    Orquestador principal de Sylphrena 4.0.
    """
    try:
        book_path = context.get_input()
        start_time = context.current_utc_datetime
        instance_id = context.instance_id
        
        # Extraer nombre del libro
        book_name = book_path.split('/')[-1].split('.')[0] if book_path else "libro"
        
        tiempos = {}
        
        # =================================================================
        # FASE 1: SEGMENTACIÓN CON METADATOS JERÁRQUICOS
        # =================================================================
        context.set_custom_status("📚 Fase 1/13: Segmentando libro con contexto jerárquico...")
        logging.info("🎬 Iniciando Sylphrena v4.0")
        
        segmentation_result = yield context.call_activity('SegmentBook', book_path)
        
        # Extraer componentes del resultado
        fragments = segmentation_result.get('fragments', [])
        book_metadata = segmentation_result.get('book_metadata', {})
        chapter_map = segmentation_result.get('chapter_map', {})

        seg_time = context.current_utc_datetime
        tiempos['segmentacion'] = f"{(seg_time - start_time).total_seconds():.1f}s"
        
        if not fragments:
            raise ValueError("La segmentación no devolvió fragmentos.")
            
        # -----------------------------------------------------------------
        # LIMITAR A 5 CAPÍTULOS SI EL MODO DE PRUEBA ESTÁ ACTIVO
        # -----------------------------------------------------------------
        if LIMIT_TO_FIRST_5_CHAPTERS:
            logging.warning("⚠️ MODO PRUEBA ACTIVO: Limitando a los primeros 5 capítulos.")
            
            # Filtramos los fragmentos cuyo 'parent_chapter_id' sea <= 5
            fragments = [f for f in fragments if int(f.get('parent_chapter_id', 999)) <= 5]
            
            # Ajustamos también el mapa de capítulos
            chapter_map = {k: v for k, v in chapter_map.items() if int(k) <= 5}
            
            # Ajustamos metadatos
            book_metadata['total_chapters'] = len(chapter_map)
            book_metadata['total_fragments'] = len(fragments)
            book_metadata['total_words'] = sum(f.get('word_count', 0) for f in fragments)
            
            logging.warning(f"⚠️ PROCESANDO SOLO: {len(fragments)} fragmentos de {len(chapter_map)} capítulos.")
        # -----------------------------------------------------------------

        total_fragments = len(fragments)
        total_chapters = len(chapter_map)
        total_words = book_metadata.get('total_words', 0)
        
        logging.info(f"✅ Segmentación: {total_chapters} capítulos, {total_fragments} fragmentos, {total_words:,} palabras")
        
        # =================================================================
        # FASE 2: ANÁLISIS CAPA 1 (EXTRACCIÓN FACTUAL)
        # =================================================================
        context.set_custom_status(f"🔍 Fase 2/13: Análisis Capa 1 ({total_fragments} fragmentos)...")
        
        if USE_BATCH_API:
            fragment_analyses = yield from analyze_with_batch_api(context, fragments)
        else:
            fragment_analyses = yield from analyze_with_simple_batches(context, fragments)
            
        # [FIX 1] ORDENAR RESULTADOS DEL BATCH
        fragment_analyses.sort(key=lambda x: int(x.get('fragment_id', 0) or x.get('id', 0)))
        logging.info("✅ Fragmentos ordenados numéricamente tras el análisis.")
        
        analysis_time = context.current_utc_datetime
        tiempos['analisis_capa1'] = f"{(analysis_time - seg_time).total_seconds():.1f}s"
        logging.info(f"✅ Análisis Capa 1 completado: {len(fragment_analyses)} fragmentos analizados")
        
        # =================================================================
        # FASE 3: CONSOLIDACIÓN DE FRAGMENTOS POR CAPÍTULO
        # =================================================================
        context.set_custom_status("🔧 Fase 3/13: Consolidando fragmentos por capítulo...")
        
        consolidated_analyses = yield context.call_activity(
            'ConsolidateFragmentAnalyses',
            {
                'fragment_analyses': fragment_analyses,
                'chapter_map': chapter_map
            }
        )
        
        consolidation_time = context.current_utc_datetime
        tiempos['consolidacion'] = f"{(consolidation_time - analysis_time).total_seconds():.1f}s"
        logging.info(f"✅ Consolidación: {len(consolidated_analyses)} capítulos")
        
        # =================================================================
        # FASE 4: ANÁLISIS CAPA 2 (PARALELIZADO - TURBO)
        # =================================================================
        context.set_custom_status(f"📊 Fase 4/13: Análisis Capa 2 - Patrones estructurales...")
        
        tasks_layer2 = []
        for chapter_analysis in consolidated_analyses:
            tasks_layer2.append(context.call_activity('StructuralPatternAnalysis', chapter_analysis))
        
        # Ejecutar en paralelo
        results_layer2 = yield context.task_all(tasks_layer2)
        
        # Reconstruir lista ordenada
        layer2_analyses = []
        for i, result in enumerate(results_layer2):
            chapter_data = consolidated_analyses[i]
            chapter_data['layer2_structural'] = result
            layer2_analyses.append(chapter_data)
        
        layer2_time = context.current_utc_datetime
        tiempos['analisis_capa2'] = f"{(layer2_time - consolidation_time).total_seconds():.1f}s"
        logging.info(f"✅ Análisis Capa 2 completado (Paralelo)")
        
        # =================================================================
        # FASE 5: ANÁLISIS CAPA 3 (PARALELIZADO - TURBO)
        # =================================================================
        context.set_custom_status(f"🧠 Fase 5/13: Análisis Capa 3 - Evaluación cualitativa (Deep Think)...")
        
        tasks_layer3 = []
        for i, chapter_analysis in enumerate(layer2_analyses):
            tasks_layer3.append(context.call_activity(
                'QualitativeEffectivenessAnalysis',
                {
                    'chapter_analysis': chapter_analysis,
                    'previous_chapters': [] # En paralelo perdemos contexto inmediato, priorizamos velocidad
                }
            ))
            
        results_layer3 = yield context.task_all(tasks_layer3)
        
        layer3_analyses = []
        for i, result in enumerate(results_layer3):
            chapter_data = layer2_analyses[i]
            chapter_data['layer3_qualitative'] = result
            layer3_analyses.append(chapter_data)
        
        layer3_time = context.current_utc_datetime
        tiempos['analisis_capa3'] = f"{(layer3_time - layer2_time).total_seconds():.1f}s"
        logging.info(f"✅ Análisis Capa 3 completado (Paralelo)")
        
        # =================================================================
        # FASE 6: LECTURA HOLÍSTICA
        # =================================================================
        context.set_custom_status("📖 Fase 6/13: Lectura holística del libro completo...")
        
        full_book_text = "\n\n---\n\n".join([
            f"CAPÍTULO: {frag['title']}\n\n{frag['content']}" 
            for frag in fragments
        ])
        
        holistic_analysis = yield context.call_activity('HolisticReading', full_book_text)
        
        holistic_time = context.current_utc_datetime
        tiempos['holistica'] = f"{(holistic_time - layer3_time).total_seconds():.1f}s"
        logging.info(f"✅ Lectura holística completada")
        
        # =================================================================
        # FASE 7: SÍNTESIS DE BIBLIA INICIAL
        # =================================================================
        context.set_custom_status("📜 Fase 7/13: Construyendo Biblia Narrativa...")
        
        bible_input = {
            "chapter_analyses": layer3_analyses,
            "holistic_analysis": holistic_analysis,
            "book_metadata": book_metadata
        }
        
        bible_initial = yield context.call_activity('CreateBible', json.dumps(bible_input))
        
        bible_time = context.current_utc_datetime
        tiempos['biblia_inicial'] = f"{(bible_time - holistic_time).total_seconds():.1f}s"
        logging.info(f"✅ Biblia inicial creada")
        
        # =================================================================
        # FASE 8: ANÁLISIS DE CAUSALIDAD (OPCIONAL)
        # =================================================================
        if ENABLE_CAUSALITY_ANALYSIS:
            context.set_custom_status("🔗 Fase 8/13: Análisis de causalidad narrativa...")
            
            all_events = []
            for chapter in layer3_analyses:
                eventos = chapter.get('eventos', [])
                chapter_id = chapter.get('chapter_id', '?')
                for evento in eventos:
                    evento['source_chapter'] = chapter_id
                    all_events.append(evento)
            
            causality_result = yield context.call_activity(
                'CausalityGraphAnalysis',
                {'events': all_events, 'chapters': layer3_analyses}
            )
            bible_initial['analisis_causalidad'] = causality_result
            
            causality_time = context.current_utc_datetime
            tiempos['causalidad'] = f"{(causality_time - bible_time).total_seconds():.1f}s"
            logging.info(f"✅ Análisis de causalidad completado")
        else:
            causality_time = bible_time
            tiempos['causalidad'] = "omitido"
        
        # =================================================================
        # FASE 9: VALIDACIÓN CRUZADA DE BIBLIA
        # =================================================================
        if ENABLE_CROSS_VALIDATION:
            context.set_custom_status("✅ Fase 9/13: Validación cruzada de Biblia...")
            
            validation_result = yield context.call_activity(
                'ValidateBibleCrossCheck',
                {
                    'bible': bible_initial,
                    'chapter_analyses': layer3_analyses
                }
            )
            
            bible_validated = validation_result.get('bible_validated', bible_initial)
            bible_validated['validacion_cruzada'] = validation_result.get('validation_report', {})
            
            validation_time = context.current_utc_datetime
            tiempos['validacion_cruzada'] = f"{(validation_time - causality_time).total_seconds():.1f}s"
            logging.info(f"✅ Validación cruzada completada")
        else:
            bible_validated = bible_initial
            validation_time = causality_time
            tiempos['validacion_cruzada'] = "omitido"
        
        # =================================================================
        # FASE 9.5: VALIDACIÓN DE ARCOS Y ANÁLISIS ESPECIALIZADOS
        # =================================================================
        context.set_custom_status("🔬 Fase 9.5/13: Ejecutando análisis especializados y validación de arcos...")
        
        tasks_specialized = []
        tasks_specialized.append(context.call_activity(
            'CharacterArcValidation', 
            json.dumps({'bible': bible_validated})
        ))
        tasks_specialized.append(context.call_activity(
            'SpecializedAnalyses', 
            json.dumps({'bible': bible_validated, 'book_metadata': book_metadata})
        ))
        
        results_specialized = yield context.task_all(tasks_specialized)
        
        bible_validated['validacion_arcos'] = results_specialized[0]
        bible_validated['analisis_profundos'] = results_specialized[1]
        
        logging.info("✅ Análisis especializados y validación de arcos completados")

        # =================================================================
        # FASE 10: GENERACIÓN DE MAPAS DE ARCO (PARALELIZADO - TURBO)
        # =================================================================
        context.set_custom_status("🗺️ Fase 10/13: Generando mapas de arco por capítulo...")
        
        tasks_arc = []
        for i, chapter in enumerate(layer3_analyses):
            chapter_id = chapter.get('chapter_id', i)
            tasks_arc.append(context.call_activity(
                'GenerateArcMapForChapter',
                {
                    'bible': bible_validated,
                    'chapter_id': chapter_id,
                    'chapter_analysis': chapter
                }
            ))
            
        results_arc = yield context.task_all(tasks_arc)
        
        arc_maps = {}
        for i, arc_map in enumerate(results_arc):
            chapter_id = layer3_analyses[i].get('chapter_id', i)
            arc_maps[str(chapter_id)] = arc_map
        
        arcmap_time = context.current_utc_datetime
        tiempos['mapas_arco'] = f"{(arcmap_time - validation_time).total_seconds():.1f}s"
        logging.info(f"✅ {len(arc_maps)} mapas de arco generados (Paralelo)")
        
        # =================================================================
        # FASE 11: EDICIÓN CON CLAUDE (VALIDACIÓN DE IMPACTO)
        # =================================================================
        context.set_custom_status("✏️ Fase 11/13: Edición con Claude...")
        pre_edit_time = context.current_utc_datetime
        
        edit_requests = []
        for fragment in fragments:
            parent_id = fragment.get('parent_chapter_id', fragment.get('id'))
            analysis = next((a for a in layer3_analyses if str(a.get('chapter_id')) == str(parent_id)), {})
            arc_map = arc_maps.get(str(parent_id), {})
            is_critical = arc_map.get('es_critico_estructuralmente', False)
            
            edit_requests.append({
                'chapter': fragment,
                'bible': bible_validated,
                'analysis': analysis,
                'arc_map': arc_map,
                'is_critical': is_critical and ENABLE_IMPACT_VALIDATION
            })
        
        if USE_CLAUDE_BATCH:
            edited_fragments = yield from edit_with_claude_batch(
                context, edit_requests, bible_validated, layer3_analyses, arc_maps
            )
        else:
            edited_fragments = yield from edit_sequentially(context, edit_requests)
        
        # [FIX 2] ORDENAR RESULTADOS DE EDICIÓN
        edited_fragments.sort(key=lambda x: int(x.get('fragment_id', 0) or x.get('chapter_id', 0)))
        logging.info("✅ Capítulos editados ordenados correctamente.")

        edit_time = context.current_utc_datetime
        tiempos['edicion'] = f"{(edit_time - pre_edit_time).total_seconds():.1f}s"
        logging.info(f"✅ Edición completada: {len(edited_fragments)} fragmentos")
        
        # =================================================================
        # FASE 12: RECONSTRUCCIÓN DE MANUSCRITO
        # =================================================================
        context.set_custom_status("📄 Fase 12/13: Reconstruyendo manuscrito...")
        
        reconstruct_result = yield context.call_activity(
            'ReconstructManuscript',
            {
                'edited_chapters': edited_fragments,
                'book_name': book_name,
                'bible': bible_validated
            }
        )
        
        manuscripts = reconstruct_result.get('manuscripts', {})
        consolidated_chapters = reconstruct_result.get('consolidated_chapters', [])
        reconstruction_stats = reconstruct_result.get('statistics', {})
        
        reconstruct_time = context.current_utc_datetime
        tiempos['reconstruccion'] = f"{(reconstruct_time - edit_time).total_seconds():.1f}s"
        logging.info(f"✅ Manuscrito reconstruido")
        
        # =================================================================
        # FASE 13: GUARDADO DE OUTPUTS
        # =================================================================
        context.set_custom_status("💾 Fase 13/13: Guardando resultados...")
        
        save_input = {
            'job_id': instance_id,
            'book_name': book_name,
            'bible': bible_validated,
            'manuscripts': manuscripts,
            'consolidated_chapters': consolidated_chapters,
            'original_chapters': fragments,
            'statistics': reconstruction_stats,
            'tiempos': tiempos
        }
        
        save_result = yield context.call_activity('SaveOutputs', save_input)
        
        save_time = context.current_utc_datetime
        tiempos['guardado'] = f"{(save_time - reconstruct_time).total_seconds():.1f}s"
        tiempos['total'] = f"{(save_time - start_time).total_seconds() / 60:.1f} min"
        
        logging.info(f"💾 Outputs guardados: {save_result.get('status')}")
        
        # =================================================================
        # RESULTADO FINAL
        # =================================================================
        context.set_custom_status("✅ Completado - Sylphrena 4.0")
        
        costos = calculate_costs_v4(
            total_words, total_chapters, total_fragments,
            len(layer3_analyses), len(edited_fragments)
        )
        
        logging.info(f"💰 COSTO TOTAL ESTIMADO: ${costos['total']:.2f}")
        
        return {
            'status': 'completed',
            'version': 'v4.0',
            'job_id': instance_id,
            'book_name': book_name,
            'palabras': total_words,
            'total_chapters': total_chapters,
            'total_fragments': total_fragments,
            'chapters_analyzed': len(layer3_analyses),
            'fragments_edited': len(edited_fragments),
            'tiempos': tiempos,
            'costos': costos,
            'outputs': save_result.get('urls', {}),
            'outputs_container': save_result.get('container', 'sylphrena-outputs'),
            'outputs_path': save_result.get('base_path', instance_id),
            'reconstruction_stats': reconstruction_stats
        }
        
    except Exception as e:
        logging.error(f"💥 Error fatal en Orchestrator 4.0: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        
        return {
            'status': 'error',
            'version': 'v4.0',
            'message': str(e)
        }


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def analyze_with_batch_api(context, fragments):
    """Analiza fragmentos usando Gemini Batch API con retry + fallback a Claude."""
    logging.info(f"📦 Modo BATCH API: {len(fragments)} fragmentos")
    
    context.set_custom_status("📤 Enviando a Gemini Batch API...")
    
    batch_info = yield context.call_activity('SubmitBatchAnalysis', fragments)
    
    if batch_info.get('error'):
        raise Exception(f"Error creando batch: {batch_info.get('error')}")
    
    logging.info(f"📦 Batch Job creado: {batch_info.get('batch_job_name', 'N/A')}")
    
    # Esperar resultado del batch
    batch_results = []
    for attempt in range(BATCH_MAX_WAIT_MINUTES):
        context.set_custom_status(f"⏳ Esperando Batch API... ({attempt + 1}/{BATCH_MAX_WAIT_MINUTES} min)")
        
        next_check = context.current_utc_datetime + timedelta(seconds=BATCH_POLL_INTERVAL_SECONDS)
        yield context.create_timer(next_check)
        
        result = yield context.call_activity('PollBatchResult', batch_info)
        
        if isinstance(result, list):
            batch_results = result
            logging.info(f"✅ Batch completado: {len(batch_results)} análisis")
            break
        
        if result.get('status') == 'failed':
            raise Exception(f"Batch falló: {result.get('error')}")
        
        batch_info = result
        logging.info(f"⏳ Batch aún procesando... (intento {attempt + 1})")
    else:
        raise Exception(f"Batch no completó en {BATCH_MAX_WAIT_MINUTES} minutos")
    
    # =========================================================================
    # RETRY + FALLBACK: Procesar fragmentos que fallaron
    # =========================================================================
    MAX_RETRY_FRAGMENTS = 10  # Límite para evitar timeout de Azure
    
    successful_ids = set()
    for analysis in batch_results:
        fid = analysis.get('fragment_id') or analysis.get('chapter_id')
        if fid:
            successful_ids.add(str(fid))
    
    failed_fragments = []
    for frag in fragments:
        frag_id = str(frag.get('id', ''))
        if frag_id not in successful_ids:
            failed_fragments.append(frag)
    
    if not failed_fragments:
        logging.info("✅ Todos los fragmentos procesados exitosamente")
        return batch_results
    
    logging.warning(f"⚠️ {len(failed_fragments)} fragmentos fallaron en batch")
    
    if len(failed_fragments) > MAX_RETRY_FRAGMENTS:
        logging.warning(f"⚠️ Demasiados fallos ({len(failed_fragments)}), limitando a {MAX_RETRY_FRAGMENTS}")
        failed_fragments = failed_fragments[:MAX_RETRY_FRAGMENTS]
    
    # PASO 1: Reintentar con Gemini síncrono
    context.set_custom_status(f"🔄 Reintentando {len(failed_fragments)} fragmentos con Gemini...")
    
    still_failed = []
    for i, frag in enumerate(failed_fragments):
        frag_id = frag.get('id', '?')
        context.set_custom_status(f"🔄 Retry Gemini {i+1}/{len(failed_fragments)}: frag {frag_id}")
        
        try:
            retry_result = yield context.call_activity('AnalyzeChapter', frag)
            
            if retry_result.get('error') or retry_result.get('status') == 'error':
                logging.warning(f"⚠️ Retry Gemini falló para frag {frag_id}")
                still_failed.append(frag)
            else:
                logging.info(f"✅ Retry Gemini exitoso para frag {frag_id}")
                batch_results.append(retry_result)
        except Exception as e:
            logging.warning(f"⚠️ Retry Gemini excepción para frag {frag_id}: {e}")
            still_failed.append(frag)
    
    # PASO 2: Fallback a Claude para los que siguen fallando
    if still_failed:
        context.set_custom_status(f"🔀 Fallback Claude: {len(still_failed)} fragmentos...")
        logging.info(f"🔀 Enviando {len(still_failed)} fragmentos a Claude como fallback")
        
        for i, frag in enumerate(still_failed):
            frag_id = frag.get('id', '?')
            context.set_custom_status(f"🔀 Claude fallback {i+1}/{len(still_failed)}: frag {frag_id}")
            
            try:
                claude_result = yield context.call_activity('AnalyzeChapterWithClaude', frag)
                
                if claude_result and not claude_result.get('error'):
                    logging.info(f"✅ Claude fallback exitoso para frag {frag_id}")
                    batch_results.append(claude_result)
                else:
                    logging.error(f"❌ Claude fallback también falló para frag {frag_id}")
            except Exception as e:
                logging.error(f"❌ Claude fallback excepción para frag {frag_id}: {e}")
    
    logging.info(f"✅ Total análisis finales: {len(batch_results)}/{len(fragments)}")
    return batch_results


def analyze_with_simple_batches(context, fragments):
    """Analiza fragmentos en lotes pequeños (sin Batch API)."""
    total_fragments = len(fragments)
    total_batches = (total_fragments + ANALYSIS_BATCH_SIZE - 1) // ANALYSIS_BATCH_SIZE
    
    logging.info(f"📊 Modo LOTES SIMPLES: {total_batches} lotes de {ANALYSIS_BATCH_SIZE}")
    
    all_analyses = []
    
    for batch_num, i in enumerate(range(0, total_fragments, ANALYSIS_BATCH_SIZE), 1):
        batch = fragments[i:i + ANALYSIS_BATCH_SIZE]
        
        context.set_custom_status(f"🔍 Analizando lote {batch_num}/{total_batches}")
        
        tasks = [context.call_activity('AnalyzeChapter', frag) for frag in batch]
        results = yield context.task_all(tasks)
        
        for result in results:
            if not result.get('error'):
                all_analyses.append(result)
    
    return all_analyses


def edit_with_claude_batch(context, edit_requests, bible, analyses, arc_maps):
    """Edita capítulos usando Claude Batch API."""
    
    # Extraer solo los datos necesarios para el batch
    chapters = [req['chapter'] for req in edit_requests]
    
    logging.info(f"✏️ Enviando {len(chapters)} fragmentos a Claude Batch API")
    
    context.set_custom_status("📤 Enviando a Claude Batch API...")
    
    batch_request = {
        'chapters': chapters,
        'bible': bible,
        'analyses': analyses,
        'arc_maps': arc_maps
    }
    
    batch_info = yield context.call_activity('SubmitClaudeBatch', batch_request)
    
    if batch_info.get('error'):
        raise Exception(f"Error creando Claude batch: {batch_info.get('error')}")
    
    batch_id = batch_info.get('batch_id')
    logging.info(f"📦 Claude Batch creado: {batch_id}")
    
    for attempt in range(CLAUDE_BATCH_MAX_WAIT_MINUTES):
        context.set_custom_status(f"⏳ Esperando Claude Batch... ({attempt + 1}/{CLAUDE_BATCH_MAX_WAIT_MINUTES} min)")
        
        next_check = context.current_utc_datetime + timedelta(seconds=CLAUDE_BATCH_POLL_INTERVAL_SECONDS)
        yield context.create_timer(next_check)
        
        result = yield context.call_activity('PollClaudeBatchResult', batch_info)
        
        if isinstance(result, list):
            logging.info(f"✅ Claude Batch completado: {len(result)} fragmentos editados")
            return result
        
        if result.get('status') == 'error':
            raise Exception(f"Claude Batch falló: {result.get('error')}")
        
        batch_info = result
        counts = result.get('request_counts', {})
        logging.info(f"⏳ Claude procesando... ({counts.get('succeeded', 0)} OK)")
    
    raise Exception(f"Claude Batch no completó en {CLAUDE_BATCH_MAX_WAIT_MINUTES} minutos")


def edit_sequentially(context, edit_requests):
    """Edita capítulos secuencialmente (sin Batch API)."""
    edited = []
    total = len(edit_requests)
    
    for i, req in enumerate(edit_requests, 1):
        context.set_custom_status(f"✏️ Editando {i}/{total}")
        
        result = yield context.call_activity('EditChapter', req)
        edited.append(result)
    
    return edited


def calculate_costs_v4(total_words, total_chapters, total_fragments, 
                       chapters_analyzed, fragments_edited):
    """Calcula costos estimados para Sylphrena 4.0."""
    
    tokens = int(total_words * 1.33)
    
    costs = {
        'segmentacion': round(tokens * 0.10 / 1_000_000, 4),
        'analisis_capa1': round(tokens * 0.05 / 1_000_000, 4),
        'analisis_capa2': round(chapters_analyzed * 5000 * 1.25 / 1_000_000 + 
                                chapters_analyzed * 500 * 5.00 / 1_000_000, 4),
        'analisis_capa3': round(chapters_analyzed * 10000 * 1.25 / 1_000_000 + 
                                chapters_analyzed * 1000 * 5.00 / 1_000_000, 4),
        'holistica': round(tokens * 1.25 / 1_000_000 + 5000 * 5.00 / 1_000_000, 4),
        'sintesis': round(30000 * 1.25 / 1_000_000 + 10000 * 5.00 / 1_000_000, 4),
        'mapas_arco': round(chapters_analyzed * 3000 * 1.25 / 1_000_000 + 
                           chapters_analyzed * 500 * 5.00 / 1_000_000, 4),
        'edicion_input': round(tokens * 2 * 1.50 / 1_000_000, 4),
        'edicion_output': round(tokens * 1.1 * 7.50 / 1_000_000, 4),
        'infraestructura': 0.15
    }
    
    costs['total'] = round(sum(costs.values()), 2)
    return costs


main = df.Orchestrator.create(orchestrator_function)
import azure.functions as func
import azure.durable_functions as df
import logging
import json

def orchestrator_function(context: df.DurableOrchestrationContext):
    try:
        # Recuperar entrada (ruta del archivo o texto raw)
        book_path = context.get_input()
        
        # Timestamp de inicio
        start_time = context.current_utc_datetime
        
        # =================================================================
        # 1. SEGMENTACIÓN (Actividad Única)
        # =================================================================
        context.set_custom_status("Segmentando libro...")
        logging.info("🎬 Iniciando orquestación Sylphrena.")
        
        # Llama a segmentbook
        chapters = yield context.call_activity('SegmentBook', book_path)
        
        seg_time = context.current_utc_datetime
        if not chapters:
            raise ValueError("La segmentación no devolvió capítulos.")

        total_chapters = len(chapters)
        logging.info(f"⏱️ Segmentación lista: {total_chapters} capítulos en {(seg_time - start_time).total_seconds():.1f}s")
        
        # =================================================================
        # 2. ANÁLISIS PARALELO (Fan-Out) -> Gemini Flash
        # =================================================================
        context.set_custom_status(f"Analizando {total_chapters} capítulos en paralelo...")
        
        parallel_tasks = []
        for chapter in chapters:
            task = context.call_activity('AnalyzeChapter', chapter)
            parallel_tasks.append(task)
        
        # Fan-In: Esperar a que todos terminen
        chapter_analyses = yield context.task_all(parallel_tasks)
        
        analysis_time = context.current_utc_datetime
        logging.info(f"⏱️ Análisis completado en {(analysis_time - seg_time).total_seconds():.1f}s")
        
        # =================================================================
        # 2.5 LECTURA HOLÍSTICA (NUEVA) → Gemini Pro lee todo
        # =================================================================
        context.set_custom_status("Realizando lectura holística del libro completo...")

        # Concatenar todo el texto para lectura completa
        full_book_text = "\n\n---\n\n".join([
            f"CAPÍTULO: {ch['title']}\n\n{ch['content']}" 
            for ch in chapters
        ])

        holistic_analysis = yield context.call_activity('HolisticReading', full_book_text)

        holistic_time = context.current_utc_datetime
        logging.info(f"⏱️ Lectura Holística completada en {(holistic_time - analysis_time).total_seconds():.1f}s")

        # =================================================================
        # 3. CREACIÓN DE BIBLIA (Modificada) → Recibe análisis + holístico
        # =================================================================
        context.set_custom_status("Construyendo la Biblia Narrativa...")

        bible_input = {
            "chapter_analyses": chapter_analyses,
            "holistic_analysis": holistic_analysis
        }

        bible = yield context.call_activity('CreateBible', json.dumps(bible_input))
        
        bible_time = context.current_utc_datetime
        logging.info(f"⏱️ Biblia creada en {(bible_time - analysis_time).total_seconds():.1f}s")
        
        # Validación simple de éxito
        bible_status = bible.get('_metadata', {}).get('status', 'unknown')
        if bible_status != 'success':
            logging.warning(f"⚠️ Alerta: La Biblia reporta estado '{bible_status}'")

        # =================================================================
        # 4. EDICIÓN CONTEXTUAL (Fan-Out) -> Claude Sonnet
        # =================================================================
        context.set_custom_status(f"Editando {total_chapters} capítulos con contexto...")
        
        edit_tasks = []
        # Usamos zip para emparejar Capítulo + Su Análisis
        for chapter, analysis in zip(chapters, chapter_analyses):
            
            # Validación defensiva de IDs (Opcional pero recomendada)
            c_id = chapter.get('id')
            a_id = analysis.get('chapter_id')
            if str(c_id) != str(a_id):
                logging.warning(f"⚠️ Mismatch de IDs: Cap {c_id} vs Análisis {a_id}")

            edit_input = {
                'chapter': chapter,
                'bible': bible,     # Pasamos la biblia completa (es pequeña, solo texto JSON)
                'analysis': analysis
            }
            task = context.call_activity('EditChapter', edit_input)
            edit_tasks.append(task)
        
        edited_chapters = yield context.task_all(edit_tasks)
        
        edit_time = context.current_utc_datetime
        total_seconds = (edit_time - start_time).total_seconds()
        
        logging.info(f"⏱️ Edición completada. Tiempo Total: {total_seconds:.1f}s")
        
        # =================================================================
        # 5. RETORNO DE RESULTADOS
        # =================================================================
        # Nota: Azure DF tiene un límite de tamaño de retorno (aprox 4MB).
        # Si el libro es muy grande, aquí deberíamos guardar en Blob Storage 
        # y devolver solo la URL. Para este ejemplo, devolvemos resumen.
        
        # Calculamos costo total estimado sumando metadatos
        total_cost_usd = 0.0
        try:
            # Costo Biblia
            total_cost_usd += bible.get('_metadata', {}).get('estimated_cost_usd', 0)
            # Costo Edición (Sumar todos los capítulos)
            for ch in edited_chapters:
                total_cost_usd += ch.get('metadata', {}).get('cost_usd', 0)
        except:
            pass # Si falla el cálculo de costos, no rompemos el proceso

        result = {
            'status': 'completed',
            'project_name': 'Sylphrena',
            'chapters_processed': len(edited_chapters),
            'total_time_seconds': round(total_seconds, 2),
            'total_estimated_cost_usd': round(total_cost_usd, 4),
            'bible': bible,
            # Devolvemos el contenido editado. 
            # ¡OJO! Si es muy grande, Azure cortará esto.
            'edited_chapters': edited_chapters 
        }
        
        return result
        
    except Exception as e:
        error_msg = f"💥 Error Fatal en Orquestador: {str(e)}"
        logging.error(error_msg)
        # Es importante relanzar o devolver estructura de error para que Azure marque Failed
        context.set_custom_status("Failed")
        raise Exception(error_msg)

main = df.Orchestrator.create(orchestrator_function)
# =============================================================================
# SaveOutputs/__init__.py - SYLPHRENA 5.0 (FIXED)
# =============================================================================
# NUEVO: Guarda carta editorial, notas de margen, y todos los outputs
# =============================================================================

import logging
import json
import os
from datetime import datetime
from azure.storage.blob import BlobServiceClient, ContentSettings
from io import BytesIO
from .structure_changes import structure_changes # Asumimos que esta función existe

logging.basicConfig(level=logging.INFO)


def safe_get(obj, key, default=''):
    """Extrae valor de forma segura."""
    val = obj.get(key, default)
    return val if val else default


def generate_bible_markdown(bible: dict) -> str:
    """Genera versión markdown legible de la Biblia."""
    lines = []
    lines.append("# 📖 BIBLIA NARRATIVA\n")
    lines.append(f"*Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")
    lines.append("---\n")
    
    # 1. IDENTIDAD
    identidad = bible.get('identidad_obra', {})
    if identidad:
        lines.append("## 🎭 IDENTIDAD DE LA OBRA\n")
        lines.append(f"**Género:** {safe_get(identidad, 'genero')}")
        lines.append(f"**Tono:** {safe_get(identidad, 'tono_predominante')}")
        lines.append(f"**Tema Central:** {safe_get(identidad, 'tema_central')}")
        lines.append("")

    # 2. VOZ DEL AUTOR
    voz = bible.get('voz_del_autor', {})
    if voz:
        lines.append("## ✍️ VOZ DEL AUTOR\n")
        lines.append(f"**Estilo:** {safe_get(voz, 'estilo_detectado')}")
        no_corregir = voz.get('NO_CORREGIR', [])
        if no_corregir:
            lines.append("\n**Elementos a preservar:**")
            for item in no_corregir[:10]:
                lines.append(f"- {item}")
        lines.append("")

    # 3. ESTRUCTURA
    estructura = bible.get('estructura_narrativa', {})
    if estructura:
        lines.append("## 📊 ESTRUCTURA NARRATIVA\n")
        modelo = safe_get(estructura, 'modelo_detectado')
        lines.append(f"**Modelo:** {modelo}")
        lines.append("")

    # 4. REPARTO
    reparto = bible.get('reparto_completo', {})
    if isinstance(reparto, dict):
        lines.append("## 👥 REPARTO\n")
        for categoria, personajes in reparto.items():
            if personajes and isinstance(personajes, list):
                lines.append(f"### {categoria.upper()}")
                for p in personajes:
                    nombre = safe_get(p, 'nombre')
                    rol = safe_get(p, 'rol_arquetipo')
                    lines.append(f"- **{nombre}** ({rol})")
                lines.append("")

    # 5. ANÁLISIS PROFUNDOS
    profundos = bible.get('analisis_profundos', {})
    if isinstance(profundos, dict):
        lines.append("## 🧠 ANÁLISIS PROFUNDOS\n")
        temas = profundos.get('temas_detectados', [])
        if temas:
            lines.append(f"**Temas Centrales:** {', '.join(temas)}")
        lines.append("")

    return "\n".join(lines)


def generate_changes_report_v5(chapters: list) -> str:
    """Genera reporte detallado de cambios - SYLPHRENA 5.0."""
    lines = []
    lines.append("# 📝 REPORTE DE CAMBIOS - SYLPHRENA 5.0")
    lines.append("")
    lines.append(f"*Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
    lines.append("")
    
    total_cambios = sum(len(ch.get('cambios_realizados', [])) for ch in chapters)
    total_preservados = sum(len(ch.get('elementos_preservados', [])) for ch in chapters)
    
    # Contar por categoría
    por_categoria = {'prosa': 0, 'narrativa': 0, 'dialogo': 0, 'consistencia': 0, 'otro': 0}
    por_impacto = {'alto': 0, 'medio': 0, 'bajo': 0}
    
    for ch in chapters:
        for cambio in ch.get('cambios_realizados', []):
            cat = cambio.get('categoria', 'otro')
            imp = cambio.get('impacto_narrativo', 'medio')
            if cat in por_categoria:
                por_categoria[cat] += 1
            else:
                por_categoria['otro'] += 1
            if imp in por_impacto:
                por_impacto[imp] += 1
    
    lines.append(f"**Total de cambios:** {total_cambios}")
    lines.append(f"**Elementos preservados:** {total_preservados}")
    lines.append("")
    lines.append("### Por Categoría")
    for cat, count in por_categoria.items():
        if count > 0:
            lines.append(f"- {cat.upper()}: {count}")
    lines.append("")
    lines.append("### Por Impacto")
    for imp, count in por_impacto.items():
        if count > 0:
            emoji = "🔴" if imp == 'alto' else "🟡" if imp == 'medio' else "🟢"
            lines.append(f"- {emoji} {imp.upper()}: {count}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    for ch in chapters:
        ch_id = ch.get('chapter_id', '?')
        title = ch.get('display_title', ch.get('original_title', f'Capítulo {ch_id}'))
        cambios = ch.get('cambios_realizados', [])
        
        lines.append(f"## {title}")
        lines.append("")
        
        if not cambios:
            lines.append("*(Sin cambios en este capítulo)*")
            lines.append("")
            lines.append("---")
            lines.append("")
            continue
        
        lines.append(f"### Cambios ({len(cambios)})")
        lines.append("")
        
        for i, cambio in enumerate(cambios, 1):
            tipo = cambio.get('tipo', 'otro').upper()
            categoria = cambio.get('categoria', '')
            impacto = cambio.get('impacto_narrativo', 'N/A')
            
            imp_emoji = "🔴" if impacto == 'alto' else "🟡" if impacto == 'medio' else "🟢" if impacto == 'bajo' else ""
            
            lines.append(f"**{i}. [{tipo}]** {imp_emoji} ({categoria})")
            
            original = cambio.get('original', '')[:100]
            editado = cambio.get('editado', '')[:100]
            
            lines.append(f"- Original: *\"{original}...\"*")
            lines.append(f"- Editado: *\"{editado}...\"*")
            lines.append(f"- Razón: {cambio.get('justificacion', '')}")
            lines.append("")
        
        lines.append("---")
        lines.append("")
    
    return "\n".join(lines)


# Función principal de la Activity (FIX aplicado aquí)
def main(input_data: any) -> dict:
    """
    Guarda todos los outputs del proceso Sylphrena 5.0.
    """
    
    logging.info(f"SaveOutputs Activity ejecutada. Tipo de input: {type(input_data)}")
    
    # ---------------------------------------------------------------------
    # FIX CRÍTICO: Manejar input que puede ser string o dict
    # ---------------------------------------------------------------------
    payload = input_data
    if isinstance(input_data, str):
        try:
            payload = json.loads(input_data)
        except json.JSONDecodeError as e:
            logging.error(f"[CRITICAL ERROR] No se pudo deserializar el input JSON: {e}")
            raise Exception(f"Input JSON inválido para SaveOutputs: {e}")

    if not isinstance(payload, dict):
        logging.error(f"[CRITICAL ERROR] El input final no es un diccionario. Tipo: {type(payload)}")
        raise Exception("El formato de datos de entrada a SaveOutputs es incorrecto.")
    # ---------------------------------------------------------------------

    try:
        # Extraer datos (ahora es seguro)
        job_id = payload.get('job_id', 'unknown')
        book_name = payload.get('book_name', 'Sin título')
        bible = payload.get('bible', {})
        consolidated_chapters = payload.get('consolidated_chapters', [])
        manuscripts = payload.get('manuscripts', {})
        statistics = payload.get('statistics', {})
        tiempos = payload.get('tiempos', {})
        original_fragments = payload.get('original_fragments', [])
        
        carta_editorial = payload.get('carta_editorial', {})
        carta_markdown = payload.get('carta_markdown', '')
        margin_notes = payload.get('margin_notes', {})
        
        logging.info(f"")
        logging.info(f"{'='*60}")
        logging.info(f">>> SAVE OUTPUTS - SYLPHRENA 5.0")
        logging.info(f"    Job ID: {job_id}")
        logging.info(f"    Libro: {book_name}")
        logging.info(f"{'='*60}")

        # Conexión a Blob Storage
        connection_string = os.environ.get('AzureWebJobsStorage')
        if not connection_string:
            raise ValueError("AzureWebJobsStorage no configurado")
        
        blob_service = BlobServiceClient.from_connection_string(connection_string)
        container_name = "sylphrena-outputs"
        
        try:
            blob_service.create_container(container_name)
        except:
            pass
        
        container_client = blob_service.get_container_client(container_name)
        base_path = job_id
        urls = {}
        
        # Helper para subir blobs
        def upload_blob(path, content, content_type):
            """Sube contenido y retorna la URL (simulación de URL pública)."""
            blob_client = container_client.get_blob_client(path)
            blob_client.upload_blob(
                content if isinstance(content, (str, bytes)) else json.dumps(content, indent=2, ensure_ascii=False), 
                overwrite=True,
                content_settings=ContentSettings(content_type=content_type)
            )
            # Retorna una URL que el Frontend puede usar para saber que el archivo existe
            return f"https://{blob_service.account_name}.blob.core.windows.net/{container_name}/{path}"


        # ─────────────────────────────────────────────────────────────────
        # A. METADATA
        # ─────────────────────────────────────────────────────────────────
        metadata_counts = {
            'original_chapters': len(set(ch.get('chapter_id') for ch in consolidated_chapters)),
            'original_fragments': len(original_fragments) if original_fragments else len(consolidated_chapters)
        }
        
        metadata = {
            'job_id': job_id,
            'book_name': book_name,
            'version': 'Sylphrena 5.0',
            'created_at': datetime.now().isoformat(),
            'status': payload.get('status', 'processing'),
            'counts': metadata_counts
        }
        
        urls['metadata'] = upload_blob(f"{base_path}/metadata.json", metadata, 'application/json')
        logging.info("✅ Metadata guardada")

        # ─────────────────────────────────────────────────────────────────
        # B. BIBLIA (Ahora guardará correctamente porque el input ya es dict)
        # ─────────────────────────────────────────────────────────────────
        if bible:
            urls['biblia_json'] = upload_blob(f"{base_path}/biblia_validada.json", bible, 'application/json')
            
            biblia_md = generate_bible_markdown(bible)
            urls['biblia_narrativa'] = upload_blob(f"{base_path}/biblia_narrativa.md", biblia_md, 'text/markdown')
            logging.info("✅ Biblia guardada")

        # ─────────────────────────────────────────────────────────────────
        # C. CARTA EDITORIAL (NUEVO 5.0)
        # ─────────────────────────────────────────────────────────────────
        if carta_editorial:
            urls['carta_editorial_json'] = upload_blob(f"{base_path}/carta_editorial.json", carta_editorial, 'application/json')
            if carta_markdown:
                urls['carta_editorial_md'] = upload_blob(f"{base_path}/carta_editorial.md", carta_markdown, 'text/markdown')
            logging.info("✅ Carta Editorial guardada")

        # ─────────────────────────────────────────────────────────────────
        # D. NOTAS DE MARGEN (NUEVO 5.0)
        # ─────────────────────────────────────────────────────────────────
        if margin_notes:
            urls['notas_margen'] = upload_blob(f"{base_path}/notas_margen.json", margin_notes, 'application/json')
            logging.info(f"✅ {len(margin_notes.get('all_notes', [])) if margin_notes else 0} notas de margen guardadas")

        # ─────────────────────────────────────────────────────────────────
        # E. CAPÍTULOS CONSOLIDADOS Y CAMBIOS
        # ─────────────────────────────────────────────────────────────────
        if consolidated_chapters:
            urls['capitulos'] = upload_blob(f"{base_path}/capitulos_consolidados.json", consolidated_chapters, 'application/json')

            logging.info("🔄 Estructurando cambios para editor...")
            structured_changes = structure_changes(consolidated_chapters)

            urls['cambios'] = upload_blob(f"{base_path}/cambios_estructurados.json", structured_changes, 'application/json')
            logging.info(f"✅ {structured_changes.get('total_changes', 0)} cambios estructurados")
        
        # ─────────────────────────────────────────────────────────────────
        # F. REPORTE DE CAMBIOS Y RESUMEN FINAL
        # ─────────────────────────────────────────────────────────────────
        # (El resto de tu lógica de reporte y resumen final)
        
        # Si la fase 6 se completó (Biblia), pero no hay más datos,
        # significa que estamos en el guardado intermedio (Fase 6).
        is_final_save = bool(carta_editorial)
        if is_final_save:
            # Reporte de cambios (solo se genera si hay consolidated_chapters)
            if consolidated_chapters:
                cambios_md = generate_changes_report_v5(consolidated_chapters)
                urls['reporte_cambios'] = upload_blob(f"{base_path}/reporte_cambios.md", cambios_md, 'text/markdown')

            # Resumen final
            total_caps_orig = metadata_counts.get('original_chapters', 0)
            resumen = {
                 # ... (Resumen de tu código original)
                 'job_id': job_id,
                 'book_name': book_name,
                 'version': 'Sylphrena 5.0',
                 'fecha_procesamiento': datetime.now().isoformat(),
                 'capitulos_originales': total_caps_orig, 
                 'capitulos_procesados': len(consolidated_chapters),
                 'fragmentos_totales': metadata_counts.get('original_fragments', len(original_fragments) if original_fragments else 0),
                 'total_cambios': structured_changes.get('total_changes', 0),
                 'total_notas_margen': len(margin_notes.get('all_notes', [])) if margin_notes else 0,
                 'estadisticas': statistics,
                 'tiempos': tiempos,
                 'archivos_generados': {
                    'biblia_json': 'biblia_validada.json', 'biblia_md': 'biblia_narrativa.md',
                    'carta_editorial_json': 'carta_editorial.json', 'carta_editorial_md': 'carta_editorial.md',
                    'notas_margen': 'notas_margen.json', 'capitulos': 'capitulos_consolidados.json',
                    'cambios': 'cambios_estructurados.json', 'reporte_cambios': 'reporte_cambios.md'
                 },
                 'urls': urls
             }
            urls['resumen'] = upload_blob(f"{base_path}/resumen_ejecutivo.json", resumen, 'application/json')
            logging.info("✅ Resumen ejecutivo guardado")

            # Capítulos individuales (solo en la fase final)
            chapters_folder = f"{base_path}/capitulos_individuales"
            for ch in consolidated_chapters:
                 ch_id = ch.get('chapter_id', '?')
                 title = ch.get('display_title', f'Capitulo_{ch_id}')
                 safe_title = title.replace('/', '_').replace('\\', '_')[:50]
                 upload_blob(f"{chapters_folder}/{safe_title}.json", ch, 'application/json')
            logging.info(f"✅ {len(consolidated_chapters)} capítulos individuales guardados")

        # ─────────────────────────────────────────────────────────────────
        # RESUMEN FINAL DE RETORNO
        # ─────────────────────────────────────────────────────────────────
        logging.info("="*60)
        logging.info("✅ SAVE OUTPUTS completado.")

        return {
            'status': 'success',
            'job_id': job_id,
            'urls': urls,
            'files_saved': len(urls)
        }

    except Exception as e:
        logging.error(f"❌ Error en SaveOutputs: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        # Devolvemos el error al Orchestrator para que pueda registrar la falla
        return {
            'status': 'error',
            'error': str(e)
        }
# =============================================================================
# SaveOutputs/__init__.py - SYLPHRENA 5.0
# =============================================================================
# NUEVO: Guarda carta editorial, notas de margen, y todos los outputs
# =============================================================================

import logging
import json
import os
from datetime import datetime
from azure.storage.blob import BlobServiceClient, ContentSettings
from io import BytesIO
from .structure_changes import structure_changes

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


def main(payload: dict) -> dict:
    """
    Guarda todos los outputs del proceso Sylphrena 5.0.
    """
    
    try:
        job_id = payload.get('job_id', 'unknown')
        book_name = payload.get('book_name', 'Sin título')
        bible = payload.get('bible', {})
        consolidated_chapters = payload.get('consolidated_chapters', [])
        manuscripts = payload.get('manuscripts', {})
        statistics = payload.get('statistics', {})
        tiempos = payload.get('tiempos', {})
        original_fragments = payload.get('original_fragments', [])
        
        # NUEVO 5.0
        carta_editorial = payload.get('carta_editorial', {})
        carta_markdown = payload.get('carta_markdown', '')
        margin_notes = payload.get('margin_notes', {})
        
        logging.info(f"")
        logging.info(f"{'='*60}")
        logging.info(f">>> SAVE OUTPUTS - SYLPHRENA 5.0")
        logging.info(f"    Job ID: {job_id}")
        logging.info(f"    Libro: {book_name}")
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
            'status': 'processing' if not carta_editorial else 'completed',
            'counts': metadata_counts
        }
        
        metadata_path = f"{base_path}/metadata.json"
        blob_client = container_client.get_blob_client(metadata_path)
        blob_client.upload_blob(
            json.dumps(metadata, indent=2, ensure_ascii=False), 
            overwrite=True,
            content_settings=ContentSettings(content_type='application/json')
        )
        urls['metadata'] = blob_client.url
        logging.info("✅ Metadata guardada")

        # ─────────────────────────────────────────────────────────────────
        # B. BIBLIA
        # ─────────────────────────────────────────────────────────────────
        # JSON
        bible_json_path = f"{base_path}/biblia_validada.json"
        blob_client = container_client.get_blob_client(bible_json_path)
        blob_client.upload_blob(
            json.dumps(bible, indent=2, ensure_ascii=False), 
            overwrite=True,
            content_settings=ContentSettings(content_type='application/json')
        )
        urls['biblia_json'] = blob_client.url

        # Markdown
        biblia_md = generate_bible_markdown(bible)
        biblia_md_path = f"{base_path}/biblia_narrativa.md"
        blob_client = container_client.get_blob_client(biblia_md_path)
        blob_client.upload_blob(
            biblia_md, 
            overwrite=True,
            content_settings=ContentSettings(content_type='text/markdown')
        )
        urls['biblia_narrativa'] = blob_client.url
        logging.info("✅ Biblia guardada")

        # ─────────────────────────────────────────────────────────────────
        # C. CARTA EDITORIAL (NUEVO 5.0)
        # ─────────────────────────────────────────────────────────────────
        if carta_editorial:
            # JSON
            carta_json_path = f"{base_path}/carta_editorial.json"
            blob_client = container_client.get_blob_client(carta_json_path)
            blob_client.upload_blob(
                json.dumps(carta_editorial, indent=2, ensure_ascii=False),
                overwrite=True,
                content_settings=ContentSettings(content_type='application/json')
            )
            urls['carta_editorial_json'] = blob_client.url
            
            # Markdown
            if carta_markdown:
                carta_md_path = f"{base_path}/carta_editorial.md"
                blob_client = container_client.get_blob_client(carta_md_path)
                blob_client.upload_blob(
                    carta_markdown,
                    overwrite=True,
                    content_settings=ContentSettings(content_type='text/markdown')
                )
                urls['carta_editorial_md'] = blob_client.url
            
            logging.info("✅ Carta Editorial guardada")

        # ─────────────────────────────────────────────────────────────────
        # D. NOTAS DE MARGEN (NUEVO 5.0)
        # ─────────────────────────────────────────────────────────────────
        if margin_notes:
            notas_path = f"{base_path}/notas_margen.json"
            blob_client = container_client.get_blob_client(notas_path)
            blob_client.upload_blob(
                json.dumps(margin_notes, indent=2, ensure_ascii=False),
                overwrite=True,
                content_settings=ContentSettings(content_type='application/json')
            )
            urls['notas_margen'] = blob_client.url
            logging.info(f"✅ {len(margin_notes.get('all_notes', []))} notas de margen guardadas")

        # ─────────────────────────────────────────────────────────────────
        # E. CAPÍTULOS CONSOLIDADOS Y CAMBIOS
        # ─────────────────────────────────────────────────────────────────
        # Capítulos
        chapters_path = f"{base_path}/capitulos_consolidados.json"
        blob_client = container_client.get_blob_client(chapters_path)
        blob_client.upload_blob(
            json.dumps(consolidated_chapters, indent=2, ensure_ascii=False),
            overwrite=True,
            content_settings=ContentSettings(content_type='application/json')
        )
        urls['capitulos'] = blob_client.url

        # Cambios estructurados
        logging.info("🔄 Estructurando cambios para editor...")
        structured_changes = structure_changes(consolidated_chapters)

        changes_path = f"{base_path}/cambios_estructurados.json"
        blob_client = container_client.get_blob_client(changes_path)
        blob_client.upload_blob(
            json.dumps(structured_changes, indent=2, ensure_ascii=False),
            overwrite=True,
            content_settings=ContentSettings(content_type='application/json')
        )
        urls['cambios'] = blob_client.url
        logging.info(f"✅ {structured_changes['total_changes']} cambios estructurados")

        # ─────────────────────────────────────────────────────────────────
        # F. REPORTE DE CAMBIOS
        # ─────────────────────────────────────────────────────────────────
        cambios_md = generate_changes_report_v5(consolidated_chapters)
        cambios_path = f"{base_path}/reporte_cambios.md"
        blob_client = container_client.get_blob_client(cambios_path)
        blob_client.upload_blob(
            cambios_md, 
            overwrite=True,
            content_settings=ContentSettings(content_type='text/markdown')
        )
        urls['reporte_cambios'] = blob_client.url

        # ─────────────────────────────────────────────────────────────────
        # G. RESUMEN EJECUTIVO
        # ─────────────────────────────────────────────────────────────────
        total_caps_orig = metadata_counts.get('original_chapters', 0)
        if total_caps_orig == 0 and original_fragments:
             total_caps_orig = len(original_fragments)

        resumen = {
            'job_id': job_id,
            'book_name': book_name,
            'version': 'Sylphrena 5.0',
            'fecha_procesamiento': datetime.now().isoformat(),
            'capitulos_originales': total_caps_orig, 
            'capitulos_procesados': len(consolidated_chapters),
            'fragmentos_totales': metadata_counts.get('original_fragments', len(original_fragments) if original_fragments else 0),
            'total_cambios': structured_changes['total_changes'],
            'total_notas_margen': len(margin_notes.get('all_notes', [])) if margin_notes else 0,
            'estadisticas': statistics,
            'tiempos': tiempos,
            'archivos_generados': {
                'biblia_json': 'biblia_validada.json',
                'biblia_md': 'biblia_narrativa.md',
                'carta_editorial_json': 'carta_editorial.json',
                'carta_editorial_md': 'carta_editorial.md',
                'notas_margen': 'notas_margen.json',
                'capitulos': 'capitulos_consolidados.json',
                'cambios': 'cambios_estructurados.json',
                'reporte_cambios': 'reporte_cambios.md'
            },
            'urls': urls
        }
        
        resumen_path = f"{base_path}/resumen_ejecutivo.json"
        blob_client = container_client.get_blob_client(resumen_path)
        blob_client.upload_blob(
            json.dumps(resumen, indent=2, ensure_ascii=False), 
            overwrite=True,
            content_settings=ContentSettings(content_type='application/json')
        )
        urls['resumen'] = blob_client.url
        logging.info("✅ Resumen ejecutivo guardado")

        # ─────────────────────────────────────────────────────────────────
        # H. CAPÍTULOS INDIVIDUALES
        # ─────────────────────────────────────────────────────────────────
        chapters_folder = f"{base_path}/capitulos_individuales"
        for ch in consolidated_chapters:
            ch_id = ch.get('chapter_id', '?')
            title = ch.get('display_title', f'Capitulo_{ch_id}')
            safe_title = title.replace('/', '_').replace('\\', '_')[:50]
            
            ch_path = f"{chapters_folder}/{safe_title}.json"
            blob_client = container_client.get_blob_client(ch_path)
            blob_client.upload_blob(
                json.dumps(ch, indent=2, ensure_ascii=False),
                overwrite=True,
                content_settings=ContentSettings(content_type='application/json')
            )
        
        logging.info(f"✅ {len(consolidated_chapters)} capítulos individuales guardados")

        # ─────────────────────────────────────────────────────────────────
        # RESUMEN FINAL
        # ─────────────────────────────────────────────────────────────────
        logging.info("")
        logging.info("="*60)
        logging.info("✅ SYLPHRENA 5.0 - TODOS LOS OUTPUTS GUARDADOS")
        logging.info(f"   Job ID: {job_id}")
        logging.info(f"   Archivos principales: {len(urls)}")
        logging.info(f"   Capítulos individuales: {len(consolidated_chapters)}")
        if carta_editorial:
            logging.info(f"   Carta Editorial: ✅")
        if margin_notes:
            logging.info(f"   Notas de margen: {len(margin_notes.get('all_notes', []))}")
        logging.info("="*60)
        
        return {
            'status': 'success',
            'job_id': job_id,
            'urls': urls,
            'files_saved': len(urls) + len(consolidated_chapters)
        }

    except Exception as e:
        logging.error(f"❌ Error en SaveOutputs: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return {
            'status': 'error',
            'error': str(e)
        }

# =============================================================================
# SaveOutputs/__init__.py - SYLPHRENA 4.0 - CON DOCX
# =============================================================================
# NUEVO: Genera manuscrito DOCX profesional con Track Changes
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


def generate_changes_report_v4(chapters: list) -> str:
    """Genera reporte detallado de cambios."""
    lines = []
    lines.append("# 📝 REPORTE DE CAMBIOS - SYLPHRENA 4.0")
    lines.append("")
    lines.append(f"*Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
    lines.append("")
    
    total_cambios = sum(len(ch.get('cambios_realizados', [])) for ch in chapters)
    total_preservados = sum(len(ch.get('elementos_preservados', [])) for ch in chapters)
    
    lines.append(f"**Total de cambios:** {total_cambios}")
    lines.append(f"**Elementos preservados intencionalmente:** {total_preservados}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    for chapter in chapters:
        ch_id = chapter.get('chapter_id', '?')
        titulo = chapter.get('display_title', f'Capítulo {ch_id}')
        cambios = chapter.get('cambios_realizados', [])
        preservados = chapter.get('elementos_preservados', [])
        notas = chapter.get('notas_editor', '')
        
        if not cambios and not preservados and not notas:
            continue
        
        lines.append(f"## {titulo}")
        lines.append("")
        
        if cambios:
            lines.append(f"### Cambios ({len(cambios)})")
            lines.append("")
            for i, c in enumerate(cambios, 1):
                tipo = c.get('tipo', 'otro')
                original = c.get('original', '')
                editado = c.get('editado', '')
                justificacion = c.get('justificacion', '')
                impacto = c.get('impacto_narrativo', 'N/A')
                
                lines.append(f"**{i}. [{tipo.upper()}]** (Impacto: {impacto})")
                lines.append(f"- Original: *\"{original[:80]}...\"*")
                lines.append(f"- Editado: *\"{editado[:80]}...\"*")
                lines.append(f"- Razón: {justificacion}")
                lines.append("")
        
        if notas:
            lines.append(f"### Notas del Editor")
            lines.append("")
            lines.append(f"> {notas}")
            lines.append("")
        
        lines.append("---")
        lines.append("")
    
    return "\n".join(lines)


def main(save_input) -> dict:
    """
    Guarda todos los outputs incluyendo DOCX profesional.
    """
    try:
        # --- BLOQUE DE SEGURIDAD ---
        if isinstance(save_input, str):
            try:
                input_data = json.loads(save_input)
            except:
                input_data = {}
        else:
            input_data = save_input
            
        save_input = input_data
        # ---------------------------

        # Extraer inputs
        job_id = save_input.get('job_id', datetime.now().strftime('%Y%m%d_%H%M%S'))
        book_name = save_input.get('book_name', 'libro')
        bible = save_input.get('bible', {})
        manuscripts = save_input.get('manuscripts', {})
        consolidated_chapters = save_input.get('consolidated_chapters', [])
        
        metadata_counts = save_input.get('metadata_counts', {})
        original_fragments = save_input.get('original_fragments', save_input.get('original_chapters', []))
        statistics = save_input.get('statistics', {})
        tiempos = save_input.get('tiempos', {})
        
        logging.info(f"💾 Guardando outputs para job: {job_id}")
        
        # ─────────────────────────────────────────────────────────────────
        # A. CONECTAR A BLOB STORAGE
        # ─────────────────────────────────────────────────────────────────
        connection_string = os.environ.get('AzureWebJobsStorage')
        if not connection_string:
            return {"status": "error", "error": "AzureWebJobsStorage no configurada"}
        
        blob_service = BlobServiceClient.from_connection_string(connection_string)
        container_name = "sylphrena-outputs"
        
        try:
            blob_service.create_container(container_name)
        except Exception:
            pass 
        
        container_client = blob_service.get_container_client(container_name)
        base_path = f"{job_id}"
        urls = {}
        
        # ─────────────────────────────────────────────────────────────────
        # B. GUARDAR BIBLIA VALIDADA
        # ─────────────────────────────────────────────────────────────────
        biblia_json_path = f"{base_path}/biblia_validada.json"
        blob_client = container_client.get_blob_client(biblia_json_path)
        blob_client.upload_blob(
            json.dumps(bible, indent=2, ensure_ascii=False), 
            overwrite=True,
            content_settings=ContentSettings(content_type='application/json')
        )
        urls['biblia_json'] = blob_client.url

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
        # C. GUARDAR MANUSCRITOS (MARKDOWN Y HTML)
        # ─────────────────────────────────────────────────────────────────
        # Frontend renderizará desde JSON - solo guardamos datos estructurados
        logging.info("📦 Guardando solo JSON estructurado (frontend renderiza)")
        # Guardar capítulos consolidados completos
        chapters_path = f"{base_path}/capitulos_consolidados.json"
        blob_client = container_client.get_blob_client(chapters_path)
        blob_client.upload_blob(
            json.dumps(consolidated_chapters, indent=2, ensure_ascii=False),
            overwrite=True,
            content_settings=ContentSettings(content_type='application/json')
        )
        urls['capitulos'] = blob_client.url

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
        # C2. NUEVO - GUARDAR MANUSCRITO DOCX PROFESIONAL
        # ─────────────────────────────────────────────────────────────────
        logging.info("ℹ️ DOCX generation moved to frontend")


        # ─────────────────────────────────────────────────────────────────
        # D. GUARDAR REPORTE DE CAMBIOS
        # ─────────────────────────────────────────────────────────────────
        cambios_md = generate_changes_report_v4(consolidated_chapters)
        cambios_path = f"{base_path}/reporte_cambios.md"
        blob_client = container_client.get_blob_client(cambios_path)
        blob_client.upload_blob(
            cambios_md, 
            overwrite=True,
            content_settings=ContentSettings(content_type='text/markdown')
        )
        urls['reporte_cambios'] = blob_client.url

        # ─────────────────────────────────────────────────────────────────
        # E. GUARDAR RESUMEN EJECUTIVO
        # ─────────────────────────────────────────────────────────────────
        total_caps_orig = metadata_counts.get('original_chapters', 0)
        if total_caps_orig == 0 and original_fragments:
             total_caps_orig = len(original_fragments)

        resumen = {
            'job_id': job_id,
            'book_name': book_name,
            'version': 'Sylphrena 4.0',
            'fecha_procesamiento': datetime.now().isoformat(),
            'capitulos_originales': total_caps_orig, 
            'capitulos_procesados': len(consolidated_chapters),
            'fragmentos_totales': metadata_counts.get('original_fragments', len(original_fragments)),
            'estadisticas': statistics,
            'tiempos': tiempos,
            'archivos_generados': {
                'biblia_json': 'biblia_validada.json',
                'biblia_md': 'biblia_narrativa.md',
                'manuscrito_limpio': 'manuscrito_editado.md',
                'manuscrito_anotado': 'manuscrito_anotado.md',
                'manuscrito_docx': 'manuscrito_editado.docx',  # NUEVO
                'control_cambios': 'control_cambios.html',
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
        # F. GUARDAR CAPÍTULOS INDIVIDUALES
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
        logging.info("✅ TODOS LOS OUTPUTS GUARDADOS")
        logging.info(f"   Job ID: {job_id}")
        logging.info(f"   Archivos: {len(urls)} principales")
        logging.info(f"   Capítulos individuales: {len(consolidated_chapters)}")
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
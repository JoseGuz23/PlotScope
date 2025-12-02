# =============================================================================
# SaveOutputs/__init__.py - SYLPHRENA 4.0
# =============================================================================
# CAMBIOS DESDE 3.1:
#   - Guarda 3 versiones del manuscrito (limpia, enriquecida, comparativa)
#   - Maneja Biblia Validada con análisis multi-capa
#   - Genera reporte de cambios detallado
#   - Estructura de archivos organizada para fácil descarga
# =============================================================================

import logging
import json
import os
from datetime import datetime
from azure.storage.blob import BlobServiceClient, ContentSettings

logging.basicConfig(level=logging.INFO)


def main(save_input) -> dict:
    """
    Guarda todos los outputs.
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
            
        save_input = input_data # Alias
        # ---------------------------

        # Extraer inputs
        job_id = save_input.get('job_id', datetime.now().strftime('%Y%m%d_%H%M%S'))
        book_name = save_input.get('book_name', 'libro')
        bible = save_input.get('bible', {})
        manuscripts = save_input.get('manuscripts', {})
        consolidated_chapters = save_input.get('consolidated_chapters', [])
        
        # [FIX] Recibir contadores explícitos del Orchestrator
        metadata_counts = save_input.get('metadata_counts', {})
        
        # Fallback para compatibilidad hacia atrás si metadata_counts no existe
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
        
        # Crear container si no existe
        try:
            blob_service.create_container(container_name)
        except Exception:
            pass 
        
        container_client = blob_service.get_container_client(container_name)
        base_path = f"{job_id}"
        urls = {}
        
        # ─────────────────────────────────────────────────────────────────
        # B. GUARDAR BIBLIA VALIDADA (JSON y MD)
        # ─────────────────────────────────────────────────────────────────
        # B1. JSON
        biblia_json_path = f"{base_path}/biblia_validada.json"
        blob_client = container_client.get_blob_client(biblia_json_path)
        blob_client.upload_blob(
            json.dumps(bible, indent=2, ensure_ascii=False), 
            overwrite=True,
            content_settings=ContentSettings(content_type='application/json')
        )
        urls['biblia_json'] = blob_client.url

        # B2. MD
        biblia_md_content = bible_to_markdown_v4(bible)
        biblia_md_path = f"{base_path}/biblia_validada.md"
        blob_client = container_client.get_blob_client(biblia_md_path)
        blob_client.upload_blob(
            biblia_md_content, 
            overwrite=True,
            content_settings=ContentSettings(content_type='text/markdown')
        )
        urls['biblia_md'] = blob_client.url
        
        logging.info("✅ Biblia guardada")

        # ─────────────────────────────────────────────────────────────────
        # C. GUARDAR MANUSCRITOS
        # ─────────────────────────────────────────────────────────────────
        # C1. Limpio
        if manuscripts.get('clean_md'):
            clean_path = f"{base_path}/manuscrito_editado.md"
            blob_client = container_client.get_blob_client(clean_path)
            blob_client.upload_blob(
                manuscripts['clean_md'], 
                overwrite=True,
                content_settings=ContentSettings(content_type='text/markdown')
            )
            urls['manuscrito_limpio'] = blob_client.url

        # C2. Enriquecido
        if manuscripts.get('enriched_md'):
            enriched_path = f"{base_path}/manuscrito_anotado.md"
            blob_client = container_client.get_blob_client(enriched_path)
            blob_client.upload_blob(
                manuscripts['enriched_md'], 
                overwrite=True,
                content_settings=ContentSettings(content_type='text/markdown')
            )
            urls['manuscrito_anotado'] = blob_client.url

        # C3. Comparativo
        if manuscripts.get('comparative_html'):
            comparative_path = f"{base_path}/control_cambios.html"
            blob_client = container_client.get_blob_client(comparative_path)
            blob_client.upload_blob(
                manuscripts['comparative_html'], 
                overwrite=True,
                content_settings=ContentSettings(content_type='text/html')
            )
            urls['control_cambios'] = blob_client.url
            
        logging.info("✅ Manuscritos guardados")

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
        # E. GUARDAR RESUMEN EJECUTIVO (FIXED)
        # ─────────────────────────────────────────────────────────────────
        
        # [FIX] Usar lógica prioritaria: Metadata explícita > Cálculo sobre lista > 0
        total_caps_orig = metadata_counts.get('original_chapters', 0)
        if total_caps_orig == 0 and original_fragments:
             # Fallback: si no hay metadata, usamos len de fragmentos (aunque sea inexacto es mejor que 0)
             total_caps_orig = len(original_fragments)

        resumen = {
            'job_id': job_id,
            'book_name': book_name,
            'version': 'Sylphrena 4.0',
            'fecha_procesamiento': datetime.now().isoformat(),
            # Aquí está el arreglo visual para el reporte:
            'capitulos_originales': total_caps_orig, 
            'capitulos_procesados': len(consolidated_chapters),
            'fragmentos_totales': metadata_counts.get('original_fragments', len(original_fragments)),
            'estadisticas': statistics,
            'tiempos': tiempos,
            'archivos_generados': {
                'biblia_json': 'biblia_validada.json',
                'biblia_md': 'biblia_validada.md',
                'manuscrito_limpio': 'manuscrito_editado.md',
                'manuscrito_anotado': 'manuscrito_anotado.md',
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
        chapters_folder = f"{base_path}/capitulos"
        for chapter in consolidated_chapters:
            ch_id = chapter.get('chapter_id', 'unknown')
            ch_title = chapter.get('display_title', f'Capitulo_{ch_id}')
            
            # Sanitizar título
            safe_title = "".join(c for c in ch_title if c.isalnum() or c in ' _-').strip()
            
            try:
                ch_num = int(ch_id)
                file_name = f"{ch_num:03d}_{safe_title}.md"
            except ValueError:
                file_name = f"{ch_id}_{safe_title}.md"
            
            ch_path = f"{chapters_folder}/{file_name}"
            
            ch_content = f"# {ch_title}\n\n"
            ch_content += chapter.get('contenido_editado', '')
            
            blob_client = container_client.get_blob_client(ch_path)
            blob_client.upload_blob(
                ch_content, 
                overwrite=True,
                content_settings=ContentSettings(content_type='text/markdown')
            )
        
        logging.info(f"💾 Todos los archivos guardados en: {container_name}/{base_path}/")
        
        return {
            'status': 'success',
            'job_id': job_id,
            'container': container_name,
            'base_path': base_path,
            'urls': urls,
            'files_count': len(urls) + len(consolidated_chapters)
        }
        
    except Exception as e:
        logging.error(f"❌ Error guardando outputs: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return {"status": "error", "error": str(e)}

def bible_to_markdown_v4(bible: dict) -> str:
    """Convierte la Biblia a MD con validación de tipos segura."""
    if not isinstance(bible, dict):
        return "⚠️ Error: La estructura de la Biblia no es válida o está incompleta."

    lines = ["# 📚 BIBLIA NARRATIVA VALIDADA", ""]
    
    # Helper seguro
    def safe_get(obj, key, default="-"):
        val = obj.get(key)
        return val if val else default

    # 1. IDENTIDAD
    identidad = bible.get('identidad_obra', {})
    if isinstance(identidad, dict):
        lines.append("## 🎭 IDENTIDAD DE LA OBRA\n")
        lines.append(f"- **Género:** {safe_get(identidad, 'genero')}")
        lines.append(f"- **Tono:** {safe_get(identidad, 'tono_predominante')}")
        lines.append("")
    
    # 2. CAUSALIDAD (El punto donde tronó antes)
    causalidad = bible.get('analisis_causalidad')
    if isinstance(causalidad, dict):
        lines.append("## 🔗 ANÁLISIS DE CAUSALIDAD\n")
        problemas = causalidad.get('problemas_detectados', {})
        
        # Caso A: Es un diccionario con categorías (lo más probable)
        if isinstance(problemas, dict):
            for categoria, items in problemas.items():
                if items and isinstance(items, list):
                    cat_title = categoria.replace('_', ' ').upper()
                    lines.append(f"### {cat_title}")
                    for prob in items:
                        desc = prob.get('descripcion', 'Sin descripción')
                        lines.append(f"- ⚠️ {desc}")
                    lines.append("")
        
        # Caso B: Es una lista directa (legacy)
        elif isinstance(problemas, list):
            for prob in problemas:
                 lines.append(f"- ⚠️ {prob.get('descripcion', 'Sin descripción')}")
            lines.append("")
            
    elif causalidad:
        # Fallback de error
        lines.append(f"## 🔗 ANÁLISIS DE CAUSALIDAD\n⚠️ Estado: {str(causalidad)}\n")

    # 3. ARCO NARRATIVO
    arco = bible.get('arco_narrativo', {})
    if isinstance(arco, dict):
        lines.append("## 📈 ARCO NARRATIVO\n")
        lines.append(f"- **Estructura:** {safe_get(arco, 'estructura_detectada')}")
        puntos = arco.get('puntos_clave', {})
        if puntos:
            lines.append("\n### Puntos Clave:")
            for key, val in puntos.items():
                if isinstance(val, dict):
                    desc = val.get('descripcion', '-')
                    cap = val.get('capitulo', '-')
                    lines.append(f"- **{key.replace('_', ' ').title()}** (Cap {cap}): {desc}")
        lines.append("")

    # 4. REPARTO (PERSONAJES)
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
        # Temas
        temas = profundos.get('temas_detectados', [])
        if temas:
            lines.append(f"**Temas Centrales:** {', '.join(temas)}")
        lines.append("")

    return "\n".join(lines)
    


def generate_changes_report_v4(chapters: list) -> str:
    """
    Genera un reporte detallado de todos los cambios realizados.
    """
    lines = []
    lines.append("# 📝 REPORTE DE CAMBIOS - SYLPHRENA 4.0")
    lines.append("")
    lines.append(f"*Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
    lines.append("")
    
    # Estadísticas globales
    total_cambios = sum(len(ch.get('cambios_realizados', [])) for ch in chapters)
    total_preservados = sum(len(ch.get('elementos_preservados', [])) for ch in chapters)
    
    lines.append(f"**Total de cambios:** {total_cambios}")
    lines.append(f"**Elementos preservados intencionalmente:** {total_preservados}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Desglose por capítulo
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
        
        # Contexto aplicado
        contexto = chapter.get('contexto_aplicado', {})
        if contexto:
            funcion = contexto.get('funcion_dramatica', 'N/A')
            posicion = contexto.get('posicion_estructura', 'N/A')
            lines.append(f"*Función narrativa: {funcion} | Posición: {posicion}*")
            lines.append("")
        
        # Cambios realizados
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
                lines.append(f"- Original: *\"{original}...\"*")
                lines.append(f"- Editado: *\"{editado}...\"*")
                lines.append(f"- Razón: {justificacion}")
                lines.append("")
        
        # Elementos preservados
        if preservados:
            lines.append(f"### Elementos Preservados ({len(preservados)})")
            lines.append("")
            for elem in preservados:
                lines.append(f"- {elem}")
            lines.append("")
        
        # Notas del editor
        if notas:
            lines.append(f"### Notas del Editor")
            lines.append("")
            lines.append(f"> {notas}")
            lines.append("")
        
        lines.append("---")
        lines.append("")
    
    return "\n".join(lines)

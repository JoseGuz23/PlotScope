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


def main(save_input: dict) -> dict:
    """
    Guarda todos los outputs de Sylphrena 4.0 en Blob Storage.
    
    Input esperado:
    {
        'job_id': str,
        'book_name': str,
        'bible': dict,                      # Biblia Validada
        'manuscripts': {                    # Output de ReconstructManuscript
            'clean_md': str,
            'enriched_md': str,
            'comparative_html': str
        },
        'consolidated_chapters': [...],     # Capítulos consolidados
        'original_chapters': [...],         # Capítulos originales
        'statistics': {...},                # Estadísticas de procesamiento
        'tiempos': {...}                    # Tiempos por fase
    }
    """
    try:
        # Extraer inputs
        job_id = save_input.get('job_id', datetime.now().strftime('%Y%m%d_%H%M%S'))
        book_name = save_input.get('book_name', 'libro')
        bible = save_input.get('bible', {})
        manuscripts = save_input.get('manuscripts', {})
        consolidated_chapters = save_input.get('consolidated_chapters', [])
        original_chapters = save_input.get('original_chapters', [])
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
            logging.info(f"📦 Container '{container_name}' creado")
        except Exception:
            pass  # Ya existe
        
        container_client = blob_service.get_container_client(container_name)
        
        # Estructura de carpetas: job_id/
        base_path = f"{job_id}"
        urls = {}
        
        # ─────────────────────────────────────────────────────────────────
        # B. GUARDAR BIBLIA VALIDADA
        # ─────────────────────────────────────────────────────────────────
        
        # B1. Biblia JSON (datos crudos)
        biblia_json_path = f"{base_path}/biblia_validada.json"
        biblia_json_content = json.dumps(bible, indent=2, ensure_ascii=False)
        
        blob_client = container_client.get_blob_client(biblia_json_path)
        blob_client.upload_blob(
            biblia_json_content, 
            overwrite=True,
            content_settings=ContentSettings(content_type='application/json')
        )
        urls['biblia_json'] = blob_client.url
        logging.info(f"✅ Guardado: {biblia_json_path}")
        
        # B2. Biblia Markdown (legible)
        biblia_md_content = bible_to_markdown_v4(bible)
        biblia_md_path = f"{base_path}/biblia_validada.md"
        
        blob_client = container_client.get_blob_client(biblia_md_path)
        blob_client.upload_blob(
            biblia_md_content, 
            overwrite=True,
            content_settings=ContentSettings(content_type='text/markdown')
        )
        urls['biblia_md'] = blob_client.url
        logging.info(f"✅ Guardado: {biblia_md_path}")
        
        # ─────────────────────────────────────────────────────────────────
        # C. GUARDAR MANUSCRITOS (3 versiones)
        # ─────────────────────────────────────────────────────────────────
        
        # C1. Manuscrito Limpio (Markdown)
        if manuscripts.get('clean_md'):
            clean_path = f"{base_path}/manuscrito_editado.md"
            blob_client = container_client.get_blob_client(clean_path)
            blob_client.upload_blob(
                manuscripts['clean_md'], 
                overwrite=True,
                content_settings=ContentSettings(content_type='text/markdown')
            )
            urls['manuscrito_limpio'] = blob_client.url
            logging.info(f"✅ Guardado: {clean_path}")
        
        # C2. Manuscrito Enriquecido (Markdown con anotaciones)
        if manuscripts.get('enriched_md'):
            enriched_path = f"{base_path}/manuscrito_anotado.md"
            blob_client = container_client.get_blob_client(enriched_path)
            blob_client.upload_blob(
                manuscripts['enriched_md'], 
                overwrite=True,
                content_settings=ContentSettings(content_type='text/markdown')
            )
            urls['manuscrito_anotado'] = blob_client.url
            logging.info(f"✅ Guardado: {enriched_path}")
        
        # C3. Manuscrito Comparativo (HTML con control de cambios)
        if manuscripts.get('comparative_html'):
            comparative_path = f"{base_path}/control_cambios.html"
            blob_client = container_client.get_blob_client(comparative_path)
            blob_client.upload_blob(
                manuscripts['comparative_html'], 
                overwrite=True,
                content_settings=ContentSettings(content_type='text/html')
            )
            urls['control_cambios'] = blob_client.url
            logging.info(f"✅ Guardado: {comparative_path}")
        
        # ─────────────────────────────────────────────────────────────────
        # D. GUARDAR REPORTE DE CAMBIOS DETALLADO
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
        logging.info(f"✅ Guardado: {cambios_path}")
        
        # ─────────────────────────────────────────────────────────────────
        # E. GUARDAR RESUMEN EJECUTIVO (JSON)
        # ─────────────────────────────────────────────────────────────────
        
        resumen = {
            'job_id': job_id,
            'book_name': book_name,
            'version': 'Sylphrena 4.0',
            'fecha_procesamiento': datetime.now().isoformat(),
            'capitulos_originales': len(original_chapters),
            'capitulos_procesados': len(consolidated_chapters),
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
        logging.info(f"✅ Guardado: {resumen_path}")
        
        # ─────────────────────────────────────────────────────────────────
        # F. GUARDAR CAPÍTULOS INDIVIDUALES (para referencia)
        # ─────────────────────────────────────────────────────────────────
        
        chapters_folder = f"{base_path}/capitulos"
        for chapter in consolidated_chapters:
            ch_id = chapter.get('chapter_id', 'unknown')
            ch_title = chapter.get('display_title', f'Capitulo_{ch_id}')
            # Sanitizar título para nombre de archivo
            safe_title = "".join(c for c in ch_title if c.isalnum() or c in ' _-').strip()[:50]
            
            ch_path = f"{chapters_folder}/{ch_id:03d}_{safe_title}.md"
            
            ch_content = f"# {ch_title}\n\n"
            ch_content += chapter.get('contenido_editado', '')
            
            blob_client = container_client.get_blob_client(ch_path)
            blob_client.upload_blob(
                ch_content, 
                overwrite=True,
                content_settings=ContentSettings(content_type='text/markdown')
            )
        
        logging.info(f"✅ Guardados {len(consolidated_chapters)} capítulos individuales")
        
        # ─────────────────────────────────────────────────────────────────
        # G. RESULTADO FINAL
        # ─────────────────────────────────────────────────────────────────
        
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
    """
    Convierte la Biblia Validada 4.0 a Markdown legible.
    Incluye secciones de análisis multi-capa.
    """
    lines = []
    lines.append("# 📚 BIBLIA NARRATIVA VALIDADA")
    lines.append("")
    lines.append(f"*Generada por Sylphrena 4.0 — {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
    lines.append("")
    
    # ─────────────────────────────────────────────────────────────────
    # 1. IDENTIDAD DE LA OBRA
    # ─────────────────────────────────────────────────────────────────
    identidad = bible.get('identidad_obra', {})
    if identidad:
        lines.append("## 🎭 IDENTIDAD DE LA OBRA")
        lines.append("")
        lines.append(f"- **Género:** {identidad.get('genero', 'No detectado')}")
        lines.append(f"- **Subgénero:** {identidad.get('subgenero', 'No detectado')}")
        lines.append(f"- **Tono:** {identidad.get('tono_predominante', 'No detectado')}")
        lines.append(f"- **Tema central:** {identidad.get('tema_central', 'No detectado')}")
        lines.append(f"- **Contrato con el lector:** {identidad.get('contrato_con_lector', 'No detectado')}")
        lines.append("")
    
    # ─────────────────────────────────────────────────────────────────
    # 2. ARCO NARRATIVO
    # ─────────────────────────────────────────────────────────────────
    arco = bible.get('arco_narrativo', {})
    if arco:
        lines.append("## 📈 ARCO NARRATIVO")
        lines.append("")
        lines.append(f"**Estructura detectada:** {arco.get('estructura_detectada', 'No detectada')}")
        lines.append("")
        
        puntos = arco.get('puntos_clave', {})
        if puntos:
            lines.append("### Puntos clave:")
            lines.append("")
            for punto, info in puntos.items():
                if isinstance(info, dict):
                    cap = info.get('capitulo', '?')
                    desc = info.get('descripcion', 'Sin descripción')
                    lines.append(f"- **{punto.replace('_', ' ').title()}** (Cap. {cap}): {desc}")
            lines.append("")
    
    # ─────────────────────────────────────────────────────────────────
    # 3. REPARTO DE PERSONAJES
    # ─────────────────────────────────────────────────────────────────
    reparto = bible.get('reparto_completo', {})
    if reparto:
        lines.append("## 👥 REPARTO DE PERSONAJES")
        lines.append("")
        
        for categoria in ['protagonistas', 'antagonistas', 'secundarios']:
            personajes = reparto.get(categoria, [])
            if personajes:
                lines.append(f"### {categoria.title()}")
                lines.append("")
                for p in personajes:
                    nombre = p.get('nombre', 'Sin nombre')
                    rol = p.get('rol_arquetipo', 'Sin rol')
                    arco_p = p.get('arco_personaje', 'Sin arco')
                    consistencia = p.get('consistencia', 'DESCONOCIDO')
                    
                    emoji = "✅" if consistencia == "CONSISTENTE" else "⚠️"
                    lines.append(f"**{nombre}** {emoji}")
                    lines.append(f"- Rol: {rol}")
                    lines.append(f"- Arco: {arco_p}")
                    
                    # Validación de arco (nuevo en 4.0)
                    validacion = p.get('validacion_arco', {})
                    if validacion:
                        score = validacion.get('score_coherencia', 'N/A')
                        lines.append(f"- Score de coherencia: {score}/10")
                    
                    if consistencia != "CONSISTENTE":
                        notas = p.get('notas_inconsistencia', [])
                        if notas:
                            lines.append(f"- ⚠️ Inconsistencias: {', '.join(notas[:3])}")
                    lines.append("")
    
    # ─────────────────────────────────────────────────────────────────
    # 4. VOZ DEL AUTOR
    # ─────────────────────────────────────────────────────────────────
    voz = bible.get('voz_del_autor', {})
    if voz:
        lines.append("## ✍️ VOZ DEL AUTOR")
        lines.append("")
        lines.append(f"**Estilo detectado:** {voz.get('estilo_detectado', 'No detectado')}")
        lines.append("")
        
        no_corregir = voz.get('NO_CORREGIR', [])
        if no_corregir:
            lines.append("### ⛔ NO CORREGIR (es intencional):")
            lines.append("")
            for item in no_corregir:
                lines.append(f"- {item}")
            lines.append("")
    
    # ─────────────────────────────────────────────────────────────────
    # 5. ANÁLISIS DE CAUSALIDAD (NUEVO en 4.0)
    # ─────────────────────────────────────────────────────────────────
    causalidad = bible.get('analisis_causalidad', {})
    if causalidad:
        lines.append("## 🔗 ANÁLISIS DE CAUSALIDAD NARRATIVA")
        lines.append("")
        
        problemas_causales = causalidad.get('problemas_detectados', [])
        if problemas_causales:
            lines.append("### Problemas de causalidad:")
            lines.append("")
            for prob in problemas_causales[:10]:
                tipo = prob.get('tipo', 'desconocido')
                desc = prob.get('descripcion', '')
                caps = prob.get('capitulos_afectados', [])
                lines.append(f"- **[{tipo.upper()}]** {desc}")
                if caps:
                    lines.append(f"  - Capítulos: {', '.join(str(c) for c in caps)}")
            lines.append("")
    
    # ─────────────────────────────────────────────────────────────────
    # 6. PROBLEMAS DETECTADOS
    # ─────────────────────────────────────────────────────────────────
    problemas = bible.get('problemas_priorizados', {})
    if problemas:
        lines.append("## 🚨 PROBLEMAS DETECTADOS")
        lines.append("")
        
        for severidad, emoji, items in [
            ('criticos', '🔴', problemas.get('criticos', [])),
            ('medios', '🟡', problemas.get('medios', [])),
            ('menores', '🟢', problemas.get('menores', []))
        ]:
            if items:
                lines.append(f"### {emoji} {severidad.title()} ({len(items)})")
                lines.append("")
                for p in items[:5]:
                    pid = p.get('id', '?')
                    tipo = p.get('tipo', 'N/A')
                    desc = p.get('descripcion', 'Sin descripción')
                    lines.append(f"- **[{pid}]** {tipo}: {desc[:100]}")
                if len(items) > 5:
                    lines.append(f"- *...y {len(items) - 5} más*")
                lines.append("")
    
    # ─────────────────────────────────────────────────────────────────
    # 7. VALIDACIÓN CRUZADA (NUEVO en 4.0)
    # ─────────────────────────────────────────────────────────────────
    validacion = bible.get('validacion_cruzada', {})
    if validacion:
        lines.append("## ✅ VALIDACIÓN CRUZADA")
        lines.append("")
        lines.append(f"- Afirmaciones verificadas: {validacion.get('verificadas', 0)}")
        lines.append(f"- Afirmaciones corregidas: {validacion.get('corregidas', 0)}")
        lines.append(f"- Nivel de confianza global: {validacion.get('confianza_global', 'N/A')}%")
        lines.append("")
    
    # ─────────────────────────────────────────────────────────────────
    # 8. MAPA DE RITMO
    # ─────────────────────────────────────────────────────────────────
    mapa_ritmo = bible.get('mapa_de_ritmo', {})
    if mapa_ritmo:
        lines.append("## ⏱️ MAPA DE RITMO")
        lines.append("")
        lines.append(f"**Patrón global:** {mapa_ritmo.get('patron_global', 'No detectado')}")
        lines.append("")
        
        capitulos = mapa_ritmo.get('capitulos', [])
        if capitulos:
            lines.append("| Cap | Título | Ritmo | Intencional | Función |")
            lines.append("|-----|--------|-------|-------------|---------|")
            for c in capitulos[:25]:
                num = c.get('numero', '?')
                titulo = c.get('titulo', 'Sin título')[:25]
                ritmo = c.get('clasificacion', '?')
                intencional = "✅" if c.get('es_intencional', False) else "❓"
                funcion = c.get('funcion_dramatica', 'N/A')[:20]
                lines.append(f"| {num} | {titulo} | {ritmo} | {intencional} | {funcion} |")
            if len(capitulos) > 25:
                lines.append(f"| ... | *({len(capitulos) - 25} más)* | ... | ... | ... |")
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
                original = c.get('original', '')[:80]
                editado = c.get('editado', '')[:80]
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

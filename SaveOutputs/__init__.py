# =============================================================================
# SaveOutputs/__init__.py
# =============================================================================
# 
# Guarda los resultados del procesamiento de forma organizada:
#   - biblia.json (datos crudos)
#   - biblia.md (legible)
#   - libro_editado.md (libro completo)
#   - resumen.json (metadata)
#
# =============================================================================

import logging
import json
import os
from datetime import datetime
from azure.storage.blob import BlobServiceClient

logging.basicConfig(level=logging.INFO)


def main(save_input: dict) -> dict:
    """
    Guarda todos los outputs en Blob Storage de forma organizada.
    
    Input: {
        'job_id': str,
        'book_name': str,
        'bible': dict,
        'edited_chapters': list,
        'original_chapters': list,
        'tiempos': dict
    }
    
    Output: {
        'status': 'success',
        'urls': {
            'biblia_json': '...',
            'biblia_md': '...',
            'libro_editado_md': '...',
            'resumen_json': '...'
        }
    }
    """
    try:
        job_id = save_input.get('job_id', datetime.now().strftime('%Y%m%d_%H%M%S'))
        book_name = save_input.get('book_name', 'libro')
        bible = save_input.get('bible', {})
        edited_chapters = save_input.get('edited_chapters', [])
        original_chapters = save_input.get('original_chapters', [])
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
        base_path = f"{job_id}"
        
        urls = {}
        
        # ─────────────────────────────────────────────────────────────────
        # B. GUARDAR BIBLIA JSON (datos crudos)
        # ─────────────────────────────────────────────────────────────────
        biblia_json_path = f"{base_path}/biblia.json"
        biblia_json_content = json.dumps(bible, indent=2, ensure_ascii=False)
        
        blob_client = container_client.get_blob_client(biblia_json_path)
        blob_client.upload_blob(biblia_json_content, overwrite=True)
        urls['biblia_json'] = blob_client.url
        logging.info(f"✅ Guardado: {biblia_json_path}")
        
        # ─────────────────────────────────────────────────────────────────
        # C. GUARDAR BIBLIA MARKDOWN (legible)
        # ─────────────────────────────────────────────────────────────────
        biblia_md_content = bible_to_markdown(bible)
        biblia_md_path = f"{base_path}/biblia.md"
        
        blob_client = container_client.get_blob_client(biblia_md_path)
        blob_client.upload_blob(biblia_md_content, overwrite=True)
        urls['biblia_md'] = blob_client.url
        logging.info(f"✅ Guardado: {biblia_md_path}")
        
        # ─────────────────────────────────────────────────────────────────
        # D. GUARDAR LIBRO EDITADO MARKDOWN
        # ─────────────────────────────────────────────────────────────────
        libro_md_content = chapters_to_markdown(edited_chapters, book_name)
        libro_md_path = f"{base_path}/libro_editado.md"
        
        blob_client = container_client.get_blob_client(libro_md_path)
        blob_client.upload_blob(libro_md_content, overwrite=True)
        urls['libro_editado_md'] = blob_client.url
        logging.info(f"✅ Guardado: {libro_md_path}")
        
        # ─────────────────────────────────────────────────────────────────
        # E. GUARDAR RESUMEN JSON (metadata)
        # ─────────────────────────────────────────────────────────────────
        resumen = {
            'job_id': job_id,
            'book_name': book_name,
            'fecha_procesamiento': datetime.now().isoformat(),
            'capitulos_originales': len(original_chapters),
            'capitulos_editados': len(edited_chapters),
            'tiempos': tiempos,
            'archivos_generados': list(urls.keys())
        }
        
        resumen_path = f"{base_path}/resumen.json"
        blob_client = container_client.get_blob_client(resumen_path)
        blob_client.upload_blob(json.dumps(resumen, indent=2, ensure_ascii=False), overwrite=True)
        urls['resumen_json'] = blob_client.url
        logging.info(f"✅ Guardado: {resumen_path}")
        
        # ─────────────────────────────────────────────────────────────────
        # F. GUARDAR CAMBIOS REALIZADOS (para revisión)
        # ─────────────────────────────────────────────────────────────────
        cambios_md_content = cambios_to_markdown(edited_chapters)
        cambios_md_path = f"{base_path}/cambios_realizados.md"
        
        blob_client = container_client.get_blob_client(cambios_md_path)
        blob_client.upload_blob(cambios_md_content, overwrite=True)
        urls['cambios_md'] = blob_client.url
        logging.info(f"✅ Guardado: {cambios_md_path}")
        
        logging.info(f"💾 Todos los archivos guardados en: {container_name}/{base_path}/")
        
        return {
            'status': 'success',
            'job_id': job_id,
            'container': container_name,
            'base_path': base_path,
            'urls': urls
        }
        
    except Exception as e:
        logging.error(f"❌ Error guardando outputs: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return {"status": "error", "error": str(e)}


def bible_to_markdown(bible: dict) -> str:
    """Convierte la Biblia JSON a Markdown legible."""
    
    lines = []
    lines.append("# 📚 BIBLIA NARRATIVA")
    lines.append("")
    lines.append(f"*Generada: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
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
    # 5. PROBLEMAS DETECTADOS
    # ─────────────────────────────────────────────────────────────────
    problemas = bible.get('problemas_priorizados', {})
    if problemas:
        lines.append("## 🚨 PROBLEMAS DETECTADOS")
        lines.append("")
        
        criticos = problemas.get('criticos', [])
        if criticos:
            lines.append("### 🔴 Críticos")
            lines.append("")
            for p in criticos:
                lines.append(f"- **[{p.get('id', '?')}]** {p.get('tipo', 'N/A')}: {p.get('descripcion', 'Sin descripción')}")
                lines.append(f"  - Capítulos afectados: {p.get('capitulos_afectados', [])}")
                lines.append(f"  - Sugerencia: {p.get('sugerencia', 'Ninguna')}")
            lines.append("")
        
        medios = problemas.get('medios', [])
        if medios:
            lines.append("### 🟡 Medios")
            lines.append("")
            for p in medios[:5]:  # Limitar a 5
                lines.append(f"- **[{p.get('id', '?')}]** {p.get('descripcion', 'Sin descripción')[:100]}")
            lines.append("")
        
        menores = problemas.get('menores', [])
        if menores:
            lines.append(f"### 🟢 Menores ({len(menores)} detectados)")
            lines.append("")
    
    # ─────────────────────────────────────────────────────────────────
    # 6. MAPA DE RITMO
    # ─────────────────────────────────────────────────────────────────
    mapa_ritmo = bible.get('mapa_de_ritmo', {})
    if mapa_ritmo:
        lines.append("## ⏱️ MAPA DE RITMO")
        lines.append("")
        lines.append(f"**Patrón global:** {mapa_ritmo.get('patron_global', 'No detectado')}")
        lines.append("")
        
        capitulos = mapa_ritmo.get('capitulos', [])
        if capitulos:
            lines.append("| Cap | Título | Ritmo | Intencional |")
            lines.append("|-----|--------|-------|-------------|")
            for c in capitulos[:20]:  # Limitar a 20
                num = c.get('numero', '?')
                titulo = c.get('titulo', 'Sin título')[:30]
                ritmo = c.get('clasificacion', '?')
                intencional = "✅" if c.get('es_intencional', False) else "❓"
                lines.append(f"| {num} | {titulo} | {ritmo} | {intencional} |")
            if len(capitulos) > 20:
                lines.append(f"| ... | *({len(capitulos) - 20} más)* | ... | ... |")
            lines.append("")
    
    return "\n".join(lines)


def chapters_to_markdown(edited_chapters: list, book_name: str) -> str:
    """Convierte los capítulos editados a un libro Markdown completo."""
    
    lines = []
    lines.append(f"# {book_name.upper()}")
    lines.append("")
    lines.append(f"*Editado con Sylphrena - {datetime.now().strftime('%Y-%m-%d')}*")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Ordenar por chapter_id
    sorted_chapters = sorted(
        edited_chapters, 
        key=lambda x: int(x.get('chapter_id', 0)) if str(x.get('chapter_id', '0')).isdigit() else 0
    )
    
    for chapter in sorted_chapters:
        chapter_id = chapter.get('chapter_id', '?')
        titulo = chapter.get('titulo', f'Capítulo {chapter_id}')
        contenido = chapter.get('contenido_editado', '')
        
        if not contenido:
            continue
        
        lines.append(f"## {titulo}")
        lines.append("")
        lines.append(contenido)
        lines.append("")
        lines.append("---")
        lines.append("")
    
    return "\n".join(lines)


def cambios_to_markdown(edited_chapters: list) -> str:
    """Genera un reporte de todos los cambios realizados."""
    
    lines = []
    lines.append("# 📝 CAMBIOS REALIZADOS")
    lines.append("")
    lines.append(f"*Reporte generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
    lines.append("")
    
    total_cambios = 0
    
    for chapter in edited_chapters:
        chapter_id = chapter.get('chapter_id', '?')
        titulo = chapter.get('titulo', f'Capítulo {chapter_id}')
        cambios = chapter.get('cambios_realizados', [])
        notas = chapter.get('notas_editor', '')
        
        if not cambios and not notas:
            continue
        
        lines.append(f"## {titulo}")
        lines.append("")
        
        if cambios:
            lines.append(f"**{len(cambios)} cambios:**")
            lines.append("")
            for c in cambios:
                tipo = c.get('tipo', 'otro')
                original = c.get('original', '')[:80]
                editado = c.get('editado', '')[:80]
                justificacion = c.get('justificacion', '')
                
                lines.append(f"- **[{tipo}]**")
                lines.append(f"  - Original: *\"{original}...\"*")
                lines.append(f"  - Editado: *\"{editado}...\"*")
                lines.append(f"  - Razón: {justificacion}")
                lines.append("")
                total_cambios += 1
        
        if notas:
            lines.append(f"**Notas del editor:** {notas}")
            lines.append("")
        
        lines.append("---")
        lines.append("")
    
    # Resumen al inicio
    summary = f"\n**Total de cambios: {total_cambios}**\n\n---\n\n"
    return lines[0] + "\n" + summary + "\n".join(lines[1:])
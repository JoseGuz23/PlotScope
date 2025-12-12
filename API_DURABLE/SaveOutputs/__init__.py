# =============================================================================
# SaveOutputs/__init__.py - LYA 6.0 (FULL + STABLE)
# =============================================================================

import logging
import json
import os
from datetime import datetime
from typing import Any
from azure.storage.blob import BlobServiceClient, ContentSettings

logging.basicConfig(level=logging.INFO)

# -----------------------------------------------------------------------------
# HELPERS (Funciones auxiliares necesarias)
# -----------------------------------------------------------------------------

def safe_get(obj, key, default=''):
    """Extrae valor de forma segura."""
    val = obj.get(key, default)
    return val if val else default

def generate_bible_markdown(bible: dict) -> str:
    """Genera versión markdown legible de la Biblia."""
    try:
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

        # 3. REPARTO
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
        
        return "\n".join(lines)
    except Exception as e:
        logging.error(f"Error generando MD Biblia: {e}")
        return "# Error generando Biblia MD"

def generate_changes_report_v5(chapters: list) -> str:
    """Genera reporte detallado de cambios."""
    try:
        lines = []
        lines.append("# 📝 REPORTE DE CAMBIOS\n")
        lines.append(f"*Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")
        
        for ch in chapters:
            title = ch.get('titulo', f"Capítulo {ch.get('chapter_id', '?')}")
            cambios = ch.get('cambios_realizados', [])
            
            lines.append(f"## {title}")
            if not cambios:
                lines.append("*(Sin cambios)*\n")
                continue
                
            for i, c in enumerate(cambios, 1):
                tipo = c.get('tipo', 'Mejora')
                just = c.get('justificacion', '')
                lines.append(f"**{i}. [{tipo}]** {just}")
                lines.append(f"> *Original:* \"{c.get('original', '')[:100]}...\"")
                lines.append(f"> *Editado:* \"{c.get('editado', '')[:100]}...\"\n")
            
            lines.append("---\n")
            
        return "\n".join(lines)
    except Exception as e:
        logging.error(f"Error generando Reporte Cambios: {e}")
        return "# Error generando Reporte"

def structure_changes_safe(consolidated):
    """Calcula estadísticas básicas de cambios."""
    try:
        # Intento de importación local si existe módulo, sino fallback
        try:
            from .structure_changes import structure_changes
            return structure_changes(consolidated)
        except ImportError:
            pass
            
        # Fallback simple
        total = 0
        changes_list = []
        for ch in consolidated:
            cambios = ch.get('cambios_realizados', [])
            total += len(cambios)
            changes_list.extend(cambios)
        return {"total_changes": total, "changes": changes_list}
    except Exception as e:
        logging.error(f"Error estructurando cambios: {e}")
        return {"total_changes": 0, "changes": []}

# -----------------------------------------------------------------------------
# MAIN FUNCTION
# -----------------------------------------------------------------------------

def main(input_data: Any) -> dict:
    """
    Guarda todos los outputs del proceso LYA 6.0.
    """
    logging.info(f"SaveOutputs Activity ejecutada. Tipo de input: {type(input_data)}")
    
    # 1. FIX DE INPUT: Asegurar que sea dict
    payload = input_data
    if isinstance(input_data, str):
        try:
            payload = json.loads(input_data)
        except json.JSONDecodeError as e:
            logging.error(f"[CRITICAL ERROR] JSON inválido: {e}")
            raise Exception(f"Input JSON inválido: {e}")

    if not isinstance(payload, dict):
        raise Exception("El formato de datos de entrada es incorrecto.")

    # 2. FIX DE VARIABLES: Inicialización temprana
    structured_changes = {"total_changes": 0, "changes": []} 
    urls = {}
    
    try:
        # Extraer datos básicos
        job_id = payload.get('job_id', 'unknown')
        book_name = payload.get('book_name', 'Sin título')
        
        # Extraer componentes principales
        bible = payload.get('bible', {})
        consolidated_chapters = payload.get('consolidated_chapters', [])
        carta_editorial = payload.get('carta_editorial', {})
        carta_markdown = payload.get('carta_markdown', '')
        margin_notes = payload.get('margin_notes', {})
        
        # --- NUEVOS COMPONENTES LYA 6.0 ---
        emotional_arc_analysis = payload.get('emotional_arc_analysis', {})
        sensory_detection_analysis = payload.get('sensory_detection_analysis', {})
        reflection_stats = payload.get('reflection_stats', {})

        # Extraer métricas y tiempos
        statistics = payload.get('statistics', {})
        tiempos = payload.get('tiempos', {})
        
        logging.info(f">>> SAVE OUTPUTS: {job_id} | {book_name}")

        # Configuración Azure
        connect_str = os.environ.get('AzureWebJobsStorage')
        if not connect_str:
            raise ValueError("AzureWebJobsStorage no configurado")
        
        blob_service = BlobServiceClient.from_connection_string(connect_str)
        container_name = "lya-outputs"
        try: blob_service.create_container(container_name)
        except: pass
        
        container_client = blob_service.get_container_client(container_name)
        base_path = job_id

        # Helper upload interno
        def upload_blob(path, content, content_type):
            blob_client = container_client.get_blob_client(path)
            content_bytes = content if isinstance(content, (str, bytes)) else json.dumps(content, indent=2, ensure_ascii=False)
            blob_client.upload_blob(content_bytes, overwrite=True, content_settings=ContentSettings(content_type=content_type))
            return f"https://{blob_service.account_name}.blob.core.windows.net/{container_name}/{path}"

        # -----------------------------------------------------------------
        # GUARDADO DE ARCHIVOS
        # -----------------------------------------------------------------

        # A. Metadata
        # Detectar estado real
        final_status = 'completed' if carta_editorial else payload.get('status', 'processing')
        if final_status == 'success': final_status = 'completed'

        # FIX: Preservar created_at original y project_name del metadata existente
        original_created_at = None
        original_project_name = None
        try:
            existing_meta_client = blob_service.get_blob_client(container_name, f'{job_id}/metadata.json')
            if existing_meta_client.exists():
                existing_meta = json.loads(existing_meta_client.download_blob().readall())
                original_created_at = existing_meta.get('created_at')
                original_project_name = existing_meta.get('project_name')
                logging.info(f"✅ Preservando created_at original: {original_created_at}")
        except Exception as e:
            logging.warning(f"⚠️ No se pudo leer metadata existente: {e}")

        metadata = {
            'job_id': job_id,
            'book_name': book_name,
            'project_name': original_project_name or book_name,
            'version': 'LYA 6.0', # <--- ACTUALIZADO A 6.0
            'created_at': original_created_at or datetime.now().isoformat(),
            'status': final_status,
            'counts': {'chapters': len(consolidated_chapters)},
            # --- FLAGS PARA FRONTEND LYA 6.0 ---
            'has_emotional_analysis': bool(emotional_arc_analysis),
            'has_sensory_analysis': bool(sensory_detection_analysis),
            'global_metrics': sensory_detection_analysis.get('global_metrics', {})
        }

        # --- AÑADIR DATOS COMPLETOS PARA FRONTEND LYA 6.0 ---
        if emotional_arc_analysis:
            metadata['emotional_arc_analysis'] = {
                'chapter_arcs': emotional_arc_analysis.get('emotional_arcs', []),
                'global_arc': emotional_arc_analysis.get('global_arc', {}),
                'diagnostics': emotional_arc_analysis.get('diagnostics', [])
            }

        if sensory_detection_analysis:
            metadata['sensory_detection_analysis'] = {
                'chapter_details': sensory_detection_analysis.get('sensory_analyses', []),
                'global_metrics': sensory_detection_analysis.get('global_metrics', {}),
                'critical_issues': sensory_detection_analysis.get('critical_issues', [])
            }

        if reflection_stats:
            metadata['reflection_stats'] = reflection_stats

        urls['metadata'] = upload_blob(f"{base_path}/metadata.json", metadata, 'application/json')

        # B. Biblia
        if bible:
            urls['biblia_json'] = upload_blob(f"{base_path}/biblia_validada.json", bible, 'application/json')
            biblia_md = generate_bible_markdown(bible)
            urls['biblia_narrativa'] = upload_blob(f"{base_path}/biblia_narrativa.md", biblia_md, 'text/markdown')

        # C. Carta Editorial
        if carta_editorial:
            urls['carta_editorial_json'] = upload_blob(f"{base_path}/carta_editorial.json", carta_editorial, 'application/json')
        
        md_content = carta_markdown
        if not md_content and isinstance(carta_editorial, dict):
            md_content = carta_editorial.get('texto_completo', '')
            
        if md_content:
            urls['carta_editorial_md'] = upload_blob(f"{base_path}/carta_editorial.md", md_content, 'text/markdown')

        # D. Notas Margen
        if margin_notes:
            urls['notas_margen'] = upload_blob(f"{base_path}/notas_margen.json", margin_notes, 'application/json')

        # E. Capítulos y Cambios
        if consolidated_chapters:
            urls['capitulos'] = upload_blob(f"{base_path}/capitulos_consolidados.json", consolidated_chapters, 'application/json')
            
            logging.info("🔄 Estructurando cambios...")
            if 'cambios_estructurados' in payload:
                structured_changes = payload['cambios_estructurados']
            else:
                structured_changes = structure_changes_safe(consolidated_chapters)
            
            urls['cambios'] = upload_blob(f"{base_path}/cambios_estructurados.json", structured_changes, 'application/json')
            
            reporte_md = generate_changes_report_v5(consolidated_chapters)
            urls['reporte_cambios'] = upload_blob(f"{base_path}/reporte_cambios.md", reporte_md, 'text/markdown')

        # --- F. NUEVOS ARCHIVOS LYA 6.0 ---
        if emotional_arc_analysis:
            urls['analisis_emocional'] = upload_blob(f"{base_path}/analisis_emocional.json", emotional_arc_analysis, 'application/json')
            logging.info("✅ Guardado analisis_emocional.json")

        if sensory_detection_analysis:
            urls['deteccion_sensorial'] = upload_blob(f"{base_path}/deteccion_sensorial.json", sensory_detection_analysis, 'application/json')
            logging.info("✅ Guardado deteccion_sensorial.json")

        if reflection_stats:
            urls['estadisticas_reflexion'] = upload_blob(f"{base_path}/estadisticas_reflexion.json", reflection_stats, 'application/json')

        # G. Resumen Ejecutivo
        resumen = {
            'job_id': job_id,
            'book_name': book_name,
            'version': 'LYA 6.0',
            'fecha_procesamiento': datetime.now().isoformat(),
            'total_cambios': structured_changes.get('total_changes', 0),
            'total_notas': len(margin_notes.get('all_notes', [])) if margin_notes else 0,
            'urls': urls
        }
        urls['resumen'] = upload_blob(f"{base_path}/resumen_ejecutivo.json", resumen, 'application/json')

        logging.info(f"✅ SAVE OUTPUTS completado. Cambios: {structured_changes.get('total_changes', 0)}")
        
        return {
            'status': 'success',
            'job_id': job_id,
            'urls': urls,
            'stats': {'total_cambios': structured_changes.get('total_changes', 0)}
        }

    except Exception as e:
        logging.error(f"❌ Error en SaveOutputs: {str(e)}")
        return {'status': 'error', 'error': str(e)}
# =============================================================================
# ReconstructManuscript/__init__.py - SYLPHRENA 4.0
# =============================================================================
# NUEVA FUNCIÓN:
#   - Consolida fragmentos editados en capítulos completos
#   - Normaliza numeración y títulos de capítulos
#   - Genera 3 versiones: limpia, enriquecida, comparativa
#   - Resuelve el Problema Crítico 6: Salida Fragmentada Sin Formato Editorial
# =============================================================================

import logging
import json
import re
from datetime import datetime
from difflib import unified_diff, SequenceMatcher

logging.basicConfig(level=logging.INFO)


def consolidate_fragments(edited_chapters: list) -> list:
    """
    Consolida fragmentos editados en capítulos completos.
    
    Agrupa por parent_chapter_id y concatena en orden de fragment_index.
    Aplica lógica de sutura inteligente para eliminar artefactos de fragmentación.
    """
    logging.info(f"🔧 Consolidando {len(edited_chapters)} fragmentos...")
    
    # Agrupar por parent_chapter_id
    chapters_by_parent = {}
    
    for frag in edited_chapters:
        parent_id = frag.get('parent_chapter_id', frag.get('chapter_id', 0))
        
        if parent_id not in chapters_by_parent:
            chapters_by_parent[parent_id] = {
                'fragments': [],
                'original_title': frag.get('titulo_original', frag.get('titulo', 'Sin título')),
                'section_type': frag.get('section_type', 'CHAPTER'),
                'total_fragments': frag.get('total_fragments', 1)
            }
        
        chapters_by_parent[parent_id]['fragments'].append(frag)
    
    # Consolidar cada capítulo
    consolidated_chapters = []
    
    for parent_id in sorted(chapters_by_parent.keys()):
        chapter_data = chapters_by_parent[parent_id]
        fragments = chapter_data['fragments']
        
        # Ordenar fragmentos por fragment_index
        fragments.sort(key=lambda f: f.get('fragment_index', 1))
        
        # Concatenar contenido con sutura inteligente
        consolidated_content = smart_stitch_fragments(fragments)
        consolidated_original = smart_stitch_fragments(fragments, use_original=True)
        
        # Agregar cambios de todos los fragmentos
        all_changes = []
        all_preserved = []
        all_problems_fixed = []
        all_notes = []
        total_cost = 0
        
        for frag in fragments:
            all_changes.extend(frag.get('cambios_realizados', []))
            all_preserved.extend(frag.get('elementos_preservados', []))
            all_problems_fixed.extend(frag.get('problemas_corregidos', []))
            if frag.get('notas_editor'):
                all_notes.append(frag.get('notas_editor'))
            if frag.get('metadata', {}).get('costo_usd'):
                total_cost += frag['metadata']['costo_usd']
        
        consolidated_chapter = {
            'chapter_id': parent_id,
            'original_title': chapter_data['original_title'],
            'section_type': chapter_data['section_type'],
            'contenido_editado': consolidated_content,
            'contenido_original': consolidated_original,
            'cambios_realizados': all_changes,
            'elementos_preservados': list(set(all_preserved)),
            'problemas_corregidos': list(set(all_problems_fixed)),
            'notas_editor': ' | '.join(all_notes) if all_notes else '',
            'fragment_count': len(fragments),
            'word_count': len(consolidated_content.split()),
            'metadata': {
                'costo_total_usd': round(total_cost, 4),
                'fragments_merged': len(fragments)
            }
        }
        
        consolidated_chapters.append(consolidated_chapter)
    
    logging.info(f"✅ Consolidados {len(consolidated_chapters)} capítulos desde {len(edited_chapters)} fragmentos")
    
    return consolidated_chapters


def smart_stitch_fragments(fragments: list, use_original: bool = False) -> str:
    """
    Concatena fragmentos aplicando lógica de sutura inteligente.
    
    - Si fragmento N termina sin puntuación terminal y N+1 empieza con minúscula: unir sin salto
    - Si fragmento N termina con diálogo abierto y N+1 continúa diálogo: preservar continuidad
    - En otros casos: insertar doble salto de línea
    """
    if not fragments:
        return ""
    
    content_key = 'contenido_original' if use_original else 'contenido_editado'
    
    result_parts = []
    
    for i, frag in enumerate(fragments):
        content = frag.get(content_key, frag.get('content', ''))
        
        if not content:
            continue
        
        if i == 0:
            result_parts.append(content)
            continue
        
        prev_content = result_parts[-1] if result_parts else ""
        
        # Analizar final del fragmento anterior
        prev_stripped = prev_content.rstrip()
        ends_with_terminal = prev_stripped and prev_stripped[-1] in '.!?»"'
        ends_with_dialogue = prev_stripped and prev_stripped[-1] in '»"' and '—' in prev_content[-100:]
        
        # Analizar inicio del fragmento actual
        current_stripped = content.lstrip()
        starts_with_lowercase = current_stripped and current_stripped[0].islower()
        starts_with_dialogue_continuation = current_stripped.startswith('—') or current_stripped.startswith('«')
        
        # Decidir tipo de unión
        if not ends_with_terminal and starts_with_lowercase:
            # Oración cortada: unir directamente con espacio
            result_parts.append(' ' + content.lstrip())
        elif ends_with_dialogue and starts_with_dialogue_continuation:
            # Continuación de diálogo: un solo salto de línea
            result_parts.append('\n' + content)
        else:
            # Caso normal: doble salto de línea (nuevo párrafo)
            result_parts.append('\n\n' + content)
    
    return ''.join(result_parts)


def normalize_chapter_titles(chapters: list) -> list:
    """
    Normaliza la numeración y títulos de capítulos para consistencia editorial.
    
    - Prólogo/Epílogo/Interludio: Preservar nombre en mayúsculas
    - Capítulos regulares: "Capítulo N" + título original si existe
    - Actos/Partes: "PRIMERA PARTE" / "ACTO I"
    """
    logging.info(f"📝 Normalizando títulos de {len(chapters)} capítulos...")
    
    chapter_counter = 0
    
    for chapter in chapters:
        section_type = chapter.get('section_type', 'CHAPTER')
        original_title = chapter.get('original_title', '')
        
        if section_type == 'PROLOGUE':
            chapter['normalized_title'] = 'PRÓLOGO'
            chapter['display_title'] = 'PRÓLOGO'
            
        elif section_type == 'EPILOGUE':
            chapter['normalized_title'] = 'EPÍLOGO'
            chapter['display_title'] = 'EPÍLOGO'
            
        elif section_type == 'INTERLUDE':
            chapter['normalized_title'] = 'INTERLUDIO'
            chapter['display_title'] = 'INTERLUDIO'
            
        elif section_type == 'ACT':
            # Extraer número si existe
            match = re.search(r'(\d+|[IVXLCDM]+)', original_title, re.IGNORECASE)
            if match:
                num = match.group(1)
                chapter['normalized_title'] = f'PARTE {num}'
            else:
                chapter['normalized_title'] = original_title.upper()
            chapter['display_title'] = chapter['normalized_title']
            
        elif section_type == 'CONTEXT':
            chapter['normalized_title'] = 'INTRODUCCIÓN'
            chapter['display_title'] = 'INTRODUCCIÓN'
            
        else:  # CHAPTER
            chapter_counter += 1
            
            # Extraer título descriptivo si existe (después de número)
            descriptive_title = ''
            # Buscar título después de "Capítulo X:" o "X." 
            match = re.search(r'(?:Capítulo\s+\d+[:\.\s]+|^\d+[:\.\s]+|\b[IVXLCDM]+[:\.\s]+)(.+)', 
                            original_title, re.IGNORECASE)
            if match:
                descriptive_title = match.group(1).strip()
            
            chapter['normalized_title'] = f'Capítulo {chapter_counter}'
            
            if descriptive_title and descriptive_title.lower() not in ['sin título', 'untitled']:
                chapter['display_title'] = f'Capítulo {chapter_counter}: {descriptive_title}'
            else:
                chapter['display_title'] = f'Capítulo {chapter_counter}'
    
    return chapters


def generate_clean_manuscript(chapters: list, book_name: str) -> str:
    """
    Genera manuscrito limpio en formato Markdown puro.
    Sin metadatos técnicos, solo texto editorial estándar.
    """
    lines = []
    
    # Encabezado del libro
    lines.append(f'# {book_name.upper()}')
    lines.append('')
    lines.append(f'*Editado con Sylphrena 4.0 — {datetime.now().strftime("%Y-%m-%d")}*')
    lines.append('')
    lines.append('---')
    lines.append('')
    lines.append('')
    
    for chapter in chapters:
        display_title = chapter.get('display_title', chapter.get('normalized_title', 'Sin título'))
        content = chapter.get('contenido_editado', '')
        section_type = chapter.get('section_type', 'CHAPTER')
        
        # Formato de encabezado según tipo
        if section_type in ['ACT']:
            lines.append(f'# {display_title}')
            lines.append('')
            lines.append('---')
            lines.append('')
        elif section_type in ['PROLOGUE', 'EPILOGUE', 'INTERLUDE']:
            lines.append(f'## {display_title}')
            lines.append('')
        else:
            lines.append(f'## {display_title}')
            lines.append('')
        
        # Contenido
        if content:
            lines.append(content)
        
        # Separador entre capítulos
        lines.append('')
        lines.append('')
        lines.append('---')
        lines.append('')
        lines.append('')
    
    return '\n'.join(lines)


def generate_enriched_manuscript(chapters: list, book_name: str, bible: dict) -> str:
    """
    Genera manuscrito enriquecido con anotaciones editoriales.
    Las anotaciones usan comentarios HTML invisibles en renders estándar.
    """
    lines = []
    
    # Encabezado
    lines.append(f'# {book_name.upper()}')
    lines.append('')
    lines.append(f'*Editado con Sylphrena 4.0 — {datetime.now().strftime("%Y-%m-%d")}*')
    lines.append('')
    lines.append('<!-- DOCUMENTO ENRIQUECIDO: Contiene anotaciones editoriales en comentarios HTML -->')
    lines.append('')
    lines.append('---')
    lines.append('')
    
    for chapter in chapters:
        display_title = chapter.get('display_title', 'Sin título')
        content = chapter.get('contenido_editado', '')
        chapter_id = chapter.get('chapter_id', '?')
        
        # Encabezado de capítulo
        lines.append(f'## {display_title}')
        lines.append('')
        
        # Anotaciones editoriales (comentario HTML)
        annotation_lines = []
        annotation_lines.append(f'<!-- ')
        annotation_lines.append(f'ANOTACIONES EDITORIALES - Capítulo {chapter_id}')
        annotation_lines.append(f'')
        
        # Cambios realizados
        cambios = chapter.get('cambios_realizados', [])
        if cambios:
            annotation_lines.append(f'CAMBIOS REALIZADOS ({len(cambios)}):')
            for i, cambio in enumerate(cambios[:5], 1):  # Limitar a 5
                tipo = cambio.get('tipo', 'otro')
                justificacion = cambio.get('justificacion', '')[:80]
                annotation_lines.append(f'  {i}. [{tipo}] {justificacion}')
            if len(cambios) > 5:
                annotation_lines.append(f'  ... y {len(cambios) - 5} cambios más')
            annotation_lines.append('')
        
        # Elementos preservados
        preservados = chapter.get('elementos_preservados', [])
        if preservados:
            annotation_lines.append(f'ELEMENTOS PRESERVADOS INTENCIONALMENTE:')
            for elem in preservados[:3]:
                annotation_lines.append(f'  - {elem[:60]}')
            annotation_lines.append('')
        
        # Notas del editor
        notas = chapter.get('notas_editor', '')
        if notas:
            annotation_lines.append(f'NOTAS DEL EDITOR:')
            annotation_lines.append(f'  {notas[:200]}')
            annotation_lines.append('')
        
        # Métricas
        word_count = chapter.get('word_count', len(content.split()))
        costo = chapter.get('metadata', {}).get('costo_total_usd', 0)
        annotation_lines.append(f'MÉTRICAS: {word_count} palabras | Costo: ${costo:.4f}')
        annotation_lines.append(f'-->')
        
        lines.extend(annotation_lines)
        lines.append('')
        
        # Contenido
        if content:
            lines.append(content)
        
        lines.append('')
        lines.append('---')
        lines.append('')
    
    return '\n'.join(lines)


def generate_diff_html(original: str, edited: str) -> str:
    """
    Genera diff visual entre texto original y editado.
    Retorna fragmento HTML con estilos inline.
    """
    # Dividir en líneas para diff
    original_lines = original.splitlines(keepends=True)
    edited_lines = edited.splitlines(keepends=True)
    
    # Usar SequenceMatcher para diff más detallado
    matcher = SequenceMatcher(None, original_lines, edited_lines)
    
    html_parts = []
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            # Texto sin cambios
            for line in original_lines[i1:i2]:
                escaped = line.replace('<', '&lt;').replace('>', '&gt;')
                html_parts.append(f'<span class="unchanged">{escaped}</span>')
                
        elif tag == 'delete':
            # Texto eliminado (rojo, tachado)
            for line in original_lines[i1:i2]:
                escaped = line.replace('<', '&lt;').replace('>', '&gt;')
                html_parts.append(f'<span class="deleted" style="color: #dc3545; text-decoration: line-through; background-color: #f8d7da;">{escaped}</span>')
                
        elif tag == 'insert':
            # Texto añadido (verde)
            for line in edited_lines[j1:j2]:
                escaped = line.replace('<', '&lt;').replace('>', '&gt;')
                html_parts.append(f'<span class="inserted" style="color: #28a745; background-color: #d4edda;">{escaped}</span>')
                
        elif tag == 'replace':
            # Texto reemplazado (mostrar ambos)
            for line in original_lines[i1:i2]:
                escaped = line.replace('<', '&lt;').replace('>', '&gt;')
                html_parts.append(f'<span class="deleted" style="color: #dc3545; text-decoration: line-through; background-color: #f8d7da;">{escaped}</span>')
            for line in edited_lines[j1:j2]:
                escaped = line.replace('<', '&lt;').replace('>', '&gt;')
                html_parts.append(f'<span class="inserted" style="color: #28a745; background-color: #d4edda;">{escaped}</span>')
    
    return ''.join(html_parts)


def generate_comparative_manuscript(chapters: list, book_name: str) -> str:
    """
    Genera versión comparativa con control de cambios en HTML.
    Muestra texto eliminado (tachado rojo) y añadido (verde).
    """
    html_lines = []
    
    # Encabezado HTML
    html_lines.append('<!DOCTYPE html>')
    html_lines.append('<html lang="es">')
    html_lines.append('<head>')
    html_lines.append('  <meta charset="UTF-8">')
    html_lines.append(f'  <title>{book_name} - Control de Cambios</title>')
    html_lines.append('  <style>')
    html_lines.append('    body { font-family: Georgia, serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.8; }')
    html_lines.append('    h1 { text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; }')
    html_lines.append('    h2 { color: #444; margin-top: 40px; }')
    html_lines.append('    .chapter { margin-bottom: 40px; padding: 20px; background: #fafafa; border-radius: 8px; }')
    html_lines.append('    .deleted { color: #dc3545; text-decoration: line-through; background-color: #f8d7da; }')
    html_lines.append('    .inserted { color: #28a745; background-color: #d4edda; }')
    html_lines.append('    .unchanged { color: #333; }')
    html_lines.append('    .stats { background: #e9ecef; padding: 15px; border-radius: 5px; margin: 20px 0; }')
    html_lines.append('    .legend { display: flex; gap: 20px; margin: 20px 0; padding: 10px; background: #f8f9fa; border-radius: 5px; }')
    html_lines.append('    .legend span { padding: 5px 10px; border-radius: 3px; }')
    html_lines.append('    pre { white-space: pre-wrap; word-wrap: break-word; }')
    html_lines.append('  </style>')
    html_lines.append('</head>')
    html_lines.append('<body>')
    
    # Título
    html_lines.append(f'<h1>{book_name.upper()}</h1>')
    html_lines.append(f'<p style="text-align: center; color: #666;">Control de Cambios — Sylphrena 4.0 — {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>')
    
    # Leyenda
    html_lines.append('<div class="legend">')
    html_lines.append('  <span class="deleted">Texto eliminado</span>')
    html_lines.append('  <span class="inserted">Texto añadido</span>')
    html_lines.append('  <span class="unchanged">Sin cambios</span>')
    html_lines.append('</div>')
    
    # Estadísticas globales
    total_changes = sum(len(ch.get('cambios_realizados', [])) for ch in chapters)
    total_words_original = sum(len(ch.get('contenido_original', '').split()) for ch in chapters)
    total_words_edited = sum(len(ch.get('contenido_editado', '').split()) for ch in chapters)
    
    html_lines.append('<div class="stats">')
    html_lines.append(f'  <strong>Resumen:</strong> {len(chapters)} capítulos | {total_changes} cambios totales')
    html_lines.append(f'  <br>Palabras: {total_words_original:,} original → {total_words_edited:,} editado')
    html_lines.append('</div>')
    
    # Capítulos con diff
    for chapter in chapters:
        display_title = chapter.get('display_title', 'Sin título')
        original = chapter.get('contenido_original', '')
        edited = chapter.get('contenido_editado', '')
        cambios = chapter.get('cambios_realizados', [])
        
        html_lines.append('<div class="chapter">')
        html_lines.append(f'<h2>{display_title}</h2>')
        html_lines.append(f'<p style="color: #666; font-size: 0.9em;">{len(cambios)} cambios en este capítulo</p>')
        
        # Generar diff visual
        if original and edited and original != edited:
            diff_html = generate_diff_html(original, edited)
            html_lines.append('<pre>')
            html_lines.append(diff_html)
            html_lines.append('</pre>')
        elif edited:
            # Sin cambios o solo texto editado disponible
            escaped = edited.replace('<', '&lt;').replace('>', '&gt;')
            html_lines.append('<pre>')
            html_lines.append(f'<span class="unchanged">{escaped}</span>')
            html_lines.append('</pre>')
        
        html_lines.append('</div>')
    
    # Cierre HTML
    html_lines.append('</body>')
    html_lines.append('</html>')
    
    return '\n'.join(html_lines)


def main(reconstruct_input: dict) -> dict:
    """
    Función principal de reconstrucción de manuscrito.
    
    Input esperado:
    {
        'edited_chapters': [...],   # Lista de capítulos/fragmentos editados
        'book_name': str,           # Nombre del libro
        'bible': {...},             # Biblia validada (para anotaciones)
        'original_chapters': [...]  # Capítulos originales (opcional, para diff)
    }
    
    Output:
    {
        'status': 'success',
        'manuscripts': {
            'clean_md': str,        # Manuscrito limpio Markdown
            'enriched_md': str,     # Manuscrito con anotaciones
            'comparative_html': str # Versión con control de cambios
        },
        'statistics': {...}
    }
    """
    try:
        edited_chapters = reconstruct_input.get('edited_chapters', [])
        book_name = reconstruct_input.get('book_name', 'Libro')
        bible = reconstruct_input.get('bible', {})
        
        if not edited_chapters:
            return {
                'status': 'error',
                'error': 'No hay capítulos editados para reconstruir'
            }
        
        logging.info(f"📚 Iniciando reconstrucción de manuscrito: {book_name}")
        logging.info(f"   Fragmentos de entrada: {len(edited_chapters)}")
        
        # 1. CONSOLIDAR FRAGMENTOS
        consolidated = consolidate_fragments(edited_chapters)
        
        # 2. NORMALIZAR TÍTULOS
        normalized = normalize_chapter_titles(consolidated)
        
        # 3. GENERAR MANUSCRITO LIMPIO
        logging.info("📄 Generando manuscrito limpio...")
        clean_manuscript = generate_clean_manuscript(normalized, book_name)
        
        # 4. GENERAR MANUSCRITO ENRIQUECIDO
        logging.info("📝 Generando manuscrito enriquecido...")
        enriched_manuscript = generate_enriched_manuscript(normalized, book_name, bible)
        
        # 5. GENERAR VERSIÓN COMPARATIVA
        logging.info("🔍 Generando versión comparativa con control de cambios...")
        comparative_manuscript = generate_comparative_manuscript(normalized, book_name)
        
        # 6. CALCULAR ESTADÍSTICAS
        total_words = sum(ch.get('word_count', 0) for ch in normalized)
        total_changes = sum(len(ch.get('cambios_realizados', [])) for ch in normalized)
        total_cost = sum(ch.get('metadata', {}).get('costo_total_usd', 0) for ch in normalized)
        
        statistics = {
            'chapters_count': len(normalized),
            'fragments_processed': len(edited_chapters),
            'total_words': total_words,
            'total_changes': total_changes,
            'total_cost_usd': round(total_cost, 4),
            'clean_size_chars': len(clean_manuscript),
            'enriched_size_chars': len(enriched_manuscript),
            'comparative_size_chars': len(comparative_manuscript)
        }
        
        logging.info(f"✅ Reconstrucción completada:")
        logging.info(f"   {statistics['chapters_count']} capítulos | {statistics['total_words']:,} palabras")
        logging.info(f"   {statistics['total_changes']} cambios | ${statistics['total_cost_usd']:.4f} costo total")
        
        return {
            'status': 'success',
            'manuscripts': {
                'clean_md': clean_manuscript,
                'enriched_md': enriched_manuscript,
                'comparative_html': comparative_manuscript
            },
            'consolidated_chapters': normalized,
            'statistics': statistics
        }
        
    except Exception as e:
        logging.error(f"❌ Error en ReconstructManuscript: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        
        return {
            'status': 'error',
            'error': str(e)
        }

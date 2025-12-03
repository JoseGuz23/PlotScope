# =============================================================================
# ReconstructManuscript/__init__.py - SYLPHRENA 4.0 - DIFF INLINE REAL
# =============================================================================
# CORRECCIONES:
#   - Preserva contenido_original EXACTAMENTE como vino (sin modificar)
#   - Diff palabra por palabra mejorado que maneja espacios correctamente
#   - HTML inline limpio mostrando cambios en contexto
# =============================================================================

import logging
import json
import os
import re
from datetime import datetime
from difflib import SequenceMatcher

logging.basicConfig(level=logging.INFO)


def sanitize_content(content: str, fragment_id: str) -> str:
    """
    Limpia contenido que podría ser JSON crudo o tener markdown.
    """
    if not content or not isinstance(content, str):
        return ""
    
    content = content.strip()
    
    # Caso 1: Texto limpio sin marcas sospechosas
    if not (content.startswith('{') or content.startswith('```') or '"capitulo_editado"' in content):
        return content
    
    # Caso 2: JSON con markdown
    if content.startswith('```json'):
        content = content.replace('```json', '').replace('```', '').strip()
    elif content.startswith('```'):
        content = content.replace('```', '').strip()
    
    # Caso 3: Contenido es JSON crudo
    if content.startswith('{'):
        try:
            parsed = json.loads(content)
            if 'capitulo_editado' in parsed:
                logging.info(f"✅ Fragmento {fragment_id}: JSON parseado correctamente")
                return parsed['capitulo_editado'].strip()
        except json.JSONDecodeError:
            pass
    
    # Caso 4: Buscar JSON embebido en texto
    if '"capitulo_editado"' in content:
        match = re.search(r'\{[\s\S]*"capitulo_editado"', content)
        if match:
            start_pos = match.start()
            try:
                brace_count = 0
                end_pos = start_pos
                for i, char in enumerate(content[start_pos:], start_pos):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_pos = i + 1
                            break
                
                if end_pos > start_pos:
                    json_str = content[start_pos:end_pos]
                    parsed = json.loads(json_str)
                    if 'capitulo_editado' in parsed:
                        logging.info(f"✅ Fragmento {fragment_id}: Extraído de JSON embebido")
                        return parsed['capitulo_editado'].strip()
            except:
                pass
    
    return content


def consolidate_fragments(edited_chapters: list) -> list:
    """
    Consolida fragmentos editados en capítulos completos.
    
    CRÍTICO: Preserva contenido_original EXACTAMENTE como vino.
    """
    logging.info(f"🔧 Consolidando {len(edited_chapters)} fragmentos...")
    
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
    
    consolidated_chapters = []
    
    for parent_id in sorted(chapters_by_parent.keys()):
        chapter_data = chapters_by_parent[parent_id]
        fragments = chapter_data['fragments']
        fragments.sort(key=lambda f: f.get('fragment_index', 1))
        
        # Sanitizar SOLO el contenido editado
        for frag in fragments:
            frag_id = f"{parent_id}-{frag.get('fragment_index', 1)}"
            original_content = frag.get('contenido_editado', frag.get('content', ''))
            sanitized_content = sanitize_content(original_content, frag_id)
            frag['contenido_editado'] = sanitized_content
            
            # CRÍTICO: NO tocar contenido_original - dejarlo exactamente como vino
            # Si no existe, usar el content original
            if 'contenido_original' not in frag or not frag['contenido_original']:
                frag['contenido_original'] = frag.get('content', '')
        
        # Concatenar contenido editado con sutura inteligente
        consolidated_content = smart_stitch_fragments(fragments, use_field='contenido_editado')
        
        # Concatenar contenido original SIN MODIFICAR (solo unir con doble salto)
        consolidated_original = simple_stitch_originals(fragments)
        
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


def simple_stitch_originals(fragments: list) -> str:
    """
    Concatena contenido original SIN MODIFICAR.
    Solo une con doble salto de línea, sin lógica inteligente.
    """
    if not fragments:
        return ""
    
    parts = []
    for frag in fragments:
        content = frag.get('contenido_original', '')
        if content:
            parts.append(content.strip())
    
    return '\n\n'.join(parts)


def smart_stitch_fragments(fragments: list, use_field: str = 'contenido_editado') -> str:
    """
    Concatena fragmentos EDITADOS con lógica inteligente.
    Solo se usa para contenido editado, NO para original.
    """
    if not fragments:
        return ""
    
    result_parts = []
    
    for i, frag in enumerate(fragments):
        content = frag.get(use_field, frag.get('content', ''))
        
        if not content:
            continue
        
        if i == 0:
            result_parts.append(content)
            continue
        
        prev_content = result_parts[-1] if result_parts else ""
        prev_stripped = prev_content.rstrip()
        ends_with_terminal = prev_stripped and prev_stripped[-1] in '.!?»"'
        ends_with_dialogue = prev_stripped and prev_stripped[-1] in '»"' and '—' in prev_content[-100:]
        
        current_stripped = content.lstrip()
        starts_with_lowercase = current_stripped and current_stripped[0].islower()
        starts_with_dialogue_continuation = current_stripped.startswith('—') or current_stripped.startswith('«')
        
        if not ends_with_terminal and starts_with_lowercase:
            result_parts.append(' ' + content.lstrip())
        elif ends_with_dialogue and starts_with_dialogue_continuation:
            result_parts.append('\n' + content)
        else:
            result_parts.append('\n\n' + content)
    
    return ''.join(result_parts)


def normalize_chapter_titles(chapters: list) -> list:
    """Normaliza títulos de capítulos."""
    for ch in chapters:
        title = ch.get('original_title', '')
        ch['display_title'] = title if title else f"Capítulo {ch.get('chapter_id', '?')}"
    return chapters


def generate_clean_manuscript(chapters: list, book_name: str) -> str:
    """Genera manuscrito limpio sin anotaciones."""
    lines = [f"# {book_name.upper()}\n", f"*Editado con Sylphrena 4.0 — {datetime.now().strftime('%Y-%m-%d')}*\n", "---\n"]
    
    for chapter in chapters:
        title = chapter.get('display_title', 'Sin título')
        content = chapter.get('contenido_editado', '')
        lines.append(f"## {title}\n")
        if content:
            lines.append(f"{content}\n")
        lines.append("---\n")
    
    return '\n'.join(lines)


def generate_enriched_manuscript(chapters: list, book_name: str, bible: dict) -> str:
    """Genera manuscrito con anotaciones editoriales."""
    lines = [
        f"# {book_name.upper()}\n",
        f"*Editado con Sylphrena 4.0 — {datetime.now().strftime('%Y-%m-%d')}*\n",
        "<!-- DOCUMENTO ENRIQUECIDO: Contiene anotaciones editoriales en comentarios HTML -->\n",
        "---\n"
    ]
    
    for chapter in chapters:
        title = chapter.get('display_title', 'Sin título')
        content = chapter.get('contenido_editado', '')
        cambios = chapter.get('cambios_realizados', [])
        preservados = chapter.get('elementos_preservados', [])
        notas = chapter.get('notas_editor', '')
        word_count = chapter.get('word_count', 0)
        costo = chapter.get('metadata', {}).get('costo_total_usd', 0)
        
        lines.append(f"## {title}\n")
        lines.append("<!-- ")
        lines.append(f"ANOTACIONES EDITORIALES - {title.upper()}\n")
        
        if cambios:
            lines.append(f"\nCAMBIOS REALIZADOS ({len(cambios)}):")
            for i, c in enumerate(cambios[:5], 1):
                tipo = c.get('tipo', 'otro')
                justificacion = c.get('justificacion', '')
                lines.append(f"  {i}. [{tipo}] {justificacion}")
            if len(cambios) > 5:
                lines.append(f"  ... y {len(cambios) - 5} cambios más")
        
        if notas:
            lines.append(f"\nNOTAS DEL EDITOR:\n  {notas}")
        
        lines.append(f"\nMÉTRICAS: {word_count} palabras | Costo: ${costo:.4f}")
        lines.append("-->\n")
        
        if content:
            lines.append(f"{content}\n")
        lines.append("---\n")
    
    return '\n'.join(lines)


# =============================================================================
# DIFF MEJORADO - PALABRA POR PALABRA CON MANEJO INTELIGENTE DE ESPACIOS
# =============================================================================

def normalize_for_diff(text: str) -> str:
    """
    Normaliza texto para mejorar la calidad del diff:
    - Convierte saltos múltiples a dobles
    - Normaliza espacios
    - Preserva estructura de párrafos
    """
    # Normalizar saltos de línea múltiples a máximo 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Normalizar espacios múltiples a uno solo (excepto entre líneas)
    lines = text.split('\n')
    normalized_lines = []
    for line in lines:
        # En cada línea, reducir espacios múltiples a uno
        normalized_line = re.sub(r' {2,}', ' ', line)
        normalized_lines.append(normalized_line)
    
    return '\n'.join(normalized_lines)


def generate_diff_html_improved(original: str, edited: str) -> str:
    """
    Genera diff visual mejorado palabra por palabra.
    
    Mejoras:
    - Normaliza espacios antes de comparar
    - Agrupa cambios pequeños para mejor legibilidad
    - Maneja saltos de línea correctamente
    """
    # Normalizar ambos textos
    original_normalized = normalize_for_diff(original)
    edited_normalized = normalize_for_diff(edited)
    
    # Tokenizar por palabras y espacios
    def tokenize_with_spaces(text):
        # Divide en tokens manteniendo espacios y saltos
        tokens = []
        current = ""
        for char in text:
            if char in ' \n\t':
                if current:
                    tokens.append(current)
                    current = ""
                tokens.append(char)
            else:
                current += char
        if current:
            tokens.append(current)
        return tokens
    
    original_tokens = tokenize_with_spaces(original_normalized)
    edited_tokens = tokenize_with_spaces(edited_normalized)
    
    # Usar SequenceMatcher
    matcher = SequenceMatcher(None, original_tokens, edited_tokens)
    
    result_parts = []
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            # Texto sin cambios
            text = ''.join(original_tokens[i1:i2])
            escaped = text.replace('<', '&lt;').replace('>', '&gt;')
            # Convertir saltos de línea a <br> para visualización
            escaped = escaped.replace('\n', '<br>')
            result_parts.append(f'<span class="unchanged">{escaped}</span>')
        
        elif tag == 'delete':
            # Texto eliminado
            text = ''.join(original_tokens[i1:i2])
            # No mostrar espacios/saltos aislados como eliminados
            if text.strip():
                escaped = text.replace('<', '&lt;').replace('>', '&gt;')
                escaped = escaped.replace('\n', '<br>')
                result_parts.append(f'<span class="deleted">{escaped}</span>')
        
        elif tag == 'insert':
            # Texto añadido
            text = ''.join(edited_tokens[j1:j2])
            # No mostrar espacios/saltos aislados como añadidos
            if text.strip():
                escaped = text.replace('<', '&lt;').replace('>', '&gt;')
                escaped = escaped.replace('\n', '<br>')
                result_parts.append(f'<span class="inserted">{escaped}</span>')
        
        elif tag == 'replace':
            # Texto reemplazado (mostrar eliminado + añadido)
            old_text = ''.join(original_tokens[i1:i2])
            new_text = ''.join(edited_tokens[j1:j2])
            
            # Solo mostrar si hay contenido real (no solo espacios)
            if old_text.strip():
                old_escaped = old_text.replace('<', '&lt;').replace('>', '&gt;')
                old_escaped = old_escaped.replace('\n', '<br>')
                result_parts.append(f'<span class="deleted">{old_escaped}</span>')
            
            if new_text.strip():
                new_escaped = new_text.replace('<', '&lt;').replace('>', '&gt;')
                new_escaped = new_escaped.replace('\n', '<br>')
                result_parts.append(f'<span class="inserted">{new_escaped}</span>')
    
    return ''.join(result_parts)


def generate_comparative_manuscript(chapters: list, book_name: str) -> str:
    """
    Genera documento HTML con control de cambios INLINE.
    Muestra texto eliminado (tachado rojo) y añadido (verde) EN CONTEXTO.
    """
    html_lines = []
    
    # Encabezado HTML
    html_lines.append('<!DOCTYPE html>')
    html_lines.append('<html lang="es">')
    html_lines.append('<head>')
    html_lines.append('  <meta charset="UTF-8">')
    html_lines.append(f'  <title>{book_name} - Control de Cambios Inline</title>')
    html_lines.append('  <style>')
    html_lines.append('    body { font-family: Georgia, serif; max-width: 900px; margin: 0 auto; padding: 20px; line-height: 1.9; background: #f5f5f5; }')
    html_lines.append('    h1 { text-align: center; border-bottom: 3px solid #333; padding-bottom: 15px; }')
    html_lines.append('    h2 { color: #444; margin-top: 40px; border-left: 4px solid #007bff; padding-left: 15px; }')
    html_lines.append('    .chapter { margin-bottom: 40px; padding: 25px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }')
    html_lines.append('    .diff-content { padding: 20px; background: #fafafa; border-radius: 5px; margin: 20px 0; line-height: 2.2; white-space: pre-wrap; }')
    html_lines.append('    .deleted { color: #dc3545; text-decoration: line-through; background-color: #f8d7da; padding: 2px 4px; border-radius: 3px; }')
    html_lines.append('    .inserted { color: #28a745; background-color: #d4edda; padding: 2px 4px; border-radius: 3px; font-weight: 500; }')
    html_lines.append('    .unchanged { color: #333; }')
    html_lines.append('    .stats { background: #e9ecef; padding: 20px; border-radius: 5px; margin: 20px 0; }')
    html_lines.append('    .legend { display: flex; gap: 20px; margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 5px; }')
    html_lines.append('    .legend span { padding: 8px 15px; border-radius: 3px; font-weight: bold; }')
    html_lines.append('    .no-changes { padding: 15px; background: #d4edda; color: #155724; border-radius: 5px; text-align: center; margin: 20px 0; }')
    html_lines.append('    .chapter-info { color: #666; font-size: 0.9em; margin-bottom: 15px; padding: 10px; background: #fff3cd; border-radius: 5px; }')
    html_lines.append('  </style>')
    html_lines.append('</head>')
    html_lines.append('<body>')
    
    # Título
    html_lines.append(f'<h1>{book_name.upper()}</h1>')
    html_lines.append(f'<p style="text-align: center; color: #666; font-size: 1.1em;">Control de Cambios Inline — Sylphrena 4.0 — {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>')
    
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
    html_lines.append(f'  <strong>📊 Resumen:</strong> {len(chapters)} capítulos procesados | {total_changes} cambios editoriales')
    html_lines.append(f'  <br><strong>Palabras:</strong> {total_words_original:,} original → {total_words_edited:,} editado ({total_words_edited - total_words_original:+,})')
    html_lines.append('</div>')
    
    # Capítulos con diff inline
    for chapter in chapters:
        display_title = chapter.get('display_title', 'Sin título')
        original = chapter.get('contenido_original', '')
        edited = chapter.get('contenido_editado', '')
        cambios = chapter.get('cambios_realizados', [])
        notas = chapter.get('notas_editor', '')
        
        html_lines.append('<div class="chapter">')
        html_lines.append(f'<h2>{display_title}</h2>')
        
        # Info del capítulo
        if cambios:
            html_lines.append(f'<div class="chapter-info">')
            html_lines.append(f'  <strong>📝 {len(cambios)} cambios editoriales realizados</strong>')
            if notas:
                html_lines.append(f'  <br>💡 {notas}')
            html_lines.append('</div>')
        
        # Generar diff visual inline
        if original and edited and original != edited:
            diff_html = generate_diff_html_improved(original, edited)
            html_lines.append('<div class="diff-content">')
            html_lines.append(diff_html)
            html_lines.append('</div>')
        elif edited:
            # Sin cambios
            html_lines.append('<div class="no-changes">✅ Sin cambios en este capítulo</div>')
            escaped = edited.replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')
            html_lines.append('<div class="diff-content">')
            html_lines.append(f'<span class="unchanged">{escaped}</span>')
            html_lines.append('</div>')
        
        html_lines.append('</div>')
    
    # Cierre HTML
    html_lines.append('</body>')
    html_lines.append('</html>')
    
    return '\n'.join(html_lines)


# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================

def main(reconstruct_input) -> dict:
    """Función principal de reconstrucción con diff inline."""
    try:
        if isinstance(reconstruct_input, str):
            try:
                input_data = json.loads(reconstruct_input)
            except:
                input_data = {}
        else:
            input_data = reconstruct_input
        
        reconstruct_input = input_data

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
        
        # 1. CONSOLIDAR FRAGMENTOS (preservando originales)
        consolidated = consolidate_fragments(edited_chapters)
        
        # 2. NORMALIZAR TÍTULOS
        normalized = normalize_chapter_titles(consolidated)
        
        # 3. GENERAR MANUSCRITO LIMPIO
        logging.info("📄 Generando manuscrito limpio...")
        clean_manuscript = generate_clean_manuscript(normalized, book_name)
        
        # 4. GENERAR MANUSCRITO ENRIQUECIDO
        logging.info("📝 Generando manuscrito enriquecido...")
        enriched_manuscript = generate_enriched_manuscript(normalized, book_name, bible)
        
        # 5. GENERAR VERSIÓN COMPARATIVA CON DIFF INLINE
        logging.info("🔍 Generando versión comparativa con diff inline...")
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
# =============================================================================
# ReconstructManuscript/__init__.py - SYLPHRENA 4.0.1
# =============================================================================
# 
# CORRECCIONES v4.0.1:
#   - NUEVA función sanitize_content() que detecta y limpia JSON residual
#   - Segunda línea de defensa contra JSON crudo en contenido editado
#   - Logging mejorado para detectar problemas de parsing upstream
#
# =============================================================================

import logging
import json
import re
from datetime import datetime
from difflib import unified_diff, SequenceMatcher

logging.basicConfig(level=logging.INFO)


# =============================================================================
# FUNCIÓN DE SANITIZACIÓN - SEGUNDA LÍNEA DE DEFENSA
# =============================================================================

def sanitize_content(content: str, fragment_id: str = "?") -> str:
    """
    SEGUNDA LÍNEA DE DEFENSA: Detecta y limpia JSON residual en contenido.
    
    Si el contenido parece ser JSON (empieza con { o ```json), intenta
    extraer el campo 'capitulo_editado' y devolver solo el texto.
    
    Args:
        content: El contenido a sanitizar
        fragment_id: ID del fragmento para logging
    
    Returns:
        Contenido limpio (texto puro, sin JSON)
    """
    if not content:
        return ""
    
    content = content.strip()
    
    # ===========================================
    # DETECCIÓN 1: Contenido envuelto en markdown
    # ===========================================
    if content.startswith("```json") or content.startswith("```"):
        logging.warning(f"⚠️ Fragmento {fragment_id}: Detectado markdown en contenido, limpiando...")
        
        # Limpiar markdown
        clean = re.sub(r'^[\s]*```(?:json)?[\s]*\n?', '', content)
        clean = re.sub(r'\n?[\s]*```[\s]*$', '', clean)
        content = clean.strip()
    
    # ===========================================
    # DETECCIÓN 2: Contenido es JSON puro
    # ===========================================
    if content.startswith('{'):
        logging.warning(f"⚠️ Fragmento {fragment_id}: Detectado JSON en contenido, extrayendo texto...")
        
        try:
            # Intentar parsear como JSON
            parsed = json.loads(content)
            
            # Buscar el campo de contenido editado
            if isinstance(parsed, dict):
                # Intentar múltiples nombres de campo posibles
                for field_name in ['capitulo_editado', 'contenido_editado', 'edited_content', 'content', 'texto']:
                    if field_name in parsed:
                        extracted = parsed[field_name]
                        if extracted and isinstance(extracted, str) and not extracted.strip().startswith('{'):
                            logging.info(f"✅ Fragmento {fragment_id}: Texto extraído exitosamente del campo '{field_name}'")
                            return extracted.strip()
                
                logging.error(f"❌ Fragmento {fragment_id}: JSON parseado pero no se encontró campo de texto válido")
        
        except json.JSONDecodeError:
            # JSON parcial o inválido - intentar extraer entre llaves
            start_idx = content.find('{')
            end_idx = content.rfind('}')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_str = content[start_idx : end_idx + 1]
                try:
                    parsed = json.loads(json_str)
                    if isinstance(parsed, dict):
                        for field_name in ['capitulo_editado', 'contenido_editado', 'edited_content', 'content', 'texto']:
                            if field_name in parsed:
                                extracted = parsed[field_name]
                                if extracted and isinstance(extracted, str):
                                    logging.info(f"✅ Fragmento {fragment_id}: Texto extraído con extracción entre llaves")
                                    return extracted.strip()
                except:
                    pass
            
            logging.error(f"❌ Fragmento {fragment_id}: No se pudo parsear JSON residual")
    
    # ===========================================
    # DETECCIÓN 3: JSON embebido en texto normal
    # ===========================================
    # Buscar patrón {"capitulo_editado": "..." en medio del contenido
    json_pattern = r'\{"capitulo_editado"\s*:\s*"'
    if re.search(json_pattern, content):
        logging.warning(f"⚠️ Fragmento {fragment_id}: Detectado JSON embebido, intentando extraer...")
        
        # Encontrar el inicio del JSON
        match = re.search(r'\{[^{}]*"capitulo_editado"', content)
        if match:
            start_pos = match.start()
            # Intentar encontrar el JSON completo
            try:
                # Buscar el final balanceado
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
    
    # Si no se detectó JSON, devolver contenido original
    return content


# =============================================================================
# CONSOLIDACIÓN DE FRAGMENTOS
# =============================================================================

def consolidate_fragments(edited_chapters: list) -> list:
    """
    Consolida fragmentos editados en capítulos completos.
    
    Agrupa por parent_chapter_id y concatena en orden de fragment_index.
    Aplica lógica de sutura inteligente para eliminar artefactos de fragmentación.
    
    NUEVO v4.0.1: Sanitiza contenido antes de consolidar.
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
        
        # NUEVO: Sanitizar contenido de cada fragmento antes de concatenar
        for frag in fragments:
            frag_id = f"{parent_id}-{frag.get('fragment_index', 1)}"
            
            # Sanitizar contenido editado
            original_content = frag.get('contenido_editado', frag.get('content', ''))
            sanitized_content = sanitize_content(original_content, frag_id)
            frag['contenido_editado'] = sanitized_content
            
            # También sanitizar original si es necesario
            original_original = frag.get('contenido_original', '')
            if original_original.strip().startswith('{') or original_original.strip().startswith('```'):
                frag['contenido_original'] = sanitize_content(original_original, f"{frag_id}-orig")
        
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
    
    Reglas:
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


# =============================================================================
# NORMALIZACIÓN DE TÍTULOS
# =============================================================================

def normalize_chapter_titles(chapters: list) -> list:
    """
    Normaliza la numeración y títulos de capítulos para consistencia editorial.
    """
    normalized = []
    chapter_counter = 0
    
    for chapter in chapters:
        original_title = chapter.get('original_title', 'Sin título')
        section_type = chapter.get('section_type', 'CHAPTER')
        
        # Determinar título normalizado según tipo
        if section_type == 'PROLOGUE':
            display_title = 'PRÓLOGO'
        elif section_type == 'EPILOGUE':
            display_title = 'EPÍLOGO'
        elif section_type == 'INTERLUDE':
            display_title = original_title
        elif section_type == 'ACT':
            display_title = original_title
        else:
            # Es un capítulo regular
            chapter_counter += 1
            
            # Intentar extraer título si existe
            title_match = re.match(r'^(?:Capítulo|Cap\.?|Chapter)\s*\d+[:\.\s]*(.+)?$', original_title, re.IGNORECASE)
            if title_match and title_match.group(1):
                subtitle = title_match.group(1).strip()
                display_title = f'Capítulo {chapter_counter}: {subtitle}'
            else:
                # Verificar si es solo número
                if re.match(r'^\d+$', original_title.strip()):
                    display_title = f'Capítulo {chapter_counter}'
                elif original_title.lower() in ['sin título', 'untitled', '']:
                    display_title = f'Capítulo {chapter_counter}'
                else:
                    display_title = f'Capítulo {chapter_counter}: {original_title}'
        
        normalized_chapter = chapter.copy()
        normalized_chapter['display_title'] = display_title
        normalized_chapter['normalized_title'] = display_title
        normalized_chapter['chapter_number'] = chapter_counter if section_type == 'CHAPTER' else 0
        
        normalized.append(normalized_chapter)
    
    return normalized


# =============================================================================
# GENERACIÓN DE MANUSCRITOS
# =============================================================================

def generate_clean_manuscript(chapters: list, book_name: str) -> str:
    """
    Genera manuscrito limpio en formato editorial estándar.
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
        annotation_lines.append(f'ANOTACIONES EDITORIALES - {display_title}')
        annotation_lines.append(f'')
        
        # Cambios realizados
        cambios = chapter.get('cambios_realizados', [])
        if cambios:
            annotation_lines.append(f'CAMBIOS REALIZADOS ({len(cambios)}):')
            for i, cambio in enumerate(cambios[:5], 1):
                tipo = cambio.get('tipo', 'otro')
                justificacion = cambio.get('justificacion', '')
                annotation_lines.append(f'  {i}. [{tipo}] {justificacion}')
            if len(cambios) > 5:
                annotation_lines.append(f'  ... y {len(cambios) - 5} cambios más')
            annotation_lines.append('')
        
        # Elementos preservados
        preservados = chapter.get('elementos_preservados', [])
        if preservados:
            annotation_lines.append(f'ELEMENTOS PRESERVADOS INTENCIONALMENTE:')
            for elem in preservados[:3]:
                annotation_lines.append(f'  - {elem}')
            annotation_lines.append('')
        
        # Notas del editor
        notas = chapter.get('notas_editor', '')
        if notas:
            annotation_lines.append(f'NOTAS DEL EDITOR:')
            annotation_lines.append(f'  {notas}')
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
    Genera diff visual palabra por palabra.
    """
    # 1. Tokenizar por palabras (manteniendo espacios para reconstruir)
    def tokenize(text):
        return re.split(r'(\s+)', text)

    original_tokens = tokenize(original)
    edited_tokens = tokenize(edited)
    
    # 2. Usar SequenceMatcher para encontrar diferencias
    matcher = SequenceMatcher(None, original_tokens, edited_tokens)
    
    result_parts = []
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            # Texto sin cambios
            text = ''.join(original_tokens[i1:i2])
            escaped = text.replace('<', '&lt;').replace('>', '&gt;')
            result_parts.append(f'<span class="unchanged">{escaped}</span>')
        
        elif tag == 'delete':
            # Texto eliminado
            text = ''.join(original_tokens[i1:i2])
            escaped = text.replace('<', '&lt;').replace('>', '&gt;')
            result_parts.append(f'<span class="deleted">{escaped}</span>')
        
        elif tag == 'insert':
            # Texto añadido
            text = ''.join(edited_tokens[j1:j2])
            escaped = text.replace('<', '&lt;').replace('>', '&gt;')
            result_parts.append(f'<span class="inserted">{escaped}</span>')
        
        elif tag == 'replace':
            # Texto reemplazado (mostrar eliminado + añadido)
            old_text = ''.join(original_tokens[i1:i2])
            new_text = ''.join(edited_tokens[j1:j2])
            old_escaped = old_text.replace('<', '&lt;').replace('>', '&gt;')
            new_escaped = new_text.replace('<', '&lt;').replace('>', '&gt;')
            result_parts.append(f'<span class="deleted">{old_escaped}</span>')
            result_parts.append(f'<span class="inserted">{new_escaped}</span>')
    
    return ''.join(result_parts)


def generate_comparative_manuscript(chapters: list, book_name: str) -> str:
    """
    Genera documento HTML con control de cambios visual.
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


# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================

def main(reconstruct_input) -> dict:
    """
    Función principal de reconstrucción.
    
    CORRECCIÓN v4.0.1: Sanitización de contenido antes de procesar.
    """
    try:
        # --- BLOQUE DE SEGURIDAD ---
        if isinstance(reconstruct_input, str):
            try:
                input_data = json.loads(reconstruct_input)
            except:
                input_data = {}
        else:
            input_data = reconstruct_input
        
        reconstruct_input = input_data 
        # ---------------------------

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
        
        # 1. CONSOLIDAR FRAGMENTOS (incluye sanitización)
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
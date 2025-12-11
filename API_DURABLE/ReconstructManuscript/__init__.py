# =============================================================================
# ReconstructManuscript/__init__.py - LYA 4.3 - ROBUST TEXT & CHANGES
# =============================================================================

import logging
import json
import re

logging.basicConfig(level=logging.INFO)

def sanitize_content(content: str, fragment_id: str) -> str:
    """
    Limpia el contenido asegurando que los párrafos se preserven.
    """
    if not content or not isinstance(content, str): return ""
    
    # 1. Limpieza básica de bloques de código Markdown
    content = content.strip()
    if content.startswith('```json'):
        content = content.replace('```json', '').replace('```', '').strip()
    elif content.startswith('```'):
        content = content.replace('```', '').strip()
    
    # 2. Intentar extraer JSON si la IA devolvió un objeto en vez de texto
    if content.startswith('{') or '"capitulo_editado"' in content:
        try:
            json_match = re.search(r'(\{[\s\S]*\})', content)
            if json_match:
                potential_json = json_match.group(1)
                parsed = json.loads(potential_json)
                # Buscar en varios campos posibles
                for key in ['capitulo_editado', 'text', 'content', 'edited_content']:
                    if key in parsed:
                        return parsed[key].strip()
        except:
            pass 

    # 3. Limpieza línea por línea (MEJORADA PARA NO BORRAR PÁRRAFOS)
    lines = content.split('\n')
    clean_lines = []
    
    for line in lines:
        # Filtrar preámbulos de IA tipo "Here is the text:"
        if re.match(r'^(Here is|This is|Adjunto|Aquí está|El texto editado).*:', line, re.IGNORECASE):
            continue
        clean_lines.append(line)
    
    # Unir de nuevo. 
    # IMPORTANTE: Si había lineas vacías (párrafos), se preservan.
    text = "\n".join(clean_lines).strip()
    
    # Asegurar que los párrafos tengan doble salto de línea para que Markdown los detecte
    # Reemplaza saltos simples por dobles si parece un bloque denso, 
    # pero respeta si ya tiene estructura.
    # Estrategia segura: No tocar los saltos internos, confiar en el split/join.
    return text

def smart_stitch_fragments(fragments: list, use_field: str = 'contenido_editado') -> str:
    """
    Une fragmentos asegurando doble salto de línea entre ellos para evitar 'muros de texto'.
    """
    if not fragments: return ""
    
    result_parts = []
    for i, frag in enumerate(fragments):
        # Preferencia de campo principal, luego fallbacks
        content = frag.get(use_field)
        if not content:
            # Fallbacks comunes
            content = frag.get('content', '') or frag.get('contenido_original', '') or frag.get('text', '')
        
        if not content: continue
        
        # Limpiar
        content = sanitize_content(content, f"frag-{i}")
        
        if i == 0:
            result_parts.append(content)
            continue
        
        # Lógica de unión: Siempre asegurar separación visual clara
        # Forzamos doble salto (\n\n) para garantizar párrafos separados entre fragmentos
        result_parts.append('\n\n' + content)
            
    return ''.join(result_parts)

def get_changes_robust(fragment: dict) -> list:
    """Busca la lista de cambios en cualquier llave posible."""
    candidates = [
        'cambios_realizados', 
        'changes', 
        'cambios', 
        'edits', 
        'list_of_changes',
        'cambios_detectados'
    ]
    
    for key in candidates:
        val = fragment.get(key)
        if val and isinstance(val, list):
            return val
    return []

def main(inputData: dict) -> dict:
    logging.info("📚 Starting ReconstructManuscript (Robust V3)...")
    
    if isinstance(inputData, str):
        try: inputData = json.loads(inputData)
        except: inputData = {}
            
    edited_chapters = inputData.get('edited_chapters', [])
    book_name = inputData.get('book_name', 'Libro')
    bible = inputData.get('bible', {})
    
    if not edited_chapters:
        return {'status': 'error', 'error': 'No edited chapters provided'}
    
    # 1. Agrupar por Capítulo
    chapters_by_parent = {}
    for frag in edited_chapters:
        parent_id = frag.get('parent_chapter_id') or frag.get('chapter_id') or 0
        if parent_id not in chapters_by_parent:
            chapters_by_parent[parent_id] = {
                'fragments': [], 
                'original_title': frag.get('titulo_original', frag.get('titulo', 'Capítulo'))
            }
        chapters_by_parent[parent_id]['fragments'].append(frag)
    
    consolidated_chapters = []
    
    # 2. Procesar cada capítulo
    for pid in sorted(chapters_by_parent.keys()):
        data = chapters_by_parent[pid]
        fragments = data['fragments']
        # Ordenar por índice
        fragments.sort(key=lambda x: int(x.get('fragment_index', 0) or 0))
        
        # A) Texto EDITADO (Buscando en varias llaves por si acaso)
        # Intentamos 'edited_content', 'contenido_editado', 'text'
        stitched_text = ""
        for field in ['edited_content', 'contenido_editado', 'text']:
            stitched_text = smart_stitch_fragments(fragments, use_field=field)
            if stitched_text: break
        
        # B) Texto ORIGINAL
        original_text = smart_stitch_fragments(fragments, use_field='contenido_original')
        if not original_text:
             original_text = smart_stitch_fragments(fragments, use_field='content')

        # C) Recopilar CAMBIOS (Robustamente)
        all_changes = []
        for f in fragments:
            cambios = get_changes_robust(f)
            if cambios:
                all_changes.extend(cambios)
            else:
                logging.warning(f"⚠️ No se encontraron cambios en fragmento {f.get('fragment_id', '?')}")
        
        consolidated_chapters.append({
            'chapter_id': pid,
            'original_title': data['original_title'],
            'contenido_editado': stitched_text,
            'contenido_original': original_text,
            'cambios_realizados': all_changes,
            'fragment_count': len(fragments)
        })

    # 3. Generar Manuscrito Markdown Final
    lines = [f"# {book_name.upper()}\n", "\n"]
    for chapter in consolidated_chapters:
        title = chapter.get('original_title', f"Capítulo {chapter.get('chapter_id')}")
        content = chapter.get('contenido_editado', '')
        
        if not content.lstrip().startswith('#'):
            lines.append(f"## {title}\n")
        
        lines.append(f"{content}\n")
        lines.append("\n***\n\n")
    
    clean_text = '\n'.join(lines)
    word_count = len(clean_text.split())
    
    logging.info(f"✅ Reconstrucción exitosa. Cambios recuperados: {sum(len(c['cambios_realizados']) for c in consolidated_chapters)}")
    
    return {
        'status': 'success',
        'manuscripts': {
            'clean_md': clean_text,
            'edited': clean_text 
        },
        'consolidated_chapters': consolidated_chapters,
        'statistics': {
            'total_words': word_count,
            'chapter_count': len(consolidated_chapters)
        }
    }
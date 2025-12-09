# =============================================================================
# ReconstructManuscript/__init__.py - SYLPHRENA 4.2 - CLEAN STITCHING
# =============================================================================

import logging
import json
import re
from datetime import datetime
from difflib import SequenceMatcher

logging.basicConfig(level=logging.INFO)

def sanitize_content(content: str, fragment_id: str) -> str:
    """Cleans content from markdown blocks or raw JSON."""
    if not content or not isinstance(content, str): return ""
    content = content.strip()
    
    # 1. Remove Markdown Code Blocks
    if content.startswith('```json'):
        content = content.replace('```json', '').replace('```', '').strip()
    elif content.startswith('```'):
        content = content.replace('```', '').strip()
    
    # 2. Try parsing as JSON (common LLM artifact)
    if content.startswith('{') or '"capitulo_editado"' in content:
        try:
            # Try finding the JSON blob even if surrounded by text
            json_match = re.search(r'(\{[\s\S]*\})', content)
            if json_match:
                potential_json = json_match.group(1)
                parsed = json.loads(potential_json)
                if 'capitulo_editado' in parsed:
                    return parsed['capitulo_editado'].strip()
                if 'text' in parsed: return parsed['text'].strip()
                if 'content' in parsed: return parsed['content'].strip()
        except:
            pass 

    # 3. Remove conversational preambles
    lines = content.split('\n')
    clean_lines = []
    for line in lines:
        if re.match(r'^(Here is|This is|Adjunto|Aquí está|El texto editado).*:', line, re.IGNORECASE): continue
        clean_lines.append(line)
    
    return "\n".join(clean_lines).strip()

def smart_stitch_fragments(fragments: list, use_field: str = 'contenido_editado') -> str:
    """Concatenates fragments handling punctuation and spacing smartly."""
    if not fragments: return ""
    
    result_parts = []
    for i, frag in enumerate(fragments):
        # Prefer edited content, fallback to original if missing
        content = frag.get(use_field)
        if not content:
            content = frag.get('content', '') or frag.get('contenido_original', '')
        
        if not content: continue
        
        # Sanitize this specific fragment before stitching
        content = sanitize_content(content, f"frag-{i}")
        
        if i == 0:
            result_parts.append(content)
            continue
        
        prev_content = result_parts[-1] if result_parts else ""
        prev_stripped = prev_content.rstrip()
        
        # Check terminators
        ends_with_terminal = prev_stripped and prev_stripped[-1] in '.!?»"'
        ends_with_dialogue = prev_stripped and prev_stripped[-1] in '»"' and '—' in prev_content[-100:]
        
        current_stripped = content.lstrip()
        starts_with_lowercase = current_stripped and current_stripped[0].islower()
        starts_with_dialogue_continuation = current_stripped.startswith('—') or current_stripped.startswith('«')
        
        # Logic: If previous sentence ended, new one usually starts with space or new line.
        # But if it looks like a continuation (lowercase), just add a space.
        if not ends_with_terminal and starts_with_lowercase:
            result_parts.append(' ' + content.lstrip())
        elif ends_with_dialogue and starts_with_dialogue_continuation:
             result_parts.append('\n' + content)
        else:
            result_parts.append('\n\n' + content)
            
    return ''.join(result_parts)

def generate_clean_manuscript(chapters: list, book_name: str) -> str:
    """Generates clean Markdown manuscript suitable for export."""
    lines = [f"# {book_name.upper()}\n", "\n"]
    
    for chapter in chapters:
        # Use original title or generic
        title = chapter.get('original_title', f"Capítulo {chapter.get('chapter_id')}")
        content = chapter.get('contenido_editado', '')
        
        # Ensure title format. If content already has a header, don't double up.
        if not content.lstrip().startswith('#'):
            lines.append(f"## {title}\n")
        
        lines.append(f"{content}\n")
        lines.append("\n***\n\n") # Scene break or chapter break
    
    return '\n'.join(lines)

def main(inputData: dict) -> dict:
    logging.info("📚 Starting ReconstructManuscript...")
    
    if isinstance(inputData, str):
        try: inputData = json.loads(inputData)
        except: inputData = {}
            
    edited_chapters = inputData.get('edited_chapters', [])
    book_name = inputData.get('book_name', 'Libro')
    bible = inputData.get('bible', {})
    
    if not edited_chapters:
        return {'status': 'error', 'error': 'No edited chapters provided'}
    
    # 1. Group fragments by Chapter
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
    
    # 2. Process Each Chapter
    for pid in sorted(chapters_by_parent.keys()):
        data = chapters_by_parent[pid]
        fragments = data['fragments']
        # Sort by fragment index
        fragments.sort(key=lambda x: int(x.get('fragment_index', 0) or 0))
        
        # STITCHING MAGIC
        stitched_text = smart_stitch_fragments(fragments, use_field='edited_content')
        
        consolidated_chapters.append({
            'chapter_id': pid,
            'original_title': data['original_title'],
            'contenido_editado': stitched_text,
            # We preserve changes just for metadata/stats if needed later
            'fragment_count': len(fragments)
        })

    # 3. Generate Final Doc
    clean_text = generate_clean_manuscript(consolidated_chapters, book_name)
    
    # Simple stats
    word_count = len(clean_text.split())
    
    return {
        'status': 'success',
        'manuscripts': {
            'clean_md': clean_text,
            # We put the same text in 'edited' for compatibility
            'edited': clean_text 
        },
        'consolidated_chapters': consolidated_chapters,
        'statistics': {
            'total_words': word_count,
            'chapter_count': len(consolidated_chapters)
        }
    }
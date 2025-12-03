"""
Transforma cambios desde formato actual a formato estructurado
con posiciones precisas para el editor frontend.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)


def structure_changes(consolidated_chapters: List[Dict]) -> Dict[str, Any]:
    """
    Transforma cambios a formato estructurado con posiciones.
    
    Args:
        consolidated_chapters: Lista de capítulos consolidados con cambios
        
    Returns:
        Diccionario con cambios estructurados y metadatos
    """
    structured_changes = []
    change_counter = 0
    
    for chapter in consolidated_chapters:
        chapter_id = chapter.get('chapter_id', 0)
        chapter_title = chapter.get('display_title', f'Capítulo {chapter_id}')
        content_original = chapter.get('contenido_original', '')
        
        # Dividir en párrafos para encontrar posiciones
        paragraphs = content_original.split('\n\n')
        
        for cambio in chapter.get('cambios_realizados', []):
            # Encontrar posición del cambio
            position = find_change_position(
                original_text=cambio.get('original', ''),
                paragraphs=paragraphs
            )
            
            structured_change = {
                'change_id': f"ch{chapter_id}-change-{str(change_counter).zfill(3)}",
                'chapter_id': chapter_id,
                'chapter_title': chapter_title,
                'position': position,
                'tipo': cambio.get('tipo', 'otro'),
                'original': cambio.get('original', ''),
                'editado': cambio.get('editado', ''),
                'justificacion': cambio.get('justificacion', ''),
                'impacto_narrativo': cambio.get('impacto_narrativo', ''),
                'status': 'pending',
                'created_at': datetime.utcnow().isoformat() + 'Z',
                'user_decision': None
            }
            
            structured_changes.append(structured_change)
            change_counter += 1
    
    # Contar por tipo
    changes_by_type = {}
    for change in structured_changes:
        tipo = change['tipo']
        changes_by_type[tipo] = changes_by_type.get(tipo, 0) + 1
    
    return {
        'total_changes': len(structured_changes),
        'changes_by_type': changes_by_type,
        'changes': structured_changes
    }


def find_change_position(original_text: str, paragraphs: List[str]) -> Dict[str, Any]:
    """
    Encuentra la posición exacta del cambio en el texto.
    
    Args:
        original_text: Texto original del cambio
        paragraphs: Lista de párrafos del capítulo
        
    Returns:
        Diccionario con información de posición
    """
    if not original_text:
        return {
            'paragraph_index': 0,
            'word_start': 0,
            'word_end': 0,
            'context_before': '',
            'context_after': ''
        }
    
    # Buscar en qué párrafo está
    for para_idx, para in enumerate(paragraphs):
        if original_text in para:
            # Encontrar posición de palabras
            pos = para.find(original_text)
            words_before = para[:pos].split()
            words_in_change = original_text.split()
            
            # Contexto (50 caracteres antes y después)
            context_start = max(0, pos - 50)
            context_end = min(len(para), pos + len(original_text) + 50)
            
            return {
                'paragraph_index': para_idx,
                'word_start': len(words_before),
                'word_end': len(words_before) + len(words_in_change),
                'context_before': para[context_start:pos].strip(),
                'context_after': para[pos + len(original_text):context_end].strip()
            }
    
    # Si no se encuentra, posición genérica
    logging.warning(f"⚠️ No se encontró posición exacta para cambio: {original_text[:50]}...")
    return {
        'paragraph_index': 0,
        'word_start': 0,
        'word_end': 0,
        'context_before': '',
        'context_after': ''
    }
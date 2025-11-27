# =============================================================================
# SegmentBook/__init__.py - SYLPHRENA 4.0
# =============================================================================
# CAMBIOS DESDE 3.1:
#   - Genera metadatos jerárquicos completos (parent_chapter_id, fragment_index, etc.)
#   - Preserva relación fragmento-capítulo durante todo el pipeline
#   - Resuelve el Problema Crítico 1: Pérdida de Contexto Jerárquico
# =============================================================================

import azure.functions as func
import regex as re
import json
import logging
import os
import pdfplumber
from docx import Document

MAX_CHARS_PER_CHUNK = 12000

logging.basicConfig(level=logging.INFO)


def extract_text_from_file(file_path: str) -> str:
    """Extrae texto de PDF, DOCX o TXT."""
    extension = os.path.splitext(file_path)[1].lower()
    
    logging.info(f"📂 Extrayendo texto de: {file_path} (formato: {extension})")
    
    if extension == '.pdf':
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    
    elif extension == '.docx':
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    
    elif extension == '.txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    else:
        raise ValueError(f"Formato no soportado: {extension}. Use .pdf, .docx o .txt")


def smart_split(text: str, max_chars: int) -> list:
    """
    Divide un texto largo en fragmentos más pequeños respetando los saltos de línea.
    Intenta cortar en párrafos completos cuando es posible.
    """
    if len(text) <= max_chars:
        return [text]
    
    chunks = []
    remaining_text = text
    
    while len(remaining_text) > max_chars:
        # Buscar punto de corte ideal (doble salto de línea = fin de párrafo)
        split_point = remaining_text.rfind('\n\n', 0, max_chars)
        
        # Si no hay doble salto, buscar salto simple
        if split_point == -1 or split_point < max_chars // 2:
            split_point = remaining_text.rfind('\n', 0, max_chars)
        
        # Si tampoco hay salto de línea, cortar en punto o espacio
        if split_point == -1 or split_point < max_chars // 2:
            split_point = remaining_text.rfind('. ', 0, max_chars)
            if split_point != -1:
                split_point += 1  # Incluir el punto
        
        # Último recurso: cortar en el límite
        if split_point == -1 or split_point < max_chars // 2:
            split_point = max_chars
        
        chunk = remaining_text[:split_point].strip()
        if chunk:
            chunks.append(chunk)
        remaining_text = remaining_text[split_point:].strip()
    
    if remaining_text:
        chunks.append(remaining_text)
    
    return chunks


def detect_section_type(title_line: str) -> str:
    """
    Normaliza el tipo de sección basado en el título detectado.
    Permite que la lógica posterior trate 'III.' igual que 'Capítulo 3'.
    """
    title_lower = title_line.lower().strip()
    
    # 1. Grupo ACTO/PARTE (Nivel Alto)
    if re.match(r'^(acto|parte)\b', title_lower):
        return 'ACT'
    
    # 2. Palabras Clave Especiales
    if re.match(r'^(prólogo|prefacio|introducción)', title_lower):
        return 'PROLOGUE'
    if re.match(r'^interludio', title_lower):
        return 'INTERLUDE'
    if re.match(r'^(epílogo|nota)', title_lower):
        return 'EPILOGUE'
    
    # Casos especiales de inicio sin título formal
    if "inicio" in title_lower and "contexto" in title_lower:
        return 'CONTEXT'

    # 3. Todo lo demás se considera CAPÍTULO
    return 'CHAPTER'


def generate_hierarchical_metadata(chapters_raw: list) -> list:
    """
    NUEVA FUNCIÓN 4.0: Genera metadatos jerárquicos completos.
    
    Cada fragmento incluye:
    - id: Identificador único global del fragmento
    - parent_chapter_id: ID del capítulo padre
    - original_title: Título limpio del capítulo
    - title: Título de display (incluye info de fragmentación)
    - fragment_index: Posición del fragmento dentro del capítulo (1-based)
    - total_fragments: Total de fragmentos del capítulo
    - section_type: Tipo de sección (CHAPTER, PROLOGUE, etc.)
    - is_first_fragment: Bandera booleana
    - is_last_fragment: Bandera booleana
    - content: Texto del fragmento
    - word_count: Conteo de palabras
    """
    
    final_list = []
    global_fragment_id = 1
    chapter_id = 1
    
    for chapter_data in chapters_raw:
        raw_title = chapter_data['title']
        content = chapter_data['content']
        section_type = chapter_data['section_type']
        
        # Decidir si fragmentar
        if len(content) > MAX_CHARS_PER_CHUNK:
            logging.warning(f"⚠️ Fragmentando capítulo extenso: '{raw_title}' ({len(content)} chars)")
            sub_chunks = smart_split(content, MAX_CHARS_PER_CHUNK)
            total_fragments = len(sub_chunks)
            
            for idx, chunk in enumerate(sub_chunks):
                fragment_index = idx + 1
                is_first = (fragment_index == 1)
                is_last = (fragment_index == total_fragments)
                
                fragment_obj = {
                    'id': global_fragment_id,
                    'parent_chapter_id': chapter_id,
                    'original_title': raw_title,
                    'title': f"{raw_title} (Fragmento {fragment_index}/{total_fragments})",
                    'fragment_index': fragment_index,
                    'total_fragments': total_fragments,
                    'section_type': section_type,
                    'is_first_fragment': is_first,
                    'is_last_fragment': is_last,
                    'is_fragment': True,
                    'content': chunk,
                    'word_count': len(chunk.split())
                }
                
                final_list.append(fragment_obj)
                global_fragment_id += 1
        else:
            # Capítulo atómico (no requiere fragmentación)
            fragment_obj = {
                'id': global_fragment_id,
                'parent_chapter_id': chapter_id,
                'original_title': raw_title,
                'title': raw_title,
                'fragment_index': 1,
                'total_fragments': 1,
                'section_type': section_type,
                'is_first_fragment': True,
                'is_last_fragment': True,
                'is_fragment': False,
                'content': content,
                'word_count': len(content.split())
            }
            
            final_list.append(fragment_obj)
            global_fragment_id += 1
        
        chapter_id += 1
    
    return final_list


def main(book_path: str) -> dict:
    """
    Función principal que segmenta un libro en capítulos con metadatos jerárquicos.
    
    Args:
        book_path: Ruta al archivo del libro (.pdf, .docx, o .txt)
    
    Returns:
        Diccionario con:
        - fragments: Lista de fragmentos con metadatos jerárquicos completos
        - book_metadata: Información global del libro
        - chapter_map: Mapa de capítulos para referencia rápida
    """
    try:
        # ============================================
        # FASE 1: EXTRAER TEXTO DEL ARCHIVO
        # ============================================
        sample_text = extract_text_from_file(book_path)
        
        logging.info(f"📖 Texto extraído: {len(sample_text)} caracteres")
        
        if len(sample_text.strip()) < 100:
            raise ValueError("El archivo parece estar vacío o tiene muy poco contenido")

        # ============================================
        # FASE 2: DEFINICIÓN DE PATRONES (REGEX)
        # ============================================
        
        # GRUPO A: Narrativa Especial
        special_keywords = r'(?:Prólogo|Prefacio|Introducción|Interludio|Epílogo|Nota para el editor)'

        # GRUPO B: Estructura Mayor
        acts_and_parts = r'(?:Acto|Parte)\s+(?:\d+|[IVXLCDM]+)'

        # GRUPO C: Capítulos y Variaciones
        chapter_variations = r'(?:Capítulo\s+(?:\d+|[IVXLCDM]+)|Final|\b[IVXLCDM]+\.|\b\d+\.)'

        # REGEX MAESTRO
        full_pattern = f'(?mi)(?:^\\s*)(?:{special_keywords}|{acts_and_parts}|{chapter_variations})[^\n]*'
        
        logging.info("🔍 Iniciando segmentación con metadatos jerárquicos...")

        # ============================================
        # FASE 3: DETECCIÓN DE CAPÍTULOS
        # ============================================
        original_chapters = re.split(f'(?={full_pattern})', sample_text)
        
        chapters_raw = []

        for i, raw_chapter in enumerate(original_chapters):
            if not raw_chapter.strip():
                continue

            lines = raw_chapter.strip().split('\n')
            raw_title = lines[0].strip()
            
            # Lógica para detectar si el primer fragmento es el "Inicio" sin título
            if i == 0 and not re.match(full_pattern, raw_title):
                raw_title = "Inicio / Contexto"

            section_type = detect_section_type(raw_title)
            content = '\n'.join(lines[1:]) if len(lines) > 1 else ""
            
            # Si es el primer bloque y no tiene contenido separado
            if i == 0 and content == "":
                content = raw_chapter
                raw_title = "Inicio / Contexto"

            # Filtro de contenido muy corto
            if len(content.split()) < 20:
                continue

            chapters_raw.append({
                'title': raw_title,
                'content': content,
                'section_type': section_type
            })

        # ============================================
        # FASE 4: GENERAR METADATOS JERÁRQUICOS
        # ============================================
        fragments = generate_hierarchical_metadata(chapters_raw)
        
        # ============================================
        # FASE 5: GENERAR MAPA DE CAPÍTULOS
        # ============================================
        chapter_map = {}
        for frag in fragments:
            parent_id = frag['parent_chapter_id']
            if parent_id not in chapter_map:
                chapter_map[parent_id] = {
                    'original_title': frag['original_title'],
                    'section_type': frag['section_type'],
                    'fragment_ids': [],
                    'total_fragments': frag['total_fragments']
                }
            chapter_map[parent_id]['fragment_ids'].append(frag['id'])
        
        # ============================================
        # FASE 6: METADATOS GLOBALES DEL LIBRO
        # ============================================
        total_words = sum(f['word_count'] for f in fragments)
        total_chapters = len(chapter_map)
        total_fragments = len(fragments)
        
        book_metadata = {
            'total_words': total_words,
            'total_chapters': total_chapters,
            'total_fragments': total_fragments,
            'source_file': book_path,
            'fragmentation_threshold': MAX_CHARS_PER_CHUNK
        }
        
        # Log de resultados
        logging.info(f"✅ Segmentación completada:")
        logging.info(f"   📚 Capítulos: {total_chapters}")
        logging.info(f"   📄 Fragmentos: {total_fragments}")
        logging.info(f"   📝 Palabras totales: {total_words:,}")
        
        for frag in fragments[:5]:  # Log primeros 5
            logging.info(f"   ID: {frag['id']} | [{frag['section_type']}] {frag['title']} | Palabras: {frag['word_count']}")
        
        if total_fragments > 5:
            logging.info(f"   ... y {total_fragments - 5} fragmentos más")

        return {
            'fragments': fragments,
            'book_metadata': book_metadata,
            'chapter_map': chapter_map
        }
        
    except Exception as e:
        logging.error(f"❌ Error en SegmentBook: {str(e)}")
        raise e

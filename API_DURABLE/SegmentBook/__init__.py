# =============================================================================
# SegmentBook/__init__.py
# =============================================================================

import azure.functions as func
import regex as re
import json
import logging
import os
import sys
import traceback

# Importaciones opcionales (Manejo de errores si faltan librerías)
try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

MAX_CHARS_PER_CHUNK = 12000
# Este valor ahora es solo un DEFAULT. Si el orquestador manda otro valor (o None), este se ignora.
DEFAULT_LIMIT_CHAPTERS = 2 

logging.basicConfig(level=logging.INFO)

# -----------------------------------------------------------------------------
# FUNCIONES AUXILIARES
# -----------------------------------------------------------------------------

def extract_text_from_file(file_path: str) -> str:
    """Extrae texto de PDF, DOCX o TXT."""
    try:
        extension = os.path.splitext(file_path)[1].lower()
        
        if extension == '.pdf':
            if not PDF_AVAILABLE: raise ImportError("pdfplumber no instalado")
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text += (page.extract_text() or "") + "\n"
            return text
        
        elif extension == '.docx':
            if not DOCX_AVAILABLE: raise ImportError("python-docx no instalado")
            doc = Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        
        elif extension == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        else:
            raise ValueError(f"Formato no soportado: {extension}")
            
    except Exception as e:
        logging.error(f"❌ Error extrayendo texto: {e}")
        raise

def smart_split(text: str, max_chars: int) -> list:
    """Divide texto largo en fragmentos respetando párrafos."""
    if len(text) <= max_chars: return [text]
    chunks = []
    while len(text) > max_chars:
        # Intentar cortar en doble salto de línea
        split_point = text.rfind('\n\n', 0, max_chars)
        if split_point == -1: split_point = text.rfind('\n', 0, max_chars)
        if split_point == -1: split_point = text.rfind('. ', 0, max_chars) + 1
        if split_point <= 0: split_point = max_chars # Corte forzoso si no hay signos
        
        chunks.append(text[:split_point].strip())
        text = text[split_point:].strip()
    if text: chunks.append(text)
    return chunks

def generate_hierarchical_metadata(chapters_raw: list) -> list:
    """Genera la estructura plana de fragmentos con metadatos."""
    final_list = []
    global_fragment_id = 1
    chapter_id = 1
    
    for chapter_data in chapters_raw:
        raw_title = chapter_data['title']
        content = chapter_data['content']
        section_type = chapter_data['section_type']
        
        # Si el contenido es muy largo, dividirlo
        if len(content) > MAX_CHARS_PER_CHUNK:
            sub_chunks = smart_split(content, MAX_CHARS_PER_CHUNK)
            total_frags = len(sub_chunks)
            for idx, chunk in enumerate(sub_chunks):
                final_list.append({
                    'id': global_fragment_id,
                    'parent_chapter_id': chapter_id,
                    'original_title': raw_title,
                    'title': f"{raw_title} ({idx + 1}/{total_frags})",
                    'fragment_index': idx + 1,
                    'total_fragments': total_frags,
                    'section_type': section_type,
                    'is_fragment': True,
                    'content': chunk,
                    'word_count': len(chunk.split())
                })
                global_fragment_id += 1
        else:
            final_list.append({
                'id': global_fragment_id,
                'parent_chapter_id': chapter_id,
                'original_title': raw_title,
                'title': raw_title,
                'fragment_index': 1,
                'total_fragments': 1,
                'section_type': section_type,
                'is_fragment': False,
                'content': content,
                'word_count': len(content.split())
            })
            global_fragment_id += 1
        chapter_id += 1
    return final_list

# -----------------------------------------------------------------------------
# MAIN FUNCTION (ACTIVITY TRIGGER)
# -----------------------------------------------------------------------------

def main(book_path) -> str:
    """
    Activity Function que recibe ruta o configuración y devuelve el libro segmentado.
    """
    try:
        logging.info("=" * 80)
        logging.info("🚀 SegmentBook (Activity) iniciado")
        
        # --- PASO 1: RECUPERAR CONFIGURACIÓN (LOGICA CORREGIDA) ---
        real_path = ""
        limit_chapters = DEFAULT_LIMIT_CHAPTERS # Valor inicial por defecto
        
        # Si el input es un diccionario (lo normal desde el orquestador)
        if isinstance(book_path, dict):
            real_path = book_path.get('book_path', '')
            
            # Si 'limit_chapters' existe en el diccionario, tiene prioridad absoluta
            # (Incluso si es None, que significa "procesar todo")
            if 'limit_chapters' in book_path:
                limit_chapters = book_path['limit_chapters']
                logging.info(f"⚙️ Límite establecido por Orquestador: {limit_chapters}")
            else:
                logging.info(f"⚙️ Usando límite por defecto local: {limit_chapters}")
                
        # Si el input es string (casos legacy o pruebas simples)
        elif isinstance(book_path, str):
            if book_path.strip().startswith('{'):
                try:
                    data = json.loads(book_path)
                    real_path = data.get('book_path', '')
                    if 'limit_chapters' in data:
                        limit_chapters = data['limit_chapters']
                except:
                    real_path = book_path
            else:
                real_path = book_path

        logging.info(f"📂 Config Final -> Archivo: {real_path} | Límite: {limit_chapters}")
        
        # --- PASO 2: LEER ARCHIVO ---
        script_dir = os.path.dirname(os.path.abspath(__file__))
        local_file_path = os.path.join(script_dir, 'Piel_Morena.docx')
        
        if not os.path.exists(local_file_path):
            raise FileNotFoundError(f"No encuentro el archivo: {local_file_path}")

        text = extract_text_from_file(local_file_path)
        
        # --- PASO 3: DETECTAR CAPÍTULOS (REGEX) ---
        special_keywords = r'(?:Prólogo|Prefacio|Introducción|Interludio|Epílogo|Nota para el editor)'
        full_pattern = f'(?mi)(?:^\\s*)(?:{special_keywords}|(?:Capítulo|Acto|Parte)\\s+)[^\n]*'
        original_chapters = re.split(f'(?={full_pattern})', text)
        
        chapters_raw = []
        for raw_chapter in original_chapters:
            if not raw_chapter.strip(): continue
            lines = raw_chapter.strip().split('\n')
            chapters_raw.append({
                'title': lines[0].strip(),
                'content': '\n'.join(lines[1:]),
                'section_type': "CHAPTER"
            })

        # --- PASO 4: APLICAR LÍMITE ---
        total_detected = len(chapters_raw)
        if limit_chapters is not None and isinstance(limit_chapters, int) and limit_chapters > 0:
            logging.warning(f"✂️ RECORTANDO LIBRO: Procesando solo los primeros {limit_chapters} de {total_detected} capítulos.")
            chapters_raw = chapters_raw[:limit_chapters]
        else:
            logging.info(f"✅ PROCESANDO LIBRO COMPLETO ({total_detected} capítulos).")

        # --- PASO 5: SEGMENTAR ---
        fragments = generate_hierarchical_metadata(chapters_raw) 

        # Crear mapa de capítulos para reconstrucción rápida
        chapter_map = {}
        for frag in fragments:
            p_id = frag['parent_chapter_id']
            if p_id not in chapter_map:
                chapter_map[p_id] = {'fragment_ids': [], 'original_title': frag['original_title']}
            chapter_map[p_id]['fragment_ids'].append(frag['id'])

        result = {
            'fragments': fragments,
            'book_metadata': {
                'total_chapters': len(chapter_map),
                'total_fragments': len(fragments),
                'source': real_path
            },
            'chapter_map': chapter_map
        }

        logging.warning(f"✅ Segmentación terminada. Total fragmentos: {len(fragments)}")
        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        logging.error(f"❌ Error Fatal en SegmentBook: {str(e)}")
        logging.error(traceback.format_exc())
        raise e
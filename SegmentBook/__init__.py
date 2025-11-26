import azure.functions as func
import regex as re
import json
import logging
import os
import pdfplumber
from docx import Document

MAX_CHARS_PER_CHUNK = 12000


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


def smart_split(text, max_chars):
    """
    Divide un texto largo en fragmentos más pequeños respetando los saltos de línea.
    """
    if len(text) <= max_chars:
        return [text]
    chunks = []
    remaining_text = text
    while len(remaining_text) > max_chars:
        split_point = remaining_text.rfind('\n', 0, max_chars)
        if split_point == -1:
            split_point = max_chars
        chunk = remaining_text[:split_point].strip()
        if chunk:
            chunks.append(chunk)
        remaining_text = remaining_text[split_point:].strip()
    if remaining_text:
        chunks.append(remaining_text)
    return chunks


def detect_section_type(title_line):
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


def main(book_path: str):
    """
    Función principal que segmenta un libro en capítulos.
    
    Args:
        book_path: Ruta al archivo del libro (.pdf, .docx, o .txt)
    
    Returns:
        Lista de diccionarios con los capítulos segmentados
    """
    try:
        # ============================================
        # EXTRAER TEXTO DEL ARCHIVO
        # ============================================
        sample_text = extract_text_from_file(book_path)
        
        logging.info(f"📖 Texto extraído: {len(sample_text)} caracteres")
        
        if len(sample_text.strip()) < 100:
            raise ValueError("El archivo parece estar vacío o tiene muy poco contenido")

        # ============================================
        # DEFINICIÓN DE PATRONES (REGEX MODULAR)
        # ============================================
        
        # GRUPO A: Narrativa Especial
        special_keywords = r'(?:Prólogo|Prefacio|Introducción|Interludio|Epílogo|Nota para el editor)'

        # GRUPO B: Estructura Mayor (Acto y Parte son equivalentes)
        acts_and_parts = r'(?:Acto|Parte)\s+(?:\d+|[IVXLCDM]+)'

        # GRUPO C: Capítulos y Variaciones
        chapter_variations = r'(?:Capítulo\s+(?:\d+|[IVXLCDM]+)|Final|\b[IVXLCDM]+\.?|\b\d+\.)'

        # ============================================
        # CONSTRUCCIÓN DEL REGEX MAESTRO
        # ============================================
        full_pattern = f'(?mi)(?:^\\s*)(?:{special_keywords}|{acts_and_parts}|{chapter_variations})[^\n]*'
        
        logging.info("🔍 Iniciando segmentación estandarizada...")

        # Usamos split con lookahead para mantener el título en el fragmento
        original_chapters = re.split(f'(?={full_pattern})', sample_text)
        
        final_list = []
        global_id = 1 

        for i, raw_chapter in enumerate(original_chapters):
            if not raw_chapter.strip():
                continue

            lines = raw_chapter.strip().split('\n')
            
            # Limpieza del título
            raw_title = lines[0].strip()
            
            # Lógica para detectar si el primer fragmento es el "Inicio" sin título
            if i == 0 and not re.match(full_pattern, raw_title):
                raw_title = "Inicio / Contexto"

            # ============================================
            # ESTANDARIZACIÓN DE TIPO
            # ============================================
            section_type = detect_section_type(raw_title)

            content = '\n'.join(lines[1:]) if len(lines) > 1 else ""
            
            # Si es el primer bloque y no tiene saltos de línea (caso borde)
            if i == 0 and content == "":
                content = raw_chapter 
                lines = raw_chapter.split('\n')
                raw_title = "Inicio / Contexto"

            # Filtro de contenido muy corto (basura o saltos de página erróneos)
            if len(content.split()) < 20: 
                continue

            # ============================================
            # LOGICA DE FRAGMENTACIÓN (CHUNKING)
            # ============================================
            is_fragmented = False
            sub_chunks = [content]

            if len(content) > MAX_CHARS_PER_CHUNK:
                logging.warning(f"⚠️ Fragmentando sección extensa: '{raw_title}'...")
                is_fragmented = True
                sub_chunks = smart_split(content, MAX_CHARS_PER_CHUNK)
                
            for idx, chunk in enumerate(sub_chunks):
                # Construimos el objeto final UNIFORME
                chapter_obj = {
                    'id': global_id,
                    'original_title': raw_title,
                    'section_type': section_type,
                    'content': chunk,
                    'word_count': len(chunk.split()),
                    'is_fragment': is_fragmented
                }

                if is_fragmented:
                    chapter_obj['fragment_index'] = f"{idx + 1}/{len(sub_chunks)}"
                    chapter_obj['title'] = f"{raw_title} ({idx + 1}/{len(sub_chunks)})"
                else:
                    chapter_obj['title'] = raw_title

                final_list.append(chapter_obj)
                global_id += 1

        # Log de resultados
        logging.info(f"✅ Se procesaron {len(final_list)} segmentos.")
        for item in final_list:
            logging.info(f"ID: {item['id']} | [{item['section_type']}] {item['title']} | Palabras: {item['word_count']}")

        return final_list
        
    except Exception as e:
        logging.error(f"❌ Error en SegmentBook: {str(e)}")
        raise e
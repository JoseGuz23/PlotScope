# =============================================================================
# MechanicalCorrection/__init__.py
# =============================================================================
# 
# Corrección mecánica con LanguageTool (ortografía, puntuación, gramática básica)
# Usa la API pública gratuita (con rate limiting) o servidor local
#
# =============================================================================

import logging
import os

logging.basicConfig(level=logging.INFO)


def main(chapter: dict) -> dict:
    """
    Aplica corrección mecánica a un capítulo usando LanguageTool.
    
    Input: {id, title, content}
    Output: {id, title, content (corregido), corrections_applied, corrections_count}
    """
    try:
        import language_tool_python
        
        chapter_id = chapter.get('id', '?')
        title = chapter.get('title', 'Sin título')
        content = chapter.get('content', '')
        
        if not content:
            return {
                **chapter,
                'corrections_applied': [],
                'corrections_count': 0,
                'mechanical_status': 'skipped_empty'
            }
        
        logging.info(f"🔧 Corrección mecánica: Cap {chapter_id} ({len(content)} chars)")
        
        # ─────────────────────────────────────────────────────────────────
        # CONFIGURACIÓN DE LANGUAGETOOL
        # ─────────────────────────────────────────────────────────────────
        
        # Detectar idioma del libro (puedes hacerlo configurable)
        # Por defecto español, pero puedes cambiarlo
        language = os.environ.get('BOOK_LANGUAGE', 'es')
        
        # Usar API pública (gratis pero con rate limiting)
        # Si tienes servidor propio, usa: LanguageTool('es', remote_server='tu-servidor')
        try:
            tool = language_tool_python.LanguageToolPublicAPI(language)
        except Exception:
            # Fallback a servidor local si la API pública falla
            tool = language_tool_python.LanguageTool(language)
        
        # ─────────────────────────────────────────────────────────────────
        # APLICAR CORRECCIONES
        # ─────────────────────────────────────────────────────────────────
        
        # Obtener matches (errores detectados)
        matches = tool.check(content)
        
        # Filtrar correcciones que queremos aplicar automáticamente
        # (solo las más seguras: ortografía, puntuación básica)
        safe_corrections = []
        
        SAFE_RULES = [
            'TYPOS',
            'MORFOLOGIK_RULE',  # Ortografía
            'PUNCTUATION',
            'COMMA_',
            'WHITESPACE',
            'UPPERCASE_SENTENCE_START',
            'DOUBLE_PUNCTUATION',
        ]
        
        for match in matches:
            rule_id = match.ruleId
            
            # Solo aplicar reglas seguras
            is_safe = any(safe in rule_id for safe in SAFE_RULES)
            
            if is_safe and match.replacements:
                safe_corrections.append({
                    'offset': match.offset,
                    'length': match.errorLength,
                    'original': content[match.offset:match.offset + match.errorLength],
                    'replacement': match.replacements[0],  # Primera sugerencia
                    'rule': rule_id,
                    'message': match.message
                })
        
        # Aplicar correcciones (de atrás hacia adelante para no romper offsets)
        corrected_content = content
        applied = []
        
        for correction in sorted(safe_corrections, key=lambda x: x['offset'], reverse=True):
            start = correction['offset']
            end = start + correction['length']
            
            # Aplicar corrección
            corrected_content = (
                corrected_content[:start] + 
                correction['replacement'] + 
                corrected_content[end:]
            )
            
            applied.append({
                'original': correction['original'],
                'corrected': correction['replacement'],
                'rule': correction['rule']
            })
        
        logging.info(f"✅ Cap {chapter_id}: {len(applied)} correcciones aplicadas")
        
        return {
            'id': chapter_id,
            'title': title,
            'content': corrected_content,
            'original_content': content,  # Guardar original por si acaso
            'corrections_applied': applied,
            'corrections_count': len(applied),
            'mechanical_status': 'success'
        }
        
    except ImportError:
        logging.warning(f"⚠️ language_tool_python no instalado, saltando corrección mecánica")
        return {
            **chapter,
            'corrections_applied': [],
            'corrections_count': 0,
            'mechanical_status': 'skipped_no_library'
        }
    except Exception as e:
        logging.error(f"❌ Error en corrección mecánica: {str(e)}")
        return {
            **chapter,
            'corrections_applied': [],
            'corrections_count': 0,
            'mechanical_status': 'error',
            'error': str(e)
        }
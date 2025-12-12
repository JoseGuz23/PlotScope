# =============================================================================
# GenerateEditorialLetter/__init__.py - LYA 7.1 (Opus 4.5 Native)
# =============================================================================
# ESTRATEGIA: Muestreo Híbrido + Razonamiento Profundo (Opus 4.5)
#
# CAMBIOS LYA 7.1:
# - Implementación nativa de Claude Opus 4.5 (2025-11-01)
# - Activación del parámetro 'effort="high"' para máxima profundidad editorial
# - Inclusión de headers beta obligatorios
# =============================================================================

import logging
import json
import os
import anthropic

logging.basicConfig(level=logging.INFO)

EDITORIAL_LETTER_PROMPT = """Eres un DEVELOPMENTAL EDITOR de clase mundial (nivel de Maxwell Perkins).
Estás editando la novela "{titulo}".

TU OBJETIVO: Escribir una Carta Editorial que analice tanto la estructura macro como la ejecución estilística.

═══════════════════════════════════════════════════════════════════════════════
INFORMACIÓN DE CONTEXTO (LA VERDAD DE LA HISTORIA)
═══════════════════════════════════════════════════════════════════════════════
BIBLIA NARRATIVA:
{biblia}

═══════════════════════════════════════════════════════════════════════════════
ESTRUCTURA DEL MANUSCRITO (MUESTREO INTELIGENTE)
═══════════════════════════════════════════════════════════════════════════════
NOTA PARA EL EDITOR: Debido a la longitud de la obra, se te presenta el manuscrito en el siguiente formato híbrido:
1. INICIO: Texto completo (para evaluar el gancho y establecimiento de tono).
2. DESARROLLO: Sinopsis detalladas capítulo a capítulo (para evaluar ritmo y trama).
3. FINAL: Texto completo (para evaluar la resolución y payoff emocional).

--- MANUSCRITO HÍBRIDO ---
{manuscrito_hibrido}

═══════════════════════════════════════════════════════════════════════════════
INSTRUCCIONES DE REDACCIÓN
═══════════════════════════════════════════════════════════════════════════════
Escribe una carta editorial cálida, brutalmente honesta pero constructiva.
Tono: Un editor veterano escribiendo a su autor estrella en 1978.

REGLAS ABSOLUTAS DE ESTILO:
- NO uses emojis.
- NO uses formato Markdown de títulos (##) ni negritas (**).
- NO uses listas con viñetas. Escribe en párrafos de prosa fluida.
- NO suenes como una IA. Evita "En conclusión", "En resumen", "Tu libro tiene potencial".
- Céntrate en la experiencia emocional del lector.

TU CARTA DEBE CUBRIR:
1. La primera impresión (basada en el texto completo del inicio).
2. La solidez de la trama central y el "sagging middle" (basado en los resúmenes del desarrollo).
3. La satisfacción del final (basada en el texto completo del desenlace).
4. La evolución de los personajes a través del arco completo.

Longitud esperada: 2000+ palabras.
"""

def build_smart_manuscript(fragments: list, consolidated: list) -> str:
    """
    Construye un manuscrito híbrido.
    Prioriza texto real al inicio y al final, y resúmenes en el medio.
    """
    if not fragments:
        return "Manuscrito vacío."

    # Ordenar por secuencia
    fragments.sort(key=lambda x: x.get('sequence', x.get('id', 0)))
    total_frags = len(fragments)
    
    # Definir zonas (porcentajes aproximados)
    # Inicio: Primer 15% / Fin: Último 10%
    cutoff_start = max(1, int(total_frags * 0.15))
    cutoff_end = max(1, int(total_frags * 0.10))
    start_index_end = total_frags - cutoff_end
    
    hybrid_text = []
    
    # 1. PROCESAR INICIO (TEXTO COMPLETO)
    hybrid_text.append("--- SECCIÓN 1: INICIO (TEXTO COMPLETO) ---")
    for frag in fragments[:cutoff_start]:
        title = frag.get('title', f"Cap {frag.get('id')}")
        content = frag.get('content', '')
        hybrid_text.append(f"\n### {title}\n{content}")

    # 2. PROCESAR MEDIO (RESÚMENES / SINOPSIS)
    hybrid_text.append("\n\n--- SECCIÓN 2: DESARROLLO (SINOPSIS ESTRUCTURALES) ---")
    hybrid_text.append("(Nota: Analiza el ritmo y la causalidad basándote en estos eventos)")
    
    for frag in fragments[cutoff_start:start_index_end]:
        frag_id = str(frag.get('id'))
        title = frag.get('title', f"Cap {frag_id}")
        
        # Buscar análisis correspondiente en consolidated
        analysis = next((c for c in consolidated if str(c.get('chapter_id')) == frag_id), None)
        
        synopsis = "Sinopsis no disponible."
        if analysis:
            l1 = analysis.get('layer1_factual', {})
            l2 = analysis.get('layer2_structural', {})
            synopsis = l1.get('summary') or l2.get('synopsis') or l1.get('one_line_summary') or "Sinopsis no generada."
        
        hybrid_text.append(f"\n### {title} [RESUMEN]\n{synopsis}")
        
        if analysis and 'layer2_structural' in analysis:
            beat = analysis['layer2_structural'].get('narrative_function', '')
            hybrid_text.append(f"[Función Narrativa: {beat}]")

    # 3. PROCESAR FINAL (TEXTO COMPLETO)
    hybrid_text.append("\n\n--- SECCIÓN 3: RESOLUCIÓN (TEXTO COMPLETO) ---")
    for frag in fragments[start_index_end:]:
        title = frag.get('title', f"Cap {frag.get('id')}")
        content = frag.get('content', '')
        hybrid_text.append(f"\n### {title}\n{content}")

    return "\n".join(hybrid_text)


def main(input_data: dict) -> dict:
    """
    Genera la carta editorial usando Claude Opus 4.5 con parámetro 'effort'.
    """
    try:
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            return {"error": "ANTHROPIC_API_KEY no configurada", "status": "config_error"}

        client = anthropic.Anthropic(api_key=api_key)

        bible = input_data.get('bible', {})
        consolidated = input_data.get('consolidated_chapters', [])
        fragments = input_data.get('fragments', [])
        book_metadata = input_data.get('book_metadata', {})

        titulo = book_metadata.get('title', bible.get('identidad_obra', {}).get('titulo', 'Sin título'))

        logging.info(f"📝 Generando Carta Editorial Híbrida para: {titulo}")
        logging.info(f"🚀 Modelo: Claude Opus 4.5 | Effort: High")

        # 1. CONSTRUCCIÓN DEL MANUSCRITO HÍBRIDO
        manuscrito_hibrido = build_smart_manuscript(fragments, consolidated)
        
        logging.info(f"📊 Manuscrito híbrido construido. Longitud: {len(manuscrito_hibrido):,} chars")

        # 2. PREPARAR BIBLIA
        bible_str = json.dumps(bible, ensure_ascii=False, indent=2)
        if len(bible_str) > 60000:
            logging.warning("⚠️ Biblia muy extensa, aplicando recorte seguro.")
            bible_str = bible_str[:60000] + "\n...(biblia truncada)..."

        # 3. CONSTRUIR PROMPT
        prompt = EDITORIAL_LETTER_PROMPT.format(
            titulo=titulo,
            biblia=bible_str,
            manuscrito_hibrido=manuscrito_hibrido
        )

        # 4. LLAMADA A CLAUDE OPUS 4.5
        # NOTA: Se añade el header 'effort-2025-11-24' y el parámetro effort='high'
        # para activar el razonamiento profundo según documentación técnica.
        
        logging.info(f"🔄 Invocando Opus 4.5...")
        
        response = client.messages.create(
            model='claude-opus-4-5-20251101',
            max_tokens=6000, # Aumentado para permitir respuestas más profundas de Opus 4.5
            temperature=0.7,
            messages=[
                {"role": "user", "content": prompt}
            ],
            # Parametros exclusivos de Opus 4.5
            extra_headers={
                "anthropic-beta": "effort-2025-11-24"
            },
            extra_body={
                "effort": "high" # Garantiza máxima exhaustividad
            },
            timeout=1800.0 # 30 min timeout para razonamiento extendido
        )

        logging.info(f"✅ Respuesta recibida")

        if not response or not response.content:
            return {"error": "Respuesta vacía", "status": "error"}

        carta_markdown = response.content[0].text

        return {
            "status": "success",
            "carta_editorial": {
                "texto_completo": carta_markdown
            },
            "carta_markdown": carta_markdown,
            "metadata": {
                "longitud_generada": len(carta_markdown),
                "modelo": "claude-opus-4-5-20251101",
                "effort_level": "high",
                "metodo": "smart_hybrid_context"
            }
        }

    except Exception as e:
        logging.error(f"❌ Error crítico: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return {"error": str(e), "status": "error"}
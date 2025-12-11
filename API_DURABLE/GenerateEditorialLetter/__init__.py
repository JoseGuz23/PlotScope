# =============================================================================
# GenerateEditorialLetter/__init__.py - SYLPHRENA 5.0
# =============================================================================
# NUEVA FUNCIÓN: Genera una carta editorial profesional de 8-15 páginas
# como la que entregaría un developmental editor ($1,500-3,000)
# =============================================================================

import logging
import json
import os

logging.basicConfig(level=logging.INFO)

EDITORIAL_LETTER_PROMPT = """Eres un DEVELOPMENTAL EDITOR. Tu OBJETIVO: Convertir los datos técnicos y el borrador de {titulo} en una CARTA EDITORIAL profunda, constructiva y orientada a la excelencia narrativa.

Tu tarea es escribir una CARTA EDITORIAL profesional, como las que escriben editores reales a sus autores.

═══════════════════════════════════════════════════════════════════════════════
INFORMACIÓN DEL ANÁLISIS PREVIO:
═══════════════════════════════════════════════════════════════════════════════

BIBLIA NARRATIVA:
{biblia}

ANÁLISIS DE CAPAS (FACTUAL, ESTRUCTURAL, CUALITATIVO):
{analisis_capas}

═══════════════════════════════════════════════════════════════════════════════
MANUSCRITO COMPLETO:
═══════════════════════════════════════════════════════════════════════════════
{manuscrito}

═══════════════════════════════════════════════════════════════════════════════
INSTRUCCIONES CRÍTICAS:
═══════════════════════════════════════════════════════════════════════════════

Escribe una CARTA EDITORIAL auténtica y profesional. Debe sonar como si la hubiera escrito un editor humano experimentado, NO como un reporte de IA.

FORMATO Y TONO:
- Escribe en PROSA CONTINUA, como una carta real
- NO uses emojis bajo ninguna circunstancia
- NO uses secciones numeradas (1., 2., 3., etc.)
- NO uses subtítulos con formato markdown (##, ###)
- Usa párrafos naturales de prosa, como escribirías un email profesional largo
- Tono: Cálido, honesto, directo pero respetuoso
- Segunda persona ("tu manuscrito", "has logrado", "te sugiero")

ESTRUCTURA GENERAL (pero en PROSA, no en secciones):
La carta debe fluir naturalmente cubriendo estos temas EN PÁRRAFOS:

1. SALUDO Y PRIMERAS IMPRESIONES (2-3 párrafos)
   - Saludo cordial al autor
   - Agradecimiento por la oportunidad de leer el manuscrito
   - Impresión general positiva (siempre empieza con lo bueno)
   - Breve sinopsis que demuestre que leíste TODO

2. FORTALEZAS PRINCIPALES (3-5 párrafos)
   - Qué funciona excepcionalmente bien
   - Momentos específicos que brillan (con ejemplos)
   - Voz única del autor que debe preservar
   - Personajes memorables y por qué

3. ÁREAS DE MEJORA (5-8 párrafos)
   - Para cada problema: descripción clara, por qué importa, ejemplo específico, sugerencia concreta
   - Cubre: estructura, personajes, arcos, diálogos, prosa, consistencia
   - Prioriza problemas (menciona cuáles son más urgentes)

4. PERSONAJES Y ARCOS (2-4 párrafos)
   - Análisis de personajes principales
   - Arcos narrativos (qué funciona, qué necesita trabajo)
   - Sugerencias específicas de desarrollo

5. ESTRUCTURA Y PACING (1-3 párrafos)
   - Evaluación del ritmo narrativo
   - Puntos de giro y su efectividad
   - Problemas estructurales si existen

6. NOTAS POR CAPÍTULO (1-2 párrafos o lista breve)
   - Breve resumen de qué revisar en cada capítulo
   - Puede ser una lista simple: "Capítulo 1: [nota breve]"

7. PRÓXIMOS PASOS Y CIERRE (2-3 párrafos)
   - Top 3-5 prioridades para la siguiente revisión
   - Orden sugerido de trabajo
   - Qué NO debe cambiar
   - Mensaje de aliento y firma

EJEMPLOS DE TONO CORRECTO:
- "He pasado las últimas semanas sumergida en tu manuscrito, y quiero empezar diciéndote que..."
- "La forma en que construyes tensión en el capítulo 3 es excepcional. Cuando Sam descubre..."
- "Hay un problema de consistencia que necesitamos abordar. En el capítulo 2, mencionas que... pero luego en el capítulo 5..."
- "Te sugiero que revises la motivación de [personaje] en la escena donde..."
- "Esto es una prioridad alta porque afecta directamente la credibilidad de..."

EJEMPLOS DE LO QUE NO DEBES HACER:
- ❌ "## 1. RESUMEN EJECUTIVO"  →  En su lugar: Párrafo de introducción
- ❌ "✨ Atmósfera y Tono"  →  En su lugar: "La atmósfera que logras crear es..."
- ❌ "🔴 ALTA PRIORIDAD"  →  En su lugar: "Esto es una prioridad alta..."
- ❌ Blockquotes con >  →  En su lugar: Integra las citas en el texto naturalmente

LONGITUD: 1500-2500 palabras (aproximadamente 8-12 páginas de carta real)

Escribe la carta completa como TEXTO PLANO EN MARKDOWN SIMPLE, sin estructura JSON.
"""


def main(input_data: dict) -> dict:
    """
    Genera la carta editorial usando Gemini Pro.
    
    Input:
        - bible: Biblia narrativa completa
        - consolidated_chapters: Análisis consolidados por capítulo
        - fragments: Fragmentos originales del manuscrito
        - book_metadata: Metadatos del libro
    
    Output:
        - carta_editorial: JSON estructurado con toda la carta
        - carta_markdown: Versión en Markdown para exportar
    """
    
    try:
        import google.generativeai as genai
        
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return {"error": "GEMINI_API_KEY no configurada", "status": "config_error"}
        
        genai.configure(api_key=api_key)
        
        bible = input_data.get('bible', {})
        consolidated = input_data.get('consolidated_chapters', [])
        fragments = input_data.get('fragments', [])
        book_metadata = input_data.get('book_metadata', {})
        
        titulo = book_metadata.get('title', bible.get('identidad_obra', {}).get('titulo', 'Sin título'))
        
        # Construir manuscrito resumido (primeros 500 chars por capítulo para contexto)
        manuscrito_resumen = []
        for frag in fragments:
            cap_title = frag.get('title', frag.get('original_title', 'Capítulo'))
            content = frag.get('content', '')[:2000]  # Primeros 2000 chars
            manuscrito_resumen.append(f"### {cap_title}\n{content}...")
        
        manuscrito_text = "\n\n".join(manuscrito_resumen)
        
        # Resumir análisis de capas
        analisis_resumen = []
        for ch in consolidated[:10]:  # Primeros 10 capítulos
            ch_id = ch.get('chapter_id', '?')
            analisis_resumen.append(f"Cap {ch_id}: {json.dumps(ch, ensure_ascii=False)[:500]}...")
        
        analisis_text = "\n".join(analisis_resumen)
        
        prompt = EDITORIAL_LETTER_PROMPT.format(
            titulo=titulo,
            biblia=json.dumps(bible, ensure_ascii=False, indent=2)[:8000],
            analisis_capas=analisis_text,
            manuscrito=manuscrito_text[:30000]  # Límite de contexto
        )
        
        logging.info(f"📝 Generando Carta Editorial para: {titulo}")
        logging.info(f"📊 Prompt size: {len(prompt):,} chars")

        # Usar Gemini 3 Pro (el más avanzado disponible)
        try:
            model = genai.GenerativeModel('gemini-3-pro-preview')
            logging.info(f"✅ Modelo Gemini 3 Pro inicializado")
        except Exception as e:
            logging.error(f"❌ Error inicializando modelo Gemini: {e}")
            raise

        generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "max_output_tokens": 16000,
            "response_mime_type": "text/plain"
        }

        logging.info(f"🔄 Llamando a Gemini API...")
        response = model.generate_content(prompt, generation_config=generation_config)
        logging.info(f"✅ Respuesta recibida de Gemini")

        # Validar respuesta
        if not response or not hasattr(response, 'text'):
            logging.error(f"❌ Respuesta de Gemini inválida o vacía")
            return {"error": "Respuesta de Gemini vacía", "status": "error"}

        carta_markdown = response.text
        logging.info(f"📄 Carta Editorial generada: {len(carta_markdown):,} chars")

        if not carta_markdown or len(carta_markdown) < 500:
            logging.error(f"❌ Carta muy corta: {carta_markdown[:200]}")
            return {"error": "Carta demasiado corta", "status": "error", "raw_response": carta_markdown}

        logging.info(f"✅ Carta Editorial generada exitosamente")

        # Devolver en formato simple (carta_editorial como objeto vacío para compatibilidad)
        return {
            "status": "success",
            "carta_editorial": {
                "texto_completo": carta_markdown
            },
            "carta_markdown": carta_markdown,
            "metadata": {
                "longitud_caracteres": len(carta_markdown),
                "longitud_palabras": len(carta_markdown.split())
            }
        }
        
    except ImportError as e:
        logging.error(f"❌ SDK no instalado: {e}")
        return {"error": str(e), "status": "import_error"}
    except Exception as e:
        logging.error(f"❌ Error generando carta editorial: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return {"error": str(e), "status": "error"}


# DEPRECATED: Ya no usamos esta función, Gemini genera el texto directo
def generate_markdown_version_DEPRECATED(carta: dict, titulo: str) -> str:
    """Convierte la carta estructurada a Markdown legible."""
    
    md = []
    md.append(f"# 📖 CARTA EDITORIAL: {titulo}")
    md.append(f"\n*Sylphrena Developmental Editor*\n")
    md.append("---\n")
    
    # Resumen Ejecutivo
    resumen = carta.get('resumen_ejecutivo', {})
    md.append("## 1. RESUMEN EJECUTIVO\n")
    if resumen.get('felicitacion'):
        md.append(f"{resumen['felicitacion']}\n")
    if resumen.get('sinopsis'):
        md.append(f"\n### Sinopsis\n{resumen['sinopsis']}\n")
    if resumen.get('evaluacion_general'):
        md.append(f"\n### Evaluación General\n{resumen['evaluacion_general']}\n")
    if resumen.get('potencial_mercado'):
        md.append(f"\n### Potencial de Mercado\n{resumen['potencial_mercado']}\n")
    
    # Lo que funciona
    funciona = carta.get('lo_que_funciona', {})
    md.append("\n---\n## 2. LO QUE FUNCIONA\n")
    
    for f in funciona.get('fortalezas_narrativas', []):
        md.append(f"\n### ✨ {f.get('aspecto', '')}")
        if f.get('ejemplo_texto'):
            md.append(f"\n> \"{f['ejemplo_texto']}\"")
        md.append(f"\n{f.get('por_que_funciona', '')}\n")
    
    momentos = funciona.get('momentos_memorables', [])
    if momentos:
        md.append("\n### 🌟 Momentos Memorables\n")
        for m in momentos:
            md.append(f"- **{m.get('escena', '')}** (Cap. {m.get('capitulo', '?')}): {m.get('impacto', '')}")
    
    # Áreas de oportunidad
    areas = carta.get('areas_de_oportunidad', [])
    md.append("\n---\n## 3. ÁREAS DE OPORTUNIDAD\n")
    
    for i, area in enumerate(areas, 1):
        prioridad_emoji = "🔴" if area.get('prioridad') == 'ALTA' else "🟡" if area.get('prioridad') == 'MEDIA' else "🟢"
        md.append(f"\n### {i}. {prioridad_emoji} {area.get('categoria', '').upper()}: {area.get('problema', '')[:50]}")
        md.append(f"\n**Problema:** {area.get('problema', '')}")
        md.append(f"\n**Por qué importa:** {area.get('por_que_importa', '')}")
        if area.get('ejemplo_texto'):
            md.append(f"\n**Ejemplo (Cap. {area.get('capitulo_ejemplo', '?')}):**\n> \"{area['ejemplo_texto']}\"")
        md.append(f"\n**💡 Sugerencia:** {area.get('sugerencia', '')}")
        md.append(f"\n**Prioridad:** {area.get('prioridad', 'MEDIA')}\n")
    
    # Análisis de personajes
    personajes = carta.get('analisis_personajes', [])
    md.append("\n---\n## 4. ANÁLISIS DE PERSONAJES\n")
    
    for p in personajes:
        md.append(f"\n### 👤 {p.get('nombre', 'Personaje')} ({p.get('rol', '')})")
        
        arco = p.get('arco_actual', {})
        if arco:
            md.append(f"\n**Arco:** {arco.get('inicio', '')} → {arco.get('desarrollo', '')} → {arco.get('fin', '')}")
        
        if p.get('fortalezas'):
            md.append(f"\n**Fortalezas:** {', '.join(p['fortalezas'])}")
        if p.get('problemas'):
            md.append(f"\n**Problemas:** {', '.join(p['problemas'])}")
        if p.get('sugerencias'):
            md.append(f"\n**Sugerencias:** {', '.join(p['sugerencias'])}")
        if p.get('cita_voz'):
            md.append(f"\n> \"{p['cita_voz']}\"")
        md.append("")
    
    # Estructura
    estructura = carta.get('analisis_estructura', {})
    md.append("\n---\n## 5. ANÁLISIS DE ESTRUCTURA\n")
    md.append(f"\n**Modelo Narrativo:** {estructura.get('modelo_narrativo', 'No identificado')}\n")
    
    puntos = estructura.get('puntos_de_giro', [])
    if puntos:
        md.append("\n### Puntos de Giro\n")
        for pt in puntos:
            md.append(f"- **{pt.get('nombre', '')}** (Cap. {pt.get('capitulo', '?')}): {pt.get('efectividad', '')}")
    
    pacing = estructura.get('pacing', {})
    if pacing:
        md.append(f"\n### Pacing\n{pacing.get('evaluacion', '')}")
    
    # Notas por capítulo
    notas = carta.get('notas_por_capitulo', [])
    md.append("\n---\n## 6. NOTAS POR CAPÍTULO\n")
    
    for n in notas:
        prioridad_emoji = "🔴" if n.get('prioridad') == 'ALTA' else "🟡" if n.get('prioridad') == 'MEDIA' else "🟢"
        md.append(f"\n### Cap. {n.get('capitulo', '?')}: {n.get('titulo', '')} {prioridad_emoji}")
        md.append(f"- **Función:** {n.get('funcion', '')}")
        md.append(f"- **✓ Funciona:** {n.get('que_funciona', '')}")
        md.append(f"- **⚠ Mejorar:** {n.get('que_mejorar', '')}")
    
    # Próximos pasos
    pasos = carta.get('proximos_pasos', {})
    md.append("\n---\n## 7. PRÓXIMOS PASOS\n")
    
    if pasos.get('top_5_prioridades'):
        md.append("\n### 🎯 Top 5 Prioridades\n")
        for i, p in enumerate(pasos['top_5_prioridades'], 1):
            md.append(f"{i}. {p}")
    
    if pasos.get('no_cambiar'):
        md.append("\n### 🔒 NO Cambiar\n")
        for nc in pasos['no_cambiar']:
            md.append(f"- {nc}")
    
    if pasos.get('mensaje_final'):
        md.append(f"\n---\n\n*{pasos['mensaje_final']}*")
    
    md.append("\n\n---\n*Generado por Sylphrena 5.0 - AI Developmental Editor*")
    
    return "\n".join(md)

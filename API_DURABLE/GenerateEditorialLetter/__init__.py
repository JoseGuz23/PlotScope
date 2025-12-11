# =============================================================================
# GenerateEditorialLetter/__init__.py - SYLPHRENA 5.0 (UPDATED SDK)
# =============================================================================

import logging
import json
import os
# ACTUALIZACIÓN: Importamos el SDK nuevo para compatibilidad con el entorno
from google import genai
from google.genai import types

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

LONGITUD: 1500-2500 palabras (aproximadamente 8-12 páginas de carta real)

Escribe la carta completa como TEXTO PLANO EN MARKDOWN SIMPLE, sin estructura JSON.
"""


def main(input_data: dict) -> dict:
    """
    Genera la carta editorial usando Gemini Pro (SDK v1.0).
    """
    
    try:
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return {"error": "GEMINI_API_KEY no configurada", "status": "config_error"}
        
        # Inicialización con el nuevo SDK
        client = genai.Client(api_key=api_key)
        
        bible = input_data.get('bible', {})
        consolidated = input_data.get('consolidated_chapters', [])
        fragments = input_data.get('fragments', [])
        book_metadata = input_data.get('book_metadata', {})
        
        titulo = book_metadata.get('title', bible.get('identidad_obra', {}).get('titulo', 'Sin título'))
        
        # Construir manuscrito resumido
        manuscrito_resumen = []
        for frag in fragments:
            cap_title = frag.get('title', frag.get('original_title', 'Capítulo'))
            content = frag.get('content', '')[:2000]
            manuscrito_resumen.append(f"### {cap_title}\n{content}...")
        
        manuscrito_text = "\n\n".join(manuscrito_resumen)
        
        # Resumir análisis de capas
        analisis_resumen = []
        for ch in consolidated[:10]:
            ch_id = ch.get('chapter_id', '?')
            analisis_resumen.append(f"Cap {ch_id}: {json.dumps(ch, ensure_ascii=False)[:500]}...")
        
        analisis_text = "\n".join(analisis_resumen)
        
        prompt = EDITORIAL_LETTER_PROMPT.format(
            titulo=titulo,
            biblia=json.dumps(bible, ensure_ascii=False, indent=2)[:8000],
            analisis_capas=analisis_text,
            manuscrito=manuscrito_text[:30000]
        )
        
        logging.info(f"📝 Generando Carta Editorial para: {titulo}")

        # Configuración usando types (nuevo SDK)
        generation_config = types.GenerateContentConfig(
            temperature=0.7,
            top_p=0.95,
            max_output_tokens=16000,
            response_mime_type="text/plain"
        )

        logging.info(f"🔄 Llamando a Gemini API...")
        
        # Llamada con el cliente nuevo
        # Mantenemos 'gemini-3-pro-preview' como solicitaste
        response = client.models.generate_content(
            model='gemini-3-pro-preview',
            contents=prompt,
            config=generation_config
        )
        
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
        
    except Exception as e:
        logging.error(f"❌ Error generando carta editorial: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return {"error": str(e), "status": "error"}
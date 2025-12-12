# =============================================================================
# GenerateEditorialLetter/__init__.py - LYA 6.0 (CLAUDE OPUS 4.1)
# =============================================================================

import logging
import json
import os
import anthropic

logging.basicConfig(level=logging.INFO)

EDITORIAL_LETTER_PROMPT = """Eres un DEVELOPMENTAL EDITOR. Tu OBJETIVO: Convertir los datos técnicos y el borrador de {titulo} en una CARTA EDITORIAL profunda, constructiva y orientada a la excelencia narrativa.

Tu tarea es escribir una CARTA EDITORIAL profesional, como las que escriben editores reales a sus autores.

---

INFORMACIÓN DEL ANÁLISIS PREVIO:

BIBLIA NARRATIVA:
{biblia}

ANÁLISIS DE CAPAS (FACTUAL, ESTRUCTURAL, CUALITATIVO):
{analisis_capas}

---

MANUSCRITO COMPLETO:
{manuscrito}

---

INSTRUCCIONES CRÍTICAS:

Escribe una CARTA EDITORIAL auténtica y profesional. Debe sonar como si la hubiera escrito un editor humano experimentado en 1978, NO como un reporte de IA o documento técnico.

FORMATO Y TONO:

IMPORTANTE: Esta carta la leerá un ser humano. NO debe sonar como si la escribió una IA.

LO QUE NO DEBES HACER JAMÁS (ejemplos específicos que DELATAN que eres IA):
- NO uses emojis (ni ⭐, ni ✨, ni 📚, ni NINGÚN emoji)
- NO uses asteriscos dobles para negritas: **Los puntos fuertes** ← NUNCA HAGAS ESTO
- NO uses guiones largos decorativos: ═══ o --- o ___
- NO uses bullet points con símbolos: •, *, -, →
- NO uses frases típicas de IA como:
  * "tu libro tiene potencial para ser un gran libro —Aunque ya lo es—"
  * "esto es solo el comienzo de algo increíble"
  * "con un poco más de trabajo, esto brillará"
  * "has logrado algo verdaderamente especial"
- NO uses secciones con subtítulos markdown (##, ###)
- NO uses listas numeradas (1., 2., 3.)
- NO seas excesivamente positivo/optimista de forma artificial

LO QUE SÍ DEBES HACER:
- Escribe en PROSA CONTINUA, párrafo tras párrafo, como una carta mecanografiada en 1978
- Usa segunda persona ("tu manuscrito", "has construido", "te recomiendo")
- Tono: Honesto, directo, respetuoso, como un editor veterano que ha visto miles de manuscritos
- Si necesitas separar secciones, usa simplemente un salto de párrafo doble
- Si necesitas enfatizar, usa MAYÚSCULAS OCASIONALES, nunca negritas
- Sé específico y concreto, menciona escenas o momentos particulares del manuscrito
- Equilibra crítica constructiva con reconocimiento genuino (no falso entusiasmo)

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
    Genera la carta editorial usando Claude Opus 4.1.
    """

    try:
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            return {"error": "ANTHROPIC_API_KEY no configurada", "status": "config_error"}

        # Inicialización del cliente de Anthropic
        client = anthropic.Anthropic(api_key=api_key)

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
        logging.info(f"🔄 Llamando a Claude Opus 4.1 API...")

        # Llamada a Claude Opus 4.1
        response = client.messages.create(
            model='claude-opus-4-1-20250805',
            max_tokens=16000,
            temperature=0.7,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        logging.info(f"✅ Respuesta recibida de Claude")

        # Validar respuesta
        if not response or not response.content or len(response.content) == 0:
            logging.error(f"❌ Respuesta de Claude inválida o vacía")
            return {"error": "Respuesta de Claude vacía", "status": "error"}

        carta_markdown = response.content[0].text
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
                "longitud_palabras": len(carta_markdown.split()),
                "modelo": "claude-opus-4.1"
            }
        }

    except Exception as e:
        logging.error(f"❌ Error generando carta editorial: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return {"error": str(e), "status": "error"}
# =============================================================================
# SubmitMarginNotes/__init__.py - LYA 5.0
# =============================================================================
# NUEVA FUNCIÓN: Genera "notas de margen" como las de un editor profesional
# Comentarios tipo: "Aquí el lector se pierde", "Este diálogo suena forzado"
# =============================================================================

import logging
import json
import os

logging.basicConfig(level=logging.INFO)

MARGIN_NOTES_PROMPT = """Eres un EDITOR PROFESIONAL revisando el capítulo "{titulo}" de "{libro}".

Tu tarea es generar NOTAS DE MARGEN como las que un developmental editor escribe mientras lee. Estas son observaciones que van más allá de correcciones de texto - son comentarios sobre narrativa, personajes, ritmo y experiencia del lector.

═══════════════════════════════════════════════════════════════════════════════
CONTEXTO EDITORIAL (de la carta editorial):
═══════════════════════════════════════════════════════════════════════════════
{contexto_editorial}

═══════════════════════════════════════════════════════════════════════════════
INFORMACIÓN DEL CAPÍTULO:
═══════════════════════════════════════════════════════════════════════════════
Posición: {posicion}
Función narrativa: {funcion}
Personajes presentes: {personajes}

═══════════════════════════════════════════════════════════════════════════════
TEXTO DEL CAPÍTULO:
═══════════════════════════════════════════════════════════════════════════════
{contenido}

═══════════════════════════════════════════════════════════════════════════════
TIPOS DE NOTAS A GENERAR:
═══════════════════════════════════════════════════════════════════════════════

1. **PACING**: Donde el ritmo no funciona
   - "Este párrafo ralentiza la acción en un momento de tensión"
   - "La escena termina abruptamente sin resolución emocional"

2. **PERSONAJE**: Inconsistencias o oportunidades
   - "Esta reacción no cuadra con lo establecido de [nombre]"
   - "Oportunidad de mostrar más de su conflicto interno"

3. **DIALOGO**: Problemas de naturalidad
   - "Este intercambio suena expositivo - los personajes están explicando para el lector"
   - "Las voces de ambos personajes suenan iguales aquí"

4. **CLARIDAD**: Donde el lector puede perderse
   - "La geografía de la escena no está clara"
   - "¿Cuánto tiempo ha pasado desde la escena anterior?"

5. **EMOCION**: Oportunidades de profundizar
   - "Aquí podríamos sentir más lo que [nombre] está experimentando"
   - "El momento pide más peso emocional"

6. **VOZ**: Inconsistencias de tono o estilo
   - "Este párrafo rompe con el tono establecido"
   - "La metáfora no encaja con el registro del narrador"

7. **TENSION**: Problemas de stakes o conflicto
   - "El conflicto se resuelve demasiado fácil"
   - "¿Qué está en juego aquí para el protagonista?"

8. **SHOW_TELL**: Oportunidades de mostrar en vez de contar
   - "Estás contando la emoción en vez de mostrarla"
   - "El narrador explica lo que la acción ya demostró"

═══════════════════════════════════════════════════════════════════════════════
INSTRUCCIONES:
═══════════════════════════════════════════════════════════════════════════════

1. Lee el capítulo COMPLETO
2. Identifica 5-15 puntos donde un editor dejaría una nota
3. Cada nota debe:
   - Ubicar el problema (párrafo aproximado)
   - Citar el texto relevante (primeras palabras)
   - Explicar el problema en términos de experiencia del LECTOR
   - Ofrecer una sugerencia constructiva
4. Prioriza notas que tengan IMPACTO REAL en la calidad narrativa
5. NO generes notas sobre errores menores de prosa (esos van en la edición)

RESPONDE ÚNICAMENTE con JSON válido:
{{
    "notas_margen": [
        {{
            "nota_id": "ch{chapter_id}-nota-001",
            "parrafo_aprox": N,
            "texto_referencia": "Primeras 10-15 palabras del párrafo...",
            "tipo": "pacing|personaje|dialogo|claridad|emocion|voz|tension|show_tell",
            "severidad": "alta|media|baja",
            "nota": "Descripción del problema desde la perspectiva del lector...",
            "sugerencia": "Cómo podría mejorarse...",
            "impacto_si_no_se_corrige": "Qué pierde el lector si esto no se arregla"
        }}
    ],
    "resumen_capitulo": {{
        "fortaleza_principal": "Lo mejor de este capítulo",
        "problema_principal": "El área más importante a mejorar",
        "prioridad_revision": "alta|media|baja"
    }}
}}
"""


def main(input_data: dict) -> dict:
    """
    Envía capítulos a Claude Batch para generar notas de margen.
    
    Input:
        - chapters: Lista de fragmentos/capítulos
        - carta_editorial: Resultado de GenerateEditorialLetter
        - bible: Biblia narrativa
        - book_metadata: Metadatos del libro
    
    Output:
        - batch_id: ID del batch de Claude
        - status: Estado del envío
    """
    
    try:
        from anthropic import Anthropic
        
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            return {"error": "ANTHROPIC_API_KEY no configurada", "status": "config_error"}
        
        chapters = input_data.get('chapters', [])
        carta = input_data.get('carta_editorial', {})
        bible = input_data.get('bible', {})
        book_metadata = input_data.get('book_metadata', {})
        
        libro = book_metadata.get('title', bible.get('identidad_obra', {}).get('titulo', 'Sin título'))
        
        logging.info(f"📝 Preparando notas de margen para {len(chapters)} capítulos")
        
        client = Anthropic(api_key=api_key)
        
        batch_requests = []
        chapter_metadata = {}
        
        # Extraer contexto editorial relevante
        contexto_editorial = extraer_contexto_editorial(carta, bible)
        
        for chapter in chapters:
            ch_id = str(chapter.get('id', chapter.get('chapter_id', '?')))
            parent_id = chapter.get('parent_chapter_id', ch_id)
            
            # Guardar metadata
            chapter_metadata[ch_id] = {
                'fragment_id': chapter.get('id', 0),
                'parent_chapter_id': parent_id,
                'original_title': chapter.get('title', chapter.get('original_title', 'Sin título'))
            }
            
            # Buscar notas específicas del capítulo en la carta
            notas_cap = ""
            for nota in carta.get('notas_por_capitulo', []):
                if str(nota.get('capitulo')) == str(parent_id):
                    notas_cap = f"Función: {nota.get('funcion', '')}\nMejorar: {nota.get('que_mejorar', '')}"
                    break
            
            # Personajes
            personajes = extraer_personajes_capitulo(bible, parent_id)
            
            prompt = MARGIN_NOTES_PROMPT.format(
                titulo=chapter.get('title', chapter.get('original_title', 'Sin título')),
                libro=libro,
                contexto_editorial=contexto_editorial,
                posicion=f"Capítulo {parent_id}",
                funcion=notas_cap or "No especificada",
                personajes=", ".join(personajes) if personajes else "No especificados",
                contenido=chapter.get('content', ''),
                chapter_id=ch_id
            )
            
            request = {
                "custom_id": f"margin-{ch_id}",
                "params": {
                    "model": "claude-sonnet-4-5-20250929",
                    "max_tokens": 4000,
                    "temperature": 0.5,
                    "messages": [{"role": "user", "content": prompt}]
                }
            }
            batch_requests.append(request)
        
        logging.info(f"📦 Enviando {len(batch_requests)} requests a Claude Batch")
        
        message_batch = client.messages.batches.create(requests=batch_requests)
        
        logging.info(f"✅ Batch de notas creado: {message_batch.id}")
        
        return {
            "batch_id": message_batch.id,
            "chapters_count": len(chapters),
            "status": "submitted",
            "processing_status": message_batch.processing_status,
            "chapter_metadata": chapter_metadata
        }
        
    except ImportError as e:
        logging.error(f"❌ SDK no instalado: {e}")
        return {"error": str(e), "status": "import_error"}
    except Exception as e:
        logging.error(f"❌ Error: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return {"error": str(e), "status": "error"}


def extraer_contexto_editorial(carta: dict, bible: dict) -> str:
    """Extrae contexto relevante de la carta editorial."""
    
    contexto = []
    
    # Áreas de oportunidad principales
    areas = carta.get('areas_de_oportunidad', [])
    if areas:
        contexto.append("PROBLEMAS PRINCIPALES IDENTIFICADOS:")
        for area in areas[:5]:  # Top 5
            if area.get('prioridad') in ['ALTA', 'MEDIA']:
                contexto.append(f"- [{area.get('categoria', '').upper()}] {area.get('problema', '')[:100]}")
    
    # Voz del autor
    voz = bible.get('voz_del_autor', {})
    if voz.get('NO_CORREGIR'):
        contexto.append("\nELEMENTOS A PRESERVAR:")
        for item in voz['NO_CORREGIR'][:3]:
            contexto.append(f"- {item}")
    
    # Estilo
    contexto.append(f"\nESTILO: {voz.get('estilo_detectado', 'No especificado')}")
    
    return "\n".join(contexto)


def extraer_personajes_capitulo(bible: dict, chapter_id) -> list:
    """Extrae personajes relevantes para un capítulo."""
    
    personajes = []
    reparto = bible.get('reparto_completo', {})
    
    try:
        ch_num = int(chapter_id)
    except:
        ch_num = 0
    
    for tipo in ['protagonistas', 'antagonistas', 'secundarios']:
        for p in reparto.get(tipo, []):
            caps = p.get('capitulos_clave', [])
            if ch_num in caps or not caps:
                personajes.append(p.get('nombre', 'Desconocido'))
    
    return personajes[:5]  # Max 5 personajes

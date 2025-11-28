# =============================================================================
# HolisticReadingChunk/__init__.py - Lectura Holística por Fragmentos
# =============================================================================
# 
# En lugar de enviar el libro completo (sufre "Lost in the Middle"),
# analizamos cada cuarto por separado y luego fusionamos.
#
# MODELOS: gemini-2.5-flash (barato, rápido, suficiente para análisis parcial)
# =============================================================================

import logging
import json
import os
import time
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logging.basicConfig(level=logging.INFO)

# Prompt para análisis de UN CUARTO del libro
HOLISTIC_CHUNK_PROMPT = """
Eres un LECTOR EXPERTO analizando la PARTE {chunk_number} de 4 de una novela.

IMPORTANTE: Este es el {position_description} del libro.

TEXTO DE ESTA SECCIÓN:
{chunk_text}

ANÁLISIS REQUERIDO PARA ESTA SECCIÓN:

1. PERSONAJES QUE APARECEN:
   - Nombre, rol, estado emocional dominante
   - ¿Hay arcos de personaje que COMIENZAN o TERMINAN aquí?

2. EVENTOS CLAVE:
   - Lista los 5-10 eventos más importantes de esta sección
   - Indica si alguno parece ser: GANCHO, GIRO, CRISIS, CLÍMAX

3. RITMO DE ESTA SECCIÓN:
   - ¿Es LENTO, MEDIO o RÁPIDO?
   - ¿Parece intencional o problemático?

4. TONO Y ATMÓSFERA:
   - Palabras clave que describen el tono
   - ¿Hay cambios de tono significativos?

5. ELEMENTOS DE VOZ DEL AUTOR:
   - Longitud típica de oraciones
   - Uso de diálogo vs narración
   - Recursos estilísticos notables

6. POSIBLES PROBLEMAS:
   - Inconsistencias internas en esta sección
   - Repeticiones excesivas
   - Info-dumps o exposición forzada

RESPONDE SOLO JSON (sin markdown):
{{
  "seccion": {chunk_number},
  "posicion": "{position_description}",
  "personajes_presentes": [
    {{"nombre": "", "rol": "", "estado_emocional": "", "arco_en_seccion": ""}}
  ],
  "eventos_clave": [
    {{"evento": "", "tipo": "normal|gancho|giro|crisis|climax", "capitulo_aproximado": 0}}
  ],
  "ritmo": {{
    "clasificacion": "LENTO|MEDIO|RAPIDO",
    "es_intencional": true,
    "justificacion": ""
  }},
  "tono": {{
    "palabras_clave": [],
    "cambios_notables": ""
  }},
  "voz_autor": {{
    "longitud_oraciones": "cortas|medias|largas|mixtas",
    "densidad_dialogo": "alta|media|baja",
    "recursos_notables": []
  }},
  "problemas_detectados": [],
  "observaciones_para_fusion": ""
}}
"""

@retry(
    retry=retry_if_exception_type((Exception,)),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(3),
    reraise=True
)
def call_gemini_flash(client, prompt):
    """Llamada a Gemini Flash para análisis de chunk"""
    return client.models.generate_content(
        model='models/gemini-2.5-flash',  # Mismo modelo que usas en AnalyzeChapter
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=4096,
            response_mime_type="application/json",
            safety_settings=[
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
            ]
        )
    )


def main(chunk_input: dict) -> dict:
    """
    Analiza UN cuarto del libro.
    
    Input: {
        'chunk_number': 1-4,
        'total_chunks': 4,
        'chapters': [{id, title, content}, ...],
        'position_description': 'INICIO del libro (establecimiento)'
    }
    """
    try:
        start_time = time.time()
        
        chunk_number = chunk_input.get('chunk_number', 1)
        chapters = chunk_input.get('chapters', [])
        position_desc = chunk_input.get('position_description', f'Parte {chunk_number}')
        
        # Construir texto del chunk
        chunk_text = "\n\n---\n\n".join([
            f"CAPÍTULO: {ch.get('title', 'Sin título')}\n\n{ch.get('content', '')}"
            for ch in chapters
        ])
        
        word_count = len(chunk_text.split())
        logging.info(f"📖 Chunk {chunk_number}/4: {len(chapters)} caps, {word_count:,} palabras")
        
        # Configurar cliente
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY no configurada")
        
        client = genai.Client(api_key=api_key)
        
        # Construir prompt
        prompt = HOLISTIC_CHUNK_PROMPT.format(
            chunk_number=chunk_number,
            position_description=position_desc,
            chunk_text=chunk_text[:500000]  # Límite de seguridad
        )
        
        # Llamar a Gemini Flash
        response = call_gemini_flash(client, prompt)
        
        elapsed = time.time() - start_time
        
        if not response.text:
            raise ValueError("Respuesta vacía o bloqueada")
        
        # Parsear respuesta
        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        chunk_analysis = json.loads(response_text.strip())
        
        # Agregar metadata
        chunk_analysis['_metadata'] = {
            'status': 'success',
            'chunk_number': chunk_number,
            'chapters_count': len(chapters),
            'word_count': word_count,
            'tiempo_segundos': round(elapsed, 1),
            'modelo': 'gemini-2.5-flash'
        }
        
        logging.info(f"✅ Chunk {chunk_number} analizado en {elapsed:.1f}s")
        
        return chunk_analysis
        
    except Exception as e:
        logging.error(f"❌ Error en chunk {chunk_input.get('chunk_number', '?')}: {e}")
        return {
            'seccion': chunk_input.get('chunk_number', 0),
            'error': str(e),
            'personajes_presentes': [],
            'eventos_clave': [],
            '_metadata': {'status': 'error'}
        }

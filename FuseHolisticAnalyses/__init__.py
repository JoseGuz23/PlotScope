# =============================================================================
# FuseHolisticAnalyses/__init__.py - Fusiona los 4 análisis parciales
# =============================================================================
# 
# Toma los 4 análisis de chunks y los combina en un análisis holístico completo.
# Usa Gemini Pro porque requiere razonamiento de síntesis.
#
# MODELO: gemini-3-pro-preview (mismo que usas en CreateBible)
# =============================================================================

import logging
import json
import os
import time
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logging.basicConfig(level=logging.INFO)

FUSION_PROMPT = """
Eres el EDITOR JEFE sintetizando 4 análisis parciales de una novela en UN análisis completo.

ANÁLISIS DE LAS 4 SECCIONES:

SECCIÓN 1 (INICIO - Establecimiento):
{analysis_1}

SECCIÓN 2 (DESARROLLO TEMPRANO):
{analysis_2}

SECCIÓN 3 (DESARROLLO TARDÍO):
{analysis_3}

SECCIÓN 4 (CLÍMAX Y RESOLUCIÓN):
{analysis_4}

TU TAREA:

1. FUSIONAR personajes: Un personaje que aparece en múltiples secciones es EL MISMO.
   - Combina sus estados emocionales en un ARCO completo.

2. IDENTIFICAR estructura narrativa:
   - ¿Dónde está el GANCHO real? (Probablemente Sección 1)
   - ¿Dónde está el INCITING INCIDENT?
   - ¿Dónde están los GIROS?
   - ¿Dónde está el CLÍMAX? (Probablemente Sección 4)

3. DETECTAR el género y tono GLOBAL:
   - No el de una sección, sino el de toda la obra.

4. SINTETIZAR la voz del autor:
   - Patrones consistentes a través de las 4 secciones.

5. PRIORIZAR problemas:
   - Un problema en Sección 4 es más grave que en Sección 1 (afecta el clímax).

RESPONDE SOLO JSON (sin markdown):
{{
  "genero": {{
    "principal": "",
    "subgenero": "",
    "convenciones_seguidas": [],
    "convenciones_rotas_intencionalmente": [],
    "contrato_con_lector": ""
  }},
  "arco_narrativo": {{
    "gancho_inicial": {{"seccion": 0, "capitulo_aprox": 0, "descripcion": ""}},
    "inciting_incident": {{"seccion": 0, "capitulo_aprox": 0, "descripcion": ""}},
    "primer_giro": {{"seccion": 0, "capitulo_aprox": 0, "descripcion": ""}},
    "punto_medio": {{"seccion": 0, "capitulo_aprox": 0, "descripcion": ""}},
    "crisis": {{"seccion": 0, "capitulo_aprox": 0, "descripcion": ""}},
    "climax": {{"seccion": 0, "capitulo_aprox": 0, "descripcion": ""}},
    "resolucion": {{"seccion": 0, "capitulo_aprox": 0, "descripcion": ""}}
  }},
  "personajes_fusionados": [
    {{
      "nombre": "",
      "aliases": [],
      "rol_global": "",
      "arco_completo": "",
      "secciones_donde_aparece": [1,2,3,4]
    }}
  ],
  "analisis_ritmo": {{
    "patron_general": "",
    "por_seccion": [
      {{"seccion": 1, "ritmo": "LENTO|MEDIO|RAPIDO", "es_intencional": true, "justificacion": ""}}
    ]
  }},
  "voz_autor": {{
    "estilo_prosa": "",
    "longitud_oraciones": {{"predominante": "", "patron": ""}},
    "densidad_dialogo": "",
    "recursos_distintivos": [],
    "advertencia_editorial": ""
  }},
  "temas": {{
    "tema_central": "",
    "motivos_recurrentes": []
  }},
  "problemas_priorizados": [
    {{"seccion": 0, "tipo": "", "descripcion": "", "gravedad": "critico|medio|menor"}}
  ],
  "advertencias_para_editor": [
    {{"tipo": "", "ubicacion": "", "descripcion": "", "razon_es_intencional": ""}}
  ]
}}
"""

@retry(
    retry=retry_if_exception_type((Exception,)),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(3),
    reraise=True
)
def call_gemini_pro(client, prompt):
    """Llamada a Gemini Pro para fusión (requiere razonamiento)"""
    return client.models.generate_content(
        model='models/gemini-3-pro-preview',  # Mismo que usas en CreateBible
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=8192,
            response_mime_type="application/json",
            safety_settings=[
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
            ]
        )
    )


def main(chunk_analyses: list) -> dict:
    """
    Fusiona 4 análisis parciales en uno completo.
    
    Input: Lista de 4 análisis de chunks
    Output: Análisis holístico fusionado
    """
    try:
        start_time = time.time()
        
        logging.info(f"🔗 Fusionando {len(chunk_analyses)} análisis parciales...")
        
        # Ordenar por número de sección
        sorted_analyses = sorted(
            chunk_analyses,
            key=lambda x: x.get('seccion', x.get('_metadata', {}).get('chunk_number', 0))
        )
        
        # Verificar que tenemos los 4
        if len(sorted_analyses) < 4:
            logging.warning(f"⚠️ Solo {len(sorted_analyses)} análisis disponibles (esperados 4)")
        
        # Configurar cliente
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY no configurada")
        
        client = genai.Client(api_key=api_key)
        
        # Preparar análisis como strings JSON (sin metadata para reducir tokens)
        analysis_strings = []
        for i, analysis in enumerate(sorted_analyses[:4], 1):
            clean_analysis = {k: v for k, v in analysis.items() if not k.startswith('_')}
            analysis_strings.append(json.dumps(clean_analysis, indent=2, ensure_ascii=False))
        
        # Rellenar si faltan
        while len(analysis_strings) < 4:
            analysis_strings.append('{"error": "Análisis no disponible para esta sección"}')
        
        # Construir prompt
        prompt = FUSION_PROMPT.format(
            analysis_1=analysis_strings[0][:20000],
            analysis_2=analysis_strings[1][:20000],
            analysis_3=analysis_strings[2][:20000],
            analysis_4=analysis_strings[3][:20000]
        )
        
        logging.info("🧠 Gemini Pro fusionando análisis...")
        
        response = call_gemini_pro(client, prompt)
        
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
        
        fused_analysis = json.loads(response_text.strip())
        
        # Agregar metadata
        fused_analysis['_metadata'] = {
            'status': 'success',
            'metodo': 'hierarchical_fusion',
            'chunks_fusionados': len(sorted_analyses),
            'tiempo_segundos': round(elapsed, 1),
            'modelo': 'gemini-3-pro-preview'
        }
        
        logging.info(f"✅ Fusión completada en {elapsed:.1f}s")
        
        return fused_analysis
        
    except Exception as e:
        logging.error(f"❌ Error en fusión: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return {
            'error': str(e),
            'genero': {'principal': 'Error en análisis'},
            '_metadata': {'status': 'error', 'error_msg': str(e)}
        }

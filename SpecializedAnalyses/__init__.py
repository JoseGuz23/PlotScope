# =============================================================================
# SpecializedAnalyses/__init__.py - SYLPHRENA 4.0
# =============================================================================
# Ejecuta 4 análisis de grado profesional en paralelo:
# 1. Detección de Clichés y Patrones
# 2. Diferenciación de Voces (Diálogo)
# 3. Economía Narrativa
# 4. Comparativa de Género
# =============================================================================

import logging
import json
import os
import asyncio
from google import genai
from google.genai import types

logging.basicConfig(level=logging.INFO)

PROMPTS = {
    "cliches": """Analiza este texto buscando patrones lingüísticos repetitivos, muletillas del autor y clichés narrativos. 
    Responde JSON: {"patrones_repetidos": [{"patron": str, "frecuencia": int}], "cliches_detectados": [str]}""",
    
    "dialogue": """Analiza las voces de los personajes. ¿Tienen sintaxis y vocabulario distinto? 
    Responde JSON: {"voces_distintivas": bool, "score_diferenciacion": 1-10, "analisis_por_personaje": [{"nombre": str, "rasgos_voz": str}]}""",
    
    "economy": """Evalúa la economía narrativa. ¿Cada capítulo cumple múltiples funciones (trama, personaje, atmósfera)?
    Responde JSON: {"score_eficiencia": 1-10, "capitulos_baja_densidad": [str], "sugerencias": [str]}""",
    
    "genre": """Compara la estructura de este libro con las convenciones del género {genre}.
    Responde JSON: {"cumplimiento_genero": 1-10, "elementos_ausentes": [str], "subversiones_intencionales": [str]}"""
}

def main(payload) -> str:
    try:
        # --- BLOQUE DE SEGURIDAD ---
        if isinstance(payload, str):
            data = json.loads(payload)
        else:
            data = payload
        # ---------------------------
        
        bible = data.get('bible', {})
        context_text = json.dumps(bible.get('holistic_analysis', {})) 
        genre = data.get('book_metadata', {}).get('genre', 'General Fiction')
        
        api_key = os.environ.get('GEMINI_API_KEY')
        client = genai.Client(api_key=api_key)
        
        results = {}
        
        # 1. Clichés (Uso gemini-2.5-flash validado)
        r1 = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=PROMPTS['cliches'],
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        results['cliches_analysis'] = json.loads(r1.text)

        # 2. Diálogo (Requiere Pro - Uso gemini-3-pro-preview validado)
        r2 = client.models.generate_content(
            model='gemini-3-pro-preview',
            contents=PROMPTS['dialogue'],
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        results['dialogue_analysis'] = json.loads(r2.text)

        # 3. Economía (Uso gemini-2.5-flash validado)
        r3 = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=PROMPTS['economy'],
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        results['narrative_economy'] = json.loads(r3.text)

        # 4. Género (Uso gemini-3-pro-preview validado)
        r4 = client.models.generate_content(
            model='gemini-3-pro-preview',
            contents=PROMPTS['genre'].format(genre=genre),
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        results['genre_comparison'] = json.loads(r4.text)

        return json.dumps({
            "status": "success",
            "specialized_analyses": results
        })

    except Exception as e:
        logging.error(f"Error in SpecializedAnalyses: {str(e)}")
        return json.dumps({"error": str(e)})
# =============================================================================
# SpecializedAnalyses/__init__.py - SYLPHRENA 4.2 (GEMINI + CLAUDE FALLBACK)
# =============================================================================
import logging
import json
import os
import re
from google import genai
from google.genai import types
import anthropic

logging.basicConfig(level=logging.INFO)

# =============================================================================
# CONFIGURACIÓN
# =============================================================================
GEMINI_MODEL_FAST = 'gemini-2.5-flash'
GEMINI_MODEL_SMART = 'gemini-3-pro-preview' # O 'gemini-3-pro-preview' si tienes acceso
CLAUDE_MODEL = 'claude-sonnet-4-20250514'

PROMPTS = {
    "cliches": """Eres un editor literario experto. Analiza este texto buscando patrones lingüísticos repetitivos, muletillas y clichés.
    Responde SOLO con este JSON: {"patrones_repetidos": [{"patron": "string", "frecuencia": 0}], "cliches_detectados": ["string"]}""",
    
    "dialogue": """Eres un experto en narrativa. Analiza las voces de los personajes. ¿Son distinguibles?
    Responde SOLO con este JSON: {"voces_distintivas": true, "score_diferenciacion": 0, "analisis_por_personaje": [{"nombre": "string", "rasgos_voz": "string"}]}""",
    
    "economy": """Evalúa la economía narrativa. ¿El texto es eficiente o tiene "grasa"?
    Responde SOLO con este JSON: {"score_eficiencia": 0, "capitulos_baja_densidad": ["string"], "sugerencias": ["string"]}""",
    
    # CORRECCIÓN AQUÍ: Doble llave {{ }} para el JSON, llave simple { } para la variable
    "genre": """Compara la estructura de este texto con las convenciones del género {genre}.
    Responde SOLO con este JSON: {{"cumplimiento_genero": 0, "elementos_ausentes": ["string"], "subversiones_intencionales": ["string"]}}"""
}

def clean_json_text(text):
    """Limpia el texto para extraer solo el JSON válido."""
    if not text: return "{}"
    # Eliminar bloques markdown
    text = re.sub(r'^```json\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^```\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'```$', '', text, flags=re.MULTILINE)
    # Intentar encontrar el primer { y el último }
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1:
        text = text[start:end+1]
    return text.strip()

def call_claude_fallback(prompt, analysis_name):
    """Intenta realizar el análisis con Claude si Gemini falla."""
    try:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            logging.warning("⚠️ No hay ANTHROPIC_API_KEY para fallback.")
            return None

        logging.info(f"🛡️ Activando Claude Fallback para: {analysis_name}")
        client = anthropic.Anthropic(api_key=api_key)
        
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text
        return json.loads(clean_json_text(response_text))
        
    except Exception as e:
        logging.error(f"❌ Claude Fallback falló para {analysis_name}: {e}")
        return None

def safe_analyze(gemini_client, model, prompt, analysis_name):
    """Ejecuta análisis con estrategia: Gemini -> Fallback Claude -> Error Controlado."""
    
    # 1. INTENTO CON GEMINI
    try:
        response = gemini_client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.3
            )
        )
        
        if response.text:
            return json.loads(clean_json_text(response.text))
        else:
            logging.warning(f"⚠️ Gemini devolvió respuesta vacía para {analysis_name} (Posible filtro de seguridad).")
            
    except Exception as e:
        logging.warning(f"⚠️ Error en Gemini para {analysis_name}: {e}")

    # 2. FALLBACK A CLAUDE (Si Gemini falló o devolvió vacío)
    claude_result = call_claude_fallback(prompt, analysis_name)
    if claude_result:
        return claude_result

    # 3. SI TODO FALLA, RETORNAR ESTRUCTURA VACÍA (NO CRASHEAR)
    logging.error(f"❌ Fallaron todos los intentos para {analysis_name}")
    return {
        "error": "Analysis failed on all providers",
        "status": "failed"
    }

def main(payload) -> str:
    try:
        # Preparación de datos
        if isinstance(payload, str):
            data = json.loads(payload)
        else:
            data = payload
            
        bible = data.get('bible', {})
        # Contexto del libro (primeras 10k palabras para no saturar)
        # Nota: Para análisis profundos, idealmente se pasa el texto, 
        # pero aquí usamos la Biblia como proxy contextual si no hay texto completo.
        # Si tienes el texto completo disponible en payload, úsalo.
        
        genre = data.get('book_metadata', {}).get('genre') or \
                bible.get('identidad_obra', {}).get('genero', 'Ficción General')
        
        logging.info(f"🔬 Iniciando análisis especializados. Género: {genre}")
        
        gemini_key = os.environ.get('GEMINI_API_KEY')
        if not gemini_key:
            return json.dumps({"error": "No Gemini API Key"})
            
        client = genai.Client(api_key=gemini_key)
        results = {}

        # Agregar contexto al prompt (Breve resumen de la obra para que la IA sepa de qué habla)
        sinopsis = bible.get('identidad_obra', {}).get('contrato_con_lector', '')
        context_prompt = f"\nCONTEXTO DE LA OBRA:\nGénero: {genre}\nSinopsis: {sinopsis}\n\n"

        # --- EJECUCIÓN SECUENCIAL BLINDADA ---
        
        # 1. Clichés
        results['cliches_analysis'] = safe_analyze(
            client, GEMINI_MODEL_FAST, context_prompt + PROMPTS['cliches'], 'cliches'
        )

        # 2. Diálogo
        results['dialogue_analysis'] = safe_analyze(
            client, GEMINI_MODEL_SMART, context_prompt + PROMPTS['dialogue'], 'dialogue'
        )

        # 3. Economía
        results['narrative_economy'] = safe_analyze(
            client, GEMINI_MODEL_FAST, context_prompt + PROMPTS['economy'], 'economy'
        )

        # 4. Comparativa de Género (Aquí solía fallar)
        formatted_prompt = context_prompt + PROMPTS['genre'].format(genre=genre)
        results['genre_comparison'] = safe_analyze(
            client, GEMINI_MODEL_SMART, formatted_prompt, 'genre'
        )

        return json.dumps({
            "status": "success",
            "specialized_analyses": results
        })

    except Exception as e:
        logging.error(f"❌ Error fatal en SpecializedAnalyses wrapper: {str(e)}")
        return json.dumps({"status": "error", "error": str(e)})
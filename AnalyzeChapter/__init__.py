import logging
import json
import os
import re
import time as time_module
import google.generativeai as genai
from google.api_core import exceptions
# CAMBIO 1: Usamos tenacity para los reintentos (arquitectura robusta)
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Configurar logs de tenacity para que no sean ruidosos
logging.getLogger('tenacity').setLevel(logging.WARNING)

# Definimos las excepciones que merecen un reintento (Rate Limit o Servidor Caído)
retry_strategy = retry(
    retry=retry_if_exception_type((
        exceptions.ResourceExhausted, 
        exceptions.ServiceUnavailable, 
        exceptions.DeadlineExceeded
    )),
    wait=wait_exponential(multiplier=1.5, min=2, max=30), # Espera exponencial
    stop=stop_after_attempt(5), # Máximo 5 intentos antes de fallar
    reraise=True # Si falla 5 veces, lanza el error para manejarlo abajo
)

@retry_strategy
def call_gemini_with_retry(model, prompt):
    """Función auxiliar encapsulada con Tenacity"""
    return model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.2,
            "max_output_tokens": 8192,
            "response_mime_type": "application/json"
        },
        request_options={'timeout': 90}, # Timeout duro de la petición HTTP
        safety_settings=[
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
    )

def main(chapter_json) -> dict:
    """
    Analiza un capítulo/fragmento con Gemini 2.5 Flash y Tenacity.
    """
    chapter_id = "Desconocido"
    parent_title = "Sin título"
    
    try:
        # 1. Manejo robusto de entrada
        if isinstance(chapter_json, str):
            try:
                chapter = json.loads(chapter_json)
            except json.JSONDecodeError:
                logging.error("Error al decodificar JSON de entrada")
                chapter = {"id": 0, "title": "Error Decode", "content": ""}
        else:
            chapter = chapter_json

        chapter_id = chapter.get('id', 0)
        
        # --- METADATOS CRÍTICOS (Alineados con segmentbook) ---
        is_fragment = chapter.get('is_fragment', False)
        # Prioridad: parent_chapter > title > Sin título
        parent_title = chapter.get('parent_chapter') or chapter.get('title') or "Sin título"
        original_title = chapter.get('title', parent_title)
        
        context_instruction = ""
        if is_fragment:
            context_instruction = f"""
            ⚠️ CONTEXTO DE FRAGMENTACIÓN:
            Este texto es SOLO UN FRAGMENTO del capítulo mayor "{parent_title}".
            NO trates esto como una historia completa. El arco narrativo puede estar cortado.
            """

        # 2. LIMPIEZA MÍNIMA
        content_clean = re.sub(r'\n+', '\n', chapter.get('content', ''))

        # Configurar Gemini
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return {"error": "No API Key", "chapter_id": chapter_id}

        genai.configure(api_key=api_key)
        
        # CAMBIO 2: Versión exacta que pediste (Flash 2.5)
        model = genai.GenerativeModel('models/gemini-2.5-flash-preview-09-2025')
        
    # EN ANALYZE CHAPTER - Instrucciones Agnósticas
        prompt = f"""
        Actúa como un Analista Literario Forense. Tu trabajo es extraer datos objetivos del texto proporcionado.
        
        {context_instruction}

        --- DATOS DEL TEXTO ---
        TÍTULO REAL: {parent_title}
        CONTENIDO:
        {content_clean}
        
        --- INSTRUCCIONES DE EXTRACCIÓN ---
        
        1. REPARTO LOCAL (EN ESTE CAPÍTULO):
           - Identifica CADA personaje que aparezca o sea mencionado.
           - CLASIFICA su rol basándote ÚNICAMENTE en sus acciones en este texto:
             * "Protagonista": Quien lleva el punto de vista o la acción positiva.
             * "Antagonista": Quien ejerce oposición, violencia o conflicto contra el protagonista.
             * "Secundario": Observadores o soporte.
        
        2. TRAMA & TIEMPO: 
           - Lista los eventos clave en orden secuencial.
           - EXTRAE TEXTUALMENTE cualquier referencia al tiempo (horas, días, clima, "al día siguiente").
        
        3. AUDITORÍA DE ESTILO:
           - Busca redundancias ("grasa literaria").
           - Evalúa el ritmo de la escena.

        DEVUELVE JSON ESTRICTO:
        (Misma estructura JSON de siempre...)
        """
        
        # 4. LLAMADA Y MEDICIÓN
        start_gemini = time_module.time()
        logging.info(f"🚀 Llamando a Gemini 2.5 Flash para {parent_title} (ID: {chapter_id})...")
        
        # Aquí usamos la función decorada con tenacity
        response = call_gemini_with_retry(model, prompt)
        
        gemini_elapsed = time_module.time() - start_gemini
        logging.info(f"⏱️ Gemini Flash tardó {gemini_elapsed:.2f}s")
        
        if not response.candidates:
             raise ValueError("Respuesta vacía o bloqueada por seguridad.")

        analysis = json.loads(response.text)
        
        # Inyección de metadatos finales
        analysis['chapter_id'] = chapter_id
        analysis['titulo_real'] = parent_title
        analysis['_metadata'] = {
            'status': 'success', 
            'model': 'gemini-2.5-flash-preview-09-2025',
            'processing_time_seconds': round(gemini_elapsed, 2)
        }
        
        return analysis

    # Manejo de errores FINAL (Si tenacity se rinde o hay otro error)
    except Exception as e:
        error_msg = str(e)
        logging.error(f"💥 Error Fatal en ID {chapter_id}: {error_msg}")
        
        status = "fatal_error"
        if "429" in error_msg or "ResourceExhausted" in error_msg:
            status = "rate_limit_exhausted"
        
        return {
            "chapter_id": chapter_id, 
            "titulo_real": parent_title,
            "error": error_msg, 
            "status": status,
            # Estructura vacía para no romper el siguiente paso
            "reparto_local": [],
            "analisis_narrativo": {"resumen_denso": "FALLO DE ANÁLISIS"}
        }
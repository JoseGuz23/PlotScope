# HolisticReading/__init__.py

import logging
import json
import os
import time
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logging.basicConfig(level=logging.INFO)

# Configuración de reintentos para errores transitorios
@retry(
    retry=retry_if_exception_type((Exception,)),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(3),
    reraise=True
)
def call_gemini_pro(model, prompt):
    """Llamada a Gemini Pro con reintentos"""
    return model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.2,  # Bajo para análisis consistente
            "max_output_tokens": 8192,
            "response_mime_type": "application/json"
        },
        safety_settings=[
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    )

def main(full_book_text: str) -> dict:
    """
    Lectura Holística: Lee el libro completo y extrae su "ADN"
    
    Input: Texto completo del libro (string)
    Output: JSON con análisis holístico
    """
    HOLISTIC_READING_PROMPT = """
    Eres un LECTOR EXPERTO. Tu trabajo NO es editar ni criticar. 
    Tu trabajo es COMPRENDER profundamente esta obra antes de que otros la editen.

    Lee la novela completa a continuación. Después, responde con tu análisis.

    ---
    NOVELA COMPLETA:
    {full_book_text}
    ---

    INSTRUCCIONES DE ANÁLISIS:

    1. GÉNERO Y SUBGÉNERO
    - ¿Qué tipo de libro es? (thriller, literary fiction, romance, fantasía, etc.)
    - ¿Qué convenciones del género sigue o rompe intencionalmente?
    - ¿Cuál es el "contrato" con el lector? (¿Qué espera el lector de este género?)

    2. ARCO NARRATIVO COMPLETO
    Identifica con precisión:
    - GANCHO INICIAL: ¿Qué atrapa al lector en el primer capítulo?
    - INCITING INCIDENT: ¿Qué evento rompe el status quo? ¿En qué capítulo?
    - PRIMER PUNTO DE GIRO: ¿Cuándo el protagonista cruza el umbral? ¿Capítulo?
    - PUNTO MEDIO: ¿Cuál es la revelación o cambio central? ¿Capítulo?
    - CRISIS/TODO ESTÁ PERDIDO: ¿Cuándo toca fondo el protagonista? ¿Capítulo?
    - CLÍMAX: ¿Cuál es el enfrentamiento final? ¿Capítulo?
    - RESOLUCIÓN: ¿Cómo se cierra la historia? ¿Capítulo?
    
    3. ANÁLISIS DE RITMO (PACING)
    Para cada capítulo, clasifica:
    - RÁPIDO: Mucha acción, diálogos cortos, tensión alta
    - MEDIO: Balance entre acción y reflexión
    - LENTO: Introspección, worldbuilding, setup, recuperación
    
    CRÍTICO: Distingue entre:
    - LENTO INTENCIONAL: Pausa necesaria después de clímax, setup de tensión, 
        momento emotivo que requiere espacio
    - LENTO PROBLEMÁTICO: Sin propósito narrativo claro, redundante, 
        podría comprimirse sin perder nada

    4. VOZ Y ESTILO DEL AUTOR
    Identifica patrones consistentes:
    - LONGITUD DE ORACIONES: ¿Cortas y directas? ¿Largas y fluidas? ¿Varía según tensión?
    - DENSIDAD DE DIÁLOGO: ¿Mucho diálogo? ¿Poca narración? ¿Balance?
    - RECURSOS ESTILÍSTICOS: ¿Usa metáforas frecuentes? ¿Estilo seco? ¿Poético?
    - PUNTO DE VISTA: ¿Primera persona? ¿Tercera limitada? ¿Omnisciente? ¿Cambia?
    
    IMPORTANTE: Estos patrones son la VOZ del autor. NO deben "corregirse".

    5. REGLAS DEL MUNDO (si aplica)
    Si hay elementos fantásticos, mágicos, tecnológicos o sistemas especiales:
    - ¿Cuáles son las reglas establecidas?
    - ¿Son consistentes a lo largo del libro?
    - ¿Hay violaciones que parecen errores vs. excepciones intencionales?

    6. TEMAS Y MOTIVOS
    - TEMA CENTRAL: ¿De qué trata realmente el libro? (no la trama, el significado)
    - MOTIVOS RECURRENTES: Símbolos, imágenes o ideas que se repiten
    - EVOLUCIÓN TEMÁTICA: ¿Cómo se desarrolla el tema a lo largo de la obra?

    7. ADVERTENCIAS PARA EL EDITOR
    Lista cualquier cosa que un editor podría malinterpretar:
    - Capítulos lentos que son INTENCIONALES (y por qué)
    - Inconsistencias aparentes que son INTENCIONALES (y por qué)
    - Estilos "incorrectos" que son VOZ DEL AUTOR (ej: fragmentos de oración deliberados)
    - Personajes "inconsistentes" que están en desarrollo o tienen secretos

    RESPONDE EN JSON ESTRICTO:
    {
    "genero": {
        "principal": "...",
        "subgenero": "...",
        "convenciones_seguidas": ["..."],
        "convenciones_rotas_intencionalmente": ["..."],
        "contrato_con_lector": "..."
    },
    "arco_narrativo": {
        "gancho_inicial": {"capitulo": N, "descripcion": "..."},
        "inciting_incident": {"capitulo": N, "descripcion": "..."},
        "primer_giro": {"capitulo": N, "descripcion": "..."},
        "punto_medio": {"capitulo": N, "descripcion": "..."},
        "crisis": {"capitulo": N, "descripcion": "..."},
        "climax": {"capitulo": N, "descripcion": "..."},
        "resolucion": {"capitulo": N, "descripcion": "..."}
    },
    "analisis_ritmo": {
        "patron_general": "Descripción del flujo rítmico del libro",
        "por_capitulo": [
        {
            "capitulo": N,
            "titulo": "...",
            "ritmo": "RAPIDO|MEDIO|LENTO",
            "intencion": "INTENCIONAL|CUESTIONABLE",
            "justificacion": "Por qué este ritmo tiene sentido aquí (o no)"
        }
        ]
    },
    "voz_autor": {
        "estilo_prosa": "minimalista|equilibrado|barroco|otro",
        "longitud_oraciones": {
        "predominante": "cortas|medias|largas|variable",
        "patron": "¿Cambia según contexto? ¿Cómo?"
        },
        "densidad_dialogo": "alto|medio|bajo",
        "recursos_distintivos": ["lista de técnicas que el autor usa consistentemente"],
        "punto_de_vista": "...",
        "advertencia_editorial": "Qué NO debe 'corregirse' porque es voz del autor"
    },
    "reglas_mundo": [
        {
        "sistema": "Nombre del sistema (magia, tecnología, etc.)",
        "reglas": ["Lista de reglas establecidas"],
        "consistencia": "CONSISTENTE|HAY_VIOLACIONES",
        "violaciones_detectadas": ["Si las hay, listarlas con capítulos"]
        }
    ],
    "temas": {
        "tema_central": "...",
        "motivos_recurrentes": [
        {"motivo": "...", "apariciones": ["cap X", "cap Y"], "significado": "..."}
        ],
        "evolucion_tematica": "Cómo se desarrolla el tema"
    },
    "advertencias_para_editor": [
        {
        "tipo": "RITMO_INTENCIONAL|INCONSISTENCIA_INTENCIONAL|VOZ_AUTOR|DESARROLLO_PERSONAJE",
        "ubicacion": "Capítulo(s) afectado(s)",
        "descripcion": "Qué podría malinterpretarse",
        "razon_es_intencional": "Por qué NO debe cambiarse"
        }
    ]
    }
    """
    try:
        start_time = time.time()
        
        # Validar input
        word_count = len(full_book_text.split())
        token_estimate = int(word_count * 1.33)
        logging.info(f"Iniciando Lectura Holística: {word_count:,} palabras (~{token_estimate:,} tokens)")
        
        # Configurar Gemini Pro
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY no configurada")
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('models/gemini-3-pro-preview')
        
        # Construir prompt con el texto completo
        prompt = HOLISTIC_READING_PROMPT.format(full_book_text=full_book_text)
        
        # Llamar a Gemini Pro
        logging.info("🧠 Gemini Pro está leyendo el libro completo...")
        response = call_gemini_pro(model, prompt)
        
        elapsed = time.time() - start_time
        logging.info(f"⏱️ Lectura Holística completada en {elapsed:.1f}s")
        
        # Parsear respuesta
        if not response.candidates:
            raise ValueError("Respuesta vacía o bloqueada por seguridad")
        
        response_text = response.text.strip()
        
        # Limpiar posibles artifacts de markdown
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Parsear JSON
        holistic_analysis = json.loads(response_text)
        
        # Añadir metadata
        holistic_analysis["_metadata"] = {
            "status": "success",
            "palabras_analizadas": word_count,
            "tokens_estimados": token_estimate,
            "tiempo_segundos": round(elapsed, 1),
            "modelo": "gemini-3-pro-preview",
            "costo_estimado": round(token_estimate * 1.25 / 1_000_000 + 8192 * 5.00 / 1_000_000, 4)
        }
        
        logging.info(f"ADN del libro extraído exitosamente")
        logging.info(f"   - Género: {holistic_analysis.get('genero', {}).get('principal', 'N/A')}")
        logging.info(f"   - Advertencias para editor: {len(holistic_analysis.get('advertencias_para_editor', []))}")
        
        return holistic_analysis
        
    except json.JSONDecodeError as e:
        logging.error(f"Error parseando JSON de lectura holística: {e}")
        raise
    except Exception as e:
        logging.error(f"Error en Lectura Holística: {str(e)}")
        raise
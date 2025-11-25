import logging
import json
import os
import re
import time as time_module
import google.generativeai as genai
from google.api_core import exceptions
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Configurar logs de tenacity para que no sean ruidosos
logging.getLogger('tenacity').setLevel(logging.WARNING)

# --- 1. DEFINICIÓN DE LAS MÉTRICAS (Texto estático) ---
ANALYZE_CHAPTER_METRICS = """
MÉTRICAS OBJETIVAS A EXTRAER:

1. ESTRUCTURA TEXTUAL
   - total_palabras: Número exacto de palabras
   - total_oraciones: Número de oraciones
   - promedio_palabras_por_oracion: total_palabras / total_oraciones
   - oracion_mas_larga: Número de palabras de la oración más larga
   - oracion_mas_corta: Número de palabras de la oración más corta
   - total_parrafos: Número de párrafos
   - promedio_oraciones_por_parrafo: total_oraciones / total_parrafos

2. COMPOSICIÓN DEL CONTENIDO
   - lineas_dialogo: Número de líneas de diálogo (entre comillas o guiones)
   - palabras_en_dialogo: Palabras dentro de diálogos
   - porcentaje_dialogo: (palabras_en_dialogo / total_palabras) * 100
   - lineas_narracion: Líneas que no son diálogo
   - escenas_accion: Número de secuencias con verbos de movimiento/conflicto
   - escenas_reflexion: Número de secuencias introspectivas

3. RITMO CALCULADO
   - eventos_por_mil_palabras: (total_eventos / total_palabras) * 1000
   - densidad_dialogos: porcentaje_dialogo
   - clasificacion_ritmo: RAPIDO (>5 eventos/1k, >40% diálogo) | 
                          MEDIO (2-5 eventos/1k, 20-40% diálogo) | 
                          LENTO (<2 eventos/1k, <20% diálogo)

4. MARCADORES TEMPORALES
   - referencias_tiempo_explicitas: ["al día siguiente", "tres horas después", etc.]
   - tiempo_transcurrido_estimado: "minutos" | "horas" | "días" | "semanas" | "indeterminado"

5. INDICADORES DE CALIDAD (para edición)
   - instancias_tell_no_show: [{"texto": "Estaba triste", "linea_aprox": N}]
   - repeticiones_detectadas: [{"palabra": "miró", "frecuencia": N}]
   - adverbios_ly_excesivos: Conteo de adverbios terminados en -mente
   - dialogos_sin_accion: Secuencias largas de diálogo sin beats de acción
"""

# --- 2. PLANTILLA DEL PROMPT (Usamos marcadores {{ASI}} para reemplazar seguro) ---
ANALYZE_CHAPTER_PROMPT_TEMPLATE = """
Actúa como un Analista Literario Forense. Tu trabajo es extraer datos OBJETIVOS y MEDIBLES del texto.

CONTEXTO DEL CAPÍTULO:
- Título: {{CHAPTER_TITLE}}
- ID: {{CHAPTER_ID}}
- Es fragmento de capítulo mayor: {{IS_FRAGMENT}}
- Capítulo padre (si aplica): {{PARENT_CHAPTER}}

---
TEXTO A ANALIZAR:
{{CHAPTER_CONTENT}}
---

INSTRUCCIONES DE EXTRACCIÓN:

1. REPARTO LOCAL (personajes en este capítulo)
Para CADA personaje que aparezca o sea mencionado:
- nombre: Nombre como aparece en el texto
- rol_en_capitulo: "protagonista" | "antagonista" | "secundario" | "mencionado"
- estado_emocional: Emoción predominante en este capítulo
- acciones_clave: Lista de acciones importantes que realiza
- dialogos_count: Número de líneas de diálogo que tiene

2. EVENTOS Y TRAMA
Lista SECUENCIAL de eventos (en orden de aparición):
- evento: Descripción breve (máx 15 palabras)
- tipo: "accion" | "dialogo" | "reflexion" | "descripcion" | "flashback"
- tension: 1-10 (1=calma total, 10=máxima tensión)

3. MÉTRICAS OBJETIVAS
{{METRICS_INSTRUCTIONS}}

4. ELEMENTOS NARRATIVOS
- lugar: Dónde ocurre la escena
- tiempo_narrativo: Cuándo ocurre (relativo a la historia)
- atmosfera: Tono emocional predominante
- conflicto_presente: Sí/No + descripción breve
- gancho_final: ¿El capítulo termina con tensión/pregunta abierta?

5. SEÑALES PARA EDICIÓN
- problemas_potenciales: Lista de posibles issues (show/tell, repeticiones, etc.)
- fortalezas: Qué hace bien este capítulo
- conexiones_con_otros: Referencias a eventos de otros capítulos (si detectables)

DEVUELVE JSON ESTRICTO:
{
"chapter_id": "{{CHAPTER_ID}}",
"titulo_capitulo": "{{CHAPTER_TITLE}}",
"parent_chapter": "{{PARENT_CHAPTER}}",

"reparto_local": [
    {
    "nombre": "...",
    "rol_en_capitulo": "protagonista|antagonista|secundario|mencionado",
    "estado_emocional": "...",
    "acciones_clave": ["...", "..."],
    "dialogos_count": 0
    }
],

"eventos": [
    {
    "evento": "...",
    "tipo": "accion|dialogo|reflexion|descripcion|flashback",
    "tension": 0
    }
],

"metricas": {
    "estructura": {
    "total_palabras": 0,
    "total_oraciones": 0,
    "promedio_palabras_por_oracion": 0.0,
    "total_parrafos": 0
    },
    "composicion": {
    "lineas_dialogo": 0,
    "porcentaje_dialogo": 0.0,
    "escenas_accion": 0,
    "escenas_reflexion": 0
    },
    "ritmo": {
    "eventos_por_mil_palabras": 0.0,
    "clasificacion": "RAPIDO|MEDIO|LENTO"
    },
    "tiempo": {
    "referencias_explicitas": ["..."],
    "transcurrido_estimado": "minutos|horas|dias|semanas|indeterminado"
    }
},

"elementos_narrativos": {
    "lugar": "...",
    "tiempo_narrativo": "...",
    "atmosfera": "...",
    "conflicto_presente": true,
    "descripcion_conflicto": "...",
    "gancho_final": true
},

"señales_edicion": {
    "instancias_tell_no_show": [
    {"texto": "...", "sugerencia": "..."}
    ],
    "repeticiones": [
    {"palabra": "...", "frecuencia": 0}
    ],
    "fortalezas": ["...", "..."],
    "problemas_potenciales": ["...", "..."]
}
}
"""

# --- 3. ESTRATEGIA DE REINTENTOS (Tenacity) ---
retry_strategy = retry(
    retry=retry_if_exception_type((
        exceptions.ResourceExhausted, 
        exceptions.ServiceUnavailable, 
        exceptions.DeadlineExceeded
    )),
    wait=wait_exponential(multiplier=1.5, min=2, max=30),
    stop=stop_after_attempt(5),
    reraise=True
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
        request_options={'timeout': 90},
        safety_settings=[
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
    )

# --- 4. FUNCIÓN PRINCIPAL ---
def main(chapter_json) -> dict:
    """
    Analiza un capítulo/fragmento con Gemini 2.5 Flash y Tenacity.
    """
    chapter_id = "Desconocido"
    parent_title = "Sin título"
    
    try:
        # A. Manejo robusto de entrada
        if isinstance(chapter_json, str):
            try:
                chapter = json.loads(chapter_json)
            except json.JSONDecodeError:
                logging.error("Error al decodificar JSON de entrada")
                chapter = {"id": 0, "title": "Error Decode", "content": ""}
        else:
            chapter = chapter_json

        # Aseguramos que sean strings para evitar errores en .replace()
        chapter_id = str(chapter.get('id', 0))
        is_fragment = str(chapter.get('is_fragment', False))
        parent_title = chapter.get('parent_chapter') or chapter.get('title') or "Sin título"
        content = chapter.get('content', '')

        # B. Limpieza mínima
        content_clean = re.sub(r'\n+', '\n', content)

        # C. Configurar Gemini
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return {"error": "No API Key", "chapter_id": chapter_id}

        genai.configure(api_key=api_key)
        
        # Modelo solicitado: Flash 2.5 Preview
        model = genai.GenerativeModel('models/gemini-2.5-flash-preview-09-2025')

        # D. CONSTRUCCIÓN DEL PROMPT (AQUÍ ESTABA EL ERROR ANTES)
        # Usamos .replace() para inyectar tus variables en la plantilla de forma segura
        prompt = ANALYZE_CHAPTER_PROMPT_TEMPLATE.replace("{{CHAPTER_TITLE}}", parent_title)
        prompt = prompt.replace("{{CHAPTER_ID}}", chapter_id)
        prompt = prompt.replace("{{IS_FRAGMENT}}", is_fragment)
        prompt = prompt.replace("{{PARENT_CHAPTER}}", parent_title)
        prompt = prompt.replace("{{METRICS_INSTRUCTIONS}}", ANALYZE_CHAPTER_METRICS)
        prompt = prompt.replace("{{CHAPTER_CONTENT}}", content_clean)
        
        # E. Llamada a la IA
        start_gemini = time_module.time()
        logging.info(f"🚀 Llamando a Gemini 2.5 Flash para {parent_title} (ID: {chapter_id})...")
        
        response = call_gemini_with_retry(model, prompt)
        
        gemini_elapsed = time_module.time() - start_gemini
        logging.info(f"⏱️ Gemini Flash tardó {gemini_elapsed:.2f}s")
        
        if not response.candidates:
             raise ValueError("Respuesta vacía o bloqueada por seguridad.")

        analysis = json.loads(response.text)
        
        # F. Inyección de metadatos finales
        analysis['chapter_id'] = chapter_id
        analysis['titulo_real'] = parent_title
        analysis['_metadata'] = {
            'status': 'success', 
            'model': 'gemini-2.5-flash-preview-09-2025',
            'processing_time_seconds': round(gemini_elapsed, 2)
        }
        
        return analysis

    # G. Manejo de errores
    except Exception as e:
        error_msg = str(e)
        logging.error(f"💥 Error Fatal en ID {chapter_id}: {error_msg}")
        
        status = "fatal_error"
        if "429" in error_msg or "ResourceExhausted" in error_msg:
            status = "rate_limit_exhausted"
        
        # Devolvemos estructura mínima para no romper el orquestador
        return {
            "chapter_id": chapter_id, 
            "titulo_real": parent_title,
            "error": error_msg, 
            "status": status,
            "reparto_local": [],
            "analisis_narrativo": {"resumen_denso": "FALLO DE ANÁLISIS"}
        }
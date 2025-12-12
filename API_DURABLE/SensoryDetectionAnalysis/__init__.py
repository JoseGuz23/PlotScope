# =============================================================================
# SensoryDetectionAnalysis/__init__.py - LYA 7.1 (FLASH 2.5)
# =============================================================================
# ACTUALIZACIÓN:
# - Modelo actualizado a: models/gemini-2.5-flash
# - Análisis semántico de Show vs Tell para evitar falsos positivos de regex.
# =============================================================================

import logging
import json
import os
import time
from typing import List, Dict, Any
import numpy as np
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logging.basicConfig(level=logging.INFO)

# Configuración del modelo "Sensor"
# Usamos Flash 2.5 para máxima velocidad y bajo costo en tareas de clasificación.
SENSORY_MODEL_ID = "models/gemini-2.5-flash" 

SENSORY_ANALYSIS_PROMPT = """
Eres un ANALISTA SENSORIAL experto en escritura creativa.
Tu tarea es analizar el siguiente texto (Capítulo de una novela) para diagnosticar el balance "Show vs Tell" (Mostrar vs Contar).

ANALIZA EL TEXTO BUSCANDO:
1. **Inmersión Sensorial (Show):** Descripciones que estimulan los 5 sentidos (vista, oído, tacto, olfato, gusto) y acciones físicas concretas.
2. **Abstracción (Tell):** Explicaciones de emociones ("sintió miedo"), resúmenes de hechos, metáforas clichés o verbos de filtrado ("vio", "oyó", "supo").

RESPONDE ÚNICAMENTE CON ESTE JSON:
{{
  "showing_ratio": 0.00, // (0.0 a 1.0) Porcentaje del texto que es inmersivo/sensorial
  "avg_sensory_density": 0.00, // (0.0 a 1.0) Intensidad promedio de los detalles
  "dominant_sense": "VISUAL|AUDITIVO|TACTIL|OLFATIVO|GUSTATIVO|KINESTESICO|NINGUNO",
  
  "problem_paragraphs": [
    // Lista de hasta 5 párrafos más problemáticos (puro Telling aburrido)
    {{
      "text_preview": "Primeras 15 palabras...",
      "issue": "Explicación abstracta de emociones / Falta de anclaje físico",
      "suggestion": "Describir la reacción física en lugar de nombrar la emoción"
    }}
  ],
  
  "diagnosis_global": "Breve diagnóstico de 1 frase sobre la inmersión del capítulo."
}}

--- TEXTO DEL CAPÍTULO ---
{chapter_content}
"""

@retry(
    retry=retry_if_exception_type((Exception,)),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(3),
    reraise=True
)
def call_gemini_flash(client, prompt):
    """Llamada rápida a Gemini Flash 2.5."""
    return client.models.generate_content(
        model=SENSORY_MODEL_ID,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1, # Determinista para clasificación precisa
            response_mime_type="application/json",
            max_output_tokens=1024
        )
    )

def analyze_chapter_with_ai(client, chapter_content: str, chapter_id: Any) -> Dict[str, Any]:
    """
    Envía el capítulo a Gemini Flash para análisis sensorial.
    INCLUYE LIMPIEZA DE JSON "ANTI-CREATIVIDAD".
    """
    if len(chapter_content) < 200:
        return {
            "chapter_id": chapter_id,
            "showing_ratio": 0.5,
            "avg_sensory_density": 0.5,
            "dominant_sense": "NEUTRO",
            "diagnosis": "Texto demasiado corto.",
            "problem_paragraphs": []
        }

    prompt = SENSORY_ANALYSIS_PROMPT.format(chapter_content=chapter_content[:50000])
    
    try:
        response = call_gemini_flash(client, prompt)
        
        if not response.text:
            raise ValueError(f"Respuesta vacía de {SENSORY_MODEL_ID}")
            
        raw_text = response.text.strip()
        
        # --- BLOQUE DE LIMPIEZA QUIRÚRGICA ---
        # 1. Eliminar bloques de código markdown si existen
        if "```" in raw_text:
            # Eliminar ```json y ``` al final
            raw_text = raw_text.replace("```json", "").replace("```", "").strip()
        
        # 2. Búsqueda de llaves (Safety Net)
        # Si Gemini dice "Claro, aquí está: { ... }", esto extrae solo lo que está entre { }
        first_brace = raw_text.find("{")
        last_brace = raw_text.rfind("}")
        
        if first_brace != -1 and last_brace != -1:
            json_str = raw_text[first_brace : last_brace + 1]
        else:
            # Si no encuentra llaves, probablemente falló la generación
            logging.warning(f"⚠️ No se encontró JSON válido en respuesta de Cap {chapter_id}")
            # Intentar parsear lo que haya por si acaso
            json_str = raw_text
            
        # 3. Parseo
        data = json.loads(json_str)
        # -------------------------------------
        
        data['chapter_id'] = chapter_id
        return data

    except json.JSONDecodeError as e:
        logging.error(f"⚠️ Error decodificando JSON de Gemini en Cap {chapter_id}: {e}")
        logging.error(f"   Respuesta cruda problemática: {raw_text[:200]}...") # Loguear el inicio para debug
        return {
            "chapter_id": chapter_id,
            "showing_ratio": 0.0,
            "avg_sensory_density": 0.0,
            "diagnosis": "Error de formato JSON en IA",
            "problem_paragraphs": []
        }
    except Exception as e:
        logging.error(f"⚠️ Error general analizando Cap {chapter_id}: {e}")
        return {
            "chapter_id": chapter_id,
            "showing_ratio": 0.0,
            "avg_sensory_density": 0.0,
            "diagnosis": f"Error: {str(e)}",
            "problem_paragraphs": []
        }

def main(consolidated_chapters: List[Dict]) -> Dict:
    """
    Función principal llamada por el Orquestador.
    """
    try:
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return {"error": "GEMINI_API_KEY missing", "status": "error"}
            
        client = genai.Client(api_key=api_key)
        
        logging.info(f"🔬 Iniciando Análisis Sensorial AI ({SENSORY_MODEL_ID})...")
        
        chapter_analyses = []
        all_ratios = []
        all_densities = []
        critical_issues = []

        # Procesar capítulos
        for chapter in consolidated_chapters:
            ch_id = chapter.get('chapter_id', '?')
            content = chapter.get('content', '')
            
            # Llamada AI
            analysis = analyze_chapter_with_ai(client, content, ch_id)
            chapter_analyses.append(analysis)
            
            # Recolectar métricas
            ratio = analysis.get('showing_ratio', 0)
            all_ratios.append(ratio)
            all_densities.append(analysis.get('avg_sensory_density', 0))
            
            # Detectar problemas graves para el reporte global
            if ratio < 0.25: # Umbral estricto
                critical_issues.append({
                    "type": "TELLING_EXCESIVO",
                    "severity": "alta",
                    "chapter_id": ch_id,
                    "description": f"Cap {ch_id}: Inmersión muy baja ({ratio:.0%}). {analysis.get('diagnosis_global', '')}"
                })

        # Métricas Globales
        global_ratio = np.mean(all_ratios) if all_ratios else 0
        global_density = np.mean(all_densities) if all_densities else 0
        
        logging.info(f"✅ Análisis Sensorial Completado. Ratio Global: {global_ratio:.2%}")

        return {
            "sensory_analyses": chapter_analyses,
            "global_metrics": {
                "avg_showing_ratio": float(global_ratio),
                "avg_sensory_density": float(global_density),
                "total_chapters_analyzed": len(chapter_analyses)
            },
            "critical_issues": critical_issues,
            "status": "completed"
        }

    except Exception as e:
        logging.error(f"❌ Error crítico en SensoryDetection: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return {"error": str(e), "status": "error"}
# CreateBible/__init__.py (v2.0)

import logging
import json
import os
import time as time_module
from collections import defaultdict
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.api_core import exceptions

logging.basicConfig(level=logging.INFO)
logging.getLogger('tenacity').setLevel(logging.WARNING)

# Estrategia de reintentos para Gemini Pro
retry_strategy = retry(
    retry=retry_if_exception_type((
        exceptions.ResourceExhausted,
        exceptions.ServiceUnavailable,
        exceptions.DeadlineExceeded
    )),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(4),
    reraise=True
)

@retry_strategy
def call_gemini_pro(model, prompt):
    """Llamada a Gemini Pro con reintentos"""
    return model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.1,  # Bajo para consistencia
            "max_output_tokens": 16384,  # Biblia puede ser larga
            "response_mime_type": "application/json"
        },
        request_options={'timeout': 120},
        safety_settings=[
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    )


def agrupar_fragmentos(analyses):
    """
    Middleware: Convierte análisis planos en capítulos consolidados
    usando el metadato 'parent_chapter' para precisión absoluta.
    (Sin cambios - tu función original funciona bien)
    """
    capitulos_consolidados = defaultdict(lambda: {
        "titulo": "",
        "fragmentos": [],
        "metadata_agregada": {
            "ids_involucrados": [],
        }
    })

    for analysis in analyses:
        clean_title = (
            analysis.get("parent_chapter") or 
            analysis.get("titulo_real") or 
            analysis.get("original_title") or 
            "Sin Título"
        )
        
        capitulos_consolidados[clean_title]["titulo"] = clean_title
        capitulos_consolidados[clean_title]["fragmentos"].append(analysis)
        capitulos_consolidados[clean_title]["metadata_agregada"]["ids_involucrados"].append(
            analysis.get("id") or analysis.get("chapter_id", "?")
        )

    resultado = list(capitulos_consolidados.values())
    logging.info(f"📦 Agrupación: {len(analyses)} fragmentos → {len(resultado)} capítulos")
    return resultado


def main(bible_input_json) -> dict:
    """
    Fase REDUCE v2.0: Fusiona análisis detallados + lectura holística
    
    Input: JSON string con {chapter_analyses: [...], holistic_analysis: {...}}
    Output: Biblia Narrativa completa con priorización
    """
    try:
        # =================================================================
        # 1. PARSEO DE INPUT (NUEVO FORMATO)
        # =================================================================
        if isinstance(bible_input_json, str):
            try:
                bible_input = json.loads(bible_input_json)
            except json.JSONDecodeError:
                logging.error("bible_input_json inválido")
                bible_input = {}
        else:
            bible_input = bible_input_json
        
        # Extraer las DOS fuentes de información
        chapter_analyses = bible_input.get('chapter_analyses', [])
        holistic_analysis = bible_input.get('holistic_analysis', {})
        
        has_holistic = bool(holistic_analysis and holistic_analysis.get('genero'))
        
        logging.info(f"📚 CreateBible v2.0 iniciando...")
        logging.info(f"   - Análisis de capítulos: {len(chapter_analyses)}")
        logging.info(f"   - Análisis holístico: {'✅ Presente' if has_holistic else '❌ Ausente'}")
        
        # =================================================================
        # 2. AGRUPACIÓN DE FRAGMENTOS (tu función original)
        # =================================================================
        capitulos_estructurados = agrupar_fragmentos(chapter_analyses)
        
        # =================================================================
        # 3. CONFIGURAR GEMINI PRO
        # =================================================================
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY no configurada")
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('models/gemini-3-pro-preview')
        
        # =================================================================
        # 4. PROMPT DE FUSIÓN (EL CORAZÓN DE v2.0)
        # =================================================================
        prompt = f"""
Eres el EDITOR JEFE del Proyecto Sylphrena. Tu misión es crear la BIBLIA NARRATIVA DEFINITIVA.

Tienes acceso a DOS fuentes de información complementarias:

1. **ANÁLISIS HOLÍSTICO**: La visión de alguien que leyó el libro COMPLETO de corrido.
   Contiene: género, arco narrativo, ritmo intencional, voz del autor, advertencias editoriales.

2. **ANÁLISIS DETALLADOS**: Métricas precisas y datos de cada capítulo individual.
   Contiene: personajes, eventos, métricas de estilo, problemas detectados.

Tu trabajo: FUSIONAR ambas perspectivas en una Biblia coherente y PRIORIZAR los problemas.

═══════════════════════════════════════════════════════════════════════════════
FUENTE 1: ANÁLISIS HOLÍSTICO (Visión Global)
═══════════════════════════════════════════════════════════════════════════════
{json.dumps(holistic_analysis, indent=2, ensure_ascii=False) if has_holistic else "NO DISPONIBLE - Inferir del análisis detallado"}

═══════════════════════════════════════════════════════════════════════════════
FUENTE 2: ANÁLISIS POR CAPÍTULO (Datos Detallados)
═══════════════════════════════════════════════════════════════════════════════
{json.dumps(capitulos_estructurados, indent=2, ensure_ascii=False)}

═══════════════════════════════════════════════════════════════════════════════
INSTRUCCIONES DE FUSIÓN
═══════════════════════════════════════════════════════════════════════════════

1. **IDENTIDAD DE LA OBRA**
   - USA el género y tono del análisis holístico como base
   - CONFIRMA con las métricas de los capítulos (% diálogo, ritmo, etc.)
   - Si hay contradicción, prioriza el holístico (vio el libro completo)

2. **REPARTO DE PERSONAJES**
   - FUSIONA las apariciones de todos los capítulos
   - DEDUPLICA: "Juan", "Juanito", "el hermano" pueden ser el mismo personaje
   - VALIDA consistencia: ¿Un personaje actúa coherente a lo largo del libro?
   - CRUZA con el análisis holístico para confirmar roles principales

3. **ARCO NARRATIVO**
   - USA el arco del análisis holístico como estructura base
   - VALIDA con los niveles de tensión detectados en cada capítulo
   - ¿Los picos de tensión coinciden con los puntos del arco?

4. **MAPA DE RITMO (CRÍTICO)**
   - CRUZA el ritmo detectado en cada capítulo con las advertencias holísticas
   - Si el holístico dice "Cap 15 es pausa intencional", márcalo así
   - Si un capítulo es LENTO y NO está marcado como intencional → ALERTA
   - No marques como problema lo que es decisión estilística del autor

5. **VOZ DEL AUTOR (NO TOCAR)**
   - Extrae del holístico qué elementos son VOZ, no errores
   - Oraciones cortas, fragmentos, estilo seco → puede ser intencional
   - Incluye instrucciones claras de qué NO debe editar Claude

6. **PRIORIZACIÓN DE PROBLEMAS (TU FUNCIÓN MÁS IMPORTANTE)**
   
   CRÍTICO: 
   - Agujeros de trama que rompen la lógica
   - Inconsistencias factuales graves (personaje muerto que reaparece)
   - Contradicciones en reglas del mundo establecidas
   
   MEDIO:
   - Problemas de ritmo NO intencionales
   - Inconsistencias menores de continuidad
   - Escenas que podrían mejorar significativamente
   
   MENOR:
   - Repeticiones de palabras
   - Oportunidades de show-don't-tell
   - Mejoras estilísticas opcionales
   
   ⚠️ IMPORTANTE: Si algo PARECE problema pero el holístico lo marca como 
   INTENCIONAL, NO es un problema. Es una característica. No lo incluyas 
   en problemas.

7. **GUÍA PARA CLAUDE (EDITOR)**
   - Sintetiza instrucciones específicas que Claude necesita
   - ¿Qué NO debe tocar? (voz del autor)
   - ¿Qué capítulos requieren cuidado especial?
   - ¿Qué patrones estilísticos debe mantener?

═══════════════════════════════════════════════════════════════════════════════
RESPONDE CON ESTE JSON EXACTO:
═══════════════════════════════════════════════════════════════════════════════
{{
  "metadata_biblia": {{
    "version": "2.0",
    "total_capitulos": N,
    "tiene_analisis_holistico": true|false
  }},
  
  "identidad_obra": {{
    "genero": "...",
    "subgenero": "...",
    "tono_predominante": "...",
    "tema_central": "...",
    "contrato_con_lector": "Qué espera el lector de este género"
  }},
  
  "arco_narrativo": {{
    "estructura_detectada": "tres_actos|viaje_heroe|in_media_res|otro",
    "puntos_clave": {{
      "gancho": {{"capitulo": N, "descripcion": "..."}},
      "inciting_incident": {{"capitulo": N, "descripcion": "..."}},
      "primer_giro": {{"capitulo": N, "descripcion": "..."}},
      "punto_medio": {{"capitulo": N, "descripcion": "..."}},
      "crisis": {{"capitulo": N, "descripcion": "..."}},
      "climax": {{"capitulo": N, "descripcion": "..."}},
      "resolucion": {{"capitulo": N, "descripcion": "..."}}
    }},
    "evaluacion": "SOLIDO|NECESITA_AJUSTES|PROBLEMATICO",
    "notas_arco": "Observaciones sobre la estructura"
  }},
  
  "reparto_completo": {{
    "protagonistas": [
      {{
        "nombre": "Nombre Principal",
        "aliases": ["apodos", "referencias"],
        "rol_arquetipo": "El héroe, el mentor, etc.",
        "arco_personaje": "Cómo evoluciona",
        "capitulos_aparicion": [1, 3, 5],
        "consistencia": "CONSISTENTE|INCONSISTENCIAS_DETECTADAS",
        "notas_inconsistencia": ["Si las hay"]
      }}
    ],
    "antagonistas": [
      {{
        "nombre": "...",
        "aliases": [],
        "naturaleza_conflicto": "territorial|ideológico|personal|otro",
        "nivel_amenaza": "alto|medio|bajo",
        "capitulos_aparicion": []
      }}
    ],
    "secundarios": [
      {{
        "nombre": "...",
        "funcion": "soporte|alivio_comico|catalizador",
        "capitulos_aparicion": []
      }}
    ]
  }},
  
  "mapa_de_ritmo": {{
    "patron_global": "Descripción del flujo rítmico general",
    "capitulos": [
      {{
        "numero": N,
        "titulo": "...",
        "clasificacion": "RAPIDO|MEDIO|LENTO",
        "es_intencional": true|false,
        "justificacion": "Por qué este ritmo (intencional o problema)",
        "posicion_en_arco": "setup|conflicto_ascendente|climax|resolucion"
      }}
    ],
    "alertas_pacing": [
      {{
        "capitulo": N,
        "problema": "Descripción del problema de ritmo",
        "sugerencia": "Qué podría mejorarse"
      }}
    ]
  }},
  
  "voz_del_autor": {{
    "estilo_detectado": "minimalista|equilibrado|barroco|experimental",
    "caracteristicas": {{
      "longitud_oraciones": "cortas|medias|largas|variable",
      "patron_oraciones": "Descripción de cuándo cambia",
      "densidad_dialogo": "alta|media|baja",
      "recursos_frecuentes": ["metáforas", "fragmentos", "etc."],
      "punto_de_vista": "primera|tercera_limitada|omnisciente"
    }},
    "NO_CORREGIR": [
      "Lista explícita de elementos que son VOZ, no errores",
      "Ej: Oraciones fragmentadas en escenas de acción",
      "Ej: Diálogos cortos sin acotaciones"
    ]
  }},
  
  "linea_temporal": {{
    "duracion_total": "Cuánto tiempo abarca la historia",
    "cronologia": [
      {{
        "orden": 1,
        "capitulo": N,
        "tiempo_narrativo": "Día 1, mañana / Año 1943 / etc.",
        "eventos_clave": ["..."]
      }}
    ],
    "flashbacks": [
      {{"capitulo": N, "referencia_temporal": "A qué momento del pasado"}}
    ]
  }},
  
  "reglas_del_mundo": [
    {{
      "sistema": "Magia, tecnología, sociedad, etc.",
      "reglas_establecidas": ["Lista de reglas"],
      "consistencia": "CONSISTENTE|VIOLACIONES_DETECTADAS",
      "violaciones": [
        {{"capitulo": N, "descripcion": "Qué regla se viola"}}
      ]
    }}
  ],
  
  "problemas_priorizados": {{
    "criticos": [
      {{
        "id": "CRIT-001",
        "tipo": "agujero_trama|inconsistencia_grave|regla_mundo",
        "descripcion": "Descripción clara del problema",
        "capitulos_afectados": [N, N],
        "evidencia": "Cita o referencia específica",
        "impacto": "Por qué es crítico para la historia",
        "sugerencia": "Posible corrección"
      }}
    ],
    "medios": [
      {{
        "id": "MED-001",
        "tipo": "ritmo|continuidad_menor|desarrollo_personaje",
        "descripcion": "...",
        "capitulos_afectados": [N],
        "sugerencia": "..."
      }}
    ],
    "menores": [
      {{
        "id": "MEN-001",
        "tipo": "repeticion|show_tell|estilo",
        "descripcion": "...",
        "capitulos_afectados": [N],
        "sugerencia": "..."
      }}
    ]
  }},
  
  "guia_para_claude": {{
    "instrucciones_globales": [
      "Mantener oraciones cortas en escenas de acción",
      "No expandir capítulos marcados como pausa intencional",
      "Respetar fragmentos de oración del autor",
      "etc."
    ],
    "capitulos_especiales": [
      {{
        "capitulo": N,
        "instruccion": "Este capítulo es lento A PROPÓSITO porque...",
        "que_no_tocar": ["elemento1", "elemento2"]
      }}
    ],
    "patrones_a_mantener": [
      "Descripción de patrones estilísticos que Claude debe preservar"
    ]
  }}
}}
"""

        # =================================================================
        # 5. LLAMADA A GEMINI PRO
        # =================================================================
        try:
            start_time = time_module.time()
            logging.info("🧠 Gemini Pro está construyendo la Biblia v2.0...")
            
            response = call_gemini_pro(model, prompt)
            
            elapsed = time_module.time() - start_time
            logging.info(f"⏱️ Gemini Pro tardó {elapsed:.2f}s en crear la Biblia")
            
            if not response.candidates:
                raise ValueError("Respuesta vacía o bloqueada por seguridad")
            
            # Parsear respuesta
            response_text = response.text.strip()
            
            # Limpiar posibles artifacts de markdown
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            bible = json.loads(response_text)
            
            # =================================================================
            # 6. METADATA DE GENERACIÓN
            # =================================================================
            # Estimar tokens y costo
            prompt_tokens = len(prompt.split()) * 1.33
            output_tokens = len(response_text.split()) * 1.33
            cost_input = prompt_tokens * 1.25 / 1_000_000  # Gemini Pro input
            cost_output = output_tokens * 5.00 / 1_000_000  # Gemini Pro output
            total_cost = cost_input + cost_output
            
            bible['_metadata'] = {
                'status': 'success',
                'version': '2.0',
                'modelo': 'gemini-3-pro-preview',
                'tiempo_segundos': round(elapsed, 2),
                'capitulos_procesados': len(capitulos_estructurados),
                'tiene_holistic': has_holistic,
                'tokens_estimados': {
                    'input': int(prompt_tokens),
                    'output': int(output_tokens)
                },
                'costo_estimado_usd': round(total_cost, 4)
            }
            
            # Log resumen
            problemas = bible.get('problemas_priorizados', {})
            logging.info(f"✅ Biblia v2.0 creada exitosamente")
            logging.info(f"   - Tiempo: {elapsed:.2f}s")
            logging.info(f"   - Costo: ${total_cost:.4f}")
            logging.info(f"   - Problemas críticos: {len(problemas.get('criticos', []))}")
            logging.info(f"   - Problemas medios: {len(problemas.get('medios', []))}")
            logging.info(f"   - Problemas menores: {len(problemas.get('menores', []))}")
            
            return bible
            
        except json.JSONDecodeError as e:
            logging.error(f"⚠️ Error parseando JSON de Biblia: {e}")
            logging.error(f"Respuesta raw: {response.text[:500]}...")
            raise
            
        except Exception as ai_error:
            logging.error(f"⚠️ Error en Gemini Pro: {str(ai_error)}")
            # Retornar estructura de fallback
            return {
                "metadata_biblia": {"version": "2.0", "error": True},
                "identidad_obra": {"genero": "Error", "tema_central": "Error generando biblia"},
                "arco_narrativo": {"estructura_detectada": "desconocida", "puntos_clave": {}},
                "reparto_completo": {"protagonistas": [], "antagonistas": [], "secundarios": []},
                "mapa_de_ritmo": {"patron_global": "Error", "capitulos": []},
                "voz_del_autor": {"estilo_detectado": "desconocido", "NO_CORREGIR": []},
                "problemas_priorizados": {"criticos": [], "medios": [], "menores": []},
                "guia_para_claude": {"instrucciones_globales": [], "capitulos_especiales": []},
                "_metadata": {
                    "status": "fallback",
                    "error": str(ai_error),
                    "version": "2.0"
                }
            }
            
    except Exception as e:
        logging.error(f"💥 Error fatal en CreateBible v2.0: {str(e)}")
        raise
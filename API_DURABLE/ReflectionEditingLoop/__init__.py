# =============================================================================
# ReflectionEditingLoop/__init__.py - LYA 7.0 (CACHED & RUTHLESS)
# =============================================================================
# MEJORAS CRÍTICAS:
# 1. Context Caching: Se cachea Biblia + Capítulo Original (Ahorro ~60-80%).
# 2. Crítico Separado: Gemini usa system_instruction para mantener rigor.
# 3. Dynamic Headers: Soporte listo para Opus 4.5 (High Stakes).
# =============================================================================

import logging
import json
import os
from typing import Dict, Any, Optional
from google import genai
from google.genai import types
from anthropic import AnthropicVertex

logging.basicConfig(level=logging.INFO)

# Importar configuración
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from vertex_utils import resolve_vertex_model_id
except ImportError:
    from API_DURABLE.vertex_utils import resolve_vertex_model_id

# Fallback por si no existe config_models
try:
    from config_models import (
        REFLECTION_CRITIC_MODEL,
        REFLECTION_WRITER_MODEL, # Idealmente Claude 3.5 Sonnet o Opus 4.5
        REFLECTION_MAX_ITERATIONS
    )
except ImportError:
    REFLECTION_CRITIC_MODEL = "gemini-3-pro-preview"
    REFLECTION_WRITER_MODEL = "claude-sonnet-4-5-20250929"
    REFLECTION_MAX_ITERATIONS = 3


# =============================================================================
# 1. SYSTEM PROMPTS (ESTÁTICOS - SE CACHEAN)
# =============================================================================

# Este bloque se envía a Claude una vez y se mantiene en memoria
WRITER_SYSTEM_CACHEABLE = """Eres un DEVELOPMENTAL EDITOR de élite.
Tu trabajo es editar el capítulo proporcionado para alcanzar la excelencia literaria.

═══════════════════════════════════════════════════════════════════════════════
BIBLIA Y CONTEXTO (FUENTE DE VERDAD)
═══════════════════════════════════════════════════════════════════════════════
Género: {genero}
Tono: {tono}
Voz del Autor: {voz_desc}

⛔ RESTRICCIONES ABSOLUTAS (NO TOCAR):
{no_corregir_text}

═══════════════════════════════════════════════════════════════════════════════
CAPÍTULO ORIGINAL (REFERENCIA)
═══════════════════════════════════════════════════════════════════════════════
{original_text}

═══════════════════════════════════════════════════════════════════════════════
TUS OBJETIVOS DE EDICIÓN
═══════════════════════════════════════════════════════════════════════════════
1. SHOW, DON'T TELL: Elimina abstracciones. "Sintió miedo" -> "Sus manos temblaron".
2. RITMO: Ajusta la longitud de oraciones a la tensión de la escena.
3. VOZ: Mantén el estilo del autor, solo pule la ejecución.
4. SUBTEXTO: Los personajes no deben decir exactamente lo que piensan.

Responde SIEMPRE en formato JSON.
"""

# Prompt del Crítico (Gemini) - Ahora va en system_instruction
CRITIC_SYSTEM_ROLE = """Eres el EDITOR JEFE más exigente de la industria.
Tu trabajo es DESTRUIR (constructivamente) el borrador del editor junior.
No dejes pasar ni una sola alucinación, ni un solo adjetivo débil.
Si el texto no es perfecto, RECHÁZALO (aprobado: false).
Tu estándar es la perfección literaria."""

# =============================================================================
# 2. USER PROMPTS (DINÁMICOS)
# =============================================================================

CRITIC_TASK_PROMPT = """
COMPARATIVA DE EDICIÓN:

--- TEXTO ORIGINAL ---
{original_text}

--- PROPUESTA DEL EDITOR JUNIOR ---
{edited_text}

EVALÚA CON RIGOR:
1. ¿Inventó cosas? (Alucinaciones = RECHAZO INMEDIATO)
2. ¿Perdió la voz del autor?
3. ¿Mejoró realmente el Show vs Tell?

Responde en JSON:
{{
  "score_global": 0.0,
  "aprobado": boolean,
  "fallos_criticos": ["string"],
  "mejoras_requeridas": ["string"],
  "aspectos_positivos": ["string"]
}}
"""

REFINER_TASK_PROMPT = """
El Editor Jefe ha revisado tu borrador. Aquí está su feedback:

SCORE: {score}/10

FALLOS A CORREGIR:
{fallos}

MEJORAS REQUERIDAS:
{mejoras}

Genera la VERSIÓN FINAL corregida.
Responde JSON:
{{
  "capitulo_editado": "...",
  "cambios_aplicados": [...]
}}
"""

# =============================================================================
# LÓGICA PRINCIPAL
# =============================================================================

def main(input_data: dict) -> dict:
    try:
        gemini_key = os.environ.get('GEMINI_API_KEY')
        # Vertex AI Config
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
        region = os.environ.get('GOOGLE_CLOUD_LOCATION', 'us-central1')

        if not gemini_key: return {"error": "GEMINI_API_KEY missing"}
        
        # Initialize Clients
        gemini_client = genai.Client(api_key=gemini_key)
        
        # Use AnthropicVertex instead of Anthropic direct
        if project_id:
            logging.info(f"🤖 Usando Anthropic sobre Vertex AI ({project_id} @ {region})")
            claude_client = AnthropicVertex(region=region, project_id=project_id)
        else:
            # Fallback to standard Anthropic if no project_id (legacy support)
            claude_key = os.environ.get('ANTHROPIC_API_KEY')
            if claude_key:
                claude_client = Anthropic(api_key=claude_key)
            else:
                 return {"error": "GOOGLE_CLOUD_PROJECT or ANTHROPIC_API_KEY missing"}

        # Desempaquetar datos
        chapter = input_data.get('chapter', {})
        bible = input_data.get('bible', {})
        margin_notes = input_data.get('margin_notes', [])
        metadata = input_data.get('metadata', {})

        original_text = chapter.get('content', '')
        chapter_title = chapter.get('title', 'Capítulo')
        
        # Datos de Biblia
        identidad = bible.get('identidad_obra', {})
        voz = bible.get('voz_del_autor', {}) # Corregido key
        genero = identidad.get('genero', 'Ficción')
        tono = identidad.get('tono_predominante', 'Neutro')
        voz_desc = voz.get('estilo_detectado', 'Estándar')
        no_corregir = voz.get('NO_CORREGIR', [])
        no_corregir_text = "\n".join([f"- {x}" for x in no_corregir])

        logging.info(f"🔄 [REFLECTION] Iniciando cirugía en: {chapter_title}")

        # ---------------------------------------------------------------------
        # PREPARAR SYSTEM PROMPT CON CACHÉ (CLAUDE)
        # ---------------------------------------------------------------------
        # Aquí inyectamos el texto original UNA VEZ.
        system_content_str = WRITER_SYSTEM_CACHEABLE.format(
            genero=genero,
            tono=tono,
            voz_desc=voz_desc,
            no_corregir_text=no_corregir_text,
            original_text=original_text[:100000] # Safety clip
        )
        
        system_block = [
            {
                "type": "text", 
                "text": system_content_str,
                "cache_control": {"type": "ephemeral"} # <--- AHORRO DE DINERO
            }
        ]

        # Variables de estado
        current_draft = ""
        current_changes = []
        feedback_history = []
        iteration = 0
        
        # ---------------------------------------------------------------------
        # BUCLE DE EDICIÓN
        # ---------------------------------------------------------------------
        while iteration < REFLECTION_MAX_ITERATIONS:
            iteration += 1
            logging.info(f" ⚡ Iteración {iteration} (Modelo: {REFLECTION_WRITER_MODEL})")

            # --- PASO 1: ESCRITURA / REFINAMIENTO ---
            if iteration == 1:
                # Prompt inicial simple (el contexto ya está en System)
                notas_txt = "\n".join([f"- {n['nota']}" for n in margin_notes])
                user_msg = f"Genera la PRIMERA VERSIÓN editada.\n\nATENCIÓN A ESTAS NOTAS DE MARGEN:\n{notas_txt}"
            else:
                # Prompt de refinamiento
                last_fb = feedback_history[-1]
                user_msg = REFINER_TASK_PROMPT.format(
                    score=last_fb.get('score_global'),
                    fallos="\n".join([f"- {f}" for f in last_fb.get('fallos_criticos', [])]),
                    mejoras="\n".join([f"- {m}" for m in last_fb.get('mejoras_requeridas', [])])
                )

            # Llamada a Claude (Writer)
            # Resolvers ID de Vertex
            writer_model_vertex = resolve_vertex_model_id(REFLECTION_WRITER_MODEL)

            # Detectamos si es Opus 4.5 para activar headers high-stakes
            extra_headers = {}
            extra_body = {}
            if "opus-4-5" in REFLECTION_WRITER_MODEL:
                extra_headers = {"anthropic-beta": "effort-2025-11-24"}
                # Solo usamos high effort en la primera pasada para establecer la base
                if iteration == 1: extra_body = {"effort": "high"}

            writer_response = claude_client.messages.create(
                model=writer_model_vertex,
                max_tokens=8192,
                system=system_block, # <--- Enviamos el bloque con caché
                messages=[{"role": "user", "content": user_msg}],
                extra_headers=extra_headers,
                extra_body=extra_body
            )
            
            # Procesar respuesta Writer
            try:
                txt = writer_response.content[0].text
                # Limpieza JSON
                if txt.strip().startswith("```json"): 
                    txt = txt.strip()[7:].strip().rstrip("```")
                
                data = json.loads(txt)
                current_draft = data.get('capitulo_editado', '')
                current_changes = data.get('cambios_aplicados', [])
            except:
                logging.error("❌ Error parseando JSON del Writer, usando texto raw")
                current_draft = writer_response.content[0].text

            # --- PASO 2: CRÍTICA (GEMINI PRO) ---
            logging.info(" ⚖️  El Juez (Gemini) está deliberando...")
            
            critic_input = CRITIC_TASK_PROMPT.format(
                original_text=original_text[:20000], # Limite seguro para comparativa
                edited_text=current_draft[:20000]
            )

            critic_response = gemini_client.models.generate_content(
                model=REFLECTION_CRITIC_MODEL, # gemini-3-pro-preview
                contents=critic_input,
                config=types.GenerateContentConfig(
                    system_instruction=CRITIC_SYSTEM_ROLE, # <--- Rol fuerte
                    temperature=0.1, # Frialdad absoluta
                    response_mime_type="application/json"
                )
            )
            
            try:
                critique = json.loads(critic_response.text)
                score = critique.get('score_global', 0)
                approved = critique.get('aprobado', False)
                feedback_history.append(critique)
                
                logging.info(f" 📊 Score Iteración {iteration}: {score}/10")
                
                if approved and score >= 9.0:
                    logging.info(" ✅ CALIDAD ALCANZADA. Saliendo del loop.")
                    break
                    
            except:
                logging.error("❌ Error parseando crítica")
                break

        # ---------------------------------------------------------------------
        # RESULTADO FINAL
        # ---------------------------------------------------------------------
        first_score = feedback_history[0]['score_global'] if feedback_history else 0
        final_score = feedback_history[-1]['score_global'] if feedback_history else 0
        
        return {
            "edited_content": current_draft,
            "changes": current_changes,
            "reflection_stats": {
                "iterations_used": iteration,
                "first_score": first_score,
                "final_score": final_score,
                "improvement_delta": round(final_score - first_score, 2),
                "model_writer": REFLECTION_WRITER_MODEL,
                "model_critic": REFLECTION_CRITIC_MODEL
            }
        }

    except Exception as e:
        logging.error(f"💥 Error crítico en ReflectionLoop: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return {"error": str(e)}

# =============================================================================
# SubmitGeminiProBatch/__init__.py - BATCH GENÉRICO GEMINI PRO (v2 FIXED)
# =============================================================================
# Soporta: layer2_structural, layer3_qualitative, arc_maps
# FIX: Escribe archivo temporal antes de subir (requerido por API)
# =============================================================================

import logging
import json
import os
import tempfile
from google import genai

logging.basicConfig(level=logging.INFO)

# =============================================================================
# PROMPTS POR TIPO DE ANÁLISIS
# =============================================================================

PROMPTS = {
    "layer2_structural": """Eres un Analista de Patrones Narrativos. Analiza la ESTRUCTURA del capítulo.

DATOS DEL CAPÍTULO:
- Título: {chapter_title}
- ID: {chapter_id}
- Tipo: {section_type}
- Palabras: {total_words}
- Eventos: {total_events}
- Ritmo: {ritmo}
- % Diálogo: {dialogo_pct}

PERSONAJES:
{characters_json}

EVENTOS:
{events_json}

Responde SOLO JSON:
{{
  "componentes_narrativos": {{
    "exposicion": {{"presente": true, "efectividad": 8}},
    "conflicto": {{"presente": true, "tipo": "interno/externo", "intensidad": 7}},
    "climax_local": {{"presente": false, "descripcion": ""}},
    "resolucion_parcial": {{"presente": false}}
  }},
  "dinamica_escenas": [
    {{"escena": 1, "tipo": "accion|dialogo|reflexion", "tension": 5, "funcion": "establecer contexto"}}
  ],
  "arcos_detectados": [
    {{"personaje": "nombre", "tipo_arco": "transformacion|revelacion|decision", "fase": "inicio|desarrollo|climax"}}
  ],
  "hooks_y_payoffs": {{
    "setups_abiertos": ["elemento que necesita resolución"],
    "payoffs_ejecutados": ["elemento resuelto de capítulos anteriores"]
  }},
  "score_estructural_global": {{
    "score": 7,
    "fortalezas": ["buena tension"],
    "debilidades": ["transiciones abruptas"]
  }}
}}""",

    "layer3_qualitative": """Eres un Editor Senior evaluando CALIDAD NARRATIVA.

CAPÍTULO: {chapter_title} (ID: {chapter_id})
Posición: {chapter_position}/{total_chapters}

ANÁLISIS ESTRUCTURAL PREVIO:
{structural_summary}

MÉTRICAS:
{metrics_summary}

Evalúa y responde SOLO JSON:
{{
  "evaluacion_tecnica": {{
    "show_vs_tell": {{"score": 8, "ejemplos_tell": ["frase problemática"]}},
    "economia_narrativa": {{"score": 7, "redundancias": ["elemento redundante"]}},
    "claridad_espaciotemporal": {{"score": 9}},
    "consistencia_voz": {{"score": 8}}
  }},
  "evaluacion_impacto": {{
    "engagement": 7,
    "resonancia_emocional": 6,
    "memorabilidad": 5
  }},
  "problemas_detectados": [
    {{"id": "P001", "tipo": "show_tell|redundancia|ritmo|continuidad", "severidad": "alta|media|baja", "ubicacion": "párrafo X", "descripcion": "problema", "sugerencia": "solución"}}
  ],
  "elementos_destacados": ["momento efectivo"],
  "score_calidad_global": 7,
  "prioridad_edicion": "alta|media|baja"
}}""",

    "arc_maps": """Eres un Arquitecto Narrativo. Genera el MAPA DE ARCO para guiar la edición.

CAPÍTULO: {chapter_title} (ID: {chapter_id})
Posición: {chapter_position}/{total_chapters}
Tipo: {section_type}

CONTEXTO DE LA BIBLIA:
- Género: {genero}
- Arcos principales: {arcos_principales}

ANÁLISIS ESTRUCTURAL:
{structural_summary}

ANÁLISIS CUALITATIVO:
{qualitative_summary}

Responde SOLO JSON:
{{
  "funcion_capitulo": {{
    "rol_en_arco_global": "introduccion|desarrollo|climax|resolucion",
    "arcos_activos": ["nombre_arco"],
    "peso_narrativo": 7
  }},
  "elementos_criticos": {{
    "setups_obligatorios": ["elemento que DEBE preservarse"],
    "payoffs_requeridos": ["elemento que DEBE resolverse aquí"],
    "foreshadowing": ["pista sutil a mantener"]
  }},
  "restricciones_edicion": [
    "NO eliminar la mención de X porque es setup para cap Y",
    "Mantener el ritmo lento - es intencional"
  ],
  "oportunidades_mejora": [
    {{"area": "show_tell", "ubicacion": "párrafo X", "impacto_si_se_edita": "alto"}}
  ],
  "dependencias": {{
    "requiere_de_capitulos": [1, 3],
    "afecta_a_capitulos": [15, 20]
  }},
  "es_punto_critico": false,
  "nivel_proteccion": "alto|medio|bajo"
}}"""
}


def build_prompt(analysis_type: str, item: dict, bible: dict = None) -> str:
    """Construye el prompt según el tipo de análisis."""
    
    template = PROMPTS.get(analysis_type, "")
    
    if analysis_type == "layer2_structural":
        characters = item.get('reparto_completo', [])[:10]
        events = item.get('secuencia_eventos', [])[:30]
        metrics = item.get('metricas_agregadas', {})
        
        return template.format(
            chapter_title=item.get('titulo', f"Capítulo {item.get('chapter_id', 0)}"),
            chapter_id=item.get('chapter_id', 0),
            section_type=item.get('section_type', 'CHAPTER'),
            total_words=metrics.get('estructura', {}).get('total_palabras', 0),
            total_events=len(events),
            ritmo=metrics.get('ritmo', {}).get('clasificacion', 'MEDIO'),
            dialogo_pct=metrics.get('composicion', {}).get('porcentaje_dialogo', 0),
            characters_json=json.dumps(characters, ensure_ascii=False, indent=2),
            events_json=json.dumps(events, ensure_ascii=False, indent=2)
        )
    
    elif analysis_type == "layer3_qualitative":
        structural = item.get('layer2_structural', {})
        metrics = item.get('metricas_agregadas', {})
        
        return template.format(
            chapter_title=item.get('titulo', f"Capítulo {item.get('chapter_id', 0)}"),
            chapter_id=item.get('chapter_id', 0),
            chapter_position=item.get('chapter_position', 1),
            total_chapters=item.get('total_chapters', 1),
            structural_summary=json.dumps(structural, ensure_ascii=False)[:3000],
            metrics_summary=json.dumps(metrics, ensure_ascii=False)[:1000]
        )
    
    elif analysis_type == "arc_maps":
        structural = item.get('layer2_structural', {})
        qualitative = item.get('layer3_qualitative', {})
        identidad = bible.get('identidad_obra', {}) if bible else {}
        arco = bible.get('arco_narrativo', {}) if bible else {}
        
        return template.format(
            chapter_title=item.get('titulo', f"Capítulo {item.get('chapter_id', 0)}"),
            chapter_id=item.get('chapter_id', 0),
            chapter_position=item.get('chapter_position', 1),
            total_chapters=item.get('total_chapters', 1),
            section_type=item.get('section_type', 'CHAPTER'),
            genero=identidad.get('genero', 'Ficción'),
            arcos_principales=json.dumps(arco.get('arcos_principales', []), ensure_ascii=False),
            structural_summary=json.dumps(structural, ensure_ascii=False)[:2000],
            qualitative_summary=json.dumps(qualitative, ensure_ascii=False)[:2000]
        )
    
    return ""


def main(batch_input: dict) -> dict:
    """
    Envía batch a Gemini Pro.
    
    Input:
        analysis_type: "layer2_structural" | "layer3_qualitative" | "arc_maps"
        items: lista de capítulos/análisis
        bible: (opcional) para arc_maps
    """
    try:
        analysis_type = batch_input.get('analysis_type', '')
        items = batch_input.get('items', [])
        bible = batch_input.get('bible', {})
        
        if not items:
            return {'error': 'No items provided', 'status': 'error'}
        
        if analysis_type not in PROMPTS:
            return {'error': f'Invalid analysis_type: {analysis_type}', 'status': 'error'}
        
        logging.info(f"📦 Preparando Batch Gemini Pro: {analysis_type} ({len(items)} items)")
        
        # Configurar cliente
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return {'error': 'GEMINI_API_KEY no configurada', 'status': 'error'}
        
        client = genai.Client(api_key=api_key)
        
        # Construir requests
        requests = []
        id_map = []
        
        for item in items:
            chapter_id = item.get('chapter_id', 0)
            prompt = build_prompt(analysis_type, item, bible)
            
            if not prompt:
                logging.warning(f"⚠️ Prompt vacío para capítulo {chapter_id}")
                continue
            
            request_id = f"{analysis_type}-{chapter_id}"
            
            requests.append({
                "key": request_id,
                "request": {
                    "model": "models/gemini-3-pro-preview",
                    "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.3,
                        "maxOutputTokens": 8192,
                        "responseMimeType": "application/json"
                    }
                }
            })
            
            id_map.append({
                "key": request_id,
                "chapter_id": chapter_id,
                "analysis_type": analysis_type
            })
        
        if not requests:
            return {'error': 'No valid requests generated', 'status': 'error'}
        
        # =========================================================================
        # FIX: Escribir a archivo temporal ANTES de subir
        # La API de Gemini requiere una RUTA DE ARCHIVO, no contenido directo
        # =========================================================================
        jsonl_content = "\n".join([json.dumps(r, ensure_ascii=False) for r in requests])
        
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.jsonl',
            encoding='utf-8',
            delete=False
        ) as tmp_file:
            tmp_file.write(jsonl_content)
            tmp_file_path = tmp_file.name
        
        logging.info(f"📁 Archivo temporal creado: {tmp_file_path} ({len(requests)} requests)")
        
        try:
            # Subir archivo usando la RUTA del archivo temporal
            logging.info(f"📤 Subiendo batch a Gemini...")
            
            uploaded_file = client.files.upload(
                file=tmp_file_path,  # ← FIX: Ahora es una RUTA, no contenido
                config={
                    'display_name': f'batch_{analysis_type}_{len(requests)}.jsonl',
                    'mime_type': 'application/jsonl'
                }
            )
            
            logging.info(f"📁 Archivo subido: {uploaded_file.name}")
            
            # Crear batch job
            batch_job = client.batches.create(
                model="models/gemini-3-pro-preview",
                src=uploaded_file.name,
                config={
                    'display_name': f'lya_{analysis_type}'
                }
            )
            
            job_name = batch_job.name if hasattr(batch_job, 'name') else str(batch_job)
            
            logging.info(f"✅ Batch Job creado: {job_name}")
            
            return {
                'status': 'submitted',
                'batch_job_name': job_name,
                'analysis_type': analysis_type,
                'total_requests': len(requests),
                'id_map': id_map
            }
            
        finally:
            # Limpiar archivo temporal
            try:
                os.unlink(tmp_file_path)
                logging.info(f"🗑️ Archivo temporal eliminado")
            except Exception as cleanup_error:
                logging.warning(f"⚠️ No se pudo eliminar archivo temporal: {cleanup_error}")
        
    except Exception as e:
        logging.error(f"❌ Error en SubmitGeminiProBatch: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return {'error': str(e), 'status': 'error'}
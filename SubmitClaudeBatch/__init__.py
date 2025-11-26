# =============================================================================
# SubmitClaudeBatch/__init__.py
# =============================================================================
# 
# Envía capítulos a Claude Batch API (50% descuento)
# Necesita: ANTHROPIC_API_KEY
#
# =============================================================================

import logging
import json
import os

logging.basicConfig(level=logging.INFO)

# Importar el prompt template desde EditChapter
EDIT_CHAPTER_PROMPT_TEMPLATE = """
Eres un EDITOR DE DESARROLLO profesional trabajando en una novela de {{GENRE}}.

═══════════════════════════════════════════════════════════════════════════════
IDENTIDAD DE LA OBRA
═══════════════════════════════════════════════════════════════════════════════
Género: {{GENRE}}
Tono: {{TONE}}
Tema central: {{THEME}}
Estilo de prosa: {{STYLE}}

═══════════════════════════════════════════════════════════════════════════════
VOZ DEL AUTOR - NO MODIFICAR ESTOS ELEMENTOS
═══════════════════════════════════════════════════════════════════════════════
{{NO_CORREGIR_STR}}

═══════════════════════════════════════════════════════════════════════════════
INFORMACIÓN DE ESTE CAPÍTULO
═══════════════════════════════════════════════════════════════════════════════
Título: {{CHAPTER_TITLE}}
Posición en el arco: {{POSITION}}
Ritmo esperado: {{PACING}}

═══════════════════════════════════════════════════════════════════════════════
PERSONAJES EN ESTE CAPÍTULO
═══════════════════════════════════════════════════════════════════════════════
{{CHARACTERS_STR}}

═══════════════════════════════════════════════════════════════════════════════
PROBLEMAS A CORREGIR EN ESTE CAPÍTULO
═══════════════════════════════════════════════════════════════════════════════
{{PROBLEMS_STR}}

═══════════════════════════════════════════════════════════════════════════════
TEXTO A EDITAR
═══════════════════════════════════════════════════════════════════════════════

{{CHAPTER_CONTENT}}

═══════════════════════════════════════════════════════════════════════════════
TU TAREA
═══════════════════════════════════════════════════════════════════════════════

1. CORRIGE únicamente:
    - Los problemas listados arriba
    - Instancias claras de "tell" que deberían ser "show" 
    - Redundancias obvias
    - Errores de continuidad

2. NO TOQUES:
    - NADA de la lista "VOZ DEL AUTOR"
    - El ritmo del capítulo
    - Diálogos breves (la brevedad es intencional)

3. CUANDO TENGAS DUDA: No edites.

═══════════════════════════════════════════════════════════════════════════════
FORMATO DE RESPUESTA (JSON)
═══════════════════════════════════════════════════════════════════════════════

{
  "capitulo_editado": "El texto completo del capítulo editado",
  "cambios_realizados": [
    {
      "tipo": "redundancia|show_tell|continuidad|otro",
      "original": "Texto original",
      "editado": "Texto corregido",
      "justificacion": "Por qué este cambio"
    }
  ],
  "problemas_corregidos": ["ID-001", "ID-002"],
  "notas_editor": "Observaciones generales (opcional)"
}
"""


def build_edit_prompt(chapter: dict, context: dict) -> str:
    """Construye el prompt de edición para un capítulo."""
    
    # Formatear elementos NO_CORREGIR
    no_corregir = context.get('no_corregir', [])
    if no_corregir:
        no_corregir_str = "\n".join([f"- {item}" for item in no_corregir[:10]])
    else:
        no_corregir_str = "- (Sin elementos específicos detectados)"
    
    # Formatear personajes
    personajes = context.get('personajes_en_capitulo', [])
    if personajes:
        personajes_str = "\n".join([
            f"- {p.get('nombre', '?')}: {p.get('rol', '?')} | {p.get('arco', 'Sin arco definido')}"
            for p in personajes[:8]
        ])
    else:
        personajes_str = "- (Sin personajes principales identificados)"
    
    # Formatear problemas
    problemas = context.get('problemas_capitulo', [])
    if problemas:
        problemas_str = "\n".join([
            f"- [{p.get('id', '?')}] {p.get('tipo', '?')}: {p.get('descripcion', '')[:100]}"
            for p in problemas[:5]
        ])
    else:
        problemas_str = "- (Sin problemas específicos detectados para este capítulo)"
    
    # Construir prompt
    prompt = EDIT_CHAPTER_PROMPT_TEMPLATE
    prompt = prompt.replace("{{GENRE}}", context.get('genero', 'ficción'))
    prompt = prompt.replace("{{TONE}}", context.get('tono', 'neutro'))
    prompt = prompt.replace("{{THEME}}", context.get('tema_central', ''))
    prompt = prompt.replace("{{STYLE}}", context.get('estilo_prosa', 'equilibrado'))
    prompt = prompt.replace("{{NO_CORREGIR_STR}}", no_corregir_str)
    prompt = prompt.replace("{{CHAPTER_TITLE}}", chapter.get('title', 'Sin título'))
    prompt = prompt.replace("{{POSITION}}", str(context.get('posicion_arco', 'desconocida')))
    prompt = prompt.replace("{{PACING}}", str(context.get('ritmo_esperado', 'MEDIO')))
    prompt = prompt.replace("{{CHARACTERS_STR}}", personajes_str)
    prompt = prompt.replace("{{PROBLEMS_STR}}", problemas_str)
    prompt = prompt.replace("{{CHAPTER_CONTENT}}", chapter.get('content', ''))
    
    return prompt


def extract_relevant_context(chapter: dict, bible: dict, analysis: dict) -> dict:
    """Extrae contexto relevante para la edición."""
    context = {
        'genero': 'ficción',
        'tono': 'neutro', 
        'tema_central': '',
        'estilo_prosa': 'equilibrado',
        'no_corregir': [],
        'posicion_arco': 'desconocida',
        'ritmo_esperado': 'MEDIO',
        'personajes_en_capitulo': [],
        'problemas_capitulo': []
    }
    
    chapter_id = chapter.get('id', 0)
    try:
        chapter_num = int(chapter_id) if str(chapter_id).isdigit() else 0
    except:
        chapter_num = 0
    
    # 1. IDENTIDAD
    identidad = bible.get('identidad_obra', {})
    context['genero'] = identidad.get('genero', 'ficción')
    context['tono'] = identidad.get('tono_predominante', 'neutro')
    context['tema_central'] = identidad.get('tema_central', '')
    
    # 2. VOZ
    voz = bible.get('voz_del_autor', {})
    context['estilo_prosa'] = voz.get('estilo_detectado', 'equilibrado')
    context['no_corregir'] = voz.get('NO_CORREGIR', [])
    
    # 3. RITMO
    mapa_ritmo = bible.get('mapa_de_ritmo', {})
    for cap in mapa_ritmo.get('capitulos', []):
        if cap.get('numero') == chapter_num or cap.get('capitulo') == chapter_num:
            context['ritmo_esperado'] = cap.get('clasificacion', 'MEDIO')
            context['posicion_arco'] = cap.get('posicion_en_arco', 'desconocida')
            break
    
    # 4. PERSONAJES (simplificado)
    local_chars = analysis.get('reparto_local', [])
    local_names = set()
    for p in local_chars:
        if isinstance(p, dict) and 'nombre' in p:
            local_names.add(p['nombre'].lower())
    
    reparto = bible.get('reparto_completo', {})
    for categoria in ['protagonistas', 'antagonistas', 'secundarios']:
        for char in reparto.get(categoria, []):
            char_name = char.get('nombre', '').lower()
            if char_name in local_names:
                context['personajes_en_capitulo'].append({
                    'nombre': char.get('nombre'),
                    'rol': char.get('rol_arquetipo', categoria),
                    'arco': char.get('arco_personaje', '')
                })
    
    # 5. PROBLEMAS
    problemas = bible.get('problemas_priorizados', {})
    for severidad in ['criticos', 'medios', 'menores']:
        for problema in problemas.get(severidad, []):
            caps_afectados = problema.get('capitulos_afectados', [])
            if chapter_num in caps_afectados or str(chapter_num) in [str(c) for c in caps_afectados]:
                context['problemas_capitulo'].append({
                    'id': problema.get('id', ''),
                    'tipo': problema.get('tipo', ''),
                    'descripcion': problema.get('descripcion', ''),
                    'sugerencia': problema.get('sugerencia', '')
                })
    
    return context


def main(edit_requests: dict) -> dict:
    """
    Envía todos los capítulos a Claude Batch API.
    
    Input: {
        'chapters': [...],
        'bible': {...},
        'analyses': [...]
    }
    Output: {batch_id, chapters_count, status, id_map}
    """
    try:
        from anthropic import Anthropic
        
        # ─────────────────────────────────────────────────────────────────
        # A. CONFIGURACIÓN
        # ─────────────────────────────────────────────────────────────────
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            return {"error": "ANTHROPIC_API_KEY no configurada", "status": "config_error"}
        
        chapters = edit_requests.get('chapters', [])
        bible = edit_requests.get('bible', {})
        analyses = edit_requests.get('analyses', [])
        
        logging.info(f"📦 Preparando Claude Batch de {len(chapters)} capítulos...")
        
        # Crear cliente
        client = Anthropic(api_key=api_key)
        
        # ─────────────────────────────────────────────────────────────────
        # B. PREPARAR REQUESTS
        # ─────────────────────────────────────────────────────────────────
        batch_requests = []
        ordered_ids = []
        
        for chapter in chapters:
            ch_id = str(chapter.get('id', '?'))
            ordered_ids.append(ch_id)
            
            # Buscar análisis correspondiente
            analysis = next(
                (a for a in analyses if str(a.get('chapter_id')) == ch_id),
                {}
            )
            
            # Extraer contexto y construir prompt
            context = extract_relevant_context(chapter, bible, analysis)
            prompt = build_edit_prompt(chapter, context)
            
            # Formato para Batch API
            request = {
                "custom_id": f"chapter-{ch_id}",
                "params": {
                    "model": "claude-sonnet-4-5-20250929",
                    "max_tokens": 8000,
                    "temperature": 0.3,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                }
            }
            batch_requests.append(request)
        
        logging.info(f"📝 {len(batch_requests)} requests preparados")
        logging.info(f"📋 IDs en orden: {ordered_ids[:5]}...")
        
        # ─────────────────────────────────────────────────────────────────
        # C. CREAR BATCH JOB
        # ─────────────────────────────────────────────────────────────────
        logging.info("🚀 Enviando a Claude Batch API...")
        
        message_batch = client.messages.batches.create(
            requests=batch_requests
        )
        
        logging.info(f"✅ Batch creado: {message_batch.id}")
        logging.info(f"   Estado: {message_batch.processing_status}")
        
        return {
            "batch_id": message_batch.id,
            "chapters_count": len(chapters),
            "status": "submitted",
            "processing_status": message_batch.processing_status,
            "id_map": ordered_ids
        }
        
    except ImportError as e:
        logging.error(f"❌ SDK no instalado: {e}")
        return {
            "error": "Instala: pip install anthropic",
            "status": "import_error"
        }
    except Exception as e:
        logging.error(f"❌ Error creando batch: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return {
            "error": str(e),
            "status": "error"
        }
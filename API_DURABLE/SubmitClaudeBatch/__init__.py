# =============================================================================
# SubmitClaudeBatch/__init__.py - SYLPHRENA 4.0 (FIXED)
# =============================================================================
# FIX APLICADO:
#   - Ahora devuelve 'fragment_metadata_map' con metadatos jerárquicos completos
#   - Esto permite que PollClaudeBatchResult reconstruya parent_chapter_id, etc.
# =============================================================================

import logging
import json
import os

logging.basicConfig(level=logging.INFO)

# =============================================================================
# PROMPT OPTIMIZADO PARA EDICIÓN
# =============================================================================

EDIT_PROMPT_OPTIMAL = """Eres un EDITOR PROFESIONAL especializado en {genero}.

IDENTIDAD DE LA OBRA:
- Género: {genero}
- Tono: {tono}
- Tema: {tema}
- Estilo: {estilo}

RESTRICCIONES (NO MODIFICAR):
{no_corregir}

═══════════════════════════════════════════════════════════════════════════════
CAPÍTULO A EDITAR: {titulo}
Posición en estructura: {posicion}
Ritmo detectado: {ritmo}{advertencia_ritmo}
═══════════════════════════════════════════════════════════════════════════════

PERSONAJES EN ESTE CAPÍTULO:
{personajes}

PROBLEMAS ESPECÍFICOS A CORREGIR:
{problemas}

═══════════════════════════════════════════════════════════════════════════════
CONTENIDO:
═══════════════════════════════════════════════════════════════════════════════
{contenido}

═══════════════════════════════════════════════════════════════════════════════
INSTRUCCIONES DE EDICIÓN:
═══════════════════════════════════════════════════════════════════════════════

1. CORRIGE problemas de show vs tell, redundancias y formato de diálogo
2. PRESERVA la voz del autor, ritmo intencional y elementos de setup
3. MANTÉN consistencia con personajes y tono establecido
4. NO añadas contenido nuevo, solo mejora lo existente

RESPONDE ÚNICAMENTE con un JSON válido (sin texto adicional):
{{
    "capitulo_editado": "...[texto completo editado]...",
    "cambios_realizados": [
        {{"tipo": "redundancia|show_tell|dialogo|otro", "original": "...", "editado": "...", "justificacion": "..."}}
    ],
    "problemas_corregidos": ["ID1", "ID2"],
    "notas_editor": "..."
}}
"""


def extract_relevant_context(chapter: dict, bible: dict, analysis: dict) -> dict:
    """Extrae contexto relevante para la edición."""
    
    chapter_id = chapter.get('id', 0)
    parent_id = chapter.get('parent_chapter_id', chapter_id)
    
    try:
        chapter_num = int(parent_id) if str(parent_id).isdigit() else 0
    except:
        chapter_num = 0
    
    context = {
        'genero': 'ficción',
        'tono': 'neutro',
        'tema': '',
        'estilo': 'equilibrado',
        'no_corregir': [],
        'posicion': 'desarrollo',
        'ritmo': 'MEDIO',
        'es_intencional': False,
        'justificacion_ritmo': '',
        'personajes': [],
        'problemas': []
    }
    
    # 1. IDENTIDAD desde la Biblia
    identidad = bible.get('identidad_obra', {})
    context['genero'] = identidad.get('genero', 'ficción')
    context['tono'] = identidad.get('tono_predominante', 'neutro')
    context['tema'] = identidad.get('tema_central', '')
    
    # 2. VOZ DEL AUTOR
    voz = bible.get('voz_del_autor', {})
    context['estilo'] = voz.get('estilo_detectado', 'equilibrado')
    context['no_corregir'] = voz.get('NO_CORREGIR', [])
    
    # 3. POSICIÓN EN ARCO
    arco = bible.get('arco_narrativo', {})
    puntos = arco.get('puntos_clave', {})
    
    for punto, data in puntos.items():
        if isinstance(data, dict) and data.get('capitulo') == chapter_num:
            context['posicion'] = punto
            break
    
    # 4. RITMO del capítulo
    mapa_ritmo = bible.get('mapa_de_ritmo', {})
    for cap in mapa_ritmo.get('capitulos', []):
        if cap.get('numero') == chapter_num or cap.get('capitulo') == chapter_num:
            context['ritmo'] = cap.get('clasificacion', 'MEDIO')
            context['es_intencional'] = cap.get('es_intencional', False)
            context['justificacion_ritmo'] = cap.get('justificacion', '')
            break
    
    # 5. PERSONAJES relevantes
    reparto = bible.get('reparto_completo', {})
    personajes_capitulo = []
    
    for tipo in ['protagonistas', 'antagonistas', 'secundarios']:
        for personaje in reparto.get(tipo, []):
            caps_clave = personaje.get('capitulos_clave', [])
            if chapter_num in caps_clave or not caps_clave:
                personajes_capitulo.append({
                    'nombre': personaje.get('nombre', ''),
                    'rol': personaje.get('rol_arquetipo', tipo),
                    'arco': personaje.get('arco_personaje', ''),
                    'alerta': personaje.get('notas_inconsistencia', [''])[0] if personaje.get('notas_inconsistencia') else ''
                })
    
    context['personajes'] = personajes_capitulo[:5]
    
    # 6. PROBLEMAS específicos
    causalidad = bible.get('analisis_causalidad', {})
    problemas_detectados = causalidad.get('problemas_detectados', {})
    
    problemas_relevantes = []
    for tipo_problema in ['eventos_huerfanos', 'cadenas_rotas', 'contradicciones']:
        for problema in problemas_detectados.get(tipo_problema, []):
            if str(problema.get('capitulo')) == str(chapter_num):
                problemas_relevantes.append({
                    'id': problema.get('evento_id', ''),
                    'tipo': problema.get('tipo_problema', 'otro'),
                    'desc': problema.get('descripcion', '')[:100],
                    'fix': problema.get('sugerencia', '')[:60]
                })
    
    context['problemas'] = problemas_relevantes[:5]
    
    return context


def build_edit_prompt(chapter: dict, context: dict) -> str:
    """Construye prompt optimizado."""
    
    # NO_CORREGIR
    if context['no_corregir']:
        no_corregir_str = "\n".join([f"- {item}" for item in context['no_corregir']])
    else:
        no_corregir_str = "- (Sin restricciones específicas)"
    
    # PERSONAJES
    if context['personajes']:
        lines = []
        for p in context['personajes']:
            line = f"- {p['nombre']}: {p['rol']}"
            if p.get('arco'):
                line += f" | {p['arco']}"
            if p.get('alerta'):
                line += f" | ⚠️ {p['alerta']}"
            lines.append(line)
        personajes_str = "\n".join(lines)
    else:
        personajes_str = "- (Ninguno identificado)"
    
    # PROBLEMAS
    if context['problemas']:
        lines = []
        for p in context['problemas']:
            line = f"- [{p['id']}] {p['tipo']}: {p['desc']}"
            if p.get('fix'):
                line += f"\n  Sugerencia: {p['fix']}"
            lines.append(line)
        problemas_str = "\n".join(lines)
    else:
        problemas_str = "- (Sin problemas específicos para este capítulo)"
    
    # ADVERTENCIA DE RITMO
    advertencia_ritmo = ""
    if context['es_intencional']:
        advertencia_ritmo = f"\n⚠️ RITMO INTENCIONAL: {context['justificacion_ritmo'][:80]}"
    
    prompt = EDIT_PROMPT_OPTIMAL.format(
        genero=context['genero'],
        tono=context['tono'],
        tema=context['tema'],
        estilo=context['estilo'],
        no_corregir=no_corregir_str,
        titulo=chapter.get('title', chapter.get('original_title', 'Sin título')),
        posicion=context['posicion'],
        ritmo=context['ritmo'],
        advertencia_ritmo=advertencia_ritmo,
        personajes=personajes_str,
        problemas=problemas_str,
        contenido=chapter.get('content', '')
    )
    
    return prompt


def main(edit_requests: dict) -> dict:
    """Envía capítulos a Claude Batch API con contexto optimizado."""
    
    try:
        from anthropic import Anthropic
        
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            return {"error": "ANTHROPIC_API_KEY no configurada", "status": "config_error"}
        
        chapters = edit_requests.get('chapters', [])
        bible = edit_requests.get('bible', {})
        analyses = edit_requests.get('analyses', [])
        
        logging.info(f"📦 Preparando Claude Batch OPTIMIZADO: {len(chapters)} capítulos")
        
        client = Anthropic(api_key=api_key)
        
        batch_requests = []
        ordered_ids = []
        
        # =====================================================================
        # FIX: Crear mapa de metadatos jerárquicos para cada fragmento
        # =====================================================================
        fragment_metadata_map = {}
        
        total_prompt_tokens = 0
        
        for chapter in chapters:
            ch_id = str(chapter.get('id', '?'))
            ordered_ids.append(ch_id)
            
            # =====================================================================
            # FIX: Guardar metadatos jerárquicos completos
            # =====================================================================
            fragment_metadata_map[ch_id] = {
                'fragment_id': chapter.get('id', 0),
                'parent_chapter_id': chapter.get('parent_chapter_id', chapter.get('id', 0)),
                'fragment_index': chapter.get('fragment_index', 1),
                'total_fragments': chapter.get('total_fragments', 1),
                'original_title': chapter.get('original_title', chapter.get('title', 'Sin título')),
                'section_type': chapter.get('section_type', 'CHAPTER'),
                'is_first_fragment': chapter.get('is_first_fragment', True),
                'is_last_fragment': chapter.get('is_last_fragment', True),
                'content': chapter.get('content', '')  # Contenido original
            }
            
            # Buscar análisis
            analysis = next(
                (a for a in analyses if str(a.get('chapter_id')) == ch_id or str(a.get('fragment_id')) == ch_id),
                {}
            )
            
            # Contexto SELECTIVO
            context = extract_relevant_context(chapter, bible, analysis)
            
            # Prompt OPTIMIZADO
            prompt = build_edit_prompt(chapter, context)
            
            # Estimar tokens
            prompt_tokens = len(prompt.split()) * 1.3
            total_prompt_tokens += prompt_tokens
            
            request = {
                "custom_id": f"chapter-{ch_id}",
                "params": {
                    "model": "claude-sonnet-4-5-20250929",
                    "max_tokens": 8000,
                    "temperature": 0.3,
                    "messages": [{"role": "user", "content": prompt}]
                }
            }
            batch_requests.append(request)
        
        logging.info(f"📝 {len(batch_requests)} requests")
        logging.info(f"📊 Tokens INPUT estimados: {total_prompt_tokens:,.0f}")
        logging.info(f"💰 Costo INPUT estimado: ${total_prompt_tokens * 1.50 / 1_000_000:.3f}")
        
        message_batch = client.messages.batches.create(requests=batch_requests)
        
        logging.info(f"✅ Batch creado: {message_batch.id}")
        
        return {
            "batch_id": message_batch.id,
            "chapters_count": len(chapters),
            "status": "submitted",
            "processing_status": message_batch.processing_status,
            "id_map": ordered_ids,
            # =====================================================================
            # FIX: Incluir mapa de metadatos para PollClaudeBatchResult
            # =====================================================================
            "fragment_metadata_map": fragment_metadata_map,
            "metrics": {
                "estimated_input_tokens": int(total_prompt_tokens),
                "estimated_input_cost_usd": round(total_prompt_tokens * 1.50 / 1_000_000, 4)
            }
        }
        
    except ImportError as e:
        logging.error(f"❌ SDK no instalado: {e}")
        return {"error": str(e), "status": "import_error"}
    except Exception as e:
        logging.error(f"❌ Error: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return {"error": str(e), "status": "error"}
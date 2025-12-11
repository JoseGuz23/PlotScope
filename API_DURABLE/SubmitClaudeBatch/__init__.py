# =============================================================================
# SubmitClaudeBatch/__init__.py - LYA 5.0 (PROMPT EXPANDIDO)
# =============================================================================
# ACTUALIZACIÓN: Prompt de edición profesional con criterios expandidos
# Ahora incluye las notas de margen y criterios de developmental editor
# =============================================================================

import logging
import json
import os

logging.basicConfig(level=logging.INFO)

# =============================================================================
# PROMPT PROFESIONAL DE EDICIÓN - LYA 5.0
# =============================================================================

EDIT_PROMPT_PROFESSIONAL = """Eres un DEVELOPMENTAL EDITOR profesional editando "{titulo}" ({genero}).

═══════════════════════════════════════════════════════════════════════════════
IDENTIDAD DE LA OBRA
═══════════════════════════════════════════════════════════════════════════════
- Género: {genero}
- Tono: {tono}
- Tema central: {tema}
- Estilo del autor: {estilo}

═══════════════════════════════════════════════════════════════════════════════
RESTRICCIONES ABSOLUTAS (NO MODIFICAR)
═══════════════════════════════════════════════════════════════════════════════
{no_corregir}

═══════════════════════════════════════════════════════════════════════════════
CAPÍTULO A EDITAR: {titulo_capitulo}
═══════════════════════════════════════════════════════════════════════════════
Posición en estructura: {posicion}
Ritmo detectado: {ritmo}{advertencia_ritmo}

PERSONAJES EN ESTE CAPÍTULO:
{personajes}

═══════════════════════════════════════════════════════════════════════════════
NOTAS DE MARGEN DEL EDITOR (priorizar estas correcciones)
═══════════════════════════════════════════════════════════════════════════════
{notas_margen}

═══════════════════════════════════════════════════════════════════════════════
PROBLEMAS ESPECÍFICOS DETECTADOS EN ANÁLISIS
═══════════════════════════════════════════════════════════════════════════════
{problemas}

═══════════════════════════════════════════════════════════════════════════════
TEXTO A EDITAR
═══════════════════════════════════════════════════════════════════════════════
{contenido}

═══════════════════════════════════════════════════════════════════════════════
CRITERIOS DE EDICIÓN PROFESIONAL
═══════════════════════════════════════════════════════════════════════════════

Aplica TODOS estos criterios donde corresponda:

### PROSA
✓ **Redundancias**: Elimina repeticiones de ideas, palabras, o información
✓ **Verbos débiles**: Cambia "estaba", "había", "era" por verbos activos
✓ **Adverbios innecesarios**: Elimina "-mente" cuando el verbo ya es fuerte
✓ **Modificadores excesivos**: "muy", "realmente", "bastante" debilitan
✓ **Muletillas**: Identifica y reduce patrones repetitivos del autor
✓ **Clichés**: Reemplaza frases hechas por expresiones originales
✓ **Ritmo**: Varía longitud de oraciones (cortas para tensión, largas para reflexión)

### NARRATIVA
✓ **Show vs Tell**: Convierte declaraciones en acciones/sensaciones observables
✓ **Profundidad emocional**: Ancla emociones en sensaciones físicas
✓ **Claridad de imágenes**: Asegura que el lector pueda "ver" la escena
✓ **Transiciones**: Suaviza saltos entre escenas/tiempos/lugares
✓ **Anclaje sensorial**: Añade detalles de los 5 sentidos donde falta
✓ **Inmersión**: Elimina lo que saca al lector de la historia

### DIÁLOGO
✓ **Naturalidad**: El diálogo debe sonar como habla real
✓ **Voces distintivas**: Cada personaje debe sonar diferente
✓ **Exposición forzada**: Elimina información que los personajes ya sabrían
✓ **Tags de diálogo**: Prefiere "dijo" sobre alternativas elaboradas
✓ **Subtexto**: Los personajes no siempre dicen lo que piensan

### CONSISTENCIA
✓ **Voz narrativa**: Mantén el mismo registro/tono
✓ **Tiempo verbal**: No mezcles pasado y presente sin razón
✓ **POV**: No violes el punto de vista establecido
✓ **Detalles internos**: No contradigas hechos establecidos

═══════════════════════════════════════════════════════════════════════════════
INSTRUCCIONES DE EDICIÓN
═══════════════════════════════════════════════════════════════════════════════

1. LEE todo el capítulo primero
2. IDENTIFICA problemas según los criterios anteriores
3. PRIORIZA las notas de margen del editor
4. EDITA preservando la voz del autor
5. DOCUMENTA cada cambio con justificación clara
6. NO añadas contenido nuevo, solo mejora lo existente
7. Si algo está bien, NO lo cambies solo por cambiar

CATEGORÍAS DE CAMBIOS:
- prosa: verbos, adverbios, redundancias, ritmo
- narrativa: show/tell, emociones, claridad, transiciones
- dialogo: naturalidad, voces, exposición, tags
- consistencia: voz, tiempo, POV, hechos

═══════════════════════════════════════════════════════════════════════════════
FORMATO DE RESPUESTA (JSON VÁLIDO)
═══════════════════════════════════════════════════════════════════════════════

{{
    "capitulo_editado": "...[texto completo editado, SIN CORTAR]...",
    "cambios_realizados": [
        {{
            "tipo": "redundancia|verbo_debil|adverbio|show_tell|dialogo|ritmo|transicion|claridad|otro",
            "categoria": "prosa|narrativa|dialogo|consistencia",
            "original": "Texto exacto original...",
            "editado": "Texto editado...",
            "justificacion": "Por qué este cambio mejora el texto...",
            "impacto_narrativo": "bajo|medio|alto",
            "nota_margen_relacionada": "ID de nota si aplica, o null"
        }}
    ],
    "notas_atendidas": ["nota-001", "nota-003"],
    "notas_no_atendidas": [
        {{"nota_id": "nota-002", "razon": "Por qué no se pudo atender"}}
    ],
    "estadisticas": {{
        "total_cambios": N,
        "por_categoria": {{"prosa": N, "narrativa": N, "dialogo": N, "consistencia": N}},
        "impacto_alto": N,
        "impacto_medio": N,
        "impacto_bajo": N
    }},
    "notas_editor": "Observaciones generales sobre el capítulo..."
}}
"""


def extract_relevant_context(chapter: dict, bible: dict, analysis: dict, margin_notes: list = None) -> dict:
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
        'problemas': [],
        'notas_margen': []
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
                    'voz': personaje.get('patron_dialogo', ''),
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
    
    # 7. NOTAS DE MARGEN (NUEVO en 5.0)
    if margin_notes:
        context['notas_margen'] = margin_notes
    
    return context


def build_edit_prompt(chapter: dict, context: dict, libro_titulo: str = "") -> str:
    """Construye prompt profesional de edición."""
    
    # NO_CORREGIR
    if context['no_corregir']:
        no_corregir_str = "\n".join([f"⚠️ {item}" for item in context['no_corregir']])
    else:
        no_corregir_str = "- (Sin restricciones específicas)"
    
    # PERSONAJES
    if context['personajes']:
        lines = []
        for p in context['personajes']:
            line = f"• {p['nombre']}: {p['rol']}"
            if p.get('arco'):
                line += f"\n  Arco: {p['arco']}"
            if p.get('voz'):
                line += f"\n  Voz: {p['voz']}"
            if p.get('alerta'):
                line += f"\n  ⚠️ ALERTA: {p['alerta']}"
            lines.append(line)
        personajes_str = "\n".join(lines)
    else:
        personajes_str = "- (Ninguno identificado)"
    
    # NOTAS DE MARGEN (NUEVO)
    notas_str = ""
    if context.get('notas_margen'):
        lines = []
        for nota in context['notas_margen']:
            severidad_emoji = "🔴" if nota.get('severidad') == 'alta' else "🟡" if nota.get('severidad') == 'media' else "🟢"
            lines.append(f"{severidad_emoji} [{nota.get('nota_id', '?')}] {nota.get('tipo', '').upper()}")
            lines.append(f"   Ubicación: Párrafo ~{nota.get('parrafo_aprox', '?')}")
            lines.append(f"   Referencia: \"{nota.get('texto_referencia', '')[:50]}...\"")
            lines.append(f"   Problema: {nota.get('nota', '')}")
            lines.append(f"   Sugerencia: {nota.get('sugerencia', '')}")
            lines.append("")
        notas_str = "\n".join(lines)
    else:
        notas_str = "(Sin notas de margen para este capítulo)"
    
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
        problemas_str = "- (Sin problemas estructurales detectados)"
    
    # ADVERTENCIA DE RITMO
    advertencia_ritmo = ""
    if context['es_intencional']:
        advertencia_ritmo = f"\n⚠️ RITMO INTENCIONAL - NO MODIFICAR: {context['justificacion_ritmo'][:80]}"
    
    prompt = EDIT_PROMPT_PROFESSIONAL.format(
        titulo=libro_titulo or "Sin título",
        genero=context['genero'],
        tono=context['tono'],
        tema=context['tema'],
        estilo=context['estilo'],
        no_corregir=no_corregir_str,
        titulo_capitulo=chapter.get('title', chapter.get('original_title', 'Sin título')),
        posicion=context['posicion'],
        ritmo=context['ritmo'],
        advertencia_ritmo=advertencia_ritmo,
        personajes=personajes_str,
        notas_margen=notas_str,
        problemas=problemas_str,
        contenido=chapter.get('content', '')
    )
    
    return prompt


def main(edit_requests: dict) -> dict:
    """Envía capítulos a Claude Batch API con contexto profesional."""
    
    try:
        from anthropic import Anthropic
        
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            return {"error": "ANTHROPIC_API_KEY no configurada", "status": "config_error"}

        # CORRECCIÓN: El Orchestrator envía 'edit_requests' como lista de {'chapter': frag}
        raw_edit_requests = edit_requests.get('edit_requests', [])

        # Extraer capítulos de la estructura [{'chapter': {...}}, ...]
        if raw_edit_requests and isinstance(raw_edit_requests, list):
            if isinstance(raw_edit_requests[0], dict) and 'chapter' in raw_edit_requests[0]:
                chapters = [req['chapter'] for req in raw_edit_requests]
            else:
                chapters = raw_edit_requests
        else:
            # Fallback: buscar en 'chapters' directamente
            chapters = edit_requests.get('chapters', [])

        bible = edit_requests.get('bible', {})
        analyses = edit_requests.get('consolidated_chapters', edit_requests.get('analyses', []))
        margin_notes_by_chapter = edit_requests.get('margin_notes', {})  # NUEVO: notas de margen
        book_metadata = edit_requests.get('book_metadata', {})
        
        libro_titulo = book_metadata.get('title', bible.get('identidad_obra', {}).get('titulo', 'Sin título'))

        logging.info(f"📦 Preparando Claude Batch PROFESIONAL: {len(chapters)} capítulos")

        # DEBUG: Verificar si chapters está vacío
        if not chapters:
            logging.error(f"❌ CRÍTICO: No hay capítulos para procesar!")
            logging.error(f"   raw_edit_requests type: {type(raw_edit_requests)}")
            logging.error(f"   raw_edit_requests length: {len(raw_edit_requests) if isinstance(raw_edit_requests, list) else 'N/A'}")
            if raw_edit_requests and isinstance(raw_edit_requests, list) and len(raw_edit_requests) > 0:
                logging.error(f"   Primer elemento: {raw_edit_requests[0]}")
            return {"error": "No chapters to process", "status": "error"}
        
        client = Anthropic(api_key=api_key)
        
        batch_requests = []
        ordered_ids = []
        fragment_metadata_map = {}
        
        total_prompt_tokens = 0
        
        for chapter in chapters:
            ch_id = str(chapter.get('id', '?'))
            parent_id = str(chapter.get('parent_chapter_id', ch_id))
            ordered_ids.append(ch_id)
            
            # Guardar metadatos jerárquicos
            fragment_metadata_map[ch_id] = {
                'fragment_id': chapter.get('id', 0),
                'parent_chapter_id': chapter.get('parent_chapter_id', chapter.get('id', 0)),
                'fragment_index': chapter.get('fragment_index', 1),
                'total_fragments': chapter.get('total_fragments', 1),
                'original_title': chapter.get('original_title', chapter.get('title', 'Sin título')),
                'section_type': chapter.get('section_type', 'CHAPTER'),
                'is_first_fragment': chapter.get('is_first_fragment', True),
                'is_last_fragment': chapter.get('is_last_fragment', True),
                'content': chapter.get('content', '')
            }
            
            # Buscar análisis
            analysis = next(
                (a for a in analyses if str(a.get('chapter_id')) == ch_id or str(a.get('fragment_id')) == ch_id),
                {}
            )
            
            # NUEVO: Obtener notas de margen para este capítulo
            chapter_margin_notes = margin_notes_by_chapter.get(parent_id, [])
            if not chapter_margin_notes:
                chapter_margin_notes = margin_notes_by_chapter.get(ch_id, [])
            
            # Contexto con notas de margen
            context = extract_relevant_context(chapter, bible, analysis, chapter_margin_notes)
            
            # Prompt profesional
            prompt = build_edit_prompt(chapter, context, libro_titulo)
            
            # Estimar tokens
            prompt_tokens = len(prompt.split()) * 1.3
            total_prompt_tokens += prompt_tokens
            
            request = {
                "custom_id": f"chapter-{ch_id}",
                "params": {
                    "model": "claude-sonnet-4-5-20250929",
                    "max_tokens": 12000,  # Aumentado para cambios detallados
                    "temperature": 0.3,
                    "messages": [{"role": "user", "content": prompt}]
                }
            }
            batch_requests.append(request)
        
        logging.info(f"📝 {len(batch_requests)} requests preparados")
        logging.info(f"📊 Tokens INPUT estimados: {total_prompt_tokens:,.0f}")
        logging.info(f"💰 Costo INPUT estimado: ${total_prompt_tokens * 3.00 / 1_000_000:.3f}")
        
        message_batch = client.messages.batches.create(requests=batch_requests)
        
        logging.info(f"✅ Batch creado: {message_batch.id}")
        
        return {
            "batch_id": message_batch.id,
            "chapters_count": len(chapters),
            "status": "submitted",
            "processing_status": message_batch.processing_status,
            "id_map": ordered_ids,
            "fragment_metadata_map": fragment_metadata_map,
            "metrics": {
                "estimated_input_tokens": int(total_prompt_tokens),
                "estimated_input_cost_usd": round(total_prompt_tokens * 3.00 / 1_000_000, 4)
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

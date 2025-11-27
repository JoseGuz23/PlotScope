# =============================================================================
# EditChapter/__init__.py - SYLPHRENA 4.0
# =============================================================================
# CAMBIOS DESDE 3.1:
#   - Edición consciente de arco narrativo
#   - Validación de impacto antes de aplicar cambios
#   - Integración con GenerateArcMapForChapter
#   - Rechazo de ediciones que dañan función narrativa
# =============================================================================

import logging
import json
import os
import time
from anthropic import Anthropic, APIError, RateLimitError, APITimeoutError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logging.basicConfig(level=logging.INFO)
logging.getLogger('tenacity').setLevel(logging.WARNING)

# =============================================================================
# PROMPT DE EDICIÓN 4.0 - CONSCIENTE DE ARCO
# =============================================================================

EDIT_CHAPTER_PROMPT_V4 = """
Eres un EDITOR DE DESARROLLO profesional trabajando en una novela de {genero}.

═══════════════════════════════════════════════════════════════════════════════
IDENTIDAD DE LA OBRA
═══════════════════════════════════════════════════════════════════════════════
Género: {genero}
Tono: {tono}
Tema central: {tema}
Estilo de prosa: {estilo}

═══════════════════════════════════════════════════════════════════════════════
VOZ DEL AUTOR - NO MODIFICAR ESTOS ELEMENTOS
═══════════════════════════════════════════════════════════════════════════════
{no_corregir}

═══════════════════════════════════════════════════════════════════════════════
🎯 FUNCIÓN NARRATIVA DE ESTE CAPÍTULO (CRÍTICO)
═══════════════════════════════════════════════════════════════════════════════
Posición en estructura: {posicion_estructura}
Función dramática: {funcion_dramatica}
Arcos de personajes activos: {arcos_activos}
Subtramas en progreso: {subtramas}
Elementos de configuración (setup): {elementos_setup}

⚠️ RESTRICCIONES BASADAS EN FUNCIÓN NARRATIVA:
{restricciones_arco}

═══════════════════════════════════════════════════════════════════════════════
INFORMACIÓN DE ESTE CAPÍTULO
═══════════════════════════════════════════════════════════════════════════════
Título: {titulo}
Título Original: {titulo_original}
Tipo de Sección: {tipo_seccion}
Es fragmento: {es_fragmento}
Contexto de fragmento: {contexto_fragmento}
Ritmo esperado: {ritmo}
Es ritmo intencional: {es_intencional}
{advertencia_ritmo}

═══════════════════════════════════════════════════════════════════════════════
PERSONAJES EN ESTE CAPÍTULO
═══════════════════════════════════════════════════════════════════════════════
{personajes}

═══════════════════════════════════════════════════════════════════════════════
PROBLEMAS A CORREGIR EN ESTE CAPÍTULO
═══════════════════════════════════════════════════════════════════════════════
{problemas}

═══════════════════════════════════════════════════════════════════════════════
EJEMPLOS DE EDICIÓN
═══════════════════════════════════════════════════════════════════════════════

✅ CORRECTO - Show don't tell:
Original: "María estaba muy triste por la noticia."
Editado: "María apartó la mirada. Sus dedos se clavaron en el borde de la mesa."
Razón: Muestra la emoción en lugar de declararla.

✅ CORRECTO - Continuidad:
Original: "Pedro sacó su espada del cinturón" (pero la perdió en cap anterior)
Editado: "Pedro buscó su espada, recordando que la había perdido en el río."
Razón: Corrige inconsistencia manteniendo la narrativa.

❌ RECHAZADO - Cambia la voz:
Original: "Era de noche. Fría. La luna no daba calor."
Incorrecto: "La noche envolvía todo con su manto gélido mientras la luna observaba."
Razón: El autor usa oraciones cortas. La "corrección" destruye su estilo.

❌ RECHAZADO - Daña función narrativa:
Original: "Juan miró a María con desconfianza." (en capítulo de SETUP de conflicto)
Incorrecto: "Juan miró a María con curiosidad."
Razón: La desconfianza es SETUP intencional para conflicto posterior. Eliminarla daña el arco.

═══════════════════════════════════════════════════════════════════════════════
TEXTO A EDITAR
═══════════════════════════════════════════════════════════════════════════════

{contenido}

═══════════════════════════════════════════════════════════════════════════════
TU TAREA
═══════════════════════════════════════════════════════════════════════════════

1. LEE el capítulo completo antes de editar.

2. CORRIGE únicamente:
   - Los problemas listados arriba (PROBLEMAS A CORREGIR)
   - Instancias claras de "tell" que deberían ser "show"
   - Redundancias obvias (palabras/frases repetidas innecesariamente)
   - Errores de continuidad con los personajes descritos

3. PRESERVA LA FUNCIÓN NARRATIVA:
   - NO elimines elementos que son SETUP para capítulos posteriores
   - NO suavices características de personajes que son parte de su arco
   - NO cambies el tono si es intencional para esta posición en la estructura
   - Si un elemento parece "negativo" pero está en la lista de SETUP, PRESÉRVALO

4. NO TOQUES:
   - NADA de la lista "VOZ DEL AUTOR - NO MODIFICAR"
   - El ritmo del capítulo (especialmente si es INTENCIONAL)
   - Elementos listados en "Elementos de configuración (setup)"

5. CUANDO TENGAS DUDA: No edites. Es mejor preservar la intención del autor.

═══════════════════════════════════════════════════════════════════════════════
FORMATO DE RESPUESTA
═══════════════════════════════════════════════════════════════════════════════

Responde SOLO con JSON válido (sin markdown):
{{
  "capitulo_editado": "El texto completo del capítulo editado",
  "cambios_realizados": [
    {{
      "tipo": "redundancia|show_tell|continuidad|otro",
      "original": "Texto original",
      "editado": "Texto corregido",
      "justificacion": "Por qué este cambio",
      "impacto_narrativo": "ninguno|bajo|medio|alto"
    }}
  ],
  "elementos_preservados": ["Lista de elementos de setup que se preservaron intencionalmente"],
  "problemas_corregidos": ["ID-001", "ID-002"],
  "notas_editor": "Observaciones generales sobre el capítulo"
}}
"""

# =============================================================================
# PROMPT DE VALIDACIÓN DE IMPACTO
# =============================================================================

IMPACT_VALIDATION_PROMPT = """
Eres un VALIDADOR DE IMPACTO NARRATIVO. Tu trabajo es verificar que las ediciones 
propuestas NO dañen la función narrativa del capítulo.

MAPA DE ARCO DEL CAPÍTULO:
{arc_map}

TEXTO ORIGINAL:
{original_text}

TEXTO EDITADO PROPUESTO:
{edited_text}

CAMBIOS REALIZADOS:
{changes}

TU TAREA:
1. Identifica TODOS los cambios significativos de contenido (no solo estilo)
2. Para cada cambio, evalúa si altera elementos marcados como importantes en el mapa de arco
3. Clasifica cada cambio como:
   - SEGURO: Cambio puramente estilístico sin impacto en contenido narrativo
   - BENEFICIOSO: Mejora claridad sin alterar función narrativa
   - PROBLEMÁTICO: Daña o elimina elementos importantes para el arco

Responde SOLO con JSON válido:
{{
  "validacion_global": "APROBADO|RECHAZADO|PARCIAL",
  "cambios_evaluados": [
    {{
      "descripcion": "Descripción del cambio",
      "clasificacion": "SEGURO|BENEFICIOSO|PROBLEMÁTICO",
      "razon": "Explicación de la clasificación",
      "elemento_afectado": "Qué elemento del mapa de arco afecta (si aplica)"
    }}
  ],
  "cambios_problematicos": ["Lista de descripciones de cambios problemáticos"],
  "recomendacion": "Descripción de qué hacer"
}}
"""

# =============================================================================
# ESTRATEGIA DE REINTENTOS
# =============================================================================

retry_strategy = retry(
    retry=retry_if_exception_type((RateLimitError, APITimeoutError)),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(4),
    reraise=True
)


@retry_strategy
def call_claude(client, prompt, max_tokens=8000):
    """Llamada a Claude con reintentos"""
    return client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=max_tokens,
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}]
    )


def extract_arc_context(chapter: dict, bible: dict, analysis: dict, arc_map: dict) -> dict:
    """
    Extrae contexto enriquecido incluyendo información del mapa de arco.
    """
    # Obtener ID del capítulo
    chapter_id = chapter.get('id', 0)
    parent_chapter_id = chapter.get('parent_chapter_id', chapter_id)
    
    try:
        chapter_num = int(parent_chapter_id) if str(parent_chapter_id).isdigit() else 0
    except:
        chapter_num = 0
    
    context = {
        # Identidad básica
        'genero': 'ficción',
        'tono': 'neutro',
        'tema': '',
        'estilo': 'equilibrado',
        'no_corregir': [],
        
        # Información de fragmento
        'es_fragmento': chapter.get('is_fragment', False),
        'fragment_index': chapter.get('fragment_index', 1),
        'total_fragments': chapter.get('total_fragments', 1),
        'is_first': chapter.get('is_first_fragment', True),
        'is_last': chapter.get('is_last_fragment', True),
        
        # Ritmo
        'ritmo': 'MEDIO',
        'es_intencional': False,
        'justificacion_ritmo': '',
        
        # Arco narrativo (NUEVO en 4.0)
        'posicion_estructura': arc_map.get('posicion_estructura', 'desarrollo'),
        'funcion_dramatica': arc_map.get('funcion_dramatica', 'desarrollo de trama'),
        'arcos_activos': arc_map.get('arcos_personajes_activos', []),
        'subtramas': arc_map.get('subtramas_en_progreso', []),
        'elementos_setup': arc_map.get('elementos_configuracion', []),
        'restricciones_arco': arc_map.get('restricciones_edicion', []),
        
        # Personajes y problemas
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
    
    # 3. RITMO del capítulo
    mapa_ritmo = bible.get('mapa_de_ritmo', {})
    for cap in mapa_ritmo.get('capitulos', []):
        if cap.get('numero') == chapter_num or cap.get('capitulo') == chapter_num:
            context['ritmo'] = cap.get('clasificacion', 'MEDIO')
            context['es_intencional'] = cap.get('es_intencional', False)
            context['justificacion_ritmo'] = cap.get('justificacion', '')
            break
    
    # 4. PERSONAJES presentes
    local_chars = analysis.get('reparto_local', [])
    nombres_locales = set()
    for p in local_chars:
        if isinstance(p, dict):
            nombre = p.get('nombre', '')
            if nombre:
                nombres_locales.add(nombre.lower())
    
    reparto = bible.get('reparto_completo', {})
    for categoria in ['protagonistas', 'antagonistas', 'secundarios']:
        for char in reparto.get(categoria, []):
            char_name = char.get('nombre', '').lower()
            aliases = [a.lower() for a in char.get('aliases', [])]
            
            if char_name in nombres_locales or any(a in nombres_locales for a in aliases):
                # Buscar fase del arco en arc_map
                fase_arco = 'desarrollo'
                for arco in context['arcos_activos']:
                    if arco.get('personaje', '').lower() == char_name:
                        fase_arco = arco.get('fase', 'desarrollo')
                        break
                
                context['personajes'].append({
                    'nombre': char.get('nombre'),
                    'rol': char.get('rol_arquetipo', categoria),
                    'fase_arco': fase_arco,
                    'consistencia': char.get('consistencia', 'CONSISTENTE')
                })
    
    # 5. PROBLEMAS del capítulo
    problemas = bible.get('problemas_priorizados', {})
    for severidad in ['criticos', 'medios']:
        for problema in problemas.get(severidad, []):
            caps_afectados = problema.get('capitulos_afectados', [])
            if chapter_num in caps_afectados or str(chapter_num) in [str(c) for c in caps_afectados]:
                context['problemas'].append({
                    'id': problema.get('id', '?'),
                    'tipo': problema.get('tipo', 'otro'),
                    'descripcion': problema.get('descripcion', '')[:100],
                    'sugerencia': problema.get('sugerencia', '')[:60]
                })
    
    return context


def build_edit_prompt_v4(chapter: dict, context: dict) -> str:
    """Construye el prompt de edición 4.0 con consciencia de arco."""
    
    # NO_CORREGIR
    if context['no_corregir']:
        no_corregir_str = "\n".join([f"- {item}" for item in context['no_corregir']])
    else:
        no_corregir_str = "- (Sin restricciones específicas)"
    
    # PERSONAJES
    if context['personajes']:
        lines = []
        for p in context['personajes']:
            line = f"- {p['nombre']}: {p['rol']} | Fase de arco: {p['fase_arco']}"
            lines.append(line)
        personajes_str = "\n".join(lines)
    else:
        personajes_str = "- (Ninguno identificado)"
    
    # PROBLEMAS
    if context['problemas']:
        lines = []
        for p in context['problemas']:
            line = f"- [{p['id']}] {p['tipo']}: {p['descripcion']}"
            if p.get('sugerencia'):
                line += f"\n  Sugerencia: {p['sugerencia']}"
            lines.append(line)
        problemas_str = "\n".join(lines)
    else:
        problemas_str = "- (Sin problemas específicos para este capítulo)"
    
    # ARCOS ACTIVOS
    if context['arcos_activos']:
        arcos_str = "\n".join([
            f"- {a.get('personaje', '?')}: Fase {a.get('fase', '?')} - {a.get('descripcion', '')}"
            for a in context['arcos_activos']
        ])
    else:
        arcos_str = "- (Sin arcos activos documentados)"
    
    # SUBTRAMAS
    if context['subtramas']:
        subtramas_str = "\n".join([f"- {s}" for s in context['subtramas']])
    else:
        subtramas_str = "- (Sin subtramas en progreso)"
    
    # ELEMENTOS DE SETUP
    if context['elementos_setup']:
        setup_str = "\n".join([f"- {e}" for e in context['elementos_setup']])
    else:
        setup_str = "- (Sin elementos de configuración documentados)"
    
    # RESTRICCIONES DE ARCO
    if context['restricciones_arco']:
        restricciones_str = "\n".join([f"⚠️ {r}" for r in context['restricciones_arco']])
    else:
        restricciones_str = "- (Sin restricciones especiales)"
    
    # ADVERTENCIA DE RITMO
    advertencia_ritmo = ""
    if context['es_intencional']:
        advertencia_ritmo = f"\n⚠️ RITMO INTENCIONAL: {context['justificacion_ritmo'][:80]}"
    
    # CONTEXTO DE FRAGMENTO
    contexto_fragmento = "Capítulo completo (no fragmentado)"
    if context['es_fragmento']:
        frag_idx = context['fragment_index']
        total = context['total_fragments']
        if context['is_first']:
            contexto_fragmento = f"INICIO del capítulo (fragmento {frag_idx}/{total}). El contenido continúa en fragmentos posteriores."
        elif context['is_last']:
            contexto_fragmento = f"FINAL del capítulo (fragmento {frag_idx}/{total}). Este contenido viene de fragmentos anteriores."
        else:
            contexto_fragmento = f"MEDIO del capítulo (fragmento {frag_idx}/{total}). El contenido viene de antes y continúa después."
    
    prompt = EDIT_CHAPTER_PROMPT_V4.format(
        genero=context['genero'],
        tono=context['tono'],
        tema=context['tema'],
        estilo=context['estilo'],
        no_corregir=no_corregir_str,
        posicion_estructura=context['posicion_estructura'],
        funcion_dramatica=context['funcion_dramatica'],
        arcos_activos=arcos_str,
        subtramas=subtramas_str,
        elementos_setup=setup_str,
        restricciones_arco=restricciones_str,
        titulo=chapter.get('title', 'Sin título'),
        titulo_original=chapter.get('original_title', 'Sin título'),
        tipo_seccion=chapter.get('section_type', 'CHAPTER'),
        es_fragmento="SÍ" if context['es_fragmento'] else "NO",
        contexto_fragmento=contexto_fragmento,
        ritmo=context['ritmo'],
        es_intencional="SÍ" if context['es_intencional'] else "No",
        advertencia_ritmo=advertencia_ritmo,
        personajes=personajes_str,
        problemas=problemas_str,
        contenido=chapter.get('content', '')
    )
    
    return prompt


def validate_edit_impact(client, original_text: str, edited_text: str, 
                         changes: list, arc_map: dict) -> dict:
    """
    Valida que las ediciones no dañen la función narrativa.
    Solo se ejecuta para capítulos marcados como estructuralmente críticos.
    """
    prompt = IMPACT_VALIDATION_PROMPT.format(
        arc_map=json.dumps(arc_map, ensure_ascii=False, indent=2),
        original_text=original_text[:5000],  # Limitar para no exceder contexto
        edited_text=edited_text[:5000],
        changes=json.dumps(changes, ensure_ascii=False, indent=2)
    )
    
    try:
        response = call_claude(client, prompt, max_tokens=2000)
        response_text = response.content[0].text.strip()
        
        # Limpiar markdown
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        return json.loads(response_text.strip())
    except Exception as e:
        logging.warning(f"⚠️ Error en validación de impacto: {e}")
        return {"validacion_global": "APROBADO", "cambios_evaluados": []}


def main(edit_input_json) -> dict:
    """
    Edita un capítulo usando Claude Sonnet con consciencia de arco narrativo.
    
    Input esperado:
    {
        'chapter': {...},          # Fragmento con metadatos jerárquicos
        'bible': {...},            # Biblia validada
        'analysis': {...},         # Análisis del capítulo
        'arc_map': {...},          # Mapa de arco generado por GenerateArcMapForChapter
        'is_critical': bool        # Si requiere validación de impacto
    }
    """
    chapter_id = "?"
    chapter_title = "Sin título"
    
    try:
        start_time = time.time()
        
        # 1. PARSEO DE INPUT
        if isinstance(edit_input_json, str):
            edit_input = json.loads(edit_input_json)
        else:
            edit_input = edit_input_json
        
        chapter = edit_input.get('chapter', {})
        bible = edit_input.get('bible', {})
        analysis = edit_input.get('analysis', {})
        arc_map = edit_input.get('arc_map', {})
        is_critical = edit_input.get('is_critical', False)
        
        chapter_id = chapter.get('id', '?')
        chapter_title = chapter.get('title', 'Sin título')
        original_content = chapter.get('content', '')
        
        logging.info(f"✏️ EditChapter v4.0 - Procesando: {chapter_title} (ID: {chapter_id})")
        logging.info(f"   Función narrativa: {arc_map.get('funcion_dramatica', 'N/A')}")
        logging.info(f"   Es crítico: {is_critical}")
        
        # 2. EXTRAER CONTEXTO CON ARCO
        context = extract_arc_context(chapter, bible, analysis, arc_map)
        
        # 3. CONSTRUIR PROMPT
        prompt = build_edit_prompt_v4(chapter, context)
        
        # 4. LLAMAR A CLAUDE
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY no configurada")
        
        client = Anthropic(api_key=api_key)
        
        logging.info(f"🤖 Llamando a Claude Sonnet...")
        response = call_claude(client, prompt)
        
        # 5. PROCESAR RESPUESTA
        response_text = response.content[0].text
        
        try:
            clean_response = response_text.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]
            elif clean_response.startswith("```"):
                clean_response = clean_response[3:]
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]
            clean_response = clean_response.strip()
            
            edit_result = json.loads(clean_response)
            edited_content = edit_result.get('capitulo_editado', response_text)
            cambios = edit_result.get('cambios_realizados', [])
            elementos_preservados = edit_result.get('elementos_preservados', [])
            problemas_corregidos = edit_result.get('problemas_corregidos', [])
            notas = edit_result.get('notas_editor', '')
            
        except json.JSONDecodeError:
            logging.warning(f"   ⚠️ Respuesta no es JSON, usando texto directo")
            edited_content = response_text
            cambios = []
            elementos_preservados = []
            problemas_corregidos = []
            notas = "Respuesta no estructurada"
        
        # 6. VALIDACIÓN DE IMPACTO (solo para capítulos críticos)
        validation_result = None
        if is_critical and cambios:
            logging.info(f"🔍 Ejecutando validación de impacto...")
            validation_result = validate_edit_impact(
                client, original_content, edited_content, cambios, arc_map
            )
            
            if validation_result.get('validacion_global') == 'RECHAZADO':
                logging.warning(f"⚠️ Edición rechazada por validación de impacto")
                logging.warning(f"   Cambios problemáticos: {validation_result.get('cambios_problematicos', [])}")
                
                # Revertir a original con nota
                edited_content = original_content
                cambios = []
                notas = f"EDICIÓN REVERTIDA: {validation_result.get('recomendacion', 'Cambios dañaban función narrativa')}"
        
        # 7. MÉTRICAS
        elapsed = time.time() - start_time
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cost_input = input_tokens * 3.00 / 1_000_000
        cost_output = output_tokens * 15.00 / 1_000_000
        total_cost = cost_input + cost_output
        
        result = {
            'chapter_id': chapter_id,
            'parent_chapter_id': chapter.get('parent_chapter_id', chapter_id),
            'fragment_index': chapter.get('fragment_index', 1),
            'total_fragments': chapter.get('total_fragments', 1),
            'titulo': chapter_title,
            'titulo_original': chapter.get('original_title', chapter_title),
            'contenido_editado': edited_content,
            'contenido_original': original_content,
            'cambios_realizados': cambios,
            'elementos_preservados': elementos_preservados,
            'problemas_corregidos': problemas_corregidos,
            'notas_editor': notas,
            'contexto_aplicado': {
                'funcion_dramatica': context['funcion_dramatica'],
                'posicion_estructura': context['posicion_estructura'],
                'ritmo': context['ritmo'],
                'fue_intencional': context['es_intencional'],
                'problemas_identificados': len(context['problemas']),
                'elementos_setup_count': len(context['elementos_setup'])
            },
            'validacion_impacto': validation_result,
            'metadata': {
                'status': 'success',
                'version': '4.0',
                'modelo': 'claude-sonnet-4-5-20250929',
                'tiempo_segundos': round(elapsed, 2),
                'costo_usd': round(total_cost, 4),
                'tokens_in': input_tokens,
                'tokens_out': output_tokens,
                'fue_validado': is_critical,
                'fue_revertido': validation_result.get('validacion_global') == 'RECHAZADO' if validation_result else False
            }
        }
        
        logging.info(f"✅ Capítulo editado en {elapsed:.2f}s | Costo: ${total_cost:.4f}")
        if elementos_preservados:
            logging.info(f"   Elementos preservados: {len(elementos_preservados)}")
        
        return result
        
    except Exception as e:
        logging.error(f"💥 Error en EditChapter: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        
        return {
            'chapter_id': chapter_id,
            'parent_chapter_id': chapter.get('parent_chapter_id', chapter_id) if 'chapter' in dir() else chapter_id,
            'titulo': chapter_title,
            'contenido_editado': chapter.get('content', '') if 'chapter' in dir() else '',
            'contenido_original': chapter.get('content', '') if 'chapter' in dir() else '',
            'error': str(e),
            'metadata': {'status': 'error', 'version': '4.0', 'error_message': str(e)}
        }

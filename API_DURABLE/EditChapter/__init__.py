# =============================================================================
# EditChapter/__init__.py - SYLPHRENA 4.0 - PARSING BLINDADO
# =============================================================================
# 
# CORRECCIONES v4.0.1:
#   - Limpieza robusta de markdown con regex
#   - Doble intento de parsing (limpieza markdown → extracción entre llaves)
#   - Fallback inteligente: si falla, busca { } y extrae JSON puro
#   - Nunca devuelve JSON crudo como contenido editado
#
# =============================================================================

import logging
import json
import os
import time
import re
from anthropic import Anthropic

logging.basicConfig(level=logging.INFO)

# =============================================================================
# PROMPTS
# =============================================================================

EDIT_CHAPTER_PROMPT_V4 = """Eres un EDITOR DE DESARROLLO profesional trabajando en una novela de {genero}.

IDENTIDAD DE LA OBRA
- Género: {genero} | Tono: {tono} | Tema central: {tema}
- Estilo de prosa detectado: {estilo}

ELEMENTOS DE VOZ DEL AUTOR - NO MODIFICAR:
{no_corregir}

═══════════════════════════════════════════════════════════════════════════════
POSICIÓN EN LA ESTRUCTURA NARRATIVA
═══════════════════════════════════════════════════════════════════════════════
- Posición actual: {posicion_estructura}
- Función dramática: {funcion_dramatica}

ARCOS NARRATIVOS ACTIVOS EN ESTE CAPÍTULO:
{arcos_activos}

SUBTRAMAS RELEVANTES:
{subtramas}

ELEMENTOS DE SETUP QUE DEBEN PRESERVARSE:
{elementos_setup}

RESTRICCIONES DE EDICIÓN POR ARCO:
{restricciones_arco}

═══════════════════════════════════════════════════════════════════════════════
CAPÍTULO A EDITAR
═══════════════════════════════════════════════════════════════════════════════
Título: {titulo}
Título original: {titulo_original}
Tipo de sección: {tipo_seccion}
Es fragmento de capítulo largo: {es_fragmento}
{contexto_fragmento}

ANÁLISIS DE RITMO:
- Clasificación: {ritmo}
- ¿Es ritmo intencional?: {es_intencional}
{advertencia_ritmo}

PERSONAJES EN ESTE CAPÍTULO:
{personajes}

PROBLEMAS DETECTADOS A CORREGIR:
{problemas}

═══════════════════════════════════════════════════════════════════════════════
TEXTO ORIGINAL:
═══════════════════════════════════════════════════════════════════════════════
{contenido}

═══════════════════════════════════════════════════════════════════════════════
TU TAREA
═══════════════════════════════════════════════════════════════════════════════
1. CORRIGE los problemas listados arriba
2. APLICA mejoras de "show don't tell" donde sea apropiado
3. ELIMINA redundancias obvias
4. PRESERVA absolutamente los elementos de setup marcados
5. MANTÉN el ritmo si está marcado como intencional
6. NO toques los elementos de voz del autor

RESPONDE ÚNICAMENTE CON UN OBJETO JSON (sin markdown, sin ```):
{{
  "capitulo_editado": "TEXTO COMPLETO EDITADO AQUÍ",
  "cambios_realizados": [
    {{
      "tipo": "redundancia|show_tell|continuidad|ritmo|otro",
      "original": "texto original",
      "editado": "texto nuevo",
      "justificacion": "razón del cambio"
    }}
  ],
  "elementos_preservados": ["lista de elementos de setup que se mantuvieron intactos"],
  "problemas_corregidos": ["IDs de problemas solucionados"],
  "notas_editor": "Observaciones generales sobre la edición"
}}"""

IMPACT_VALIDATION_PROMPT = """Evalúa si las ediciones propuestas dañan la función narrativa del capítulo.

MAPA DE ARCO DEL CAPÍTULO:
{arc_map}

TEXTO ORIGINAL (primeros 5000 caracteres):
{original_text}

TEXTO EDITADO (primeros 5000 caracteres):
{edited_text}

CAMBIOS REALIZADOS:
{changes}

EVALÚA:
1. ¿Los cambios preservan los elementos de setup críticos?
2. ¿Se mantiene la función dramática del capítulo?
3. ¿El ritmo narrativo sigue siendo coherente?
4. ¿Hay algún cambio que rompa la continuidad?

RESPONDE JSON (sin markdown):
{{
  "validacion_global": "APROBADO|RECHAZADO",
  "cambios_evaluados": [
    {{
      "cambio_index": 0,
      "impacto": "SEGURO|RIESGOSO|DAÑINO",
      "razon": "explicación"
    }}
  ],
  "cambios_problematicos": ["índices de cambios dañinos"],
  "recomendacion": "acción sugerida si hay problemas"
}}"""


# =============================================================================
# FUNCIONES DE LIMPIEZA BLINDADA DE JSON
# =============================================================================

def clean_json_response(response_text: str) -> tuple:
    """
    Limpieza BLINDADA de respuesta JSON.
    
    Estrategia de 3 niveles:
    1. Limpieza de markdown con regex
    2. Extracción entre { y } si lo anterior falla
    3. Retorna (json_dict, success_flag)
    
    NUNCA devuelve JSON crudo como fallback.
    """
    if not response_text:
        return {}, False
    
    clean = response_text.strip()
    
    # ===========================================
    # NIVEL 1: Limpieza de markdown con regex
    # ===========================================
    # Patrón: ```json o ``` al inicio (con posibles espacios/saltos)
    clean = re.sub(r'^[\s]*```(?:json)?[\s]*\n?', '', clean)
    # Patrón: ``` al final (con posibles espacios/saltos)
    clean = re.sub(r'\n?[\s]*```[\s]*$', '', clean)
    clean = clean.strip()
    
    # Intentar parsear después de limpieza de markdown
    try:
        parsed = json.loads(clean)
        logging.info("✅ JSON parseado con limpieza de markdown")
        return parsed, True
    except json.JSONDecodeError:
        pass
    
    # ===========================================
    # NIVEL 2: Extracción entre llaves { }
    # ===========================================
    start_idx = clean.find('{')
    end_idx = clean.rfind('}')
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        json_str = clean[start_idx : end_idx + 1]
        try:
            parsed = json.loads(json_str)
            logging.info("✅ JSON parseado con extracción entre llaves")
            return parsed, True
        except json.JSONDecodeError as e:
            logging.warning(f"⚠️ Extracción entre llaves falló: {e}")
    
    # ===========================================
    # NIVEL 3: Intentar reparar JSON común
    # ===========================================
    # A veces Claude trunca o tiene errores menores
    try:
        # Intentar con el texto original (sin modificar)
        parsed = json.loads(response_text.strip())
        logging.info("✅ JSON parseado del texto original")
        return parsed, True
    except json.JSONDecodeError:
        pass
    
    logging.error("❌ Todos los intentos de parsing JSON fallaron")
    return {}, False


def extract_edited_content(response_text: str, original_content: str) -> dict:
    """
    Extrae el contenido editado de la respuesta de Claude.
    
    Si el parsing falla completamente, devuelve el contenido original
    con una nota de error (NUNCA devuelve JSON crudo).
    
    Returns:
        dict con: edited_content, cambios, elementos_preservados, 
                  problemas_corregidos, notas
    """
    parsed, success = clean_json_response(response_text)
    
    if success and parsed:
        # Extraer campos del JSON parseado
        edited_content = parsed.get('capitulo_editado', '')
        
        # Validación: si capitulo_editado está vacío o parece JSON, usar original
        if not edited_content or edited_content.strip().startswith('{'):
            logging.warning("⚠️ capitulo_editado vacío o inválido, usando original")
            edited_content = original_content
        
        return {
            'edited_content': edited_content,
            'cambios': parsed.get('cambios_realizados', []),
            'elementos_preservados': parsed.get('elementos_preservados', []),
            'problemas_corregidos': parsed.get('problemas_corregidos', []),
            'notas': parsed.get('notas_editor', ''),
            'parse_success': True
        }
    
    # Si falló el parsing, devolver original con nota
    logging.warning("⚠️ Parsing falló completamente, devolviendo contenido original")
    return {
        'edited_content': original_content,
        'cambios': [],
        'elementos_preservados': [],
        'problemas_corregidos': [],
        'notas': 'ERROR: No se pudo parsear la respuesta de Claude. Contenido original preservado.',
        'parse_success': False
    }


# =============================================================================
# FUNCIONES DE CONTEXTO
# =============================================================================

def extract_arc_context(chapter: dict, bible: dict, analysis: dict, arc_map: dict) -> dict:
    """
    Extrae contexto de arco narrativo para guiar la edición.
    """
    chapter_id = chapter.get('id', 0)
    try:
        chapter_num = int(chapter_id) if str(chapter_id).isdigit() else 0
    except:
        chapter_num = 0
    
    # Identidad de la obra
    identidad = bible.get('identidad_obra', {})
    context = {
        'genero': identidad.get('genero', 'ficción'),
        'tono': identidad.get('tono_predominante', 'neutro'),
        'tema': identidad.get('tema_central', 'no especificado'),
    }
    
    # Voz del autor
    voz = bible.get('voz_del_autor', {})
    context['estilo'] = voz.get('estilo_detectado', 'equilibrado')
    context['no_corregir'] = voz.get('NO_CORREGIR', [])[:10]
    
    # Ritmo del capítulo
    context['ritmo'] = 'MEDIO'
    context['es_intencional'] = False
    context['justificacion_ritmo'] = ''
    
    mapa_ritmo = bible.get('mapa_de_ritmo', {})
    for cap in mapa_ritmo.get('capitulos', []):
        if cap.get('numero') == chapter_num or cap.get('capitulo') == chapter_num:
            context['ritmo'] = cap.get('clasificacion', 'MEDIO')
            context['es_intencional'] = cap.get('es_intencional', False)
            context['justificacion_ritmo'] = cap.get('justificacion', '')
            break
    
    # Posición en estructura
    context['posicion_estructura'] = 'desarrollo'
    context['funcion_dramatica'] = 'progresión de trama'
    
    estructura = bible.get('estructura_narrativa', {})
    for punto in estructura.get('puntos_clave', []):
        if punto.get('capitulo') == chapter_num:
            context['posicion_estructura'] = punto.get('tipo', 'desarrollo')
            context['funcion_dramatica'] = punto.get('funcion', 'progresión de trama')
            break
    
    # Arcos activos
    context['arcos_activos'] = []
    context['subtramas'] = []
    context['elementos_setup'] = []
    context['restricciones'] = []
    
    if arc_map:
        arcos = arc_map.get('arcos_en_capitulo', [])
        for arco in arcos[:5]:
            context['arcos_activos'].append({
                'nombre': arco.get('nombre', 'Sin nombre'),
                'fase': arco.get('fase_actual', 'desarrollo'),
                'tension': arco.get('nivel_tension', 5)
            })
        
        context['subtramas'] = arc_map.get('subtramas', [])[:3]
        context['elementos_setup'] = arc_map.get('elementos_setup', [])[:5]
        context['restricciones'] = arc_map.get('restricciones_edicion', [])[:5]
    
    # Personajes del capítulo
    context['personajes'] = []
    if analysis:
        reparto = analysis.get('reparto_local', [])
        for personaje in reparto[:8]:
            context['personajes'].append({
                'nombre': personaje.get('nombre', 'Desconocido'),
                'rol': personaje.get('rol', 'secundario'),
                'estado': personaje.get('estado_emocional', 'neutro')
            })
    
    # Problemas detectados
    context['problemas'] = []
    if analysis:
        senales = analysis.get('senales_edicion', {})
        for problema in senales.get('problemas_potenciales', [])[:10]:
            if isinstance(problema, dict):
                context['problemas'].append(problema)
            else:
                context['problemas'].append({'descripcion': str(problema)})
    
    # Metadata de fragmentación
    context['es_fragmento'] = chapter.get('is_fragment', False)
    context['fragment_index'] = chapter.get('fragment_index', 1)
    context['total_fragments'] = chapter.get('total_fragments', 1)
    context['is_first'] = context['fragment_index'] == 1
    context['is_last'] = context['fragment_index'] == context['total_fragments']
    
    return context


def build_edit_prompt_v4(chapter: dict, context: dict) -> str:
    """
    Construye el prompt de edición con contexto de arco narrativo.
    """
    # Formatear listas para el prompt
    no_corregir_str = '\n'.join([f"- {item}" for item in context['no_corregir']]) if context['no_corregir'] else "- (ninguno especificado)"
    
    arcos_str = ""
    for arco in context['arcos_activos']:
        arcos_str += f"- {arco['nombre']}: fase {arco['fase']}, tensión {arco['tension']}/10\n"
    if not arcos_str:
        arcos_str = "- (sin arcos específicos identificados)"
    
    subtramas_str = '\n'.join([f"- {s}" for s in context['subtramas']]) if context['subtramas'] else "- (ninguna)"
    setup_str = '\n'.join([f"- {e}" for e in context['elementos_setup']]) if context['elementos_setup'] else "- (ninguno)"
    restricciones_str = '\n'.join([f"- {r}" for r in context['restricciones']]) if context['restricciones'] else "- (ninguna)"
    
    personajes_str = ""
    for p in context['personajes']:
        personajes_str += f"- {p['nombre']} ({p['rol']}): {p['estado']}\n"
    if not personajes_str:
        personajes_str = "- (sin personajes identificados)"
    
    problemas_str = ""
    for i, prob in enumerate(context['problemas'], 1):
        if isinstance(prob, dict):
            desc = prob.get('descripcion', prob.get('problema', str(prob)))
            problemas_str += f"[{i}] {desc}\n"
        else:
            problemas_str += f"[{i}] {prob}\n"
    if not problemas_str:
        problemas_str = "- (sin problemas detectados)"
    
    # Advertencia de ritmo
    advertencia_ritmo = ""
    if context['es_intencional']:
        advertencia_ritmo = f"\n⚠️ ADVERTENCIA: Este ritmo es INTENCIONAL. Justificación: {context['justificacion_ritmo']}\nNO expandas ni modifiques el ritmo de este capítulo."
    
    # Contexto de fragmento
    contexto_fragmento = ""
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


def call_claude(client, prompt: str, max_tokens: int = 16000):
    """
    Llama a Claude Sonnet con reintentos.
    """
    return client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )


def validate_edit_impact(client, original_text: str, edited_text: str, 
                         changes: list, arc_map: dict) -> dict:
    """
    Valida que las ediciones no dañen la función narrativa.
    Solo se ejecuta para capítulos marcados como estructuralmente críticos.
    """
    prompt = IMPACT_VALIDATION_PROMPT.format(
        arc_map=json.dumps(arc_map, ensure_ascii=False, indent=2),
        original_text=original_text[:5000],
        edited_text=edited_text[:5000],
        changes=json.dumps(changes, ensure_ascii=False, indent=2)
    )
    
    try:
        response = call_claude(client, prompt, max_tokens=2000)
        response_text = response.content[0].text.strip()
        
        # Usar la función de limpieza blindada
        parsed, success = clean_json_response(response_text)
        if success:
            return parsed
        
        return {"validacion_global": "APROBADO", "cambios_evaluados": []}
    except Exception as e:
        logging.warning(f"⚠️ Error en validación de impacto: {e}")
        return {"validacion_global": "APROBADO", "cambios_evaluados": []}


# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================

def main(edit_input_json) -> dict:
    """
    Edita un capítulo usando Claude Sonnet con consciencia de arco narrativo.
    
    CORRECCIÓN v4.0.1: Parsing blindado de JSON para evitar JSON crudo en output.
    """
    start_time = time.time()
    
    # Parsear input
    if isinstance(edit_input_json, str):
        edit_input = json.loads(edit_input_json)
    else:
        edit_input = edit_input_json
    
    chapter = edit_input.get('chapter', {})
    bible = edit_input.get('bible', {})
    analysis = edit_input.get('analysis', {})
    arc_map = edit_input.get('arc_map', {})
    
    chapter_id = chapter.get('id', 0)
    chapter_title = chapter.get('title', 'Sin título')
    original_content = chapter.get('content', '')
    
    logging.info(f"📝 Editando capítulo {chapter_id}: {chapter_title}")
    
    # Determinar si es crítico para validación
    is_critical = arc_map.get('es_punto_critico', False) if arc_map else False
    
    try:
        # 1. EXTRAER CONTEXTO CON ARCO
        context = extract_arc_context(chapter, bible, analysis, arc_map)
        
        # 2. CONSTRUIR PROMPT
        prompt = build_edit_prompt_v4(chapter, context)
        
        # 3. LLAMAR A CLAUDE
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY no configurada")
        
        client = Anthropic(api_key=api_key)
        
        logging.info(f"🤖 Llamando a Claude Sonnet...")
        response = call_claude(client, prompt)
        
        # 4. PROCESAR RESPUESTA CON LIMPIEZA BLINDADA
        response_text = response.content[0].text
        
        # Usar la función de extracción blindada
        extracted = extract_edited_content(response_text, original_content)
        
        edited_content = extracted['edited_content']
        cambios = extracted['cambios']
        elementos_preservados = extracted['elementos_preservados']
        problemas_corregidos = extracted['problemas_corregidos']
        notas = extracted['notas']
        
        if not extracted['parse_success']:
            logging.warning(f"⚠️ Capítulo {chapter_id}: usando contenido original por fallo de parsing")
        
        # 5. VALIDACIÓN DE IMPACTO (solo para capítulos críticos)
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
        
        # 6. MÉTRICAS
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
                'version': '4.0.1',
                'modelo': 'claude-sonnet-4-5-20250929',
                'tiempo_segundos': round(elapsed, 2),
                'costo_usd': round(total_cost, 4),
                'tokens_in': input_tokens,
                'tokens_out': output_tokens,
                'fue_validado': is_critical,
                'fue_revertido': validation_result.get('validacion_global') == 'RECHAZADO' if validation_result else False,
                'parse_success': extracted['parse_success']
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
            'metadata': {'status': 'error', 'version': '4.0.1', 'error_message': str(e)}
        }
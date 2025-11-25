# EditChapter/__init__.py (v2.0)

import logging
import json
import os
import time
from anthropic import Anthropic, APIError, RateLimitError, APITimeoutError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logging.basicConfig(level=logging.INFO)
logging.getLogger('tenacity').setLevel(logging.WARNING)

# Estrategia de reintentos para Claude
retry_strategy = retry(
    retry=retry_if_exception_type((RateLimitError, APITimeoutError)),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(4),
    reraise=True
)

@retry_strategy
def call_claude(client, prompt):
    """Llamada a Claude con reintentos"""
    return client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=8000,
        temperature=0.3,  # Bajo para edición consistente
        messages=[
            {"role": "user", "content": prompt}
        ]
    )


def extract_relevant_context(chapter: dict, bible: dict, analysis: dict) -> dict:
    """
    RAG Mejorado: Extrae SOLO el contexto relevante de la Biblia v2.0
    para este capítulo específico. Ahorra tokens y mejora precisión.
    """
    context = {
        # Identidad
        'genero': 'ficción',
        'tono': 'neutro',
        'tema_central': '',
        
        # Voz del autor
        'estilo_prosa': 'equilibrado',
        'no_corregir': [],
        
        # Este capítulo
        'posicion_arco': 'desconocida',
        'ritmo_esperado': 'MEDIO',
        'es_intencional': False,
        'justificacion_ritmo': '',
        
        # Personajes relevantes
        'personajes_en_capitulo': [],
        
        # Problemas a corregir
        'problemas_capitulo': [],
        
        # Instrucciones especiales
        'instrucciones_globales': [],
        'instrucciones_capitulo': [],
        'patrones_mantener': []
    }
    
    # Obtener número de capítulo
    chapter_id = chapter.get('id', 0)
    try:
        chapter_num = int(chapter_id) if str(chapter_id).isdigit() else 0
    except:
        chapter_num = 0
    
    # =================================================================
    # 1. IDENTIDAD DE LA OBRA
    # =================================================================
    identidad = bible.get('identidad_obra', {})
    context['genero'] = identidad.get('genero', 'ficción')
    context['tono'] = identidad.get('tono_predominante', 'neutro')
    context['tema_central'] = identidad.get('tema_central', '')
    
    # =================================================================
    # 2. VOZ DEL AUTOR (CRÍTICO - NO TOCAR)
    # =================================================================
    voz = bible.get('voz_del_autor', {})
    context['estilo_prosa'] = voz.get('estilo_detectado', 'equilibrado')
    context['no_corregir'] = voz.get('NO_CORREGIR', [])
    
    caracteristicas = voz.get('caracteristicas', {})
    context['longitud_oraciones'] = caracteristicas.get('longitud_oraciones', 'variable')
    context['densidad_dialogo'] = caracteristicas.get('densidad_dialogo', 'media')
    
    # =================================================================
    # 3. RITMO DE ESTE CAPÍTULO
    # =================================================================
    mapa_ritmo = bible.get('mapa_de_ritmo', {})
    for cap in mapa_ritmo.get('capitulos', []):
        if cap.get('numero') == chapter_num or cap.get('capitulo') == chapter_num:
            context['ritmo_esperado'] = cap.get('clasificacion', 'MEDIO')
            context['es_intencional'] = cap.get('es_intencional', False)
            context['justificacion_ritmo'] = cap.get('justificacion', '')
            context['posicion_arco'] = cap.get('posicion_en_arco', 'desconocida')
            break
    
    # =================================================================
    # 4. PERSONAJES EN ESTE CAPÍTULO
    # =================================================================
    # Obtener nombres del análisis local
    local_chars = analysis.get('reparto_local', [])
    local_names = set()
    for p in local_chars:
        if isinstance(p, dict) and 'nombre' in p:
            local_names.add(p['nombre'].lower())
    
    # Buscar en la Biblia información completa de esos personajes
    reparto = bible.get('reparto_completo', {})
    for categoria in ['protagonistas', 'antagonistas', 'secundarios']:
        for char in reparto.get(categoria, []):
            char_name = char.get('nombre', '').lower()
            aliases = [a.lower() for a in char.get('aliases', [])]
            
            # Match si nombre o alias aparece en el capítulo
            if char_name in local_names or any(a in local_names for a in aliases):
                context['personajes_en_capitulo'].append({
                    'nombre': char.get('nombre'),
                    'rol': char.get('rol_arquetipo', categoria),
                    'arco': char.get('arco_personaje', ''),
                    'consistencia': char.get('consistencia', 'CONSISTENTE'),
                    'notas': char.get('notas_inconsistencia', [])
                })
    
    # =================================================================
    # 5. PROBLEMAS A CORREGIR EN ESTE CAPÍTULO
    # =================================================================
    problemas = bible.get('problemas_priorizados', {})
    
    for severidad in ['criticos', 'medios', 'menores']:
        for problema in problemas.get(severidad, []):
            caps_afectados = problema.get('capitulos_afectados', [])
            
            # Verificar si este capítulo está afectado
            if chapter_num in caps_afectados or str(chapter_num) in [str(c) for c in caps_afectados]:
                context['problemas_capitulo'].append({
                    'severidad': severidad.upper().rstrip('S'),  # CRITICO, MEDIO, MENOR
                    'id': problema.get('id', ''),
                    'tipo': problema.get('tipo', ''),
                    'descripcion': problema.get('descripcion', ''),
                    'sugerencia': problema.get('sugerencia', '')
                })
    
    # =================================================================
    # 6. INSTRUCCIONES PARA CLAUDE
    # =================================================================
    guia = bible.get('guia_para_claude', {})
    context['instrucciones_globales'] = guia.get('instrucciones_globales', [])
    context['patrones_mantener'] = guia.get('patrones_a_mantener', [])
    
    # Instrucciones específicas para este capítulo
    for cap_especial in guia.get('capitulos_especiales', []):
        if cap_especial.get('capitulo') == chapter_num:
            context['instrucciones_capitulo'].append(cap_especial.get('instruccion', ''))
            context['que_no_tocar'] = cap_especial.get('que_no_tocar', [])
    
    return context


def build_edit_prompt(chapter: dict, context: dict) -> str:
    """
    Construye el prompt para Claude con few-shot examples y contexto enriquecido.
    """
    
    # Formatear personajes
    personajes_str = "Ninguno identificado"
    if context['personajes_en_capitulo']:
        personajes_str = json.dumps(context['personajes_en_capitulo'], indent=2, ensure_ascii=False)
    
    # Formatear problemas
    problemas_str = "Ninguno detectado"
    if context['problemas_capitulo']:
        problemas_str = json.dumps(context['problemas_capitulo'], indent=2, ensure_ascii=False)
    
    # Formatear instrucciones globales
    instrucciones_globales_str = "\n".join(f"- {i}" for i in context['instrucciones_globales']) or "- Ninguna específica"
    
    # Formatear NO_CORREGIR
    no_corregir_str = "\n".join(f"- {item}" for item in context['no_corregir']) or "- Ninguna restricción específica"
    
    # Formatear instrucciones del capítulo
    instrucciones_cap_str = ""
    if context['instrucciones_capitulo']:
        instrucciones_cap_str = "\n⚠️ INSTRUCCIONES ESPECIALES PARA ESTE CAPÍTULO:\n"
        instrucciones_cap_str += "\n".join(f"- {i}" for i in context['instrucciones_capitulo'])
    
    # Advertencia de ritmo intencional
    advertencia_ritmo = ""
    if context['es_intencional']:
        advertencia_ritmo = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ⚠️  ADVERTENCIA: RITMO INTENCIONAL                                          ║
║                                                                              ║
║  Este capítulo tiene ritmo {context['ritmo_esperado']} A PROPÓSITO.          ║
║  Razón: {context['justificacion_ritmo'][:60]}...                             ║
║                                                                              ║
║  NO intentes "arreglarlo" acelerando, expandiendo o cambiando el ritmo.     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

    prompt = f"""
Eres un EDITOR DE DESARROLLO profesional trabajando en una novela de {context['genero']}.

═══════════════════════════════════════════════════════════════════════════════
IDENTIDAD DE LA OBRA
═══════════════════════════════════════════════════════════════════════════════
Género: {context['genero']}
Tono: {context['tono']}
Tema central: {context['tema_central']}
Estilo de prosa: {context['estilo_prosa']}

═══════════════════════════════════════════════════════════════════════════════
VOZ DEL AUTOR - NO MODIFICAR ESTOS ELEMENTOS
═══════════════════════════════════════════════════════════════════════════════
{no_corregir_str}

═══════════════════════════════════════════════════════════════════════════════
INFORMACIÓN DE ESTE CAPÍTULO
═══════════════════════════════════════════════════════════════════════════════
Título: {chapter.get('title', 'Sin título')}
Posición en el arco: {context['posicion_arco']}
Ritmo esperado: {context['ritmo_esperado']}
Es ritmo intencional: {"SÍ" if context['es_intencional'] else "No"}
{advertencia_ritmo}
{instrucciones_cap_str}

═══════════════════════════════════════════════════════════════════════════════
PERSONAJES EN ESTE CAPÍTULO
═══════════════════════════════════════════════════════════════════════════════
{personajes_str}

═══════════════════════════════════════════════════════════════════════════════
PROBLEMAS A CORREGIR EN ESTE CAPÍTULO
═══════════════════════════════════════════════════════════════════════════════
{problemas_str}

═══════════════════════════════════════════════════════════════════════════════
INSTRUCCIONES GENERALES DE EDICIÓN
═══════════════════════════════════════════════════════════════════════════════
{instrucciones_globales_str}

═══════════════════════════════════════════════════════════════════════════════
EJEMPLOS DE EDICIÓN (APRENDE DE ESTOS)
═══════════════════════════════════════════════════════════════════════════════

✅ CORRECCIÓN ACEPTABLE - Eliminar redundancia:
ORIGINAL: "Juan caminó hacia la puerta. Juan abrió la puerta lentamente."
EDITADO: "Juan caminó hacia la puerta y la abrió lentamente."
RAZÓN: Elimina repetición sin cambiar significado ni voz.

✅ CORRECCIÓN ACEPTABLE - Show don't tell:
ORIGINAL: "María estaba muy triste por la noticia."
EDITADO: "María apartó la mirada. Sus dedos se clavaron en el borde de la mesa."
RAZÓN: Muestra la emoción en lugar de declararla.

✅ CORRECCIÓN ACEPTABLE - Continuidad:
ORIGINAL: "Pedro sacó su espada del cinturón" (pero la perdió en cap anterior)
EDITADO: "Pedro buscó su espada, recordando que la había perdido en el río."
RAZÓN: Corrige inconsistencia manteniendo la narrativa.

❌ CORRECCIÓN RECHAZADA - Cambia la voz:
ORIGINAL: "Era de noche. Fría. La luna no daba calor."
INCORRECTO: "La noche envolvía todo con su manto gélido mientras la luna, indiferente, observaba desde lo alto."
RAZÓN: El autor usa oraciones cortas y directas. La "corrección" impone estilo barroco. DESTRUYE LA VOZ.

❌ CORRECCIÓN RECHAZADA - Expande pausa intencional:
ORIGINAL (en capítulo de recuperación): "Caminó por el jardín. Las flores estaban marchitas."
INCORRECTO: "Caminó lentamente por el sendero del jardín, observando con melancolía cómo las flores, otrora vibrantes, ahora mostraban los signos del otoño..."
RAZÓN: Si el capítulo es intencionalmente austero, expandir ROMPE el ritmo narrativo.

❌ CORRECCIÓN RECHAZADA - Añade donde no debe:
ORIGINAL: "—No —dijo."
INCORRECTO: "—No —respondió él, con voz firme y decidida, mirándola directamente a los ojos."
RAZÓN: La brevedad es intencional. No añadir adornos innecesarios a diálogos deliberadamente secos.

❌ CORRECCIÓN RECHAZADA - Arregla lo que no está roto:
ORIGINAL: "Corrió. Saltó. Rodó. Se levantó."
INCORRECTO: "Corrió hacia la salida, luego saltó el obstáculo, rodó al caer y finalmente se levantó."
RAZÓN: La fragmentación crea ritmo de acción. Unir las oraciones DESTRUYE la tensión.

═══════════════════════════════════════════════════════════════════════════════
TEXTO A EDITAR
═══════════════════════════════════════════════════════════════════════════════

{chapter.get('content', '')}

═══════════════════════════════════════════════════════════════════════════════
TU TAREA
═══════════════════════════════════════════════════════════════════════════════

1. LEE el capítulo completo antes de editar.

2. CORRIGE únicamente:
   - Los problemas listados arriba (PROBLEMAS A CORREGIR)
   - Instancias claras de "tell" que deberían ser "show" 
   - Redundancias obvias (palabras/frases repetidas innecesariamente)
   - Errores de continuidad con los personajes descritos

3. NO TOQUES:
   - NADA de la lista "VOZ DEL AUTOR - NO MODIFICAR"
   - El ritmo del capítulo (especialmente si es INTENCIONAL)
   - La longitud característica de oraciones del autor
   - Diálogos breves (la brevedad suele ser intencional)
   - Fragmentos de oración (pueden ser estilísticos)

4. CUANDO TENGAS DUDA: No edites. Es mejor preservar la voz del autor 
   que "mejorar" algo que era intencional.

5. MARCA cambios significativos con [NOTA EDITORIAL: explicación breve]
   - Solo para cambios de contenido/continuidad
   - NO para correcciones menores de estilo

═══════════════════════════════════════════════════════════════════════════════
FORMATO DE RESPUESTA
═══════════════════════════════════════════════════════════════════════════════

Responde con este formato JSON:

{{
  "capitulo_editado": "El texto completo del capítulo editado",
  "cambios_realizados": [
    {{
      "tipo": "redundancia|show_tell|continuidad|otro",
      "original": "Texto original",
      "editado": "Texto corregido",
      "justificacion": "Por qué este cambio"
    }}
  ],
  "problemas_corregidos": ["ID-001", "ID-002"],
  "notas_editor": "Observaciones generales sobre el capítulo (opcional)"
}}
"""
    
    return prompt


def main(edit_input_json) -> dict:
    """
    Edita un capítulo usando Claude Sonnet con contexto enriquecido v2.0
    
    Input: JSON con {chapter, bible, analysis}
    Output: Capítulo editado con metadata
    """
    chapter_id = "?"
    chapter_title = "Sin título"
    
    try:
        start_time = time.time()
        
        # =================================================================
        # 1. PARSEO DE INPUT
        # =================================================================
        if isinstance(edit_input_json, str):
            edit_input = json.loads(edit_input_json)
        else:
            edit_input = edit_input_json
        
        chapter = edit_input.get('chapter', {})
        bible = edit_input.get('bible', {})
        analysis = edit_input.get('analysis', {})
        
        chapter_id = chapter.get('id', '?')
        chapter_title = chapter.get('title', 'Sin título')
        
        logging.info(f"✏️ EditChapter v2.0 - Procesando: {chapter_title} (ID: {chapter_id})")
        
        # =================================================================
        # 2. EXTRAER CONTEXTO RELEVANTE
        # =================================================================
        context = extract_relevant_context(chapter, bible, analysis)
        
        logging.info(f"   - Ritmo: {context['ritmo_esperado']} ({'INTENCIONAL' if context['es_intencional'] else 'normal'})")
        logging.info(f"   - Personajes: {len(context['personajes_en_capitulo'])}")
        logging.info(f"   - Problemas a corregir: {len(context['problemas_capitulo'])}")
        
        # =================================================================
        # 3. CONSTRUIR PROMPT
        # =================================================================
        prompt = build_edit_prompt(chapter, context)
        
        # =================================================================
        # 4. LLAMAR A CLAUDE
        # =================================================================
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY no configurada")
        
        client = Anthropic(api_key=api_key)
        
        logging.info(f"🤖 Llamando a Claude Sonnet...")
        response = call_claude(client, prompt)
        
        elapsed = time.time() - start_time
        
        # =================================================================
        # 5. PROCESAR RESPUESTA
        # =================================================================
        response_text = response.content[0].text
        
        # Intentar parsear como JSON
        try:
            # Limpiar posibles artifacts de markdown
            clean_response = response_text.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]
            if clean_response.startswith("```"):
                clean_response = clean_response[3:]
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]
            clean_response = clean_response.strip()
            
            edit_result = json.loads(clean_response)
            edited_content = edit_result.get('capitulo_editado', response_text)
            cambios = edit_result.get('cambios_realizados', [])
            problemas_corregidos = edit_result.get('problemas_corregidos', [])
            notas = edit_result.get('notas_editor', '')
            
        except json.JSONDecodeError:
            # Si no es JSON válido, asumir que es el texto editado directamente
            logging.warning(f"   ⚠️ Respuesta no es JSON, usando texto directo")
            edited_content = response_text
            cambios = []
            problemas_corregidos = []
            notas = "Respuesta no estructurada"
        
        # =================================================================
        # 6. CALCULAR MÉTRICAS Y COSTO
        # =================================================================
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        
        # Precios Claude Sonnet 4.5 (noviembre 2025)
        cost_input = input_tokens * 3.00 / 1_000_000
        cost_output = output_tokens * 15.00 / 1_000_000
        total_cost = cost_input + cost_output
        
        # =================================================================
        # 7. CONSTRUIR RESULTADO
        # =================================================================
        result = {
            'chapter_id': chapter_id,
            'titulo': chapter_title,
            'contenido_editado': edited_content,
            'cambios_realizados': cambios,
            'problemas_corregidos': problemas_corregidos,
            'notas_editor': notas,
            'contexto_aplicado': {
                'ritmo': context['ritmo_esperado'],
                'fue_intencional': context['es_intencional'],
                'problemas_identificados': len(context['problemas_capitulo']),
                'personajes_en_capitulo': len(context['personajes_en_capitulo'])
            },
            'metadata': {
                'status': 'success',
                'modelo': 'claude-sonnet-4-5-20250929',
                'tiempo_segundos': round(elapsed, 2),
                'tokens': {
                    'input': input_tokens,
                    'output': output_tokens
                },
                'costo_usd': round(total_cost, 4)
            }
        }
        
        logging.info(f"✅ Capítulo editado en {elapsed:.2f}s | Costo: ${total_cost:.4f}")
        logging.info(f"   - Cambios realizados: {len(cambios)}")
        
        return result
        
    except Exception as e:
        logging.error(f"💥 Error en EditChapter: {str(e)}")
        return {
            'chapter_id': chapter_id,
            'titulo': chapter_title,
            'contenido_editado': chapter.get('content', ''),  # Devolver original si falla
            'cambios_realizados': [],
            'error': str(e),
            'metadata': {
                'status': 'error',
                'error_message': str(e)
            }
        }
# =============================================================================
# SubmitClaudeBatch/__init__.py - PUNTO ÓPTIMO v2.0
# =============================================================================
# 
# Optimizaciones:
#   - Prompt reducido ~40% (mantiene ejemplos clave)
#   - RAG selectivo (solo contexto relevante por capítulo)
#   - Métricas de tokens estimados
#
# =============================================================================

import logging
import json
import os

logging.basicConfig(level=logging.INFO)

# ═══════════════════════════════════════════════════════════════════════════════
# PROMPT PUNTO ÓPTIMO
# - Mantiene 4 ejemplos esenciales (2 buenos, 2 malos)
# - Elimina decoraciones y repeticiones
# - ~1200 tokens vs ~2000 original
# ═══════════════════════════════════════════════════════════════════════════════

EDIT_PROMPT_OPTIMAL = """Eres un EDITOR DE DESARROLLO profesional trabajando en una novela de {genero}.

IDENTIDAD DE LA OBRA
- Género: {genero} | Tono: {tono} | Tema: {tema}
- Estilo de prosa: {estilo}

VOZ DEL AUTOR - NO MODIFICAR:
{no_corregir}

CAPÍTULO ACTUAL
- Título: {titulo}
- Posición en arco: {posicion}
- Ritmo: {ritmo}{advertencia_ritmo}

PERSONAJES EN ESTE CAPÍTULO:
{personajes}

PROBLEMAS A CORREGIR:
{problemas}

EJEMPLOS DE EDICIÓN:

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
Incorrecto: "La noche envolvía todo con su manto gélido mientras la luna observaba desde lo alto."
Razón: El autor usa oraciones cortas. La "corrección" destruye su estilo.

❌ RECHAZADO - Expande ritmo intencional:
Original (capítulo lento): "Caminó por el jardín. Las flores estaban marchitas."
Incorrecto: "Caminó lentamente por el sendero, observando con melancolía las flores marchitas..."
Razón: Si el ritmo es intencional, expandir ROMPE la narrativa.

TEXTO A EDITAR:

{contenido}

TU TAREA:
1. Corrige SOLO: problemas listados + "tell vs show" + redundancias + continuidad
2. NO toques: voz del autor, ritmo intencional, diálogos breves
3. Ante la duda: NO edites

RESPONDE JSON (sin markdown):
{{"capitulo_editado": "texto completo", "cambios_realizados": [{{"tipo": "redundancia|show_tell|continuidad|otro", "original": "texto", "editado": "texto", "justificacion": "razón"}}], "problemas_corregidos": ["ID-001"], "notas_editor": "observaciones opcionales"}}"""


def extract_relevant_context(chapter: dict, bible: dict, analysis: dict) -> dict:
    """
    RAG SELECTIVO: Extrae SOLO lo relevante para este capítulo.
    ~800-1000 tokens vs ~5000 de la biblia completa.
    """
    chapter_id = chapter.get('id', 0)
    try:
        chapter_num = int(chapter_id) if str(chapter_id).isdigit() else 0
    except:
        chapter_num = 0
    
    # 1. IDENTIDAD (~50 tokens)
    identidad = bible.get('identidad_obra', {})
    context = {
        'genero': identidad.get('genero', 'ficción'),
        'tono': identidad.get('tono_predominante', 'neutro'),
        'tema': identidad.get('tema_central', 'no especificado'),
    }
    
    # 2. VOZ (~150 tokens)
    voz = bible.get('voz_del_autor', {})
    context['estilo'] = voz.get('estilo_detectado', 'equilibrado')
    context['no_corregir'] = voz.get('NO_CORREGIR', [])[:7]  # Max 7 items
    
    # 3. RITMO de este capítulo (~50 tokens)
    context['ritmo'] = 'MEDIO'
    context['posicion'] = 'desarrollo'
    context['es_intencional'] = False
    context['justificacion_ritmo'] = ''
    
    mapa_ritmo = bible.get('mapa_de_ritmo', {})
    for cap in mapa_ritmo.get('capitulos', []):
        if cap.get('numero') == chapter_num or cap.get('capitulo') == chapter_num:
            context['ritmo'] = cap.get('clasificacion', 'MEDIO')
            context['posicion'] = cap.get('posicion_en_arco', 'desarrollo')
            context['es_intencional'] = cap.get('es_intencional', False)
            context['justificacion_ritmo'] = cap.get('justificacion', '')
            break
    
    # 4. PERSONAJES solo los presentes (~200 tokens max)
    local_chars = analysis.get('reparto_local', [])
    nombres_locales = set()
    for p in local_chars:
        if isinstance(p, dict):
            nombre = p.get('nombre', '')
            if nombre:
                nombres_locales.add(nombre.lower())
    
    personajes_relevantes = []
    reparto = bible.get('reparto_completo', {})
    
    for categoria in ['protagonistas', 'antagonistas', 'secundarios']:
        for char in reparto.get(categoria, []):
            char_name = char.get('nombre', '').lower()
            aliases = [a.lower() for a in char.get('aliases', [])]
            
            if char_name in nombres_locales or any(a in nombres_locales for a in aliases):
                info = {
                    'nombre': char.get('nombre'),
                    'rol': char.get('rol_arquetipo', categoria),
                }
                # Solo agregar arco si existe y es corto
                arco = char.get('arco_personaje', '')
                if arco and len(arco) < 80:
                    info['arco'] = arco
                
                # Marcar si tiene inconsistencias
                if char.get('consistencia') != 'CONSISTENTE':
                    notas = char.get('notas_inconsistencia', [])
                    if notas:
                        info['alerta'] = notas[0][:60]
                
                personajes_relevantes.append(info)
    
    context['personajes'] = personajes_relevantes[:8]  # Max 8
    
    # 5. PROBLEMAS que afectan ESTE capítulo (~150 tokens max)
    problemas_relevantes = []
    problemas = bible.get('problemas_priorizados', {})
    
    for severidad in ['criticos', 'medios']:
        for problema in problemas.get(severidad, []):
            caps_afectados = problema.get('capitulos_afectados', [])
            
            if chapter_num in caps_afectados or str(chapter_num) in [str(c) for c in caps_afectados]:
                problemas_relevantes.append({
                    'id': problema.get('id', '?'),
                    'tipo': problema.get('tipo', 'otro'),
                    'desc': problema.get('descripcion', '')[:100],
                    'fix': problema.get('sugerencia', '')[:60]
                })
    
    context['problemas'] = problemas_relevantes[:5]  # Max 5
    
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
        titulo=chapter.get('title', 'Sin título'),
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
        total_prompt_tokens = 0
        
        for chapter in chapters:
            ch_id = str(chapter.get('id', '?'))
            ordered_ids.append(ch_id)
            
            # Buscar análisis
            analysis = next(
                (a for a in analyses if str(a.get('chapter_id')) == ch_id),
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
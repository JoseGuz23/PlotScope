# =============================================================================
# SubmitClaudeBatch/__init__.py - LYA 6.0 (Vertex AI Migration)
# =============================================================================
# MIGRACIÓN VERTEX AI: Uso de Vertex AI Batch Prediction para Claude.
# Se mantiene la lógica de prompts pero se adapta la infraestructura.
# =============================================================================

import logging
import json
import os
import sys
import uuid
from typing import Dict, List, Any

# Agregar directorio padre para importar vertex_utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
try:
    from vertex_utils import submit_vertex_batch_job, upload_jsonl_to_gcs, format_claude_vertex_request
    from config_models import CLAUDE_SONNET_MODEL
except ImportError:
    # Fallback para desarrollo local si el path falla
    from API_DURABLE.vertex_utils import submit_vertex_batch_job, upload_jsonl_to_gcs, format_claude_vertex_request
    from API_DURABLE.config_models import CLAUDE_SONNET_MODEL

logging.basicConfig(level=logging.INFO)

# =============================================================================
# 1. PROMPT DE SISTEMA (ESTÁTICO)
# =============================================================================
STATIC_SYSTEM_TEMPLATE = """Eres un DEVELOPMENTAL EDITOR profesional editando "{titulo}" ({genero}).

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
CRITERIOS DE EDICIÓN PROFESIONAL
═══════════════════════════════════════════════════════════════════════════════
Aplica TODOS estos criterios donde corresponda:

### PROSA
✓ **Redundancias**: Elimina repeticiones de ideas o palabras.
✓ **Verbos débiles**: Cambia "estaba", "había" por verbos activos.
✓ **Adverbios**: Elimina "-mente" si el verbo es fuerte.
✓ **Muletillas**: Reduce patrones repetitivos.
✓ **Ritmo**: Varía longitud de oraciones según la tensión.

### NARRATIVA
✓ **Show vs Tell**: Convierte explicaciones en acciones.
✓ **Profundidad emocional**: Ancla emociones en sensaciones físicas.
✓ **Claridad**: Asegura que la geografía y tiempo sean claros.
✓ **Inmersión**: Elimina lo que saca al lector de la historia.

### DIÁLOGO
✓ **Naturalidad**: Debe sonar real, no robótico.
✓ **Voces**: Cada personaje debe sonar distinto.
✓ **Exposición**: Elimina "As You Know Bob" (explicaciones obvias).
✓ **Tags**: Prefiere "dijo" sobre verbos distractores.

### CONSISTENCIA
✓ **Voz narrativa**: Mantén el registro.
✓ **POV**: No violes el punto de vista establecido.

═══════════════════════════════════════════════════════════════════════════════
INSTRUCCIONES DE EDICIÓN
═══════════════════════════════════════════════════════════════════════════════
1. LEE el capítulo proporcionado por el usuario.
2. IDENTIFICA problemas según los criterios y las NOTAS DE MARGEN específicas.
3. EDITA preservando la voz del autor.
4. DOCUMENTA cada cambio.
5. NO añadas contenido nuevo (trama), solo mejora la ejecución.

═══════════════════════════════════════════════════════════════════════════════
FORMATO DE RESPUESTA (JSON VÁLIDO)
═══════════════════════════════════════════════════════════════════════════════
{{
    "id_referencia": "DEBE_COINCIDIR_CON_INPUT",
    "capitulo_editado": "...[texto completo editado, SIN CORTAR]...",
    "cambios_realizados": [
        {{
            "tipo": "redundancia|verbo_debil|adverbio|show_tell|dialogo|ritmo|transicion|claridad|otro",
            "categoria": "prosa|narrativa|dialogo|consistencia",
            "original": "Texto exacto original...",
            "editado": "Texto editado...",
            "justificacion": "Por qué mejora el texto...",
            "impacto_narrativo": "bajo|medio|alto",
            "nota_margen_relacionada": "ID o null"
        }}
    ],
    "notas_atendidas": ["nota-ID"],
    "notas_no_atendidas": [
        {{"nota_id": "ID", "razon": "..."}}
    ],
    "estadisticas": {{
        "total_cambios": N,
        "por_categoria": {{"prosa": N, "narrativa": N, "dialogo": N, "consistencia": N}}
    }},
    "notas_editor": "Observaciones finales..."
}}
"""

# =============================================================================
# 2. PROMPT DE USUARIO (DINÁMICO)
# =============================================================================
DYNAMIC_USER_TEMPLATE = """Por favor edita este capítulo siguiendo las instrucciones del sistema.

IMPORTANTE: En tu respuesta JSON, el campo "id_referencia" DEBE SER EXACTAMENTE: "{chapter_id}"

═══════════════════════════════════════════════════════════════════════════════
DATOS DEL CAPÍTULO: {titulo_capitulo}
═══════════════════════════════════════════════════════════════════════════════
Posición: {posicion}
Ritmo actual: {ritmo} {advertencia_ritmo}

PERSONAJES PRESENTES:
{personajes}

═══════════════════════════════════════════════════════════════════════════════
NOTAS DE MARGEN A CORREGIR (PRIORIDAD ALTA):
═══════════════════════════════════════════════════════════════════════════════
{notas_margen}

═══════════════════════════════════════════════════════════════════════════════
PROBLEMAS ESTRUCTURALES:
═══════════════════════════════════════════════════════════════════════════════
{problemas}

═══════════════════════════════════════════════════════════════════════════════
TEXTO ORIGINAL:
═══════════════════════════════════════════════════════════════════════════════
{contenido}
"""

def extract_book_context(bible: Dict, book_metadata: Dict) -> Dict:
    identidad = bible.get('identidad_obra', {})
    voz = bible.get('voz_del_autor', {})
    
    return {
        'titulo': book_metadata.get('title', identidad.get('titulo', 'Sin título')),
        'genero': identidad.get('genero', 'ficción'),
        'tono': identidad.get('tono_predominante', 'neutro'),
        'tema': identidad.get('tema_central', ''),
        'estilo': voz.get('estilo_detectado', 'equilibrado'),
        'no_corregir': voz.get('NO_CORREGIR', [])
    }

def extract_chapter_context(chapter: Dict, bible: Dict, margin_notes: List) -> Dict:
    chapter_id = chapter.get('id', 0)
    parent_id = chapter.get('parent_chapter_id', chapter_id)
    
    try:
        ch_num = int(parent_id) if str(parent_id).isdigit() else 0
    except:
        ch_num = 0
        
    context = {
        'posicion': 'desarrollo',
        'ritmo': 'MEDIO',
        'es_intencional': False,
        'justificacion_ritmo': '',
        'personajes': [],
        'problemas': [],
        'notas_margen': margin_notes or []
    }
    
    # Posición Arco
    arco = bible.get('arco_narrativo', {})
    for punto, data in arco.get('puntos_clave', {}).items():
        if isinstance(data, dict) and data.get('capitulo') == ch_num:
            context['posicion'] = punto
            break
            
    # Ritmo
    mapa = bible.get('mapa_de_ritmo', {})
    for cap in mapa.get('capitulos', []):
        if cap.get('numero') == ch_num:
            context['ritmo'] = cap.get('clasificacion', 'MEDIO')
            context['es_intencional'] = cap.get('es_intencional', False)
            context['justificacion_ritmo'] = cap.get('justificacion', '')
            break
            
    # Personajes
    reparto = bible.get('reparto_completo', {})
    for tipo in ['protagonistas', 'antagonistas', 'secundarios']:
        for p in reparto.get(tipo, []):
            caps = p.get('capitulos_clave', [])
            if not caps or ch_num in caps:
                context['personajes'].append({
                    'nombre': p.get('nombre', ''),
                    'rol': p.get('rol_arquetipo', tipo),
                    'voz': p.get('patron_dialogo', '')
                })
    context['personajes'] = context['personajes'][:5]
    
    # Problemas
    causalidad = bible.get('analisis_causalidad', {}).get('problemas_detectados', {})
    for tipo in ['eventos_huerfanos', 'contradicciones']:
        for p in causalidad.get(tipo, []):
            if str(p.get('capitulo')) == str(ch_num):
                context['problemas'].append(f"{p.get('tipo_problema')}: {p.get('descripcion')[:100]}")
                
    return context

def format_dynamic_lists(context: Dict) -> Dict:
    p_lines = [f"• {p['nombre']} ({p['rol']}) - Voz: {p.get('voz', 'N/A')}" for p in context['personajes']]
    personajes_str = "\n".join(p_lines) if p_lines else "(Ninguno identificado)"
    
    n_lines = []
    for n in context['notas_margen']:
        sev = "🔴" if n.get('severidad') == 'alta' else "🟡"
        n_lines.append(f"{sev} [{n.get('nota_id')}] {n.get('tipo', '').upper()}: {n.get('nota')}\n   Sugerencia: {n.get('sugerencia')}")
    notas_str = "\n".join(n_lines) if n_lines else "(Sin notas pendientes)"
    
    prob_str = "\n".join([f"- {p}" for p in context['problemas']]) if context['problemas'] else "(Sin problemas estructurales)"
    
    adv_ritmo = f"⚠️ INTENCIONAL: {context['justificacion_ritmo']}" if context['es_intencional'] else ""
    
    return {
        'personajes_str': personajes_str,
        'notas_str': notas_str,
        'problemas_str': prob_str,
        'advertencia_ritmo': adv_ritmo
    }

def main(edit_requests: Dict) -> Dict:
    """Envía capítulos a Vertex AI Batch (Claude)."""
    try:
        # 1. Recuperar datos
        raw_requests = edit_requests.get('edit_requests', [])
        chapters = [r['chapter'] for r in raw_requests] if raw_requests and 'chapter' in raw_requests[0] else edit_requests.get('chapters', [])
        
        bible = edit_requests.get('bible', {})
        margin_notes_map = edit_requests.get('margin_notes', {})
        book_metadata = edit_requests.get('book_metadata', {})
        
        logging.info(f"📦 Preparando Edición Batch (Vertex AI) para {len(chapters)} capítulos")

        batch_requests = []
        ordered_ids = []
        fragment_metadata = {}
        
        # 2. CONSTRUIR SYSTEM PROMPT
        book_ctx = extract_book_context(bible, book_metadata)
        no_corregir_str = "\n".join([f"⚠️ {i}" for i in book_ctx['no_corregir']]) if book_ctx['no_corregir'] else "Sin restricciones"
        
        system_content = STATIC_SYSTEM_TEMPLATE.format(
            titulo=book_ctx['titulo'],
            genero=book_ctx['genero'],
            tono=book_ctx['tono'],
            tema=book_ctx['tema'],
            estilo=book_ctx['estilo'],
            no_corregir=no_corregir_str
        )

        # 3. CONSTRUIR REQUESTS
        for chapter in chapters:
            ch_id = str(chapter.get('id', '?'))
            parent_id = str(chapter.get('parent_chapter_id', ch_id))
            ordered_ids.append(ch_id)
            
            fragment_metadata[ch_id] = {
                'fragment_id': chapter.get('id'),
                'original_title': chapter.get('title', 'Sin título'),
                'content': chapter.get('content', ''), # Guardar contenido para fallback
                'parent_chapter_id': parent_id
            }
            
            ch_notes = margin_notes_map.get(parent_id, [])
            if not ch_notes: ch_notes = margin_notes_map.get(ch_id, [])
            
            ch_ctx = extract_chapter_context(chapter, bible, ch_notes)
            fmt_ctx = format_dynamic_lists(ch_ctx)
            
            user_content = DYNAMIC_USER_TEMPLATE.format(
                chapter_id=ch_id, # INYECTADO PARA MATCHING
                titulo_capitulo=chapter.get('title', 'Capítulo'),
                posicion=ch_ctx['posicion'],
                ritmo=ch_ctx['ritmo'],
                advertencia_ritmo=fmt_ctx['advertencia_ritmo'],
                personajes=fmt_ctx['personajes_str'],
                notas_margen=fmt_ctx['notas_str'],
                problemas=fmt_ctx['problemas_str'],
                contenido=chapter.get('content', '')
            )
            
            # Formato Vertex AI Claude
            request = format_claude_vertex_request(
                messages=[{"role": "user", "content": user_content}],
                system=system_content,
                max_tokens=8192,
                temperature=0.3
            )
            batch_requests.append(request)
            
        logging.info(f"📝 Subiendo {len(batch_requests)} requests a GCS")
        
        # Generar nombre único para el archivo batch
        batch_filename = f"claude_edit_batch_{uuid.uuid4()}.jsonl"
        source_uri = upload_jsonl_to_gcs(batch_requests, batch_filename)
        
        # Destino
        timestamp = uuid.uuid4().hex[:8]
        destination_prefix = f"claude_edit_results_{timestamp}"
        
        # Submit Job
        model_name = CLAUDE_SONNET_MODEL # Usar configuración centralizada
        job_id = submit_vertex_batch_job(
            model_name=model_name,
            source_uri=source_uri,
            destination_uri_prefix=destination_prefix,
            job_display_name=f"lya-edit-{timestamp}"
        )
        
        logging.info(f"✅ Batch Vertex AI iniciado: {job_id}")
        
        return {
            "batch_id": job_id,
            "status": "processing",
            "chapters_count": len(chapters),
            "id_map": ordered_ids,
            "fragment_metadata_map": fragment_metadata,
            "provider": "vertex_ai"
        }

    except Exception as e:
        logging.error(f"❌ Error: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return {"error": str(e), "status": "error"}

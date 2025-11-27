# =============================================================================
# ConsolidateFragmentAnalyses/__init__.py - SYLPHRENA 4.0 (FINAL FIX)
# =============================================================================
# CORRECCIÓN APLICADA:
#   - Se agregó la lógica de desempaquetado en 'main' para manejar el input
#     del orquestador (que llega como dict, no como list directa).
#   - Se mantiene la verbosidad y comentarios originales.
# =============================================================================

import logging
import json
from collections import defaultdict

logging.basicConfig(level=logging.INFO)


def merge_character_lists(char_lists: list) -> list:
    """
    Fusiona listas de personajes de múltiples fragmentos.
    - Elimina duplicados por nombre
    - Suma conteos de diálogos
    - Combina acciones clave
    - Preserva el estado emocional más reciente
    """
    characters = {}
    
    for char_list in char_lists:
        for char in char_list:
            name = char.get('nombre', 'Desconocido').lower().strip()
            
            if name not in characters:
                characters[name] = {
                    'nombre': char.get('nombre', 'Desconocido'),
                    'roles_detectados': [],
                    'estados_emocionales': [],
                    'acciones_clave': [],
                    'dialogos_count_total': 0,
                    'fragmentos_aparicion': []
                }
            
            # Agregar rol si es nuevo
            rol = char.get('rol_en_fragmento', 'mencionado')
            if rol not in characters[name]['roles_detectados']:
                characters[name]['roles_detectados'].append(rol)
            
            # Agregar estado emocional
            estado = char.get('estado_emocional', '')
            if estado:
                characters[name]['estados_emocionales'].append(estado)
            
            # Agregar acciones
            acciones = char.get('acciones_clave', [])
            characters[name]['acciones_clave'].extend(acciones)
            
            # Sumar diálogos
            characters[name]['dialogos_count_total'] += char.get('dialogos_count', 0)
    
    # Convertir a lista y determinar rol principal
    result = []
    for name, data in characters.items():
        # Determinar rol principal (prioridad: protagonista > antagonista > secundario > mencionado)
        rol_priority = {'protagonista': 4, 'antagonista': 3, 'secundario': 2, 'mencionado': 1}
        roles = data['roles_detectados']
        main_role = max(roles, key=lambda r: rol_priority.get(r, 0)) if roles else 'mencionado'
        
        # Determinar estado emocional predominante
        estados = data['estados_emocionales']
        if estados:
            estado_predominante = max(set(estados), key=estados.count)
        else:
            estado_predominante = 'no especificado'
        
        result.append({
            'nombre': data['nombre'],
            'rol_en_capitulo': main_role,
            'estado_emocional_predominante': estado_predominante,
            'arco_emocional': data['estados_emocionales'],
            'acciones_clave': list(set(data['acciones_clave']))[:10],
            'dialogos_count_total': data['dialogos_count_total'],
            'apariciones_en_fragmentos': len(set(estados)) if estados else 1
        })
    
    # Ordenar por importancia
    result.sort(key=lambda x: (
        rol_priority.get(x['rol_en_capitulo'], 0),
        x['dialogos_count_total']
    ), reverse=True)
    
    return result


def merge_event_lists(event_lists: list, fragment_indices: list) -> list:
    """Fusiona listas de eventos preservando orden."""
    all_events = []
    
    for events, frag_idx in zip(event_lists, fragment_indices):
        for event in events:
            event_copy = event.copy()
            event_copy['fragment_source'] = frag_idx
            all_events.append(event_copy)
    
    # Índice global
    for i, event in enumerate(all_events):
        event['global_sequence'] = i + 1
    
    return all_events


def aggregate_metrics(metrics_list: list) -> dict:
    """Agrega métricas de todos los fragmentos."""
    if not metrics_list:
        return {}
    
    # Estructura
    total_palabras = sum(m.get('estructura', {}).get('total_palabras', 0) for m in metrics_list)
    total_oraciones = sum(m.get('estructura', {}).get('total_oraciones', 0) for m in metrics_list)
    total_parrafos = sum(m.get('estructura', {}).get('total_parrafos', 0) for m in metrics_list)
    
    # Composición
    lineas_dialogo = sum(m.get('composicion', {}).get('lineas_dialogo', 0) for m in metrics_list)
    escenas_accion = sum(m.get('composicion', {}).get('escenas_accion', 0) for m in metrics_list)
    escenas_reflexion = sum(m.get('composicion', {}).get('escenas_reflexion', 0) for m in metrics_list)
    
    porcentaje_dialogo = (lineas_dialogo / max(total_oraciones, 1)) * 100
    
    # Ritmo
    ritmo_scores = {'RAPIDO': 3, 'MEDIO': 2, 'LENTO': 1}
    ritmo_values = []
    justificaciones = []
    
    for m in metrics_list:
        ritmo = m.get('ritmo', {})
        clasificacion = ritmo.get('clasificacion', 'MEDIO')
        ritmo_values.append(ritmo_scores.get(clasificacion, 2))
        if ritmo.get('justificacion'):
            justificaciones.append(ritmo.get('justificacion'))
    
    avg_ritmo = sum(ritmo_values) / len(ritmo_values) if ritmo_values else 2
    
    if avg_ritmo >= 2.5: clasificacion_final = 'RAPIDO'
    elif avg_ritmo >= 1.5: clasificacion_final = 'MEDIO'
    else: clasificacion_final = 'LENTO'
    
    # Tiempo
    referencias_temporales = []
    for m in metrics_list:
        refs = m.get('tiempo', {}).get('referencias_explicitas', [])
        referencias_temporales.extend(refs)
    
    return {
        'estructura': {
            'total_palabras': total_palabras,
            'total_oraciones': total_oraciones,
            'total_parrafos': total_parrafos
        },
        'composicion': {
            'lineas_dialogo': lineas_dialogo,
            'porcentaje_dialogo': round(porcentaje_dialogo, 1),
            'escenas_accion': escenas_accion,
            'escenas_reflexion': escenas_reflexion
        },
        'ritmo': {
            'clasificacion': clasificacion_final,
            'score_promedio': round(avg_ritmo, 2),
            'justificaciones_fragmentos': justificaciones
        },
        'tiempo': {
            'referencias_explicitas': referencias_temporales
        }
    }


def consolidate_editorial_signals(signals_list: list) -> dict:
    """Consolida señales de edición."""
    all_tell_no_show = []
    all_repeticiones = {}
    all_inconsistencias = []
    all_fortalezas = []
    all_problemas = []
    
    for signals in signals_list:
        tns = signals.get('instancias_tell_no_show', [])
        all_tell_no_show.extend(tns)
        
        reps = signals.get('repeticiones', [])
        for rep in reps:
            palabra = rep.get('palabra', '').lower()
            freq = rep.get('frecuencia', 1)
            all_repeticiones[palabra] = all_repeticiones.get(palabra, 0) + freq
        
        all_inconsistencias.extend(signals.get('inconsistencias_internas', []))
        all_fortalezas.extend(signals.get('fortalezas', []))
        all_problemas.extend(signals.get('problemas_potenciales', []))
    
    repeticiones_list = [
        {'palabra': p, 'frecuencia': f} 
        for p, f in sorted(all_repeticiones.items(), key=lambda x: x[1], reverse=True)
    ]
    
    return {
        'instancias_tell_no_show': all_tell_no_show,
        'repeticiones': repeticiones_list[:20],
        'inconsistencias_internas': list(set(all_inconsistencias)),
        'fortalezas': list(set(all_fortalezas)),
        'problemas_potenciales': list(set(all_problemas))
    }


def main(payload: dict) -> list:
    """
    Consolida análisis. 
    CORREGIDO: Maneja payload como diccionario (Orchestrator input) o lista.
    """
    try:
        # --- BLOQUE DE CORRECCIÓN CRÍTICA ---
        if isinstance(payload, dict) and 'fragment_analyses' in payload:
            fragment_analyses = payload.get('fragment_analyses', [])
        elif isinstance(payload, list):
            fragment_analyses = payload
        else:
            logging.warning(f"⚠️ Formato de input inesperado: {type(payload)}")
            fragment_analyses = []
        # ------------------------------------

        if not fragment_analyses:
            logging.warning("⚠️ No hay análisis de fragmentos para consolidar")
            return []
        
        logging.info(f"🔄 Consolidando {len(fragment_analyses)} análisis de fragmentos...")
        
        # Agrupar por capítulo padre
        chapters = defaultdict(list)
        
        for analysis in fragment_analyses:
            # Protección extra contra strings mal parseados
            if isinstance(analysis, str):
                try:
                    analysis = json.loads(analysis)
                except:
                    continue
            
            if not isinstance(analysis, dict):
                continue

            parent_id = analysis.get('parent_chapter_id', 0)
            chapters[parent_id].append(analysis)
        
        logging.info(f"📚 Detectados {len(chapters)} capítulos únicos")
        
        # Consolidar cada capítulo
        consolidated = []
        
        for parent_id, fragments in sorted(chapters.items()):
            fragments.sort(key=lambda x: x.get('fragment_index', 0))
            first_frag = fragments[0]
            
            chapter_title = first_frag.get('titulo_capitulo', f'Capítulo {parent_id}')
            section_type = first_frag.get('section_type', 'CHAPTER')
            total_fragments = first_frag.get('total_fragments', len(fragments))
            
            logging.info(f"   📖 Consolidando: {chapter_title} ({len(fragments)} fragmentos)")
            
            # Extraer listas y fusionar
            char_lists = [f.get('reparto_local', []) for f in fragments]
            event_lists = [f.get('eventos', []) for f in fragments]
            fragment_indices = [f.get('fragment_index', 0) for f in fragments]
            metrics_list = [f.get('metricas', {}) for f in fragments]
            signals_list = [f.get('senales_edicion', {}) for f in fragments]
            
            merged_characters = merge_character_lists(char_lists)
            merged_events = merge_event_lists(event_lists, fragment_indices)
            aggregated_metrics = aggregate_metrics(metrics_list)
            consolidated_signals = consolidate_editorial_signals(signals_list)
            
            # Elementos narrativos
            first_narratives = first_frag.get('elementos_narrativos', {})
            last_narratives = fragments[-1].get('elementos_narrativos', {})
            
            chapter_consolidated = {
                'chapter_id': parent_id,
                'titulo': chapter_title,
                'section_type': section_type,
                'total_fragments': total_fragments,
                'fragment_ids': [f.get('fragment_id', 0) for f in fragments],
                'reparto_completo': merged_characters,
                'secuencia_eventos': merged_events,
                'metricas_agregadas': aggregated_metrics,
                'senales_edicion': consolidated_signals,
                'elementos_narrativos': {
                    'lugar_inicial': first_narratives.get('lugar', ''),
                    'lugar_final': last_narratives.get('lugar', ''),
                    'tiempo_inicio': first_narratives.get('tiempo_narrativo', ''),
                    'atmosfera_predominante': first_narratives.get('atmosfera', ''),
                    'conflicto_presente': any(f.get('elementos_narrativos', {}).get('conflicto_presente', False) for f in fragments),
                    'gancho_final': last_narratives.get('gancho_final', False)
                },
                'fragmentacion': {'total_fragmentos': total_fragments},
                '_metadata': {'status': 'consolidated'}
            }
            
            consolidated.append(chapter_consolidated)
        
        logging.info(f"✅ Consolidación completada: {len(consolidated)} capítulos")
        return consolidated

    except Exception as e:
        logging.error(f"💥 Error en ConsolidateFragmentAnalyses: {str(e)}")
        raise e
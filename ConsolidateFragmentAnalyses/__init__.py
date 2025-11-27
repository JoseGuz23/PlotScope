# =============================================================================
# ConsolidateFragmentAnalyses/__init__.py - SYLPHRENA 4.0
# =============================================================================
# NUEVA FUNCIÓN:
#   - Agrupa análisis de fragmentos por capítulo padre
#   - Consolida listas de personajes (elimina duplicados, suma métricas)
#   - Concatena eventos en orden secuencial
#   - Agrega métricas cuantitativas
#   - Prepara datos para análisis de Capa 2 y 3
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
        
        # Determinar estado emocional predominante (el más frecuente)
        estados = data['estados_emocionales']
        if estados:
            estado_predominante = max(set(estados), key=estados.count)
        else:
            estado_predominante = 'no especificado'
        
        result.append({
            'nombre': data['nombre'],
            'rol_en_capitulo': main_role,
            'estado_emocional_predominante': estado_predominante,
            'arco_emocional': data['estados_emocionales'],  # Secuencia de estados
            'acciones_clave': list(set(data['acciones_clave']))[:10],  # Top 10 únicas
            'dialogos_count_total': data['dialogos_count_total'],
            'apariciones_en_fragmentos': len(set(estados)) if estados else 1
        })
    
    # Ordenar por importancia (diálogos + prioridad de rol)
    result.sort(key=lambda x: (
        rol_priority.get(x['rol_en_capitulo'], 0),
        x['dialogos_count_total']
    ), reverse=True)
    
    return result


def merge_event_lists(event_lists: list, fragment_indices: list) -> list:
    """
    Fusiona listas de eventos de múltiples fragmentos en orden cronológico.
    Preserva la secuencia narrativa.
    """
    all_events = []
    
    for events, frag_idx in zip(event_lists, fragment_indices):
        for event in events:
            event_copy = event.copy()
            event_copy['fragment_source'] = frag_idx
            all_events.append(event_copy)
    
    # Ya están en orden por fragmento, solo agregar índice global
    for i, event in enumerate(all_events):
        event['global_sequence'] = i + 1
    
    return all_events


def aggregate_metrics(metrics_list: list) -> dict:
    """
    Agrega métricas de todos los fragmentos de un capítulo.
    """
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
    
    # Ritmo (promedio ponderado)
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
    
    if avg_ritmo >= 2.5:
        clasificacion_final = 'RAPIDO'
    elif avg_ritmo >= 1.5:
        clasificacion_final = 'MEDIO'
    else:
        clasificacion_final = 'LENTO'
    
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
    """
    Consolida señales de edición de todos los fragmentos.
    """
    all_tell_no_show = []
    all_repeticiones = {}
    all_inconsistencias = []
    all_fortalezas = []
    all_problemas = []
    
    for signals in signals_list:
        # Tell no show
        tns = signals.get('instancias_tell_no_show', [])
        all_tell_no_show.extend(tns)
        
        # Repeticiones (agregar frecuencias)
        reps = signals.get('repeticiones', [])
        for rep in reps:
            palabra = rep.get('palabra', '').lower()
            freq = rep.get('frecuencia', 1)
            all_repeticiones[palabra] = all_repeticiones.get(palabra, 0) + freq
        
        # Inconsistencias
        incons = signals.get('inconsistencias_internas', [])
        all_inconsistencias.extend(incons)
        
        # Fortalezas
        fort = signals.get('fortalezas', [])
        all_fortalezas.extend(fort)
        
        # Problemas
        prob = signals.get('problemas_potenciales', [])
        all_problemas.extend(prob)
    
    # Convertir repeticiones a lista ordenada por frecuencia
    repeticiones_list = [
        {'palabra': p, 'frecuencia': f} 
        for p, f in sorted(all_repeticiones.items(), key=lambda x: x[1], reverse=True)
    ]
    
    return {
        'instancias_tell_no_show': all_tell_no_show,
        'repeticiones': repeticiones_list[:20],  # Top 20
        'inconsistencias_internas': list(set(all_inconsistencias)),
        'fortalezas': list(set(all_fortalezas)),
        'problemas_potenciales': list(set(all_problemas))
    }


def main(fragment_analyses: list) -> list:
    """
    Consolida análisis de fragmentos en análisis de capítulos completos.
    
    Input: Lista de análisis de fragmentos (Capa 1)
    Output: Lista de análisis de capítulos consolidados
    
    Cada capítulo consolidado incluye:
    - Información jerárquica del capítulo
    - Lista unificada de personajes
    - Secuencia completa de eventos
    - Métricas agregadas
    - Señales de edición consolidadas
    """
    
    if not fragment_analyses:
        logging.warning("⚠️ No hay análisis de fragmentos para consolidar")
        return []
    
    logging.info(f"🔄 Consolidando {len(fragment_analyses)} análisis de fragmentos...")
    
    # Agrupar por capítulo padre
    chapters = defaultdict(list)
    
    for analysis in fragment_analyses:
        parent_id = analysis.get('parent_chapter_id', 0)
        chapters[parent_id].append(analysis)
    
    logging.info(f"📚 Detectados {len(chapters)} capítulos únicos")
    
    # Consolidar cada capítulo
    consolidated = []
    
    for parent_id, fragments in sorted(chapters.items()):
        # Ordenar fragmentos por índice
        fragments.sort(key=lambda x: x.get('fragment_index', 0))
        
        # Información del capítulo
        first_frag = fragments[0]
        chapter_title = first_frag.get('titulo_capitulo', f'Capítulo {parent_id}')
        section_type = first_frag.get('section_type', 'CHAPTER')
        total_fragments = first_frag.get('total_fragments', len(fragments))
        
        logging.info(f"   📖 Consolidando: {chapter_title} ({len(fragments)} fragmentos)")
        
        # Extraer listas para fusión
        char_lists = [f.get('reparto_local', []) for f in fragments]
        event_lists = [f.get('eventos', []) for f in fragments]
        fragment_indices = [f.get('fragment_index', 0) for f in fragments]
        metrics_list = [f.get('metricas', {}) for f in fragments]
        signals_list = [f.get('senales_edicion', {}) for f in fragments]
        
        # Fusionar
        merged_characters = merge_character_lists(char_lists)
        merged_events = merge_event_lists(event_lists, fragment_indices)
        aggregated_metrics = aggregate_metrics(metrics_list)
        consolidated_signals = consolidate_editorial_signals(signals_list)
        
        # Extraer elementos narrativos del primer y último fragmento
        first_narratives = first_frag.get('elementos_narrativos', {})
        last_frag = fragments[-1]
        last_narratives = last_frag.get('elementos_narrativos', {})
        
        # Construir capítulo consolidado
        chapter_consolidated = {
            'chapter_id': parent_id,
            'titulo': chapter_title,
            'section_type': section_type,
            'total_fragments': total_fragments,
            'fragment_ids': [f.get('fragment_id', 0) for f in fragments],
            
            # Datos fusionados
            'reparto_completo': merged_characters,
            'secuencia_eventos': merged_events,
            'metricas_agregadas': aggregated_metrics,
            'senales_edicion': consolidated_signals,
            
            # Elementos narrativos
            'elementos_narrativos': {
                'lugar_inicial': first_narratives.get('lugar', ''),
                'lugar_final': last_narratives.get('lugar', ''),
                'tiempo_inicio': first_narratives.get('tiempo_narrativo', ''),
                'atmosfera_predominante': first_narratives.get('atmosfera', ''),
                'conflicto_presente': any(
                    f.get('elementos_narrativos', {}).get('conflicto_presente', False) 
                    for f in fragments
                ),
                'gancho_final': last_narratives.get('gancho_final', False)
            },
            
            # Contexto de fragmentación
            'fragmentacion': {
                'fue_fragmentado': total_fragments > 1,
                'total_fragmentos': total_fragments,
                'escenas_interrumpidas': sum(
                    1 for f in fragments 
                    if f.get('contexto_fragmentacion', {}).get('escena_incompleta', False)
                )
            },
            
            # Metadata
            '_metadata': {
                'status': 'consolidated',
                'fragments_processed': len(fragments),
                'analysis_layer': '1_consolidated'
            }
        }
        
        consolidated.append(chapter_consolidated)
    
    # Ordenar por chapter_id
    consolidated.sort(key=lambda x: x['chapter_id'])
    
    logging.info(f"✅ Consolidación completada: {len(consolidated)} capítulos")
    
    return consolidated

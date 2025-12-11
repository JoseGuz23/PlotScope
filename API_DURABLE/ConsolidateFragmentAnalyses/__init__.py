# =============================================================================
# ConsolidateFragmentAnalyses/__init__.py - LYA 4.0 (ULTRA ROBUST)
# =============================================================================
# CORRECCIONES APLICADAS:
#   - Safety-checks para conversiones int() en 'frecuencia' y 'dialogos_count'
#   - Manejo robusto de estructuras malformadas
#   - Compatibilidad total con function.json (param: fragment_analyses)
# =============================================================================

import logging
import json
from collections import defaultdict

logging.basicConfig(level=logging.INFO)


def merge_character_lists(char_lists: list) -> list:
    """
    Fusiona listas de personajes normalizando nombres y roles.
    INCLUYE SAFEGUARD PARA ENTEROS.
    """
    characters = {}
    
    rol_priority = {
        'protagonista': 4, 
        'antagonista': 3, 
        'secundario': 2, 
        'mencionado': 1
    }

    for char_list in char_lists:
        if not isinstance(char_list, list): continue
        
        for char in char_list:
            if not isinstance(char, dict): continue
            
            name = str(char.get('nombre', 'Desconocido')).lower().strip()
            
            if name not in characters:
                characters[name] = {
                    'nombre': char.get('nombre', 'Desconocido'),
                    'roles_detectados': set(),
                    'estados_emocionales': [],
                    'acciones_clave': [],
                    'dialogos_count_total': 0
                }
            
            raw_role = char.get('rol_en_fragmento', 'mencionado')
            rol = raw_role.lower().strip() if raw_role else 'mencionado'
            characters[name]['roles_detectados'].add(rol)
            
            estado = char.get('estado_emocional', '')
            if estado:
                characters[name]['estados_emocionales'].append(estado)
            
            acciones = char.get('acciones_clave', [])
            if isinstance(acciones, list):
                characters[name]['acciones_clave'].extend([str(a) for a in acciones])
            
            # --- SAFEGUARD INT CONVERSION ---
            try:
                d_count = int(char.get('dialogos_count', 0))
            except (ValueError, TypeError):
                d_count = 0 # Fallback seguro
            
            characters[name]['dialogos_count_total'] += d_count
            # --------------------------------
    
    result = []
    for name, data in characters.items():
        roles = list(data['roles_detectados'])
        main_role = max(roles, key=lambda r: rol_priority.get(r, 0)) if roles else 'mencionado'
        estados = data['estados_emocionales']
        estado_predominante = max(set(estados), key=estados.count) if estados else 'no especificado'
        
        result.append({
            'nombre': data['nombre'],
            'rol_en_capitulo': main_role,
            'estado_emocional_predominante': estado_predominante,
            'arco_emocional': estados,
            'acciones_clave': list(set(data['acciones_clave']))[:10],
            'dialogos_count_total': data['dialogos_count_total'],
            'apariciones_en_fragmentos': len(set(estados)) if estados else 1
        })
    
    result.sort(key=lambda x: (
        rol_priority.get(x['rol_en_capitulo'], 0),
        x['dialogos_count_total']
    ), reverse=True)
    
    return result


def merge_event_lists(event_lists: list, fragment_indices: list) -> list:
    """Fusiona listas de eventos preservando orden."""
    all_events = []
    
    for events, frag_idx in zip(event_lists, fragment_indices):
        if not isinstance(events, list): continue
        for event in events:
            if isinstance(event, dict):
                event_copy = event.copy()
                event_copy['fragment_source'] = frag_idx
                all_events.append(event_copy)
    
    for i, event in enumerate(all_events):
        event['global_sequence'] = i + 1
    
    return all_events


def aggregate_metrics(metrics_list: list) -> dict:
    """Agrega métricas de todos los fragmentos."""
    if not metrics_list:
        return {}
    
    total_palabras = 0
    total_oraciones = 0
    total_parrafos = 0
    lineas_dialogo = 0
    escenas_accion = 0
    escenas_reflexion = 0
    ritmo_values = []
    justificaciones = []
    referencias_temporales = []
    
    ritmo_scores = {'RAPIDO': 3, 'MEDIO': 2, 'LENTO': 1}
    
    for m in metrics_list:
        if not isinstance(m, dict): continue
        
        est = m.get('estructura', {})
        comp = m.get('composicion', {})
        rit = m.get('ritmo', {})
        tiem = m.get('tiempo', {})
        
        # Helper para sumar con seguridad
        def safe_add(val):
            try: return int(val)
            except: return 0

        total_palabras += safe_add(est.get('total_palabras', 0))
        total_oraciones += safe_add(est.get('total_oraciones', 0))
        total_parrafos += safe_add(est.get('total_parrafos', 0))
        
        lineas_dialogo += safe_add(comp.get('lineas_dialogo', 0))
        escenas_accion += safe_add(comp.get('escenas_accion', 0))
        escenas_reflexion += safe_add(comp.get('escenas_reflexion', 0))
        
        clasificacion = rit.get('clasificacion', 'MEDIO')
        ritmo_values.append(ritmo_scores.get(clasificacion, 2))
        if rit.get('justificacion'):
            justificaciones.append(rit.get('justificacion'))
            
        referencias_temporales.extend(tiem.get('referencias_explicitas', []))
    
    porcentaje_dialogo = (lineas_dialogo / max(total_oraciones, 1)) * 100
    avg_ritmo = sum(ritmo_values) / len(ritmo_values) if ritmo_values else 2
    
    if avg_ritmo >= 2.5: clasificacion_final = 'RAPIDO'
    elif avg_ritmo >= 1.5: clasificacion_final = 'MEDIO'
    else: clasificacion_final = 'LENTO'
    
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
    Consolida señales de edición de forma robusta.
    INCLUYE SAFEGUARD PARA ENTEROS EN FRECUENCIA.
    """
    all_tell_no_show = []
    all_repeticiones = {}
    all_inconsistencias = []
    all_fortalezas = []
    all_problemas = []
    
    for signals in signals_list:
        if not isinstance(signals, dict): continue

        # Tell vs Show
        tns = signals.get('instancias_tell_no_show', [])
        if isinstance(tns, list):
            for item in tns:
                if isinstance(item, dict):
                    all_tell_no_show.append(item)
                elif isinstance(item, str):
                    all_tell_no_show.append({'texto': item, 'sugerencia': 'Revisar show vs tell'})

        # Repeticiones - PUNTO DE FALLA CORREGIDO
        reps = signals.get('repeticiones', [])
        if isinstance(reps, list):
            for rep in reps:
                palabra = ""
                freq = 1
                
                if isinstance(rep, dict):
                    palabra = str(rep.get('palabra', '')).lower()
                    
                    # --- SAFEGUARD CRÍTICO ---
                    # Si 'frecuencia' viene como texto (ej: "Moderada"), int() falla.
                    try:
                        freq = int(rep.get('frecuencia', 1))
                    except (ValueError, TypeError):
                        # Si falla, asumimos 1. El log indicaba que llegó un string descriptivo.
                        # Esto evita el crash y cuenta al menos una ocurrencia.
                        freq = 1
                    # -------------------------
                    
                elif isinstance(rep, str):
                    palabra = rep.lower()
                    freq = 1
                
                if palabra:
                    all_repeticiones[palabra] = all_repeticiones.get(palabra, 0) + freq
        
        # Listas simples (strings)
        for field, target_list in [
            ('inconsistencias_internas', all_inconsistencias), 
            ('fortalezas', all_fortalezas), 
            ('problemas_potenciales', all_problemas)
        ]:
            items = signals.get(field, [])
            if isinstance(items, list):
                target_list.extend([str(i) for i in items if i])
            elif isinstance(items, str):
                target_list.append(items)
    
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


def main(fragment_analyses) -> list:
    """
    Consolida análisis.
    NOTA: El argumento coincide con function.json ('fragment_analyses').
    """
    # Alias para lógica interna
    payload = fragment_analyses 
    
    try:
        analyses_list = []
        chapter_map = {}

        # 1. Desempaquetado inteligente
        if isinstance(payload, dict) and 'fragment_analyses' in payload:
            analyses_list = payload.get('fragment_analyses', [])
            chapter_map = payload.get('chapter_map', {}) 
        elif isinstance(payload, list):
            analyses_list = payload
        else:
            logging.warning(f"⚠️ Formato de input inesperado: {type(payload)}")
            if isinstance(payload, dict): 
                pass 
            else:
                return []

        if not analyses_list:
            logging.warning("⚠️ No hay análisis de fragmentos para consolidar")
            return []
        
        logging.info(f"🔄 Consolidando {len(analyses_list)} análisis...")
        
        # Agrupar por capítulo padre
        chapters = defaultdict(list)
        
        for analysis in analyses_list:
            if isinstance(analysis, str):
                try:
                    analysis = json.loads(analysis)
                except:
                    continue
            
            if not isinstance(analysis, dict):
                continue

            # Agrupar usando string para consistencia
            parent_id = str(analysis.get('parent_chapter_id', '0'))
            chapters[parent_id].append(analysis)
        
        logging.info(f"📚 Detectados {len(chapters)} capítulos únicos")
        
        consolidated = []
        
        # Ordenar claves de forma segura
        sorted_chapters = sorted(chapters.items(), key=lambda x: str(x[0]))
        
        for parent_id, fragments in sorted_chapters:
            fragments.sort(key=lambda x: x.get('fragment_index', 0))
            if not fragments: continue
            
            first_frag = fragments[0]
            
            # Obtener título oficial
            map_data = chapter_map.get(parent_id, {})
            official_title = map_data.get('original_title') # Usar original_title del mapa
            
            chapter_title = official_title if official_title else first_frag.get('titulo_capitulo', f'Capítulo {parent_id}')
            section_type = first_frag.get('section_type', 'CHAPTER')
            total_fragments = len(fragments)
            
            logging.info(f"   📖 Consolidando: {chapter_title} ({len(fragments)} frags)")
            
            # Extraer listas de forma segura
            char_lists = [f.get('reparto_local', []) for f in fragments]
            event_lists = [f.get('eventos', []) for f in fragments]
            fragment_indices = [f.get('fragment_index', 0) for f in fragments]
            metrics_list = [f.get('metricas', {}) for f in fragments]
            signals_list = [f.get('senales_edicion', {}) for f in fragments]
            
            merged_characters = merge_character_lists(char_lists)
            merged_events = merge_event_lists(event_lists, fragment_indices)
            aggregated_metrics = aggregate_metrics(metrics_list)
            
            # Llamada a función robusta
            consolidated_signals = consolidate_editorial_signals(signals_list)
            
            # Elementos narrativos
            last_frag = fragments[-1]
            first_narratives = first_frag.get('elementos_narrativos', {})
            last_narratives = last_frag.get('elementos_narrativos', {})
            
            # Construir objeto consolidado
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
        import traceback
        logging.error(traceback.format_exc())
        raise e
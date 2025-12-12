#!/usr/bin/env python3
"""
Script para actualizar metadata.json con datos de insights LYA 6.0
Fusiona analisis_emocional.json, deteccion_sensorial.json y estadisticas_reflexion.json
en metadata.json para que el frontend los pueda leer.
"""

import json
import sys
from pathlib import Path

def main():
    outputs_dir = Path("outputs")

    # Leer archivos existentes
    try:
        with open(outputs_dir / "metadata.json", 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        print("[OK] Metadata cargado")
    except FileNotFoundError:
        print("[ERROR] No se encontro metadata.json en outputs/")
        sys.exit(1)

    # Cargar análisis emocional
    try:
        with open(outputs_dir / "analisis_emocional.json", 'r', encoding='utf-8') as f:
            emotional_data = json.load(f)

        metadata['emotional_arc_analysis'] = {
            'chapter_arcs': emotional_data.get('emotional_arcs', []),
            'global_arc': emotional_data.get('global_arc', {}),
            'diagnostics': emotional_data.get('diagnostics', [])
        }
        metadata['has_emotional_analysis'] = True
        print("[OK] Analisis emocional agregado")
    except FileNotFoundError:
        print("[WARN] No se encontro analisis_emocional.json")

    # Cargar detección sensorial
    try:
        with open(outputs_dir / "deteccion_sensorial.json", 'r', encoding='utf-8') as f:
            sensory_data = json.load(f)

        metadata['sensory_detection_analysis'] = {
            'chapter_details': sensory_data.get('sensory_analyses', []),
            'global_metrics': sensory_data.get('global_metrics', {}),
            'critical_issues': sensory_data.get('critical_issues', [])
        }
        metadata['has_sensory_analysis'] = True
        metadata['global_metrics'] = sensory_data.get('global_metrics', {})
        print("[OK] Deteccion sensorial agregada")
    except FileNotFoundError:
        print("[WARN] No se encontro deteccion_sensorial.json")

    # Cargar estadísticas de reflexión
    try:
        with open(outputs_dir / "estadisticas_reflexion.json", 'r', encoding='utf-8') as f:
            reflection_stats = json.load(f)

        metadata['reflection_stats'] = reflection_stats
        print("[OK] Estadisticas de reflexion agregadas")
    except FileNotFoundError:
        print("[WARN] No se encontro estadisticas_reflexion.json")

    # Guardar metadata actualizado
    with open(outputs_dir / "metadata.json", 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print("\n[SUCCESS] metadata.json actualizado exitosamente!")
    print("\nResumen:")
    print(f"  - Emotional Analysis: {'SI' if 'emotional_arc_analysis' in metadata else 'NO'}")
    print(f"  - Sensory Detection: {'SI' if 'sensory_detection_analysis' in metadata else 'NO'}")
    print(f"  - Reflection Stats: {'SI' if 'reflection_stats' in metadata else 'NO'}")

    # Mostrar métricas globales
    if 'global_metrics' in metadata:
        print(f"\nMetricas globales:")
        gm = metadata['global_metrics']
        print(f"  - Avg Showing Ratio: {gm.get('avg_showing_ratio', 0)*100:.1f}%")
        print(f"  - Avg Sensory Density: {gm.get('avg_sensory_density', 0)*100:.2f}%")
        print(f"  - Total Chapters: {gm.get('total_chapters_analyzed', 0)}")

if __name__ == "__main__":
    main()

# =============================================================================
# SensoryDetectionAnalysis/__init__.py - LYA 6.0 (CORREGIDO Y CALIBRADO)
# =============================================================================
# Detecta contenido sensorial vs abstracto para diagnosticar "Show vs Tell"
# Proporciona análisis cuantitativo de inmersión sensorial por párrafo
# =============================================================================

import logging
import json
import re
from typing import List, Dict, Any
import numpy as np

logging.basicConfig(level=logging.INFO)

# =============================================================================
# LÉXICOS SENSORIALES
# =============================================================================

SENSORY_LEXICONS = {
    "visual": [
        "rojo", "azul", "verde", "negro", "blanco", "gris", "dorado", "plateado",
        "oscuro", "brillante", "opaco", "transparente", "turbio",
        "puntiagudo", "redondo", "anguloso", "irregular", "suave", "rugoso",
        "ver", "mirar", "observar", "contemplar", "vislumbrar", "divisar",
        "parpadear", "brillar", "destellar", "relucir", "resplandecer",
        "oscurecer", "iluminar", "sombrear",
        "luz", "sombra", "reflejo", "destello", "brillo", "color", "forma"
    ],
    "auditivo": [
        "sonido", "ruido", "eco", "silencio", "estruendo", "murmullo",
        "oír", "escuchar", "susurrar", "gritar", "murmurar", "gemir",
        "crujir", "chasquear", "retumbar", "zumbar", "sisear",
        "aullar", "rugir", "chirriar", "tronar",
        "fuerte", "débil", "agudo", "grave", "estridente", "melodioso",
        "ronco", "chirriante", "metálico"
    ],
    "olfativo": [
        "olor", "aroma", "hedor", "peste", "fragancia", "perfume",
        "oler", "olfatear", "apestar", "perfumar",
        "putrefacto", "rancio", "fresco", "aromático", "fétido",
        "dulce", "acre", "penetrante", "nauseabundo"
    ],
    "táctil": [
        "suave", "áspero", "rugoso", "liso", "viscoso", "pegajoso",
        "húmedo", "seco", "resbaladizo", "afilado", "punzante",
        "caliente", "frío", "tibio", "helado", "ardiente", "gélido",
        "templado", "hirviente",
        "tocar", "palpar", "acariciar", "rozar", "frotar", "arañar",
        "apretar", "sujetar", "agarrar", "empuñar",
        "dolor", "presión", "peso", "textura", "roce", "caricia"
    ],
    "gustativo": [
        "sabor", "gusto", "amargor", "dulzura",
        "dulce", "amargo", "salado", "ácido", "agrio", "picante",
        "insípido", "sabroso",
        "saborear", "probar", "degustar", "lamer", "masticar", "tragar"
    ],
    "kinestésico": [
        "caminar", "correr", "saltar", "agacharse", "inclinarse",
        "tambalearse", "tropezar", "arrastrarse", "gatear",
        "latir", "palpitar", "temblar", "estremecerse", "tiritar",
        "retorcerse", "tensar", "relajar",
        "mano", "pie", "brazo", "pierna", "dedo", "puño", "rodilla"
    ]
}

ABSTRACT_MARKERS = [
    "miedo", "temor", "terror", "pánico",
    "alegría", "felicidad", "tristeza", "melancolía",
    "ira", "rabia", "furia", "enfado",
    "sorpresa", "asombro", "admiración",
    "disgusto", "desprecio", "vergüenza",
    "pensar", "creer", "saber", "recordar", "olvidar",
    "imaginar", "soñar", "suponer", "considerar",
    "destino", "esperanza", "desesperación", "valentía", "cobardía",
    "honor", "gloria", "humillación",
    "sentir que", "experimentar", "percibir que"
]


class SensoryDetector:
    """
    Detector de contenido sensorial vs abstracto en texto narrativo.
    """

    def __init__(self):
        self.sensory_lexicons = SENSORY_LEXICONS
        self.abstract_markers = ABSTRACT_MARKERS


    def analyze_paragraph(self, paragraph: str) -> Dict[str, Any]:
        """
        Analiza un párrafo individual.
        """
        words = paragraph.lower().split()
        total_words = len(words) if words else 1
        lower_paragraph = paragraph.lower()

        # Contar palabras sensoriales por categoría
        sensory_counts = {category: 0 for category in self.sensory_lexicons.keys()}
        total_sensory = 0

        for category, lexicon in self.sensory_lexicons.items():
            for sensory_word in lexicon:
                # --- FIX 1: Regex mejorado para plurales (s, es) ---
                # Busca la palabra exacta o con plural simple (ej: color -> colores, rojo -> rojos)
                pattern = r'\b' + re.escape(sensory_word) + r'(?:s|es)?\b'
                matches = len(re.findall(pattern, lower_paragraph))
                
                if matches > 0:
                    sensory_counts[category] += matches
                    total_sensory += matches

        # Contar marcadores abstractos
        abstract_count = 0
        for marker in self.abstract_markers:
            pattern = r'\b' + re.escape(marker) + r'(?:s|es)?\b'
            matches = len(re.findall(pattern, lower_paragraph))
            abstract_count += matches

        # Calcular densidades
        sensory_density = total_sensory / total_words
        abstract_density = abstract_count / total_words

        # --- FIX 2: CALIBRACIÓN DE UMBRALES ---
        # 0.15 (15%) era irreal. Se ajusta a 0.02 (2%) que es un estándar narrativo bueno.
        # Abstracto se ajusta a 0.05 (5%).
        is_showing = sensory_density > 0.02 and abstract_density < 0.05

        # Generar diagnóstico
        diagnosis = self._generate_diagnosis(
            sensory_density,
            abstract_density,
            sensory_counts,
            is_showing
        )

        return {
            "text": paragraph[:100] + "..." if len(paragraph) > 100 else paragraph,
            "sensory_density": round(sensory_density, 4),
            "sensory_breakdown": {k: v for k, v in sensory_counts.items() if v > 0},
            "abstract_density": round(abstract_density, 4),
            "is_showing": is_showing,
            "diagnosis": diagnosis,
            "total_words": total_words,
            "sensory_word_count": total_sensory,
            "abstract_word_count": abstract_count
        }


    def _generate_diagnosis(
        self,
        sensory_density: float,
        abstract_density: float,
        sensory_counts: Dict,
        is_showing: bool
    ) -> str:
        """
        Genera diagnóstico textual basado en métricas.
        """
        if is_showing:
            dominant_sense = max(sensory_counts.items(), key=lambda x: x[1])[0] if any(sensory_counts.values()) else "ninguno"
            return f"SHOWING: Inmersión sensorial fuerte (densidad: {sensory_density:.1%}). Sentido dominante: {dominant_sense}."

        elif abstract_density > 0.05:
            return f"TELLING: Alto contenido abstracto (densidad: {abstract_density:.1%}). Convertir emociones nombradas en sensaciones físicas."

        elif sensory_density < 0.02:
            return f"VAGO: Bajo contenido sensorial (densidad: {sensory_density:.1%}). Añadir detalles sensoriales para inmersión."

        else:
            return f"MIXTO: Balance entre sensorial ({sensory_density:.1%}) y abstracto ({abstract_density:.1%}). Puede mejorarse."


    def analyze_chapter(self, chapter_content: str, chapter_id: int) -> Dict[str, Any]:
        """
        Analiza un capítulo completo párrafo por párrafo.
        """
        logging.info(f"🔬 Analizando detección sensorial del capítulo {chapter_id}")

        paragraphs = [p.strip() for p in re.split(r'\n\n+', chapter_content) if p.strip()]

        if not paragraphs:
            return {
                "chapter_id": chapter_id,
                "error": "No se encontraron párrafos",
                "paragraphs_analyzed": 0
            }

        paragraph_analyses = []
        showing_count = 0
        total_sensory_accum = 0

        for i, paragraph in enumerate(paragraphs):
            # Saltar párrafos muy cortos (< 10 palabras) para evitar ruido
            if len(paragraph.split()) < 10:
                continue

            analysis = self.analyze_paragraph(paragraph)
            analysis['paragraph_index'] = i
            paragraph_analyses.append(analysis)

            if analysis['is_showing']:
                showing_count += 1
            
            total_sensory_accum += analysis['sensory_density']

        total_analyzed = len(paragraph_analyses)
        
        # Calcular promedios globales del capítulo
        avg_sensory = total_sensory_accum / total_analyzed if total_analyzed > 0 else 0
        showing_ratio = showing_count / total_analyzed if total_analyzed > 0 else 0

        # --- LOG DE DEBUG PARA VER EL VALOR REAL EN EL PORTAL ---
        logging.info(f"📊 Cap {chapter_id} STATS: Densidad={avg_sensory:.4f}, Ratio={showing_ratio:.2%}")

        problem_paragraphs = [
            {
                "paragraph_index": p['paragraph_index'],
                "text_preview": p['text'],
                "diagnosis": p['diagnosis'],
                "sensory_density": p['sensory_density'],
                "abstract_density": p['abstract_density']
            }
            for p in paragraph_analyses
            if not p['is_showing'] and p['abstract_density'] > 0.05
        ]

        recommendations = self._generate_recommendations(
            avg_sensory,
            showing_ratio,
            len(problem_paragraphs),
            total_analyzed
        )

        return {
            "chapter_id": chapter_id,
            "paragraphs_analyzed": total_analyzed,
            "avg_sensory_density": round(avg_sensory, 4),
            "showing_ratio": round(showing_ratio, 4),
            "problem_paragraphs": problem_paragraphs[:10],
            "recommendations": recommendations,
            "detailed_analyses": paragraph_analyses
        }


    def _generate_recommendations(
        self,
        avg_sensory: float,
        showing_ratio: float,
        problem_count: int,
        total_paragraphs: int
    ) -> List[str]:
        recs = []
        if avg_sensory < 0.02:
            recs.append("CRÍTICO: Densidad sensorial muy baja. Añadir descripciones visuales, auditivas y táctiles.")
        if showing_ratio < 0.3:
            recs.append(f"ALTO TELLING: Solo {showing_ratio*100:.0f}% de párrafos usan 'showing'.")
        if problem_count > total_paragraphs * 0.5:
            recs.append(f"MÚLTIPLES PÁRRAFOS PROBLEMÁTICOS: {problem_count} necesitan revisión.")
        if len(recs) == 0:
            recs.append("CALIDAD ACEPTABLE: Buen balance entre showing y telling.")
        return recs


def main(consolidated_chapters: List[Dict]) -> Dict:
    """
    Analiza detección sensorial para todos los capítulos.
    """
    try:
        logging.info("🔬 Iniciando Análisis de Detección Sensorial V2 (Calibrado)...")
        detector = SensoryDetector()

        chapter_analyses = []
        all_showing_ratios = []
        all_sensory_densities = []

        for chapter in consolidated_chapters:
            chapter_id = chapter.get('chapter_id', 0)
            content = chapter.get('content', '')

            if not content or len(content) < 100: # Ignorar capítulos vacíos o muy cortos
                logging.warning(f"⚠️ Capítulo {chapter_id} demasiado corto, omitiendo")
                continue

            analysis = detector.analyze_chapter(content, chapter_id)
            chapter_analyses.append(analysis)

            all_showing_ratios.append(analysis.get('showing_ratio', 0))
            all_sensory_densities.append(analysis.get('avg_sensory_density', 0))

        global_showing_ratio = np.mean(all_showing_ratios) if all_showing_ratios else 0
        global_sensory_density = np.mean(all_sensory_densities) if all_sensory_densities else 0

        # Identificar issues críticos
        critical_issues = []
        for analysis in chapter_analyses:
            if analysis.get('showing_ratio', 1) < 0.3:
                critical_issues.append({
                    "type": "CAPITULO_CON_EXCESO_TELLING",
                    "severity": "alta",
                    "chapter_id": analysis['chapter_id'],
                    "showing_ratio": analysis['showing_ratio'],
                    "description": f"Capítulo {analysis['chapter_id']}: Solo {analysis['showing_ratio']*100:.0f}% de showing"
                })

        logging.info(f"✅ Análisis sensorial completado: {len(chapter_analyses)} capítulos. Ratio Global: {global_showing_ratio:.2%}")

        return {
            "sensory_analyses": chapter_analyses,
            "global_metrics": {
                "avg_showing_ratio": float(global_showing_ratio),
                "avg_sensory_density": float(global_sensory_density),
                "total_chapters_analyzed": len(chapter_analyses)
            },
            "critical_issues": critical_issues,
            "status": "completed"
        }

    except Exception as e:
        logging.error(f"❌ Error en análisis sensorial: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return {
            "error": str(e),
            "status": "error"
        }
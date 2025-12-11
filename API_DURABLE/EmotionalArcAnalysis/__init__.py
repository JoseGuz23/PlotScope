# =============================================================================
# EmotionalArcAnalysis/__init__.py - LYA 6.0
# =============================================================================
# Analiza el arco emocional de la narrativa usando sentiment analysis
# Detecta problemas de ritmo emocional y verifica coherencia con estructura
# =============================================================================

import logging
import json
import os
import re
from typing import List, Dict, Any, Tuple
import numpy as np

logging.basicConfig(level=logging.INFO)

# =============================================================================
# CONFIGURACIÓN DE SENTIMENT ANALYSIS
# =============================================================================

# Intentar importar transformers (si no está, usar fallback simple)
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("⚠️ transformers no disponible, usando análisis léxico simple")


class EmotionalArcAnalyzer:
    """
    Analiza el arco emocional de un manuscrito mediante sentiment analysis.
    """

    def __init__(self, model_name: str = "finiteautomata/beto-sentiment-analysis"):
        """
        Inicializa el analizador emocional.

        Args:
            model_name: Modelo de HuggingFace para sentiment analysis en español
        """
        self.model_name = model_name
        self.sentiment_analyzer = None

        if TRANSFORMERS_AVAILABLE:
            try:
                logging.info(f"🤖 Cargando modelo de sentiment: {model_name}")
                self.sentiment_analyzer = pipeline(
                    "sentiment-analysis",
                    model=model_name,
                    truncation=True,
                    max_length=512
                )
                logging.info("✅ Modelo cargado exitosamente")
            except Exception as e:
                logging.error(f"❌ Error cargando modelo: {e}")
                self.sentiment_analyzer = None


    def analyze_text_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analiza el sentimiento de un texto.

        Args:
            text: Texto a analizar

        Returns:
            {"label": "POS/NEG/NEU", "score": 0.0-1.0, "valence": -1.0 a 1.0}
        """
        if self.sentiment_analyzer:
            try:
                result = self.sentiment_analyzer(text[:512])[0]  # Truncar a 512 chars
                label = result['label']
                score = result['score']

                # Convertir a valencia (-1 a 1)
                if label == 'POS':
                    valence = score
                elif label == 'NEG':
                    valence = -score
                else:  # NEU
                    valence = 0.0

                return {
                    "label": label,
                    "score": score,
                    "valence": valence
                }

            except Exception as e:
                logging.error(f"Error en análisis de sentimiento: {e}")
                return self._fallback_sentiment(text)
        else:
            return self._fallback_sentiment(text)


    def _fallback_sentiment(self, text: str) -> Dict[str, float]:
        """
        Análisis léxico simple si no hay modelo ML disponible.
        """
        positive_words = [
            'feliz', 'alegre', 'amor', 'risa', 'victoria', 'triunfo',
            'esperanza', 'luz', 'sonrisa', 'abrazo', 'paz', 'belleza'
        ]
        negative_words = [
            'muerte', 'miedo', 'dolor', 'oscuro', 'sangre', 'horror',
            'grito', 'llorar', 'tristeza', 'pérdida', 'fracaso', 'odio'
        ]

        text_lower = text.lower()

        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)

        total = pos_count + neg_count
        if total == 0:
            return {"label": "NEU", "score": 0.5, "valence": 0.0}

        valence = (pos_count - neg_count) / (total + 5)  # Normalizado

        if valence > 0.2:
            return {"label": "POS", "score": 0.6 + valence * 0.4, "valence": valence}
        elif valence < -0.2:
            return {"label": "NEG", "score": 0.6 - valence * 0.4, "valence": valence}
        else:
            return {"label": "NEU", "score": 0.5, "valence": valence}


    def create_sliding_windows(self, text: str, window_size: int = 500) -> List[str]:
        """
        Divide el texto en ventanas deslizantes para análisis granular.

        Args:
            text: Texto completo
            window_size: Tamaño de ventana en palabras

        Returns:
            Lista de ventanas de texto
        """
        words = text.split()
        windows = []

        step_size = window_size // 2  # Overlap de 50%

        for i in range(0, len(words), step_size):
            window = ' '.join(words[i:i + window_size])
            if len(window.split()) >= 50:  # Mínimo 50 palabras
                windows.append(window)

        return windows


    def analyze_chapter_arc(
        self,
        chapter_content: str,
        chapter_id: int,
        window_size: int = 500
    ) -> Dict[str, Any]:
        """
        Analiza el arco emocional de un capítulo.

        Args:
            chapter_content: Contenido del capítulo
            chapter_id: ID del capítulo
            window_size: Tamaño de ventana para análisis

        Returns:
            {
                "chapter_id": int,
                "emotional_trajectory": [...],  # Lista de valencias
                "avg_valence": float,
                "emotional_range": float,
                "emotional_pattern": "string",
                "critical_moments": [...]
            }
        """
        logging.info(f"📊 Analizando arco emocional del capítulo {chapter_id}")

        windows = self.create_sliding_windows(chapter_content, window_size)

        if not windows:
            return {
                "chapter_id": chapter_id,
                "error": "Capítulo demasiado corto para análisis",
                "emotional_trajectory": [],
                "avg_valence": 0.0
            }

        # Analizar cada ventana
        trajectory = []
        for i, window in enumerate(windows):
            sentiment = self.analyze_text_sentiment(window)
            trajectory.append({
                "window_index": i,
                "valence": sentiment['valence'],
                "label": sentiment['label']
            })

        # Calcular métricas
        valences = [point['valence'] for point in trajectory]
        avg_valence = np.mean(valences)
        emotional_range = max(valences) - min(valences)

        # Detectar patrón emocional
        pattern = self._detect_emotional_pattern(valences)

        # Identificar momentos críticos (picos y valles)
        critical_moments = self._find_critical_moments(trajectory, chapter_content, window_size)

        return {
            "chapter_id": chapter_id,
            "emotional_trajectory": trajectory,
            "avg_valence": float(avg_valence),
            "emotional_range": float(emotional_range),
            "emotional_pattern": pattern,
            "critical_moments": critical_moments,
            "total_windows": len(windows)
        }


    def _detect_emotional_pattern(self, valences: List[float]) -> str:
        """
        Detecta el patrón emocional de una serie de valencias.

        Patrones posibles:
        - ASCENDENTE: Mejora constante (esperanzador)
        - DESCENDENTE: Empeora constante (trágico)
        - MONTAÑA_RUSA: Alta variación (thriller/acción)
        - PLANO_POSITIVO: Estable positivo
        - PLANO_NEGATIVO: Estable negativo (grimdark)
        - VALLE: Comienza bien, empeora, mejora (estructura clásica)
        """
        if len(valences) < 3:
            return "INDETERMINADO"

        # Calcular tendencia
        first_third = np.mean(valences[:len(valences)//3])
        middle_third = np.mean(valences[len(valences)//3:2*len(valences)//3])
        last_third = np.mean(valences[2*len(valences)//3:])

        # Calcular varianza
        variance = np.var(valences)

        # Clasificar
        if variance > 0.3:
            return "MONTAÑA_RUSA"
        elif last_third - first_third > 0.3:
            return "ASCENDENTE"
        elif first_third - last_third > 0.3:
            return "DESCENDENTE"
        elif first_third > 0.2 and middle_third < -0.2 and last_third > 0.2:
            return "VALLE"
        elif np.mean(valences) > 0.2:
            return "PLANO_POSITIVO"
        elif np.mean(valences) < -0.2:
            return "PLANO_NEGATIVO"
        else:
            return "NEUTRAL"


    def _find_critical_moments(
        self,
        trajectory: List[Dict],
        chapter_content: str,
        window_size: int
    ) -> List[Dict]:
        """
        Identifica picos emocionales (altos y bajos) en el capítulo.
        """
        valences = [point['valence'] for point in trajectory]

        if len(valences) < 3:
            return []

        critical = []

        # Encontrar máximos y mínimos locales
        for i in range(1, len(valences) - 1):
            if valences[i] > valences[i-1] and valences[i] > valences[i+1]:
                # Pico positivo
                critical.append({
                    "type": "PICO_POSITIVO",
                    "window_index": i,
                    "valence": valences[i],
                    "description": "Momento de mayor intensidad emocional positiva"
                })
            elif valences[i] < valences[i-1] and valences[i] < valences[i+1]:
                # Valle negativo
                critical.append({
                    "type": "VALLE_NEGATIVO",
                    "window_index": i,
                    "valence": valences[i],
                    "description": "Momento de mayor intensidad emocional negativa"
                })

        # Limitar a los 3 más extremos
        critical.sort(key=lambda x: abs(x['valence']), reverse=True)

        return critical[:3]


def main(consolidated_chapters: List[Dict]) -> Dict:
    """
    Analiza el arco emocional completo de la obra.

    Args:
        consolidated_chapters: Lista de capítulos consolidados

    Returns:
        {
            "emotional_arcs": [...],  # Por capítulo
            "global_arc": {...},      # Del manuscrito completo
            "diagnostics": [...]      # Problemas detectados
        }
    """
    try:
        logging.info("🎭 Iniciando Análisis de Arco Emocional...")

        analyzer = EmotionalArcAnalyzer()

        chapter_arcs = []
        all_valences = []

        for chapter in consolidated_chapters:
            chapter_id = chapter.get('chapter_id', 0)
            content = chapter.get('content', '')

            if not content or len(content) < 500:
                logging.warning(f"⚠️ Capítulo {chapter_id} demasiado corto, omitiendo")
                continue

            arc = analyzer.analyze_chapter_arc(content, chapter_id)
            chapter_arcs.append(arc)

            # Agregar valencias para análisis global
            all_valences.extend([point['valence'] for point in arc['emotional_trajectory']])

        # Análisis global
        global_avg_valence = np.mean(all_valences) if all_valences else 0.0
        global_pattern = analyzer._detect_emotional_pattern(all_valences) if all_valences else "INDETERMINADO"

        # Diagnosticar problemas
        diagnostics = []

        # Detectar capítulos planos
        for arc in chapter_arcs:
            if arc.get('emotional_range', 0) < 0.1:
                diagnostics.append({
                    "type": "CAPITULO_PLANO",
                    "severity": "media",
                    "chapter_id": arc['chapter_id'],
                    "description": f"Capítulo {arc['chapter_id']} tiene muy poca variación emocional (rango: {arc['emotional_range']:.2f})",
                    "suggestion": "Considera añadir contraste emocional: momentos de tensión vs alivio"
                })

        # Detectar falta de coherencia con estructura
        # (Esto se puede expandir cuando tengamos info de estructura de 3 actos)

        logging.info(f"✅ Análisis emocional completado: {len(chapter_arcs)} capítulos analizados")

        return {
            "emotional_arcs": chapter_arcs,
            "global_arc": {
                "avg_valence": float(global_avg_valence),
                "emotional_pattern": global_pattern,
                "total_data_points": len(all_valences)
            },
            "diagnostics": diagnostics,
            "status": "completed"
        }

    except Exception as e:
        logging.error(f"❌ Error en análisis emocional: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return {
            "error": str(e),
            "status": "error"
        }

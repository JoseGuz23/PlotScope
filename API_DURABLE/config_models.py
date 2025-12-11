# =============================================================================
# config_models.py - Configuración Centralizada de Modelos IA (LYA 6.0)
# =============================================================================
# Última actualización: Diciembre 2025
# Modelos probados y confirmados funcionales
# =============================================================================

# =============================================================================
# GEMINI MODELS (Google)
# =============================================================================

# Modelo principal para análisis masivo (Batch API) - Balance costo/calidad
GEMINI_FLASH_MODEL = "models/gemini-2.5-flash"

# Modelo premium para síntesis complejas (Biblia, Carta Editorial)
GEMINI_PRO_MODEL = "models/gemini-2.5-pro"

# Modelo experimental para features avanzadas (opcional)
GEMINI_EXPERIMENTAL_MODEL = "models/gemini-3-pro-preview"

# =============================================================================
# CLAUDE MODELS (Anthropic)
# =============================================================================

# Modelo principal para edición profesional - Mejor calidad literaria
CLAUDE_SONNET_MODEL = "claude-sonnet-4-5-20250929"

# Modelo premium para reflexión crítica y análisis profundo
CLAUDE_OPUS_MODEL = "claude-opus-4-5-20251101"

# Modelo rápido para validaciones y tareas ligeras
CLAUDE_HAIKU_MODEL = "claude-haiku-4-5-20251001"

# =============================================================================
# CONFIGURACIÓN DE CONTEXT CACHING (LYA 6.0)
# =============================================================================

# Habilitar context caching para reducir costos en llamadas repetitivas
ENABLE_CONTEXT_CACHING = True

# Duración del cache en segundos (default: 300 = 5 minutos)
CACHE_TTL_SECONDS = 300

# =============================================================================
# CONFIGURACIÓN DE REFLECTION LOOPS (LYA 6.0)
# =============================================================================

# Habilitar reflection loops selectivos
ENABLE_REFLECTION_LOOPS = True

# Umbral de calidad para activar reflection (0-10)
# Capítulos con score < umbral usarán reflection, otros single-pass
REFLECTION_QUALITY_THRESHOLD = 7.0

# Máximo de iteraciones en reflection loop
REFLECTION_MAX_ITERATIONS = 3

# Modelo para crítica en reflection loop
REFLECTION_CRITIC_MODEL = GEMINI_PRO_MODEL

# Modelo para redacción en reflection loop
REFLECTION_WRITER_MODEL = CLAUDE_SONNET_MODEL

# =============================================================================
# CONFIGURACIÓN DE ANÁLISIS EMOCIONAL (LYA 6.0)
# =============================================================================

# Habilitar análisis de arco emocional
ENABLE_EMOTIONAL_ARC_ANALYSIS = True

# Modelo local de sentiment analysis (HuggingFace)
SENTIMENT_MODEL = "finiteautomata/beto-sentiment-analysis"

# Tamaño de ventana para análisis deslizante (palabras)
SENTIMENT_WINDOW_SIZE = 500

# =============================================================================
# CONFIGURACIÓN DE DETECCIÓN SENSORIAL (LYA 6.0)
# =============================================================================

# Habilitar detección sensorial para Show vs Tell
ENABLE_SENSORY_DETECTION = True

# Umbral de contenido sensorial (0-1)
# Si < umbral en párrafo crítico, se marca como "telling"
SENSORY_CONTENT_THRESHOLD = 0.3

# =============================================================================
# MAPPING DE MODELOS POR FUNCIÓN (para retrocompatibilidad)
# =============================================================================

MODEL_CONFIG = {
    # Análisis factual en batch (Fase 2)
    "batch_analysis": GEMINI_FLASH_MODEL,

    # Análisis estructural (Fase 4)
    "structural_analysis": GEMINI_PRO_MODEL,

    # Análisis cualitativo (Fase 5)
    "qualitative_analysis": GEMINI_PRO_MODEL,

    # Creación de Biblia Narrativa (Fase 6)
    "bible_synthesis": GEMINI_PRO_MODEL,

    # Generación de carta editorial (Fase 7)
    "editorial_letter": GEMINI_PRO_MODEL,

    # Notas de margen (Fase 8)
    "margin_notes": CLAUDE_SONNET_MODEL,

    # Mapas de arcos (Fase 9)
    "arc_mapping": GEMINI_FLASH_MODEL,

    # Edición profesional (Fase 10)
    "professional_editing": CLAUDE_SONNET_MODEL,

    # Reflection - Crítica
    "reflection_critic": GEMINI_PRO_MODEL,

    # Reflection - Redacción
    "reflection_writer": CLAUDE_SONNET_MODEL,
}

# =============================================================================
# FUNCIONES HELPER
# =============================================================================

def get_model(function_name: str) -> str:
    """
    Obtiene el modelo apropiado para una función específica.

    Args:
        function_name: Nombre de la función (clave en MODEL_CONFIG)

    Returns:
        String con el nombre del modelo
    """
    return MODEL_CONFIG.get(function_name, GEMINI_FLASH_MODEL)


def get_reflection_config() -> dict:
    """
    Retorna configuración completa para reflection loops.
    """
    return {
        "enabled": ENABLE_REFLECTION_LOOPS,
        "quality_threshold": REFLECTION_QUALITY_THRESHOLD,
        "max_iterations": REFLECTION_MAX_ITERATIONS,
        "critic_model": REFLECTION_CRITIC_MODEL,
        "writer_model": REFLECTION_WRITER_MODEL
    }


def get_emotional_analysis_config() -> dict:
    """
    Retorna configuración para análisis emocional.
    """
    return {
        "enabled": ENABLE_EMOTIONAL_ARC_ANALYSIS,
        "sentiment_model": SENTIMENT_MODEL,
        "window_size": SENTIMENT_WINDOW_SIZE
    }


def get_sensory_detection_config() -> dict:
    """
    Retorna configuración para detección sensorial.
    """
    return {
        "enabled": ENABLE_SENSORY_DETECTION,
        "threshold": SENSORY_CONTENT_THRESHOLD
    }

# =============================================================================
# SubmitMarginNotes/__init__.py - LYA 6.0 (Optimized)
# =============================================================================
# ACTUALIZACIÓN: Implementación de Context Caching para reducción de costos.
# Se separa el contexto estático (instrucciones/carta) del dinámico (capítulos).
# =============================================================================

import logging
import json
import os
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO)

# -----------------------------------------------------------------------------
# PROMPTS (Divididos para Caching)
# -----------------------------------------------------------------------------

# PARTE 1: INSTRUCCIONES ESTÁTICAS (Se cacheará esto)
STATIC_SYSTEM_INSTRUCTIONS = """Eres un EDITOR PROFESIONAL. Tu tarea es generar NOTAS DE MARGEN para el libro "{libro}".

═══════════════════════════════════════════════════════════════════════════════
CONTEXTO EDITORIAL (de la carta editorial):
═══════════════════════════════════════════════════════════════════════════════
{contexto_editorial}

═══════════════════════════════════════════════════════════════════════════════
TIPOS DE NOTAS A GENERAR:
═══════════════════════════════════════════════════════════════════════════════
1. **PACING**: Donde el ritmo no funciona (muy lento/rápido).
2. **PERSONAJE**: Inconsistencias o falta de profundidad.
3. **DIALOGO**: Problemas de naturalidad o "infodumping".
4. **CLARIDAD**: Confusión espacial o temporal.
5. **EMOCION**: Falta de impacto emocional requerido.
6. **VOZ**: Inconsistencias de tono.
7. **TENSION**: Falta de conflicto o resolución fácil.
8. **SHOW_TELL**: Explicar en lugar de mostrar.

═══════════════════════════════════════════════════════════════════════════════
INSTRUCCIONES DE SALIDA:
═══════════════════════════════════════════════════════════════════════════════
1. Lee el fragmento proporcionado por el usuario.
2. Identifica 5-15 puntos de mejora crítica.
3. Prioriza notas con IMPACTO REAL en la narrativa.
4. RESPONDE ÚNICAMENTE CON JSON VÁLIDO con el siguiente formato:

{{
    "notas_margen": [
        {{
            "nota_id": "chID-nota-001",
            "parrafo_aprox": N,
            "texto_referencia": "Primeras 10-15 palabras...",
            "tipo": "categoria",
            "severidad": "alta|media|baja",
            "nota": "Problema...",
            "sugerencia": "Solución...",
            "impacto_si_no_se_corrige": "Consecuencia..."
        }}
    ],
    "resumen_capitulo": {{
        "fortaleza_principal": "...",
        "problema_principal": "...",
        "prioridad_revision": "alta|media|baja"
    }}
}}
"""

# PARTE 2: CONTENIDO DINÁMICO (Cambia por capítulo)
CHAPTER_USER_PROMPT = """Analiza el siguiente capítulo basándote en las instrucciones cacheadas.

INFORMACIÓN DEL CAPÍTULO:
- Título: {titulo}
- ID Referencia: {chapter_id}
- Función narrativa prevista: {funcion}
- Personajes presentes: {personajes}

TEXTO DEL CAPÍTULO:
═══════════════════════════════════════════════════════════════════════════════
{contenido}
═══════════════════════════════════════════════════════════════════════════════
"""

def main(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Envía capítulos a Claude Batch utilizando Context Caching.
    """
    try:
        from anthropic import Anthropic
        
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            return {"error": "ANTHROPIC_API_KEY no configurada", "status": "config_error"}
        
        chapters = input_data.get('chapters', [])
        carta = input_data.get('carta_editorial', {})
        bible = input_data.get('bible', {})
        book_metadata = input_data.get('book_metadata', {})
        
        libro_titulo = book_metadata.get('title', bible.get('identidad_obra', {}).get('titulo', 'Sin título'))
        
        logging.info(f"📝 Preparando notas de margen para {len(chapters)} capítulos con Caching.")
        
        client = Anthropic(api_key=api_key)
        
        batch_requests = []
        chapter_metadata = {}
        
        # 1. Preparar el contenido estático para el Caché
        # Este string debe ser IDÉNTICO en todos los requests para que el caché funcione
        contexto_editorial_str = extraer_contexto_editorial(carta, bible)
        
        system_content_cached = [
            {
                "type": "text",
                "text": STATIC_SYSTEM_INSTRUCTIONS.format(
                    libro=libro_titulo,
                    contexto_editorial=contexto_editorial_str
                ),
                # AQUI ESTA LA MAGIA DEL AHORRO:
                "cache_control": {"type": "ephemeral"} 
            }
        ]

        # 2. Iterar capítulos y construir requests
        for chapter in chapters:
            ch_id = str(chapter.get('id', chapter.get('chapter_id', '?')))
            parent_id = chapter.get('parent_chapter_id', ch_id)
            
            # Guardar metadata para seguimiento
            chapter_metadata[ch_id] = {
                'fragment_id': chapter.get('id', 0),
                'parent_chapter_id': parent_id,
                'original_title': chapter.get('title', chapter.get('original_title', 'Sin título'))
            }
            
            # Extraer datos dinámicos (específicos de este request)
            notas_cap = ""
            for nota in carta.get('notas_por_capitulo', []):
                if str(nota.get('capitulo')) == str(parent_id):
                    notas_cap = f"Función: {nota.get('funcion', '')}. Mejorar: {nota.get('que_mejorar', '')}"
                    break
            
            personajes = extraer_personajes_capitulo(bible, parent_id)
            
            # Construir el mensaje del usuario (dinámico)
            user_content = CHAPTER_USER_PROMPT.format(
                titulo=chapter.get('title', chapter.get('original_title', 'Sin título')),
                chapter_id=ch_id,
                funcion=notas_cap or "No especificada",
                personajes=", ".join(personajes) if personajes else "No especificados",
                contenido=chapter.get('content', '')
            )
            
            request = {
                "custom_id": f"margin-{ch_id}",
                "params": {
                    "model": "claude-sonnet-4-5-20250929", # Modelo preservado según instrucciones
                    "max_tokens": 4000,
                    "temperature": 0.5,
                    "system": system_content_cached, # Pasamos la estructura con cache_control
                    "messages": [
                        {"role": "user", "content": user_content}
                    ]
                }
            }
            batch_requests.append(request)
        
        logging.info(f"📦 Enviando {len(batch_requests)} requests a Claude Batch")
        
        # Crear el batch
        message_batch = client.messages.batches.create(requests=batch_requests)
        
        logging.info(f"✅ Batch creado: {message_batch.id}")
        
        return {
            "batch_id": message_batch.id,
            "chapters_count": len(chapters),
            "status": "submitted",
            "processing_status": message_batch.processing_status,
            "chapter_metadata": chapter_metadata,
            "optimization": "context_caching_enabled"
        }
        
    except ImportError as e:
        logging.error(f"❌ SDK no instalado: {e}")
        return {"error": str(e), "status": "import_error"}
    except Exception as e:
        logging.error(f"❌ Error crítico: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return {"error": str(e), "status": "error"}


def extraer_contexto_editorial(carta: Dict, bible: Dict) -> str:
    """Extrae contexto relevante de la carta editorial (Estático)."""
    contexto = []
    
    # Áreas de oportunidad principales
    areas = carta.get('areas_de_oportunidad', [])
    if areas:
        contexto.append("PROBLEMAS PRINCIPALES DEL LIBRO:")
        for area in areas[:5]:
            if area.get('prioridad') in ['ALTA', 'MEDIA']:
                cat = area.get('categoria', '').upper()
                prob = area.get('problema', '')[:120] # Limitado para consistencia
                contexto.append(f"- [{cat}] {prob}")
    
    # Voz del autor
    voz = bible.get('voz_del_autor', {})
    if voz.get('NO_CORREGIR'):
        contexto.append("\nELEMENTOS A PRESERVAR (VOZ):")
        for item in voz['NO_CORREGIR'][:3]:
            contexto.append(f"- {item}")
    
    contexto.append(f"\nESTILO GENERAL: {voz.get('estilo_detectado', 'Estándar')}")
    
    return "\n".join(contexto)


def extraer_personajes_capitulo(bible: Dict, chapter_id) -> List[str]:
    """Extrae personajes relevantes para un capítulo (Dinámico)."""
    personajes = []
    reparto = bible.get('reparto_completo', {})
    
    try:
        ch_num = int(chapter_id)
    except:
        ch_num = 0
    
    for tipo in ['protagonistas', 'antagonistas', 'secundarios']:
        for p in reparto.get(tipo, []):
            caps = p.get('capitulos_clave', [])
            # Si no tiene capítulos definidos, asumimos que aparece, o si coincide el ID
            if not caps or ch_num in caps:
                personajes.append(p.get('nombre', 'Personaje'))
    
    return personajes[:6]
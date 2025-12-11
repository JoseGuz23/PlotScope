# =============================================================================
# helpers_context_cache.py - Context Caching Helper (LYA 6.0)
# =============================================================================
# Implementa context caching de Gemini para reducir costos en llamadas repetitivas
# Ahorro estimado: ~75% en costos de input para manuscritos procesados múltiples veces
# =============================================================================

import logging
import hashlib
from typing import Optional, Dict, Any
from google.genai import types

logging.basicConfig(level=logging.INFO)

class ContextCacheManager:
    """
    Gestiona el cacheo de contexto para llamadas a Gemini API.

    Context Caching permite:
    - Cachear manuscritos completos o análisis previos
    - Reducir costo de input en ~75% para contenido cacheado
    - Reducir latencia en llamadas subsiguientes
    """

    def __init__(self):
        self.cache_registry = {}

    def create_cached_content(
        self,
        client,
        model: str,
        content: str,
        cache_name: Optional[str] = None,
        ttl_seconds: int = 300
    ) -> str:
        """
        Crea contenido cacheado en Gemini API.

        Args:
            client: Cliente de Google GenAI
            model: Nombre del modelo (ej: "models/gemini-2.5-flash")
            content: Texto a cachear (manuscrito, biblia, etc)
            cache_name: Nombre identificador del cache (opcional)
            ttl_seconds: Tiempo de vida del cache en segundos (default: 300)

        Returns:
            Cache resource name para usar en llamadas subsiguientes
        """
        try:
            # Generar nombre de cache si no se provee
            if not cache_name:
                content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
                cache_name = f"lya-cache-{content_hash}"

            logging.info(f"📦 Creando context cache: {cache_name}")
            logging.info(f"   Tamaño: {len(content)} chars")
            logging.info(f"   TTL: {ttl_seconds}s")

            # Crear cached content usando la API de Gemini
            cached_content = client.caches.create(
                model=model,
                config={
                    'display_name': cache_name,
                    'system_instruction': "Manuscrito completo cacheado para análisis",
                    'contents': [{
                        'role': 'user',
                        'parts': [{'text': content}]
                    }],
                    'ttl_seconds': ttl_seconds
                }
            )

            cache_resource_name = cached_content.name

            logging.info(f"✅ Cache creado: {cache_resource_name}")

            # Registrar en cache local
            self.cache_registry[cache_name] = {
                'resource_name': cache_resource_name,
                'created_at': cached_content.create_time,
                'expires_at': cached_content.expire_time,
                'size_chars': len(content)
            }

            return cache_resource_name

        except Exception as e:
            logging.error(f"❌ Error creando cache: {e}")
            # Si falla el cache, retornar None para usar modo sin cache
            return None


    def generate_with_cache(
        self,
        client,
        model: str,
        prompt: str,
        cached_content_name: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        Genera contenido usando context cache.

        Args:
            client: Cliente de Google GenAI
            model: Nombre del modelo
            prompt: Prompt de la consulta
            cached_content_name: Nombre del recurso cacheado
            **kwargs: Argumentos adicionales para generate_content

        Returns:
            Response de Gemini
        """
        try:
            if cached_content_name:
                logging.info(f"🔄 Usando context cache: {cached_content_name}")

                # Llamada usando cached content
                response = client.models.generate_content(
                    model=cached_content_name,  # Usar el cache como "modelo"
                    contents=prompt,
                    **kwargs
                )
            else:
                logging.info("⚠️ Cache no disponible, usando llamada estándar")

                # Llamada normal sin cache
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    **kwargs
                )

            return response

        except Exception as e:
            logging.error(f"❌ Error en generate_with_cache: {e}")
            raise


    def delete_cache(self, client, cache_resource_name: str) -> bool:
        """
        Elimina un cache existente.

        Args:
            client: Cliente de Google GenAI
            cache_resource_name: Nombre del recurso a eliminar

        Returns:
            True si se eliminó exitosamente
        """
        try:
            client.caches.delete(name=cache_resource_name)
            logging.info(f"🗑️ Cache eliminado: {cache_resource_name}")

            # Eliminar del registro local
            for key, value in list(self.cache_registry.items()):
                if value['resource_name'] == cache_resource_name:
                    del self.cache_registry[key]
                    break

            return True

        except Exception as e:
            logging.error(f"❌ Error eliminando cache: {e}")
            return False


    def get_cache_info(self, cache_name: str) -> Optional[Dict]:
        """
        Obtiene información de un cache registrado.

        Args:
            cache_name: Nombre del cache

        Returns:
            Diccionario con info del cache o None
        """
        return self.cache_registry.get(cache_name)


# =============================================================================
# Instancia global del cache manager
# =============================================================================

cache_manager = ContextCacheManager()


# =============================================================================
# Helper Functions para uso en Activities
# =============================================================================

def cache_manuscript_for_analysis(
    client,
    manuscript_text: str,
    job_id: str,
    model: str = "models/gemini-2.5-flash"
) -> Optional[str]:
    """
    Cachea un manuscrito completo para análisis subsiguientes.

    Args:
        client: Cliente de Google GenAI
        manuscript_text: Texto completo del manuscrito
        job_id: ID del job (para nombre de cache)
        model: Modelo a usar

    Returns:
        Cache resource name o None si falla
    """
    cache_name = f"manuscript-{job_id}"
    return cache_manager.create_cached_content(
        client=client,
        model=model,
        content=manuscript_text,
        cache_name=cache_name,
        ttl_seconds=3600  # 1 hora (suficiente para todo el procesamiento)
    )


def cache_bible_for_editing(
    client,
    bible_json: dict,
    consolidated_chapters: list,
    job_id: str,
    model: str = "models/gemini-2.5-pro"
) -> Optional[str]:
    """
    Cachea la Biblia Narrativa + capítulos para uso en edición.

    Args:
        client: Cliente de Google GenAI
        bible_json: Biblia Narrativa en formato JSON
        consolidated_chapters: Lista de capítulos consolidados
        job_id: ID del job
        model: Modelo a usar

    Returns:
        Cache resource name o None si falla
    """
    import json

    # Construir contexto combinado
    context = f"""BIBLIA NARRATIVA:
{json.dumps(bible_json, ensure_ascii=False, indent=2)}

═══════════════════════════════════════════════════════════════════════════════

CAPÍTULOS CONSOLIDADOS:
{json.dumps(consolidated_chapters, ensure_ascii=False, indent=2)}
"""

    cache_name = f"bible-context-{job_id}"
    return cache_manager.create_cached_content(
        client=client,
        model=model,
        content=context,
        cache_name=cache_name,
        ttl_seconds=1800  # 30 minutos
    )


def cleanup_job_caches(client, job_id: str):
    """
    Limpia todos los caches asociados a un job cuando termina el procesamiento.

    Args:
        client: Cliente de Google GenAI
        job_id: ID del job
    """
    logging.info(f"🧹 Limpiando caches para job: {job_id}")

    for cache_name, cache_info in list(cache_manager.cache_registry.items()):
        if job_id in cache_name:
            cache_manager.delete_cache(client, cache_info['resource_name'])

import azure.functions as func
from anthropic import Anthropic, APIError, RateLimitError, APITimeoutError
import json
import logging
import os
import time
# Implementación de robustez con Tenacity
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Configurar logs
logging.basicConfig(level=logging.INFO)
logging.getLogger('tenacity').setLevel(logging.WARNING)

# Estrategia de reintento para Claude
retry_strategy = retry(
    retry=retry_if_exception_type((RateLimitError, APITimeoutError)), # Reintentar solo en errores transitorios
    wait=wait_exponential(multiplier=1, min=2, max=20),
    stop=stop_after_attempt(4),
    reraise=True
)

def extract_relevant_context(chapter, bible, analysis):
    """
    RAG Ligero: Extrae contexto cruzando datos del Capítulo vs. La Biblia.
    SOLUCIONADO: Alineado con la estructura 'reparto_organizado' de createbible.
    """
    context = {
        'tono_general': 'No especificado',
        'personajes_aqui': [],
        'problemas': [],
        'resumen_breve': ''
    }

    try:
        # 1. Obtener nombres normalizados del análisis local (lowercase para comparación)
        local_chars = analysis.get('reparto_local', []) # createbible/analyze usaba 'reparto_local'
        chapter_names_norm = set()
        
        for p in local_chars:
            if isinstance(p, dict) and 'nombre' in p:
                chapter_names_norm.add(p['nombre'].lower())

        # 2. Buscar coincidencias en la Biblia (reparto_organizado)
        found_chars = []
        full_cast = bible.get('reparto_organizado', {})
        
        # Iteramos por categorías (protagonistas, antagonistas, etc.)
        for category in ['protagonistas', 'antagonistas', 'secundarios']:
            for char_data in full_cast.get(category, []):
                bible_name = char_data.get('nombre', '').lower()
                
                # Lógica de coincidencia difusa: 
                # Si "Juan" (local) está en "Juan Moreno" (biblia) O viceversa
                match = any(local in bible_name or bible_name in local for local in chapter_names_norm)
                
                if match:
                    # Añadimos etiqueta de su rol original en la biblia
                    char_data['_rol_biblia'] = category 
                    found_chars.append(char_data)

        # 3. Filtrar Inconsistencias por ID de capítulo
        chapter_id_str = str(chapter.get('id', ''))
        found_issues = []
        for issue in bible.get('inconsistencias_criticas', []): # Key correcta de createbible
            affected_chapters = [str(c) for c in issue.get('capitulos_en_conflicto', [])]
            if chapter_id_str in affected_chapters:
                found_issues.append(issue)

        # 4. Construir resultado final
        context['tono_general'] = bible.get('resumen_ejecutivo', 'Tono estándar') # Usamos resumen como proxy de tono si no hay campo explícito
        context['personajes_aqui'] = found_chars[:4] # Top 4 personajes más relevantes
        context['problemas'] = found_issues
        context['resumen_breve'] = bible.get('resumen_ejecutivo', '')[:600]

    except Exception as e:
        logging.error(f"⚠️ Error en extracción de contexto: {str(e)}")
        # Fallback seguro para no romper la edición
        context['resumen_breve'] = "Error extrayendo contexto."

    return context

@retry_strategy
def call_claude_with_retry(client, model, system_prompt, user_prompt):
    """Llamada encapsulada a Claude con Tenacity"""
    return client.messages.create(
        model=model,
        max_tokens=4000,
        temperature=0.5, # Balance entre creatividad y fidelidad
        system=system_prompt, # Claude 3.5 prefiere instrucciones de rol en 'system'
        messages=[{"role": "user", "content": user_prompt}]
    )

def main(edit_input_json) -> str:
    """
    Edita un capítulo usando Claude 3.5 Sonnet.
    """
    start_total = time.time()
    
    try:
        # 1. Parsear entrada
        if isinstance(edit_input_json, str):
            edit_input = json.loads(edit_input_json)
        else:
            edit_input = edit_input_json

        chapter = edit_input.get('chapter', {})
        bible = edit_input.get('bible', {})
        analysis = edit_input.get('analysis', {})
        
        chapter_id = chapter.get('id', 'Unknown')
        logging.info(f"🚀 INICIANDO edición de capítulo {chapter_id}")
        
        # Configurar Cliente
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY no configurada")
        client = Anthropic(api_key=api_key)
        
        # 2. Extracción de contexto (RAG Ligero)
        start_prep = time.time()
        relevant_context = extract_relevant_context(chapter, bible, analysis)
        prep_time = time.time() - start_prep
        
        # 3. Construcción del Prompt
        # Serializamos a JSON bonito para que Claude lo lea claramente
        personajes_str = json.dumps(relevant_context['personajes_aqui'], indent=2, ensure_ascii=False)
        problemas_str = json.dumps(relevant_context['problemas'], indent=2, ensure_ascii=False)
        
        system_prompt = f"""
        Eres un EDITOR LITERARIO DE ALTA FIDELIDAD. Tu trabajo es pulir la prosa, mejorar el ritmo y corregir errores sin perder la voz original del autor.
        
        CONTEXTO DE LA OBRA:
        {relevant_context['resumen_breve']}
        """

        user_prompt = f"""
        Revisa y mejora el siguiente capítulo.
        
        --- DATOS DE CONTEXTO ---
        PERSONAJES EN ESCENA (Usar para coherencia de voz/comportamiento):
        {personajes_str}
        
        INCONSISTENCIAS CRÍTICAS A CORREGIR (Prioridad Máxima):
        {problemas_str}
        
        --- TEXTO ORIGINAL ---
        TÍTULO: {chapter.get('title', '')}
        CONTENIDO:
        {chapter.get('content', '')}
        
        --- INSTRUCCIONES DE SALIDA ---
        1. Mantén la fidelidad a los hechos, pero mejora la prosa (elimina redundancias, mejora el vocabulario).
        2. Si hay inconsistencias listadas arriba, CORRÍGELAS en la narración.
        3. Devuelve SOLAMENTE el texto editado final. No incluyas "Aquí está el texto" ni comillas al inicio/final.
        """
        
        # 4. Llamada a la API
        logging.info(f"📞 Llamando a Claude ({chapter.get('title')})...")
        start_claude = time.time()
        
        # MODELO ESPECIFICADO EN EL DOCUMENTO
        # Nota: Si este modelo específico aún no está disponible públicamente, 
        model_id = "claude-sonnet-4-5-20250929" 
        
        response = call_claude_with_retry(client, model_id, system_prompt, user_prompt)
        
        claude_time = time.time() - start_claude
        edited_content = response.content[0].text
        
        # 5. Cálculo de Costos (Actualizado con precios estimados de Sonnet 3.5 actual)
        # Input: ~$3.00 / MTok | Output: ~$15.00 / MTok
        input_tokens = len(user_prompt.split()) * 1.33 # Estimación simple
        output_tokens = len(edited_content.split()) * 1.33
        
        cost_input = (input_tokens / 1_000_000) * 3.00
        cost_output = (output_tokens / 1_000_000) * 15.00
        total_cost = cost_input + cost_output
        
        result = {
            'chapter_id': chapter_id,
            'original_title': chapter.get('title'),
            'edited_content': edited_content,
            'metadata': {
                'model': model_id,
                'status': 'success',
                'cost_usd': round(total_cost, 6),
                'claude_time_seconds': round(claude_time, 2),
                'prep_time_seconds': round(prep_time, 2)
            }
        }
        
        total_time = time.time() - start_total
        logging.info(f"✅ Edición finalizada. Costo: ${total_cost:.6f}. Tiempo total: {total_time:.2f}s")
        return result

    except Exception as e:
        logging.error(f"❌ Error fatal en edición: {str(e)}")
        # En caso de error, devolvemos el texto original para no perder datos
        return {
            'chapter_id': edit_input.get('chapter', {}).get('id', '?'),
            'edited_content': edit_input.get('chapter', {}).get('content', ''), # Fallback al original
            'metadata': {'status': 'error', 'error_msg': str(e)}
        }
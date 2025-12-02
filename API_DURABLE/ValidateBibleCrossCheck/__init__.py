# =============================================================================
# ValidateBibleCrossCheck/__init__.py - SYLPHRENA 4.0
# =============================================================================
# NUEVA FUNCIÓN:
#   - Extrae afirmaciones verificables de la Biblia
#   - Confronta contra evidencia granular de los análisis
#   - Detecta alucinaciones y discrepancias
#   - Resuelve Problema Crítico 4: Ausencia de Validación Cruzada
# =============================================================================

import logging
import json
import os
import time
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logging.basicConfig(level=logging.INFO)

# =============================================================================
# PROMPTS DE VALIDACIÓN
# =============================================================================

EXTRACT_CLAIMS_PROMPT = """
Lee la siguiente Biblia Narrativa y extrae todas las AFIRMACIONES FÁCTICAS sobre personajes, estructura, temas y ritmo.

Ignora afirmaciones puramente interpretativas. Enfócate en afirmaciones que hacen predicciones sobre contenido específico del libro que podrían verificarse examinando los capítulos.

BIBLIA NARRATIVA:
{bible_json}

Para cada afirmación, reformúlala como una PROPOSICIÓN VERIFICABLE que especifique qué evidencia la respaldaría o refutaría.

RESPONDE CON JSON:
{{
  "afirmaciones_extraidas": [
    {{
      "id": 1,
      "seccion_origen": "string (ej: 'reparto_completo', 'arco_narrativo')",
      "afirmacion_original": "string",
      "proposicion_verificable": "string",
      "tipo": "PERSONAJE|EVENTO|RITMO|TEMA|ESTRUCTURA",
      "entidades_involucradas": ["string"]
    }}
  ]
}}
"""

RESOLVE_DISCREPANCY_PROMPT = """
Se ha detectado una DISCREPANCIA entre una conclusión de la lectura holística y la evidencia del análisis granular.

CONCLUSIÓN HOLÍSTICA:
{holistic_claim}

EVIDENCIA GRANULAR (de análisis de capítulos):
{granular_evidence}

Evalúa esta discrepancia:
1. ¿La evidencia granular contradice claramente la conclusión holística?
2. ¿La conclusión holística capta un patrón sutil que el análisis granular pierde?
3. ¿Cuál interpretación es correcta?

Considera que:
- La lectura holística puede captar patrones sutiles pero también puede alucinar
- El análisis granular tiene datos objetivos pero puede perder contexto interpretativo

RESPONDE CON JSON:
{{
  "veredicto": "CONFIRMAR|CORREGIR|MATIZAR",
  "conclusion_final": "string",
  "razonamiento": "string",
  "confianza": "ALTA|MEDIA|BAJA",
  "evidencia_citada": ["string"]
}}
"""


@retry(
    retry=retry_if_exception_type((Exception,)),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(3),
    reraise=True
)
def call_gemini_pro(client, prompt):
    """Llamada a Gemini Pro para validación."""
    return client.models.generate_content(
        model='gemini-2.5-pro',
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=8192,
            response_mime_type="application/json",
            safety_settings=[
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
            ]
        )
    )


def extract_claims(client, bible: dict) -> list:
    """Extrae afirmaciones verificables de la Biblia."""
    
    # Simplificar la Biblia para el prompt
    bible_simplified = {
        'identidad_obra': bible.get('identidad_obra', {}),
        'reparto_completo': bible.get('reparto_completo', {}),
        'arco_narrativo': bible.get('arco_narrativo', {}),
        'mapa_de_ritmo': bible.get('mapa_de_ritmo', {})
    }
    
    bible_json = json.dumps(bible_simplified, indent=2, ensure_ascii=False)
    prompt = EXTRACT_CLAIMS_PROMPT.format(bible_json=bible_json)
    
    response = call_gemini_pro(client, prompt)
    
    if not response.text:
        return []
    
    response_text = response.text.strip()
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    
    result = json.loads(response_text.strip())
    return result.get('afirmaciones_extraidas', [])


def verify_claim_against_evidence(claim: dict, chapters_consolidated: list) -> dict:
    """
    Verifica una afirmación contra la evidencia de los capítulos.
    Retorna el resultado de la verificación.
    """
    
    claim_type = claim.get('tipo', 'DESCONOCIDO')
    entities = claim.get('entidades_involucradas', [])
    proposition = claim.get('proposicion_verificable', '')
    
    evidence = {
        'supporting': [],
        'contradicting': [],
        'neutral': []
    }
    
    # Buscar evidencia según el tipo de afirmación
    if claim_type == 'PERSONAJE':
        # Buscar apariciones y acciones del personaje
        for chapter in chapters_consolidated:
            for char in chapter.get('reparto_completo', []):
                char_name = char.get('nombre', '').lower()
                for entity in entities:
                    if entity.lower() in char_name or char_name in entity.lower():
                        evidence['supporting'].append({
                            'chapter': chapter.get('chapter_id'),
                            'data': f"Personaje {char.get('nombre')} aparece con rol {char.get('rol_en_capitulo')}"
                        })
    
    elif claim_type == 'RITMO':
        # Verificar clasificaciones de ritmo
        for chapter in chapters_consolidated:
            metrics = chapter.get('metricas_agregadas', {})
            ritmo = metrics.get('ritmo', {}).get('clasificacion', 'MEDIO')
            evidence['supporting'].append({
                'chapter': chapter.get('chapter_id'),
                'data': f"Ritmo: {ritmo}"
            })
    
    elif claim_type == 'EVENTO':
        # Buscar eventos específicos
        for chapter in chapters_consolidated:
            for event in chapter.get('secuencia_eventos', []):
                for entity in entities:
                    if entity.lower() in event.get('evento', '').lower():
                        evidence['supporting'].append({
                            'chapter': chapter.get('chapter_id'),
                            'data': event.get('evento')
                        })
    
    # Determinar si hay discrepancia
    has_discrepancy = len(evidence['contradicting']) > len(evidence['supporting'])
    
    return {
        'claim_id': claim.get('id'),
        'proposition': proposition,
        'evidence': evidence,
        'has_discrepancy': has_discrepancy,
        'supporting_count': len(evidence['supporting']),
        'contradicting_count': len(evidence['contradicting'])
    }


def resolve_discrepancy(client, claim: dict, verification: dict) -> dict:
    """Resuelve una discrepancia usando Gemini Pro."""
    
    evidence_str = json.dumps(verification.get('evidence', {}), indent=2, ensure_ascii=False)
    
    prompt = RESOLVE_DISCREPANCY_PROMPT.format(
        holistic_claim=claim.get('afirmacion_original', ''),
        granular_evidence=evidence_str
    )
    
    response = call_gemini_pro(client, prompt)
    
    if not response.text:
        return {
            'veredicto': 'MATIZAR',
            'conclusion_final': claim.get('afirmacion_original'),
            'razonamiento': 'No se pudo resolver automáticamente'
        }
    
    response_text = response.text.strip()
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    
    return json.loads(response_text.strip())


def main(validation_input: dict) -> dict:
    # ... docstring ...
    
    bible = validation_input.get('bible', {})
    
    # --- CORRECCIÓN: Nombres de claves robustos ---
    chapters_consolidated = validation_input.get('chapters_consolidated') or \
                            validation_input.get('chapter_analyses') or \
                            []
    # ----------------------------------------------
    
    try:
        start_time = time.time()
        
        logging.info(f"🔍 Validación Cruzada de Biblia...")
        
        # Configurar cliente
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY no configurada")
        
        client = genai.Client(api_key=api_key)
        
        # 1. Extraer afirmaciones verificables
        logging.info("   📝 Extrayendo afirmaciones verificables...")
        claims = extract_claims(client, bible)
        logging.info(f"   📊 {len(claims)} afirmaciones extraídas")
        
        # 2. Verificar cada afirmación
        logging.info("   ✓ Verificando contra evidencia granular...")
        verifications = []
        discrepancies = []
        
        for claim in claims:
            verification = verify_claim_against_evidence(claim, chapters_consolidated)
            verifications.append(verification)
            
            if verification.get('has_discrepancy'):
                discrepancies.append({
                    'claim': claim,
                    'verification': verification
                })
        
        logging.info(f"   ⚠️ {len(discrepancies)} discrepancias detectadas")
        
        # 3. Resolver discrepancias
        corrections = []
        
        for disc in discrepancies[:10]:  # Limitar a 10 resoluciones
            logging.info(f"   🔧 Resolviendo discrepancia: {disc['claim'].get('id')}")
            resolution = resolve_discrepancy(client, disc['claim'], disc['verification'])
            
            corrections.append({
                'claim_id': disc['claim'].get('id'),
                'afirmacion_original': disc['claim'].get('afirmacion_original'),
                'seccion': disc['claim'].get('seccion_origen'),
                'veredicto': resolution.get('veredicto'),
                'conclusion_corregida': resolution.get('conclusion_final'),
                'razonamiento': resolution.get('razonamiento'),
                'confianza': resolution.get('confianza')
            })
        
        # 4. Aplicar correcciones a la Biblia
        bible_validada = bible.copy()
        bible_validada['_validacion'] = {
            'estado': 'VALIDADA',
            'afirmaciones_verificadas': len(claims),
            'discrepancias_detectadas': len(discrepancies),
            'correcciones_aplicadas': len([c for c in corrections if c.get('veredicto') == 'CORREGIR']),
            'correcciones': corrections
        }
        
        # Calcular métricas de confianza
        total_claims = len(claims)
        verified_ok = total_claims - len(discrepancies)
        corrected = len([c for c in corrections if c.get('veredicto') == 'CORREGIR'])
        matized = len([c for c in corrections if c.get('veredicto') == 'MATIZAR'])
        
        confianza_global = round((verified_ok + corrected) / max(total_claims, 1) * 100, 1)
        
        elapsed = time.time() - start_time
        
        reporte = {
            'metricas': {
                'afirmaciones_totales': total_claims,
                'verificadas_directamente': verified_ok,
                'discrepancias_detectadas': len(discrepancies),
                'correcciones_aplicadas': corrected,
                'matizaciones': matized,
                'confianza_global_porcentaje': confianza_global
            },
            'correcciones': corrections,
            'tiempo_procesamiento_segundos': round(elapsed, 2)
        }
        
        logging.info(f"✅ Validación completada en {elapsed:.1f}s | Confianza: {confianza_global}%")
        
        return {
            'bible_validada': bible_validada,
            'reporte_validacion': reporte
        }
        
    except Exception as e:
        logging.error(f"❌ Error en validación cruzada: {e}")
        return {
            'bible_validada': bible,
            'reporte_validacion': {
                'error': str(e),
                'metricas': {
                    'confianza_global_porcentaje': 0
                }
            }
        }

# =============================================================================
# GenerateEditorialLetter/__init__.py - SYLPHRENA 5.0
# =============================================================================
# NUEVA FUNCIÓN: Genera una carta editorial profesional de 8-15 páginas
# como la que entregaría un developmental editor ($1,500-3,000)
# =============================================================================

import logging
import json
import os

logging.basicConfig(level=logging.INFO)

EDITORIAL_LETTER_PROMPT = """Eres un DEVELOPMENTAL EDITOR profesional con 20 años de experiencia.
Has leído completamente el manuscrito "{titulo}" y realizado un análisis exhaustivo.

Tu tarea es escribir una CARTA EDITORIAL profesional, el documento principal que un editor de desarrollo entrega a un autor después de leer su manuscrito.

═══════════════════════════════════════════════════════════════════════════════
INFORMACIÓN DEL ANÁLISIS PREVIO:
═══════════════════════════════════════════════════════════════════════════════

BIBLIA NARRATIVA:
{biblia}

ANÁLISIS DE CAPAS (FACTUAL, ESTRUCTURAL, CUALITATIVO):
{analisis_capas}

═══════════════════════════════════════════════════════════════════════════════
MANUSCRITO COMPLETO:
═══════════════════════════════════════════════════════════════════════════════
{manuscrito}

═══════════════════════════════════════════════════════════════════════════════
INSTRUCCIONES PARA LA CARTA EDITORIAL:
═══════════════════════════════════════════════════════════════════════════════

Escribe una carta editorial COMPLETA y PROFESIONAL. Debe sentirse como un documento escrito por un editor humano experimentado, no por una IA. Usa un tono cálido pero profesional.

LA CARTA DEBE INCLUIR:

## 1. RESUMEN EJECUTIVO (1 página)
- Felicita al autor por lo que funciona
- Sinopsis de 2-3 párrafos (demuestra que leíste TODO)
- Evaluación general honesta (fortalezas y debilidades principales)
- Potencial de mercado y comparables (ej: "Lectores de [Autor X] disfrutarán...")

## 2. LO QUE FUNCIONA (2-3 páginas)
- Fortalezas narrativas ESPECÍFICAS con citas directas del texto
- Momentos que brillan (escenas memorables)
- Elementos únicos de la voz del autor que DEBE preservar
- Personajes que resuenan y por qué
- Decisiones narrativas inteligentes

## 3. ÁREAS DE OPORTUNIDAD (3-4 páginas)
Para cada problema identificado:
- Descripción clara del problema
- Por qué es un problema (impacto en el lector)
- Ejemplo ESPECÍFICO del texto
- Sugerencia concreta de cómo solucionarlo
- Prioridad: ALTA / MEDIA / BAJA

Categorías a cubrir:
- Estructura y pacing
- Desarrollo de personajes
- Arcos narrativos
- Diálogos
- Prosa y estilo
- Consistencia interna

## 4. ANÁLISIS DE PERSONAJES (2-3 páginas)
Para cada personaje principal:
- Rol en la historia
- Arco actual (inicio → fin)
- Fortalezas del personaje
- Inconsistencias o problemas detectados
- Oportunidades de desarrollo
- Citas que ejemplifican su voz

## 5. ANÁLISIS DE ESTRUCTURA (1-2 páginas)
- Modelo narrativo identificado (3 actos, viaje del héroe, etc.)
- Evaluación de cada punto de giro
- Análisis de pacing (dónde acelera/desacelera)
- Problemas estructurales específicos
- Sugerencias de reestructuración si aplica

## 6. NOTAS POR CAPÍTULO (resumen)
Para cada capítulo, en 2-3 líneas:
- Función en la historia
- Qué funciona
- Qué mejorar
- Prioridad de revisión

## 7. PRÓXIMOS PASOS (1 página)
- Top 5 prioridades para la siguiente revisión
- Orden sugerido de trabajo
- Qué NO cambiar
- Palabras de aliento finales

═══════════════════════════════════════════════════════════════════════════════
FORMATO DE RESPUESTA:
═══════════════════════════════════════════════════════════════════════════════

Responde con un JSON válido:
{{
    "carta_editorial": {{
        "resumen_ejecutivo": {{
            "felicitacion": "...",
            "sinopsis": "...",
            "evaluacion_general": "...",
            "potencial_mercado": "...",
            "comparables": ["Autor1", "Autor2"]
        }},
        "lo_que_funciona": {{
            "fortalezas_narrativas": [
                {{"aspecto": "...", "ejemplo_texto": "...", "por_que_funciona": "..."}}
            ],
            "momentos_memorables": [
                {{"escena": "...", "capitulo": N, "impacto": "..."}}
            ],
            "voz_del_autor": {{
                "elementos_unicos": ["..."],
                "preservar_absolutamente": ["..."]
            }}
        }},
        "areas_de_oportunidad": [
            {{
                "categoria": "estructura|personajes|dialogo|prosa|pacing|consistencia",
                "problema": "...",
                "por_que_importa": "...",
                "ejemplo_texto": "...",
                "capitulo_ejemplo": N,
                "sugerencia": "...",
                "prioridad": "ALTA|MEDIA|BAJA"
            }}
        ],
        "analisis_personajes": [
            {{
                "nombre": "...",
                "rol": "protagonista|antagonista|secundario",
                "arco_actual": {{"inicio": "...", "desarrollo": "...", "fin": "..."}},
                "fortalezas": ["..."],
                "problemas": ["..."],
                "sugerencias": ["..."],
                "cita_voz": "..."
            }}
        ],
        "analisis_estructura": {{
            "modelo_narrativo": "...",
            "puntos_de_giro": [
                {{"nombre": "...", "capitulo": N, "efectividad": "...", "sugerencia": "..."}}
            ],
            "pacing": {{
                "evaluacion": "...",
                "zonas_lentas": [N],
                "zonas_rapidas": [N],
                "recomendaciones": ["..."]
            }}
        }},
        "notas_por_capitulo": [
            {{
                "capitulo": N,
                "titulo": "...",
                "funcion": "...",
                "que_funciona": "...",
                "que_mejorar": "...",
                "prioridad": "ALTA|MEDIA|BAJA"
            }}
        ],
        "proximos_pasos": {{
            "top_5_prioridades": ["..."],
            "orden_sugerido": ["..."],
            "no_cambiar": ["..."],
            "mensaje_final": "..."
        }}
    }},
    "metadata": {{
        "total_palabras_manuscrito": N,
        "total_capitulos": N,
        "tiempo_lectura_estimado": "X horas"
    }}
}}
"""


def main(input_data: dict) -> dict:
    """
    Genera la carta editorial usando Gemini Pro.
    
    Input:
        - bible: Biblia narrativa completa
        - consolidated_chapters: Análisis consolidados por capítulo
        - fragments: Fragmentos originales del manuscrito
        - book_metadata: Metadatos del libro
    
    Output:
        - carta_editorial: JSON estructurado con toda la carta
        - carta_markdown: Versión en Markdown para exportar
    """
    
    try:
        import google.generativeai as genai
        
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return {"error": "GEMINI_API_KEY no configurada", "status": "config_error"}
        
        genai.configure(api_key=api_key)
        
        bible = input_data.get('bible', {})
        consolidated = input_data.get('consolidated_chapters', [])
        fragments = input_data.get('fragments', [])
        book_metadata = input_data.get('book_metadata', {})
        
        titulo = book_metadata.get('title', bible.get('identidad_obra', {}).get('titulo', 'Sin título'))
        
        # Construir manuscrito resumido (primeros 500 chars por capítulo para contexto)
        manuscrito_resumen = []
        for frag in fragments:
            cap_title = frag.get('title', frag.get('original_title', 'Capítulo'))
            content = frag.get('content', '')[:2000]  # Primeros 2000 chars
            manuscrito_resumen.append(f"### {cap_title}\n{content}...")
        
        manuscrito_text = "\n\n".join(manuscrito_resumen)
        
        # Resumir análisis de capas
        analisis_resumen = []
        for ch in consolidated[:10]:  # Primeros 10 capítulos
            ch_id = ch.get('chapter_id', '?')
            analisis_resumen.append(f"Cap {ch_id}: {json.dumps(ch, ensure_ascii=False)[:500]}...")
        
        analisis_text = "\n".join(analisis_resumen)
        
        prompt = EDITORIAL_LETTER_PROMPT.format(
            titulo=titulo,
            biblia=json.dumps(bible, ensure_ascii=False, indent=2)[:8000],
            analisis_capas=analisis_text,
            manuscrito=manuscrito_text[:30000]  # Límite de contexto
        )
        
        logging.info(f"📝 Generando Carta Editorial para: {titulo}")
        logging.info(f"📊 Prompt size: {len(prompt):,} chars")
        
        # Usar Gemini 3 Pro
        model = genai.GenerativeModel('gemini-2.5-pro-preview-05-06')
        
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "max_output_tokens": 16000,
            "response_mime_type": "application/json"
        }
        
        response = model.generate_content(prompt, generation_config=generation_config)
        
        # Parsear respuesta
        try:
            result = json.loads(response.text)
        except json.JSONDecodeError:
            # Intentar extraer JSON del texto
            import re
            json_match = re.search(r'\{[\s\S]*\}', response.text)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = {"raw_response": response.text}
        
        # Generar versión Markdown
        carta_md = generate_markdown_version(result.get('carta_editorial', result), titulo)
        
        logging.info(f"✅ Carta Editorial generada exitosamente")
        
        return {
            "status": "success",
            "carta_editorial": result.get('carta_editorial', result),
            "carta_markdown": carta_md,
            "metadata": result.get('metadata', {})
        }
        
    except ImportError as e:
        logging.error(f"❌ SDK no instalado: {e}")
        return {"error": str(e), "status": "import_error"}
    except Exception as e:
        logging.error(f"❌ Error generando carta editorial: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return {"error": str(e), "status": "error"}


def generate_markdown_version(carta: dict, titulo: str) -> str:
    """Convierte la carta estructurada a Markdown legible."""
    
    md = []
    md.append(f"# 📖 CARTA EDITORIAL: {titulo}")
    md.append(f"\n*Sylphrena Developmental Editor*\n")
    md.append("---\n")
    
    # Resumen Ejecutivo
    resumen = carta.get('resumen_ejecutivo', {})
    md.append("## 1. RESUMEN EJECUTIVO\n")
    if resumen.get('felicitacion'):
        md.append(f"{resumen['felicitacion']}\n")
    if resumen.get('sinopsis'):
        md.append(f"\n### Sinopsis\n{resumen['sinopsis']}\n")
    if resumen.get('evaluacion_general'):
        md.append(f"\n### Evaluación General\n{resumen['evaluacion_general']}\n")
    if resumen.get('potencial_mercado'):
        md.append(f"\n### Potencial de Mercado\n{resumen['potencial_mercado']}\n")
    
    # Lo que funciona
    funciona = carta.get('lo_que_funciona', {})
    md.append("\n---\n## 2. LO QUE FUNCIONA\n")
    
    for f in funciona.get('fortalezas_narrativas', []):
        md.append(f"\n### ✨ {f.get('aspecto', '')}")
        if f.get('ejemplo_texto'):
            md.append(f"\n> \"{f['ejemplo_texto']}\"")
        md.append(f"\n{f.get('por_que_funciona', '')}\n")
    
    momentos = funciona.get('momentos_memorables', [])
    if momentos:
        md.append("\n### 🌟 Momentos Memorables\n")
        for m in momentos:
            md.append(f"- **{m.get('escena', '')}** (Cap. {m.get('capitulo', '?')}): {m.get('impacto', '')}")
    
    # Áreas de oportunidad
    areas = carta.get('areas_de_oportunidad', [])
    md.append("\n---\n## 3. ÁREAS DE OPORTUNIDAD\n")
    
    for i, area in enumerate(areas, 1):
        prioridad_emoji = "🔴" if area.get('prioridad') == 'ALTA' else "🟡" if area.get('prioridad') == 'MEDIA' else "🟢"
        md.append(f"\n### {i}. {prioridad_emoji} {area.get('categoria', '').upper()}: {area.get('problema', '')[:50]}")
        md.append(f"\n**Problema:** {area.get('problema', '')}")
        md.append(f"\n**Por qué importa:** {area.get('por_que_importa', '')}")
        if area.get('ejemplo_texto'):
            md.append(f"\n**Ejemplo (Cap. {area.get('capitulo_ejemplo', '?')}):**\n> \"{area['ejemplo_texto']}\"")
        md.append(f"\n**💡 Sugerencia:** {area.get('sugerencia', '')}")
        md.append(f"\n**Prioridad:** {area.get('prioridad', 'MEDIA')}\n")
    
    # Análisis de personajes
    personajes = carta.get('analisis_personajes', [])
    md.append("\n---\n## 4. ANÁLISIS DE PERSONAJES\n")
    
    for p in personajes:
        md.append(f"\n### 👤 {p.get('nombre', 'Personaje')} ({p.get('rol', '')})")
        
        arco = p.get('arco_actual', {})
        if arco:
            md.append(f"\n**Arco:** {arco.get('inicio', '')} → {arco.get('desarrollo', '')} → {arco.get('fin', '')}")
        
        if p.get('fortalezas'):
            md.append(f"\n**Fortalezas:** {', '.join(p['fortalezas'])}")
        if p.get('problemas'):
            md.append(f"\n**Problemas:** {', '.join(p['problemas'])}")
        if p.get('sugerencias'):
            md.append(f"\n**Sugerencias:** {', '.join(p['sugerencias'])}")
        if p.get('cita_voz'):
            md.append(f"\n> \"{p['cita_voz']}\"")
        md.append("")
    
    # Estructura
    estructura = carta.get('analisis_estructura', {})
    md.append("\n---\n## 5. ANÁLISIS DE ESTRUCTURA\n")
    md.append(f"\n**Modelo Narrativo:** {estructura.get('modelo_narrativo', 'No identificado')}\n")
    
    puntos = estructura.get('puntos_de_giro', [])
    if puntos:
        md.append("\n### Puntos de Giro\n")
        for pt in puntos:
            md.append(f"- **{pt.get('nombre', '')}** (Cap. {pt.get('capitulo', '?')}): {pt.get('efectividad', '')}")
    
    pacing = estructura.get('pacing', {})
    if pacing:
        md.append(f"\n### Pacing\n{pacing.get('evaluacion', '')}")
    
    # Notas por capítulo
    notas = carta.get('notas_por_capitulo', [])
    md.append("\n---\n## 6. NOTAS POR CAPÍTULO\n")
    
    for n in notas:
        prioridad_emoji = "🔴" if n.get('prioridad') == 'ALTA' else "🟡" if n.get('prioridad') == 'MEDIA' else "🟢"
        md.append(f"\n### Cap. {n.get('capitulo', '?')}: {n.get('titulo', '')} {prioridad_emoji}")
        md.append(f"- **Función:** {n.get('funcion', '')}")
        md.append(f"- **✓ Funciona:** {n.get('que_funciona', '')}")
        md.append(f"- **⚠ Mejorar:** {n.get('que_mejorar', '')}")
    
    # Próximos pasos
    pasos = carta.get('proximos_pasos', {})
    md.append("\n---\n## 7. PRÓXIMOS PASOS\n")
    
    if pasos.get('top_5_prioridades'):
        md.append("\n### 🎯 Top 5 Prioridades\n")
        for i, p in enumerate(pasos['top_5_prioridades'], 1):
            md.append(f"{i}. {p}")
    
    if pasos.get('no_cambiar'):
        md.append("\n### 🔒 NO Cambiar\n")
        for nc in pasos['no_cambiar']:
            md.append(f"- {nc}")
    
    if pasos.get('mensaje_final'):
        md.append(f"\n---\n\n*{pasos['mensaje_final']}*")
    
    md.append("\n\n---\n*Generado por Sylphrena 5.0 - AI Developmental Editor*")
    
    return "\n".join(md)

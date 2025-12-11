#!/usr/bin/env python
"""
Script para corregir el prompt inicial en ReflectionEditingLoop
"""

filepath = r"c:\Sylphrena\LYA\API_DURABLE\ReflectionEditingLoop\__init__.py"

old_code = """        # Construir contexto completo para primera edición
        # (Usamos el prompt existente de SubmitClaudeBatch, pero llamada directa)
        from SubmitClaudeBatch import build_editing_prompt

        initial_prompt = build_editing_prompt(
            chapter=chapter,
            bible=bible,
            consolidated_chapters=input_data.get('consolidated_chapters', []),
            arc_map=arc_map,
            margin_notes=margin_notes,
            metadata=metadata
        )"""

new_code = """        # Construir prompt inicial de edición
        chapter_content = chapter.get('content', '')
        chapter_title = chapter.get('title', chapter.get('original_title', 'Sin título'))

        # Formatear notas de margen
        notas_str = "\\n".join([f"- {n.get('nota', '')}: {n.get('sugerencia', '')}"
                               for n in margin_notes]) if margin_notes else "(Sin notas de margen)"

        initial_prompt = f\"\"\"Eres un DEVELOPMENTAL EDITOR profesional editando "{metadata.get('title', 'Sin título')}".

═══════════════════════════════════════════════════════════════════════════════
CONTEXTO DE LA OBRA
═══════════════════════════════════════════════════════════════════════════════
- Género: {genero}
- Tono: {tono}
- Voz del autor: {voz_desc}

RESTRICCIONES ABSOLUTAS (NO MODIFICAR):
{no_corregir_text}

═══════════════════════════════════════════════════════════════════════════════
CAPÍTULO A EDITAR: {chapter_title}
═══════════════════════════════════════════════════════════════════════════════

NOTAS DE MARGEN DEL EDITOR (priorizar):
{notas_str}

═══════════════════════════════════════════════════════════════════════════════
TEXTO A EDITAR
═══════════════════════════════════════════════════════════════════════════════
{chapter_content}

═══════════════════════════════════════════════════════════════════════════════
CRITERIOS DE EDICIÓN
═══════════════════════════════════════════════════════════════════════════════
1. **Show vs Tell**: Convierte declaraciones en acciones/sensaciones observables
2. **Profundidad emocional**: Ancla emociones en sensaciones físicas
3. **Economía narrativa**: Elimina redundancias genuinas
4. **Voz del autor**: Preserva el estilo distintivo
5. **Coherencia**: Respeta la Biblia Narrativa

═══════════════════════════════════════════════════════════════════════════════
INSTRUCCIONES
═══════════════════════════════════════════════════════════════════════════════
1. Lee todo el capítulo primero
2. Identifica problemas según criterios
3. Prioriza las notas de margen del editor
4. Edita preservando la voz del autor

Responde SOLO con JSON (sin markdown):
{{
  "capitulo_editado": "texto editado completo",
  "cambios_aplicados": [
    {{
      "tipo": "show_tell|redundancia|claridad|dialogos|etc",
      "original": "fragmento original",
      "editado": "fragmento editado",
      "justificacion": "por qué este cambio mejora el texto",
      "impacto_narrativo": "bajo|medio|alto"
    }}
  ]
}}
\"\"\""""

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

if old_code in content:
    content = content.replace(old_code, new_code)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print("[OK] Corrección aplicada exitosamente")
else:
    print("[SKIP] No se encontró el código a reemplazar (puede que ya esté corregido)")

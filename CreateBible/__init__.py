import logging
import json
import os
import re
import time as time_module  # NAMESPACE COMPLETAMENTE SEPARADO
from collections import defaultdict
import google.generativeai as genai

def agrupar_fragmentos(analyses):
    """
    Middleware: Convierte análisis planos en capítulos consolidados
    usando el metadato 'parent_chapter' para precisión absoluta.
    """
    capitulos_consolidados = defaultdict(lambda: {
        "titulo": "",
        "fragmentos": [],
        "metadata_agregada": {
            "ids_involucrados": [],
        }
    })

    # Ya no necesitamos el regex de limpieza si confiamos en el upstream
    # patron_limpieza = re.compile(...) <--- ELIMINAR O COMENTAR

    for analysis in analyses:
        # LÓGICA MEJORADA:
        # Usamos parent_chapter si existe (lo ideal), si no, fallback al título
        clean_title = analysis.get("parent_chapter") or analysis.get("titulo_real") or analysis.get("original_title") or "Sin Título"
        
        capitulos_consolidados[clean_title]["titulo"] = clean_title
        capitulos_consolidados[clean_title]["fragmentos"].append(analysis)
        
        # Nota: Asegúrate que 'id' o 'chapter_id' vengan consistentes
        capitulos_consolidados[clean_title]["metadata_agregada"]["ids_involucrados"].append(
            analysis.get("id") or analysis.get("chapter_id", "?")
        )

    resultado = list(capitulos_consolidados.values())
    logging.info(f"📦 Agrupación: {len(analyses)} fragmentos → {len(resultado)} capítulos")
    return resultado

def main(analyses_json) -> dict:
    """
    Fase REDUCE con medición de tiempo de Gemini Pro.
    """
    try:
        # 1. Manejo de entrada
        if isinstance(analyses_json, str):
            try:
                analyses = json.loads(analyses_json)
            except json.JSONDecodeError:
                logging.warning("analyses_json inválido, usando lista vacía")
                analyses = []
        else:
            analyses = analyses_json
            
        # 2. AGRUPACIÓN
        capitulos_estructurados = agrupar_fragmentos(analyses)
        logging.info(f"📚 Procesando {len(capitulos_estructurados)} capítulos consolidados...")

        # Configurar Gemini Pro
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY no configurada")
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('models/gemini-3-pro-preview')
        
        # 3. PROMPT
    # 3. PROMPT DE INGENIERÍA (AGNÓSTICO / UNIVERSAL)
        prompt = f"""
        Eres el EDITOR JEFE del Proyecto Sylphrena. Tienes acceso a los análisis forenses de todos los capítulos de una obra literaria completa.
        Tu misión es construir la "Biblia Narrativa", la fuente única de verdad para la consistencia de la historia.

        DATOS DE ENTRADA (Capítulos Consolidados):
        {json.dumps(capitulos_estructurados, indent=2, ensure_ascii=False)}
        
        --- INSTRUCCIONES CRÍTICAS (APLICABLES A CUALQUIER OBRA) ---
        
        1. **TAXONOMÍA DE PERSONAJES (JERARQUÍA Y ROLES)**:
           Genera una lista definitiva basada en la preponderancia narrativa.
           - **Protagonistas**: Identifica al núcleo central. Define sus arquetipos (Ej: El Líder, El Intelectual, La Fuerza Física, La Brújula Moral, etc., según corresponda a ESTA historia).
           - **Antagonistas**: Identifica las fuerzas de oposición (individuos, familias rivales, instituciones o entidades). Define la naturaleza exacta del conflicto (¿Es territorial? ¿Ideológico? ¿Venganza personal?).
           - **Secundarios**: Personajes de soporte, alivio cómico o catalizadores de trama.
           
        2. **CRONOLOGÍA MAESTRA (LINEA DE TIEMPO ABSOLUTA)**:
           - Establece una línea temporal lógica unificada.
           - Conecta eventos dispersos: Vincula causas (ej. un evento detonante al inicio) con sus consecuencias tardías.
           - Rastrea el paso del tiempo: Identifica marcadores como "días después", "a la mañana siguiente", cambios de estación o fechas específicas si existen.
        
        3. **DETECCIÓN DE INCONSISTENCIAS (CONTINUIDAD)**:
           - Cruza datos entre todos los capítulos para hallar errores lógicos.
           - **Continuidad Física**: Rastrea heridas, objetos poseídos y ubicación de personajes. (Ej: Si alguien pierde un arma en el Cap 1, no puede tenerla en el Cap 3 sin explicación).
           - **Continuidad Emocional/Relacional**: ¿Las relaciones evolucionan coherentemente? (Ej: Enemigos que se tratan bien sin motivo aparente).
           - Marca cualquier discrepancia como "CRÍTICA".

        DEVUELVE JSON ESTRICTO:
        {{
            "resumen_ejecutivo": "Sinopsis de alto nivel de la obra completa, enfocada en el arco dramático.",
            "reparto_organizado": {{
                "protagonistas": [
                    {{"nombre": "...", "rol_arquetipo": "...", "arco_detectado": "..."}}
                ],
                "antagonistas": [
                    {{"nombre": "...", "origen_conflicto": "...", "nivel_amenaza": "..."}}
                ],
                "secundarios": []
            }},
            "linea_temporal_maestra": [
                {{"tiempo_estimado": "Ej: Día 1, Noche / Año 1943", "evento_clave": "...", "capitulos_source": ["..."]}}
            ],
            "inconsistencias_criticas": [
                {{
                    "tipo": "Continuidad Física/Lógica/Temporal", 
                    "descripcion": "Descripción detallada del error de continuidad", 
                    "capitulos_en_conflicto": ["Título Cap A", "Título Cap B"],
                    "severidad": "ALTA/MEDIA"
                }}
            ],
            "analisis_simbolico_global": [
                {{"objeto_o_tema_recurrente": "...", "significado_consolidado": "..."}}
            ]
        }}
        """
        
        try:
            # 4. ⏱️ MEDICIÓN DE TIEMPO
            start_gemini_pro = time_module.time()  # USANDO EL ALIAS ÚNICO
            logging.info(f"🚀 Llamando a Gemini Pro para crear Biblia...")
            
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.1,
                    "max_output_tokens": 8192,
                    "response_mime_type": "application/json"
                },
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                ]
            )
            
            gemini_pro_elapsed = time_module.time() - start_gemini_pro  # USANDO EL ALIAS ÚNICO
            logging.info(f"⏱️  Gemini Pro tardó {gemini_pro_elapsed:.2f}s en crear la Biblia")
            
            if not response.candidates:
                raise ValueError("Bloqueo de seguridad en Gemini Pro.")

            bible = json.loads(response.text)
            
            # Metadata con tiempo de procesamiento
            input_tokens = len(prompt.split()) * 1.3
            cost = input_tokens * 0.0000035 
            
            bible['_metadata'] = {
                'estimated_cost': round(cost, 5),
                'model': 'gemini-3-pro-preview',
                'status': 'success',
                'chapters_grouped': len(capitulos_estructurados),
                'processing_time_seconds': round(gemini_pro_elapsed, 2)
            }
            
            logging.info(f"✅ Biblia creada. Capítulos: {len(capitulos_estructurados)}, Costo: ${cost:.5f}, Tiempo: {gemini_pro_elapsed:.2f}s")
            return bible

        except Exception as ai_error:
            logging.error(f"⚠️ Error en Gemini Pro: {str(ai_error)}")
            return {
                "resumen_ejecutivo": "Error generando biblia (Fallo de IA).",
                "reparto_organizado": {
                    "protagonistas": [],
                    "antagonistas": [],
                    "secundarios": []
                },
                "diagnostico_literario": {
                    "estilo_predominante": "Error",
                    "vicios_detectados": [],
                    "sugerencias_recorte": []
                },
                "linea_temporal_maestra": [],
                "analisis_simbolico": [],
                "inconsistencias_criticas": [],
                "_metadata": {
                    "error": str(ai_error),
                    "status": "fallback"
                }
            }
            
    except Exception as e:
        logging.error(f"💥 Error fatal en CreateBible: {str(e)}")
        raise
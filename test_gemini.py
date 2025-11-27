# test_gemini.py ACTUALIZADO (Para google-genai v1)
from google import genai
import os
import json

# --- CARGA DE VARIABLES ---
if os.path.exists('local.settings.json'):
    with open('local.settings.json') as f:
        config = json.load(f)
        for key, value in config.get("Values", {}).items():
            os.environ[key] = value

def test_all_available_models():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY no encontrada.")
        return

    client = genai.Client(api_key=api_key)
    
    print(f"Buscando modelos disponibles para tu API Key (SDK v1)...\n")
    print(f"{'MODELO':<50} | {'RESULTADO'}")
    print("-" * 70)

    try:
        # En el nuevo SDK, list() devuelve un iterador de modelos
        for m in client.models.list():
            # Filtramos modelos que parecen de generación de texto/multimodal
            # (El nuevo SDK maneja esto diferente, probamos generativos típicos)
            model_name = m.name
            
            # Filtro simple: ignorar modelos de embedding o tuning si solo queremos probar chat
            if "embedding" in model_name or "bison" in model_name:
                continue

            # Probamos generar contenido
            try:
                # La llamada es client.models.generate_content
                response = client.models.generate_content(
                    model=model_name,
                    contents="Responde solo con la palabra: Funciona"
                )
                print(f"{model_name:<50} | ✅ {response.text.strip()}")
            except Exception as e:
                # Capturamos errores (404, permisos, etc)
                error_msg = str(e).split('\n')[0]
                if "404" in error_msg:
                    print(f"{model_name:<50} | ⚠️ No encontrado/Soportado")
                else:
                    print(f"{model_name:<50} | ⚠️ Error: {error_msg[:40]}...")
                    
    except Exception as e:
        print(f"Error listando modelos: {e}")

if __name__ == "__main__":
    test_all_available_models()
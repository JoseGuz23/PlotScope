import google.generativeai as genai
import os
import json

# --- CARGA DE VARIABLES (Tu bloque de configuración local) ---
if os.path.exists('local.settings.json'):
    with open('local.settings.json') as f:
        config = json.load(f)
        for key, value in config.get("Values", {}).items():
            os.environ[key] = value

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

def test_all_available_models():
    print(f"Buscando modelos disponibles para tu API Key...\n")
    
    print(f"{'MODELO':<50} | {'RESULTADO'}")
    print("-" * 70)

    # 1. Obtenemos la lista dinámica de modelos desde Google
    for m in genai.list_models():
        
        # 2. FILTRO: Solo probamos modelos que soporten 'generateContent'
        # (Ignoramos modelos de embeddings o tuning que darían error aquí)
        if 'generateContent' in m.supported_generation_methods:
            model_name = m.name
            
            try:
                # Instanciamos y probamos
                model = genai.GenerativeModel(model_name)
                response = model.generate_content("Responde solo con la palabra: Funciona")
                
                # Si llega aquí, es exitoso
                print(f"{model_name:<50} | ✅ {response.text.strip()}")
                
            except Exception as e:
                # Capturamos errores (ej. modelos deprecados o sin acceso en tu región)
                error_msg = str(e).split('\n')[0]
                print(f"{model_name:<50} | ⚠️ Error: {error_msg[:40]}...")

if __name__ == "__main__":
    test_all_available_models()
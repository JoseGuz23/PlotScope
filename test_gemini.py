import google.generativeai as genai
import os

# Configurar API
genai.configure(api_key="AIzaSyDPM9BhXcOiBSHBK4-O77ceJChfONfi3nM")

def test_correct_models():
    # Lista corregida basada en tu salida de consola
    models_to_test = [
        "models/gemini-3-propreview",                # La versión más potente (Gemini 3)
        "models/gemini-2.5-flash",    # La versión rápida específica
        "models/gemini-pro-latest"                    # Alias genérico estable
    ]

    print(f"{'MODELO':<45} | {'RESULTADO'}")
    print("-" * 65)

    for model_name in models_to_test:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("Responde solo con la palabra: Funciona")
            print(f"{model_name:<45} | ✅ {response.text.strip()}")
            
        except Exception as e:
            # Limpiamos el error para que no llene la pantalla
            error_msg = str(e).split('\n')[0] 
            print(f"{model_name:<45} | ⚠️ Error: {error_msg[:30]}...")

if __name__ == "__main__":
    test_correct_models()
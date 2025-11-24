import os
from anthropic import Anthropic

def get_available_models():
    print("=== CONSULTANDO MODELOS DISPONIBLES EN TU CUENTA ANTHROPIC ===\n")
    
    # ---------------------------------------------------------
    # PEGA TU API KEY AQUÍ
    # ---------------------------------------------------------
    api_key = "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"
    
    if "sk-ant-api03-..." in api_key:
        print("❌ ERROR: Por favor edita el script y pega tu API Key real.")
        return

    try:
        client = Anthropic(api_key=api_key)
        
        # Esta línea hace la magia: le pide la lista al servidor
        # El límite=100 asegura que traiga todos, ordenados del más nuevo al más viejo
        models_page = client.models.list(limit=100)
        
        print(f"{'ID DEL MODELO (Poner esto en el código)':<45} | {'NOMBRE REAL'}")
        print("-" * 75)
        
        available_models = []
        
        for model in models_page:
            # Filtramos solo los que sean "claude" para evitar ruido
            if "claude" in model.id:
                print(f"{model.id:<45} | {model.display_name}")
                available_models.append(model.id)
        
        print("-" * 75)
        
        if available_models:
            print(f"\n✅ RECOMENDACIÓN: Copia y pega este ID en tu código:")
            # El primero de la lista suele ser el más reciente
            print(f"model=\"{available_models[0]}\"")
        else:
            print("\n⚠️ No se encontraron modelos 'claude' en tu lista. Revisa tu plan.")

    except Exception as e:
        print(f"\n❌ Error de conexión: {e}")
        print("Nota: Si dice 'authentication_error', tu llave está mal.")

if __name__ == "__main__":
    get_available_models()
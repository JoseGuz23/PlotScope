import requests
import json

# TU CONFIGURACIÓN
INSTANCE_ID = "37b45a54d25348dda39a157d5e02e2dd" 
BASE_URL = "https://sylphrena-orchestrator-ece2a4epbdbrfbgk.westus3-01.azurewebsites.net"
# La Master Key suele ser necesaria para consultar arbitrary IDs, 
# pero prueba con tu function key actual primero.
FUNCTION_KEY = "MIp55UvFMQvH2JDSlntTO5h1kuntjEASEkwstAMCcIPuAzFu1Vrhmg==" 

def check_ghost_process():
    print(f"🕵️ Buscando forense del proceso: {INSTANCE_ID}")
    
    url = f"{BASE_URL}/runtime/webhooks/durabletask/instances/{INSTANCE_ID}"
    
    try:
        response = requests.get(
            url, 
            headers={"x-functions-key": FUNCTION_KEY},
            params={"showHistory": "true", "showInput": "false"} # Pedimos el historial para ver qué pasó
        )
        
        if response.status_code == 200:
            data = response.json()
            status = data.get("runtimeStatus")
            output = data.get("output")
            history = data.get("historyEvents", [])
            
            print(f"💀 Estado Final: {status}")
            
            if status == "Failed":
                print(f"❌ Razón del fallo: {output}")
            
            print(f"\n📜 Historial de Eventos ({len(history)} eventos):")
            # Buscamos si algún capítulo se completó antes de morir
            completed_chapters = 0
            for event in history:
                if event['EventType'] == 'TaskCompleted' and 'AnalyzeChapter' in event.get('FunctionName', ''):
                    completed_chapters += 1
                    print(f"   ✅ Capítulo analizado (recuperable en logs)")
            
            print(f"\n📊 Total Capítulos Salvados: {completed_chapters}")
            
        else:
            print(f"❌ No se pudo conectar. Code: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_ghost_process()
#!/usr/bin/env python3
"""
test_mvp_v2.py - Script de prueba para Sylphrena MVP (CORREGIDO)
================================================================

Uso:
    python test_mvp_v2.py              # Inicia nueva orquestación
    python test_mvp_v2.py --no-wait    # Inicia sin esperar resultado
"""

import os
import sys
import json
import time
import argparse
import requests
from datetime import datetime

# =============================================================================
# CONFIGURACIÓN - AJUSTA ESTOS VALORES
# =============================================================================

# Tu Function App URL base
FUNCTION_APP_BASE = "https://sylphrena-orchestrator-ece2a4epbdbrfbgk.westus3-01.azurewebsites.net"

# Tiempo máximo de espera (minutos)
MAX_WAIT_MINUTES = 180

# Intervalo de polling (segundos)
POLL_INTERVAL = 20


# =============================================================================
# FUNCIONES
# =============================================================================

def get_function_key():
    """Obtiene la API key de local.settings.json o variables de entorno."""
    
    # Primero intentar leer de local.settings.json
    local_settings_path = os.path.join(os.path.dirname(__file__), 'local.settings.json')
    
    if os.path.exists(local_settings_path):
        try:
            with open(local_settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                key = settings.get('Values', {}).get('Azure_Function_Key')
                if key:
                    print(f"🔑 Key cargada desde local.settings.json")
                    return key
        except Exception as e:
            print(f"⚠️ Error leyendo local.settings.json: {e}")
    
    # Fallback a variable de entorno
    key = os.environ.get('Azure_Function_Key')
    if key:
        print(f"🔑 Key cargada desde variable de entorno")
        return key
    
    # No encontrada
    print("❌ ERROR: 'Azure_Function_Key' no encontrada.")
    print("\n   Opciones:")
    print("   1. Agrégala a local.settings.json:")
    print('      "Values": { "Azure_Function_Key": "tu_key_aqui" }')
    print("\n   2. O configura variable de entorno:")
    print("      $env:Azure_Function_Key=\"tu_key_aqui\"")
    sys.exit(1)


def print_header():
    print("\n" + "=" * 60)
    print("  🌸 SYLPHRENA MVP - Test Runner v2")
    print("=" * 60)
    print(f"  Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")


def format_duration(seconds):
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    if minutes > 0:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def start_orchestration(book_input="test_book.txt"):
    """Inicia una nueva orquestación."""
    api_key = get_function_key()
    
    # URL de HttpStart con código
    url = f"{FUNCTION_APP_BASE}/api/HttpStart?code={api_key}"
    
    print(f"🚀 Iniciando orquestación...")
    print(f"   Input: {book_input}")
    print(f"   URL: {url[:60]}...")
    
    try:
        response = requests.post(
            url,
            json=book_input,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"\n   HTTP Status: {response.status_code}")
        
        if response.status_code in [200, 202]:
            data = response.json()
            
            # Debug: mostrar qué devolvió Azure
            print(f"\n   📦 Respuesta de Azure:")
            print(f"   - id: {data.get('id', 'N/A')}")
            print(f"   - statusQueryGetUri: {'✅ Presente' if data.get('statusQueryGetUri') else '❌ Falta'}")
            print(f"   - sendEventPostUri: {'✅ Presente' if data.get('sendEventPostUri') else '❌ Falta'}")
            
            instance_id = data.get('id')
            status_url = data.get('statusQueryGetUri')
            
            if not status_url:
                print("\n❌ ERROR: Azure no devolvió statusQueryGetUri")
                print(f"   Respuesta completa: {json.dumps(data, indent=2)[:500]}")
                return None
            
            print(f"\n✅ Orquestación iniciada!")
            print(f"   Instance ID: {instance_id}")
            
            return {
                'instance_id': instance_id,
                'status_url': status_url,
                'data': data
            }
        else:
            print(f"\n❌ Error al iniciar: HTTP {response.status_code}")
            
            # Diagnóstico de respuesta del servidor:
            print(f"   Respuesta del servidor: {response.text[:500]}")
            
            # Nuevo: Mostrar Headers (puede revelar políticas de seguridad o CORS)
            print("\n   Headers de Respuesta:")
            for key, value in response.headers.items():
                 # Mostrar solo algunos headers relevantes para no saturar
                 if key.lower() in ['server', 'date', 'www-authenticate', 'content-type']:
                     print(f"   - {key}: {value}")
            
            # Opcional: imprimir el JSON de solicitud si el error fuera 400
            # print(f"   JSON Enviado: {book_input}")
            
            return None
            
    except requests.exceptions.Timeout:
        print("\n❌ Timeout al conectar con Azure Functions")
        return None
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error de conexión: {e}")
        return None


def check_status(status_url):
    """Consulta el estado de una orquestación."""
    try:
        response = requests.get(status_url, timeout=30)
        
        # 200 = terminado, 202 = aún procesando (ambos son OK)
        if response.status_code in [200, 202]:
            return response.json()
        else:
            return None
    except Exception as e:
        return None


def wait_for_completion(orchestration_info):
    """Espera a que la orquestación termine."""
    status_url = orchestration_info['status_url']
    instance_id = orchestration_info['instance_id']
    
    print(f"\n⏳ Monitoreando orquestación {instance_id[:8]}...")
    print(f"   URL de status: {status_url[:80]}...")
    print("-" * 50)
    
    start_time = time.time()
    max_wait_seconds = MAX_WAIT_MINUTES * 60
    terminal_states = ['Completed', 'Failed', 'Terminated', 'Canceled']
    
    last_status = ""
    
    while True:
        elapsed = time.time() - start_time
        
        if elapsed > max_wait_seconds:
            print(f"\n\n⚠️ Timeout alcanzado ({MAX_WAIT_MINUTES} minutos)")
            return None
        
        status = check_status(status_url)
        
        if status:
            runtime_status = status.get('runtimeStatus', 'Unknown')
            custom_status = status.get('customStatus', '')
            
            # Solo imprimir si cambió
            current = f"{runtime_status}|{custom_status}"
            if current != last_status:
                status_emoji = {
                    'Pending': '⏳',
                    'Running': '🔄',
                    'Completed': '✅',
                    'Failed': '❌',
                }.get(runtime_status, '❓')
                
                print(f"\n{status_emoji} [{format_duration(elapsed)}] {runtime_status}", end='')
                if custom_status:
                    print(f" - {custom_status}", end='')
                last_status = current
            else:
                print(".", end='', flush=True)
            
            if runtime_status in terminal_states:
                print()
                return status
        
        time.sleep(POLL_INTERVAL)


def print_results(final_status):
    """Imprime los resultados finales."""
    print("\n" + "=" * 60)
    print("  📊 RESULTADOS FINALES")
    print("=" * 60)
    
    runtime_status = final_status.get('runtimeStatus')
    
    if runtime_status == 'Completed':
        output = final_status.get('output', {})
        
        if isinstance(output, dict):
            print(f"\n✅ Estado: {output.get('status', 'unknown')}")
            print(f"📖 Capítulos procesados: {output.get('chapters_processed', 'N/A')}")
            
            tiempos = output.get('tiempos', {})
            if tiempos:
                print(f"\n⏱️ Tiempos:")
                for fase, tiempo in tiempos.items():
                    print(f"   - {fase}: {tiempo}")
            
            # Errores si los hay
            errors = output.get('errors', {})
            if errors.get('analysis_failures') or errors.get('edit_failures'):
                print(f"\n⚠️ Hubo algunos errores:")
                for err in errors.get('analysis_failures', [])[:3]:
                    print(f"   - Análisis: {err.get('chapter_id')} - {err.get('error', 'N/A')[:50]}")
                for err in errors.get('edit_failures', [])[:3]:
                    print(f"   - Edición: {err.get('chapter_id')} - {err.get('error', 'N/A')[:50]}")
        else:
            print(f"\nOutput: {str(output)[:500]}")
            
    elif runtime_status == 'Failed':
        print(f"\n❌ La orquestación falló")
        output = final_status.get('output', {})
        if isinstance(output, dict):
            print(f"   Error: {output.get('message', 'Sin detalles')}")
            print(f"   Fase: {output.get('phase', 'N/A')}")
        else:
            print(f"   Output: {output}")
    else:
        print(f"\n⚠️ Estado: {runtime_status}")
    
    print("\n" + "=" * 60)


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Test runner para Sylphrena MVP')
    parser.add_argument('--no-wait', '-n', action='store_true', help='No esperar resultado')
    parser.add_argument('--input', '-i', default='test_book.txt', help='Input para el libro')
    args = parser.parse_args()
    
    print_header()
    
    # Iniciar orquestación
    result = start_orchestration(args.input)
    
    if not result:
        print("\n💀 No se pudo iniciar la orquestación")
        sys.exit(1)
    
    if args.no_wait:
        print(f"\n💡 Orquestación iniciada. Consulta el status en Azure Portal.")
        print(f"   Instance ID: {result['instance_id']}")
        return
    
    # Esperar
    final_status = wait_for_completion(result)
    
    if final_status:
        print_results(final_status)
    
    print("\n🏁 Prueba finalizada.\n")


if __name__ == "__main__":
    main()
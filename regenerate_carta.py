"""
Script para regenerar SOLO la Carta Editorial sin reprocesar todo.
Usa la biblia y datos existentes del blob storage.

Uso:
    python regenerate_carta.py <job_id>

Ejemplo:
    python regenerate_carta.py 2110_20251210_223051
"""

import requests
import sys
import json

def regenerate_carta_editorial(job_id, base_url="http://localhost:7071"):
    """
    Llama al endpoint de regeneración de carta editorial.
    """
    url = f"{base_url}/api/project/{job_id}/editorial-letter/regenerate"

    print(f"Regenerando Carta Editorial para job: {job_id}")
    print(f"URL: {url}")
    print()

    try:
        # Nota: En producción necesitarás el token de autenticación
        # headers = {"Authorization": f"Bearer {token}"}

        response = requests.post(url, timeout=300)  # 5 minutos timeout

        if response.status_code == 200:
            result = response.json()
            print("[OK] Carta Editorial regenerada exitosamente!")
            print()
            print(f"Job ID: {result.get('job_id')}")
            print(f"Secciones generadas: {', '.join(result.get('sections', []))}")
            print(f"Markdown generado: {'Si' if result.get('has_markdown') else 'No'}")
            print()
            print("Archivos guardados en blob storage:")
            print(f"  - {job_id}/carta_editorial.json")
            print(f"  - {job_id}/carta_editorial.md")
            print()
            print("Ahora puedes descargarlos o verlos en el frontend.")
            return True
        else:
            print(f"[ERROR] Error al regenerar carta editorial")
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("[ERROR] No se pudo conectar al servidor.")
        print("Asegurate de que Azure Functions esta corriendo:")
        print("  func start")
        return False
    except requests.exceptions.Timeout:
        print("[TIMEOUT] La generacion esta tomando mas de 5 minutos.")
        print("Revisa los logs del servidor para ver el progreso.")
        return False
    except Exception as e:
        print(f"[ERROR] Error inesperado: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("[ERROR] Debes proporcionar el job_id")
        print()
        print("Uso:")
        print("  python regenerate_carta.py <job_id>")
        print()
        print("Ejemplo:")
        print("  python regenerate_carta.py 2110_20251210_223051")
        sys.exit(1)

    job_id = sys.argv[1]

    # Opcionalmente puedes especificar una URL diferente
    base_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:7071"

    success = regenerate_carta_editorial(job_id, base_url)
    sys.exit(0 if success else 1)

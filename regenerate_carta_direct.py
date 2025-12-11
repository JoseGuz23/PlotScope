"""
Script directo para regenerar Carta Editorial sin HTTP
Usa directamente el módulo GenerateEditorialLetter
"""

import sys
import json
import os

# Cargar variables de entorno desde local.settings.json
def load_local_settings():
    """Carga variables de entorno desde local.settings.json"""
    try:
        with open('local.settings.json', 'r') as f:
            settings = json.load(f)
            for key, value in settings.get('Values', {}).items():
                os.environ[key] = value
        print("[OK] Variables de entorno cargadas desde local.settings.json\n")
    except FileNotFoundError:
        print("[WARNING] local.settings.json no encontrado\n")
    except Exception as e:
        print(f"[WARNING] Error cargando local.settings.json: {e}\n")

# Cargar settings al inicio
load_local_settings()

# Agregar rutas necesarias
sys.path.insert(0, 'API_DURABLE')

from azure.storage.blob import BlobServiceClient

def main(job_id):
    print(f"=== Regenerando Carta Editorial para job: {job_id} ===\n")

    try:
        # 1. Leer archivos desde carpeta local outputs/
        outputs_dir = "outputs"

        if not os.path.exists(outputs_dir):
            print(f"[ERROR] Carpeta {outputs_dir}/ no encontrada")
            print("Descarga los archivos del blob storage primero")
            return False

        print("[1/5] Cargando biblia...")
        bible_path = os.path.join(outputs_dir, "biblia_validada.json")
        if not os.path.exists(bible_path):
            print(f"[ERROR] No se encontró {bible_path}")
            return False

        with open(bible_path, 'r', encoding='utf-8') as f:
            bible = json.load(f)
        print(f"  [OK] Biblia cargada")

        print("[2/5] Cargando capitulos consolidados...")
        chapters_path = os.path.join(outputs_dir, "capitulos_consolidados.json")
        if not os.path.exists(chapters_path):
            print(f"[ERROR] No se encontró {chapters_path}")
            return False

        with open(chapters_path, 'r', encoding='utf-8') as f:
            consolidated_chapters = json.load(f)
        print(f"  [OK] {len(consolidated_chapters)} capitulos cargados")

        print("[3/5] Cargando metadata...")
        metadata_path = os.path.join(outputs_dir, "metadata.json")
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            book_name = metadata.get('book_name', metadata.get('project_name', 'Sin titulo'))
            print(f"  [OK] Libro: {book_name}")
        except FileNotFoundError:
            book_name = "Sin titulo"
            print(f"  [WARNING] Metadata no encontrada, usando nombre por defecto")

        # 2. Importar y ejecutar GenerateEditorialLetter
        print("[4/5] Generando carta editorial...")
        print(f"  Llamando a Gemini API (esto puede tomar 1-2 minutos)...")

        from GenerateEditorialLetter import main as generate_editorial_letter

        carta_input = {
            'bible': bible,
            'consolidated_chapters': consolidated_chapters,
            'fragments': [],
            'book_metadata': {
                'title': book_name,
                'job_id': job_id
            }
        }

        carta_result = generate_editorial_letter(carta_input)

        if carta_result.get('status') == 'error':
            print(f"  [ERROR] {carta_result.get('error')}")
            return False

        carta_editorial = carta_result.get('carta_editorial', {})
        carta_markdown = carta_result.get('carta_markdown', '')

        if not carta_editorial:
            print("  [ERROR] carta_editorial esta vacia")
            return False

        print("  [OK] Carta generada exitosamente")

        # 3. Guardar resultados en carpeta local
        print("[5/5] Guardando archivos...")

        # Guardar JSON
        carta_json_path = os.path.join(outputs_dir, "carta_editorial.json")
        with open(carta_json_path, 'w', encoding='utf-8') as f:
            json.dump(carta_editorial, f, ensure_ascii=False, indent=2)
        print(f"  [OK] carta_editorial.json guardado")

        # Guardar Markdown
        if carta_markdown:
            carta_md_path = os.path.join(outputs_dir, "carta_editorial.md")
            with open(carta_md_path, 'w', encoding='utf-8') as f:
                f.write(carta_markdown)
            print(f"  [OK] carta_editorial.md guardado")

        # Actualizar metadata
        try:
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                meta['status'] = 'completed'
                from datetime import datetime
                meta['carta_regenerated_at'] = datetime.utcnow().isoformat() + 'Z'
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(meta, f, ensure_ascii=False, indent=2)
                print(f"  [OK] Metadata actualizada a 'completed'")
        except Exception as e:
            print(f"  [WARNING] No se pudo actualizar metadata: {e}")

        print("\n=== COMPLETADO ===")
        print(f"\nArchivos guardados en outputs/:")
        print(f"  - carta_editorial.json")
        print(f"  - carta_editorial.md")
        print(f"\nSecciones generadas: {list(carta_editorial.keys())[:5]}")
        print(f"\nAhora debes subir estos archivos al blob storage para verlos en el frontend.")

        return True

    except FileNotFoundError as e:
        print(f"\n[ERROR] Archivo no encontrado: {e}")
        print("Verifica que el job_id sea correcto")
        return False
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("[ERROR] Debes proporcionar el job_id")
        print("\nUso:")
        print("  python regenerate_carta_direct.py <job_id>")
        print("\nEjemplo:")
        print("  python regenerate_carta_direct.py 2110_20251210_223051")
        sys.exit(1)

    job_id = sys.argv[1]
    success = main(job_id)
    sys.exit(0 if success else 1)

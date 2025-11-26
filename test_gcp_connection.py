#!/usr/bin/env python3
"""
test_gcp_connection.py - Verifica que GCP esté bien configurado
"""

import os
import json

def main():
    print("\n" + "=" * 60)
    print("  🔧 TEST DE CONEXIÓN A GCP")
    print("=" * 60 + "\n")
    
    errors = []
    
    # ─────────────────────────────────────────────────────────────
    # 1. VERIFICAR VARIABLES DE ENTORNO
    # ─────────────────────────────────────────────────────────────
    print("1️⃣ Verificando variables de entorno...\n")
    
    # Intentar cargar de local.settings.json
    local_settings_path = 'local.settings.json'
    settings = {}
    
    if os.path.exists(local_settings_path):
        with open(local_settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f).get('Values', {})
        print(f"   ✅ local.settings.json encontrado")
    else:
        print(f"   ⚠️ local.settings.json no encontrado, usando variables de entorno")
    
    # Variables requeridas
    project_id = settings.get('GCP_PROJECT_ID') or os.environ.get('GCP_PROJECT_ID')
    bucket_name = settings.get('GCP_BUCKET_NAME') or os.environ.get('GCP_BUCKET_NAME')
    
    # Credenciales: puede ser archivo O json inline
    creds_file = settings.get('GOOGLE_APPLICATION_CREDENTIALS') or os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    creds_json = settings.get('GOOGLE_APPLICATION_CREDENTIALS_JSON') or os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_JSON')
    
    if project_id:
        print(f"   ✅ GCP_PROJECT_ID: {project_id}")
    else:
        print(f"   ❌ GCP_PROJECT_ID: NO CONFIGURADA")
        errors.append("Falta GCP_PROJECT_ID")
    
    if bucket_name:
        print(f"   ✅ GCP_BUCKET_NAME: {bucket_name}")
    else:
        print(f"   ❌ GCP_BUCKET_NAME: NO CONFIGURADA")
        errors.append("Falta GCP_BUCKET_NAME")
    
    # Credenciales
    creds_source = None
    if creds_file and os.path.exists(creds_file):
        print(f"   ✅ GOOGLE_APPLICATION_CREDENTIALS: {creds_file}")
        creds_source = "file"
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_file
    elif creds_json:
        if isinstance(creds_json, dict):
            print(f"   ⚠️ GOOGLE_APPLICATION_CREDENTIALS_JSON: Es un dict, convirtiéndolo a string...")
            creds_json = json.dumps(creds_json)
        print(f"   ✅ GOOGLE_APPLICATION_CREDENTIALS_JSON: ({len(creds_json)} caracteres)")
        creds_source = "json"
    else:
        print(f"   ❌ Credenciales GCP: NO CONFIGURADAS")
        print(f"      Opción 1: GOOGLE_APPLICATION_CREDENTIALS = ruta/al/archivo.json")
        print(f"      Opción 2: GOOGLE_APPLICATION_CREDENTIALS_JSON = '{{...}}'")
        errors.append("Faltan credenciales GCP")
    
    required_vars = {
        'GCP_PROJECT_ID': project_id,
        'GCP_BUCKET_NAME': bucket_name,
    }
    
    if errors:
        print(f"\n❌ Faltan variables. Agrégalas a local.settings.json:")
        print("""
{
  "Values": {
    "GCP_PROJECT_ID": "tu-proyecto-id",
    "GCP_BUCKET_NAME": "tu-bucket-name",
    "GOOGLE_APPLICATION_CREDENTIALS_JSON": "{\\"type\\": \\"service_account\\", ...}"
  }
}
        """)
        return False
    
    # ─────────────────────────────────────────────────────────────
    # 2. VERIFICAR CREDENCIALES JSON
    # ─────────────────────────────────────────────────────────────
    print("\n2️⃣ Verificando credenciales JSON...\n")
    
    if creds_source == "file":
        # Ya configurado via archivo
        try:
            with open(creds_file, 'r') as f:
                creds = json.load(f)
            print(f"   ✅ Archivo JSON válido")
            print(f"   ✅ Tipo: {creds.get('type', 'N/A')}")
            print(f"   ✅ Project: {creds.get('project_id', 'N/A')}")
            print(f"   ✅ Client email: {creds.get('client_email', 'N/A')[:50]}...")
        except Exception as e:
            print(f"   ❌ Error leyendo archivo: {e}")
            errors.append("Archivo de credenciales inválido")
            return False
            
    elif creds_source == "json":
        try:
            if isinstance(creds_json, str):
                creds = json.loads(creds_json)
            else:
                creds = creds_json
                
            print(f"   ✅ JSON válido")
            print(f"   ✅ Tipo: {creds.get('type', 'N/A')}")
            print(f"   ✅ Project: {creds.get('project_id', 'N/A')}")
            print(f"   ✅ Client email: {creds.get('client_email', 'N/A')[:50]}...")
            
            # Guardar temporalmente para las pruebas
            creds_path = 'temp_gcp_creds.json'
            with open(creds_path, 'w') as f:
                json.dump(creds, f)
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
            
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON inválido: {e}")
            errors.append("JSON de credenciales inválido")
            return False
    else:
        print(f"   ❌ No hay credenciales configuradas")
        return False
    
    # ─────────────────────────────────────────────────────────────
    # 3. PROBAR CONEXIÓN A CLOUD STORAGE
    # ─────────────────────────────────────────────────────────────
    print("\n3️⃣ Probando conexión a Cloud Storage...\n")
    
    try:
        from google.cloud import storage
        
        client = storage.Client(project=project_id)
        bucket = client.bucket(bucket_name)
        
        # Verificar que el bucket existe
        if bucket.exists():
            print(f"   ✅ Bucket '{bucket_name}' existe y es accesible")
        else:
            print(f"   ❌ Bucket '{bucket_name}' NO existe")
            print(f"      Créalo en: https://console.cloud.google.com/storage/browser")
            errors.append("Bucket no existe")
            
    except ImportError:
        print(f"   ❌ google-cloud-storage no instalado")
        print(f"      Ejecuta: pip install google-cloud-storage")
        errors.append("Librería no instalada")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        errors.append(str(e))
    
    # ─────────────────────────────────────────────────────────────
    # 4. PROBAR CONEXIÓN A VERTEX AI
    # ─────────────────────────────────────────────────────────────
    print("\n4️⃣ Probando conexión a Vertex AI...\n")
    
    try:
        from google.cloud import aiplatform
        
        aiplatform.init(project=project_id, location="us-central1")
        print(f"   ✅ Vertex AI inicializado")
        print(f"   ✅ Project: {project_id}")
        print(f"   ✅ Location: us-central1")
        
    except ImportError:
        print(f"   ❌ google-cloud-aiplatform no instalado")
        print(f"      Ejecuta: pip install google-cloud-aiplatform")
        errors.append("Librería no instalada")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        errors.append(str(e))
    
    # ─────────────────────────────────────────────────────────────
    # 5. RESUMEN
    # ─────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    
    # Limpiar archivo temporal
    if os.path.exists('temp_gcp_creds.json'):
        os.remove('temp_gcp_creds.json')
    
    if errors:
        print("  ❌ HAY ERRORES - CORRIGE ANTES DE CONTINUAR")
        print("=" * 60)
        for err in errors:
            print(f"  • {err}")
        return False
    else:
        print("  ✅ TODO LISTO - PUEDES CORRER BATCH API")
        print("=" * 60)
        print("\n  Siguiente paso:")
        print("  1. Asegúrate que USE_BATCH_API = True en Orchestrator")
        print("  2. Despliega: func azure functionapp publish sylphrena-orchestrator")
        print("  3. Corre: python test_mvp_v2.py")
        return True


if __name__ == "__main__":
    main()

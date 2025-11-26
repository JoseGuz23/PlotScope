"""
Prueba SOLO la extracción de resultados de un batch que ya completó.
"""

import os
import json
import logging

logging.basicConfig(level=logging.INFO)

# Cargar config local
if os.path.exists('local.settings.json'):
    with open('local.settings.json') as f:
        config = json.load(f)
        for key, value in config.get("Values", {}).items():
            os.environ[key] = value

# Importar la función
from PollBatchResult import main

# El nombre del batch que ya completó (cámbialo por el tuyo)
# Lo puedes ver en los logs: "📦 Batch Job creado: batches/xxxxx"
BATCH_JOB_NAME = "batches/TU_BATCH_ID_AQUI"  # ← CAMBIA ESTO

# IDs de prueba (101 capítulos)
id_map = [str(i) for i in range(1, 102)]

result = main({
    "batch_job_name": BATCH_JOB_NAME,
    "id_map": id_map
})

print("\n" + "=" * 50)
print("RESULTADO:")
print("=" * 50)

if isinstance(result, list):
    print(f"✅ Extraídos {len(result)} análisis")
    if result:
        print(f"\nPrimer análisis:")
        print(json.dumps(result[0], indent=2, ensure_ascii=False)[:500])
else:
    print(f"❌ Error o sin resultados:")
    print(json.dumps(result, indent=2))
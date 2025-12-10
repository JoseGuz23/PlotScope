"""
HttpStart/__init__.py - LYA
CORREGIDO: Usa el job_id como instance_id para que el status funcione.
CORREGIDO V2: Siempre envía dict completo al orquestrador (no solo blob_path).
"""

import logging
import json
import azure.functions as func
import azure.durable_functions as df

async def main(req: func.HttpRequest, starter: str) -> func.HttpResponse:
    client = df.DurableOrchestrationClient(starter)
    
    try:
        body = req.get_json()
        
        # Determinar input y ID
        if isinstance(body, dict):
            job_id = body.get('job_id')
            blob_path = body.get('blob_path')
            book_name = body.get('book_name', 'Sin título')
            
            # CRÍTICO: Si tenemos job_id, lo usamos como instance_id
            instance_id_to_use = job_id 
            
            # SIEMPRE enviar dict completo (no solo blob_path string)
            orchestrator_input = {
                'job_id': job_id,
                'blob_path': blob_path,
                'book_name': book_name
            }
            
            logging.info(f"🚀 Iniciando orquestador para: {blob_path} (ID: {instance_id_to_use})")
        else:
            # Legacy
            orchestrator_input = body
            instance_id_to_use = None # Dejar que genere uno random
            logging.info(f"🚀 Iniciando orquestador legacy: {body}")
            
    except ValueError:
        orchestrator_input = {"job_id": "test", "blob_path": "test_book.txt", "book_name": "Test"}
        instance_id_to_use = None
        logging.info("🚀 Iniciando test default")
    
    # Iniciar orquestación forzando el ID si existe
    instance_id = await client.start_new("Orchestrator", instance_id_to_use, orchestrator_input)
    
    logging.info(f"✅ Orquestación iniciada con ID = '{instance_id}'")
    
    return client.create_check_status_response(req, instance_id)
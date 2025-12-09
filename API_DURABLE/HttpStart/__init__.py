"""
HttpStart/__init__.py - LYA
Inicia el orquestador con input dinámico desde el request
"""

import logging
import json
import azure.functions as func
import azure.durable_functions as df

async def main(req: func.HttpRequest, starter: str) -> func.HttpResponse:
    """
    Inicia el orquestador Sylphrena.
    
    Acepta:
    - POST con JSON body: { "job_id": "...", "blob_path": "..." }
    - POST con string: "nombre_archivo.docx" (legacy)
    """
    client = df.DurableOrchestrationClient(starter)
    
    try:
        # Intentar obtener JSON body
        body = req.get_json()
        
        if isinstance(body, dict):
            # Nuevo formato: { job_id, blob_path }
            job_id = body.get('job_id')
            blob_path = body.get('blob_path')
            
            if blob_path:
                orchestrator_input = blob_path
                logging.info(f"🚀 Iniciando orquestador para: {blob_path}")
            else:
                orchestrator_input = body
                logging.info(f"🚀 Iniciando orquestador con input dict")
        else:
            # Legacy: string directo
            orchestrator_input = body
            logging.info(f"🚀 Iniciando orquestador con input string: {body}")
            
    except ValueError:
        # No hay body JSON, usar default para testing
        orchestrator_input = "test_book.txt"
        logging.info(f"🚀 Iniciando orquestador con default: {orchestrator_input}")
    
    # Iniciar orquestación
    instance_id = await client.start_new("Orchestrator", None, orchestrator_input)
    
    logging.info(f"✅ Orquestación iniciada con ID = '{instance_id}'")
    
    # Devolver response con URLs de status
    return client.create_check_status_response(req, instance_id)
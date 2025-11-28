import logging
import os  # <-- Importar la librería os
import azure.functions as func
import azure.durable_functions as df

async def main(req: func.HttpRequest, starter: str) -> func.HttpResponse:
    client = df.DurableOrchestrationClient(starter)
    
    # Construcción de la ruta: .. luego LIBROS, luego el nombre del archivo.
    book_path = os.path.join("..", "LIBROS", "Piel_Morena.docx")
    
    instance_id = await client.start_new("Orchestrator", None, book_path)
    
    logging.info(f"Started orchestration with ID = '{instance_id}'.")
    
    return client.create_check_status_response(req, instance_id)
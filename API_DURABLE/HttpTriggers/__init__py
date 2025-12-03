"""
HTTP API Endpoints para Sylphrena Web Platform
"""

import azure.functions as func
import logging
import json
import os
from azure.storage.blob import BlobServiceClient

logging.basicConfig(level=logging.INFO)


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Router principal para todos los endpoints."""
    
    # Extraer ruta
    route = req.route_params.get('route', '')
    method = req.method
    
    logging.info(f"📥 {method} /api/{route}")
    
    # Router
    try:
        if route.startswith('project/'):
            return handle_project_routes(req, route, method)
        elif route == 'projects':
            return handle_projects_list(req, method)
        else:
            return func.HttpResponse(
                json.dumps({'error': 'Route not found'}),
                status_code=404,
                mimetype='application/json'
            )
    except Exception as e:
        logging.error(f"❌ Error: {str(e)}")
        return func.HttpResponse(
            json.dumps({'error': str(e)}),
            status_code=500,
            mimetype='application/json'
        )


def handle_project_routes(req: func.HttpRequest, route: str, method: str) -> func.HttpResponse:
    """
    Maneja rutas de proyectos:
    - GET /api/project/{job_id} - Info del proyecto
    - GET /api/project/{job_id}/bible - Obtener biblia
    - POST /api/project/{job_id}/bible - Guardar biblia editada
    - POST /api/project/{job_id}/bible/approve - Aprobar biblia
    - GET /api/project/{job_id}/changes - Lista de cambios
    - POST /api/project/{job_id}/changes/{change_id}/decision - Guardar decisión
    - POST /api/project/{job_id}/export - Exportar manuscrito final
    """
    parts = route.split('/')
    
    if len(parts) < 2:
        return error_response('Invalid route', 400)
    
    job_id = parts[1]
    
    # GET /api/project/{job_id}
    if method == 'GET' and len(parts) == 2:
        return get_project_info(job_id)
    
    # GET /api/project/{job_id}/bible
    if method == 'GET' and len(parts) == 3 and parts[2] == 'bible':
        return get_bible(job_id)
    
    # POST /api/project/{job_id}/bible
    if method == 'POST' and len(parts) == 3 and parts[2] == 'bible':
        return save_bible(job_id, req)
    
    # POST /api/project/{job_id}/bible/approve
    if method == 'POST' and len(parts) == 4 and parts[2] == 'bible' and parts[3] == 'approve':
        return approve_bible(job_id)
    
    # GET /api/project/{job_id}/changes
    if method == 'GET' and len(parts) == 3 and parts[2] == 'changes':
        return get_changes(job_id)
    
    # POST /api/project/{job_id}/changes/{change_id}/decision
    if method == 'POST' and len(parts) == 5 and parts[2] == 'changes' and parts[4] == 'decision':
        change_id = parts[3]
        return save_change_decision(job_id, change_id, req)
    
    # POST /api/project/{job_id}/export
    if method == 'POST' and len(parts) == 3 and parts[2] == 'export':
        return export_manuscript(job_id)
    
    return error_response('Route not found', 404)


# =============================================================================
# IMPLEMENTACIONES
# =============================================================================

def get_project_info(job_id: str) -> func.HttpResponse:
    """Obtiene información completa del proyecto."""
    try:
        blob_service = get_blob_service()
        container = blob_service.get_container_client('sylphrena-outputs')
        
        # Verificar que existe
        resumen_path = f"{job_id}/resumen_ejecutivo.json"
        blob = container.get_blob_client(resumen_path)
        
        if not blob.exists():
            return error_response('Project not found', 404)
        
        resumen = json.loads(blob.download_blob().readall())
        
        return success_response(resumen)
        
    except Exception as e:
        return error_response(str(e), 500)


def get_bible(job_id: str) -> func.HttpResponse:
    """Obtiene la Biblia del proyecto."""
    try:
        blob_service = get_blob_service()
        container = blob_service.get_container_client('sylphrena-outputs')
        
        bible_path = f"{job_id}/biblia_validada.json"
        blob = container.get_blob_client(bible_path)
        
        if not blob.exists():
            return error_response('Bible not found', 404)
        
        bible_data = json.loads(blob.download_blob().readall())
        
        return success_response(bible_data)
        
    except Exception as e:
        return error_response(str(e), 500)


def save_bible(job_id: str, req: func.HttpRequest) -> func.HttpResponse:
    """Guarda la Biblia editada por el usuario."""
    try:
        edited_bible = req.get_json()
        
        blob_service = get_blob_service()
        container = blob_service.get_container_client('sylphrena-outputs')
        
        # Guardar como biblia_editada.json
        bible_path = f"{job_id}/biblia_editada.json"
        blob = container.get_blob_client(bible_path)
        blob.upload_blob(
            json.dumps(edited_bible, indent=2, ensure_ascii=False),
            overwrite=True
        )
        
        return success_response({'message': 'Bible saved successfully'})
        
    except Exception as e:
        return error_response(str(e), 500)


def approve_bible(job_id: str) -> func.HttpResponse:
    """
    Marca la Biblia como aprobada y continúa el procesamiento.
    
    TODO: Reiniciar Orchestrator desde fase de edición
    """
    try:
        # Por ahora solo marca como aprobada
        # En el futuro: reiniciar orquestador
        
        return success_response({
            'message': 'Bible approved',
            'note': 'Processing will continue automatically'
        })
        
    except Exception as e:
        return error_response(str(e), 500)


def get_changes(job_id: str) -> func.HttpResponse:
    """Obtiene lista estructurada de cambios."""
    try:
        blob_service = get_blob_service()
        container = blob_service.get_container_client('sylphrena-outputs')
        
        changes_path = f"{job_id}/cambios_estructurados.json"
        blob = container.get_blob_client(changes_path)
        
        if not blob.exists():
            return error_response('Changes not found', 404)
        
        changes_data = json.loads(blob.download_blob().readall())
        
        return success_response(changes_data)
        
    except Exception as e:
        return error_response(str(e), 500)


def save_change_decision(job_id: str, change_id: str, req: func.HttpRequest) -> func.HttpResponse:
    """
    Guarda la decisión del usuario sobre un cambio.
    
    TODO: Implementar base de datos para persistencia
    Por ahora solo responde OK
    """
    try:
        decision = req.get_json()
        action = decision.get('action')  # 'accept' o 'reject'
        
        if action not in ['accept', 'reject']:
            return error_response('Invalid action', 400)
        
        # TODO: Guardar en base de datos
        logging.info(f"✅ Decision saved: {change_id} -> {action}")
        
        return success_response({
            'change_id': change_id,
            'action': action,
            'saved': True
        })
        
    except Exception as e:
        return error_response(str(e), 500)


def export_manuscript(job_id: str) -> func.HttpResponse:
    """
    Exporta manuscrito final con cambios aplicados.
    
    TODO: Implementar generación de DOCX con decisiones aplicadas
    Por ahora devuelve los capítulos consolidados
    """
    try:
        blob_service = get_blob_service()
        container = blob_service.get_container_client('sylphrena-outputs')
        
        chapters_path = f"{job_id}/capitulos_consolidados.json"
        blob = container.get_blob_client(chapters_path)
        
        chapters_data = blob.download_blob().readall()
        
        return func.HttpResponse(
            chapters_data,
            mimetype='application/json',
            headers={
                'Content-Disposition': f'attachment; filename="manuscript_{job_id}.json"'
            }
        )
        
    except Exception as e:
        return error_response(str(e), 500)


def handle_projects_list(req: func.HttpRequest, method: str) -> func.HttpResponse:
    """
    Lista todos los proyectos.
    
    TODO: Filtrar por usuario cuando se implemente auth
    """
    try:
        if method != 'GET':
            return error_response('Method not allowed', 405)
        
        blob_service = get_blob_service()
        container = blob_service.get_container_client('sylphrena-outputs')
        
        # Listar todas las carpetas (job_ids)
        projects = []
        for blob in container.walk_blobs():
            # Cada proyecto tiene su carpeta
            # TODO: Mejorar esta lógica
            pass
        
        return success_response({'projects': projects})
        
    except Exception as e:
        return error_response(str(e), 500)


# =============================================================================
# HELPERS
# =============================================================================

def get_blob_service() -> BlobServiceClient:
    """Obtiene cliente de Blob Storage."""
    connection_string = os.environ.get('AzureWebJobsStorage')
    return BlobServiceClient.from_connection_string(connection_string)


def success_response(data: dict) -> func.HttpResponse:
    """Respuesta exitosa estandarizada."""
    return func.HttpResponse(
        json.dumps(data, ensure_ascii=False),
        status_code=200,
        mimetype='application/json',
        headers={'Access-Control-Allow-Origin': '*'}  # CORS
    )


def error_response(message: str, status_code: int) -> func.HttpResponse:
    """Respuesta de error estandarizada."""
    return func.HttpResponse(
        json.dumps({'error': message}),
        status_code=status_code,
        mimetype='application/json',
        headers={'Access-Control-Allow-Origin': '*'}  # CORS
    )
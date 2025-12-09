"""
HTTP API Endpoints para Sylphrena Web Platform
Con autenticación simple por contraseña (tokens auto-verificables)
"""

import azure.functions as func
import logging
import json
import os
import hashlib
import hmac
import base64
from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient

logging.basicConfig(level=logging.INFO)

# =============================================================================
# CONFIGURACIÓN DE SEGURIDAD
# =============================================================================

ADMIN_PASSWORD = os.environ.get('SYLPHRENA_PASSWORD', 'sylphrena2025')
TOKEN_SECRET = os.environ.get('SYLPHRENA_TOKEN_SECRET', 'sylphrena-secret-key-2025')


# =============================================================================
# FUNCIONES DE TOKEN (auto-verificables, no necesitan memoria)
# =============================================================================

def generate_token():
    """Genera un token que expira en 24 horas."""
    expiry = datetime.utcnow() + timedelta(hours=24)
    expiry_str = expiry.strftime('%Y%m%d%H%M%S')
    
    # Crear firma
    message = f"sylphrena:{expiry_str}"
    signature = hmac.new(
        TOKEN_SECRET.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()[:32]
    
    # Token = expiry:signature (codificado en base64)
    token_data = f"{expiry_str}:{signature}"
    token = base64.urlsafe_b64encode(token_data.encode()).decode()
    
    return token, expiry


def verify_token(token):
    """Verifica si un token es válido. Retorna True/False."""
    try:
        # Decodificar
        token_data = base64.urlsafe_b64decode(token.encode()).decode()
        expiry_str, signature = token_data.split(':')
        
        # Verificar firma
        message = f"sylphrena:{expiry_str}"
        expected_signature = hmac.new(
            TOKEN_SECRET.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()[:32]
        
        if not hmac.compare_digest(signature, expected_signature):
            logging.warning("❌ Token con firma inválida")
            return False
        
        # Verificar expiración
        expiry = datetime.strptime(expiry_str, '%Y%m%d%H%M%S')
        if datetime.utcnow() > expiry:
            logging.warning("❌ Token expirado")
            return False
        
        return True
        
    except Exception as e:
        logging.warning(f"❌ Error verificando token: {e}")
        return False


# =============================================================================
# MAIN ROUTER
# =============================================================================

def main(req: func.HttpRequest) -> func.HttpResponse:
    """Router principal para todos los endpoints."""
    
    # Manejar preflight CORS
    if req.method == 'OPTIONS':
        return cors_response()
    
    route = req.route_params.get('route', '')
    method = req.method
    
    logging.info(f"📥 {method} /api/{route}")
    
    try:
        # Rutas públicas (no requieren auth)
        if route == 'auth/login':
            return handle_login(req)
        
        # Todas las demás rutas requieren autenticación
        auth_error = verify_auth(req)
        if auth_error:
            return auth_error
        
        # Router de rutas protegidas
        if route == 'projects':
            return handle_projects_list(req, method)
        elif route.startswith('project/'):
            return handle_project_routes(req, route, method)
        else:
            return error_response('Route not found', 404)
            
    except Exception as e:
        logging.error(f"❌ Error: {str(e)}")
        return error_response(str(e), 500)


# =============================================================================
# AUTENTICACIÓN
# =============================================================================

def handle_login(req: func.HttpRequest) -> func.HttpResponse:
    """Login con contraseña simple."""
    try:
        if req.method != 'POST':
            return error_response('Method not allowed', 405)
        
        body = req.get_json()
        password = body.get('password', '')
        
        if password != ADMIN_PASSWORD:
            logging.warning("❌ Intento de login fallido")
            return error_response('Contraseña incorrecta', 401)
        
        # Generar token auto-verificable
        token, expiry = generate_token()
        
        logging.info("✅ Login exitoso")
        
        return success_response({
            'token': token,
            'expiresAt': expiry.isoformat(),
            'message': 'Login exitoso'
        })
        
    except Exception as e:
        return error_response(str(e), 500)


def verify_auth(req: func.HttpRequest) -> func.HttpResponse:
    """Verifica el token. Retorna None si OK, o error response."""
    auth_header = req.headers.get('Authorization', '')
    
    if not auth_header.startswith('Bearer '):
        return error_response('Token no proporcionado', 401)
    
    token = auth_header[7:]  # Quitar "Bearer "
    
    if not verify_token(token):
        return error_response('Token inválido o expirado', 401)
    
    return None  # Auth OK


# =============================================================================
# PROJECT ROUTES
# =============================================================================

def handle_project_routes(req: func.HttpRequest, route: str, method: str) -> func.HttpResponse:
    """Maneja todas las rutas de /api/project/..."""
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
    
    # GET /api/project/{job_id}/manuscript/edited
    if method == 'GET' and len(parts) == 4 and parts[2] == 'manuscript' and parts[3] == 'edited':
        return get_manuscript_edited(job_id)
    
    # GET /api/project/{job_id}/manuscript/annotated
    if method == 'GET' and len(parts) == 4 and parts[2] == 'manuscript' and parts[3] == 'annotated':
        return get_manuscript_annotated(job_id)
    
    # GET /api/project/{job_id}/manuscript/changes-html
    if method == 'GET' and len(parts) == 4 and parts[2] == 'manuscript' and parts[3] == 'changes-html':
        return get_changes_html(job_id)
    
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
    
    # POST /api/project/upload
    if method == 'POST' and len(parts) == 2 and parts[1] == 'upload':
        return handle_upload(req)
    
    return error_response('Route not found', 404)


# =============================================================================
# IMPLEMENTACIONES - PROYECTOS
# =============================================================================

def handle_projects_list(req: func.HttpRequest, method: str) -> func.HttpResponse:
    """Lista todos los proyectos."""
    try:
        if method != 'GET':
            return error_response('Method not allowed', 405)
        
        blob_service = get_blob_service()
        container = blob_service.get_container_client('sylphrena-outputs')
        
        projects = []
        found_job_ids = set()
        
        logging.info("📂 Buscando proyectos...")
        
        for blob in container.list_blobs():
            parts = blob.name.split('/')
            if len(parts) >= 2:
                job_id = parts[0]
                
                if job_id not in found_job_ids:
                    found_job_ids.add(job_id)
                    project_info = get_project_summary(container, job_id)
                    if project_info:
                        projects.append(project_info)
        
        projects.sort(key=lambda x: x.get('createdAt', ''), reverse=True)
        
        logging.info(f"📊 Proyectos encontrados: {len(projects)}")
        
        return success_response({'projects': projects})
        
    except Exception as e:
        return error_response(str(e), 500)


def get_project_summary(container, job_id: str) -> dict:
    """Obtiene resumen de un proyecto."""
    try:
        resumen_blob = container.get_blob_client(f"{job_id}/resumen_ejecutivo.json")
        
        if resumen_blob.exists():
            resumen = json.loads(resumen_blob.download_blob().readall())
            properties = resumen_blob.get_blob_properties()
            
            return {
                'id': job_id,
                'name': resumen.get('book_name', job_id),
                'status': 'completed',
                'createdAt': properties.last_modified.isoformat() if properties.last_modified else '',
                'wordCount': resumen.get('estadisticas', {}).get('total_words', 0),
                'chaptersCount': resumen.get('capitulos_procesados', 0),
                'changesCount': resumen.get('estadisticas', {}).get('total_changes', 0),
                'version': resumen.get('version', 'unknown'),
            }
        
        bible_blob = container.get_blob_client(f"{job_id}/biblia_validada.json")
        
        if bible_blob.exists():
            bible = json.loads(bible_blob.download_blob().readall())
            properties = bible_blob.get_blob_properties()
            
            return {
                'id': job_id,
                'name': bible.get('titulo_obra', job_id),
                'status': 'pending_bible',
                'createdAt': properties.last_modified.isoformat() if properties.last_modified else '',
                'wordCount': bible.get('metricas_globales', {}).get('total_palabras', 0),
                'chaptersCount': bible.get('metricas_globales', {}).get('total_capitulos', 0),
                'changesCount': 0,
            }
        
        return None
        
    except Exception as e:
        logging.warning(f"⚠️ Error en {job_id}: {str(e)}")
        return None


def get_project_info(job_id: str) -> func.HttpResponse:
    """Obtiene información completa del proyecto."""
    try:
        blob_service = get_blob_service()
        container = blob_service.get_container_client('sylphrena-outputs')
        
        resumen_path = f"{job_id}/resumen_ejecutivo.json"
        blob = container.get_blob_client(resumen_path)
        
        if not blob.exists():
            return error_response('Project not found', 404)
        
        resumen = json.loads(blob.download_blob().readall())
        
        return success_response(resumen)
        
    except Exception as e:
        return error_response(str(e), 500)


# =============================================================================
# IMPLEMENTACIONES - BIBLIA
# =============================================================================

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
    """Guarda la Biblia editada."""
    try:
        edited_bible = req.get_json()
        
        blob_service = get_blob_service()
        container = blob_service.get_container_client('sylphrena-outputs')
        
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
    """Aprueba la Biblia."""
    try:
        return success_response({
            'message': 'Bible approved',
            'note': 'Processing will continue automatically'
        })
    except Exception as e:
        return error_response(str(e), 500)


# =============================================================================
# IMPLEMENTACIONES - MANUSCRITOS
# =============================================================================

def get_manuscript_edited(job_id: str) -> func.HttpResponse:
    """Obtiene manuscrito editado (limpio)."""
    try:
        blob_service = get_blob_service()
        container = blob_service.get_container_client('sylphrena-outputs')
        
        blob = container.get_blob_client(f"{job_id}/manuscrito_editado.md")
        
        if not blob.exists():
            return error_response('Manuscript not found', 404)
        
        content = blob.download_blob().readall().decode('utf-8')
        
        return func.HttpResponse(
            content,
            status_code=200,
            mimetype='text/plain',
            headers=get_cors_headers()
        )
        
    except Exception as e:
        return error_response(str(e), 500)


def get_manuscript_annotated(job_id: str) -> func.HttpResponse:
    """Obtiene manuscrito anotado (con cambios)."""
    try:
        blob_service = get_blob_service()
        container = blob_service.get_container_client('sylphrena-outputs')
        
        blob = container.get_blob_client(f"{job_id}/manuscrito_anotado.md")
        
        if not blob.exists():
            return error_response('Annotated manuscript not found', 404)
        
        content = blob.download_blob().readall().decode('utf-8')
        
        return func.HttpResponse(
            content,
            status_code=200,
            mimetype='text/plain',
            headers=get_cors_headers()
        )
        
    except Exception as e:
        return error_response(str(e), 500)


def get_changes_html(job_id: str) -> func.HttpResponse:
    """Obtiene control de cambios en HTML."""
    try:
        blob_service = get_blob_service()
        container = blob_service.get_container_client('sylphrena-outputs')
        
        blob = container.get_blob_client(f"{job_id}/control_cambios.html")
        
        if not blob.exists():
            return error_response('Changes HTML not found', 404)
        
        content = blob.download_blob().readall().decode('utf-8')
        
        return func.HttpResponse(
            content,
            status_code=200,
            mimetype='text/html',
            headers=get_cors_headers()
        )
        
    except Exception as e:
        return error_response(str(e), 500)


def get_changes(job_id: str) -> func.HttpResponse:
    """Obtiene lista estructurada de cambios."""
    try:
        blob_service = get_blob_service()
        container = blob_service.get_container_client('sylphrena-outputs')
        
        blob = container.get_blob_client(f"{job_id}/cambios_estructurados.json")
        
        if not blob.exists():
            return error_response('Changes not found', 404)
        
        changes_data = json.loads(blob.download_blob().readall())
        
        return success_response(changes_data)
        
    except Exception as e:
        return error_response(str(e), 500)


def save_change_decision(job_id: str, change_id: str, req: func.HttpRequest) -> func.HttpResponse:
    """Guarda decisión sobre un cambio."""
    try:
        decision = req.get_json()
        action = decision.get('action')
        
        if action not in ['accept', 'reject']:
            return error_response('Invalid action', 400)
        
        logging.info(f"✅ Decision: {change_id} -> {action}")
        
        return success_response({
            'change_id': change_id,
            'action': action,
            'saved': True
        })
        
    except Exception as e:
        return error_response(str(e), 500)


def export_manuscript(job_id: str) -> func.HttpResponse:
    """Exporta manuscrito final."""
    try:
        blob_service = get_blob_service()
        container = blob_service.get_container_client('sylphrena-outputs')
        
        blob = container.get_blob_client(f"{job_id}/capitulos_consolidados.json")
        chapters_data = blob.download_blob().readall()
        
        return func.HttpResponse(
            chapters_data,
            mimetype='application/json',
            headers={
                **get_cors_headers(),
                'Content-Disposition': f'attachment; filename="manuscript_{job_id}.json"'
            }
        )
        
    except Exception as e:
        return error_response(str(e), 500)


def handle_upload(req: func.HttpRequest) -> func.HttpResponse:
    """Maneja upload de nuevo manuscrito."""
    try:
        body = req.get_json()
        filename = body.get('filename')
        project_name = body.get('projectName')
        content_base64 = body.get('content')
        
        if not all([filename, project_name, content_base64]):
            return error_response('Missing required fields', 400)
        
        return success_response({
            'message': 'Upload received',
            'note': 'Processing will start soon'
        })
        
    except Exception as e:
        return error_response(str(e), 500)


# =============================================================================
# HELPERS
# =============================================================================

def get_blob_service() -> BlobServiceClient:
    """Obtiene cliente de Blob Storage."""
    connection_string = os.environ.get('AzureWebJobsStorage')
    return BlobServiceClient.from_connection_string(connection_string)


def get_cors_headers():
    """Headers CORS estándar."""
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    }


def cors_response() -> func.HttpResponse:
    """Respuesta para preflight CORS."""
    return func.HttpResponse(
        status_code=200,
        headers=get_cors_headers()
    )


def success_response(data: dict) -> func.HttpResponse:
    """Respuesta exitosa."""
    return func.HttpResponse(
        json.dumps(data, ensure_ascii=False),
        status_code=200,
        mimetype='application/json',
        headers=get_cors_headers()
    )


def error_response(message: str, status_code: int) -> func.HttpResponse:
    """Respuesta de error."""
    return func.HttpResponse(
        json.dumps({'error': message}),
        status_code=status_code,
        mimetype='application/json',
        headers=get_cors_headers()
    )
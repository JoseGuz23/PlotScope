"""
HTTP API Endpoints para Sylphrena Web Platform
VERSIÓN MAESTRA - Conexión de Biblia y Status Nativo
"""

import azure.functions as func
import azure.durable_functions as df
import logging
import json
import os
import base64
import hmac
import hashlib
import re
from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient, ContentSettings

# Configuración
ADMIN_PASSWORD = os.environ.get('SYLPHRENA_PASSWORD', 'sylphrena2025')
TOKEN_SECRET = os.environ.get('SYLPHRENA_TOKEN_SECRET', 'sylphrena-secret-key-2025')
logging.basicConfig(level=logging.INFO)

# =============================================================================
# MAIN ROUTER
# =============================================================================

async def main(req: func.HttpRequest, starter: str) -> func.HttpResponse:
    if req.method == 'OPTIONS': return cors_response()

    # Cliente Durable para hablar con el orquestador
    client = df.DurableOrchestrationClient(starter)
    
    # Limpieza de ruta
    raw_route = req.route_params.get('route', '')
    parts = [p for p in raw_route.strip('/').split('/') if p] 
    method = req.method
    
    try:
        # Auth Publica
        if raw_route == 'auth/login': return handle_login(req)
        if raw_route == 'analyze-file': return handle_analyze_file(req)

        # Auth Privada
        auth_error = verify_auth(req)
        if auth_error: return auth_error

        if raw_route == 'projects':
            return handle_projects_list(req, method)

        if len(parts) >= 2 and parts[0] == 'project':
            job_id = parts[1]

            # UPLOAD
            if method == 'POST' and job_id == 'upload':
                return handle_upload(req)

            # STATUS
            if method == 'GET' and len(parts) == 3 and parts[2] == 'status':
                return await get_orchestrator_status(client, job_id)
            
            # TERMINATE
            if method == 'POST' and len(parts) == 3 and parts[2] == 'terminate':
                return await terminate_orchestrator(client, job_id, req)

            # DELETE
            if method == 'DELETE' and len(parts) == 2:
                return delete_project(job_id)

            # INFO
            if method == 'GET' and len(parts) == 2: return get_project_info(job_id)
            
            # --- BIBLIA (AQUÍ ESTÁ LA MAGIA) ---
            if len(parts) >= 3 and parts[2] == 'bible':
                # Aprobar y reanudar orquestador
                if len(parts) == 4 and parts[3] == 'approve' and method == 'POST':
                    return await approve_bible_and_resume(client, job_id)
                
                # Leer/Guardar manual
                if method == 'GET': return get_bible(job_id)
                if method == 'POST': return save_bible(job_id, req)

            # MANUSCRITOS
            if len(parts) >= 3 and parts[2] == 'manuscript':
                if parts[3] == 'edited': return get_manuscript_edited(job_id)
                if parts[3] == 'annotated': return get_manuscript_annotated(job_id)
            
            # CAMBIOS
            if len(parts) >= 3 and parts[2] == 'changes':
                if len(parts) == 3: return get_changes(job_id)
                if len(parts) == 4: return save_all_decisions(job_id, req)
                if len(parts) == 5: return save_change_decision(job_id, parts[3], req)

            if len(parts) >= 3 and parts[2] == 'export': return export_manuscript(job_id)
            if len(parts) >= 3 and parts[2] == 'chapters': return get_chapters(job_id)

        return error_response(f'Ruta no encontrada: {raw_route}', 404)

    except Exception as e:
        return error_response(str(e), 500)

# =============================================================================
# LOGIC: APPROVE BIBLE (EL ESLABÓN PERDIDO)
# =============================================================================

async def approve_bible_and_resume(client, instance_id):
    """
    1. Marca la metadata como aprobada.
    2. Envía el evento 'BibleApproved' al orquestador para que salga de la pausa.
    """
    try:
        logging.info(f"👍 Aprobando biblia para: {instance_id}")
        
        # 1. Actualizar Metadata (Para historial)
        try:
            c = get_blob_service().get_blob_client("sylphrena-outputs", f"{instance_id}/metadata.json")
            if c.exists():
                meta = json.loads(c.download_blob().readall())
                meta['bible_approved'] = True
                meta['bible_approved_at'] = datetime.utcnow().isoformat() + 'Z'
                c.upload_blob(json.dumps(meta), overwrite=True)
        except Exception as e:
            logging.warning(f"No se pudo actualizar metadata (no crítico): {e}")

        # 2. DESPERTAR AL ORQUESTADOR
        await client.raise_event(instance_id, "BibleApproved")
        
        return success_response({'message': 'Biblia aprobada. Reanudando edición.'})
        
    except Exception as e:
        logging.error(f"Error reanudando orquestador: {e}")
        # Si falla el raise_event (ej: el proceso ya murió), avisamos
        return error_response(f"No se pudo reanudar el proceso: {str(e)}", 500)

# =============================================================================
# LOGIC: STATUS & TERMINATE
# =============================================================================

async def get_orchestrator_status(client, instance_id):
    try:
        status = await client.get_status(instance_id, show_history=False)
        
        if status:
            rt = str(status.runtime_status.value) if hasattr(status.runtime_status, 'value') else str(status.runtime_status)
            cust = status.custom_status
            
            # --- TRADUCTOR DE ESTADOS (SOLO TEXTO) ---
            cust_str = str(cust).lower() if cust else ""
            friendly = "Iniciando motores..." # Default

            if 'segment' in cust_str: 
                friendly = 'Segmentando manuscrito...'
            elif 'capa 1' in cust_str or 'batch c1' in cust_str: 
                friendly = 'Analizando hechos y datos (Capa 1)...'
            elif 'consolid' in cust_str: 
                friendly = 'Unificando hallazgos...'
            # Capa 2
            elif 'layer2' in cust_str or 'estructur' in cust_str or 'structur' in cust_str: 
                friendly = 'Analizando estructura narrativa (Capa 2)...'
            # Capa 3
            elif 'layer3' in cust_str or 'cualitativ' in cust_str or 'qualitative' in cust_str: 
                friendly = 'Evaluando estilo y profundidad (Capa 3)...'
            # Biblia / Holístico
            elif 'biblia' in cust_str or 'holistic' in cust_str: 
                friendly = 'Escribiendo la Biblia Narrativa...'
            # Espera
            elif 'esperando' in cust_str or 'wait' in cust_str: 
                friendly = 'Esperando revisión de Biblia...'
            # Arcos
            elif 'arco' in cust_str or 'arc' in cust_str: 
                friendly = 'Mapeando arcos de personajes...'
            # Edición
            elif 'edici' in cust_str or 'claude' in cust_str: 
                friendly = 'El Editor IA está puliendo el texto...'
            # Finalización
            elif 'finaliz' in cust_str or 'save' in cust_str: 
                friendly = 'Guardando y empaquetando proyecto...'
            elif cust:
                # Fallback para estados desconocidos pero con texto
                friendly = 'Procesando análisis avanzado...'
            
            return success_response({
                'instance_id': instance_id,
                'runtime_status': rt,
                'custom_status': cust,          
                'friendly_message': friendly,   
                'is_completed': rt == 'Completed',
                'is_failed': rt == 'Failed',
                'is_running': rt == 'Running',
                'output': status.output if rt == 'Completed' else None
            })
            
        # Fallback Metadata (cuando el proceso ya murió o se limpió del historial)
        try:
            c = get_blob_service().get_blob_client("sylphrena-outputs", f"{instance_id}/metadata.json")
            if c.exists():
                meta = json.loads(c.download_blob().readall())
                is_terminated = meta.get('status') == 'terminated'
                return success_response({
                    'instance_id': instance_id,
                    'runtime_status': 'Terminated' if is_terminated else 'Pending',
                    'custom_status': 'Detenido' if is_terminated else 'Iniciando',
                    'friendly_message': 'Proyecto detenido manualmente' if is_terminated else 'Inicializando...',
                    'is_completed': False, 
                    'is_failed': is_terminated,
                    'metadata': meta
                })
        except: pass
        
        return error_response('Proceso no encontrado', 404)
    except Exception as e: return error_response(str(e), 500)
    
async def terminate_orchestrator(client, instance_id, req):
    try:
        await client.terminate(instance_id, 'User termination')
        try:
            c = get_blob_service().get_blob_client("sylphrena-outputs", f"{instance_id}/metadata.json")
            if c.exists():
                meta = json.loads(c.download_blob().readall())
                meta['status'] = 'terminated'
                meta['terminated_at'] = datetime.utcnow().isoformat() + 'Z'
                c.upload_blob(json.dumps(meta), overwrite=True)
        except: pass
        return success_response({'terminated': True})
    except Exception as e: return error_response(str(e), 500)

# =============================================================================
# OTRAS FUNCIONES
# =============================================================================

def handle_upload(req):
    try:
        body = req.get_json()
        filename, project_name, content = body.get('filename'), body.get('projectName'), body.get('content')
        if not all([filename, project_name, content]): return error_response('Faltan datos', 400)
        
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        safe_name = re.sub(r'[^a-zA-Z0-9]', '_', project_name)[:30]
        job_id = f"{safe_name}_{timestamp}"
        
        service = get_blob_service()
        try: service.create_container("sylphrena-inputs")
        except: pass
        try: service.create_container("sylphrena-outputs")
        except: pass
        
        service.get_blob_client("sylphrena-inputs", f"{job_id}/{filename}").upload_blob(base64.b64decode(content), overwrite=True)
        
        meta = {'job_id': job_id, 'project_name': project_name, 'original_filename': filename, 'status': 'starting', 'created_at': datetime.utcnow().isoformat() + 'Z'}
        service.get_blob_client("sylphrena-outputs", f"{job_id}/metadata.json").upload_blob(json.dumps(meta), overwrite=True)
        
        return success_response({'job_id': job_id, 'status': 'uploaded', 'blob_path': f"{job_id}/{filename}"})
    except Exception as e: return error_response(str(e), 500)

def delete_project(job_id):
    try:
        srv = get_blob_service()
        for c in ["sylphrena-outputs", "sylphrena-inputs"]:
            try:
                cont = srv.get_container_client(c)
                for b in cont.list_blobs(name_starts_with=job_id): cont.delete_blob(b.name)
            except: pass
        return success_response({'deleted': True})
    except Exception as e: return error_response(str(e), 500)

def handle_projects_list(req, method):
    try:
        c = get_blob_service().get_container_client("sylphrena-outputs")
        projects = []
        seen = set()
        for b in c.list_blobs():
            jid = b.name.split('/')[0]
            if jid not in seen:
                seen.add(jid)
                try:
                    bc = c.get_blob_client(f"{jid}/metadata.json")
                    if bc.exists():
                        m = json.loads(bc.download_blob().readall())
                        projects.append({'id': jid, 'name': m.get('project_name'), 'status': m.get('status'), 'createdAt': m.get('created_at', '')})
                except: pass
        projects.sort(key=lambda x: x.get('createdAt', ''), reverse=True)
        return success_response({'projects': projects})
    except: return success_response({'projects': []})

# --- HELPERS ---
def verify_auth(req):
    auth = req.headers.get('Authorization', '')
    if not auth.startswith('Bearer ') or not verify_token(auth[7:]): return error_response('Unauthorized', 401)
    return None

def verify_token(token):
    try:
        data = base64.urlsafe_b64decode(token).decode()
        exp_str, sig = data.split(':')
        expected = hmac.new(TOKEN_SECRET.encode(), f"sylphrena:{exp_str}".encode(), hashlib.sha256).hexdigest()[:32]
        if not hmac.compare_digest(sig, expected): return False
        if datetime.utcnow() > datetime.strptime(exp_str, '%Y%m%d%H%M%S'): return False
        return True
    except: return False

def handle_login(req):
    try:
        if req.get_json().get('password') != ADMIN_PASSWORD: return error_response('Bad password', 401)
        exp = datetime.utcnow() + timedelta(hours=24)
        exp_str = exp.strftime('%Y%m%d%H%M%S')
        sig = hmac.new(TOKEN_SECRET.encode(), f"sylphrena:{exp_str}".encode(), hashlib.sha256).hexdigest()[:32]
        tk = base64.urlsafe_b64encode(f"{exp_str}:{sig}".encode()).decode()
        return success_response({'token': tk})
    except: return error_response('Login error', 500)

def handle_analyze_file(req): return success_response({'word_count': 0})
def get_blob_service(): return BlobServiceClient.from_connection_string(os.environ['AzureWebJobsStorage'])
def cors_response(): return func.HttpResponse(status_code=200, headers=get_cors_headers())
def success_response(d): return func.HttpResponse(json.dumps(d), status_code=200, mimetype='application/json', headers=get_cors_headers())
def error_response(m, c): return func.HttpResponse(json.dumps({'error': m}), status_code=c, mimetype='application/json', headers=get_cors_headers())
def get_cors_headers(): return {'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': '*', 'Access-Control-Allow-Headers': '*'}

# Stubs
def get_blob_json(jid, f):
    try: return success_response(json.loads(get_blob_service().get_blob_client("sylphrena-outputs", f"{jid}/{f}").download_blob().readall()))
    except: return error_response("Not found", 404)
def save_blob_json(jid, f, d):
    try: 
        get_blob_service().get_blob_client("sylphrena-outputs", f"{jid}/{f}").upload_blob(json.dumps(d), overwrite=True)
        return success_response({'success': True})
    except: return error_response("Error saving", 500)
def get_blob_text(jid, f):
    try: return func.HttpResponse(get_blob_service().get_blob_client("sylphrena-outputs", f"{jid}/{f}").download_blob().readall().decode(), headers=get_cors_headers())
    except: return error_response("Not found", 404)

def get_project_info(jid): return get_blob_json(jid, 'metadata.json')
def get_bible(jid): return get_blob_json(jid, 'biblia_validada.json')
def get_changes(jid): return get_blob_json(jid, 'cambios_estructurados.json')
def get_chapters(jid): return get_blob_json(jid, 'capitulos_consolidados.json')
def get_manuscript_edited(jid): return get_blob_text(jid, 'manuscrito_editado.md')
def get_manuscript_annotated(jid): return get_blob_text(jid, 'manuscrito_anotado.md')
def save_bible(jid, req): return save_blob_json(jid, 'biblia_validada.json', req.get_json())
# approve_bible ahora es manejado por approve_bible_and_resume en main
def approve_bible(jid): return success_response({'approved': True}) 
def save_all_decisions(jid, req): return save_blob_json(jid, 'cambios_estructurados.json', req.get_json())
def save_change_decision(jid, cid, req): return success_response({'saved': True})
def export_manuscript(jid): return get_blob_text(jid, 'manuscrito_editado.md')
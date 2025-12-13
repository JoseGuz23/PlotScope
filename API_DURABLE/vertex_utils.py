import os
import json
import logging
import time
from typing import List, Dict, Any, Optional
from google.cloud import storage
from google.cloud import aiplatform

logging.basicConfig(level=logging.INFO)

# Configuration from Environment Variables
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
REGION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-east5") # us-east5 recomendado para Claude
GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME", "sylphrena-app-batch-data")

# Initialize Vertex AI
if PROJECT_ID:
    try:
        aiplatform.init(project=PROJECT_ID, location=REGION)
    except Exception as e:
        logging.warning(f"Failed to initialize aiplatform: {e}")

def upload_jsonl_to_gcs(data: List[Dict], filename: str) -> str:
    """
    Uploads a list of dictionaries as a JSONL file to GCS.
    Returns the GCS URI (gs://bucket/path).
    """
    if not PROJECT_ID or not GCS_BUCKET_NAME:
        raise ValueError("GOOGLE_CLOUD_PROJECT and GCS_BUCKET_NAME must be set")

    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob(filename)

    jsonl_content = "\n".join([json.dumps(item) for item in data])
    blob.upload_from_string(jsonl_content, content_type="application/jsonl")

    gcs_uri = f"gs://{GCS_BUCKET_NAME}/{filename}"
    logging.info(f"Uploaded {len(data)} items to {gcs_uri}")
    return gcs_uri

def resolve_vertex_model_id(model_name: str) -> str:
    """
    Resuelve el nombre del modelo (config interna) a un ID de Vertex AI Publisher.
    """
    # Mapeo de nombres internos a Vertex AI Publisher Model IDs
    model_map = {
        # Sonnet (Balance Calidad/Velocidad)
        "claude-sonnet-4-5-20250929": "claude-3-5-sonnet-v2@20241022",
        "claude-3-5-sonnet": "claude-3-5-sonnet-v2@20241022",
        "claude-3-sonnet": "claude-3-sonnet@20240229",
        
        # Opus (Alta Calidad)
        "claude-opus-4-5-20251101": "claude-3-opus@20240229", 
        "claude-3-opus": "claude-3-opus@20240229",
        
        # Haiku (Velocidad/Costo)
        "claude-haiku-4-5-20251001": "claude-3-5-haiku@20241022",
        "claude-3-5-haiku": "claude-3-5-haiku@20241022",
        "claude-3-haiku": "claude-3-haiku@20240307",
    }
    
    # Intenta obtener del mapa
    vertex_id = model_map.get(model_name, model_name)
    
    return vertex_id

def submit_vertex_batch_job(
    model_name: str,
    source_uri: str,
    destination_uri_prefix: str,
    job_display_name: str = None
) -> str:
    """
    Submits a Batch Prediction Job to Vertex AI.
    Returns the Job ID (resource name).
    """
    if not job_display_name:
        job_display_name = f"claude-batch-{int(time.time())}"

    # Resolvemos el ID base
    base_id = resolve_vertex_model_id(model_name)
    
    # Para Batch Prediction, necesitamos el resource name completo
    if not base_id.startswith("publishers/") and not base_id.startswith("projects/"):
        # Limpiar @version para el path de publisher si da problemas
        # Generalmente: publishers/anthropic/models/claude-3-5-sonnet-v2
        model_clean = base_id.split('@')[0]
        vertex_model_id = f"publishers/anthropic/models/{model_clean}"
    else:
        vertex_model_id = base_id

    logging.info(f"Submitting Batch Job for model: {vertex_model_id}")

    batch_prediction_job = aiplatform.BatchPredictionJob.create(
        job_display_name=job_display_name,
        model_name=vertex_model_id,
        instances_format="jsonl",
        predictions_format="jsonl",
        gcs_source=source_uri,
        gcs_destination_prefix=destination_uri_prefix,
        sync=False 
    )

    logging.info(f"Batch Job submitted: {batch_prediction_job.resource_name}")
    return batch_prediction_job.resource_name

def get_batch_job_status(job_resource_name: str) -> Dict[str, Any]:
    """
    Checks the status of a Batch Prediction Job.
    """
    job = aiplatform.BatchPredictionJob(job_resource_name)
    
    state_map = {
        0: "JOB_STATE_UNSPECIFIED",
        1: "JOB_STATE_QUEUED",
        2: "JOB_STATE_PENDING",
        3: "JOB_STATE_RUNNING",
        4: "JOB_STATE_SUCCEEDED",
        5: "JOB_STATE_FAILED",
        6: "JOB_STATE_CANCELLING",
        7: "JOB_STATE_CANCELLED",
        8: "JOB_STATE_PAUSED",
        9: "JOB_STATE_EXPIRED",
        10: "JOB_STATE_UPDATING",
        11: "JOB_STATE_PARTIALLY_SUCCEEDED",
    }
    
    state_str = state_map.get(job.state.value, "UNKNOWN")
    
    return {
        "state": state_str,
        "error": str(job.error) if job.error else None,
        "completion_stats": job.completion_stats,
        "output_info": job.output_info,
        "create_time": str(job.create_time),
        "end_time": str(job.end_time)
    }

def get_batch_job_results(job_resource_name: str) -> List[Dict]:
    """
    Downloads and parses results from a completed Batch Job.
    """
    job = aiplatform.BatchPredictionJob(job_resource_name)
    
    if job.state.name not in ["JOB_STATE_SUCCEEDED", "JOB_STATE_PARTIALLY_SUCCEEDED"]:
         raise ValueError(f"Job not succeeded. State: {job.state.name}")

    if not job.output_info or not job.output_info.gcs_output_directory:
        raise ValueError("No GCS output directory found.")

    output_dir = job.output_info.gcs_output_directory
    # output_dir is like gs://bucket/path/prediction-model-timestamp
    
    storage_client = storage.Client(project=PROJECT_ID)
    
    # Parse bucket and prefix
    if output_dir.startswith("gs://"):
        output_dir = output_dir[5:]
    bucket_name = output_dir.split("/")[0]
    prefix = "/".join(output_dir.split("/")[1:])

    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=prefix)
    
    results = []
    for blob in blobs:
        if blob.name.endswith("prediction.results-00000-of-00001") or blob.name.endswith(".jsonl"): # File naming pattern varies
             content = blob.download_as_text()
             for line in content.splitlines():
                 if line.strip():
                     try:
                        results.append(json.loads(line))
                     except json.JSONDecodeError:
                         logging.warning(f"Failed to parse line in results: {line}")

    return results

def format_claude_vertex_request(
    messages: List[Dict],
    system: str = "",
    max_tokens: int = 4096,
    temperature: float = 0.5,
    custom_id: str = None
) -> Dict:
    """
    Formats a request for Claude on Vertex AI Batch.
    """
    
    instance = {
        "anthropic_version": "vertex-2023-10-16",
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False
    }
    
    if system:
        instance["system"] = system
        
    return instance

import azure.functions as func
import json
import sys

def main(req: func.HttpRequest) -> func.HttpResponse:
    """Verifica que todos los módulos estén instalados en Azure."""
    
    modules = [
        "azure.functions",
        "azure.durable_functions",
        "google.genai",
        "anthropic",
        "tenacity",
        "docx",
        "pdfplumber",
        "regex",
        "requests",
    ]
    
    results = {"ok": [], "failed": [], "python_version": sys.version}
    
    for module in modules:
        try:
            __import__(module)
            results["ok"].append(module)
        except ImportError as e:
            results["failed"].append({"module": module, "error": str(e)})
    
    results["all_ok"] = len(results["failed"]) == 0
    results["summary"] = f"{len(results['ok'])}/{len(modules)} módulos OK"
    
    status_code = 200 if results["all_ok"] else 500
    
    return func.HttpResponse(
        json.dumps(results, indent=2),
        status_code=status_code,
        mimetype="application/json"
    )
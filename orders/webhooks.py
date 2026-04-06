import logging
import json
from django.http import JsonResponse
from .router import ProviderRouter

logger = logging.getLogger(__name__)

def vtu_webhook(request, provider_name):
    """Generic webhook handler for all VTU providers."""
    try:
        if request.method == "POST":
            try:
                data = json.loads(request.body.decode("utf-8"))
            except:
                data = request.POST.dict()
        else:
            data = request.GET.dict()
            
        logger.info(f"Webhook received from {provider_name}: {data}")
        
        provider = ProviderRouter.get_provider_implementation(provider_name)
        if provider:
            provider.handle_webhook(data)
            return JsonResponse({"status": "SUCCESS", "message": "Webhook processed"})
        
        return JsonResponse({"status": "NOT_FOUND", "message": f"Provider {provider_name} implementation not found"}, status=404)
    except Exception as e:
        logger.error(f"Error in vtu_webhook for {provider_name}: {e}")
        return JsonResponse({"status": "ERROR", "message": str(e)}, status=500)

def vtu_callback(request, provider_name):
    """Generic callback handler for all VTU providers."""
    try:
        if request.method == "POST":
            try:
                data = json.loads(request.body.decode("utf-8"))
            except:
                data = request.POST.dict()
        else:
            data = request.GET.dict()
            
        logger.info(f"Callback received from {provider_name}: {data}")
        
        provider = ProviderRouter.get_provider_implementation(provider_name)
        if provider:
            provider.handle_callback(data)
            return JsonResponse({"status": "SUCCESS", "message": "Callback processed"})
            
        return JsonResponse({"status": "NOT_FOUND", "message": f"Provider {provider_name} implementation not found"}, status=404)
    except Exception as e:
        logger.error(f"Error in vtu_callback for {provider_name}: {e}")
        return JsonResponse({"status": "ERROR", "message": str(e)}, status=500)
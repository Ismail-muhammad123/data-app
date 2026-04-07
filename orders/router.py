from .models import VTUProviderConfig, ServiceRouting, ServiceFallback
from django.db import models
from .interfaces import BaseVTUProvider
from typing import Optional, List, Dict, Any
import logging

# Import all provider implementations
from .providers.vtpass import VTPassProvider
from .providers.clubkonnect import ClubKonnectProvider
from .providers.generic import GenericLocalProvider
from .providers.arewa_global import ArewaGlobalProvider


logger = logging.getLogger(__name__)

class ProviderRouter:
    """
    Router to select, instantiate and handle fallbacks for VTU providers.
    """
    

    FACTORIES = {
        'vtpass': VTPassProvider,
        'clubkonnect': ClubKonnectProvider,
        'arewa_global': ArewaGlobalProvider,
        'alrahuz': GenericLocalProvider,
        'mobilenig': GenericLocalProvider,
        'otapay': GenericLocalProvider,
        'mightydata': GenericLocalProvider,
        'smedata': GenericLocalProvider,
        'mobilevtu': GenericLocalProvider,
        'aimtoget': GenericLocalProvider,
        'nata_api': GenericLocalProvider,
        'amigo': GenericLocalProvider,
        'vtu_org': GenericLocalProvider,
        'payflex': GenericLocalProvider,
    }

    @classmethod
    def get_provider_implementation(cls, provider_name: str) -> Optional[BaseVTUProvider]:
        """
        Instantiate the provider implementation class.
        Checks for dynamic providers first, then hardcoded factories.
        """
        from .models import DynamicVTUProvider
        from .providers.dynamic import DynamicProvider

        # 1. Try Dynamic Provider matching slug or name
        dynamic = DynamicVTUProvider.objects.filter(is_active=True).filter(
            models.Q(name__iexact=provider_name) | models.Q(slug__iexact=provider_name)
        ).first()

        if dynamic:
            # Build config from many-to-one relations
            ops = {}
            for op in dynamic.operations.all():
                ops[op.operation_type] = {
                    'endpoint_path': op.endpoint_path,
                    'method': op.method,
                    'request_params': op.request_params,
                    'static_params': op.static_params,
                    'success_condition': op.success_condition,
                }
            
            config = {
                'name': dynamic.name,
                'slug': dynamic.slug,
                'base_url': dynamic.base_url,
                'api_key': dynamic.api_key,
                'api_key_header': dynamic.api_key_header,
                'api_key_prefix': dynamic.api_key_prefix,
                'request_format': dynamic.request_format,
                'operations': ops
            }
            return DynamicProvider(config)

        # 2. Try hardcoded factories
        provider_class = cls.FACTORIES.get(provider_name.lower())
        if not provider_class:
            return None

        config_obj = VTUProviderConfig.objects.filter(name=provider_name, is_active=True).first()
        if not config_obj:
            return None

        try:     
            instance = provider_class(config_obj.get_config_dict())
            instance.provider_config = config_obj
            return instance
        except Exception as e:
            logger.error(f"Error instantiating provider {provider_name}: {e}")
            
        return None

    @staticmethod
    def get_routing_chain(service: str) -> List[BaseVTUProvider]:
        """
        Return an ordered list of providers to try for a given service.
        Primary provider first, then fallbacks in order.
        """
        routing = ServiceRouting.objects.filter(service=service).first()
        if not routing:
            return []

        chain = []
        
        # 1. Primary
        if routing.primary_provider and routing.primary_provider.is_active:
            impl = ProviderRouter.get_provider_implementation(routing.primary_provider.name)
            if impl:
                chain.append(impl)

        # 2. Fallbacks
        fallbacks = ServiceFallback.objects.filter(service_routing=routing, provider__is_active=True).order_by('priority')
        for fb in fallbacks:
            if routing.primary_provider and fb.provider == routing.primary_provider:
                continue # Already added
                
            impl = ProviderRouter.get_provider_implementation(fb.provider.name)
            if impl:
                chain.append(impl)

        return chain

    @staticmethod
    def execute_with_fallback(service: str, action: str, **kwargs) -> Dict[str, Any]:
        routing = ServiceRouting.objects.filter(service=service).first()
        max_retries = routing.retry_count if routing else 1
        
        chain = ProviderRouter.get_routing_chain(service)
        if not chain:
            return {"status": "FAILED", "error": f"No active provider configured for {service}."}

        last_error = ""
        for provider in chain:
            # Retry logic per provider
            for attempt in range(max_retries):
                try:
                    method = getattr(provider, action)
                    res = method(**kwargs)
                    
                    if res.get('status') == 'SUCCESS' or res.get('status') == 'ORDER_RECEIVED':
                        res['provider_used'] = provider.provider_name
                        return res
                    
                    last_error = res.get('message', 'Unknown provider error')
                    logger.warning(f"Provider {provider.provider_name} attempt {attempt+1} failed: {last_error}.")
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(1) # Brief pause before retry
                    
                except Exception as e:
                    last_error = str(e)
                    logger.error(f"Error calling {action} on {provider.provider_name}: {last_error}")
                    break # Skip to next provider if implementation error

        return {"status": "FAILED", "error": f"All providers and retries failed. Last error: {last_error}"}

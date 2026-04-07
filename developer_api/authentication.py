from rest_framework import authentication
from rest_framework import exceptions
from .models import APIKey

class APIKeyAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        api_key_header = request.META.get('HTTP_X_API_KEY')
        if not api_key_header:
            return None

        try:
            key = APIKey.objects.select_related('profile__user').get(key=api_key_header, is_active=True)
        except APIKey.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid or inactive API key')

        if not key.profile.is_active:
            raise exceptions.AuthenticationFailed('Developer account is inactive')

        # Attach useful context to request
        request.mode = key.mode
        request.developer_profile = key.profile
        
        from django.utils import timezone
        key.last_used = timezone.now()
        key.save(update_fields=['last_used'])

        return (key.profile.user, key)

from django.contrib import admin
from .models import DeveloperProfile, APIKey, APIRequestLog

class APIKeyInline(admin.TabularInline):
    model = APIKey
    extra = 0
    readonly_fields = ['key', 'mode', 'created_at', 'last_used']

@admin.register(DeveloperProfile)
class DeveloperProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_active', 'webhook_url', 'created_at')
    search_fields = ('user__phone_number', 'user__email')
    list_filter = ('is_active',)
    inlines = [APIKeyInline]

@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ('profile', 'mode', 'is_active', 'last_used')
    list_filter = ('mode', 'is_active')
    search_fields = ('key', 'profile__user__phone_number')

@admin.register(APIRequestLog)
class APIRequestLogAdmin(admin.ModelAdmin):
    list_display = ('profile', 'endpoint', 'method', 'status_code', 'timestamp')
    list_filter = ('method', 'status_code')
    readonly_fields = ('profile', 'endpoint', 'method', 'request_payload', 'response_payload', 'status_code', 'ip_address', 'timestamp')

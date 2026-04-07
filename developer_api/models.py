import uuid
import secrets
import hashlib
from django.db import models
from django.conf import settings

class DeveloperProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="developer_profile")
    is_active = models.BooleanField(default=True)
    webhook_url = models.URLField(blank=True, null=True)
    webhook_secret = models.CharField(max_length=64, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.webhook_secret:
            self.webhook_secret = secrets.token_hex(32)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.phone_number} - Developer"

class APIKey(models.Model):
    MODE_CHOICES = [('live', 'Live'), ('sandbox', 'Sandbox')]
    
    profile = models.ForeignKey(DeveloperProfile, on_delete=models.CASCADE, related_name="api_keys")
    key = models.CharField(max_length=128, unique=True, db_index=True)
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='live')
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)

    @staticmethod
    def generate_key(mode='live'):
        prefix = "ak_live_" if mode == 'live' else "ak_test_"
        return f"{prefix}{secrets.token_urlsafe(48)}"

    def __str__(self):
        return f"{self.mode} Key ({self.profile.user.phone_number})"

class APIRequestLog(models.Model):
    profile = models.ForeignKey(DeveloperProfile, on_delete=models.CASCADE, related_name="request_logs")
    endpoint = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    request_payload = models.JSONField(null=True, blank=True)
    response_payload = models.JSONField(null=True, blank=True)
    status_code = models.IntegerField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

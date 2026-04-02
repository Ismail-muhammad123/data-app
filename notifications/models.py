from django.db import models
from django.conf import settings

class NotificationProviderConfig(models.Model):
    PROVIDER_CHOICES = [
        ('fcm', 'Firebase Cloud Messaging'),
        ('email', 'Email'),
        ('termii', 'Termii (SMS)'),
        ('whatsapp', 'WhatsApp'),
    ]

    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, unique=True)
    is_active = models.BooleanField(default=True)
    config_data = models.JSONField(default=dict, help_text='{"api_key": "...", "sender_id": "...", "from_email": "..."}')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Notification Provider Config"
        verbose_name_plural = "Notification Provider Configs"

    def __str__(self):
        return self.get_provider_display()


class NotificationLog(models.Model):
    CHANNEL_CHOICES = [
        ('push', 'Push'),
        ('email', 'Email'),
        ('sms', 'SMS'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_logs")
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    title = models.CharField(max_length=255)
    body = models.TextField()
    status = models.CharField(max_length=20, default="SENT") # SENT, FAILED
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.channel} to {self.user.phone_number}: {self.title}"


class NotificationTemplate(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=255)
    body = models.TextField(help_text="Use {username}, {amount}, {reference} placeholder tags.")
    
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.slug

class Announcement(models.Model):
    AUDIENCE_CHOICES = [('all','All Users'),('agents','Agents Only'),('customers','Customers Only')]
    title = models.CharField(max_length=255)
    body = models.TextField()
    image_url = models.URLField(blank=True, null=True)
    audience = models.CharField(max_length=20, choices=AUDIENCE_CHOICES, default='all')
    is_active = models.BooleanField(default=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

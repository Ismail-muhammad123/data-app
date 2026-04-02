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


class Notification(models.Model):
    CHANNEL_CHOICES = [
        ('fcm', 'Push (FCM)'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
    ]
    title = models.CharField(max_length=255)
    body = models.TextField()
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    
    # Metadata for deep linking or extra info
    data = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_channel_display()}: {self.title}"

class UserNotification(models.Model):
    STATUS_CHOICES = [
        ('SENT', 'Sent'),
        ('FAILED', 'Failed'),
        ('PENDING', 'Pending'),
    ]
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name="user_notifications")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="SENT")
    error_message = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('notification', 'user')

    def __str__(self):
        return f"Notification for {self.user.phone_number}: {self.notification.title}"


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

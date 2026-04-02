from django.db import models
from django.conf import settings

class SupportTicket(models.Model):
    CATEGORY_CHOICES = [
        ('transaction','Transaction Issue'), 
        ('wallet','Wallet Issue'),
        ('account','Account Issue'), 
        ('other','Other'),
    ]
    STATUS_CHOICES = [
        ('open','Open'), 
        ('in_progress','In Progress'),
        ('resolved','Resolved'), 
        ('closed','Closed'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tickets')
    subject = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    related_reference = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"#{self.id} {self.subject} ({self.status})"

class TicketMessage(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    is_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Msg on #{self.ticket.id} by {self.sender.phone_number}"

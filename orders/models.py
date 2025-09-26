# vtpass_integration/models.py

from django.db import models
from django.conf import settings



class Plan(models.Model):
    SERVICE_TYPES = [
        ("airtime", "Airtime"),
        ("data", "Data"),
        ("smile", "Smile"),
        ("other", "Other"),
    ]

    service_type = models.CharField(max_length=20, choices=SERVICE_TYPES)
    service_id = models.CharField(max_length=100)  
    name = models.CharField(max_length=255)        
    description = models.TextField(blank=True, null=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)   
    selling_price = models.DecimalField(max_digits=10, decimal_places=2) 
    duration_days = models.PositiveIntegerField(blank=True, null=True)   

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["service_type", "name"]
        # unique_together = ("service_id", "variation_code")
        verbose_name = "Plan"
        verbose_name_plural = "Plans"


    def __str__(self):
        return f"{self.name} ({self.service_type})"


class PlanTransaction(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20)  # where airtime/data goes
    reference = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    response_data = models.JSONField(blank=True, null=True)  # store VTPass response
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.plan} - {self.status}"
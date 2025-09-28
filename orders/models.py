from django.db import models
from django.conf import settings

STATUS_CHOICES = (
    ("pending", "Pending"),
    ("success", "Success"),
    ("failed", "Failed"),
)

class DataNetwork(models.Model):
    name=models.CharField(max_length=100)
    service_id= models.CharField(max_length=100)
    image_url = models.URLField(blank=True,null=True)

    def __str__(self):
        return self.name


class DataPlan(models.Model):
    name = models.CharField(max_length=255)   
    service_type = models.ForeignKey(DataNetwork, on_delete=models.SET_NULL, null=True, related_name="data_plans")
    variation_code = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)   
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0) 
    duration_days = models.PositiveIntegerField(blank=True, null=True)   


    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Data Plan"
        verbose_name_plural = "Data Plans"


    def __str__(self):
        return self.name
    
class DataSale(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey(DataPlan, on_delete=models.CASCADE)
    reference = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    beneficiary = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.plan} - {self.status}"

    
class AirtimeNetwork(models.Model):
    name = models.CharField(max_length=200)
    service_id = models.CharField(max_length=100)
    minimum_amount = models.PositiveIntegerField()
    maximum_amount= models.PositiveIntegerField()
    image_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name


class AirtimeSale(models.Model):
    airtime_type = models.ForeignKey(AirtimeNetwork, null=True, on_delete=models.SET_NULL, related_name="airtime_sales")
    reference = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="airtime_purchases")
    amount = models.PositiveBigIntegerField()
    beneficiary = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    time = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.amount} {self.airtime_type.name} to {self.beneficiary}"



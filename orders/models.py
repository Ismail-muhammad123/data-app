from django.db import models
from django.conf import settings

SERVICES = (
    ('mtn', 'MTN'),
    ('glo', 'GLO'),
    ('airtel', 'AIRTEL'),
    ('9mobile', '9MOBILE'),
)




class DataService(models.Model):
    service_name=models.CharField(max_length=100)
    service_id= models.CharField(max_length=100)
    image_url = models.URLField(blank=True,null=True)

    def __str__(self):
        return self.service_name

class AirtimeNetwork(models.Model):
    service_name = models.CharField(max_length=200)
    service_id = models.CharField(max_length=100)
    image_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.service_name

class DataVariation(models.Model):
    name = models.CharField(max_length=255)   
    service = models.ForeignKey(DataService, on_delete=models.CASCADE, related_name="variations", null=True)
    variation_id = models.CharField(max_length=100)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)   
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0) 

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Data Variation"
        verbose_name_plural = "Data Variations"


    def __str__(self):
        return self.name
    

# class ElectricityVariations(models.Model):
#     pass


# class TVVariations(models.Model):
#     pass

    

class Purchase(models.Model):
    PURCHASE_TYPES = (
        ('data', 'Data'),
        ('airtime', 'Airtime'),
    )

    STATUS_CHOICES = (
    ("pending", "Pending"),
    ("success", "Success"),
    ("failed", "Failed"),
)

    purchase_type = models.CharField(max_length=50, choices=PURCHASE_TYPES)  # 'data' or 'airtime'
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="purchases")
    # airtime_network = models.CharField(max_length=100, null=True, blank=True, choices=AIRTIME_NETWORKS)
    airtime_service = models.ForeignKey(AirtimeNetwork, on_delete=models.SET_NULL, null=True, related_name="sales")
    data_variation = models.ForeignKey(DataVariation, on_delete=models.SET_NULL, null=True, related_name="sales")
    reference = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    beneficiary = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    time = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.purchase_type} purchase to {self.beneficiary}"



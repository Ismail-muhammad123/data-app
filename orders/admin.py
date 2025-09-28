from django.contrib import admin
from .models import DataNetwork, DataPlan, DataSale, AirtimeNetwork, AirtimeSale 


@admin.register(DataNetwork)
class DataNetworkAdmin(admin.ModelAdmin):
    list_display= ["name", "service_id", "image_url", ]


@admin.register(DataPlan)
class DataPlanAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "service_type",
        "description",
        "cost_price",
        "selling_price",
        "duration_days",
        "is_active",
        "updated_at",
    ]

    list_filter = ["service_type", "is_active"]
    ordering = ["service_type"]
    list_per_page = 50


@admin.register(DataSale)
class DataPlanSaleAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "plan",
        "amount",
        "beneficiary",
        "status",
        "reference",
        "time",
    ]

    list_filter = ["plan__service_type"]
    list_per_page = 50



@admin.register(AirtimeNetwork)
class AirtimeNetworkAdmin(admin.ModelAdmin):
    list_display= [
        "name", 
        "service_id", 
        "minimum_amount", 
        "maximum_amount", 
        # "image_url", 
    ]
    


@admin.register(AirtimeSale)
class AirtimeNetwroSale(admin.ModelAdmin):
    list_display= [
        "airtime_type",
        "reference",
        "user",
        "amount",
        "beneficiary",
        "status",
        "time",
    ]

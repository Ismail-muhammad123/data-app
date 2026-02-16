from django.contrib import admin
from .models import (
    DataService, DataVariation, AirtimeNetwork, 
    ElectricityService, ElectricityVariation, 
    Purchase, TVService, TVVariation,
    SmileVariation
)
from .services.clubkonnect import ClubKonnectClient
from django.utils.html import format_html
from django.db.models import Sum, Count, F
from django.contrib.admin import SimpleListFilter


class ClubKonnectSyncMixin:
    def sync_all_clubkonnect_services(self, request, queryset):
        client = ClubKonnectClient()
        try:
            success = client.sync_all_services()
            if success:
                self.message_user(request, "Successfully synced all services from ClubKonnect")
            else:
                self.message_user(request, "Failed to sync services from ClubKonnect", level='error')
        except Exception as e:
            self.message_user(request, f"An error occurred: {str(e)}", level='error')
    sync_all_clubkonnect_services.short_description = "Sync all ClubKonnect services"

    def sync_airtime_services(self, request, queryset):
        client = ClubKonnectClient()
        try:
            count = client.sync_airtime()
            self.message_user(request, f"Successfully synced {count} airtime networks")
        except Exception as e:
            self.message_user(request, f"An error occurred: {str(e)}", level='error')
    sync_airtime_services.short_description = "Sync Airtime from ClubKonnect"

    def sync_data_services(self, request, queryset):
        client = ClubKonnectClient()
        try:
            count = client.sync_data()
            self.message_user(request, f"Successfully synced {count} data plans")
        except Exception as e:
            self.message_user(request, f"An error occurred: {str(e)}", level='error')
    sync_data_services.short_description = "Sync Data from ClubKonnect"

    def sync_cable_services(self, request, queryset):
        client = ClubKonnectClient()
        try:
            count = client.sync_cable()
            self.message_user(request, f"Successfully synced {count} cable packages")
        except Exception as e:
            self.message_user(request, f"An error occurred: {str(e)}", level='error')
    sync_cable_services.short_description = "Sync Cable from ClubKonnect"

    def sync_electricity_services(self, request, queryset):
        client = ClubKonnectClient()
        try:
            count = client.sync_electricity()
            self.message_user(request, f"Successfully synced {count} electricity discos")
        except Exception as e:
            self.message_user(request, f"An error occurred: {str(e)}", level='error')
    sync_electricity_services.short_description = "Sync Electricity from ClubKonnect"

    def sync_smile_services(self, request, queryset):
        client = ClubKonnectClient()
        try:
            count = client.sync_smile()
            self.message_user(request, f"Successfully synced {count} smile packages")
        except Exception as e:
            self.message_user(request, f"An error occurred: {str(e)}", level='error')
    sync_smile_services.short_description = "Sync Smile from ClubKonnect"


@admin.register(DataService)
class DataServiceAdmin(admin.ModelAdmin, ClubKonnectSyncMixin):
    list_display= ["network_image", "service_name", "service_id", ]
    list_display_links = ["service_name", "network_image"]
    actions = ["sync_data_services", "sync_all_clubkonnect_services"]
    
    def network_image(self, obj):
        if obj.image_url:
            return format_html(
                '<img src="{}" width="150" height="150" style="object-fit: cover; border-radius: 6px;" />',
                obj.image_url
            )
        return "#"
    network_image.short_description = "Preview"


@admin.register(DataVariation)
class DataVariationAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "service",
        "variation_id",
        "cost_price",
        "selling_price",
        "is_active",
        "created_at",
        "updated_at",
    ]

    list_filter = ["service", "is_active"]
    ordering = ["service__service_name", "name", "selling_price"]
    list_per_page = 50


    
    actions = ["make_as_active"]

    def make_as_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} plan(s) marked as active.")
    make_as_active.short_description = "Mark selected plans as active"


@admin.register(ElectricityService)
class ElectricityServiceAdmin(admin.ModelAdmin, ClubKonnectSyncMixin):
    list_display= [
        "service_name", 
        "service_id", 
    ]
    list_display_links = ["service_name"]
    list_per_page= 100
    actions = ["sync_electricity_services", "sync_all_clubkonnect_services"]

@admin.register(ElectricityVariation)
class ElectricityVariationAdmin(admin.ModelAdmin):
    list_display = ["name", "service", "variation_id", "is_active"]
    list_filter = ["service", "is_active"]
    list_per_page = 50


@admin.register(TVService)
class TVServiceAdmin(admin.ModelAdmin, ClubKonnectSyncMixin):
    list_display= [
        "service_name", 
        "service_id", 
    ]
    list_display_links = ["service_name"]
    list_per_page= 100
    actions = ["sync_cable_services", "sync_all_clubkonnect_services"]


@admin.register(TVVariation)
class TVVariationAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "service",
        "variation_id",
        "selling_price",
        "is_active",
        "created_at",
        "updated_at",
    ]

    list_filter = ["service", "is_active"]
    ordering = ["service__service_name", "name", "selling_price"]
    list_per_page = 50


    
    actions = ["make_as_active"]

    def make_as_active(self, request, queryset):
        updated =queryset.update(is_active=True)
        self.message_user(request, f"{updated} plan(s) marked as active.")
    make_as_active.short_description = "Mark selected plans as active"


@admin.register(SmileVariation)
class SmileVariationAdmin(admin.ModelAdmin, ClubKonnectSyncMixin):
    list_display = [
        "name",
        "variation_id",
        "selling_price",
        "is_active",
        "created_at",
        "updated_at",
    ]

    list_filter = ["is_active"]
    ordering = ["name", "selling_price"]
    list_per_page = 50
    actions = ["make_as_active", "sync_smile_services", "sync_all_clubkonnect_services"]

    def make_as_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} plan(s) marked as active.")
    make_as_active.short_description = "Mark selected plans as active"


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = [
        "purchase_type",
        "user",
        "service_name",
        "reference",
        "order_id",
        "amount",
        "beneficiary",
        "status",
        "time",
    ]
  

    list_filter = ["purchase_type", "data_variation__service", "airtime_service", "status"]
    list_per_page = 100    

    actions = ["query_status", "cancel_transaction_action"]

    def query_status(self, request, queryset):
        client = ClubKonnectClient()
        for purchase in queryset:
            if not purchase.order_id and not purchase.reference:
                self.message_user(request, f"Purchase {purchase.id} has no OrderID or Reference", level='warning')
                continue
            
            resp = client.query_transaction(order_id=purchase.order_id, request_id=purchase.reference)
            if resp.get("status") == "success":
                status_code = resp.get("statuscode")
                if status_code == "200":
                    purchase.status = "success"
                elif status_code in ["100", "101", "102"]:
                    purchase.status = "pending"
                else:
                    purchase.status = "failed"
                purchase.save()
                self.message_user(request, f"Updated {purchase.reference}: {resp.get('orderstatus')}")
            else:
                self.message_user(request, f"Failed to query {purchase.reference}: {resp.get('message')}", level='error')

    query_status.short_description = "Check status from ClubKonnect"

    def cancel_transaction_action(self, request, queryset):
        client = ClubKonnectClient()
        for purchase in queryset:
            if not purchase.order_id:
                self.message_user(request, f"Purchase {purchase.id} has no OrderID to cancel", level='warning')
                continue
            
            resp = client.cancel_transaction(order_id=purchase.order_id)
            if resp.get("status") == "success":
                self.message_user(request, f"Cancelled {purchase.order_id}: {resp.get('message')}")
            else:
                self.message_user(request, f"Failed to cancel {purchase.order_id}: {resp.get('message')}", level='error')

    cancel_transaction_action.short_description = "Cancel on ClubKonnect"

    def service_name(self, obj):
        if obj.airtime_service:
            return obj.airtime_service.service_name
        elif obj.electricity_service:
            return obj.electricity_service.service_name
        elif obj.tv_variation:
            return obj.tv_variation.service.service_name
        elif obj.smile_variation:
            return "Smile Subscription"
        elif obj.data_variation:
            return obj.data_variation.service.service_name
        return "-"
    service_name.short_description = "Service Name"

    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj = ...):
        return False
    
    def has_change_permission(self, request, obj = ...):
        return False


@admin.register(AirtimeNetwork)
class AirtimeNetworkAdmin(admin.ModelAdmin, ClubKonnectSyncMixin):
    list_display= [
        "id",
        "network_image",
        "service_name", 
        "service_id", 
    ]

    list_display_links = ["network_image","service_name"]
    actions = ["sync_airtime_services", "sync_all_clubkonnect_services"]

    def network_image(self, obj):
        if obj.image_url:
            return format_html(
                '<img src="{}" width="150" height="150" style="object-fit: cover; border-radius: 6px;" />',
                obj.image_url
            )
        return "#"
    network_image.short_description = "Preview"

    list_per_page= 100
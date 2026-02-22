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
        "selling_price",
        "is_active",
        "updated_at",
    ]

    list_filter = ["service", "is_active", "updated_at"]
    ordering = ["service__service_name", "selling_price"]
    search_fields = ["name", "service__service_name"]
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
        "amount",
        "beneficiary",
        "status",
        "initiator",
        "time",
    ]
    
    readonly_fields = [
        "user", "purchase_type", "amount", "beneficiary", 
        "status", "reference", "order_id", "time", 
        "initiator", "initiated_by", "airtime_service",
        "data_variation", "electricity_service", "tv_variation",
        "smile_variation",
    ]
    fieldsets = [
        ("Purchase Details", {
            "fields": ("user", "purchase_type", "amount", "beneficiary", "service_name", "time")
        }),
        ("Transaction Status", {
            "fields": ("status", "reference", "order_id", "initiator", "initiated_by")
        }),
        ("Service Data", {
            "fields": ("airtime_service", "data_variation", "electricity_service", "tv_variation", "smile_variation")
        }),
    ]
    list_filter = ["purchase_type", "status", "initiator", "time"]
    search_fields = ["user__email", "user__phone_number", "reference", "beneficiary"]
    list_per_page = 100    
    change_list_template = "admin/orders/purchase/change_list.html"

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

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_admin_purchase_link'] = True
        return super().changelist_view(request, extra_context=extra_context)

    def has_add_permission(self, request):
        return True # We will use a custom view for adding
    
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('admin-purchase/', self.admin_site.admin_view(self.admin_purchase_view), name='orders-admin-purchase'),
        ]
        return custom_urls + urls

    def admin_purchase_view(self, request):
        from django.shortcuts import render, redirect
        from django.contrib import messages
        from users.models import User
        from wallet.utils import debit_wallet
        from .services.clubkonnect import ClubKonnectClient

        if request.method == "POST":
            user_id = request.POST.get("user")
            purchase_type = request.POST.get("purchase_type")
            beneficiary = request.POST.get("beneficiary")
            
            try:
                user = User.objects.get(id=user_id)
                client = ClubKonnectClient()
                
                if purchase_type == "AIRTIME":
                    network_id = request.POST.get("network")
                    amount = float(request.POST.get("amount"))
                    network = AirtimeNetwork.objects.get(id=network_id)
                    
                    # 1. Debit wallet first
                    debit_success, msg = debit_wallet(user.id, amount, f"Admin Airtime Purchase: {network.service_name}", initiator="admin", initiated_by=request.user)
                    if not debit_success:
                        messages.error(request, f"Debit failed: {msg}")
                    else:
                        # 2. Call ClubKonnect
                        ref = f"ADM-AIR-{uuid.uuid4().hex[:8].upper()}"
                        resp = client.buy_airtime(network.service_id, amount, beneficiary, ref)
                        
                        # 3. Create Purchase record
                        Purchase.objects.create(
                            user=user,
                            purchase_type="AIRTIME",
                            airtime_service=network,
                            amount=amount,
                            beneficiary=beneficiary,
                            reference=ref,
                            order_id=resp.get("orderid") if resp.get("status") == "success" else None,
                            status="success" if resp.get("status") == "success" else "failed",
                            initiator="admin",
                            initiated_by=request.user
                        )
                        if resp.get("status") == "success":
                            messages.success(request, "Airtime purchase successful")
                        else:
                            messages.error(request, f"ClubKonnect Error: {resp.get('message')}")

                elif purchase_type == "DATA":
                    variation_id = request.POST.get("variation")
                    variation = DataVariation.objects.get(id=variation_id)
                    amount = float(variation.selling_price)
                    
                    # 1. Debit wallet
                    debit_success, msg = debit_wallet(user.id, amount, f"Admin Data Purchase: {variation.name}", initiator="admin", initiated_by=request.user)
                    if not debit_success:
                        messages.error(request, f"Debit failed: {msg}")
                    else:
                        # 2. Call ClubKonnect
                        ref = f"ADM-DAT-{uuid.uuid4().hex[:8].upper()}"
                        resp = client.buy_data(variation.service.service_id, variation.variation_id, beneficiary, ref)
                        
                        # 3. Create Purchase record
                        Purchase.objects.create(
                            user=user,
                            purchase_type="DATA",
                            data_variation=variation,
                            amount=amount,
                            beneficiary=beneficiary,
                            reference=ref,
                            order_id=resp.get("orderid") if resp.get("status") == "success" else None,
                            status="success" if resp.get("status") == "success" else "failed",
                            initiator="admin",
                            initiated_by=request.user
                        )
                        if resp.get("status") == "success":
                            messages.success(request, "Data purchase successful")
                        else:
                            messages.error(request, f"ClubKonnect Error: {resp.get('message')}")
                
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
            
            return redirect("..")

        # GET request: Show form
        context = {
            **self.admin_site.each_context(request),
            "users": User.objects.all(),
            "networks": AirtimeNetwork.objects.all(),
            "variations": DataVariation.objects.filter(is_active=True).select_related('service'),
            "title": "Perform Admin VTU Purchase"
        }
        return render(request, "admin/orders/admin_purchase.html", context)

    def has_change_permission(self, request, obj = ...):
        return False


@admin.register(AirtimeNetwork)
class AirtimeNetworkAdmin(admin.ModelAdmin, ClubKonnectSyncMixin):
    list_display= [
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
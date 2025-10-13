from django.contrib import admin
from .models import DataNetwork, DataPlan, AirtimeNetwork, Purchase 
from django.utils.html import format_html
from django.db.models import Sum, Count, F
from django.contrib.admin import SimpleListFilter
from .models import DataPlan, AirtimeNetwork, DataNetwork


@admin.register(DataNetwork)
class DataNetworkAdmin(admin.ModelAdmin):
    list_display= ["network_image", "name", "service_id", ]
    list_display_links = ["name", "network_image"]
    
    def network_image(self, obj):
        if obj.image_url:
            return format_html(
                '<img src="{}" width="150" height="150" style="object-fit: cover; border-radius: 6px;" />',
                obj.image_url
            )
        return "#"
    network_image.short_description = "Preview"


@admin.register(DataPlan)
class DataPlanAdmin(admin.ModelAdmin):
    list_display = [
        "id",
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


    
    actions = ["make_as_active"]

    def make_as_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} plan(s) marked as active.")
    make_as_active.short_description = "Mark selected plans as active"

    


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "purchase_type",
        "user",
        # "airtime_type",
        # "data_plan",
        "reference",
        "amount",
        "beneficiary",
        "status",
        "time",
    ]
  

    list_filter = ["purchase_type", "data_plan__service_type", "airtime_type", "status"]
    list_per_page = 50


    def title(self, obj):
        if obj.purchase_type == "airtime":
            return obj.airtime_type
        else: 
            return obj.data_plan.service_type
        

    def service_type(self, obj):
        if obj.purchase_type == "airtime":
            return obj.airtime_type
        else: 
            return obj.data_plan.service_type


@admin.register(AirtimeNetwork)
class AirtimeNetworkAdmin(admin.ModelAdmin):
    list_display= [
        "network_image",
        "id",
        "name", 
        "service_id", 
        "minimum_amount", 
        "maximum_amount", 
    ]

    list_display_links = ["name", "network_image"]

    def network_image(self, obj):
        if obj.image_url:
            return format_html(
                '<img src="{}" width="150" height="150" style="object-fit: cover; border-radius: 6px;" />',
                obj.image_url
            )
        return "#"
    network_image.short_description = "Preview"

    list_per_page= 50


# class PurchaseSummaryProxy(Purchase):
#     class Meta:
#         proxy = True
#         verbose_name = "Purchase Summary"
#         verbose_name_plural = "Purchase Summaries"

# @admin.register(PurchaseSummaryProxy)
# class PurchaseSummaryAdmin(admin.ModelAdmin):
#     change_list_template = "admin/purchase_summary_change_list.html"
#     list_display = ("summary_type", "name", "total_amount", "total_count")

#     def get_queryset(self, request):
#         # Aggregate summaries for airtime, data, data plans, airtime networks, data networks
#         qs = Purchase.objects.all()
#         summaries = []

#         # Airtime summary
#         airtime_qs = qs.filter(purchase_type="airtime")
#         airtime_total = airtime_qs.aggregate(total=Sum("amount"), count=Count("id"))
#         summaries.append({
#             "summary_type": "Airtime",
#             "name": "All Airtime Purchases",
#             "total_amount": airtime_total["total"] or 0,
#             "total_count": airtime_total["count"] or 0,
#         })

#         # Data summary
#         data_qs = qs.filter(purchase_type="data")
#         data_total = data_qs.aggregate(total=Sum("amount"), count=Count("id"))
#         summaries.append({
#             "summary_type": "Data",
#             "name": "All Data Purchases",
#             "total_amount": data_total["total"] or 0,
#             "total_count": data_total["count"] or 0,
#         })

#         # Data Plan summary
#         for plan in DataPlan.objects.all():
#             plan_qs = qs.filter(data_plan=plan)
#             plan_total = plan_qs.aggregate(total=Sum("amount"), count=Count("id"))
#             summaries.append({
#                 "summary_type": "Data Plan",
#                 "name": plan.name,
#                 "total_amount": plan_total["total"] or 0,
#                 "total_count": plan_total["count"] or 0,
#             })

#         # Airtime Network summary
#         for network in AirtimeNetwork.objects.all():
#             network_qs = qs.filter(airtime_type=network)
#             network_total = network_qs.aggregate(total=Sum("amount"), count=Count("id"))
#             summaries.append({
#                 "summary_type": "Airtime Network",
#                 "name": network.name,
#                 "total_amount": network_total["total"] or 0,
#                 "total_count": network_total["count"] or 0,
#             })

#         # Data Network summary
#         for network in DataNetwork.objects.all():
#             network_qs = qs.filter(data_plan__service_type=network)
#             network_total = network_qs.aggregate(total=Sum("amount"), count=Count("id"))
#             summaries.append({
#                 "summary_type": "Data Network",
#                 "name": network.name,
#                 "total_amount": network_total["total"] or 0,
#                 "total_count": network_total["count"] or 0,
#             })

#         # Return as a list of dicts, not queryset
#         class SummaryObj:
#             def __init__(self, d):
#                 self.__dict__.update(d)
#         return [SummaryObj(d) for d in summaries]

#     def summary_type(self, obj):
#         return obj.summary_type

#     def name(self, obj):
#         return obj.name

#     def total_amount(self, obj):
#         return obj.total_amount

#     def total_count(self, obj):
#         return obj.total_count

#     def has_add_permission(self, request):
#         return False

#     def has_delete_permission(self, request, obj=None):
#         return False

#     def has_change_permission(self, request, obj=None):
#         return False
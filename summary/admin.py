from django import forms
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import SummaryDashboard, SiteConfig


class AnalyticsDateForm(forms.Form):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'vDateField form-control'}),
        required=False
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'vDateField form-control'}),
        required=False
    )


@admin.register(SummaryDashboard)
class SummaryAdmin(admin.ModelAdmin):
    change_list_template = "admin/summaries/system_summary.html"
    model = SummaryDashboard

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def changelist_view(self, request, extra_context=None):
        form = AnalyticsDateForm(request.GET or None)
        extra_context = extra_context or {}
        extra_context["summary"] = SummaryDashboard.summary()
        extra_context["form"] = form
        
        request.GET._mutable = True
        if request.GET.get("start_date", None) is not None:
             request.GET.pop("start_date")
        if request.GET.get("end_date", None) is not None:
             request.GET.pop("end_date")

        return super().changelist_view(request, extra_context=extra_context)


@admin.register(SiteConfig)
class SiteConfigAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Universal Charges", {
            "fields": ("withdrawal_charge", "crediting_charge")
        }),
        ("VTU Provider Funding Account", {
            "fields": ("vtu_funding_bank_name", "vtu_funding_account_number", "vtu_funding_account_name"),
            "description": "The bank account details for funding your VTU API wallet."
        }),
    )

    def has_add_permission(self, request):
        if SiteConfig.objects.exists():
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        return False

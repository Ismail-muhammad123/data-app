# from django.contrib import admin
# from django.utils.html import format_html
# from .models import UserSummary, WalletSummary, SavingsSummary, PaymentSummary, InvestmentSummary


# @admin.register(UserSummary)
# class UserSummaryAdmin(admin.ModelAdmin):
#     change_list_template = "admin/summaries/user_summary.html"

#     def changelist_view(self, request, extra_context=None):
#         extra_context = extra_context or {}
#         extra_context["summary"] = UserSummary.summary()
#         return super().changelist_view(request, extra_context=extra_context)


# @admin.register(WalletSummary)
# class WalletSummaryAdmin(admin.ModelAdmin):
#     change_list_template = "admin/summaries/wallet_summary.html"

#     def changelist_view(self, request, extra_context=None):
#         extra_context = extra_context or {}
#         extra_context["summary"] = WalletSummary.summary()
#         return super().changelist_view(request, extra_context=extra_context)


# @admin.register(SavingsSummary)
# class SavingsSummaryAdmin(admin.ModelAdmin):
#     change_list_template = "admin/summaries/savings_summary.html"

#     def changelist_view(self, request, extra_context=None):
#         extra_context = extra_context or {}
#         extra_context["summary"] = SavingsSummary.summary()
#         return super().changelist_view(request, extra_context=extra_context)


# @admin.register(PaymentSummary)
# class PaymentSummaryAdmin(admin.ModelAdmin):
#     change_list_template = "admin/summaries/payment_summary.html"

#     def changelist_view(self, request, extra_context=None):
#         extra_context = extra_context or {}
#         extra_context["summary"] = PaymentSummary.summary()
#         return super().changelist_view(request, extra_context=extra_context)


# @admin.register(InvestmentSummary)
# class InvestmentSummaryAdmin(admin.ModelAdmin):
#     change_list_template = "admin/summaries/investment_summary.html"

#     def changelist_view(self, request, extra_context=None):
#         extra_context = extra_context or {}
#         extra_context["summary"] = InvestmentSummary.summary()
#         return super().changelist_view(request, extra_context=extra_context)


from django import forms
from django.contrib import admin
from .models import SummaryDashboard
from django.utils.translation import gettext_lazy as _



class DateRangeFilter(admin.SimpleListFilter):
    title = _('Date Range')
    parameter_name = 'daterange'

    def lookups(self, request, model_admin):
        return ()  # No predefined choices, we’ll parse query params manually

    def queryset(self, request, queryset):
        start = request.GET.get("start_date")
        end = request.GET.get("end_date")

        if start:
            queryset = queryset.filter(created_at__gte=start)
        if end:
            queryset = queryset.filter(created_at__lte=end)

        return queryset
    
# class BranchAnalyticsFilterForm(forms.Form):
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
        
        
        # sales_qs = Sale.objects.all()
        # expense_qs = Expense.objects.all()
        # inventory_qs = BranchStock.objects.all()

        start = None
        end = None

        if form.is_valid():
            start = form.cleaned_data.get("start_date")
            end = form.cleaned_data.get("end_date")
          
            # if start:
            #     sales_qs = sales_qs.filter(date__gte=start)
            #     expense_qs = expense_qs.filter(date__gte=start)
            #     # inventory_qs = inventory_qs.filter(date__gte=start)

            # if end:
            #     sales_qs = sales_qs.filter(date__lte=end)
            #     expense_qs = expense_qs.filter(date__lte=end)
            #     # inventory_qs = inventory_qs.filter(date__lte=end)


        
        extra_context = extra_context or {}
        extra_context["summary"] = SummaryDashboard.summary()
        extra_context["form"] = form
        
        
        request.GET._mutable = True
        if request.GET.get("start_date", None) is not None:
            request.GET.pop("start_date")
        if request.GET.get("end_date", None) is not None:
            request.GET.pop("end_date")
        
        return super().changelist_view(request, extra_context=extra_context)

from django.contrib import admin
from django import forms
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from users.models import OTP, User
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from rest_framework.authtoken.models import Token

# update labes for dashboard
admin.site.site_title = "A-Star Data App - Dashboard"
admin.site.site_header = "A-Star Data App - Admin" 
admin.site.index_title = "Dashboard"


# Unregister Token if already registered
try:
    admin.site.unregister(Token)
except admin.sites.NotRegistered:
    pass

class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "middle_name",
            "phone_country_code",
            "phone_number",
            "email",
            )

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "middle_name",
            "phone_country_code",
            "phone_number",
            "email",
            "is_active",
            "is_staff",
            "is_closed",
            "closed_at",
            "closed_reason",
            'password',
        )


class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    list_display = [
        "full_name_and_phone",
        "email", 
        "tier",
        "wallet_balance",
        "account_verification_status",
        "active_status", 
        "staff_status", 
        "created_at", 
    ]
    readonly_fields = [
        "created_at",
        "bvn",
        "email_verified",
        "phone_number_verified",
        "is_verified"
    ]
    actions = ["create_virtual_account", "deactivate_user", "activate_user", "set_as_verified"]

    def wallet_balance(self, obj):
        from wallet.models import Wallet
        wallet = Wallet.objects.filter(user=obj).first()
        if wallet:
            return f"₦{wallet.balance:,.2f}"
        return "₦0.00"
    wallet_balance.short_description = "Wallet Balance"

    def full_name_and_phone(self, obj):
        from django.utils.html import format_html
        return format_html(
            '<div style="font-weight: bold; color: var(--body-quiet-color);">{}</div>'
            '<div style="font-size: 0.9em; color: var(--body-loud-color);">{}</div>',
            f"{obj.first_name or ''} {obj.last_name or ''}".strip() or "No Name",
            obj.phone_number
        )
    full_name_and_phone.short_description = "User Details"

    def active_status(self, obj):
        from django.utils.html import format_html
        color = "#16a34a" if obj.is_active else "#dc2626"
        status ="Closed" if obj.is_closed else "Active" if obj.is_active else "Inactive"
        return format_html(
            '<span style="color: {}; font-weight: 600;">{}</span>',
            color, status
        )
    active_status.short_description = "Status"

    def staff_status(self, obj):
        status = "Admin" if obj.is_staff else "Customer"
        return status
    staff_status.short_description = "Role"

    
    def account_verification_status(self, obj):
        from django.utils.html import format_html
        methods = []
        if obj.email_verified:
            methods.append("Email")
        if obj.phone_number_verified:
            methods.append("Phone")
        
        if not methods:
            return format_html('<span style="color: #dc2626;">Not Verified</span>')
        
        return format_html(
            '<span style="color: #2563eb; font-weight: 500;">{} Verified</span>',
            " & ".join(methods)
        )
    account_verification_status.short_description = "Verification"

    @admin.display(description="Deactivate User")   
    def deactivate_user(self, request, queryset):
        for obj in queryset:
            obj.is_active = False
            obj.save()
        self.message_user(request, "Users deactivated successfully")

    @admin.display(description="Activate User")
    def activate_user(self, request, queryset):
        for obj in queryset:
            obj.is_active = True
            obj.save()
        self.message_user(request, "Users activated successfully")

    @admin.display(description="Set as Verified")
    def set_as_verified(self, request, queryset):
        for obj in queryset:
            obj.is_verified = True
            obj.save()
        self.message_user(request, "Users verified successfully")

    @admin.action(description="Create virtual account")
    def create_virtual_account(self, request, queryset):
        from wallet.models import VirtualAccount
        from payments.utils import PaystackGateway
        from django.conf import settings
        import logging

        success_count = 0
        failed_count = 0
        
        logger = logging.getLogger(__name__)

        for obj in queryset:
            # Check if profile is complete
            is_complete = all([obj.first_name, obj.last_name, obj.email])
            has_account = VirtualAccount.objects.filter(user=obj).exists()

            if obj.tier == 1 and is_complete and not has_account:
                try:
                    client = PaystackGateway(settings.PAYSTACK_SECRET_KEY)
                    phone = f"{obj.phone_country_code}{obj.phone_number}" if obj.phone_number else ""
                    
                    client.create_virtual_account(
                        email=obj.email,
                        first_name=obj.first_name,
                        middle_name=obj.middle_name or "",
                        last_name=obj.last_name,
                        phone=phone,
                    )
                    success_count += 1
                except Exception as e:
                    error_msg = f"Error creating virtual account for {obj.email}: {str(e)}"
                    logger.error(error_msg)
                    print(error_msg) # Print to console
                    self.message_user(request, error_msg, level='error')
                    failed_count += 1
            else:
                reason = ""
                if not is_complete:
                    reason = "Profile incomplete (missing name, email or BVN)"
                elif has_account:
                    reason = "Already has a virtual account"
                elif obj.tier != 1:
                    reason = f"Not Tier 1 (Current Tier: {obj.get_tier_display()})"
                
                error_msg = f"Skipped {obj.email or obj.phone_number}: {reason}"
                logger.error(error_msg)
                print(error_msg) # Print to console
                self.message_user(request, error_msg, level='warning')
                failed_count += 1

        if success_count > 0:
            self.message_user(request, f"Successfully triggered virtual account creation for {success_count} users.")
        
    ordering = ['-created_at']
    list_filter = ('is_active', 'is_staff', 'tier')
    search_fields = ('first_name', 'last_name', 'email', "phone_number")
    filter_horizontal = ('groups', 'user_permissions',)
    fieldsets = (
        ('Authentication', {'fields': ('phone_country_code', 'phone_number', 'password')}),
        ("Personal Information", {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'middle_name', 'email', 'bvn'),
        }),
        ("Account Level", {"fields": ("tier", "is_verified", "email_verified", "phone_number_verified")}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'is_active', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('created_at', )}),
        ('Account Status', {
            'fields': (
                'is_closed',
                'closed_at',
                'closed_reason',
            ),
        }),
    )
    add_fieldsets = (
        ('Authentication', {'fields': ('phone_country_code', 'phone_number', 'password1', 'password2')}),
        ("Personal Information", {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'middle_name', 'email', ),
        }),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'is_active', 'groups', 'user_permissions')}),
        ('Account Status', {
            'fields': (
                'is_closed',
                'closed_at',
                'closed_reason',
            ),
        }),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        
        if obj.tier == 1 and obj.first_name and obj.last_name and obj.email and obj.bvn:
            from wallet.models import VirtualAccount
            if not VirtualAccount.objects.filter(user=obj).exists():
                try:
                    from payments.utils import PaystackGateway
                    from django.conf import settings
                    client = PaystackGateway(settings.PAYSTACK_SECRET_KEY)
                    
                    phone = f"{obj.phone_country_code}{obj.phone_number}" if obj.phone_number else ""
                    
                    client.create_virtual_account(
                        email=obj.email,
                        first_name=obj.first_name,
                        middle_name=obj.middle_name or "",
                        last_name=obj.last_name,
                        phone=phone,
                    )
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to create virtual account in admin: {e}")
    

from django.contrib.auth.models import Group
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin

admin.site.unregister(Group)

@admin.register(Group)
class GroupAdmin(BaseGroupAdmin):
    filter_horizontal = ('permissions',)

admin.site.register(User, UserAdmin)
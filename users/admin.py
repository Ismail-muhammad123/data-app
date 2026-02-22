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
            'password',
        )


class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    list_display = [
        "first_name", 
        "last_name",
        "phone_number", 
        "email", 
        "tier",
        "is_verified",
        "verification_methods",
        "is_active", 
        "is_staff", 
        "created_at", 
    ]
    readonly_fields = [
        "created_at",
        "email",
        "phone_number",
        "bvn",
        "is_verified",
        "email_verified",
        "phone_number_verified"
    ]

    def verification_methods(self, obj):
        from django.utils.html import format_html
        methods = []
        if obj.email_verified:
            methods.append('<span style="display:inline-block;padding:3px 10px;background-color:#2563eb;color:#fff;border-radius:6px;font-size:12px;font-weight:600;">Email</span>')
        if obj.phone_number_verified:
            methods.append('<span style="display:inline-block;padding:3px 10px;background-color:#16a34a;color:#fff;border-radius:6px;font-size:12px;font-weight:600;">Phone</span>')
        return format_html(", ".join(methods)) if methods else "None"
    
    verification_methods.short_description = "Verification Methods"

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
    )
    add_fieldsets = (
        ('Authentication', {'fields': ('phone_country_code', 'phone_number', 'password1', 'password2')}),
        ("Personal Information", {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'middle_name', 'email', ),
        }),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'is_active', 'groups', 'user_permissions')}),
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
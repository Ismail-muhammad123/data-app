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
        "middle_name",
        "phone_country_code", 
        "phone_number", 
        "email", 
        "tier",
        "is_verified",
        "verification_methods",
        "is_active", 
        "is_staff", 
        "created_at", 
    ]

    def verification_methods(self, obj):
        methods = []
        if obj.email_verified:
            methods.append('<span style="display:inline-block;padding:3px 10px;background-color:#2563eb;color:#fff;border-radius:6px;font-size:12px;font-weight:600;">Email</span>')
        if obj.phone_number_verified:
            methods.append('<span style="display:inline-block;padding:3px 10px;background-color:#16a34a;color:#fff;border-radius:6px;font-size:12px;font-weight:600;">Phone</span>')
        return ", ".join(methods) if methods else "None"
    
    verification_methods.allow_tags = True
    verification_methods.short_description = "Verification Methods"

    ordering = ['created_at']
    list_filter = ('is_active', 'is_staff' )
    search_fields = ('first_name', 'last_name', 'middle_name', 'email', "phone_number")
    filter_horizontal = ('groups', 'user_permissions',)
    fieldsets = (
        ('Authentication', {'fields': ('phone_country_code', 'phone_number', 'password')}),
        ("Personal Information", {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'middle_name', 'email', ),
        }),
        ("Account Level", {"fields": ("tier",)}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'is_active', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        ('Authentication', {'fields': ('phone_country_code', 'phone_number', 'password1', 'password2')}),
        ("Personal Information", {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'middle_name', 'email', ),
        }),
        # ("Account Level", {"fields": ("tier",)}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'is_active', 'groups', 'user_permissions')}),
    )
    

class OTPAdmin(admin.ModelAdmin):
    list_display= [
        "user",
        "code",
        "purpose",
        "created_at",
        "expires_at",
        "is_used",
    ]

admin.site.register(User, UserAdmin)
admin.site.register(OTP, OTPAdmin)
# from django.contrib import admin
# from django import forms
# from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
# from django.contrib.auth.models import Permission
# from users.models import User
# from django.contrib.auth.forms import ReadOnlyPasswordHashField
# from django.contrib.auth.models import Group
# from rest_framework.authtoken.models import Token

# # update labes for dashboard
# admin.site.site_title = "Z9Trades Dashboard"
# admin.site.site_header = "Z9Trades Admin" 
# admin.site.index_title = "Dashboard"

# # Unregister Group if already registered
# try:
#     admin.site.unregister(Group)
# except admin.sites.NotRegistered:
#     pass

# # Unregister Token if already registered
# try:
#     admin.site.unregister(Token)
# except admin.sites.NotRegistered:
#     pass

# class UserCreationForm(forms.ModelForm):
#     password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
#     password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

#     class Meta:
#         model = User
#         fields = (
#             "full_name",
#             "phone_country_code",
#             "phone_number",
#             "email",
#             )

#     def clean_password2(self):
#         password1 = self.cleaned_data.get("password1")
#         password2 = self.cleaned_data.get("password2")
#         if password1 and password2 and password1 != password2:
#             raise forms.ValidationError("Passwords don't match")
#         return password2

#     def save(self, commit=True):
#         user = super().save(commit=False)
#         user.set_password(self.cleaned_data["password1"])
#         if commit:
#             user.save()
#         return user

# class UserChangeForm(forms.ModelForm):
#     password = ReadOnlyPasswordHashField()

#     class Meta:
#         model = User
#         fields = (
#             "full_name",
#             "phone_country_code",
#             "phone_number",
#             "email",
#             "is_active",
#             "is_staff",
#             "created_at",
#             'password',
#         )


# class UserAdmin(BaseUserAdmin):
#     form = UserChangeForm
#     add_form = UserCreationForm
#     list_display = (
#         "full_name",
#         "phone_country_code",
#         "phone_number",
#         "email",
#         "is_active",
#         "is_staff",
#         "created_at",
#         )
     
#     list_filter = ('is_active', 'is_staff' )
#     fieldsets = (
#         ('Authentication', {'fields': ('phone_country_code', 'phone_number', 'password')}),
#         ("Personal Information", {
#             'classes': ('wide',),
#             'fields': ('full_name', 'email', 'country', ),
#         }),
#         ('Permissions', {'fields': ('is_staff', 'is_superuser', 'is_active')}),
#     )
#     add_fieldsets = (
#         ('Authentication', {'fields': ('phone_country_code', 'phone_number', 'password1', 'password2')}),
#         ("Personal Information", {
#             'classes': ('wide',),
#             'fields': ('full_name', 'country', ),
#         }),
#         ('Permissions', {'fields': ('is_staff', 'is_superuser', 'is_active')}),
#     )
#     search_fields = ('full_name', 'email')
#     ordering = ('date_joined', 'is_active')
#     filter_horizontal = ()

# admin.site.register(User, UserAdmin)
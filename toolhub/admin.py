from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser

    # What shows up in the user list table
    list_display = ('username', 'email', 'role', 'is_active')

    # What shows up in the form (edit page)
    fieldsets = (
        (None, {
            'fields': ('username', 'email', 'password')
        }),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'phone_number', 'profile_picture')
        }),
        ('CLA Settings', {
            'fields': ('role',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

    # For when adding a new user via the admin
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role')
        }),
    )

    search_fields = ('username', 'email')
    ordering = ('email',)
    filter_horizontal = ()  # Disable group/permission widget
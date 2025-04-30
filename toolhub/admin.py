from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser

    # What shows up in the user list table
    list_display = ('username', 'email', 'role', 'is_active', 'is_staff', 'date_joined', 'last_login', 'phone_number')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
    ordering = ('-date_joined',)

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
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined')
        }),
    )

    # For when adding a new user via the admin
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'is_active', 'is_staff', 'is_superuser')
        }),
    )

    filter_horizontal = ('groups', 'user_permissions')  # Enable group/permission widget

    readonly_fields = ('date_joined', 'last_login')

    # Add a bulk action
    actions = ['make_active', 'make_inactive', 'promote_to_librarian']

    def promote_to_librarian(self, request, queryset):
        queryset.update(role='librarian')
    promote_to_librarian.short_description = "Promote selected users to librarian"

    def get_readonly_fields(self, request, obj=None):
        # Only superusers may edit the 'role' field
        if not request.user.is_superuser:
            # lock down role for staff/patrons
            return self.readonly_fields + ('role',)
        return self.readonly_fields
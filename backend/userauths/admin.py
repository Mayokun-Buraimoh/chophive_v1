from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin
from userauths.models import User, Profile

# Register your models here.
class UserAdmin(BaseUserAdmin, ModelAdmin):
    list_display = ['email', 'username', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser', 'date_joined']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'date_joined']
    list_per_page = 10
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('OTP', {'fields': ('otp',)}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )

class ProfileAdmin(ModelAdmin):
    list_display = ['user', 'username', 'phone', 'hostel', 'room_number', 'level', 'department', 'created_at']
    search_fields = ['user__email', 'user__username', 'username', 'phone', 'hostel', 'department']
    list_filter = ['gender', 'level', 'department', 'hostel', 'created_at']
    list_per_page = 10
    ordering = ['-created_at']
    readonly_fields = ['pid', 'created_at', 'updated_at']
    
    fieldsets = (
        (None, {'fields': ('user', 'pid')}),
        ('Personal Information', {'fields': ('username', 'phone', 'gender', 'date_of_birth', 'image')}),
        ('Academic Information', {'fields': ('level', 'department', 'hostel', 'room_number')}),
        ('Preferences', {'fields': ('favorite_cafeteria', 'dietary_preferences')}),
        ('Address', {'fields': ('address',)}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
    )

admin.site.register(User, UserAdmin)
admin.site.register(Profile, ProfileAdmin)
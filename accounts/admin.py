from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from axes.models import AccessAttempt, AccessFailureLog
from axes.admin import AccessAttemptAdmin, AccessFailureLogAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'municipality', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'municipality']
    search_fields = ['username', 'email', 'municipality']
    fieldsets = UserAdmin.fieldsets + (
        ('LGU Info', {'fields': ('role', 'municipality', 'contact_number', 'profile_photo')}),
    )

# Re-register axes models explicitly to ensure they appear in admin
if not admin.site.is_registered(AccessAttempt):
    admin.site.register(AccessAttempt, AccessAttemptAdmin)

if not admin.site.is_registered(AccessFailureLog):
    admin.site.register(AccessFailureLog, AccessFailureLogAdmin)
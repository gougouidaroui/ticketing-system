from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from website.models import CustomUser, Ticket, Category, TicketComment

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'is_active', 'is_superuser', 'get_groups')
    list_filter = ('is_active', 'is_superuser', 'groups')
    search_fields = ('username', 'email')
    ordering = ('username',)

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_active', 'is_staff', 'is_superuser', 'groups'),
        }),
    )

    def get_groups(self, obj):
        return ", ".join([group.name for group in obj.groups.all()])
    get_groups.short_description = 'Groups'

admin.site.register(CustomUser, CustomUserAdmin)

admin.site.register(Ticket)
admin.site.register(Category)
admin.site.register(TicketComment)

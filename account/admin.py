from django.contrib import admin
from account.models import User


@admin.register(User)
class User(admin.ModelAdmin):
    exclude = ['password', 'groups', 'user_permissions']
    readonly_fields = ['email', 'last_login', 'date_joined', 'first_name', 'last_name', 'avatar']

from django.contrib import admin
from context.models import Fetcher


@admin.register(Fetcher)
class Fetchers(admin.ModelAdmin):
    pass

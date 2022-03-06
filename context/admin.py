from django.contrib import admin
from context.models import Gatherer


@admin.register(Gatherer)
class Gatherers(admin.ModelAdmin):
    pass

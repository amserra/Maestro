from django.contrib import admin
from context.models import Fetcher, PostProcessor


@admin.register(PostProcessor)
class PostProcessors(admin.ModelAdmin):
    pass


@admin.register(Fetcher)
class Fetchers(admin.ModelAdmin):
    pass

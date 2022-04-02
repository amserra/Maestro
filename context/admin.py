from django.contrib import admin
from context.models import Fetcher, PostProcessor, Filter, Classifier


@admin.register(Fetcher)
class Fetchers(admin.ModelAdmin):
    pass


@admin.register(PostProcessor)
class PostProcessors(admin.ModelAdmin):
    pass


@admin.register(Filter)
class Filters(admin.ModelAdmin):
    pass


@admin.register(Classifier)
class Classifiers(admin.ModelAdmin):
    pass

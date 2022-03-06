from django.contrib import admin
from django.contrib.auth.models import Group
from taggit.admin import Tag

# Remove group from django admin
admin.site.unregister(Group)

# Remove taggit from django admin
admin.site.unregister(Tag)



from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from taggit.managers import TaggableManager


class Configuration(models.Model):
    # Perhaps more than one search string allowed?
    search_string = models.CharField(max_length=50, help_text='This field should be similar to what you would input on a search engine.')
    keywords = TaggableManager()


class SearchContext(models.Model):
    STATUS_CHOICES = [
        ('Finished', 'Finished'),
        ('Not configured', 'Not configured'),
        ('Running', 'Running'),
        ('Stopped', 'Stopped'),
    ]

    # Meta configurations
    code = models.CharField(max_length=30)  # unique for the user/organization. Created by the system based on the name
    name = models.CharField(max_length=30, blank=False)  # required
    description = models.TextField(blank=True)
    create_date = models.DateTimeField(auto_now_add=True)
    creator = models.ForeignKey(to='account.User', on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Not configured')

    # Owner of search context (can be User or Organization)
    owner_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    owner_id = models.PositiveIntegerField()
    owner = GenericForeignKey('owner_type', 'owner_id')

    # "Inner" configurations
    configuration = models.ForeignKey(to=Configuration, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.code

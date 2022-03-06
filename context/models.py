from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from taggit.managers import TaggableManager
from django.contrib.postgres.fields import ArrayField


COUNTRY_CHOICES = [('PT', 'Portugal'), ('US', 'United States')]


class Gatherer(models.Model):
    name = models.CharField(max_length=50)
    # Some gatherers may be incompatible with others. For example, to restrict API calls, we may only allow to use one of the bing/bing images/google
    incompatible_with = models.ManyToManyField(to="self", blank=True)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False, help_text='Tells if this gatherer is used by default (when a context doesn\'t have gatherers specified). A default gatherer is only used if it is active.')

    def __str__(self):
        return self.name


class ImagesConfiguration(models.Model):
    SMALL = 'Small'
    MEDIUM = 'Medium'
    LARGE = 'Large'
    IMAGES_SIZE_CHOICES = [
        (SMALL, 'Small'),
        (MEDIUM, 'Medium'),
        (LARGE, 'Large')
    ]

    size = models.CharField(max_length=10, choices=IMAGES_SIZE_CHOICES, null=True)

    min_width = models.IntegerField(blank=True)
    min_height = models.IntegerField(blank=True)
    max_width = models.IntegerField(blank=True)
    max_height = models.IntegerField(blank=True)
    height = models.IntegerField(blank=True)
    width = models.IntegerField(blank=True)


class AdvancedConfiguration(models.Model):
    country_of_search = models.CharField(max_length=2, choices=COUNTRY_CHOICES, default='PT', null=True)
    # freshness/date = ...
    seed_urls = ArrayField(models.URLField(), null=True)
    gatherers = models.ManyToManyField(to=Gatherer, blank=True)

    # Data-type-specific configurations
    images_configuration = models.ForeignKey(to=ImagesConfiguration, on_delete=models.SET_NULL, null=True)


class Configuration(models.Model):
    IMAGES = 'Images'
    DATA_TYPE_CHOICES = [
        (IMAGES, 'Images')
    ]

    # Essential configuration
    search_string = models.CharField(max_length=50, help_text='This field should be similar to what you would input on a search engine.')  # Perhaps more than one search string allowed?
    keywords = TaggableManager()
    data_type = models.CharField(max_length=10, choices=DATA_TYPE_CHOICES, help_text='Data type that will be gathered.')

    # Advanced configuration FK
    advanced_configuration = models.ForeignKey(to=AdvancedConfiguration, on_delete=models.SET_NULL, null=True)

    @property
    def context(self):
        return self.searchcontext_set.all()[0]


class SearchContext(models.Model):
    FINISHED = 'Finished'
    NOT_CONFIGURED = 'Not configured'
    READY = 'Ready'
    GATHERING_URLS = 'Gathering urls'
    RUNNING = 'Running'
    STOPPED = 'Stopped'
    STATUS_CHOICES = [
        (FINISHED, 'Finished'),
        (NOT_CONFIGURED, 'Not configured'),
        (READY, 'Ready'),
        (GATHERING_URLS, 'Gathering urls'),
        (RUNNING, 'Running'),
        (STOPPED, 'Stopped'),
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

    @property
    def owner_code(self):
        if self.owner_type.name == 'organization':
            return self.owner.code
        else:
            return self.owner.email

    def __str__(self):
        return self.code

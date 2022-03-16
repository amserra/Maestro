import os
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from taggit.managers import TaggableManager
from django.contrib.postgres.fields import ArrayField

# Hardcoded for now
THUMB_SIZE = (270, 270)
COUNTRY_CHOICES = [('PT', 'Portugal'), ('US', 'United States')]


def fetchers_path():
    return os.path.join(settings.BASE_DIR, 'fetchers')


class Fetcher(models.Model):
    PYTHON_SCRIPT = 'Python'
    SCRAPY_SCRIPT = 'Scrapy'
    FETCHER_TYPE = [
        (PYTHON_SCRIPT, 'Python script'),
        (SCRAPY_SCRIPT, 'Scrapy script'),
    ]

    name = models.CharField(max_length=50)
    # Some fetchers may be incompatible with others. For example, to restrict API calls, we may only allow to use one of the bing/bing images/google
    incompatible_with = models.ManyToManyField(to="self", blank=True)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False, help_text='Tells if this fetcher is used by default (when a context doesn\'t have fetchers specified). A default fetcher is only used if it is active.')
    type = models.CharField(max_length=20, choices=FETCHER_TYPE)
    path = models.FilePathField(path=fetchers_path, recursive=True, match='fetcher_*')
    # TODO: Ideally there's another field here: supported datatypes. Some fetchers (e.g.: bing image) don't make sense fetching some data types (e.g.: sounds). Since we are only supporting image data type for now, we can leave it like this

    def __str__(self):
        return self.name


class ImageConfiguration(models.Model):
    min_width = models.IntegerField(blank=True)
    min_height = models.IntegerField(blank=True)
    max_width = models.IntegerField(blank=True)
    max_height = models.IntegerField(blank=True)
    height = models.IntegerField(blank=True)
    width = models.IntegerField(blank=True)


class AdvancedConfiguration(models.Model):
    DEFAULT_COUNTRY_OF_SEARCH = 'PT'

    country_of_search = models.CharField(max_length=2, choices=COUNTRY_CHOICES, default=DEFAULT_COUNTRY_OF_SEARCH, null=True)
    # freshness/date = ...
    seed_urls = ArrayField(models.URLField(), null=True)
    fetchers = models.ManyToManyField(to=Fetcher, blank=True)
    post_processors = models.ManyToManyField(to='PostProcessor', blank=True)
    yield_after_gathering_data = models.BooleanField(default=True, help_text='Whether to stop or not after data is gathered. This is recommended to be on, because it will potentially allow for better results.')

    # Data-type-specific configurations
    # TODO: Ideally, this would be a generic foreign key to ImagesConfiguration, AudioConfiguration, etc. (a data-type specific configuration). Since we are only using images for now, we can leave it like this
    images_configuration = models.ForeignKey(to=ImageConfiguration, on_delete=models.SET_NULL, null=True)

    @property
    def context(self):
        return self.configuration_set.all()[0].context

    def __str__(self):
        return f'{self.context}\'s advanced configuration'


class Configuration(models.Model):
    IMAGES = 'IMAGES'
    DATA_TYPE_CHOICES = [
        (IMAGES, 'Images')
    ]

    # Essential configuration
    search_string = models.CharField(max_length=50, help_text='This field should be similar to what you would input on a search engine.')  # Perhaps more than one search string allowed?
    keywords = TaggableManager(help_text='A comma-separated list of words. Think of them as hashtags.')
    data_type = models.CharField(max_length=10, choices=DATA_TYPE_CHOICES, help_text='Data type that will be gathered.')

    # Advanced configuration FK
    advanced_configuration = models.ForeignKey(to=AdvancedConfiguration, on_delete=models.SET_NULL, null=True)

    @property
    def context(self):
        return self.searchcontext_set.all()[0]

    def __str__(self):
        return f'{self.context}\'s configuration'


class SearchContext(models.Model):
    NOT_CONFIGURED = 'NOT CONFIGURED'
    READY = 'READY'
    FETCHING_URLS = 'FETCHING'
    GATHERING_DATA = 'GATHERING'
    WAITING_DATA_REVISION = 'WAITING'
    STATUS_CHOICES = [
        (NOT_CONFIGURED, 'Not configured'),
        (READY, 'Ready'),
        (FETCHING_URLS, 'Fetching urls'),
        (GATHERING_DATA, 'Gathering data'),
        (WAITING_DATA_REVISION, 'Waiting data revision'),
    ]

    # Meta configurations
    code = models.CharField(max_length=30)  # unique for the user/organization. Created by the system based on the name
    name = models.CharField(max_length=30, blank=False)  # required
    description = models.TextField(blank=True)
    create_date = models.DateTimeField(auto_now_add=True)
    creator = models.ForeignKey(to='account.User', on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES)

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

    @property
    def context_folder(self):
        return os.path.join(settings.CONTEXTS_DATA_DIR, self.owner_code, self.code)

    @property
    def context_folder_media(self):
        return os.path.join(settings.MEDIA_ROOT, self.owner_code, self.code)

    @property
    def datastream(self):
        if self.imagedata_set.exists():
            return self.imagedata_set.all()
        # Other datatype cases
        else:
            return None

    def __str__(self):
        return self.code


def api_logs_path():
    return os.path.join(settings.LOGS_PATH, 'apis')


class APIResults(models.Model):
    """
        Caches API request queries. This prevents duplicate requests. Used only in a dev (settings.DEBUG=True) environment
        Not applicable to non-dev environments because they may require time-sensitive data
    """
    configuration = models.JSONField(encoder=DjangoJSONEncoder)
    fetcher = models.ForeignKey(to=Fetcher, on_delete=models.CASCADE)
    result_file = models.FilePathField(path=api_logs_path)

    def __str__(self):
        return f'API results for fetcher {self.fetcher}'


class Data(models.Model):
    metadata = models.JSONField(encoder=DjangoJSONEncoder, null=True)
    data = models.NOT_PROVIDED  # overriden in subclass
    context = models.ForeignKey(to=SearchContext, on_delete=models.CASCADE)
    add_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class ImageData(Data):
    data = models.FilePathField(max_length=200)
    data_thumb = models.FilePathField(max_length=200)
    data_thumb_media = models.FilePathField(max_length=200)


def post_processors_path():
    return os.path.join(settings.BASE_DIR, 'post_processors')


class PostProcessor(models.Model):
    """
    Represents a post-processor. A post-processor enhances the datastream, either the data objects themselves (e.g.: rotate all the images), or the metadata associated with each (e.g.: retrieve exif data).
    """
    PYTHON_SCRIPT = 'Python'
    POST_PROCESSOR_TYPE = [
        (PYTHON_SCRIPT, 'Python script'),
    ]

    DATA_MANIPULATION = 'DATA'
    METADATA_RETRIEVAL = 'METADATA'
    POST_PROCESSOR_KIND = [
        (DATA_MANIPULATION, 'Data manipulation'),
        (METADATA_RETRIEVAL, 'Metadata retrieval'),
    ]

    name = models.CharField(max_length=50)
    # Some fetchers may be incompatible with others. For example, to restrict API calls, we may only allow to use one of the bing/bing images/google
    is_active = models.BooleanField(default=True)
    type = models.CharField(max_length=20, choices=POST_PROCESSOR_TYPE)
    data_type = models.CharField(max_length=20, choices=Configuration.DATA_TYPE_CHOICES)
    kind = models.CharField(max_length=20, choices=POST_PROCESSOR_KIND)
    path = models.FilePathField(path=post_processors_path, recursive=True)
    # The supported data type (image/text/other), and the type of post-processor depend on the folder where the post-processor is stored

    def __str__(self):
        return self.name

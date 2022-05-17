from django.db import models
from django.core.exceptions import ValidationError


def validate_file_type(value):
    ext = value.name.split('.')[-1]
    if ext != 'py' and ext != 'zip':
        raise ValidationError('Please input a python (.py) or a zip (.zip) file.')


class SubmitPlugin(models.Model):
    submitter_name = models.CharField(max_length=50)
    submitter_email = models.EmailField()
    plugin_name = models.CharField(max_length=50)
    file = models.FileField(upload_to='plugins/', help_text='Python file.', validators=[validate_file_type])
    kind = models.CharField(max_length=50, choices=(('FETCHER', 'Fetcher'), ('POST_PROCESSOR', 'Post-processor'), ('FILTER', 'Filter'), ('CLASSIFIER', 'Classifier')))

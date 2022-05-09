import os
from django import template
from django.conf import settings

register = template.Library()


@register.filter
def getallattrs(value):
    return dir(value)


@register.filter
def underscore_to_space(value):
    return value.replace('_', ' ')


@register.filter
def space_to_underscore(value):
    return value.replace(' ', '_')


@register.filter
def addstr(arg1, arg2):
    """concatenate arg1 & arg2"""
    return str(arg1) + str(arg2)


@register.filter
def get_type(value):
    return value.__class__.__name__


@register.filter
def split_log(value):
    splitted = value.split(' ')
    date_time = f'{splitted[0]} {splitted[1]}'
    error = splitted[2] if 'error' in splitted[2].lower() else None
    if error:
        rest = splitted[3:]
        result = [date_time, error, ' '.join(rest)]
    else:
        rest = splitted[2:]
        result = [date_time, ' '.join(rest)]
    return result


@register.simple_tag
def get_mapbox_key():
    return settings.MAPBOX_KEY


@register.simple_tag
def get_arcgis_key():
    return settings.ARCGIS_KEY


@register.filter
def filename(value):
    return os.path.basename(value.file.name)

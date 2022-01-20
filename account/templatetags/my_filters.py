from django import template

register = template.Library()


@register.filter
def getallattrs(value):
    return dir(value)

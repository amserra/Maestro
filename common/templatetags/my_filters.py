from django import template

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

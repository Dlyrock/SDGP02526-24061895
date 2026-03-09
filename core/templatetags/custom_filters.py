from django import template
register = template.Library()

@register.filter
def dict_get(d, key):
    """Get value from dict by key"""
    return d.get(key, {})

@register.filter
def dict_keys(d):
    """Return dict keys as list"""
    return list(d.keys())

@register.filter
def dict_values(d):
    """Return dict values as list"""
    return list(d.values())
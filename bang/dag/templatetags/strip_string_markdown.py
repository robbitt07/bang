from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter()
@stringfilter
def strip_string_markdown(value):
    try:
        return str(value).rstrip()
    except:
        return str(value)
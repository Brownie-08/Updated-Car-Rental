from django import template
from django.forms import Widget

register = template.Library()

@register.filter
def add_class(field, css_class):
    """
    Add CSS class to form field widget
    Usage: {{ form.field|add_class:"my-class" }}
    """
    if hasattr(field, 'as_widget'):
        return field.as_widget(attrs={'class': css_class})
    return field

@register.filter
def add_attrs(field, attrs):
    """
    Add multiple attributes to form field widget
    Usage: {{ form.field|add_attrs:"class:my-class,placeholder:Enter text" }}
    """
    if not hasattr(field, 'as_widget'):
        return field
    
    attr_dict = {}
    for attr in attrs.split(','):
        if ':' in attr:
            key, value = attr.split(':', 1)
            attr_dict[key.strip()] = value.strip()
    
    return field.as_widget(attrs=attr_dict)

@register.filter
def field_type(field):
    """
    Get the field type/widget name
    Usage: {{ form.field|field_type }}
    """
    return field.field.widget.__class__.__name__

@register.filter
def is_checkbox(field):
    """
    Check if field is a checkbox
    Usage: {% if form.field|is_checkbox %}
    """
    return field.field.widget.__class__.__name__ == 'CheckboxInput'

@register.filter
def is_password(field):
    """
    Check if field is a password field
    Usage: {% if form.field|is_password %}
    """
    return field.field.widget.__class__.__name__ == 'PasswordInput'

@register.filter
def is_email(field):
    """
    Check if field is an email field
    Usage: {% if form.field|is_email %}
    """
    return field.field.widget.__class__.__name__ == 'EmailInput'

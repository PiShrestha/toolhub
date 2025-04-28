# toolhub/templatetags/form_tags.py
from django import template

register = template.Library()


@register.filter(name="add_class")
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})


@register.filter
def is_checkbox(field):
    return field.field.widget.__class__.__name__ == "CheckboxSelectMultiple"

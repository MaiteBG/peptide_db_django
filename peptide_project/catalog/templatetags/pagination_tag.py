# pagination_tags.py
from django import template

register = template.Library()


@register.inclusion_tag('shared/pagination.html')
def htmx_pagination(page_obj, target_id='#results', extra_query_params=''):
    return {
        'page_obj': page_obj,
        'target_id': target_id,
        'extra_query_params': extra_query_params,
    }

from django import template
from django.utils.html import format_html

register = template.Library()


@register.simple_tag
def tooltip_icon(text, aria_label="Help information"):
    html = f'''
    <span
      data-bs-toggle="tooltip"
      title="{text}"
      role="button"
      tabindex="0"
      aria-label="{aria_label}"
      style="cursor: pointer; font-size: 0.5rem; vertical-align: top; color: #0d6efd;"
    >
      <i class="bi bi-info-circle"></i>
    </span>
    '''
    return format_html(html)

from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def status_badge(status):
    colors = {
        'ACTIVE': 'danger',
        'MONITORING': 'warning',
        'RESOLVED': 'success',
        'CLOSED': 'secondary',
    }
    c = colors.get(status, 'secondary')
    return mark_safe(f'<span class="badge bg-{c}">{status}</span>')

@register.simple_tag
def severity_badge(severity):
    colors = {
        'LOW': 'info',
        'MODERATE': 'warning',
        'HIGH': 'danger',
        'CRITICAL': 'dark',
    }
    c = colors.get(severity, 'secondary')
    return mark_safe(f'<span class="badge bg-{c}">{severity}</span>')

@register.simple_tag
def alert_badge(level):
    colors = {
        'INFO': 'info',
        'WARNING': 'warning',
        'DANGER': 'danger',
        'CRITICAL': 'dark',
    }
    c = colors.get(level, 'secondary')
    return mark_safe(f'<span class="badge bg-{c}"><i class="bi bi-exclamation-triangle-fill me-1"></i>{level}</span>')

@register.simple_tag
def sensor_status_icon(status):
    icons = {
        'NORMAL': ('bi-check-circle-fill', 'text-success'),
        'WARNING': ('bi-exclamation-triangle-fill', 'text-warning'),
        'CRITICAL': ('bi-x-circle-fill', 'text-danger'),
        'OFFLINE': ('bi-dash-circle-fill', 'text-secondary'),
    }
    icon, cls = icons.get(status, ('bi-circle', 'text-secondary'))
    return mark_safe(f'<i class="bi {icon} {cls}"></i>')

@register.simple_tag
def role_badge(role):
    styles = {
        'LGU_ADMIN': ('danger', 'LGU Admin'),
        'DISPATCHER': ('warning text-dark', 'Dispatcher'),
        'PUBLIC': ('secondary', 'Public Viewer'),
    }
    cls, label = styles.get(role, ('secondary', role))
    return mark_safe(f'<span class="badge bg-{cls}">{label}</span>')
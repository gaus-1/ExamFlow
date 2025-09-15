from __future__ import annotations

from django.conf import settings

def inject_static_version(request):
    return {
        'STATIC_VERSION': getattr(settings, 'STATIC_VERSION', '1'),
    }

def static_version(request):
    """Алиас для совместимости"""
    return inject_static_version(request)

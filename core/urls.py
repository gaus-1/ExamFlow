"""
URL-маршруты для core приложения
"""

from django.urls import path
from django.http import HttpResponse
from django.conf import settings
from django.contrib.sitemaps import views as sitemap_views
from django.contrib.sitemaps import Sitemap
from learning.models import Subject  # type: ignore


class SubjectSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        try:
            return Subject.objects.filter(is_archived=False, is_primary=True).order_by('id')  # type: ignore
        except Exception:
            return Subject.objects.all().order_by('id')  # type: ignore

    def location(self, obj):  # type: ignore
        return f"/subject/{obj.id}/"


def robots_txt(_request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /accounts/",
        "Sitemap: %s/sitemap.xml" % getattr(settings, 'WEBSITE_URL', 'https://examflow.ru'),
        "Host: %s" % getattr(settings, 'WEBSITE_URL', 'https://examflow.ru'),
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")  # type: ignore


from . import api
from .ultra_simple_health import ultra_simple_health, minimal_health_check

urlpatterns = [
    # API для RAG-системы
    path('api/ai/query/', api.AIQueryView.as_view(), name='ai_query'),
    path('api/ai/search/', api.SearchView.as_view(), name='ai_search'),
    path('api/ai/stats/', api.VectorStoreStatsView.as_view(), name='vector_stats'),
    path('api/health/', api.HealthCheckView.as_view(), name='health_check'),

    # Health check endpoints (ультра-простые для Render)
    path('health/', ultra_simple_health, name='health_check_basic'),
    path('health/simple/', minimal_health_check, name='health_check_simple'),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('sitemap.xml', sitemap_views.sitemap, {'sitemaps': {'subjects': SubjectSitemap}}, name='sitemap'),
]

"""
URL-маршруты для core приложения
"""

from django.urls import path
from django.http import HttpResponse
from django.conf import settings
from django.contrib.sitemaps import views as sitemap_views
from django.contrib.sitemaps import Sitemap
from django.shortcuts import render
from django.shortcuts import redirect
from learning.models import Subject  # type: ignore
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView


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

class StaticSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return ["/", "/subjects/", "/faq/"]

    def location(self, item):
        return item


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


def faq_view(request):
    qa = {
        'Как подготовиться к ЕГЭ по математике (профильная)?': 'Решайте типовые задания 1–19, ведите список ошибок, изучайте критерии ФИПИ, тренируйтесь по времени. На сайте доступны разборы и видео.',
        'Как готовиться к ЕГЭ по русскому языку?': 'Отработайте структуру сочинения, аргументацию, повторите орфографию и пунктуацию. Используйте наши чек‑листы и примеры сочинений.',
        'Чем отличается ОГЭ от ЕГЭ по математике?': 'ОГЭ — базовый экзамен 9 класса с иным набором заданий и критериев. У нас есть отдельные страницы с разборами для ОГЭ.',
        'Где посмотреть типичные ошибки?': 'На страницах заданий мы выделяем частые ошибки и даём рекомендации, как их избегать.',
        'Есть ли видеоразборы?': 'Да, для сложных тем — видеоразборы с пошаговыми объяснениями.',
    }
    from . import seo as core_seo
    context = {
        'page_title': 'FAQ — ответы по подготовке к ЕГЭ/ОГЭ — ExamFlow',
        'page_description': 'Частые вопросы о подготовке к ЕГЭ/ОГЭ по математике и русскому: ошибки, критерии ФИПИ, видеоразборы.',
        'canonical_url': getattr(settings, 'WEBSITE_URL', 'https://examflow.ru') + '/faq/',
        'og_title': 'FAQ — ExamFlow',
        'og_description': 'Ответы на частые вопросы по ЕГЭ/ОГЭ (математика и русский).',
        'og_image': getattr(settings, 'WEBSITE_URL', 'https://examflow.ru') + '/static/images/logo-512.png',
        'og_url': getattr(settings, 'WEBSITE_URL', 'https://examflow.ru') + '/faq/',
        'twitter_title': 'FAQ — ExamFlow',
        'twitter_description': 'Частые вопросы по подготовке к ЕГЭ/ОГЭ.',
        'twitter_image': getattr(settings, 'WEBSITE_URL', 'https://examflow.ru') + '/static/images/logo-512.png',
        'jsonld': core_seo.jsonld_faq(qa),
        'qa': qa,
    }
    return render(request, 'faq.html', context)


from . import api  # noqa: E402
from .ultra_simple_health import ultra_simple_health, minimal_health_check  # noqa: E402
from core.rag_system.search_api import fipi_semantic_search  # noqa: E402
from core.rag_system.ai_api import (
    ai_ask, ai_subjects, ai_user_profile, 
    ai_problem_submit, ai_statistics
)  # noqa: E402

urlpatterns = [
    # API для RAG-системы
    path('api/ai/query/', api.AIQueryView.as_view(), name='ai_query'),
    path('api/ai/search/', api.SearchView.as_view(), name='ai_search'),
    path('api/ai/stats/', api.VectorStoreStatsView.as_view(), name='vector_stats'),
    path('api/health/', api.HealthCheckView.as_view(), name='health_check'),

    # Health check endpoints (ультра-простые для Render)
    path('health/', ultra_simple_health, name='health_check_basic'),
    path('health/simple/', minimal_health_check, name='health_check_simple'),
    path('health/minimal/', minimal_health_check, name='health_check_minimal'),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('sitemap.xml', sitemap_views.sitemap, {'sitemaps': {'subjects': SubjectSitemap, 'static': StaticSitemap}}, name='sitemap'),
    path('faq/', faq_view, name='faq'),
    path('api/fipi/search/', fipi_semantic_search, name='fipi_semantic_search'),
    
    # Новые AI API эндпоинты
    path('api/ai/ask/', ai_ask, name='ai_ask'),
    path('api/ai/subjects/', ai_subjects, name='ai_subjects'),
    path('api/ai/user/profile/', ai_user_profile, name='ai_user_profile'),
    path('api/ai/problem/submit/', ai_problem_submit, name='ai_problem_submit'),
    path('api/ai/statistics/', ai_statistics, name='ai_statistics'),
    
    # Страница подписки
    path('subscription/', lambda request: render(request, 'subscription.html'), name='subscription'),
    
    # API документация (Swagger/OpenAPI)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    # SEO-friendly ЧПУ (301) для ЕГЭ/ОГЭ: ведём на список предметов (без ломки текущих маршрутов)
    path('ege/matematika/', lambda r: redirect('/subjects/?utm=seo_ege_math', permanent=True)),
    path('ege/russkiy/', lambda r: redirect('/subjects/?utm=seo_ege_rus', permanent=True)),
    path('oge/matematika/', lambda r: redirect('/subjects/?utm=seo_oge_math', permanent=True)),
    path('oge/russkiy/', lambda r: redirect('/subjects/?utm=seo_oge_rus', permanent=True)),
]

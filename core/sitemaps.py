"""
Простые sitemap для ExamFlow
"""

from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    """Sitemap для статических страниц"""
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        return ['learning:home', 'learning:subjects_list']

    def location(self, item):
        return reverse(item)


class RootViewSitemap(Sitemap):
    """Sitemap для корневых страниц"""
    priority = 1.0
    changefreq = 'daily'

    def items(self):
        return ['/']

    def location(self, item):
        return item

from __future__ import annotations

from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return [
            "features",
            "pricing",
            "subscribe",
        ]

    def location(self, item):
        return reverse(item)


class RootViewSitemap(Sitemap):
    changefreq = "daily"
    priority = 1.0

    def items(self):
        return ["learning:home"] if self._has_learning_home() else ["features"]

    def location(self, item):
        return reverse(item)

    def _has_learning_home(self) -> bool:
        try:
            reverse("learning:home")
            return True
        except Exception:
            return False



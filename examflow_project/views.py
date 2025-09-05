"""
Обработчики ошибок для ExamFlow
"""

from django.shortcuts import render


def handler404(request, exception):
    """Обработчик 404 ошибки"""
    return render(request, '404.html', status=404)

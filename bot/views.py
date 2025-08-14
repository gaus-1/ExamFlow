from django.shortcuts import render
from django.http import JsonResponse
from .tasks import get_bot_status

def bot_control_panel(request):
    """Панель управления ботом"""
    status = get_bot_status()
    
    return render(request, 'bot/panel.html', {
        'status': status['status'],
        'pid': status.get('pid', 'N/A')
    })

def bot_api_status(request):
    """API для получения статуса бота"""
    status = get_bot_status()
    return JsonResponse(status)

"""
Административные представления для управления парсингом
Доступны без Console через веб-интерфейс
"""

import json
import threading
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
from django.core.management import call_command
from django.shortcuts import render
from core.models import Subject, Task
import logging

logger = logging.getLogger(__name__)

# Глобальные переменные для отслеживания статуса
_parsing_status = {
    'running': False,
    'progress': 0,
    'message': 'Готов к запуску',
    'last_update': None
}


def admin_panel(request):
    """Административная панель управления"""
    try:
        from core.models import Subject, Task
        subjects_count = Subject.objects.count()  # type: ignore
    except Exception:
        subjects_count = 0
    
    try:
        tasks_count = Task.objects.count()  # type: ignore
    except Exception:
        tasks_count = 0
    
    context = {
        'subjects_count': subjects_count,
        'tasks_count': tasks_count,
        'parsing_status': _parsing_status,
    }
    
    return render(request, 'admin/parsing_panel.html', context)


@csrf_exempt
@require_POST
def start_parsing(request):
    """API для запуска парсинга через веб-интерфейс"""
    global _parsing_status
    
    if _parsing_status['running']:
        return JsonResponse({
            'status': 'error',
            'message': 'Парсинг уже выполняется'
        })
    
    # Получаем параметры
    data = json.loads(request.body.decode('utf-8')) if request.body else {}
    quick_mode = data.get('quick', True)
    with_voices = data.get('with_voices', False)
    
    # Запускаем парсинг в фоновом потоке
    def run_parsing():
        global _parsing_status
        
        try:
            _parsing_status.update({
                'running': True,
                'progress': 0,
                'message': 'Запуск парсинга...'
            })
            
            logger.info("🚀 Запуск парсинга через веб-интерфейс")
            
            # Шаг 1: Миграции
            _parsing_status.update({
                'progress': 10,
                'message': 'Применение миграций...'
            })
            call_command('migrate', verbosity=0)
            
            # Шаг 2: Базовые данные
            _parsing_status.update({
                'progress': 20,
                'message': 'Загрузка базовых данных...'
            })
            call_command('load_sample_data', verbosity=0)
            
            # Шаг 3: Парсинг ФИПИ
            _parsing_status.update({
                'progress': 30,
                'message': f'Парсинг ФИПИ ({"быстрый" if quick_mode else "полный"} режим)...'
            })
            
            if quick_mode:
                call_command('parse_all_fipi', quick=True, verbosity=1)
            else:
                call_command('parse_all_fipi', verbosity=1)
            
            _parsing_status.update({
                'progress': 70,
                'message': 'Настройка webhook...'
            })
            
            # Шаг 4: Webhook
            try:
                call_command('setup_webhook', 'set', verbosity=0)
            except Exception as e:
                logger.warning(f"Ошибка webhook: {str(e)}")
            
            # Шаг 5: Голосовые подсказки (опционально)
            if with_voices:
                _parsing_status.update({
                    'progress': 80,
                    'message': 'Генерация голосовых подсказок...'
                })
                try:
                    call_command('generate_voices', limit=50, verbosity=0)
                except Exception as e:
                    logger.warning(f"Ошибка генерации голоса: {str(e)}")
            
            # Финиш
            from core.models import Subject, Task
            subjects_count = Subject.objects.count()  # type: ignore
            tasks_count = Task.objects.count()  # type: ignore
            
            _parsing_status.update({
                'running': False,
                'progress': 100,
                'message': f'Парсинг завершен! {subjects_count} предметов, {tasks_count} заданий'
            })
            
            logger.info(f"✅ Парсинг завершен: {subjects_count} предметов, {tasks_count} заданий")
            
        except Exception as e:
            _parsing_status.update({
                'running': False,
                'progress': 0,
                'message': f'Ошибка: {str(e)}'
            })
            logger.error(f"❌ Ошибка парсинга: {str(e)}")
    
    # Запускаем в отдельном потоке
    thread = threading.Thread(target=run_parsing, daemon=True)
    thread.start()
    
    return JsonResponse({
        'status': 'success',
        'message': 'Парсинг запущен в фоновом режиме'
    })


def parsing_status(request):
    """API для получения статуса парсинга"""
    return JsonResponse(_parsing_status)


@csrf_exempt
def trigger_parsing(request):
    """Простой endpoint для запуска парсинга одним запросом"""
    if request.method == 'GET':
        # Показываем простую форму
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>ExamFlow - Запуск парсинга</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial; margin: 40px; background: #f5f5f5; }
                .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
                button { background: #007cba; color: white; padding: 15px 30px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
                button:hover { background: #005a87; }
                .status { margin-top: 20px; padding: 15px; border-radius: 5px; }
                .loading { background: #fff3cd; border: 1px solid #ffeaa7; }
                .success { background: #d4edda; border: 1px solid #c3e6cb; }
                .error { background: #f8d7da; border: 1px solid #f5c6cb; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 ExamFlow - Запуск парсинга ФИПИ</h1>
                <p>Нажмите кнопку для запуска автоматического парсинга материалов ФИПИ.</p>
                
                <button onclick="startParsing()">🔥 Запустить быстрый парсинг</button>
                <button onclick="startFullParsing()">📚 Запустить полный парсинг</button>
                
                <div id="status"></div>
                
                <script>
                    function startParsing() {
                        fetch('/admin/start-parsing/', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({quick: true, with_voices: true})
                        })
                        .then(response => response.json())
                        .then(data => {
                            document.getElementById('status').innerHTML = 
                                '<div class="status loading">🔄 ' + data.message + '</div>';
                            checkStatus();
                        });
                    }
                    
                    function startFullParsing() {
                        fetch('/admin/start-parsing/', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({quick: false, with_voices: true})
                        })
                        .then(response => response.json())
                        .then(data => {
                            document.getElementById('status').innerHTML = 
                                '<div class="status loading">🔄 ' + data.message + '</div>';
                            checkStatus();
                        });
                    }
                    
                    function checkStatus() {
                        fetch('/admin/parsing-status/')
                        .then(response => response.json())
                        .then(data => {
                            const statusDiv = document.getElementById('status');
                            if (data.running) {
                                statusDiv.innerHTML = 
                                    '<div class="status loading">🔄 ' + data.message + ' (' + data.progress + '%)</div>';
                                setTimeout(checkStatus, 3000);
                            } else if (data.progress === 100) {
                                statusDiv.innerHTML = 
                                    '<div class="status success">✅ ' + data.message + '</div>';
                            } else if (data.message.includes('Ошибка')) {
                                statusDiv.innerHTML = 
                                    '<div class="status error">❌ ' + data.message + '</div>';
                            }
                        });
                    }
                </script>
            </div>
        </body>
        </html>
        """
        return HttpResponse(html_content.encode('utf-8'), content_type='text/html; charset=utf-8')
    
    elif request.method == 'POST':
        return start_parsing(request)

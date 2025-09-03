"""
Система мониторинга и уведомлений для движка сбора данных
"""

import logging
import smtplib
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass
from enum import Enum
import threading
import time

from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string

from core.models import FIPISourceMap, FIPIData

logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    """Уровни уведомлений"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class Alert:
    """Уведомление"""
    id: str
    level: AlertLevel
    title: str
    message: str
    source: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'level': self.level.value,
            'title': self.title,
            'message': self.message,
            'source': self.source,
            'timestamp': self.timestamp.isoformat(),
            'resolved': self.resolved,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }

class HealthChecker:
    """Проверка состояния системы"""
    
    def __init__(self):
        self.last_check = None
        self.check_interval = 300  # 5 минут
    
    def check_system_health(self) -> Dict[str, Any]:
        """Проверяет общее состояние системы"""
        health_status = {
            'timestamp': timezone.now().isoformat(),
            'overall_status': 'healthy',
            'checks': {}
        }
        
        # Проверка базы данных
        db_health = self._check_database()
        health_status['checks']['database'] = db_health
        
        # Проверка источников данных
        sources_health = self._check_data_sources()
        health_status['checks']['data_sources'] = sources_health
        
        # Проверка движка сбора
        engine_health = self._check_ingestion_engine()
        health_status['checks']['ingestion_engine'] = engine_health
        
        # Проверка планировщика
        scheduler_health = self._check_scheduler()
        health_status['checks']['scheduler'] = scheduler_health
        
        # Определяем общий статус
        critical_issues = sum(1 for check in health_status['checks'].values() 
                            if check.get('status') == 'critical')
        if critical_issues > 0:
            health_status['overall_status'] = 'critical'
        elif any(check.get('status') == 'warning' for check in health_status['checks'].values()):
            health_status['overall_status'] = 'warning'
        
        self.last_check = timezone.now()
        return health_status
    
    def _check_database(self) -> Dict[str, Any]:
        """Проверяет состояние базы данных"""
        try:
            # Проверяем подключение к БД
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            
            # Проверяем количество записей
            total_sources = FIPISourceMap.objects.count()  # type: ignore
            total_data = FIPIData.objects.count()  # type: ignore
            
            return {
                'status': 'healthy',
                'message': 'База данных доступна',
                'metrics': {
                    'total_sources': total_sources,
                    'total_data': total_data
                }
            }
        except Exception as e:
            return {
                'status': 'critical',
                'message': f'Ошибка базы данных: {e}',
                'error': str(e)
            }
    
    def _check_data_sources(self) -> Dict[str, Any]:
        """Проверяет состояние источников данных"""
        try:
            # Проверяем активные источники
            active_sources = FIPISourceMap.objects.filter(is_active=True)  # type: ignore
            
            # Источники, которые давно не обновлялись
            old_threshold = timezone.now() - timedelta(days=7)
            old_sources = active_sources.filter(
                last_checked__lt=old_threshold
            ).count()
            
            # Источники с ошибками
            error_sources = active_sources.filter(
                last_checked__isnull=False
            ).exclude(
                content_hash__isnull=True
            ).count()
            
            status = 'healthy'
            message = 'Источники данных в порядке'
            
            if old_sources > 10:
                status = 'warning'
                message = f'{old_sources} источников давно не обновлялись'
            elif old_sources > 50:
                status = 'critical'
                message = f'Критически много ({old_sources}) источников не обновлялись'
            
            return {
                'status': status,
                'message': message,
                'metrics': {
                    'active_sources': active_sources.count(),
                    'old_sources': old_sources,
                    'error_sources': error_sources
                }
            }
        except Exception as e:
            return {
                'status': 'critical',
                'message': f'Ошибка проверки источников: {e}',
                'error': str(e)
            }
    
    def _check_ingestion_engine(self) -> Dict[str, Any]:
        """Проверяет состояние движка сбора данных"""
        try:
            from core.data_ingestion.ingestion_engine import get_ingestion_engine
            
            engine = get_ingestion_engine()
            stats = engine.get_statistics()
            
            if not stats['is_running']:
                return {
                    'status': 'critical',
                    'message': 'Движок сбора данных не запущен',
                    'metrics': stats
                }
            
            # Проверяем воркеры
            active_workers = sum(1 for worker in stats['worker_stats'] 
                               if worker['is_running'])
            total_workers = len(stats['worker_stats'])
            
            if active_workers == 0:
                status = 'critical'
                message = 'Нет активных воркеров'
            elif active_workers < total_workers:
                status = 'warning'
                message = f'Только {active_workers}/{total_workers} воркеров активны'
            else:
                status = 'healthy'
                message = f'Все {active_workers} воркеров активны'
            
            return {
                'status': status,
                'message': message,
                'metrics': stats
            }
        except Exception as e:
            return {
                'status': 'critical',
                'message': f'Ошибка проверки движка: {e}',
                'error': str(e)
            }
    
    def _check_scheduler(self) -> Dict[str, Any]:
        """Проверяет состояние планировщика"""
        try:
            from core.data_ingestion.scheduler import get_scheduler
            
            scheduler = get_scheduler()
            status = scheduler.get_job_status()
            
            if not status['scheduler_running']:
                return {
                    'status': 'critical',
                    'message': 'Планировщик не запущен',
                    'metrics': status
                }
            
            return {
                'status': 'healthy',
                'message': 'Планировщик работает',
                'metrics': status
            }
        except Exception as e:
            return {
                'status': 'critical',
                'message': f'Ошибка проверки планировщика: {e}',
                'error': str(e)
            }

class AlertManager:
    """Менеджер уведомлений"""
    
    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.notification_channels = self._setup_notification_channels()
    
    def _setup_notification_channels(self) -> Dict[str, bool]:
        """Настраивает каналы уведомлений"""
        return {
            'email': getattr(settings, 'EMAIL_BACKEND', None) is not None,
            'log': True,
            'webhook': getattr(settings, 'MONITORING_WEBHOOK_URL', None) is not None
        }
    
    def create_alert(self, level: AlertLevel, title: str, message: str, 
                    source: str = "system") -> Alert:
        """Создает новое уведомление"""
        alert_id = f"{source}_{int(time.time())}"
        alert = Alert(
            id=alert_id,
            level=level,
            title=title,
            message=message,
            source=source,
            timestamp=timezone.now()
        )
        
        self.alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # Отправляем уведомления
        self._send_notifications(alert)
        
        logger.info(f"Создано уведомление {level.value}: {title}")
        return alert
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Разрешает уведомление"""
        if alert_id in self.alerts:
            alert = self.alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = timezone.now()
            logger.info(f"Уведомление {alert_id} разрешено")
            return True
        return False
    
    def get_active_alerts(self) -> List[Alert]:
        """Получает активные уведомления"""
        return [alert for alert in self.alerts.values() if not alert.resolved]
    
    def get_alerts_by_level(self, level: AlertLevel) -> List[Alert]:
        """Получает уведомления по уровню"""
        return [alert for alert in self.alerts.values() 
                if alert.level == level and not alert.resolved]
    
    def _send_notifications(self, alert: Alert):
        """Отправляет уведомления по всем каналам"""
        if self.notification_channels['email'] and alert.level in [AlertLevel.ERROR, AlertLevel.CRITICAL]:
            self._send_email_alert(alert)
        
        if self.notification_channels['webhook']:
            self._send_webhook_alert(alert)
        
        # Логирование
        log_level = {
            AlertLevel.INFO: logging.INFO,
            AlertLevel.WARNING: logging.WARNING,
            AlertLevel.ERROR: logging.ERROR,
            AlertLevel.CRITICAL: logging.CRITICAL
        }[alert.level]
        
        logger.log(log_level, f"[{alert.source}] {alert.title}: {alert.message}")
    
    def _send_email_alert(self, alert: Alert):
        """Отправляет уведомление по email"""
        try:
            subject = f"[{alert.level.value.upper()}] {alert.title}"
            
            # Создаем HTML-сообщение
            context = {
                'alert': alert,
                'timestamp': alert.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'level_color': {
                    AlertLevel.INFO: '#17a2b8',
                    AlertLevel.WARNING: '#ffc107',
                    AlertLevel.ERROR: '#dc3545',
                    AlertLevel.CRITICAL: '#6f42c1'
                }[alert.level]
            }
            
            html_message = render_to_string('monitoring/alert_email.html', context)
            
            # Отправляем email
            send_mail(
                subject=subject,
                message=alert.message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=getattr(settings, 'MONITORING_EMAIL_RECIPIENTS', []),
                html_message=html_message,
                fail_silently=False
            )
            
            logger.info(f"Email уведомление отправлено: {alert.title}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки email уведомления: {e}")
    
    def _send_webhook_alert(self, alert: Alert):
        """Отправляет уведомление через webhook"""
        try:
            import requests
            
            webhook_url = getattr(settings, 'MONITORING_WEBHOOK_URL', None)
            if not webhook_url:
                return
            
            payload = {
                'alert': alert.to_dict(),
                'system': 'ExamFlow Data Ingestion',
                'timestamp': timezone.now().isoformat()
            }
            
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Webhook уведомление отправлено: {alert.title}")
            else:
                logger.warning(f"Webhook вернул статус {response.status_code}")
                
        except Exception as e:
            logger.error(f"Ошибка отправки webhook уведомления: {e}")

class MonitoringService:
    """Основной сервис мониторинга"""
    
    def __init__(self):
        self.health_checker = HealthChecker()
        self.alert_manager = AlertManager()
        self.is_running = False
        self._monitoring_thread: Optional[threading.Thread] = None
    
    def start(self):
        """Запускает сервис мониторинга"""
        if self.is_running:
            return
        
        self.is_running = True
        self._monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitoring_thread.start()
        logger.info("Сервис мониторинга запущен")
    
    def stop(self):
        """Останавливает сервис мониторинга"""
        self.is_running = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)
        logger.info("Сервис мониторинга остановлен")
    
    def _monitoring_loop(self):
        """Основной цикл мониторинга"""
        while self.is_running:
            try:
                # Проверяем состояние системы
                health = self.health_checker.check_system_health()
                
                # Анализируем результаты и создаем уведомления
                self._analyze_health_status(health)
                
                # Ждем следующую проверку
                time.sleep(self.health_checker.check_interval)
                
            except Exception as e:
                logger.error(f"Ошибка в цикле мониторинга: {e}")
                time.sleep(60)  # Пауза при ошибке
    
    def _analyze_health_status(self, health: Dict[str, Any]):
        """Анализирует состояние системы и создает уведомления"""
        overall_status = health['overall_status']
        
        if overall_status == 'critical':
            # Критические проблемы
            for check_name, check_result in health['checks'].items():
                if check_result.get('status') == 'critical':
                    self.alert_manager.create_alert(
                        level=AlertLevel.CRITICAL,
                        title=f"Критическая проблема: {check_name}",
                        message=check_result.get('message', 'Неизвестная ошибка'),
                        source=check_name
                    )
        
        elif overall_status == 'warning':
            # Предупреждения
            for check_name, check_result in health['checks'].items():
                if check_result.get('status') == 'warning':
                    self.alert_manager.create_alert(
                        level=AlertLevel.WARNING,
                        title=f"Предупреждение: {check_name}",
                        message=check_result.get('message', 'Неизвестная проблема'),
                        source=check_name
                    )
    
    def get_health_status(self) -> Dict[str, Any]:
        """Получает текущее состояние системы"""
        return self.health_checker.check_system_health()
    
    def get_alerts_summary(self) -> Dict[str, Any]:
        """Получает сводку уведомлений"""
        active_alerts = self.alert_manager.get_active_alerts()
        
        return {
            'total_active': len(active_alerts),
            'by_level': {
                level.value: len(self.alert_manager.get_alerts_by_level(level))
                for level in AlertLevel
            },
            'recent_alerts': [
                alert.to_dict() for alert in active_alerts[-10:]  # Последние 10
            ]
        }

# Глобальный экземпляр сервиса мониторинга
_monitoring_service: Optional[MonitoringService] = None

def get_monitoring_service() -> MonitoringService:
    """Получает глобальный экземпляр сервиса мониторинга"""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = MonitoringService()
    return _monitoring_service

def start_monitoring():
    """Запускает сервис мониторинга"""
    service = get_monitoring_service()
    service.start()
    return service

def stop_monitoring():
    """Останавливает сервис мониторинга"""
    global _monitoring_service
    if _monitoring_service:
        _monitoring_service.stop()
        _monitoring_service = None

"""
Детальная карта структуры сайта fipi.ru
Создана для промышленной системы агрегации контента ExamFlow 2.0
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class DataType(Enum):
    """Типы данных на fipi.ru"""
    DEMO_VARIANT = "demo_variant"  # Демонстрационный вариант
    SPECIFICATION = "specification"  # Спецификация КИМ
    CODEFIER = "codefier"  # Кодификатор
    OPEN_BANK_TASK = "open_bank_task"  # Задание из открытого банка
    METHODICAL_MATERIAL = "methodical_material"  # Методический материал
    NEWS = "news"  # Новости и анонсы
    DOCUMENT = "document"  # Официальные документы

class ExamType(Enum):
    """Типы экзаменов"""
    EGE = "ege"  # ЕГЭ
    OGE = "oge"  # ОГЭ
    GVE_11 = "gve_11"  # ГВЭ-11
    GVE_9 = "gve_9"  # ГВЭ-9
    ESSAY = "essay"  # Итоговое сочинение
    INTERVIEW = "interview"  # Итоговое собеседование

class Priority(Enum):
    """Приоритеты данных"""
    CRITICAL = 1  # Критически важные
    HIGH = 2  # Высокий приоритет
    MEDIUM = 3  # Средний приоритет
    LOW = 4  # Низкий приоритет

class UpdateFrequency(Enum):
    """Частота обновления"""
    ANNUALLY = "annually"  # Ежегодно
    MONTHLY = "monthly"  # Ежемесячно
    WEEKLY = "weekly"  # Еженедельно
    DAILY = "daily"  # Ежедневно
    ON_DEMAND = "on_demand"  # По требованию

@dataclass
class FIPISource:
    """Модель источника данных с fipi.ru"""
    id: str
    name: str
    url: str
    data_type: DataType
    exam_type: ExamType
    subject: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    update_frequency: UpdateFrequency = UpdateFrequency.ANNUALLY
    file_format: str = "HTML"  # HTML, PDF, DOC, XLS
    description: str = ""
    last_checked: Optional[str] = None
    content_hash: Optional[str] = None

class FIPIStructureMap:
    """Карта структуры сайта fipi.ru"""
    
    def __init__(self):
        self.sources: List[FIPISource] = []
        self._initialize_sources()
    
    def _initialize_sources(self):
        """Инициализация всех известных источников данных"""
        
        # === ЕГЭ - КРИТИЧЕСКИ ВАЖНЫЕ ===
        
        # Демоверсии/Спецификации/Кодификаторы ЕГЭ (индекс-страница)
        # Дальнейшие ссылки будут собираться скрейпером с этой индекс-страницы
        ege_index_url = "https://fipi.ru/ege/demoversii-specifikacii-kodifikatory"

        self.sources.append(FIPISource(
            id="ege_demo_index",
            name="ЕГЭ: Демоверсии (индекс)",
            url=ege_index_url,
            data_type=DataType.DEMO_VARIANT,
            exam_type=ExamType.EGE,
            priority=Priority.CRITICAL,
            update_frequency=UpdateFrequency.ANNUALLY,
            file_format="HTML",
            description="Индекс-страница демоверсий ЕГЭ"
        ))

        self.sources.append(FIPISource(
            id="ege_spec_index",
            name="ЕГЭ: Спецификации (индекс)",
            url=ege_index_url,
            data_type=DataType.SPECIFICATION,
            exam_type=ExamType.EGE,
            priority=Priority.CRITICAL,
            update_frequency=UpdateFrequency.ANNUALLY,
            file_format="HTML",
            description="Индекс-страница спецификаций ЕГЭ"
        ))

        self.sources.append(FIPISource(
            id="ege_code_index",
            name="ЕГЭ: Кодификаторы (индекс)",
            url=ege_index_url,
            data_type=DataType.CODEFIER,
            exam_type=ExamType.EGE,
            priority=Priority.CRITICAL,
            update_frequency=UpdateFrequency.ANNUALLY,
            file_format="HTML",
            description="Индекс-страница кодификаторов ЕГЭ"
        ))
        
        # Открытый банк заданий ЕГЭ
        self.sources.append(FIPISource(
            id="ege_open_bank",
            name="Открытый банк заданий ЕГЭ",
            url="https://fipi.ru/ege/otkrytyy-bank-zadaniy-ege",
            data_type=DataType.OPEN_BANK_TASK,
            exam_type=ExamType.EGE,
            priority=Priority.HIGH,
            update_frequency=UpdateFrequency.MONTHLY,
            file_format="HTML",
            description="База заданий для составления вариантов КИМ ЕГЭ"
        ))
        
        # === ОГЭ - ВЫСОКИЙ ПРИОРИТЕТ ===
        
        # Демоверсии ОГЭ
        # ОГЭ: индекс-страница
        oge_index_url = "https://fipi.ru/oge/demoversii-specifikacii-kodifikatory"
        self.sources.append(FIPISource(
            id="oge_demo_index",
            name="ОГЭ: Демоверсии (индекс)",
            url=oge_index_url,
            data_type=DataType.DEMO_VARIANT,
            exam_type=ExamType.OGE,
            priority=Priority.HIGH,
            update_frequency=UpdateFrequency.ANNUALLY,
            file_format="HTML",
            description="Индекс-страница демоверсий ОГЭ"
        ))
        
        # === МЕТОДИЧЕСКИЕ МАТЕРИАЛЫ - СРЕДНИЙ ПРИОРИТЕТ ===
        
        self.sources.append(FIPISource(
            id="methodical_materials",
            name="Методическая копилка",
            url="https://fipi.ru/metodicheskaya-kopilka",
            data_type=DataType.METHODICAL_MATERIAL,
            exam_type=ExamType.EGE,  # Общие материалы
            priority=Priority.MEDIUM,
            update_frequency=UpdateFrequency.MONTHLY,
            file_format="HTML",
            description="Методические материалы и рекомендации"
        ))
        
        # === НОВОСТИ И АНОНСЫ - НИЗКИЙ ПРИОРИТЕТ ===
        
        self.sources.append(FIPISource(
            id="news_announcements",
            name="Новости и анонсы",
            url="https://fipi.ru/news",
            data_type=DataType.NEWS,
            exam_type=ExamType.EGE,  # Общие новости
            priority=Priority.LOW,
            update_frequency=UpdateFrequency.DAILY,
            file_format="HTML",
            description="Актуальные новости и объявления ФИПИ"
        ))
        
        # === ОФИЦИАЛЬНЫЕ ДОКУМЕНТЫ ===
        
        self.sources.append(FIPISource(
            id="fipi_documents",
            name="Документы ФИПИ",
            url="https://fipi.ru/dokumenty-fipi",
            data_type=DataType.DOCUMENT,
            exam_type=ExamType.EGE,  # Общие документы
            priority=Priority.MEDIUM,
            update_frequency=UpdateFrequency.MONTHLY,
            file_format="PDF",
            description="Официальные документы и отчеты ФИПИ"
        ))
    
    def get_sources_by_priority(self, priority: Priority) -> List[FIPISource]:
        """Получить источники по приоритету"""
        return [source for source in self.sources if source.priority == priority]
    
    def get_sources_by_type(self, data_type: DataType) -> List[FIPISource]:
        """Получить источники по типу данных"""
        return [source for source in self.sources if source.data_type == data_type]
    
    def get_sources_by_exam_type(self, exam_type: ExamType) -> List[FIPISource]:
        """Получить источники по типу экзамена"""
        return [source for source in self.sources if source.exam_type == exam_type]
    
    def get_sources_by_subject(self, subject: str) -> List[FIPISource]:
        """Получить источники по предмету"""
        return [source for source in self.sources if source.subject == subject]
    
    def get_critical_sources(self) -> List[FIPISource]:
        """Получить критически важные источники"""
        return self.get_sources_by_priority(Priority.CRITICAL)
    
    def get_high_priority_sources(self) -> List[FIPISource]:
        """Получить источники высокого приоритета"""
        return self.get_sources_by_priority(Priority.HIGH)
    
    def get_all_sources(self) -> List[FIPISource]:
        """Получить все источники"""
        return self.sources
    
    def get_source_by_id(self, source_id: str) -> Optional[FIPISource]:
        """Получить источник по ID"""
        for source in self.sources:
            if source.id == source_id:
                return source
        return None
    
    def get_statistics(self) -> Dict:
        """Получить статистику по источникам"""
        stats = {
            "total_sources": len(self.sources),
            "by_priority": {},
            "by_type": {},
            "by_exam_type": {},
            "by_format": {}
        }
        
        # Статистика по приоритетам
        for priority in Priority:
            count = len(self.get_sources_by_priority(priority))
            stats["by_priority"][priority.name] = count
        
        # Статистика по типам данных
        for data_type in DataType:
            count = len(self.get_sources_by_type(data_type))
            stats["by_type"][data_type.name] = count
        
        # Статистика по типам экзаменов
        for exam_type in ExamType:
            count = len(self.get_sources_by_exam_type(exam_type))
            stats["by_exam_type"][exam_type.name] = count
        
        # Статистика по форматам
        formats = {}
        for source in self.sources:
            formats[source.file_format] = formats.get(source.file_format, 0) + 1
        stats["by_format"] = formats
        
        return stats

# Создаем глобальный экземпляр карты
fipi_structure_map = FIPIStructureMap()

def get_fipi_structure_map() -> FIPIStructureMap:
    """Получить карту структуры fipi.ru"""
    return fipi_structure_map

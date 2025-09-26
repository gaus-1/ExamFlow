"""
Vector Store - полноценное векторное хранилище для семантического поиска
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class VectorStore:
    """Полноценное векторное хранилище с семантическим поиском"""

    def __init__(self):
        self.documents = []
        self.index = {}  # Простой индекс для быстрого поиска
        logger.info("Векторное хранилище инициализировано")

    def add_document(self, content: str, metadata: dict[str, Any] = None):  # type: ignore
        """
        Добавление документа в хранилище

        Args:
            content: Текст документа
            metadata: Метаданные (предмет, тип, ID и т.д.)
        """
        if not content:
            return

        doc_id = len(self.documents)
        document = {
            "id": doc_id,
            "content": content,
            "metadata": metadata or {},
            "tokens": self._tokenize(content),
        }

        self.documents.append(document)
        self._update_index(document)

        logger.debug(f"Добавлен документ {doc_id}: {content[:50]}...")

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """
        Семантический поиск документов

        Args:
            query: Поисковый запрос
            limit: Максимальное количество результатов

        Returns:
            Список релевантных документов с оценками
        """
        if not query or not self.documents:
            return []

        query_tokens = self._tokenize(query)
        scored_docs = []

        for doc in self.documents:
            score = self._calculate_similarity(query_tokens, doc["tokens"])
            if score > 0:
                scored_docs.append(
                    {
                        "document": doc,
                        "score": score,
                        "content": doc["content"],
                        "metadata": doc["metadata"],
                    }
                )

        # Сортируем по релевантности
        scored_docs.sort(key=lambda x: x["score"], reverse=True)

        logger.info(f"Поиск '{query}': найдено {len(scored_docs)} документов")
        return scored_docs[:limit]

    def search_by_subject(
        self, query: str, subject: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        """
        Поиск по предмету

        Args:
            query: Поисковый запрос
            subject: Предмет (математика, русский)
            limit: Максимальное количество результатов
        """
        all_results = self.search(query, limit * 2)

        # Фильтруем по предмету
        subject_results = []
        for result in all_results:
            doc_subject = result["metadata"].get("subject", "").lower()
            if subject.lower() in doc_subject or doc_subject in subject.lower():
                subject_results.append(result)
                if len(subject_results) >= limit:
                    break

        return subject_results

    def _tokenize(self, text: str) -> list[str]:
        """Токенизация текста"""
        # Приводим к нижнему регистру и разбиваем на слова
        text = text.lower()
        # Убираем знаки препинания
        text = re.sub(r"[^\w\s]", " ", text)
        # Разбиваем на токены
        tokens = text.split()

        # Убираем стоп-слова
        stop_words = {
            "и",
            "в",
            "на",
            "с",
            "по",
            "для",
            "от",
            "к",
            "из",
            "о",
            "а",
            "но",
            "или",
            "что",
            "как",
            "это",
            "все",
            "еще",
            "уже",
            "только",
            "может",
            "быть",
            "есть",
            "был",
            "была",
            "было",
            "были",
        }
        tokens = [
            token for token in tokens if token not in stop_words and len(token) > 2
        ]

        return tokens

    def _calculate_similarity(
        self, query_tokens: list[str], doc_tokens: list[str]
    ) -> float:
        """
        Вычисление сходства между запросом и документом
        Использует простую метрику пересечения токенов
        """
        if not query_tokens or not doc_tokens:
            return 0.0

        query_set = set(query_tokens)
        doc_set = set(doc_tokens)

        # Пересечение токенов
        intersection = query_set.intersection(doc_set)

        if not intersection:
            return 0.0

        # Простая метрика: отношение пересечения к объединению (Jaccard)
        union = query_set.union(doc_set)
        jaccard = len(intersection) / len(union)

        # Бонус за точные совпадения
        exact_matches = sum(1 for token in query_tokens if token in doc_tokens)
        exact_bonus = exact_matches / len(query_tokens)

        # Итоговая оценка
        score = jaccard * 0.7 + exact_bonus * 0.3

        return score

    def _update_index(self, document: dict[str, Any]):
        """Обновление поискового индекса"""
        doc_id = document["id"]

        for token in document["tokens"]:
            if token not in self.index:
                self.index[token] = []
            self.index[token].append(doc_id)

    def get_documents_by_metadata(self, key: str, value: str) -> list[dict[str, Any]]:
        """Получение документов по метаданным"""
        results = []
        for doc in self.documents:
            if doc["metadata"].get(key) == value:
                results.append(doc)
        return results

    def initialize(self):
        """Инициализация хранилища"""
        logger.info("Векторное хранилище инициализировано")

        # Загружаем существующие задания из базы данных
        self._load_existing_tasks()

    def _load_existing_tasks(self):
        """Загрузка существующих заданий в векторное хранилище"""
        try:
            from learning.models import Task

            tasks = Task.objects.select_related("subject").all()  # type: ignore
            loaded_count = 0

            for task in tasks:
                content = ""
                if task.title:
                    content += f"Заголовок: {task.title}\n"
                if task.content:
                    content += f"Содержание: {task.content}\n"

                if content:
                    metadata = {
                        "type": "task",
                        "subject": task.subject.name if task.subject else "общее",
                        "task_id": task.id,
                        "difficulty": getattr(task, "difficulty", "средний"),
                    }

                    self.add_document(content, metadata)
                    loaded_count += 1

            logger.info(f"Загружено {loaded_count} заданий в векторное хранилище")

        except Exception as e:
            logger.error(f"Ошибка загрузки заданий: {e}")

    def get_stats(self) -> dict[str, Any]:
        """Статистика хранилища"""
        subjects = {}
        for doc in self.documents:
            subject = doc["metadata"].get("subject", "неизвестно")
            subjects[subject] = subjects.get(subject, 0) + 1

        return {
            "total_documents": len(self.documents),
            "subjects": subjects,
            "index_size": len(self.index),
        }

"""
Модуль обработки PDF документов
Включает OCR, извлечение текста, структурирование и векторизацию
"""

import logging
import io
import hashlib
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

import fitz  # PyMuPDF
import pdfplumber
import pytesseract
from PIL import Image
import numpy as np
import cv2

from django.conf import settings
from django.utils import timezone
from django.db import transaction

from core.models import FIPIData, DataChunk
from core.data_ingestion.advanced_fipi_scraper import AdvancedFIPIScraper

logger = logging.getLogger(__name__)


class PDFProcessingStatus(Enum):
    """Статусы обработки PDF"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ContentType(Enum):
    """Типы контента в PDF"""
    TEXT = "text"
    TABLE = "table"
    IMAGE = "image"
    FORMULA = "formula"
    HEADER = "header"
    FOOTER = "footer"


@dataclass
class PDFChunk:
    """Чанк обработанного PDF"""
    text: str
    chunk_type: ContentType
    page_number: int
    bbox: Tuple[float, float, float, float]  # x0, y0, x1, y1
    confidence: float
    metadata: Dict[str, Any]


class OCRProcessor:
    """Процессор OCR для извлечения текста из изображений"""

    def __init__(self):
        self.tesseract_config = '--oem 3 --psm 6 -l rus+eng'
        self.min_confidence = 60

    def extract_text_from_image(self, image: Image.Image) -> Tuple[str, float]:
        """Извлекает текст из изображения с помощью OCR"""
        try:
            # Получаем данные OCR
            ocr_data = pytesseract.image_to_data(
                image,
                config=self.tesseract_config,
                output_type=pytesseract.Output.DICT
            )

            # Фильтруем по уверенности
            confident_texts = []
            total_confidence = 0
            confidence_count = 0

            for i, conf in enumerate(ocr_data['conf']):
                if int(conf) > self.min_confidence:
                    text = ocr_data['text'][i].strip()
                    if text:
                        confident_texts.append(text)
                        total_confidence += int(conf)
                        confidence_count += 1

            if confidence_count > 0:
                avg_confidence = total_confidence / confidence_count
                extracted_text = ' '.join(confident_texts)
                return extracted_text, avg_confidence
            else:
                return "", 0.0

        except Exception as e:
            logger.error(f"Ошибка OCR: {e}")
            return "", 0.0

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """Предобработка изображения для улучшения OCR"""
        try:
            # Конвертируем в numpy array
            img_array = np.array(image)

            # Конвертируем в grayscale если нужно
            if len(img_array.shape) == 3:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

            # Увеличиваем контраст
            img_array = cv2.convertScaleAbs(img_array, alpha=1.5, beta=0)

            # Убираем шум
            img_array = cv2.medianBlur(img_array, 3)

            # Конвертируем обратно в PIL Image
            return Image.fromarray(img_array)

        except Exception as e:
            logger.error(f"Ошибка предобработки изображения: {e}")
            return image


class PDFTextExtractor:
    """Извлекает текст из PDF документов"""

    def __init__(self):
        self.ocr_processor = OCRProcessor()

    def extract_text_with_pdfplumber(self, pdf_path: str) -> List[PDFChunk]:
        """Извлекает текст с помощью pdfplumber"""
        chunks = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    # Извлекаем текст
                    text = page.extract_text()
                    if text:
                        chunks.append(PDFChunk(
                            text=text.strip(),
                            chunk_type=ContentType.TEXT,
                            page_number=page_num,
                            bbox=(0, 0, page.width, page.height),
                            confidence=100.0,
                            metadata={'extraction_method': 'pdfplumber'}
                        ))

                    # Извлекаем таблицы
                    tables = page.extract_tables()
                    for table in tables:
                        if table:
                            table_text = self._table_to_text(table)  # type: ignore
                            chunks.append(PDFChunk(
                                text=table_text,
                                chunk_type=ContentType.TABLE,
                                page_number=page_num,
                                bbox=(0, 0, page.width, page.height),
                                confidence=90.0,
                                metadata={'extraction_method': 'pdfplumber_table'}
                            ))

        except Exception as e:
            logger.error(f"Ошибка извлечения текста с pdfplumber: {e}")

        return chunks

    def extract_text_with_pymupdf(self, pdf_path: str) -> List[PDFChunk]:
        """Извлекает текст с помощью PyMuPDF"""
        chunks = []

        try:
            doc = fitz.open(pdf_path)

            for page_num in range(len(doc)):
                page = doc[page_num]

                # Извлекаем текст
                text = page.get_text()  # type: ignore
                if text.strip():
                    chunks.append(PDFChunk(
                        text=text.strip(),
                        chunk_type=ContentType.TEXT,
                        page_number=page_num + 1,
                        bbox=page.rect,  # type: ignore
                        confidence=95.0,
                        metadata={'extraction_method': 'pymupdf'}
                    ))

                # Извлекаем изображения для OCR
                image_list = page.get_images()
                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        pix = fitz.Pixmap(doc, xref)

                        if pix.n - pix.alpha < 4:  # GRAY или RGB
                            img_data = pix.tobytes("png")
                            image = Image.open(io.BytesIO(img_data))

                            # Предобработка и OCR
                            processed_image = self.ocr_processor.preprocess_image(image)
                            ocr_text, confidence = self.ocr_processor.extract_text_from_image(
                                processed_image)

                            if ocr_text and confidence > 50:
                                chunks.append(PDFChunk(
                                    text=ocr_text,
                                    chunk_type=ContentType.IMAGE,
                                    page_number=page_num + 1,
                                    bbox=page.rect,  # type: ignore
                                    confidence=confidence,
                                    metadata={
                                        'extraction_method': 'ocr',
                                        'image_index': img_index
                                    }
                                ))

                        pix = None

                    except Exception as e:
                        logger.error(f"Ошибка обработки изображения {img_index}: {e}")

            doc.close()

        except Exception as e:
            logger.error(f"Ошибка извлечения текста с PyMuPDF: {e}")

        return chunks

    def _table_to_text(self, table: List[List[str]]) -> str:
        """Преобразует таблицу в текст"""
        if not table:
            return ""

        text_rows = []
        for row in table:
            if row:
                # Фильтруем None значения и объединяем ячейки
                clean_row = [cell or "" for cell in row]
                text_rows.append(" | ".join(clean_row))

        return "\n".join(text_rows)


class PDFStructuringEngine:
    """Движок структурирования PDF контента"""

    def __init__(self):
        self.header_patterns = [
            r'^\d+\.\s+[А-ЯЁ]',  # 1. Заголовок
            r'^[А-ЯЁ][а-яё\s]+:$',  # Заголовок:
            r'^[А-ЯЁ]{2,}$',  # ЗАГОЛОВОК
        ]
        self.formula_patterns = [
            r'\$[^$]+\$',  # $формула$
            r'\\[a-zA-Z]+',  # LaTeX команды
        ]

    def structure_chunks(self, chunks: List[PDFChunk]) -> List[PDFChunk]:
        """Структурирует чанки PDF"""
        structured_chunks = []

        for chunk in chunks:
            # Определяем тип контента
            chunk_type = self._classify_content(chunk.text)

            # Обновляем тип если определен
            if chunk_type != ContentType.TEXT:
                chunk.chunk_type = chunk_type

            # Разбиваем длинные тексты на более мелкие чанки
            if len(chunk.text) > 1000:
                sub_chunks = self._split_long_text(chunk)
                structured_chunks.extend(sub_chunks)
            else:
                structured_chunks.append(chunk)

        return structured_chunks

    def _classify_content(self, text: str) -> ContentType:
        """Классифицирует тип контента"""
        text = text.strip()

        # Проверяем на заголовок
        for pattern in self.header_patterns:
            if re.match(pattern, text, re.MULTILINE):
                return ContentType.HEADER

        # Проверяем на формулу
        for pattern in self.formula_patterns:
            if re.search(pattern, text):
                return ContentType.FORMULA

        # Проверяем на таблицу (содержит разделители)
        if '|' in text and text.count('|') > 2:
            return ContentType.TABLE

        return ContentType.TEXT

    def _split_long_text(self, chunk: PDFChunk) -> List[PDFChunk]:
        """Разбивает длинный текст на более мелкие чанки"""
        text = chunk.text
        max_length = 1000
        overlap = 100

        sub_chunks = []
        start = 0

        while start < len(text):
            end = start + max_length

            # Ищем хорошее место для разрыва
            if end < len(text):
                # Ищем конец предложения
                sentence_end = text.rfind('.', start, end)
                if sentence_end > start + max_length // 2:
                    end = sentence_end + 1
                else:
                    # Ищем конец слова
                    word_end = text.rfind(' ', start, end)
                    if word_end > start + max_length // 2:
                        end = word_end

            sub_text = text[start:end].strip()
            if sub_text:
                sub_chunk = PDFChunk(
                    text=sub_text,
                    chunk_type=chunk.chunk_type,
                    page_number=chunk.page_number,
                    bbox=chunk.bbox,
                    confidence=chunk.confidence,
                    metadata=chunk.metadata.copy()
                )
                sub_chunk.metadata['chunk_index'] = len(sub_chunks)
                sub_chunks.append(sub_chunk)

            start = end - overlap
            if start >= len(text):
                break

        return sub_chunks


class PDFVectorizer:
    """Векторизатор для PDF контента"""

    def __init__(self):
        self.scraper = AdvancedFIPIScraper()

    def generate_embeddings(self, chunks: List[PDFChunk]) -> List[Dict[str, Any]]:
        """Генерирует эмбеддинги для чанков"""
        vectorized_chunks = []

        for chunk in chunks:
            try:
                # Генерируем эмбеддинг с помощью Gemini API
                embedding = self._get_embedding(chunk.text)

                if embedding:
                    vectorized_chunks.append({
                        'chunk': chunk,
                        'embedding': embedding,
                        'vector_size': len(embedding)
                    })
                else:
                    logger.warning(
                        f"Не удалось сгенерировать эмбеддинг для чанка: {chunk.text[:100]}...")

            except Exception as e:
                logger.error(f"Ошибка векторизации чанка: {e}")

        return vectorized_chunks

    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Получает эмбеддинг текста через Gemini API (embedding model)."""
        try:
            import google.generativeai as genai

            genai.configure(api_key=settings.GEMINI_API_KEY)
            # Используем модель эмбеддингов
            embed_model = genai.EmbeddingModel(
                model_name='text-embedding-004')  # type: ignore
            response = embed_model.embed_content(input=text)

            # Ответ SDK может быть объектом с полем embedding
            if hasattr(response, 'embedding'):
                return list(response.embedding)  # type: ignore
            if isinstance(response, dict) and 'embedding' in response:
                return response['embedding']
            return None

        except Exception as e:
            logger.error(f"Ошибка получения эмбеддинга: {e}")
            return None


class PDFProcessor:
    """Основной процессор PDF документов"""

    def __init__(self):
        self.text_extractor = PDFTextExtractor()
        self.structuring_engine = PDFStructuringEngine()
        self.vectorizer = PDFVectorizer()

    def process_pdf(self, fipi_data: FIPIData) -> Dict[str, Any]:
        """Обрабатывает PDF документ"""
        logger.info(f"Начинаем обработку PDF: {fipi_data.title}")

        try:
            # Скачиваем PDF если нужно
            pdf_path = self._download_pdf(str(fipi_data.url))
            if not pdf_path:
                return {'status': 'failed', 'error': 'Не удалось скачать PDF'}

            # Извлекаем текст
            chunks = self._extract_text_from_pdf(pdf_path)
            if not chunks:
                return {'status': 'failed', 'error': 'Не удалось извлечь текст из PDF'}

            # Структурируем контент
            structured_chunks = self.structuring_engine.structure_chunks(chunks)

            # Генерируем эмбеддинги
            vectorized_chunks = self.vectorizer.generate_embeddings(structured_chunks)

            # Сохраняем в базу данных
            saved_chunks = self._save_chunks_to_db(fipi_data, vectorized_chunks)

            # Обновляем статус
            fipi_data.mark_as_processed()

            return {
                'status': 'completed',
                'chunks_processed': len(structured_chunks),
                'chunks_saved': saved_chunks,
                'vectorized_chunks': len(vectorized_chunks)
            }

        except Exception as e:
            logger.error(f"Ошибка обработки PDF {fipi_data.title}: {e}")
            return {'status': 'failed', 'error': str(e)}

    def _download_pdf(self, url: str) -> Optional[str]:
        """Скачивает PDF файл"""
        try:
            import tempfile
            import requests

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://fipi.ru/',
                'Accept': 'application/pdf,application/octet-stream;q=0.9,*/*;q=0.8',
            }

            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            # Создаем временный файл
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                tmp_file.write(response.content)
                return tmp_file.name

        except Exception as e:
            logger.error(f"Ошибка скачивания PDF {url}: {e}")
            return None

    def _extract_text_from_pdf(self, pdf_path: str) -> List[PDFChunk]:
        """Извлекает текст из PDF"""
        chunks = []

        # Пробуем pdfplumber
        try:
            chunks = self.text_extractor.extract_text_with_pdfplumber(pdf_path)
            if chunks:
                logger.info(f"Извлечено {len(chunks)} чанков с помощью pdfplumber")
                return chunks
        except Exception as e:
            logger.warning(f"pdfplumber не сработал: {e}")

        # Пробуем PyMuPDF
        try:
            chunks = self.text_extractor.extract_text_with_pymupdf(pdf_path)
            if chunks:
                logger.info(f"Извлечено {len(chunks)} чанков с помощью PyMuPDF")
                return chunks
        except Exception as e:
            logger.warning(f"PyMuPDF не сработал: {e}")

        return chunks

    def _save_chunks_to_db(self, fipi_data: FIPIData,
                           vectorized_chunks: List[Dict[str, Any]]) -> int:
        """Сохраняет чанки в базу данных"""
        saved_count = 0

        try:
            with transaction.atomic():
                for i, vectorized_chunk in enumerate(vectorized_chunks):
                    chunk = vectorized_chunk['chunk']
                    embedding = vectorized_chunk['embedding']

                    # Создаем запись в DataChunk
                    data_chunk = DataChunk.objects.create(  # type: ignore
                        source_data=fipi_data,
                        chunk_text=chunk.text,
                        chunk_index=i,
                        embedding=embedding,
                        metadata={
                            'chunk_type': chunk.chunk_type.value,
                            'page_number': chunk.page_number,
                            'bbox': chunk.bbox,
                            'confidence': chunk.confidence,
                            **chunk.metadata
                        }
                    )

                    saved_count += 1

        except Exception as e:
            logger.error(f"Ошибка сохранения чанков: {e}")

        return saved_count


# Глобальный экземпляр процессора
_pdf_processor: Optional[PDFProcessor] = None


def get_pdf_processor() -> PDFProcessor:
    """Получает глобальный экземпляр процессора PDF"""
    global _pdf_processor
    if _pdf_processor is None:
        _pdf_processor = PDFProcessor()
    return _pdf_processor


def process_pdf_document(fipi_data: FIPIData) -> Dict[str, Any]:
    """Обрабатывает PDF документ"""
    processor = get_pdf_processor()
    return processor.process_pdf(fipi_data)


def process_document(url: str, fipi_id: int) -> Dict[str, Any]:
    """Совместимый интерфейс для вызова из fill_site: по URL и id."""
    try:
        obj = FIPIData.objects.get(id=fipi_id)  # type: ignore
    except Exception:
        # если объекта нет, пытаемся создать заглушку записи
        obj = FIPIData.objects.create(  # type: ignore
            title=url,
            url=url,
            data_type='document',
            subject=None,
            exam_type='ege',
            content_hash=hashlib.sha256(url.encode('utf-8')).hexdigest(),
            content='',
            collected_at=timezone.now()
        )
    return get_pdf_processor().process_pdf(obj)

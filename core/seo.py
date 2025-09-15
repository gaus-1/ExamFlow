from __future__ import annotations

from typing import Dict
from django.conf import settings

SITE_URL = getattr(settings, 'WEBSITE_URL', 'https://examflow.ru')
DEFAULT_IMAGE = SITE_URL + '/static/images/logo-512.png'

def build_canonical(path: str) -> str:
    if path.startswith('http'):  # already full
        return path
    if not path.startswith('/'):
        path = '/' + path
    return SITE_URL.rstrip('/') + path

def seo_for_home() -> Dict[str, str]:
    title = 'Подготовка к ЕГЭ/ОГЭ по математике и русскому — ExamFlow'
    description = 'Разборы заданий, критерии ФИПИ, видеоуроки и тренажёры. Фокус: математика и русский.'
    url = build_canonical('/')
    return {
        'page_title': title,
        'page_description': description,
        'canonical_url': url,
        'og_title': title,
        'og_description': description,
        'og_image': DEFAULT_IMAGE,
        'og_url': url,
        'twitter_title': title,
        'twitter_description': description,
        'twitter_image': DEFAULT_IMAGE,
        'jsonld': _jsonld_org(),
    }

def seo_for_subject(subject_name: str, path: str) -> Dict[str, str]:
    title = 'Подготовка к {subject_name} ЕГЭ/ОГЭ — задания и разборы — ExamFlow'
    description = '{subject_name}: задания, критерии ФИПИ, видеоразборы, тренажёры и типичные ошибки.'
    url = build_canonical(path)
    data = {
        'page_title': title,
        'page_description': description,
        'canonical_url': url,
        'og_title': title,
        'og_description': description,
        'og_image': DEFAULT_IMAGE,
        'og_url': url,
        'twitter_title': title,
        'twitter_description': description,
        'twitter_image': DEFAULT_IMAGE,
    }
    # Добавим Course JSON-LD
    data['jsonld'] = _jsonld_course(subject_name, url)
    return data

def seo_for_task(subject_name: str, exam: str,
                 task_label: str, path: str) -> Dict[str, str]:
    title = 'ЕГЭ/ОГЭ {subject_name} — задание {task_label} с разбором — ExamFlow'
    description = 'Подробный разбор задания {task_label} по {subject_name}: критерии ФИПИ, типичные ошибки.'
    url = build_canonical(path)
    return {
        'page_title': title,
        'page_description': description,
        'canonical_url': url,
        'og_title': title,
        'og_description': description,
        'og_image': DEFAULT_IMAGE,
        'og_url': url,
        'twitter_title': title,
        'twitter_description': description,
        'twitter_image': DEFAULT_IMAGE,
    }

def _jsonld_org() -> str:
    data = {
        '@context': 'https://schema.org',
        '@type': 'EducationalOrganization',
        'name': 'ExamFlow',
        'url': SITE_URL,
        'logo': DEFAULT_IMAGE,
        'sameAs': [
            'https://t.me/ExamFlowBot',
        ],
    }
    # Simple safe serialization
    import json
    return json.dumps(data, ensure_ascii=False)

def _jsonld_course(subject_name: str, url: str) -> str:
    data = {
        '@context': 'https://schema.org',
        '@type': 'Course',
        'name': subject_name,
        'description': 'Курс подготовки к экзаменам по предмету {subject_name}.',
        'provider': {
            '@type': 'EducationalOrganization',
            'name': 'ExamFlow',
            'url': SITE_URL,
        },
        'url': url,
    }
    import json
    return json.dumps(data, ensure_ascii=False)

def jsonld_faq(qa: Dict[str, str]) -> str:
    """Build FAQPage JSON-LD from dict of question->answer."""
    data = {
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        'mainEntity': [
            {
                '@type': 'Question',
                'name': q,
                'acceptedAnswer': {'@type': 'Answer', 'text': a},
            }
            for q, a in qa.items()
        ],
    }
    import json
    return json.dumps(data, ensure_ascii=False)

def jsonld_video(title: str, page_url: str, thumb_url: str, content_url: str) -> str:
    data = {
        '@context': 'https://schema.org',
        '@type': 'VideoObject',
        'name': title,
        'thumbnailUrl': [thumb_url],
        'contentUrl': content_url,
        'embedUrl': content_url,
        'uploadDate': '2025-01-01',
        'description': title,
        'url': page_url,
    }
    import json
    return json.dumps(data, ensure_ascii=False)

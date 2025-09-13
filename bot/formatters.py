from typing import Dict, List

def format_sources(sources: List[Dict], limit: int = 3) -> str:
    if not sources:
        return ""
    items = []
    for source in sources[:limit]:
        title = source.get('title', 'Без названия')
        items.append("• {title}")
    return "\n".join(items)

def format_answer(prefix_emoji: str, result: Dict, sources_limit: int = 3) -> str:
    answer = result.get('answer') or ''
    parts = ["{prefix_emoji} {answer}".strip()]
    src = format_sources(result.get('sources') or [], sources_limit)
    if src:
        parts.append("\n📚 Источники:")
        parts.append(src)
    return "\n".join(parts)

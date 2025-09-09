from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@require_GET
def fipi_semantic_search(request: HttpRequest) -> JsonResponse:
    """Базовый семантический поиск по FIPI для двух предметов.

    q: строка запроса (обяз.)
    subject: Математика|Русский язык (опц.)
    limit: int (по умолчанию 5)
    """
    from core.rag_system.vector_store import VectorStore  # noqa: E402

    query = (request.GET.get("q") or "").strip()  # type: ignore
    subject = (request.GET.get("subject") or "").strip()  # type: ignore
    try:
        limit = int(request.GET.get("limit") or 5)  # type: ignore
    except Exception:
        limit = 5

    if not query:
        return JsonResponse({"error": "q is required"}, status=400)

    store = VectorStore()
    try:
        results = store.semantic_search(query=query, subject_filter=subject, limit=limit)  # type: ignore
        return JsonResponse({"results": results, "count": len(results)})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)



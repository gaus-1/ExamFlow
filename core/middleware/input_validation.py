from __future__ import annotations

from django.utils.deprecation import MiddlewareMixin
from django.http import HttpRequest


class InputValidationMiddleware(MiddlewareMixin):
    """Простейшая безопасная нормализация входа (обратима, без блокировок)."""

    MAX_PARAM_LEN = 2000

    def process_request(self, request: HttpRequest):  # type: ignore
        # Ограничим длины и уберём управляющие символы в query/POST
        for source in (request.GET, request.POST):
            # QueryDict по умолчанию неизменяем; временно делаем изменяемым
            if not hasattr(source, 'setlist'):
                continue
            try:
                original_mutable = getattr(source, '_mutable', True)
                if hasattr(source, '_mutable'):
                    source._mutable = True  # type: ignore[attr-defined]

                for k in list(source.keys()):
                    try:
                        v_list = source.getlist(k)  # type: ignore[no-untyped-call]
                    except Exception:
                        continue
                    if not isinstance(v_list, (list, tuple)):
                        continue
                    new_list = []
                    for v in v_list or []:
                        if isinstance(v, str):
                            trimmed = v[: self.MAX_PARAM_LEN]
                            cleaned = ''.join(ch for ch in trimmed if ord(ch) >= 32)
                            new_list.append(cleaned)
                        else:
                            new_list.append(v)
                    try:
                        source.setlist(k, new_list)
                    except Exception:
                        # Не блокируем запрос при ошибке мутации
                        pass
            finally:
                if hasattr(source, '_mutable'):
                    source._mutable = original_mutable  # type: ignore[attr-defined]



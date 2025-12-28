# backend/api/pagination.py
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPagination(PageNumberPagination):
    """
    Foodgram-подобная пагинация:
    - /api/recipes/?page=2&limit=6
    - limit управляет размером страницы
    - ответ: count/next/previous/results
    """
    page_size = 6
    page_size_query_param = "limit"
    page_query_param = "page"
    max_page_size = 100

    def get_page_size(self, request):
        """
        DRF сам умеет limit, но здесь чуть строже:
        - если limit не число / <= 0 -> используем page_size
        - если слишком большой -> ограничим max_page_size
        """
        raw = request.query_params.get(self.page_size_query_param)
        if not raw:
            return self.page_size
        try:
            value = int(raw)
        except (TypeError, ValueError):
            return self.page_size
        if value <= 0:
            return self.page_size
        return min(value, self.max_page_size)

    def get_paginated_response(self, data):
        return Response(
            {
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
            }
        )

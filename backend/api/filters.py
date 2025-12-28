# backend/api/filters.py
import django_filters
from django_filters import rest_framework as filters

from recipes.models import Recipe, Tag


class RecipeFilter(filters.FilterSet):
    """
    Под Postman/тесты Foodgram:
      - /api/recipes/?author=1
      - /api/recipes/?tags=breakfast&tags=lunch   (по slug)
      - /api/recipes/?is_favorited=1
      - /api/recipes/?is_in_shopping_cart=1
    """

    tags = filters.ModelMultipleChoiceFilter(
        field_name="tags__slug",
        to_field_name="slug",
        queryset=Tag.objects.all(),
    )

    # Добавление валидации для author (предполагается, что автор это ID пользователя)
    author = filters.NumberFilter(field_name="author__id", required=False)

    is_favorited = filters.NumberFilter(method="filter_is_favorited", required=False)
    is_in_shopping_cart = filters.NumberFilter(method="filter_is_in_shopping_cart", required=False)

    class Meta:
        model = Recipe
        fields = ("author", "tags", "is_favorited", "is_in_shopping_cart")

    def filter_is_favorited(self, queryset, name, value):
        """
        value ожидается 1/0.
        Если 1:
          - для авторизованного: отдать только избранные
          - для анонима: пусто
        """
        if value != 1:
            return queryset

        user = getattr(self.request, "user", None)
        if not user or not user.is_authenticated:
            return queryset.none()

        return queryset.filter(favorites__user=user)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """
        value ожидается 1/0.
        Если 1:
          - для авторизованного: отдать только в корзине
          - для анонима: пусто
        """
        if value != 1:
            return queryset

        user = getattr(self.request, "user", None)
        if not user or not user.is_authenticated:
            return queryset.none()

        return queryset.filter(shopping_cart__user=user)

# backend/recipes/filters.py
import django_filters as df
from django_filters.rest_framework import FilterSet

from .models import Recipe, Tag


class RecipeFilter(FilterSet):
    author = df.NumberFilter(field_name="author__id")

    tags = df.ModelMultipleChoiceFilter(
        field_name="tags__slug",
        to_field_name="slug",
        queryset=Tag.objects.all(),
    )

    # В спецификации Foodgram эти поля обычно приходят как 0/1
    is_favorited = df.NumberFilter(method="filter_is_favorited")
    is_in_shopping_cart = df.NumberFilter(method="filter_is_in_shopping_cart")

    class Meta:
        model = Recipe
        fields = ("author", "tags", "is_favorited", "is_in_shopping_cart")

    def _truthy(self, value) -> bool:
        """
        Приводим value к булевому флагу.
        Поддержка: 1/0, '1'/'0', true/false, 'true'/'false', True/False.
        """
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return int(value) == 1
        if isinstance(value, str):
            v = value.strip().lower()
            if v in ("1", "true", "yes", "y", "on"):
                return True
            if v in ("0", "false", "no", "n", "off", ""):
                return False
        # всё неизвестное считаем False, чтобы не ломать выдачу
        return False

    def filter_is_favorited(self, queryset, name, value):
        user = getattr(self.request, "user", None)
        if not self._truthy(value) or not user or user.is_anonymous:
            return queryset
        return queryset.filter(favorites__user=user)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = getattr(self.request, "user", None)
        if not self._truthy(value) or not user or user.is_anonymous:
            return queryset
        return queryset.filter(shopping_cart__user=user)

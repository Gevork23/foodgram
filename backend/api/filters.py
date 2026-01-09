from django_filters import rest_framework as filters

from .models import Ingredient, Recipe, Tag


class RecipeFilter(filters.FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name="tags__slug",
        to_field_name="slug",
        queryset=Tag.objects.all(),
    )
    is_favorited = filters.BooleanFilter(method="filter_is_favorited")
    is_in_shopping_cart = filters.BooleanFilter(
        method="filter_is_in_shopping_cart"
    )

    class Meta:
        model = Recipe
        fields = ("tags", "author", "is_favorited", "is_in_shopping_cart")

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        return (
            queryset.filter(favorites__user=user).distinct()
            if value and user.is_authenticated
            else queryset
        )

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        return (
            queryset.filter(shopping_cart__user=user).distinct()
            if value and user.is_authenticated
            else queryset
        )


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(field_name="name", lookup_expr="istartswith")
    search = filters.CharFilter(field_name="name", lookup_expr="istartswith")

    class Meta:
        model = Ingredient
        fields = ("name", "search")

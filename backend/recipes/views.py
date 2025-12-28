# backend/recipes/views.py
from django.db.models import Sum
from django.http import HttpResponse

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response

from api.pagination import CustomPagination
from api.permissions import IsAuthorOrReadOnly

from .filters import RecipeFilter
from .models import Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Tag
from .serializers import (
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeShortSerializer,
    RecipeWriteSerializer,
    TagSerializer,
)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    # В Foodgram ищут так: /api/ingredients/?name=сах
    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get("name")
        if name:
            return queryset.filter(name__istartswith=name)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthorOrReadOnly]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_queryset(self):
        # важно для производительности + корректных данных в сериализаторе
        return (
            Recipe.objects.all()
            .select_related("author")
            .prefetch_related("tags", "recipeingredient_set__ingredient")
        )

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _add_relation(self, model, request, recipe, err_msg="Уже добавлено."):
        obj, created = model.objects.get_or_create(user=request.user, recipe=recipe)
        if not created:
            return Response({"errors": err_msg}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            RecipeShortSerializer(recipe, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    def _remove_relation(self, model, request, recipe, err_msg="Нет в списке."):
        deleted, _ = model.objects.filter(user=request.user, recipe=recipe).delete()
        if deleted == 0:
            return Response({"errors": err_msg}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post", "delete"], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        if request.method == "POST":
            return self._add_relation(
                Favorite, request, recipe, err_msg="Рецепт уже в избранном."
            )
        return self._remove_relation(
            Favorite, request, recipe, err_msg="Рецепта нет в избранном."
        )

    @action(detail=True, methods=["post", "delete"], permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        if request.method == "POST":
            return self._add_relation(
                ShoppingCart, request, recipe, err_msg="Рецепт уже в списке покупок."
            )
        return self._remove_relation(
            ShoppingCart, request, recipe, err_msg="Рецепта нет в списке покупок."
        )

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        cart_exists = ShoppingCart.objects.filter(user=request.user).exists()
        if not cart_exists:
            return Response(
                {"errors": "Список покупок пуст."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ingredients = (
            RecipeIngredient.objects.filter(recipe__shopping_cart__user=request.user)
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(total_amount=Sum("amount"))
            .order_by("ingredient__name")
        )

        lines = ["Список покупок:", ""]
        for item in ingredients:
            lines.append(
                f'• {item["ingredient__name"]}: {item["total_amount"]} {item["ingredient__measurement_unit"]}'
            )
        lines.append("")
        lines.append(f"Итого: {ingredients.count()} ингредиентов")

        content = "\n".join(lines) + "\n"

        response = HttpResponse(content, content_type="text/plain; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="shopping_cart.txt"'
        return response

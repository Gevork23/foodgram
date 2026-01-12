import csv

from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from .auth_serializers import EmailAuthTokenSerializer
from .filters import IngredientFilter, RecipeFilter
from .models import (
    Favorite,
    Ingredient,
    Recipe,
    ShoppingCart,
    Subscription,
    Tag,
    User,
)
from .pagination import CustomPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    FavoriteCreateSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeShortSerializer,
    RecipeWriteSerializer,
    ShoppingCartCreateSerializer,
    SubscriptionSerializer,
    TagSerializer,
    UserAvatarSerializer,
    UserCreateSerializer,
    UserPasswordSerializer,
    UserSerializer,
)


class CustomAuthToken(ObtainAuthToken):
    """Кастомная аутентификация для возврата токена в правильном формате"""

    serializer_class = EmailAuthTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"auth_token": token.key})

def recipe_short_redirect(request, pk: int):
    get_object_or_404(Recipe, pk=pk)
    return redirect(request.build_absolute_uri(f"/recipes/{pk}"))

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    Token.objects.filter(user=request.user).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет для пользователей"""

    queryset = User.objects.all()
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        if self.action == "avatar":
            return UserAvatarSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in (
            "me",
            "set_password",
            "avatar",
            "subscribe",
            "subscriptions",
        ):
            return [IsAuthenticated()]
        return [AllowAny()]

    @staticmethod
    def _create_by_serializer(serializer_class, request, data):
        """
        Универсальный хелпер для POST:
        1) создать сериализатор
        2) провалидировать
        3) сохранить
        4) вернуть данные
        """
        serializer = serializer_class(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @staticmethod
    def _delete_by_filter(queryset, error_message):
        """
        Универсальный хелпер для DELETE:
        1) попытаться удалить
        2) если нечего удалять — вернуть 400
        """
        deleted, _ = queryset.delete()
        if not deleted:
            return Response(
                {"errors": error_message}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def set_password(self, request):
        serializer = UserPasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.update(request.user, serializer.validated_data)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["put", "delete"], url_path="me/avatar")
    def avatar(self, request):
        user = request.user

        if request.method == "PUT":
            serializer = UserAvatarSerializer(
                user, data=request.data, partial=False
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {"avatar": request.build_absolute_uri(user.avatar.url)}
            )

        if user.avatar:
            user.avatar.delete(save=False)
        user.avatar = None
        user.save(update_fields=["avatar"])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True, methods=["post"], permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, pk=None):
        author = get_object_or_404(User, id=pk)
        return self._create_by_serializer(
            serializer_class=SubscriptionSerializer,
            request=request,
            data={"author": author.id},
        )

    @subscribe.mapping.delete
    def delete_subscribe(self, request, pk=None):
        return self._delete_by_filter(
            Subscription.objects.filter(user=request.user, author_id=pk),
            error_message="Подписки не существует",
        )

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path="subscriptions",
    )
    def subscriptions(self, request):
        queryset = Subscription.objects.filter(user=request.user)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = SubscriptionSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = SubscriptionSerializer(
            queryset, many=True, context={"request": request}
        )
        return Response(serializer.data)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для тегов"""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    @staticmethod
    def _create_relation(serializer_class, request, recipe_pk):
        """
        Универсальный хелпер для POST (favorite/shopping_cart):
        - валидируем через сериализатор
        - сохраняем
        - возвращаем short-сериализацию рецепта
        """
        serializer = serializer_class(
            data={"recipe": recipe_pk}, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            RecipeShortSerializer(
                serializer.instance.recipe, context={"request": request}
            ).data,
            status=status.HTTP_201_CREATED,
        )

    @staticmethod
    def _delete_relation(request, model, recipe, error_message):
        deleted, _ = model.objects.filter(
            user=request.user, recipe=recipe
        ).delete()
        if not deleted:
            return Response(
                {"errors": error_message}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save()
        return Response(
            RecipeReadSerializer(recipe, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save()
        return Response(
            RecipeReadSerializer(recipe, context={"request": request}).data
        )

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    @action(
        detail=True, methods=["post"], permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        return self._create_relation(
            FavoriteCreateSerializer, request, recipe_pk=pk
        )

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        recipe = self.get_object()
        return self._delete_relation(
            request=request,
            model=Favorite,
            recipe=recipe,
            error_message="Рецепта нет в избранном.",
        )

    @action(
        detail=True, methods=["post"], permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        return self._create_relation(
            ShoppingCartCreateSerializer, request, recipe_pk=pk
        )

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        return self._delete_relation(
            request=request,
            model=ShoppingCart,
            recipe=recipe,
            error_message="Рецепта нет в списке покупок.",
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="download_shopping_cart",
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        recipes = Recipe.objects.filter(shopping_cart__user=request.user)

        ingredients = (
            recipes.values(
                "recipe_ingredients__ingredient__name",
                "recipe_ingredients__ingredient__measurement_unit",
            )
            .annotate(total_amount=Sum("recipe_ingredients__amount"))
            .order_by("recipe_ingredients__ingredient__name")
        )

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            'attachment; filename="shopping_list.csv"'
        )

        writer = csv.writer(response)
        writer.writerow(["Ингредиент", "Количество", "Единица измерения"])
        writer.writerows(
            [
                [
                    item["recipe_ingredients__ingredient__name"],
                    item["total_amount"],
                    item["recipe_ingredients__ingredient__measurement_unit"],
                ]
                for item in ingredients
            ]
        )
        return response

    @action(detail=True, methods=["get"], url_path="get-link")
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        short_url = request.build_absolute_uri(f"/s/{recipe.id}/")
        return Response({"short-link": short_url})


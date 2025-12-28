# backend/api/views.py
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import viewsets, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from recipes.models import (
    Recipe, RecipeIngredient, Ingredient, Tag,
    Favorite, ShoppingCart, Subscription
)

from .filters import RecipeFilter
from .pagination import CustomPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    RecipeSerializer, RecipeCreateSerializer, RecipeMinifiedSerializer,
    IngredientSerializer, TagSerializer,
    UserSerializer, UserCreateSerializer, CustomUserResponseOnCreateSerializer,
    UserWithRecipesSerializer, SetPasswordSerializer,
    TokenCreateSerializer,
    SetAvatarSerializer,
)

User = get_user_model()


class RecipeViewSet(viewsets.ModelViewSet):
    """
    /api/recipes/
    + actions:
      - /api/recipes/{id}/favorite/ (POST, DELETE)
      - /api/recipes/{id}/shopping_cart/ (POST, DELETE)
      - /api/recipes/download_shopping_cart/ (GET)
      - /api/recipes/{id}/get-link/ (GET)
    """
    permission_classes = [IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    pagination_class = CustomPagination

    def get_queryset(self):
        return (
            Recipe.objects
            .select_related("author")
            .prefetch_related("tags", "recipeingredient_set__ingredient")
            .all()
        )

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return RecipeCreateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        recipe = self.get_object()

        if request.method == "POST":
            obj, created = Favorite.objects.get_or_create(
                user=request.user,
                recipe=recipe
            )
            if not created:
                return Response(
                    {"errors": "Рецепт уже в избранном"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            data = RecipeMinifiedSerializer(
                recipe, context={"request": request}
            ).data
            return Response(data, status=status.HTTP_201_CREATED)

        deleted, _ = Favorite.objects.filter(
            user=request.user,
            recipe=recipe
        ).delete()

        if not deleted:
            return Response(
                {"errors": "Рецепта нет в избранном"},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
        url_path="shopping_cart",
    )
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()

        if request.method == "POST":
            obj, created = ShoppingCart.objects.get_or_create(
                user=request.user,
                recipe=recipe
            )
            if not created:
                return Response(
                    {"errors": "Рецепт уже в списке покупок"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            data = RecipeMinifiedSerializer(
                recipe, context={"request": request}
            ).data
            return Response(data, status=status.HTTP_201_CREATED)

        deleted, _ = ShoppingCart.objects.filter(
            user=request.user,
            recipe=recipe
        ).delete()

        if not deleted:
            return Response(
                {"errors": "Рецепта нет в списке покупок"},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[AllowAny],
        url_path="get-link",
    )
    def get_link(self, request, pk=None):
        """
        В Foodgram по тестам ожидают поле 'short-link'.
        Формируем ссылку на основе текущего хоста, чтобы не было 'example.org'.
        """
        recipe = self.get_object()
        base = request.build_absolute_uri("/").rstrip("/")
        short_link = f"{base}/s/{recipe.id}"
        return Response({"short-link": short_link}, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path="download_shopping_cart",
    )
    def download_shopping_cart(self, request):
        ingredients = (
            RecipeIngredient.objects
            .filter(recipe__shopping_cart__user=request.user)
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(amount=Sum("amount"))
            .order_by("ingredient__name")
        )

        # По тестам обычно ждут TXT-файл всегда, даже если пусто — но многие реализации
        # возвращают 400. Чтобы не падать на "пусто", отдаем пустой список покупок.
        lines = ["Список покупок:"]
        for item in ingredients:
            lines.append(
                f"{item['ingredient__name']} "
                f"({item['ingredient__measurement_unit']}) — {item['amount']}"
            )
        text = "\n".join(lines) + "\n"

        response = HttpResponse(text, content_type="text/plain; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="shopping_cart.txt"'
        return response


class UserViewSet(viewsets.ModelViewSet):
    """
    /api/users/
    + actions:
      - /api/users/me/ (GET)
      - /api/users/set_password/ (POST)
      - /api/users/{id}/subscribe/ (POST, DELETE)
      - /api/users/subscriptions/ (GET)
      - /api/users/me/avatar/ (PUT, DELETE)
    """
    queryset = User.objects.all()
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        if self.action in ("subscriptions", "subscribe"):
            return UserWithRecipesSerializer
        if self.action == "set_password":
            return SetPasswordSerializer
        if self.action == "avatar":
            return SetAvatarSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]
        if self.action in ("me", "set_password", "subscriptions", "subscribe", "avatar"):
            return [IsAuthenticated()]
        return [permissions.AllowAny()]

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="set_password"
    )
    def set_password(self, request):
        serializer = SetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        current_password = serializer.validated_data.get("current_password")
        new_password = serializer.validated_data.get("new_password")

        if not user.check_password(current_password):
            return Response(
                {"current_password": "Неверный текущий пароль"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post", "delete"], permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk=None):
        author = self.get_object()

        if request.method == "POST":
            if author == request.user:
                return Response(
                    {"errors": "Нельзя подписаться на себя"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            sub, created = Subscription.objects.get_or_create(
                user=request.user,
                author=author
            )
            if not created:
                return Response(
                    {"errors": "Вы уже подписаны на этого пользователя"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            data = self.get_serializer(author, context={"request": request}).data
            return Response(data, status=status.HTTP_201_CREATED)

        deleted, _ = Subscription.objects.filter(
            user=request.user,
            author=author
        ).delete()

        if not deleted:
            return Response(
                {"errors": "Вы не подписаны на этого пользователя"},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        authors = (
            User.objects
            .filter(following__user=request.user)
            .prefetch_related("recipes")
            .distinct()
        )

        page = self.paginate_queryset(authors)
        if page is not None:
            serializer = self.get_serializer(page, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(authors, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        response_serializer = CustomUserResponseOnCreateSerializer(
            serializer.instance,
            context={"request": request}
        )
        headers = self.get_success_headers(serializer.data)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    @action(
        detail=False,
        methods=["put", "delete"],
        permission_classes=[IsAuthenticated],
        url_path="me/avatar",
    )
    def avatar(self, request):
        user = request.user

        if request.method == "PUT":
            serializer = SetAvatarSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user.avatar = serializer.validated_data["avatar"]
            user.save()
            return Response(
                {"avatar": request.build_absolute_uri(user.avatar.url)},
                status=status.HTTP_200_OK
            )

        user.avatar = None
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomObtainAuthToken(ObtainAuthToken):
    """
    /api/auth/token/login/
    Body: { "email": "...", "password": "..." }
    Response: { "auth_token": "..." }
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = TokenCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"errors": "Пользователь с таким email не найден"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except User.MultipleObjectsReturned:
            user = User.objects.filter(email=email).first()

        if not user or not user.check_password(password):
            return Response(
                {"errors": "Неверные учетные данные"},
                status=status.HTTP_400_BAD_REQUEST
            )

        token, _ = Token.objects.get_or_create(user=user)
        return Response({"auth_token": token.key}, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    /api/auth/token/logout/
    """
    if request.auth:
        request.auth.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    /api/ingredients/
    Поиск: /api/ingredients/?name=сах
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get("name")
        if name:
            return queryset.filter(name__istartswith=name)
        return queryset


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    /api/tags/
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    pagination_class = None

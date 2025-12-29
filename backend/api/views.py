# backend/api/views.py
from rest_framework import viewsets, status, generics, mixins
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Q
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from .auth_serializers import EmailAuthTokenSerializer

from .models import (
    User, Tag, Ingredient, Recipe,
    Subscription, Favorite, ShoppingCart
)
from .serializers import (
    UserSerializer, UserCreateSerializer, UserAvatarSerializer,
    UserPasswordSerializer, TagSerializer, IngredientSerializer,
    RecipeReadSerializer, RecipeWriteSerializer, SubscriptionSerializer, RecipeShortSerializer
)
from .permissions import IsAuthorOrReadOnly
from .pagination import CustomPagination
from .filters import RecipeFilter, IngredientFilter
import csv


class CustomAuthToken(ObtainAuthToken):
    """Кастомная аутентификация для возврата токена в правильном формате"""
    serializer_class = EmailAuthTokenSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({'auth_token': token.key})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        token = Token.objects.get(user=request.user)
        token.delete()
    except Token.DoesNotExist:
        pass
    
    return Response(status=status.HTTP_204_NO_CONTENT)


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет для пользователей"""
    queryset = User.objects.all()
    pagination_class = CustomPagination
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action == 'avatar':
            return UserAvatarSerializer
        return UserSerializer
    
    def get_permissions(self):
        if self.action in ['me', 'set_password', 'avatar', 'subscribe', 'subscriptions']:
            return [IsAuthenticated()]
        return [AllowAny()]

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def set_password(self, request):
        serializer = UserPasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.update(request.user, serializer.validated_data)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar')
    def avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            serializer = UserAvatarSerializer(
                user,
                data=request.data,
                partial=False
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'avatar': request.build_absolute_uri(user.avatar.url)})
        elif request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete(save=False)
            user.avatar = None
            user.save(update_fields=['avatar'])
            return Response(status=status.HTTP_204_NO_CONTENT)
        

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk=None):
        user = request.user
        author = get_object_or_404(User, id=pk)

        if request.method == 'POST':
            if user == author:
                return Response({'errors': 'Нельзя подписаться на самого себя'},
                                status=status.HTTP_400_BAD_REQUEST)
            if Subscription.objects.filter(user=user, author=author).exists():
                return Response({'errors': 'Вы уже подписаны на этого пользователя'},
                                status=status.HTTP_400_BAD_REQUEST)

            subscription = Subscription.objects.create(user=user, author=author)
            serializer = SubscriptionSerializer(subscription, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        qs = Subscription.objects.filter(user=user, author=author)
        if not qs.exists():
            return Response({'errors': 'Подписки не существует'},
                            status=status.HTTP_400_BAD_REQUEST)
        qs.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], url_path='subscriptions')
    def subscriptions(self, request):
        queryset = Subscription.objects.filter(user=request.user)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SubscriptionSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = SubscriptionSerializer(
            queryset, many=True, context={'request': request}
        )
        return Response(serializer.data)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для тегов"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для ингредиентов"""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save()
        return Response(
            RecipeReadSerializer(recipe, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial, context={'request': request})
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save()
        return Response(RecipeReadSerializer(recipe, context={'request': request}).data)

    def partial_update(self, request, *args, **kwargs):
        # PATCH делаем строгим: обязаны прийти tags и ingredients
        kwargs['partial'] = False
        return self.update(request, *args, **kwargs)
    
    @action(detail=True, methods=('post', 'delete'), permission_classes=(IsAuthenticated,))
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response({'errors': 'Рецепт уже в избранном.'},
                                status=status.HTTP_400_BAD_REQUEST)
            Favorite.objects.create(user=user, recipe=recipe)
            serializer = RecipeShortSerializer(recipe, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # DELETE
        qs = Favorite.objects.filter(user=user, recipe=recipe)
        if not qs.exists():
            return Response({'errors': 'Рецепта нет в избранном.'},
                            status=status.HTTP_400_BAD_REQUEST)
        qs.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=('post', 'delete'), permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user

        if request.method == 'POST':
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response({'errors': 'Рецепт уже в списке покупок.'},
                                status=status.HTTP_400_BAD_REQUEST)
            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = RecipeShortSerializer(recipe, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        cart_qs = ShoppingCart.objects.filter(user=user, recipe=recipe)
        if not cart_qs.exists():
            return Response({'errors': 'Рецепта нет в списке покупок.'},
                            status=status.HTTP_400_BAD_REQUEST)
        cart_qs.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'], url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        user = request.user
        recipes = Recipe.objects.filter(shopping_cart__user=user)
        
        ingredients = recipes.values(
            'recipe_ingredients__ingredient__name',
            'recipe_ingredients__ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('recipe_ingredients__amount')
        ).order_by('recipe_ingredients__ingredient__name')
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="shopping_list.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Ингредиент', 'Количество', 'Единица измерения'])
        
        for ingredient in ingredients:
            writer.writerow([
                ingredient['recipe_ingredients__ingredient__name'],
                ingredient['total_amount'],
                ingredient['recipe_ingredients__ingredient__measurement_unit']
            ])
        
        return response
    
    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        return Response({'short-link': f'/api/recipes/{recipe.id}/'})



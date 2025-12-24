# api/views.py
from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, permissions, filters, status
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from recipes.models import Recipe, RecipeIngredient, Ingredient, Tag, Favorite, ShoppingCart, Subscription
from .serializers import (
    RecipeSerializer, RecipeCreateSerializer, RecipeMinifiedSerializer,
    IngredientSerializer, TagSerializer, UserSerializer, 
    UserCreateSerializer, CustomUserResponseOnCreateSerializer,
    UserWithRecipesSerializer, SetPasswordSerializer,
    TokenCreateSerializer, TokenGetResponseSerializer
)
from .filters import RecipeFilter
from .pagination import CustomPagination
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import api_view, permission_classes

User = get_user_model()

class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    pagination_class = CustomPagination
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateSerializer
        return RecipeSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()

        author_id = self.request.query_params.get('author')
        tags = self.request.query_params.getlist('tags')
        is_favorited = self.request.query_params.get('is_favorited')
        is_in_shopping_cart = self.request.query_params.get('is_in_shopping_cart')
        
        if author_id:
            queryset = queryset.filter(author_id=author_id)
        
        if tags:
            queryset = queryset.filter(tags__slug__in=tags).distinct()
        
        if is_favorited == '1' and self.request.user.is_authenticated:
            queryset = queryset.filter(favorites__user=self.request.user)
        
        if is_in_shopping_cart == '1' and self.request.user.is_authenticated:
            queryset = queryset.filter(shopping_cart__user=self.request.user)
        
        return queryset.select_related('author').prefetch_related(
            'tags', 'recipeingredient_set__ingredient'
        )
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    @action(detail=True, methods=['post', 'delete'], 
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        
        if request.method == 'POST':
            favorite, created = Favorite.objects.get_or_create(
                user=request.user,
                recipe=recipe
            )
            if created:
                serializer = RecipeMinifiedSerializer(recipe)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(
                {'error': 'Рецепт уже в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        elif request.method == 'DELETE':
            deleted, _ = Favorite.objects.filter(
                user=request.user, 
                recipe=recipe
            ).delete()
            
            if deleted:
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'error': 'Рецепта нет в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        
        if request.method == 'POST':
            cart_item, created = ShoppingCart.objects.get_or_create(
                user=request.user,
                recipe=recipe
            )
            if created:
                serializer = RecipeMinifiedSerializer(recipe)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(
                {'error': 'Рецепт уже в списке покупок'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        elif request.method == 'DELETE':
            deleted, _ = ShoppingCart.objects.filter(
                user=request.user, 
                recipe=recipe
            ).delete()
            
            if deleted:
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'error': 'Рецепта нет в списке покупок'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        short_link = f"https://foodgram.example.org/s/{recipe.id}"
        return Response({'short-link': short_link})
    
    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        shopping_cart_items = ShoppingCart.objects.filter(user=request.user)
        
        if not shopping_cart_items.exists():
            return Response(
                {'error': 'Список покупок пуст'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('ingredient__name')
        
        text = "Список покупок:\n\n"
        text += "=" * 40 + "\n\n"
        
        for item in ingredients:
            text += f"• {item['ingredient__name']}: {item['total_amount']} {item['ingredient__measurement_unit']}\n"
        
        text += f"\nИтого: {len(ingredients)} ингредиентов"
        
        response = HttpResponse(text, content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        
        return response

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action == 'subscriptions':
            return UserWithRecipesSerializer
        elif self.action == 'subscribe':
            return UserWithRecipesSerializer
        elif self.action == 'set_password':
            return SetPasswordSerializer
        return UserSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        elif self.action in ['me', 'subscriptions', 'subscribe', 'set_password']:
            return [IsAuthenticated()]
        return super().get_permissions()
    
    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'],
            permission_classes=[IsAuthenticated])
    def set_password(self, request):
        serializer = SetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            
            if not user.check_password(serializer.validated_data['current_password']):
                return Response(
                    {'current_password': 'Неверный текущий пароль'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk=None):
        author = self.get_object()
        
        if request.method == 'POST':
            if author == request.user:
                return Response(
                    {'error': 'Нельзя подписаться на себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            subscription, created = Subscription.objects.get_or_create(
                user=request.user,
                author=author
            )
            
            if created:
                serializer = self.get_serializer(
                    author, 
                    context={'request': request}
                )
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            
            return Response(
                {'error': 'Вы уже подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        elif request.method == 'DELETE':
            deleted, _ = Subscription.objects.filter(
                user=request.user,
                author=author
            ).delete()
            
            if deleted:
                return Response(status=status.HTTP_204_NO_CONTENT)
            
            return Response(
                {'error': 'Вы не подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        authors = User.objects.filter(
            following__user=request.user
        ).prefetch_related('recipes')
        
        page = self.paginate_queryset(authors)
        
        if page is not None:
            serializer = self.get_serializer(
                page, 
                many=True, 
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(
            authors, 
            many=True, 
            context={'request': request}
        )
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        response_serializer = CustomUserResponseOnCreateSerializer(
            serializer.instance
        )
        headers = self.get_success_headers(serializer.data)
        return Response(
            response_serializer.data, 
            status=status.HTTP_201_CREATED, 
            headers=headers
        )

    @action(detail=False, methods=['put', 'delete'], 
            permission_classes=[IsAuthenticated])
    def avatar(self, request):
        if request.method == 'PUT':
            return Response(
                {'avatar': 'http://foodgram.example.org/media/users/image.png'},
                status=status.HTTP_200_OK
            )
        elif request.method == 'DELETE':
            return Response(status=status.HTTP_204_NO_CONTENT)

class CustomObtainAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = TokenCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            user = User.objects.get(email=serializer.validated_data['email'])
        except User.DoesNotExist:
            return Response(
                {'error': 'Пользователь с таким email не найден'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except User.MultipleObjectsReturned:
            user = User.objects.filter(email=serializer.validated_data['email']).first()
        
        if not user.check_password(serializer.validated_data['password']):
            return Response(
                {'error': 'Неверные учетные данные'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        token, created = Token.objects.get_or_create(user=user)
        return Response({'auth_token': token.key})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    request.auth.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    pagination_class = None
    
    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset

class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None
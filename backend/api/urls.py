# api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'recipes', views.RecipeViewSet, basename='recipe')
router.register(r'ingredients', views.IngredientViewSet, basename='ingredient')
router.register(r'tags', views.TagViewSet, basename='tag')
router.register(r'users', views.UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/token/login/', views.CustomObtainAuthToken.as_view(), name='login'),
    path('auth/token/logout/', views.logout_view, name='logout'),
]
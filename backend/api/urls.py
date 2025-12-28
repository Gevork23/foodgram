# backend/api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    RecipeViewSet,
    IngredientViewSet,
    TagViewSet,
    UserViewSet,
    CustomObtainAuthToken,
    logout_view,
)

router = DefaultRouter()
router.register(r"recipes", RecipeViewSet, basename="recipe")
router.register(r"ingredients", IngredientViewSet, basename="ingredient")
router.register(r"tags", TagViewSet, basename="tag")
router.register(r"users", UserViewSet, basename="user")

urlpatterns = [
    # API root + viewsets:
    path("", include(router.urls)),

    # Auth endpoints (for Postman):
    # POST /api/auth/token/login/  -> get token
    # POST /api/auth/token/logout/ -> delete token (or server-side logout)
    path("auth/token/login/", CustomObtainAuthToken.as_view(), name="token-login"),
    path("auth/token/logout/", logout_view, name="token-logout"),
]

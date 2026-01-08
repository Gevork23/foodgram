from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CustomAuthToken,
    IngredientViewSet,
    RecipeViewSet,
    TagViewSet,
    UserViewSet,
    logout_view,
)

router = DefaultRouter()
router.register("users", UserViewSet, basename="users")
router.register("tags", TagViewSet, basename="tags")
router.register("ingredients", IngredientViewSet, basename="ingredients")
router.register("recipes", RecipeViewSet, basename="recipes")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/token/login/", CustomAuthToken.as_view(), name="login"),
    path("auth/token/logout/", logout_view, name="logout"),
]

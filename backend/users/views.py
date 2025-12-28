# users/views.py
from django.contrib.auth import get_user_model
from rest_framework import mixins, viewsets
from rest_framework.permissions import AllowAny

from api.pagination import CustomPagination
from .serializers import UserSerializer, UserCreateSerializer

User = get_user_model()


class UsersViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """
    Запасной ViewSet пользователей (если подключишь users/urls.py).

    Совместим по формату ответа с Foodgram/Postman:
    - список с пагинацией count/next/previous/results
    - детальный просмотр
    - регистрация
    - без update/delete через этот роут
    """

    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

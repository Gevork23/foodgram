# backend/api/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAuthorOrReadOnly(BasePermission):
    """
    Разрешение:
      - SAFE_METHODS (GET/HEAD/OPTIONS) доступны всем.
      - Небезопасные методы доступны только авторизованным.
      - На уровне объекта менять/удалять может только автор.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        # поддержка разных названий поля "автор"
        author = getattr(obj, "author", None)
        if author is None:
            author = getattr(obj, "user", None)
        if author is None:
            author = getattr(obj, "owner", None)

        return bool(request.user and request.user.is_authenticated and author == request.user)

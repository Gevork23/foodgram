# users/serializers.py
import base64
import binascii
import imghdr
import uuid

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework import serializers

from recipes.models import Subscription

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """
    Принимает:
    1) "data:image/png;base64,AAAA..."
    2) "AAAA..." (чистый base64)
    """

    def to_internal_value(self, data):
        if data in (None, "", {}):
            return super().to_internal_value(data)

        if isinstance(data, str):
            if data.startswith("data:image"):
                try:
                    _, b64data = data.split(";base64,")
                except ValueError:
                    raise serializers.ValidationError("Неверный формат base64 изображения.")
            else:
                b64data = data

            try:
                decoded = base64.b64decode(b64data)
            except (binascii.Error, ValueError):
                raise serializers.ValidationError("Неверный base64.")

            ext = imghdr.what(None, decoded)
            if ext is None:
                raise serializers.ValidationError("Не удалось определить формат изображения.")
            if ext == "jpeg":
                ext = "jpg"

            file_name = f"{uuid.uuid4().hex}.{ext}"
            data = ContentFile(decoded, name=file_name)

        return super().to_internal_value(data)


class UserSerializer(serializers.ModelSerializer):
    """
    Совместим с тем, что ожидают Postman-тесты Foodgram:
    - avatar: URL или null
    - is_subscribed: bool
    """

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "email", "username", "first_name", "last_name", "is_subscribed", "avatar")
        read_only_fields = ("id", "is_subscribed", "avatar")

    def get_avatar(self, obj):
        request = self.context.get("request")
        if not getattr(obj, "avatar", None):
            return None
        url = obj.avatar.url
        return request.build_absolute_uri(url) if request else url

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(user=request.user, author=obj).exists()
        return False


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Создание пользователя в стиле Foodgram:
    - password write_only
    - создание через manager.create_user(email, password, ...)
    """

    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ("id", "email", "username", "first_name", "last_name", "password")
        read_only_fields = ("id",)

    def create(self, validated_data):
        password = validated_data.pop("password")
        email = validated_data.get("email")
        # ВАЖНО: твой CustomUserManager ожидает email первым аргументом
        user = User.objects.create_user(
            email,
            password=password,
            username=validated_data.get("username"),
            first_name=validated_data.get("first_name"),
            last_name=validated_data.get("last_name"),
        )
        return user


class SetAvatarSerializer(serializers.Serializer):
    """Если когда-нибудь будете делать отдельный endpoint users/me/avatar."""
    avatar = Base64ImageField(required=True)

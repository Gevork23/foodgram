# backend/api/serializers.py
import base64
import binascii
import imghdr
import uuid

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db import transaction
from rest_framework import serializers

from recipes.models import (
    Recipe, Ingredient, Tag, RecipeIngredient,
    Favorite, ShoppingCart, Subscription
)

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """
    Принимает:
      1) "data:image/png;base64,AAAA..."
      2) "AAAA..." (чистый base64)
    Возвращает ContentFile -> стандартный ImageField.
    """

    def to_internal_value(self, data):
        # Если пришёл уже файл/объект — отдаём на стандартную обработку
        if data is None or data == "":
            return super().to_internal_value(data)

        if isinstance(data, ContentFile):
            return super().to_internal_value(data)

        if isinstance(data, str):
            if data.startswith("data:image"):
                try:
                    _, b64data = data.split(";base64,", 1)
                except ValueError:
                    raise serializers.ValidationError("Неверный формат base64 изображения.")
            else:
                b64data = data

            try:
                decoded = base64.b64decode(b64data)
            except (binascii.Error, ValueError):
                raise serializers.ValidationError("Неверный base64.")

            ext = imghdr.what(None, decoded)
            if not ext:
                raise serializers.ValidationError("Не удалось определить формат изображения.")
            if ext == "jpeg":
                ext = "jpg"

            file_name = f"{uuid.uuid4().hex}.{ext}"
            data = ContentFile(decoded, name=file_name)

        return super().to_internal_value(data)


# -------------------------
# Users
# -------------------------

class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "email", "username", "first_name", "last_name",
            "is_subscribed", "avatar"
        ]

    def get_avatar(self, obj):
        request = self.context.get("request")
        avatar = getattr(obj, "avatar", None)
        if not avatar:
            return None
        url = avatar.url
        return request.build_absolute_uri(url) if request else url

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return Subscription.objects.filter(user=request.user, author=obj).exists()


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ["email", "username", "first_name", "last_name", "password"]

    def validate_password(self, value):
        if not value or len(value) < 8:
            raise serializers.ValidationError("Пароль должен быть не короче 8 символов.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        # Безопаснее через keyword-args: менеджер/модель у всех разные
        user = User.objects.create_user(
            email=validated_data.get("email"),
            password=password,
            username=validated_data.get("username"),
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
        )
        return user


class CustomUserResponseOnCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "username", "first_name", "last_name"]


class SetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True)
    current_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        if not value or len(value) < 8:
            raise serializers.ValidationError("Пароль должен быть не короче 8 символов.")
        return value


class TokenCreateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class SetAvatarSerializer(serializers.Serializer):
    avatar = Base64ImageField(required=True)


# -------------------------
# Tags / Ingredients
# -------------------------

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "color", "slug"]


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ["id", "name", "measurement_unit"]


# -------------------------
# Recipes (read)
# -------------------------

class IngredientInRecipeSerializer(serializers.ModelSerializer):
    # В ответе tests обычно ждут id ингредиента как число
    id = serializers.IntegerField(source="ingredient.id", read_only=True)
    name = serializers.CharField(source="ingredient.name", read_only=True)
    measurement_unit = serializers.CharField(source="ingredient.measurement_unit", read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ["id", "name", "measurement_unit", "amount"]


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ["id", "name", "image", "cooking_time"]

    def get_image(self, obj):
        request = self.context.get("request")
        image = getattr(obj, "image", None)
        if not image:
            return None
        url = image.url
        return request.build_absolute_uri(url) if request else url


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientInRecipeSerializer(
        source="recipeingredient_set", many=True, read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        ]

    def get_image(self, obj):
        request = self.context.get("request")
        image = getattr(obj, "image", None)
        if not image:
            return None
        url = image.url
        return request.build_absolute_uri(url) if request else url

    def get_is_favorited(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return Favorite.objects.filter(user=request.user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return ShoppingCart.objects.filter(user=request.user, recipe=obj).exists()


# -------------------------
# Recipes (write)
# -------------------------

class IngredientAmountSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)

    def validate_id(self, value):
        if not Ingredient.objects.filter(id=value).exists():
            raise serializers.ValidationError(f"Ингредиент с id {value} не найден.")
        return value


class RecipeCreateSerializer(serializers.ModelSerializer):
    """
    Вход (POST/PUT/PATCH):
      ingredients: [{id, amount}, ...]
      tags: [1, 2, 3]
      image: base64
      name, text, cooking_time

    Выход: как RecipeSerializer
    """
    ingredients = IngredientAmountSerializer(many=True, write_only=True, required=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        write_only=True,
        required=True
    )
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields = ["ingredients", "tags", "image", "name", "text", "cooking_time"]

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data

    def validate(self, attrs):
        ingredients = attrs.get("ingredients")
        tags = attrs.get("tags")

        if not ingredients:
            raise serializers.ValidationError({"ingredients": "Добавьте хотя бы один ингредиент."})

        ids = [item["id"] for item in ingredients]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError({"ingredients": "Ингредиенты не должны повторяться."})

        if not tags:
            raise serializers.ValidationError({"tags": "Добавьте хотя бы один тег."})

        cooking_time = attrs.get("cooking_time")
        if cooking_time is not None and cooking_time <= 0:
            raise serializers.ValidationError({"cooking_time": "Время приготовления должно быть больше 0."})

        return attrs

    def _set_ingredients(self, recipe, ingredients_data):
        ingredient_ids = [item["id"] for item in ingredients_data]
        ingredients_map = {
            ing.id: ing for ing in Ingredient.objects.filter(id__in=ingredient_ids)
        }

        objs = []
        for item in ingredients_data:
            ing = ingredients_map.get(item["id"])
            if not ing:
                raise serializers.ValidationError(
                    {"ingredients": f"Ингредиент с id {item['id']} не найден."}
                )
            objs.append(
                RecipeIngredient(
                    recipe=recipe,
                    ingredient=ing,
                    amount=item["amount"]
                )
            )
        RecipeIngredient.objects.bulk_create(objs)

    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        tags_data = validated_data.pop("tags")

        request = self.context.get("request")
        author = request.user if request else None

        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags_data)
        self._set_ingredients(recipe, ingredients_data)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        if "ingredients" in validated_data:
            ingredients_data = validated_data.pop("ingredients")
            instance.recipeingredient_set.all().delete()
            self._set_ingredients(instance, ingredients_data)

        if "tags" in validated_data:
            tags_data = validated_data.pop("tags")
            instance.tags.set(tags_data)

        return super().update(instance, validated_data)


# -------------------------
# Subscriptions
# -------------------------

class UserWithRecipesSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source="recipes.count", read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ["recipes", "recipes_count"]

    def get_recipes(self, obj):
        request = self.context.get("request")
        limit = None
        if request:
            raw = request.query_params.get("recipes_limit")
            if raw is not None:
                try:
                    limit = int(raw)
                except ValueError:
                    limit = None

        qs = obj.recipes.all()
        if limit is not None and limit >= 0:
            qs = qs[:limit]

        return RecipeMinifiedSerializer(qs, many=True, context={"request": request}).data

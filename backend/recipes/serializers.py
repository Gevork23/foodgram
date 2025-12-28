# backend/recipes/serializers.py
import base64
import binascii
import imghdr
import uuid

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework import serializers

from .models import (
    Tag,
    Ingredient,
    Recipe,
    RecipeIngredient,
    Favorite,
    ShoppingCart,
    Subscription,
)

User = get_user_model()


# --------- Utils ---------
class Base64ImageField(serializers.ImageField):
    """
    Принимает:
    1) "data:image/png;base64,AAAA..."
    2) "AAAA..." (чистый base64)
    Отдает стандартный ImageField.
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
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "avatar",
        )

    def get_avatar(self, obj):
        request = self.context.get("request")
        if not getattr(obj, "avatar", None):
            return None
        url = obj.avatar.url
        return request.build_absolute_uri(url) if request else url

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not request or not user or user.is_anonymous:
            return False
        return Subscription.objects.filter(user=user, author=obj).exists()


# --------- Simple serializers ---------
class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "color", "slug")


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


# --------- Ingredients in recipe ---------
class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="ingredient.id", read_only=True)
    name = serializers.CharField(source="ingredient.name", read_only=True)
    measurement_unit = serializers.CharField(source="ingredient.measurement_unit", read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class IngredientAmountWriteSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)

    def validate_id(self, value):
        if not Ingredient.objects.filter(id=value).exists():
            raise serializers.ValidationError("Ингредиент не найден.")
        return value


# --------- Recipes ---------
class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientReadSerializer(source="recipeingredient_set", many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
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
        )

    def get_image(self, obj):
        request = self.context.get("request")
        if not obj.image:
            return None
        url = obj.image.url
        return request.build_absolute_uri(url) if request else url

    def _is_exists(self, model, obj):
        request = self.context.get("request")
        if not request or request.user.is_anonymous:
            return False
        return model.objects.filter(user=request.user, recipe=obj).exists()

    def get_is_favorited(self, obj):
        return self._is_exists(Favorite, obj)

    def get_is_in_shopping_cart(self, obj):
        return self._is_exists(ShoppingCart, obj)


class RecipeWriteSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all())
    ingredients = IngredientAmountWriteSerializer(many=True)
    author = serializers.PrimaryKeyRelatedField(read_only=True)
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def validate(self, attrs):
        # Валидация по raw input, чтобы ловить ошибки формата до внутренних преобразований
        ingredients = self.initial_data.get("ingredients")
        tags = self.initial_data.get("tags")

        if not ingredients:
            raise serializers.ValidationError({"ingredients": "Нужен минимум 1 ингредиент."})
        if not tags:
            raise serializers.ValidationError({"tags": "Нужен минимум 1 тег."})

        # уникальность ингредиентов
        try:
            ids = [int(i["id"]) for i in ingredients]
        except (TypeError, KeyError, ValueError):
            raise serializers.ValidationError({"ingredients": "Неверный формат ингредиентов."})

        if len(ids) != len(set(ids)):
            raise serializers.ValidationError({"ingredients": "Ингредиенты должны быть уникальны."})

        # уникальность тегов
        try:
            tag_ids = [int(t) for t in tags]
        except (TypeError, ValueError):
            # tags может прийти как список строк/чисел — ок, но если мусор, ловим
            raise serializers.ValidationError({"tags": "Неверный формат тегов."})

        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError({"tags": "Теги должны быть уникальны."})

        return attrs

    def _set_ingredients(self, recipe, ingredients_data):
        RecipeIngredient.objects.filter(recipe=recipe).delete()
        objs = []
        for item in ingredients_data:
            ingredient = Ingredient.objects.get(id=item["id"])
            objs.append(
                RecipeIngredient(
                    recipe=recipe,
                    ingredient=ingredient,
                    amount=item["amount"],
                )
            )
        RecipeIngredient.objects.bulk_create(objs)

    def create(self, validated_data):
        tags = validated_data.pop("tags")
        ingredients_data = validated_data.pop("ingredients")
        request = self.context["request"]

        recipe = Recipe.objects.create(author=request.user, **validated_data)
        recipe.tags.set(tags)
        self._set_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags", None)
        ingredients_data = validated_data.pop("ingredients", None)

        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()

        if tags is not None:
            instance.tags.set(tags)
        if ingredients_data is not None:
            self._set_ingredients(instance, ingredients_data)

        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data


class RecipeShortSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")

    def get_image(self, obj):
        request = self.context.get("request")
        if not obj.image:
            return None
        url = obj.image.url
        return request.build_absolute_uri(url) if request else url

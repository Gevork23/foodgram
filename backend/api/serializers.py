from django.core.validators import MinValueValidator
from django.db import transaction
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Subscription,
    Tag,
    User,
)


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания пользователя"""

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "password",
        )
        extra_kwargs = {
            "password": {"write_only": True},
            "email": {"required": True},
            "username": {"required": True},
            "first_name": {"required": True},
            "last_name": {"required": True},
        }

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователя"""

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField(required=False, allow_null=True)

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

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        return (
            request
            and request.user.is_authenticated
            and Subscription.objects.filter(
                user=request.user, author=obj
            ).exists()
        )


class UserAvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для аватара пользователя"""

    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ("avatar",)


class UserPasswordSerializer(serializers.Serializer):
    """Сериализатор для смены пароля"""

    current_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Текущий пароль неверен")
        return value

    def update(self, instance, validated_data):
        instance.set_password(validated_data["new_password"])
        instance.save()
        return instance


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "slug")


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source="ingredient",
    )
    name = serializers.CharField(source="ingredient.name", read_only=True)
    measurement_unit = serializers.CharField(
        source="ingredient.measurement_unit",
        read_only=True,
    )
    amount = serializers.IntegerField(validators=[MinValueValidator(1)])

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="ingredient.id", read_only=True)
    name = serializers.CharField(source="ingredient.name", read_only=True)
    measurement_unit = serializers.CharField(
        source="ingredient.measurement_unit",
        read_only=True,
    )
    amount = serializers.IntegerField(read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        source="recipe_ingredients",
        many=True,
        read_only=True,
    )
    image = serializers.ImageField(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

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

    def get_is_favorited(self, obj):
        request = self.context.get("request")
        return (
            request
            and request.user.is_authenticated
            and Favorite.objects.filter(user=request.user, recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get("request")
        return (
            request
            and request.user.is_authenticated
            and ShoppingCart.objects.filter(
                user=request.user, recipe=obj
            ).exists()
        )


class RecipeWriteSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True, source="recipe_ingredients"
    )
    image = Base64ImageField(required=True)
    cooking_time = serializers.IntegerField(validators=[MinValueValidator(1)])

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
        read_only_fields = ("author",)

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                "Добавьте хотя бы один ингредиент"
            )

        seen = set()
        for item in value:
            ingredient = item["ingredient"]
            if ingredient.id in seen:
                raise serializers.ValidationError(
                    "Ингредиенты не должны повторяться"
                )
            seen.add(ingredient.id)
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError("Добавьте хотя бы один тег")
        tag_ids = [tag.id for tag in value]
        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError("Теги не должны повторяться")
        return value

    def _set_tags_ingredients(self, recipe, tags=None, ingredients=None):
        """
        Общий метод, чтобы не дублировать код в create/update.
        tags: список Tag или None
        ingredients: список словарей вида
        {"ingredient": Ingredient, "amount": int} или None
        """
        if tags is not None:
            recipe.tags.set(tags)

        if ingredients is not None:
            recipe.recipe_ingredients.all().delete()
            RecipeIngredient.objects.bulk_create(
                [
                    RecipeIngredient(
                        recipe=recipe,
                        ingredient=item["ingredient"],
                        amount=item["amount"],
                    )
                    for item in ingredients
                ]
            )

    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop("recipe_ingredients")
        tags_data = validated_data.pop("tags")

        validated_data["author"] = self.context["request"].user
        recipe = super().create(validated_data)

        self._set_tags_ingredients(
            recipe, tags=tags_data, ingredients=ingredients_data
        )
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop("recipe_ingredients", None)
        tags_data = validated_data.pop("tags", None)

        instance = super().update(instance, validated_data)
        self._set_tags_ingredients(
            instance, tags=tags_data, ingredients=ingredients_data
        )
        return instance


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сокращенный сериализатор для рецептов"""

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class SubscriptionSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        required=True,
    )

    id = serializers.ReadOnlyField(source="author.id")
    email = serializers.ReadOnlyField(source="author.email")
    username = serializers.ReadOnlyField(source="author.username")
    first_name = serializers.ReadOnlyField(source="author.first_name")
    last_name = serializers.ReadOnlyField(source="author.last_name")
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField(source="author.avatar", read_only=True)
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = (
            "author",
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "avatar",
            "recipes",
            "recipes_count",
        )

    def validate(self, attrs):
        request = self.context.get("request")
        if request is None:
            return attrs

        author = attrs["author"]

        if request.user == author:
            raise serializers.ValidationError(
                {"errors": "Нельзя подписаться на самого себя"}
            )

        if Subscription.objects.filter(
            user=request.user, author=author
        ).exists():
            raise serializers.ValidationError(
                {"errors": "Вы уже подписаны на этого пользователя"}
            )

        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        return Subscription.objects.create(
            user=request.user,
            author=validated_data["author"],
        )

    def get_is_subscribed(self, obj):
        return True

    def get_recipes(self, obj):
        request = self.context.get("request")
        recipes_limit = (
            request.query_params.get("recipes_limit") if request else None
        )

        qs = obj.author.recipes.all()
        if recipes_limit:
            try:
                qs = qs[: int(recipes_limit)]
            except ValueError:
                pass

        return RecipeShortSerializer(qs, many=True, context=self.context).data

    def get_recipes_count(self, obj):
        return obj.author.recipes.count()


class FavoriteCreateSerializer(serializers.ModelSerializer):
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        model = Favorite
        fields = ("recipe",)

    def validate_recipe(self, recipe):
        request = self.context.get("request")
        if (
            request
            and Favorite.objects.filter(
                user=request.user, recipe=recipe
            ).exists()
        ):
            raise serializers.ValidationError("Рецепт уже в избранном.")
        return recipe

    def create(self, validated_data):
        request = self.context["request"]
        return Favorite.objects.create(user=request.user, **validated_data)


class ShoppingCartCreateSerializer(serializers.ModelSerializer):
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        model = ShoppingCart
        fields = ("recipe",)

    def validate_recipe(self, recipe):
        request = self.context.get("request")
        if (
            request
            and ShoppingCart.objects.filter(
                user=request.user, recipe=recipe
            ).exists()
        ):
            raise serializers.ValidationError("Рецепт уже в списке покупок.")
        return recipe

    def create(self, validated_data):
        request = self.context["request"]
        return ShoppingCart.objects.create(user=request.user, **validated_data)

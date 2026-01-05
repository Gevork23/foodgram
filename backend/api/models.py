# api/models.py
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models


class User(AbstractUser):
    """Модель пользователя"""

    email = models.EmailField(
        "email address", unique=True, max_length=254, blank=False, null=False
    )
    username = models.CharField(
        "username",
        max_length=150,
        unique=True,
        blank=False,
        null=False,
        validators=[
            RegexValidator(
                regex=r"^[\w.@+-]+\Z",
                message="Username должен содержать только буквы, цифры и @/./+/-/_",
            )
        ],
    )
    first_name = models.CharField("first name", max_length=150, blank=False)
    last_name = models.CharField("last name", max_length=150, blank=False)
    avatar = models.ImageField("Аватар", upload_to="avatars/", blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        ordering = ["id"]
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.email


class Tag(models.Model):
    """Модель тегов"""

    name = models.CharField("Название тега", max_length=200, unique=True, blank=False)
    slug = models.SlugField("Уникальный слаг", max_length=200, unique=True, blank=False)

    class Meta:
        ordering = ["id"]
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиентов"""

    name = models.CharField("Название ингредиента", max_length=200, blank=False)
    measurement_unit = models.CharField(
        "Единица измерения", max_length=200, blank=False
    )

    class Meta:
        ordering = ["id"]
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "measurement_unit"], name="unique_ingredient"
            )
        ]

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецептов"""

    name = models.CharField("Название рецепта", max_length=200, blank=False)
    text = models.TextField("Описание рецепта", blank=False)
    cooking_time = models.PositiveIntegerField(
        "Время приготовления (в минутах)",
        validators=[
            MinValueValidator(
                1, message="Время приготовления должно быть не менее 1 минуты"
            )
        ],
    )
    image = models.ImageField("Изображение рецепта", upload_to="recipes/", blank=False)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="Автор рецепта",
    )
    tags = models.ManyToManyField(
        Tag, related_name="recipes", verbose_name="Теги рецепта"
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through="RecipeIngredient",
        related_name="recipes",
        verbose_name="Ингредиенты рецепта",
    )
    pub_date = models.DateTimeField("Дата публикации", auto_now_add=True)

    class Meta:
        ordering = ["-pub_date"]
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Промежуточная модель для связи рецепта и ингредиента"""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
        verbose_name="Рецепт",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
        verbose_name="Ингредиент",
    )
    amount = models.PositiveIntegerField(
        "Количество",
        validators=[MinValueValidator(1, message="Количество должно быть не менее 1")],
    )

    class Meta:
        ordering = ["id"]
        verbose_name = "Ингредиент рецепта"
        verbose_name_plural = "Ингредиенты рецепта"
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"],
                name="unique_recipe_ingredient",
            )
        ]

    def __str__(self):
        return f"{self.ingredient.name} - {self.amount}"


class Subscription(models.Model):
    """Модель подписок"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower",
        verbose_name="Подписчик",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name="Автор",
    )
    created = models.DateTimeField("Дата подписки", auto_now_add=True)

    class Meta:
        ordering = ["-created"]
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "author"], name="unique_subscription"
            ),
        ]

    def clean(self):
        """Валидация, чтобы пользователь не мог подписаться сам на себя"""
        if self.user == self.author:
            raise ValidationError("Нельзя подписаться на самого себя")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} подписан на {self.author}"


class Favorite(models.Model):
    """Модель избранных рецептов"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="Рецепт",
    )
    created = models.DateTimeField("Дата добавления", auto_now_add=True)

    class Meta:
        ordering = ["-created"]
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"
        constraints = [
            models.UniqueConstraint(fields=["user", "recipe"], name="unique_favorite")
        ]

    def __str__(self):
        return f"{self.user} - {self.recipe}"


class ShoppingCart(models.Model):
    """Модель списка покупок"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="shopping_cart",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="shopping_cart",
        verbose_name="Рецепт",
    )
    created = models.DateTimeField("Дата добавления", auto_now_add=True)

    class Meta:
        ordering = ["-created"]
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_shopping_cart"
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.recipe}"

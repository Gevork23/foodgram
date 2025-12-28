# backend/recipes/admin.py
from django.contrib import admin
from django.utils.html import format_html

from .models import Tag, Ingredient, Recipe, RecipeIngredient


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "color", "slug")
    search_fields = ("name", "slug")
    list_filter = ("name",)
    ordering = ("name",)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "measurement_unit")
    search_fields = ("name",)
    list_filter = ("measurement_unit",)
    ordering = ("name",)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    autocomplete_fields = ("ingredient",)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "author",
        "cooking_time",
        "ingredients_count",
        "tags_list",
        "image_preview",
        "created_display",
    )
    search_fields = ("name", "author__username", "author__email")
    list_filter = ("tags",)
    filter_horizontal = ("tags",)
    inlines = (RecipeIngredientInline,)
    readonly_fields = ("image_preview",)

    def ingredients_count(self, obj):
        # RecipeIngredient usually has related_name "recipe_ingredients" or default "recipeingredient_set"
        if hasattr(obj, "recipe_ingredients"):
            return obj.recipe_ingredients.count()
        return obj.recipeingredient_set.count()
    ingredients_count.short_description = "Ингредиентов"

    def tags_list(self, obj):
        return ", ".join(obj.tags.values_list("name", flat=True))
    tags_list.short_description = "Теги"

    def image_preview(self, obj):
        if not getattr(obj, "image", None):
            return "—"
        try:
            return format_html(
                '<img src="{}" style="max-height: 80px; max-width: 120px; object-fit: cover;" />',
                obj.image.url,
            )
        except Exception:
            return "—"
    image_preview.short_description = "Изображение"

    def created_display(self, obj):
        """
        Не привязываемся к конкретному имени поля, чтобы админка не падала.
        Часто в Foodgram бывает pub_date/created/created_at.
        """
        for field_name in ("created_at", "created", "pub_date", "date_created"):
            if hasattr(obj, field_name):
                value = getattr(obj, field_name)
                return value
        return "—"
    created_display.short_description = "Создано"

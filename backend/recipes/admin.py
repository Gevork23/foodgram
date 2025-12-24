# recipes/admin.py
from django.contrib import admin
from .models import Tag, Ingredient, Recipe, RecipeIngredient

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')
    search_fields = ('name', 'slug')
    list_filter = ('name',)

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)

class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'cooking_time', 'created_at')
    search_fields = ('name', 'author__username')
    list_filter = ('tags', 'created_at')
    filter_horizontal = ('tags',)
    inlines = [RecipeIngredientInline]
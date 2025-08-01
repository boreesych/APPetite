from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import Ingredient, Recipe, RecipeIngredients, Tag


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)


class RecipeIngredientsInline(admin.TabularInline):
    model = RecipeIngredients
    min_num = 1
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = [RecipeIngredientsInline]
    list_display = (
        'name', 'author',
        'get_ingredients', 'get_tags',
        'pub_date', 'pk', 'get_image'
    )
    # exclude = ('short_link',)
    search_fields = ('name', 'author')
    list_filter = ('tags__name',)

    @admin.display(description='Ингредиенты')
    def get_ingredients(self, obj):
        return [ingredients.name for ingredients in obj.ingredients.all()]

    @admin.display(description='Теги')
    def get_tags(self, obj):
        return [tags.name for tags in obj.tags.all()]

    @admin.display(description='Фото')
    def get_image(self, obj):
        return mark_safe(f'<img src={obj.image.url} width="65" height="40">')

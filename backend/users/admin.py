from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group

from .models import User


admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username',
                    'first_name', 'last_name',
                    'get_recipes_count', 'get_subscribers_count',
                    'id')
    search_fields = ('username', 'email')

    @admin.display(description='Количество рецептов')
    def get_recipes_count(self, obj):
        return obj.recipes.count()

    @admin.display(description='Количество подписчиков')
    def get_subscribers_count(self, obj):
        return obj.subscribing.count()

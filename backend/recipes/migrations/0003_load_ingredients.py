import json
from django.conf import settings
from django.db import migrations


file_json = open(
    settings.BASE_DIR / 'data/ingredients.json', 'r', encoding='utf-8')
INGREDIENT_DATA = json.load(file_json)


def add_ingredients(apps, schema_editor):
    Ingredient = apps.get_model("recipes", "Ingredient")
    for ingredient in INGREDIENT_DATA:
        new_ingredient = Ingredient(**ingredient)
        new_ingredient.save()


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0002_initial'),
    ]

    operations = [
        migrations.RunPython(add_ingredients),
    ]

from django.db import migrations


TAG_DATA = [
    {'name': 'Завтрак', 'slug': 'breakfast'},
    {'name': 'Обед', 'slug': 'lunch'},
    {'name': 'Ужин', 'slug': 'dinner'},
    {'name': 'Десерт', 'slug': 'dessert'},
]

def add_tags(apps, schema_editor):
    Tag = apps.get_model('recipes', 'Tag')
    for tag in TAG_DATA:
        new_tag = Tag(**tag)
        new_tag.save()

class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0003_load_ingredients'),
    ]

    operations = [
        migrations.RunPython(add_tags),
    ]

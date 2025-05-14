import os
from django.db import migrations
from django.core.management import call_command
from django.conf import settings

def load_categories(apps, schema_editor):
    Category = apps.get_model('website', 'Category')
    Category.objects.all().delete()
    fixture_path = os.path.join(settings.BASE_DIR, 'website', 'fixtures', 'categories.yaml')
    if os.path.exists(fixture_path):
        call_command('loaddata', fixture_path, verbosity=0)
    else:
        raise FileNotFoundError(f"Fixture file not found at {fixture_path}")

def unload_categories(apps, schema_editor):
    Category = apps.get_model('website', 'Category')
    Category.objects.filter(name__in=['Technical', 'Billing', 'General Inquiry']).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('website', '0001_initial'),  # Ensure this matches your initial migration
    ]

    operations = [
        migrations.RunPython(load_categories, reverse_code=unload_categories),
    ]

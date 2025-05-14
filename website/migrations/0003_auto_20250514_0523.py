from django.db import migrations
from django.contrib.auth.models import Group

def create_groups(apps, schema_editor):
    Group.objects.get_or_create(name='Normal Users')
    Group.objects.get_or_create(name='Technical Agents')
    Group.objects.get_or_create(name='HR Agents')
    Group.objects.get_or_create(name='Consultants')

def remove_groups(apps, schema_editor):
    Group.objects.filter(name__in=['Normal Users', 'Technical Agents', 'HR Agents', 'Consultants']).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('website', '0002_auto_20250514_0522'),
    ]

    operations = [
        migrations.RunPython(create_groups, reverse_code=remove_groups),
    ]

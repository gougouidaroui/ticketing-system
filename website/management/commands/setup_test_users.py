from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

class Command(BaseCommand):
    help = 'Set up test users with groups'

    def handle(self, *args, **options):
        User = get_user_model()
        # Create users
        normal_user, _ = User.objects.get_or_create(username='user1', defaults={
            'email': 'user1@example.com', 'phone_number': '+1234567890'
        })
        normal_user.set_password('password123')
        normal_user.save()

        tech_agent, _ = User.objects.get_or_create(username='tech1', defaults={
            'email': 'tech1@example.com', 'phone_number': '+1234567891', 'is_staff': True
        })
        tech_agent.set_password('password123')
        tech_agent.save()

        hr_agent, _ = User.objects.get_or_create(username='hr1', defaults={
            'email': 'hr1@example.com', 'phone_number': '+1234567892', 'is_staff': True
        })
        hr_agent.set_password('password123')
        hr_agent.save()

        consultant, _ = User.objects.get_or_create(username='consultant1', defaults={
            'email': 'consultant1@example.com', 'phone_number': '+1234567893', 'is_staff': True
        })
        consultant.set_password('password123')
        consultant.save()

        admin, _ = User.objects.get_or_create(username='admin1', defaults={
            'email': 'admin1@example.com', 'phone_number': '+1234567894', 'is_staff': True, 'is_superuser': True
        })
        admin.set_password('password123')
        admin.save()

        # Assign groups
        normal_user.groups.add(Group.objects.get(name='Normal Users'))
        tech_agent.groups.add(Group.objects.get(name='Technical Agents'))
        hr_agent.groups.add(Group.objects.get(name='HR Agents'))
        consultant.groups.add(Group.objects.get(name='Consultants'))

        self.stdout.write(self.style.SUCCESS('Test users and groups set up successfully!'))

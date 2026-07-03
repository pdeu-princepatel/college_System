from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from admin_dashboard.models import Staff


class Command(BaseCommand):
    help = 'Creates a new staff user for the admin dashboard'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str)
        parser.add_argument('password', type=str)

    def handle(self, *args, **kwargs):
        username = kwargs['username']
        password = kwargs['password']

        if Staff.objects.filter(username=username).exists():
            self.stdout.write(self.style.ERROR(f'Staff user "{username}" already exists.'))
            return

        Staff.objects.create(
            username=username,
            password=make_password(password)
        )
        self.stdout.write(self.style.SUCCESS(f'Successfully created staff user: {username}'))
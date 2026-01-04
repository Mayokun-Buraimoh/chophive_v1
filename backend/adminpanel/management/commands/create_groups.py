"""
Management command to create required groups for adminpanel
"""
from django.core.management.base import BaseCommand
from adminpanel.permissions import ensure_groups_exist


class Command(BaseCommand):
    help = 'Creates the required groups (Admin, Rider) for the admin panel'

    def handle(self, *args, **options):
        from adminpanel.permissions import ensure_groups_exist
        ensure_groups_exist()
        self.stdout.write(
            self.style.SUCCESS('Successfully created/verified required groups: Admin, Rider')
        )



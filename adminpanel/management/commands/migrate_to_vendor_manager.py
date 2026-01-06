"""
Management command to migrate from CafeteriaManager group to Vendor-based permissions.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from userauths.models import User
from core.models import Vendor


class Command(BaseCommand):
    help = 'Migrate users from CafeteriaManager group to Vendor-based permissions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete-group',
            action='store_true',
            help='Delete the CafeteriaManager group after migration',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(self.style.WARNING('Cafeteria Manager to Vendor Manager Migration'))
        self.stdout.write(self.style.WARNING('=' * 70))
        
        # Check if CafeteriaManager group exists
        try:
            cafeteria_group = Group.objects.get(name='CafeteriaManager')
        except Group.DoesNotExist:
            self.stdout.write(self.style.SUCCESS('✓ CafeteriaManager group does not exist. Nothing to migrate.'))
            return
        
        # Get all users in the CafeteriaManager group
        cafeteria_managers = User.objects.filter(groups=cafeteria_group)
        count = cafeteria_managers.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS(f'✓ No users found in CafeteriaManager group.'))
            
            if options['delete_group']:
                cafeteria_group.delete()
                self.stdout.write(self.style.SUCCESS('✓ Deleted CafeteriaManager group.'))
            else:
                self.stdout.write(self.style.WARNING('  Use --delete-group flag to delete the empty group.'))
            return
        
        self.stdout.write(self.style.WARNING(f'\nFound {count} user(s) in CafeteriaManager group:\n'))
        
        # List users and their vendor status
        for user in cafeteria_managers:
            has_vendor = hasattr(user, 'vendor')
            vendor_name = user.vendor.name if has_vendor else 'N/A'
            status = '✓ Linked' if has_vendor else '✗ NOT LINKED'
            
            self.stdout.write(f'  • {user.username} ({user.email})')
            self.stdout.write(f'    Vendor: {vendor_name} - {status}')
        
        # Count users without vendor
        users_without_vendor = [u for u in cafeteria_managers if not hasattr(u, 'vendor')]
        
        if users_without_vendor:
            self.stdout.write(self.style.ERROR(f'\n⚠ WARNING: {len(users_without_vendor)} user(s) do NOT have a Vendor linked!'))
            self.stdout.write(self.style.WARNING('\nAction Required:'))
            self.stdout.write('  1. Create Vendor records for these users in Django admin')
            self.stdout.write('  2. Link each Vendor to the user via the "manager" field')
            self.stdout.write('  3. Run this command again with --delete-group flag\n')
        else:
            self.stdout.write(self.style.SUCCESS('\n✓ All users have Vendor records linked!'))
            
            if options['delete_group']:
                # Remove users from the group
                for user in cafeteria_managers:
                    user.groups.remove(cafeteria_group)
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Removed {user.username} from CafeteriaManager group'))
                
                # Delete the group
                cafeteria_group.delete()
                self.stdout.write(self.style.SUCCESS('\n✓ Deleted CafeteriaManager group.'))
                self.stdout.write(self.style.SUCCESS('✓ Migration complete!'))
            else:
                self.stdout.write(self.style.WARNING('\nTo complete migration:'))
                self.stdout.write('  Run: python manage.py migrate_to_vendor_manager --delete-group\n')
        
        self.stdout.write(self.style.WARNING('=' * 70))

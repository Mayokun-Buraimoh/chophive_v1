"""
Permission utilities for role-based access control.
"""
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied


# Group names
ADMIN_GROUP = 'Admin'
CAFETERIA_MANAGER_GROUP = 'CafeteriaManager'
RIDER_GROUP = 'Rider'


def get_user_role(user):
    """
    Get the primary role of a user based on their groups.
    Returns: 'admin', 'vendor_manager', 'rider', or None
    """
    if not user.is_authenticated:
        return None
    
    if user.groups.filter(name=ADMIN_GROUP).exists():
        return 'admin'
    elif is_vendor_manager(user):
        return 'vendor_manager'
    elif user.groups.filter(name=RIDER_GROUP).exists():
        return 'rider'
    
    return None


def is_admin(user):
    """Check if user is in Admin group."""
    return user.is_authenticated and user.groups.filter(name=ADMIN_GROUP).exists()


def is_vendor_manager(user):
    """Check if user has a vendor profile assigned OR is in CafeteriaManager group."""
    if not user.is_authenticated:
        return False
    return hasattr(user, 'vendor') or user.groups.filter(name=CAFETERIA_MANAGER_GROUP).exists()


def is_rider(user):
    """Check if user is in Rider group."""
    return user.is_authenticated and user.groups.filter(name=RIDER_GROUP).exists()


def require_role(*allowed_roles):
    """
    Decorator to require specific roles for a view.
    Usage: @require_role('admin', 'vendor_manager')
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path())
            
            user_role = get_user_role(request.user)
            if user_role not in allowed_roles:
                raise PermissionDenied("You don't have permission to access this page.")
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def ensure_groups_exist():
    """
    Ensure that the required groups exist in the database.
    Call this in a management command or migration.
    """
    groups = [ADMIN_GROUP, CAFETERIA_MANAGER_GROUP, RIDER_GROUP]
    for group_name in groups:
        Group.objects.get_or_create(name=group_name)


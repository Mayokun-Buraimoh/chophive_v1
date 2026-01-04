"""
Template tags for adminpanel permissions
"""
from django import template
from adminpanel.permissions import get_user_role, is_admin, is_vendor_manager, is_rider

register = template.Library()


@register.simple_tag
def get_user_role_tag(user):
    """Get user role as template variable"""
    return get_user_role(user)


@register.filter
def is_user_admin(user):
    """Check if user is admin"""
    return is_admin(user)


@register.filter
def is_user_vendor_manager(user):
    """Check if user is vendor manager"""
    return is_vendor_manager(user)


@register.filter
def is_user_rider(user):
    """Check if user is rider"""
    return is_rider(user)


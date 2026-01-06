"""
Middleware for role-based redirects after login.
"""
from django.shortcuts import redirect
from django.urls import reverse
from .permissions import get_user_role


class RoleBasedRedirectMiddleware:
    """
    Redirect users to their appropriate dashboard after login.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only process authenticated users
        if request.user.is_authenticated:
            # Skip redirect for admin panel URLs and static files
            path = request.path
            
            # Skip if already on an admin panel page
            if path.startswith('/admin/'):
                # Check if user is trying to access wrong dashboard
                role = get_user_role(request.user)
                
                # Redirect to appropriate dashboard if accessing root /admin/
                if path == '/admin/' or path == '/admin':
                    if role == 'admin':
                        return redirect('/admin/dashboard/')
                    elif role == 'vendor_manager':
                        return redirect('/admin/vendor-manager/')
                    elif role == 'rider':
                        return redirect('/admin/rider-dashboard/')
                
                # Block access to wrong dashboards
                if path.startswith('/admin/dashboard/') and role != 'admin':
                    if role == 'vendor_manager':
                        return redirect('/admin/vendor-manager/')
                    elif role == 'rider':
                        return redirect('/admin/rider-dashboard/')
                
                if path.startswith('/admin/vendor-manager/') and role != 'vendor_manager':
                    if role == 'admin':
                        return redirect('/admin/dashboard/')
                    elif role == 'rider':
                        return redirect('/admin/rider-dashboard/')
                
                if path.startswith('/admin/rider-dashboard/') and role != 'rider':
                    if role == 'admin':
                        return redirect('/admin/dashboard/')
                    elif role == 'vendor_manager':
                        return redirect('/admin/vendor-manager/')

        response = self.get_response(request)
        return response


"""
Profile Management Views
"""
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from userauths.models import Profile
from adminpanel.permissions import get_user_role


class ProfileView(TemplateView):
    """User Profile Page"""
    template_name = 'adminpanel/profile/profile.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('adminpanel:login')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from adminpanel.permissions import get_user_role
        
        # Get or create profile
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        
        raw_role = get_user_role(self.request.user)  # e.g. "vendor_manager"
        context['profile'] = profile
        context['user'] = self.request.user
        if raw_role:
            context['user_role'] = raw_role.replace("_", " ").title()
        else:
            context['user_role'] = "User"
        # context['user_role'] = get_user_role(self.request.user)
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle profile updates"""
        profile, created = Profile.objects.get_or_create(user=request.user)
        
        # Update profile fields
        if 'username' in request.POST:
            profile.username = request.POST.get('username', '')
        if 'phone' in request.POST:
            profile.phone = request.POST.get('phone', '')
        if 'hostel' in request.POST:
            profile.hostel = request.POST.get('hostel', '')
        if 'room_number' in request.POST:
            profile.room_number = request.POST.get('room_number', '')
        if 'department' in request.POST:
            profile.department = request.POST.get('department', '')
        if 'level' in request.POST:
            try:
                profile.level = int(request.POST.get('level', 0))
            except ValueError:
                pass
        
        # Handle image upload
        if 'image' in request.FILES:
            profile.image = request.FILES['image']
        
        profile.save()
        
        # Update user fields
        if 'first_name' in request.POST:
            request.user.first_name = request.POST.get('first_name', '')
        if 'last_name' in request.POST:
            request.user.last_name = request.POST.get('last_name', '')
        if 'email' in request.POST:
            request.user.email = request.POST.get('email', '')
        request.user.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('adminpanel:profile')


class ChangePasswordView(TemplateView):
    """Change Password View"""
    template_name = 'adminpanel/profile/change_password.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('adminpanel:login')
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('adminpanel:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
            return render(request, self.template_name, {'form': form})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from adminpanel.permissions import get_user_role
        context['form'] = PasswordChangeForm(self.request.user)
        context['user_role'] = get_user_role(self.request.user)
        return context


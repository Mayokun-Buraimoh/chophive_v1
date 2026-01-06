"""
Admin Dashboard Views
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from core.models import Order, Vendor, OrderItem
from userauths.models import User
from adminpanel.permissions import is_admin, require_role, ADMIN_GROUP, CAFETERIA_MANAGER_GROUP, RIDER_GROUP
from django.views.generic import ListView


class AdminDashboardView(TemplateView):
    """Admin Dashboard - Main overview page"""
    template_name = 'adminpanel/dashboard/admin_dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('adminpanel:login')
        if not is_admin(request.user):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("You don't have permission to access this page.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from adminpanel.permissions import get_user_role
        
        # Total Orders
        total_orders = Order.objects.count()
        
        # Total Vendors
        total_vendors = Vendor.objects.count()
        
        # Total Vendor Managers (users with vendor relationships OR in CafeteriaManager group)
        vendor_managers = User.objects.filter(
            Q(vendor__isnull=False) | Q(groups__name=CAFETERIA_MANAGER_GROUP)
        ).distinct().count()
        
        # Total Riders
        riders = User.objects.filter(groups__name=RIDER_GROUP).count()
        
        # Total Revenue (sum of all paid orders)
        total_revenue = Order.objects.filter(
            payment_status='Paid'
        ).aggregate(total=Sum('total'))['total'] or 0
        
        # Recent orders (last 10)
        recent_orders = Order.objects.select_related('buyer', 'vendor').prefetch_related('items').order_by('-created_at')[:10]
        
        # Orders by status
        orders_by_status = Order.objects.values('status').annotate(count=Count('id'))
        
        # Today's orders
        today = timezone.now().date()
        today_orders = Order.objects.filter(created_at__date=today).count()
        
        context.update({
            'user_role': get_user_role(self.request.user),
            'total_orders': total_orders,
            'total_vendors': total_vendors,
            'total_vendor_managers': vendor_managers,
            'total_riders': riders,
            'total_revenue': total_revenue,
            'recent_orders': recent_orders,
            'orders_by_status': orders_by_status,
            'paid_orders_count': Order.objects.filter(status='Paid').count(),
            'today_orders': today_orders,
            'today': today,
        })
        
        return context


class AdminOrderListView(ListView):
    """View for managing and verifying all orders (Admin only)"""
    model = Order
    template_name = 'adminpanel/dashboard/admin_orders.html'
    context_object_name = 'orders'
    paginate_by = 25
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('adminpanel:login')
        if not is_admin(request.user):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("You don't have permission to access this page.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        # Allow multi-status filtering via query params
        status_filter = self.request.GET.get('status')
        queryset = Order.objects.select_related('buyer', 'vendor', 'hostel').prefetch_related('items').order_by('-created_at')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from adminpanel.permissions import get_user_role
        context.update({
            'user_role': get_user_role(self.request.user),
            'status_choices': Order.STATUS_CHOICES,
            'current_status': self.request.GET.get('status', 'all'),
        })
        return context


def logout_view(request):
    """Logout view"""
    from django.contrib.auth import logout
    logout(request)
    return redirect('adminpanel:login')


def login_view(request):
    """Custom login view that redirects based on role"""
    if request.user.is_authenticated:
        from adminpanel.permissions import get_user_role
        role = get_user_role(request.user)
        if role == 'admin':
            return redirect('adminpanel:admin_dashboard')
        elif role == 'vendor_manager':
            return redirect('adminpanel:vendor_dashboard')
        elif role == 'rider':
            return redirect('adminpanel:rider_dashboard')
        else:
            return redirect('/django-admin/')  # Default Django admin
    
    from django.contrib.auth.views import LoginView
    from django.contrib.auth.forms import AuthenticationForm
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            from django.contrib.auth import login
            from adminpanel.permissions import get_user_role
            
            user = form.get_user()
            login(request, user)
            
            # Redirect based on role
            role = get_user_role(user)
            if role == 'admin':
                return redirect('adminpanel:admin_dashboard')
            elif role == 'vendor_manager':
                return redirect('adminpanel:vendor_dashboard')
            elif role == 'rider':
                return redirect('adminpanel:rider_dashboard')
            else:
                return redirect('/django-admin/')
    else:
        form = AuthenticationForm()
    
    return render(request, 'adminpanel/login.html', {'form': form})


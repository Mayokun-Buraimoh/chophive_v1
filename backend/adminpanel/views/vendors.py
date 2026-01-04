from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, TemplateView
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.utils import timezone
from django.http import JsonResponse
from core.models import Vendor, Order
from adminpanel.permissions import is_admin, get_user_role


class VendorsListView(ListView):
    """List all vendors with order counts"""
    model = Vendor
    template_name = 'adminpanel/vendors/vendors_list.html'
    context_object_name = 'vendors'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('adminpanel:login')
        if not is_admin(request.user):
            raise PermissionDenied("You don't have permission to access this page.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        # Annotate with order counts
        return Vendor.objects.annotate(
            total_orders=Count('orders'),
            active_orders=Count('orders', filter=Q(orders__status__in=['Pending', 'Processing']))
        ).order_by('-is_active', 'name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from adminpanel.permissions import get_user_role
        context['user_role'] = get_user_role(self.request.user)
        context['total_vendors'] = Vendor.objects.count()
        context['active_vendors'] = Vendor.objects.filter(is_active=True).count()
        return context


class VendorDashboardView(TemplateView):
    """Vendor Manager Dashboard"""
    template_name = 'adminpanel/vendors/vendor_dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('adminpanel:login')
        # Check if user has a vendor profile
        if not hasattr(request.user, 'vendor'):
             # If admin, maybe redirect to admin dashboard or show error
            if is_admin(request.user):
                return redirect('adminpanel:admin_dashboard')
            raise PermissionDenied("You don't have a vendor account associated with this user.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vendor = self.request.user.vendor
        today = timezone.now().date()
        
        # Get active tab from request
        active_tab = self.request.GET.get('tab', 'today')
        
        # Base query filtered by vendor
        base_qs = Order.objects.filter(vendor=vendor).select_related('buyer', 'vendor').prefetch_related('items')
        
        if active_tab == 'today':
            # Orders Today
            orders = base_qs.filter(created_at__date=today).order_by('-created_at')
        else:
            # History (all orders)
            orders = base_qs.order_by('-created_at')[:100]
        
        # Group orders by hostel/location
        orders_by_hostel = {}
        for order in orders:
            hostel = order.hostel or 'Unknown'
            if hostel not in orders_by_hostel:
                orders_by_hostel[hostel] = []
            orders_by_hostel[hostel].append(order)
        
        # Order statistics for this vendor
        today_qs = Order.objects.filter(vendor=vendor, created_at__date=today)
        
        today_orders_count = today_qs.count()
        pending_count = today_qs.filter(status='Pending').count()
        packaging_count = today_qs.filter(status='Processing').count()
        delivered_count = today_qs.filter(status='Delivered').count()
        
        context.update({
            'user_role': get_user_role(self.request.user),
            'vendor': vendor,
            'active_tab': active_tab,
            'orders': orders,
            'orders_by_hostel': orders_by_hostel,
            'today_orders_count': today_orders_count,
            'pending_count': pending_count,
            'packaging_count': packaging_count,
            'delivered_count': delivered_count,
            'today': today,
        })
        
        return context


def update_order_status(request, order_id):
    """Update order status (AJAX endpoint)"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        try:
            # Ensure order belongs to the vendor
            if hasattr(request.user, 'vendor'):
                order = Order.objects.get(id=order_id, vendor=request.user.vendor)
            elif is_admin(request.user):
                 order = Order.objects.get(id=order_id)
            else:
                return JsonResponse({'error': 'Unauthorized'}, status=403)

            new_status = request.POST.get('status')
            
            if new_status in ['Pending', 'Processing', 'Delivered', 'Cancelled']:
                order.status = new_status
                order.save()
                return JsonResponse({'success': True, 'status': new_status})
            else:
                return JsonResponse({'error': 'Invalid status'}, status=400)
        except Order.DoesNotExist:
            return JsonResponse({'error': 'Order not found'}, status=404)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def toggle_vendor_status(request, vendor_id):
    """Toggle vendor active/inactive status"""
    if not request.user.is_authenticated or not is_admin(request.user):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        try:
            vendor = get_object_or_404(Vendor, id=vendor_id)
            vendor.is_active = not vendor.is_active
            vendor.save()
            
            return JsonResponse({
                'success': True,
                'is_active': vendor.is_active,
                'message': f'Vendor {"activated" if vendor.is_active else "deactivated"} successfully'
            })
        except Exception as e:
            from django.http import JsonResponse
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


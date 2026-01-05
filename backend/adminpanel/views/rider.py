"""
Rider Dashboard Views
"""
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.db.models import Q
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from core.models import Order, DeliveryBatch
from adminpanel.permissions import is_rider, get_user_role


class RiderDashboardView(TemplateView):
    """Rider Dashboard"""
    template_name = 'adminpanel/rider/rider_dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('adminpanel:login')
        if not is_rider(request.user):
            raise PermissionDenied("You don't have permission to access this page.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get all delivery batches to show as tabs
        all_batches = DeliveryBatch.objects.filter(is_active=True).order_by('cutoff_time')
        
        # Get current date
        today = timezone.now().date()

        # Get active tab from request
        active_tab = self.request.GET.get('tab', '')
        
        # Set default tab if not provided or invalid
        if not active_tab or (active_tab not in ['scheduled'] and not all_batches.filter(name=active_tab).exists()):
            if all_batches.exists():
                active_tab = all_batches.first().name
            else:
                active_tab = 'scheduled'

        # Get assigned hostels for this rider
        assigned_hostels = []
        if hasattr(user, 'rider_profile'):
            assigned_hostels = user.rider_profile.hostels.all()
        
        # Base filters
        base_filters = Q(status__in=['Processing', 'Pending'])
        if not user.is_superuser:
            base_filters &= Q(hostel__in=assigned_hostels)

        # Filter orders based on active tab
        if active_tab == 'scheduled':
             orders = Order.objects.filter(
                base_filters,
                created_at__date__gt=today
            ).select_related('buyer', 'vendor').prefetch_related('items').order_by('created_at')
        else:
            orders = Order.objects.filter(
                base_filters,
                delivery_batch__name=active_tab,
                created_at__date=today
            ).select_related('buyer', 'vendor', 'hostel').prefetch_related('items').order_by('created_at')

        # Count orders per batch dynamically
        batch_data = []
        for batch in all_batches:
            count = Order.objects.filter(
                base_filters,
                delivery_batch=batch,
                created_at__date=today
            ).count()
            batch_data.append({
                'name': batch.name,
                'count': count,
            })
        
        scheduled_count = Order.objects.filter(
            base_filters,
            created_at__date__gt=today
        ).count()

        context.update({
            'user_role': get_user_role(self.request.user),
            'active_tab': active_tab,
            'orders': orders,
            'batch_data': batch_data,
            'assigned_hostels': assigned_hostels,
            'scheduled_count': scheduled_count,
            'today': today,
        })

        
        return context



def update_delivery_status(request, order_id):
    """Update delivery status (AJAX endpoint)"""
    if not request.user.is_authenticated or not is_rider(request.user):
        from django.http import JsonResponse
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        from django.http import JsonResponse
        try:
            order = Order.objects.get(id=order_id)
            
            # Check if rider is assigned to this order's hostel
            if not request.user.is_superuser:
                if not hasattr(request.user, 'rider_profile') or (order.hostel and order.hostel not in request.user.rider_profile.hostels.all()):
                    return JsonResponse({'error': 'You are not assigned to this hostel'}, status=403)
            
            new_status = request.POST.get('status')
            
            if new_status == 'Delivered':

                order.status = 'Delivered'
                order.save()
                
                from django.http import JsonResponse
                return JsonResponse({'success': True, 'status': 'Delivered'})
            else:
                from django.http import JsonResponse
                return JsonResponse({'error': 'Invalid status'}, status=400)
        except Order.DoesNotExist:
            from django.http import JsonResponse
            return JsonResponse({'error': 'Order not found'}, status=404)
    
    from django.http import JsonResponse
    return JsonResponse({'error': 'Method not allowed'}, status=405)


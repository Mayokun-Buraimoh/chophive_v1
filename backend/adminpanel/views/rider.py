"""
Rider Dashboard Views
"""
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.db.models import Q
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from core.models import Order
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
        from adminpanel.permissions import get_user_role
        
        # Get active tab from request
        active_tab = self.request.GET.get('tab', '1pm')
        
        today = timezone.now().date()
        
        # Filter orders based on batch
        if active_tab == '1pm':
            orders = Order.objects.filter(
                delivery_batch='1pm',
                created_at__date=today,
                status__in=['Processing', 'Pending']
            ).select_related('buyer', 'vendor').prefetch_related('items').order_by('created_at')
        elif active_tab == '6pm':
            orders = Order.objects.filter(
                delivery_batch='6pm',
                created_at__date=today,
                status__in=['Processing', 'Pending']
            ).select_related('buyer', 'vendor').prefetch_related('items').order_by('created_at')
        else:  # scheduled
            orders = Order.objects.filter(
                created_at__date__gt=today,
                status__in=['Processing', 'Pending']
            ).select_related('buyer', 'vendor').prefetch_related('items').order_by('created_at')
        
        # Count orders per batch
        batch_1pm_count = Order.objects.filter(
            delivery_batch='1pm',
            created_at__date=today,
            status__in=['Processing', 'Pending']
        ).count()
        
        batch_6pm_count = Order.objects.filter(
            delivery_batch='6pm',
            created_at__date=today,
            status__in=['Processing', 'Pending']
        ).count()
        
        scheduled_count = Order.objects.filter(
            created_at__date__gt=today,
            status__in=['Processing', 'Pending']
        ).count()
        
        context.update({
            'user_role': get_user_role(self.request.user),
            'active_tab': active_tab,
            'orders': orders,
            'batch_1pm_count': batch_1pm_count,
            'batch_6pm_count': batch_6pm_count,
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
        try:
            order = Order.objects.get(id=order_id)
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


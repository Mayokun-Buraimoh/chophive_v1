from django.shortcuts import render, get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny
from userauths.models import User
from core.models import Order
from core.serializers import OrderSerializer

# Create your views here.

class OrdersAPIView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Order.objects.none()
        
        # Return only orders with payment_status="Processing" (not paid yet)
        orders = Order.objects.filter(buyer=user, payment_status="Processing").order_by('-created_at')
        
        orders = Order.objects.filter(
        buyer=user,
        payment_status__in=["Processing", "Paid"]
        ).order_by('-created_at')
 
        return orders

class OrdersDetailAPIView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = (AllowAny,)
    lookup_field = 'user_id'

    def get_object(self):
        user_id = self.kwargs['user_id']
        order_oid = self.kwargs['order_oid']

        user = get_object_or_404(User, id=user_id)
        
        # Get order by oid and buyer, with payment_status="Processing" (not paid yet)
        order = get_object_or_404(Order, buyer=user, payment_status="Processing", oid=order_oid)
        return order
    
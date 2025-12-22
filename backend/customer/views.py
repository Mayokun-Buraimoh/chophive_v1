from django.shortcuts import render

from rest_framework import generics
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
        user = User.objects.get(id=user_id)
        orders = Order.objects.filter(buyer=user, payment_status="paid")
        return orders

class OrdersDetailAPIView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = (AllowAny,)
    lookup_field = 'user_id'

    def get_object(self):
        user_id = self.kwargs['user_id']
        order_oid = self.kwargs['order_oid']

        user = User.objects.get(id=user_id)

        order = Order.objects.get(buyer=user, payment_status="paid", oid=order_oid)
        return order
    
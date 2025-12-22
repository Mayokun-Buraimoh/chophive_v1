from decimal import Decimal
from collections import defaultdict
from django.shortcuts import get_object_or_404, render
from django.http import Http404
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound

from core.models import Cart, CartItem, Category, FoodItem, Order, OrderItem, Vendor
from core.serializers import CartSerializer, CategorySerializer, FoodItemSerializer, OrderSerializer, VendorDetailSerializer, VendorSerializer
from userauths.models import User, Profile
from userauths.serializers import ProfileSerializer

class CategoryListView(generics.ListAPIView):
    """
    List all food categories or create a new category (admin only).
    Endpoint: GET /api/v1/categories/ - List all categories (public)
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    
class VendorListView(generics.ListAPIView):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    permission_classes = [AllowAny]
    
class VendorDetailView(generics.RetrieveAPIView):
    queryset = Vendor.objects.all()
    serializer_class = VendorDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'
    lookup_url_kwarg = 'vendor_id'
    
class FoodItemListView(generics.ListAPIView):
    queryset = FoodItem.objects.all()
    serializer_class = FoodItemSerializer
    permission_classes = [AllowAny]
    
class FoodItemDetailView(generics.RetrieveAPIView):
    queryset = FoodItem.objects.all()
    serializer_class = FoodItemSerializer
    permission_classes = [AllowAny]
    
class CartAPIView(generics.ListCreateAPIView):
    """
    List or create cart items.
    Endpoint: GET/POST /api/v1/cart/
    """
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        payload = request.data
        
        item_id = payload['item_id']
        user_id = payload['user_id']
        qty = payload['qty']
        price = payload['price']
        delivery_fee = payload['shipping_amount']
        service_fee = payload['service_fee']
        cart_id= payload['cart_id']
        
        item = FoodItem.objects.get(id=item_id)
        if user_id != "undefined":
            user = User.objects.get(id=user_id)
        else:
            user=None   
            
        cart = Cart.objects.filter(cart_id=cart_id, food_item=item).first()
        
        if cart:
            cart.food_item = item
            cart.user = user
            cart.qty = qty
            cart.price = price
            cart.sub_total = Decimal(price) * int(qty)
            cart.delivery_fee = Decimal(delivery_fee) * int(qty)
            cart.service_fee = Decimal(service_fee) 
            cart.total_amount = cart.sub_total + cart.delivery_fee + cart.service_fee
            cart.save()
            return Response({'message':"Cart updated successfully"}, status=status.HTTP_200_OK)
        
        else:
            cart = Cart() 
            cart.food_item = item
            cart.user = user
            cart.qty = qty
            cart.price = price 
            cart.sub_total = Decimal(price) * int(qty)
            cart.delivery_fee = Decimal(delivery_fee) * int(qty)
            cart.service_fee = Decimal(service_fee) 
            cart.cart_id = cart_id
            cart.total_amount = cart.sub_total + cart.delivery_fee + cart.service_fee
            cart.save()
            return Response({'message':"Cart created successfully"}, status=status.HTTP_201_CREATED)
   
class CustomerUpdateProfileView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update the authenticated user's profile.
    Endpoint: GET/PUT/PATCH /api/v1/profile/ or /api/v1/profile/<pid>/
    Users can only access and update their own profile.
    """
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return only the authenticated user's profile."""
        return Profile.objects.filter(user=self.request.user)
    
    def get_object(self):
        """Get the authenticated user's profile."""
        # If pid is provided in URL, validate it belongs to the user
        pid = self.kwargs.get('pid')
        if pid:
            try:
                profile = Profile.objects.get(pid=pid, user=self.request.user)
                return profile
            except Profile.DoesNotExist:
                raise NotFound({"error": "Profile not found"})
        
        # Otherwise, return the user's profile directly (most common case)
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return profile
    
class CartItemDeleteAPIView(generics.DestroyAPIView):
    """
    Delete a cart item (works for both authenticated and guest users).
    Endpoint: DELETE /api/v1/cart-delete/<cart_id>/<item_id>/
    Endpoint: DELETE /api/v1/cart-delete/<cart_id>/<item_id>/<user_id>/ (optional)
    """
    serializer_class = CartSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'
    
    def get_object(self):
        cart_id = self.kwargs.get('cart_id')
        item_id = self.kwargs.get('item_id')
        user_id = self.kwargs.get('user_id')

        if not cart_id or not item_id:
            raise ValidationError(
                {"error": "cart_id and item_id are required"}
            )

        # Build query filters
        filters = {
            'cart_id': cart_id,
            'id': item_id
        }

        # Add user filter if user_id is provided and valid (for signed-in users)
        if user_id and user_id != "undefined":
            try:
                user = User.objects.get(id=user_id)
                filters['user'] = user
            except User.DoesNotExist:
                # User doesn't exist, but we don't raise error - just ignore user filter
                pass

        try:
            cart = Cart.objects.get(**filters)
            return cart
        except Cart.DoesNotExist:
            raise NotFound({"error": "Cart item not found"})
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        cart_id = instance.cart_id
        item_name = instance.food_item.name if instance.food_item else "item"
        
        self.perform_destroy(instance)
        
        return Response(
            {
                "message": f"Cart item '{item_name}' deleted successfully",
                "cart_id": cart_id
            },
            status=status.HTTP_200_OK
        )
    
    
class CartDetailView(generics.RetrieveAPIView):
    # Define the serializer class for the view
    serializer_class = CartSerializer
    # Specify the lookup field for retrieving objects using 'cart_id'
    lookup_field = 'cart_id'

    # Add a permission class for the view
    permission_classes = (AllowAny,)


    def get_queryset(self):
        # Get 'cart_id' and 'user_id' from the URL kwargs
        cart_id = self.kwargs['cart_id']
        user_id = self.kwargs.get('user_id')  # Use get() to handle cases where 'user_id' is not present

        if user_id is not None:
            # If 'user_id' is provided, filter the queryset by both 'cart_id' and 'user_id'
            user = User.objects.get(id=user_id)
            queryset = Cart.objects.filter(cart_id=cart_id, user=user)
        else:
            # If 'user_id' is not provided, filter the queryset by 'cart_id' only
            queryset = Cart.objects.filter(cart_id=cart_id)

        return queryset

    def get(self, request, *args, **kwargs):
        # Get the queryset of cart items based on 'cart_id' and 'user_id' (if provided)
        queryset = self.get_queryset()

        # Initialize sums for various cart item attributes
        total_delivery = 0.0
        total_service_fee = 0.0
        total_sub_total = 0.0
        total_total = 0.0

        # Iterate over the queryset of cart items to calculate cumulative sums
        for cart_item in queryset:
            # Calculate the cumulative shipping, tax, service_fee, and total values
            total_delivery += float(self.calculate_delivery_fee(cart_item))
            total_service_fee += float(self.calculate_service_fee(cart_item))
            total_sub_total += float(self.calculate_sub_total(cart_item))
            total_total += round(float(self.calculate_total(cart_item)), 2)

        # Create a data dictionary to store the cumulative values
        data = {
            'delivery_fee': total_delivery,
            'service_fee': total_service_fee,
            'sub_total': total_sub_total,
            'total_amount': total_total,
        }

    def calculate_service_fee(self, cart_item):
        # Implement your service fee calculation logic here for a single cart item
        # Example: Calculate based on service type, cart total, etc.
        return cart_item.service_fee

    def calculate_sub_total(self, cart_item):
        # Implement your service fee calculation logic here for a single cart item
        # Example: Calculate based on service type, cart total, etc.
        return cart_item.sub_total

    def calculate_total(self, cart_item):
        # Implement your total calculation logic here for a single cart item
        # Example: Sum of sub_total, shipping, tax, and service_fee
        return cart_item.total
    
    
class CreateOrderAPIView(generics.CreateAPIView):
    """
    Create an order from cart items.
    Endpoint: POST /api/v1/create-order/{cart_id}/ or /api/v1/create-order/{cart_id}/{user_id}/
    Creates a single order that can contain items from multiple vendors.
    Each OrderItem maintains its own vendor reference.
    
    Authentication:
    - Option 1: Provide JWT token in Authorization header (recommended)
    - Option 2: Provide user_id in URL (less secure, but allows guest checkout)
    
    Requires:
    - cart_id in URL path
    - delivery_address in request body
    - Either JWT token OR user_id in URL
    
    Example:
    POST /api/v1/create-order/abc123/1/
    Body: {"delivery_address": "123 Main St"}
    """
    serializer_class = OrderSerializer
    queryset = Order.objects.all()
    permission_classes = [AllowAny]  # Allow both authenticated and unauthenticated requests
    
    def create(self, request, *args, **kwargs):
        payload = request.data
        
        # Get cart_id and optional user_id from URL parameters
        cart_id = self.kwargs.get('cart_id')
        url_user_id = self.kwargs.get('user_id')
        
        if not cart_id:
            return Response(
                {"error": "cart_id is required in URL"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extract required fields from payload
        delivery_address = payload.get('delivery_address') or payload.get('address', '')
        
        if not delivery_address:
            return Response(
                {"error": "delivery_address is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Determine user: prefer authenticated user, fallback to user_id from URL
        user = None
        
        if request.user.is_authenticated:
            # User is authenticated via JWT token
            user = request.user
            
            # If user_id is also in URL, validate it matches
            if url_user_id and user.id != url_user_id:
                return Response(
                    {"error": "User ID in URL does not match authenticated user."},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif url_user_id:
            # No authentication, but user_id provided in URL
            try:
                user = User.objects.get(id=url_user_id)
            except User.DoesNotExist:
                return Response(
                    {"error": f"User with ID {url_user_id} not found."},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Neither authenticated nor user_id provided
            return Response(
                {
                    "error": "Authentication required. Please provide either:",
                    "options": [
                        "1. JWT token in Authorization header: 'Authorization: Bearer <token>'",
                        "2. user_id in URL: /api/v1/create-order/{cart_id}/{user_id}/"
                    ]
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get all cart items (Cart model has food_item directly)
        cart_items = Cart.objects.filter(cart_id=cart_id)
        
        if not cart_items.exists():
            return Response(
                {"error": "Cart is empty. Please add items to cart before placing an order."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Determine primary vendor (first vendor found, or None for multi-vendor orders)
        vendors = set()
        for cart_item in cart_items:
            if cart_item.food_item and cart_item.food_item.vendor:
                vendors.add(cart_item.food_item.vendor)
        
        primary_vendor = vendors.pop() if vendors else None
        # If multiple vendors, set primary_vendor to None or first vendor
        # For now, we'll use the first vendor as primary, but order can have items from multiple vendors
        
        total_amount = Decimal('0.00')
        total_delivery_fee = Decimal('0.00')
        total_service_fee = Decimal('0.00')
        
        # Create a single order for all items (can contain items from multiple vendors)
        order = Order.objects.create(
            user=user,
            vendor=primary_vendor,  # Primary vendor (nullable, can be None for multi-vendor)
            delivery_address=delivery_address,
            status='Pending',
            payment_status='Processing',
        )
        
        # Group items by vendor for response
        vendor_items = defaultdict(list)
        
        # Create order items and calculate totals
        for cart_item in cart_items:
            if not cart_item.food_item:
                continue
                
            food_item = cart_item.food_item
            vendor = food_item.vendor
            item_price = food_item.price
            quantity = cart_item.qty  # Cart uses 'qty' field
            
            # Create order item with its vendor
            order_item = OrderItem.objects.create(
                order=order,
                food_item=food_item,
                vendor=vendor,
                quantity=quantity,
                price=item_price,
            )
            
            # Calculate totals
            item_subtotal = Decimal(str(item_price)) * Decimal(quantity)
            total_amount += item_subtotal
            
            # Track items by vendor for response
            vendor_items[vendor.name].append({
                'food_item': food_item.name,
                'quantity': quantity,
                'price': str(item_price),
                'subtotal': str(item_subtotal),
            })
        
        # Add delivery and service fees to total (sum from all cart items)
        # For multi-vendor orders, we sum fees from all items
        for cart_item in cart_items:
            total_delivery_fee += Decimal(str(cart_item.delivery_fee)) if hasattr(cart_item, 'delivery_fee') else Decimal('0.00')
            total_service_fee += Decimal(str(cart_item.service_fee)) if hasattr(cart_item, 'service_fee') else Decimal('0.00')
        
        total_amount += total_delivery_fee + total_service_fee
        
        # Update order with calculated total
        order.total_amount = total_amount
        order.save()
        
        return Response({
            "message": "Order Created Successfully",
            "order": {
                "order_id": order.id,
                "order_pin": order.order_pin,
                "primary_vendor": primary_vendor.name if primary_vendor else None,
                "vendors": list(vendor_items.keys()),  # List of all vendors in this order
                "items_by_vendor": dict(vendor_items),  # Items grouped by vendor
                "total_amount": str(total_amount),
                "delivery_fee": str(total_delivery_fee),
                "service_fee": str(total_service_fee),
                "status": order.status,
                "payment_status": order.payment_status,
            }
        }, status=status.HTTP_201_CREATED)
    
class CheckoutView(generics.ListAPIView):
    """
    Retrieve order details for checkout summary.
    Endpoint: GET /api/v1/checkout/{user_id}/ or GET /api/v1/checkout/{user_id}/{order_id}/
    Returns order details with items and totals for checkout confirmation.
    
    Authentication:
    - Option 1: Provide JWT token in Authorization header (recommended)
    - Option 2: Provide user_id in URL (less secure)
    
    If order_id is provided, returns that specific order.
    If only user_id is provided, returns the latest order for that user.
    """
    serializer_class = OrderSerializer
    permission_classes = [AllowAny]  # Allow both authenticated and unauthenticated
    
    def get_queryset(self):
        """Get orders based on user_id from URL or authenticated user."""
        user_id = self.kwargs.get('user_id')
        order_id = self.kwargs.get('order_id')
        
        # Determine user
        user = None
        if self.request.user.is_authenticated:
            user = self.request.user
            # If user_id in URL, validate it matches authenticated user
            if user_id and user.id != int(user_id):
                return Order.objects.none()  # Return empty queryset if mismatch
        elif user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Order.objects.none()
        else:
            return Order.objects.none()
        
        # Filter orders by user
        queryset = Order.objects.filter(user=user).order_by('-created_at')
        
        # If order_id is provided, filter to that specific order
        if order_id:
            queryset = queryset.filter(id=order_id)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """List orders or retrieve specific order with checkout summary."""
        queryset = self.get_queryset()
        
        if not queryset.exists():
            raise NotFound({
                "error": "No orders found",
                "message": "No orders found for the specified user."
            })
        
        # Get the first order (latest if multiple, or specific if order_id provided)
        order = queryset.first()
        
        # Calculate totals from order items
        order_items = order.items.all()
        items_data = []
        calculated_subtotal = Decimal('0.00')
        
        for item in order_items:
            item_subtotal = Decimal(str(item.price)) * Decimal(item.quantity)
            calculated_subtotal += item_subtotal
            items_data.append({
                'food_item': item.food_item.name,
                'food_item_id': item.food_item.item_id,
                'quantity': item.quantity,
                'price': str(item.price),
                'subtotal': str(item_subtotal),
            })
        
        # Get delivery and service fees (if stored separately, otherwise calculate)
        # For now, using order total_amount - calculated_subtotal as fees
        fees = order.total_amount - calculated_subtotal
        
        # Get unique vendors from order items
        vendors_set = set()
        for item in order_items:
            if item.vendor:
                vendors_set.add(item.vendor.name)
        
        checkout_summary = {
            'order_id': order.id,
            'order_pin': order.order_pin,
            'primary_vendor': order.vendor.name if order.vendor else None,
            'vendors': list(vendors_set),  # List of all vendors in this order
            'status': order.status,
            'payment_status': order.payment_status,
            'delivery_address': order.delivery_address,
            'items': items_data,
            'summary': {
                'subtotal': str(calculated_subtotal),
                'fees': str(fees),
                'total_amount': str(order.total_amount),
            },
            'created_at': order.created_at,
        }
        
        return Response(checkout_summary, status=status.HTTP_200_OK)
        
            
      
    
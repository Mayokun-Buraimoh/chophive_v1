from decimal import Decimal
from collections import defaultdict
from django.shortcuts import get_object_or_404, render
from django.http import Http404
from django.db import transaction
from django.db.models import Q
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound
from uuid import uuid4

from core.models import Cart,CartItem, Category, FoodItem, Order, OrderItem, Vendor, SiteSettings
from core.serializers import CartItemSerializer, CartSerializer, CategorySerializer, FoodItemSerializer, OrderSerializer, VendorSerializer
from userauths.models import User, Profile
from userauths.serializers import ProfileSerializer


def transfer_guest_cart_to_user(request, user):
    """
    Helper function to transfer guest cart to database when user registers or logs in.
    Creates a cart with cart_id if it doesn't exist.
    Returns the cart_id.
    """
    # Ensure session is available
    if not hasattr(request, 'session'):
        print("ERROR: Request does not have session attribute")
        return None
    
    # Get guest cart from session
    guest_cart = request.session.get('guest_cart', {})
    
    print(f"DEBUG: Guest cart from session: {guest_cart}")
    print(f"DEBUG: Guest cart type: {type(guest_cart)}, length: {len(guest_cart) if isinstance(guest_cart, dict) else 'N/A'}")
    
    if not guest_cart or not isinstance(guest_cart, dict) or len(guest_cart) == 0:
        print("No guest cart to transfer")
        return None  # No guest cart to transfer
    
    # Get or create cart for user
    try:
        cart = Cart.objects.get(user=user)
        print(f"DEBUG: Found existing cart for user {user.id}, cart_id: {cart.cart_id}")
    except Cart.DoesNotExist:
        print(f"DEBUG: No existing cart for user {user.id}, creating new cart")
        # Create new cart with first food item as placeholder
        # Get site settings for default fees
        site_settings = SiteSettings.get_settings()
        cart_id = uuid4().hex[:12]
        # Get first food item from guest cart for placeholder
        first_item_data = next(iter(guest_cart.values()), None)
        if first_item_data:
            try:
                first_food_item = FoodItem.objects.get(id=first_item_data.get('food_item_id'))
                cart = Cart.objects.create(
                    user=user,
                    food_item=first_food_item,  # Required field - placeholder
                    qty=1,
                    price=first_food_item.price,
                    sub_total=first_food_item.price,
                    delivery_fee=site_settings.delivery_fee,  # Set from site settings
                    service_fee=site_settings.service_fee,  # Set from site settings
                    cart_id=cart_id
                )
                print(f"DEBUG: Created cart with cart_id: {cart_id} for user {user.id}")
            except FoodItem.DoesNotExist:
                print(f"DEBUG: First food item {first_item_data.get('food_item_id')} not found, trying any food item")
                # If first item doesn't exist, create cart with any available food item
                any_food_item = FoodItem.objects.first()
                if any_food_item:
                    cart = Cart.objects.create(
                        user=user,
                        food_item=any_food_item,
                        qty=1,
                        price=any_food_item.price,
                        sub_total=any_food_item.price,
                        delivery_fee=site_settings.delivery_fee,  # Set from site settings
                        service_fee=site_settings.service_fee,  # Set from site settings
                        cart_id=cart_id
                    )
                    print(f"DEBUG: Created cart with any food item, cart_id: {cart_id}")
                else:
                    print("ERROR: No food items available to create cart")
                    return None  # No food items available
        else:
            print("ERROR: No items in guest cart to use as placeholder")
            return None
    
    # Transfer guest cart items
    food_item_ids = [item_data.get('food_item_id') for item_data in guest_cart.values() if item_data.get('food_item_id')]
    
    if not food_item_ids:
        return cart.cart_id
    
    # Fetch all food items in one query
    food_items = FoodItem.objects.filter(id__in=food_item_ids).select_related('vendor')
    food_items_dict = {item.id: item for item in food_items}
    
    # Get existing cart items in one query
    existing_cart_items = CartItem.objects.filter(
        cart=cart,
        food_item_id__in=food_item_ids
    ).select_related('food_item')
    existing_items_dict = {item.food_item_id: item for item in existing_cart_items}
    
    # Prepare items for bulk create and update
    items_to_create = []
    items_to_update = []
    
    for item_key, item_data in guest_cart.items():
        food_item_id = item_data.get('food_item_id')
        quantity = item_data.get('quantity', 1)
        
        if not food_item_id or quantity < 1:
            continue
        
        food_item = food_items_dict.get(food_item_id)
        if not food_item:
            continue  # Food item no longer exists
        
        vendor = food_item.vendor
        
        # Check if item already exists in cart
        existing_item = existing_items_dict.get(food_item_id)
        
        if existing_item:
            # Update existing item quantity
            existing_item.quantity += quantity
            items_to_update.append(existing_item)
        else:
            # Create new cart item
            items_to_create.append(
                CartItem(
                    cart=cart,
                    food_item=food_item,
                    quantity=quantity,
                    user=user,
                    vendor=vendor
                )
            )
    
    # Bulk operations for efficiency
    if items_to_create:
        print(f"DEBUG: Creating {len(items_to_create)} new cart items")
        CartItem.objects.bulk_create(items_to_create)
    
    if items_to_update:
        print(f"DEBUG: Updating {len(items_to_update)} existing cart items")
        CartItem.objects.bulk_update(items_to_update, ['quantity'])
    
    # Verify items were created
    total_items = CartItem.objects.filter(cart=cart).count()
    print(f"DEBUG: Total cart items after transfer: {total_items}")
    
    # Clear guest cart from session
    if 'guest_cart' in request.session:
        del request.session['guest_cart']
        request.session.modified = True
        print("DEBUG: Cleared guest cart from session")
    
    return cart.cart_id


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
    serializer_class = VendorSerializer
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
    lookup_field = 'item_id'



class CartAPIView(generics.ListCreateAPIView):
    """
    List or create cart items.
    Endpoint: GET/POST /api/v1/cart-view/
    - GET: Returns cart items (from database for authenticated, from session for guests)
    - POST: Adds item to cart (stores in database for authenticated, in session for guests)
    """
    serializer_class = CartSerializer
    permission_classes = [AllowAny]
    queryset = Cart.objects.all()
    
    def list(self, request, *args, **kwargs):
        """
        Return cart items.
        - Authenticated users: Return from database (CartItems)
        - Guest users: Return from session
        """
        user = request.user if request.user.is_authenticated else None
        
        # GUEST USER: Return session cart
        if not user:
            guest_cart = request.session.get('guest_cart', {})
            cart_items = []
            
            for item_key, item_data in guest_cart.items():
                try:
                    food_item = FoodItem.objects.get(id=item_data['food_item_id'])
                    # Format similar to CartItem serializer
                    # Use food_item_id as temporary ID (negative to distinguish from DB IDs)
                    cart_items.append({
                        'id': -food_item.id,  # Negative ID to indicate it's a guest cart item
                        'food_item': {
                            'id': food_item.id,
                            'name': food_item.name,
                            'price': str(food_item.price),
                            'image': food_item.image.url if food_item.image else None,
                            'item_id': food_item.item_id,
                        },
                        'qty': item_data['quantity'],
                        'quantity': item_data['quantity'],
                        'price': item_data['price'],
                        'sub_total': str(Decimal(item_data['price']) * item_data['quantity']),
                        'cart_id': None,  # No cart_id for guests
                    })
                except FoodItem.DoesNotExist:
                    # Skip if food item no longer exists
                    continue
            
            return Response(cart_items, status=status.HTTP_200_OK)
        
        # AUTHENTICATED USER: Return from database
        try:
            cart = Cart.objects.get(user=user)
            cart_items = CartItem.objects.filter(cart=cart)
            
            # Format response similar to CartSerializer but for CartItems
            items_data = []
            for item in cart_items:
                items_data.append({
                    'id': item.id,
                    'food_item': {
                        'id': item.food_item.id,
                        'name': item.food_item.name,
                        'price': str(item.food_item.price),
                        'image': item.food_item.image.url if item.food_item.image else None,
                        'item_id': item.food_item.item_id,
                    },
                    'qty': item.quantity,
                    'quantity': item.quantity,
                    'price': str(item.food_item.price),
                    'sub_total': str(item.subtotal),
                    'cart_id': cart.cart_id,
                })
            
            return Response(items_data, status=status.HTTP_200_OK)
        except Cart.DoesNotExist:
            # User has no cart yet
            return Response([], status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        """
        Add item to cart.
        - Authenticated users: Store in database (Cart + CartItems)
        - Guest users: Store in session (temporary, cleared on browser close)
        - When guest logs in: Session cart is transferred to database cart
        """
        data = request.data
        user = request.user if request.user.is_authenticated else None
        user_id = data.get("user_id")

        item_id = data.get("item_id")
        qty = data.get("qty")
        qty = int(qty) if qty not in [None, ""] else 1


        if not item_id:
            return Response({"error": "item_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        if qty < 1:
            return Response({"error": "Quantity must be at least 1"}, status=status.HTTP_400_BAD_REQUEST)

        food_item = get_object_or_404(FoodItem, id=item_id)
        vendor = food_item.vendor

        # Get or determine user
        if not user and user_id and user_id != "undefined" and user_id != "null":
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                user = None

        # GUEST USER: Store in session (temporary, no database)
        if not user:
            # Ensure session is available
            if not hasattr(request, 'session'):
                return Response({
                    "error": "Session not available",
                    "detail": "Please enable session middleware"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Get or initialize guest cart from session
            guest_cart = request.session.get('guest_cart', {})
            
            # Ensure it's a dictionary
            if not isinstance(guest_cart, dict):
                guest_cart = {}
            
            # Use item_id as unique key (each different item gets its own entry)
            item_key = str(item_id)
            
            # Check if this specific item already exists in session cart
            if item_key in guest_cart:
                # Update quantity for existing item of the same type
                guest_cart[item_key]['quantity'] += qty
                message = "Cart item quantity updated"
            else:
                # Add new item to session cart (different items have different keys)
                # This allows multiple different items in the same cart
                guest_cart[item_key] = {
                    'item_id': int(item_id),
                    'food_item_id': food_item.id,
                    'food_item_name': food_item.name,
                    'price': str(food_item.price),
                    'quantity': qty,
                    'vendor_id': vendor.id,
                    'vendor_name': vendor.name,
                }
                message = "New item added to guest cart"
            
            # Save the updated cart back to session (important: reassign to trigger save)
                request.session['guest_cart'] = guest_cart
                request.session.modified = True
            
            # Verify the cart was saved (for debugging)
            saved_cart = request.session.get('guest_cart', {})
            
            return Response({
                "message": message,
                "cart_id": None,  # No cart_id for guest users
                "is_guest": True,
                "cart_item_count": len(saved_cart),  # Number of different items in cart
                "item_id": item_id,
                "quantity": guest_cart[item_key]['quantity']
            }, status=status.HTTP_201_CREATED)

        # AUTHENTICATED USER: Store in database
        # Get or create ONE Cart for this user (OneToOneField ensures only one cart per user)
        cart_created = False
        try:
            cart = Cart.objects.get(user=user)
            # Cart already exists, use it
        except Cart.DoesNotExist:
            # Create new Cart for user (Cart model requires food_item, so we use first item as placeholder)
            # Get site settings for default fees
            site_settings = SiteSettings.get_settings()
            cart_id = uuid4().hex[:12]
            cart = Cart.objects.create(
                user=user,
                food_item=food_item,  # Required field - used as placeholder for first item
                qty=1,  # Placeholder
                price=food_item.price,  # Placeholder
                sub_total=food_item.price,  # Placeholder
                delivery_fee=site_settings.delivery_fee,  # Set from site settings
                service_fee=site_settings.service_fee,  # Set from site settings
                cart_id=cart_id
            )
            cart_created = True
            
            # Transfer guest cart to database if exists
            if 'guest_cart' in request.session and request.session['guest_cart']:
                self._transfer_guest_cart_to_database(request, user, cart)
                # Clear guest cart from session
                del request.session['guest_cart']
                request.session.modified = True

        # Check if CartItem already exists for this cart and food_item
        # This allows multiple different items (different food_items) in the same cart
        cart_item = CartItem.objects.filter(cart=cart, food_item=food_item).first()
        
        if cart_item:
            # Determine if this is an increase or decrease operation
            # Frontend sends:
            # - Plus: qty=1 (increment by 1)
            # - Minus: qty=current_quantity-1 (set to new quantity)
            current_quantity = cart_item.quantity
            
            if qty == 1 and current_quantity >= 1:
                # Plus button: increment by 1
                cart_item.quantity += 1
            elif qty < current_quantity:
                # Minus button: frontend sends new total quantity (current - 1)
                # Set to the new quantity instead of adding
                if qty < 1:
                    # Quantity would be 0 or less - delete the item
                    cart_item.delete()
                    return Response({
                        "message": "Cart item deleted (quantity was 0)",
                        "cart_id": cart.cart_id,
                        "cart_item_count": CartItem.objects.filter(cart=cart).count()
                    }, status=status.HTTP_200_OK)
                else:
                    # Set to new quantity
                    cart_item.quantity = qty
            else:
                # Same item added again: add to existing quantity
                cart_item.quantity += qty
            
            cart_item.save()
            return Response({
                "message": "Cart item quantity updated",
                "cart_id": cart.cart_id,
                "cart_item_count": CartItem.objects.filter(cart=cart).count(),
                "quantity": cart_item.quantity
            }, status=status.HTTP_200_OK)

        # Create new CartItem (different food_item - allows multiple items in cart)
        # This is where the actual items are stored
        CartItem.objects.create(
            cart=cart,
            food_item=food_item,
            quantity=qty,
            user=user,
            vendor=vendor
        )

        return Response({
            "message": "Item added to cart",
            "cart_id": cart.cart_id,
            "cart_item_count": CartItem.objects.filter(cart=cart).count()
        }, status=status.HTTP_201_CREATED)
    
    def _transfer_guest_cart_to_database(self, request, user, cart):
        """
        Efficiently transfer guest cart items from session to database.
        Uses bulk operations to minimize database queries.
        """
        guest_cart = request.session.get('guest_cart', {})
        
        if not guest_cart:
            return  # No items to transfer
        
        # Get all food_item_ids at once
        food_item_ids = [item_data.get('food_item_id') for item_data in guest_cart.values() if item_data.get('food_item_id')]
        
        if not food_item_ids:
            return  # No valid food items
        
        # Fetch all food items in one query
        food_items = FoodItem.objects.filter(id__in=food_item_ids).select_related('vendor')
        food_items_dict = {item.id: item for item in food_items}
        
        # Get existing cart items in one query
        existing_cart_items = CartItem.objects.filter(
            cart=cart,
            food_item_id__in=food_item_ids
        ).select_related('food_item')
        existing_items_dict = {item.food_item_id: item for item in existing_cart_items}
        
        # Prepare items for bulk create and update
        items_to_create = []
        items_to_update = []
        
        for item_key, item_data in guest_cart.items():
            food_item_id = item_data.get('food_item_id')
            quantity = item_data.get('quantity', 1)
            
            if not food_item_id or quantity < 1:
                continue
            
            food_item = food_items_dict.get(food_item_id)
            if not food_item:
                continue  # Food item no longer exists
            
            vendor = food_item.vendor
            
            # Check if item already exists in cart
            existing_item = existing_items_dict.get(food_item_id)
            
            if existing_item:
                # Update existing item quantity
                existing_item.quantity += quantity
                items_to_update.append(existing_item)
            else:
                # Create new cart item
                items_to_create.append(
                    CartItem(
                        cart=cart,
                        food_item=food_item,
                        quantity=quantity,
                        user=user,
                        vendor=vendor
                    )
                )
        
        # Bulk operations for efficiency
        if items_to_create:
            CartItem.objects.bulk_create(items_to_create)
        
        if items_to_update:
            CartItem.objects.bulk_update(items_to_update, ['quantity'])



# class CartAPIView(generics.ListCreateAPIView):
    # """
    # List or create cart items.
    # Endpoint: GET/POST /api/v1/cart/
    # """
    # queryset = Cart.objects.all()
    # serializer_class = CartSerializer
    # permission_classes = [AllowAny]
    
    # def create(self, request, *args, **kwargs):
    #     payload = request.data
        
    #     item_id = payload['item_id']
    #     user_id = payload['user_id']
    #     qty = payload['qty']
    #     price = payload['price']
    #     # delivery_fee = payload['shipping_amount']
    #     # service_fee = payload['service_fee']
    #     cart_id= payload['cart_id']
        
    #     item = FoodItem.objects.get(id=item_id)
    #     if user_id != "undefined":
    #         user = User.objects.get(id=user_id)
    #     else:
    #         user=None
            
    #     cart = Cart.objects.filter(cart_id=cart_id, food_item=item).first()
        
    #     if cart:
    #         cart.food_item = item
    #         cart.user = user
    #         cart.qty = qty
    #         cart.price = price
    #         # cart.sub_total = Decimal(price) * int(qty)
    #         # cart.delivery_fee = Decimal(delivery_fee) * int(qty)
    #         # cart.service_fee = Decimal(service_fee) 
    #         # cart.total_amount = cart.sub_total + cart.delivery_fee + cart.service_fee
    #         cart.cart_id = cart_id
    #         cart.save()
    #         return Response({'message':"Cart updated successfully"}, status=status.HTTP_200_OK)
        
    #     else:
    #         cart = Cart() 
    #         cart.food_item = item
    #         cart.user = user
    #         cart.qty = qty
    #         cart.price = price 
    #         # cart.sub_total = Decimal(price) * int(qty)
    #         # cart.delivery_fee = Decimal(delivery_fee) * int(qty)
    #         # cart.service_fee = Decimal(service_fee) 
    #         cart.cart_id = cart_id
    #         cart.total_amount = cart.sub_total + cart.delivery_fee + cart.service_fee
    #         cart.save()
    #         return Response({'message':"Cart created successfully"}, status=status.HTTP_201_CREATED)
   
class CartListView(generics.ListAPIView):
    """
    List cart items for a user or cart_id.
    Endpoint: GET /api/v1/cart-list/<cart_id>/<user_id>/
    - Returns all CartItems for authenticated users
    - Returns session cart for guest users (if implemented)
    """
    serializer_class = CartItemSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        cart_id = self.kwargs.get("cart_id")
        user_id = self.kwargs.get("user_id")
        user = self.request.user if self.request.user.is_authenticated else None

        # GUEST USER: Return session cart items
        if not user and not user_id:
            # For guest users, return empty (they use session cart)
            return CartItem.objects.none()

        # AUTHENTICATED USER: Get user from request or user_id
        if user:
            target_user = user
        elif user_id:
            try:
                target_user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return CartItem.objects.none()
        else:
            return CartItem.objects.none()

        # Get all CartItems for this user's cart
        # This returns ALL items in the cart (multiple different food_items)
        try:
            cart = Cart.objects.get(user=target_user)
            # Return all CartItems for this cart
            return CartItem.objects.filter(cart=cart).select_related('food_item', 'vendor', 'cart')
        except Cart.DoesNotExist:
            # User has no cart yet
            return CartItem.objects.none()

    def list(self, request, *args, **kwargs):
        """
        Override list to handle both authenticated and guest users properly.
        """
        user = request.user if request.user.is_authenticated else None
        user_id = self.kwargs.get("user_id")
        
        # GUEST USER: Return session cart
        if not user and (not user_id or user_id == "null" or user_id == "undefined"):
            guest_cart = request.session.get('guest_cart', {})
            cart_items = []
            
            for item_key, item_data in guest_cart.items():
                try:
                    food_item = FoodItem.objects.get(id=item_data['food_item_id'])
                    cart_items.append({
                        'id': -food_item.id,  # Negative ID for guest items
                        'cart': None,
                        'user': None,
                        'vendor': item_data['vendor_id'],
                        'food_item': {
                            'id': food_item.id,
                            'name': food_item.name,
                            'price': str(food_item.price),
                            'image': food_item.image.url if food_item.image else None,
                            'item_id': food_item.item_id,
                        },
                        'food_item_name': food_item.name,
                        'quantity': item_data['quantity'],
                        'qty': item_data['quantity'],
                        'price': item_data['price'],
                        'sub_total': str(Decimal(item_data['price']) * item_data['quantity']),
                        'subtotal': str(Decimal(item_data['price']) * item_data['quantity']),
                    })
                except FoodItem.DoesNotExist:
                    continue
            
            return Response(cart_items, status=status.HTTP_200_OK)
        
        # AUTHENTICATED USER: Return from database with cart_id
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        # Add cart_id to each item in the response
        cart = None
        if queryset.exists():
            # Get cart from first item
            first_item = queryset.first()
            if first_item and first_item.cart:
                cart = first_item.cart
        
        items_data = serializer.data
        if cart:
            # Add cart_id to each item
            for item in items_data:
                item['cart_id'] = cart.cart_id
        
        return Response(items_data, status=status.HTTP_200_OK)



class CartTotalView(generics.ListAPIView):
    serializer_class = CartSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        cart_id = self.kwargs['cart_id']
        user_id = self.kwargs.get('user_id')  # Use get() method to handle the case where user_id is not present

        
        if user_id is not None:
            user = User.objects.get(id=user_id)
            queryset = Cart.objects.filter(cart_id=cart_id, user=user)
        else:
            queryset = Cart.objects.filter(cart_id=cart_id)
        
        return queryset
        
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
    
class CartItemUpdateAPIView(generics.UpdateAPIView):
    """
    Update cart item quantity (works for both authenticated and guest users).
    Endpoint: PATCH /api/v1/cart-item-update/<cart_item_id>/
    """
    serializer_class = CartItemSerializer
    permission_classes = [AllowAny]
    queryset = CartItem.objects.all()
    lookup_field = 'id'
    
    def update(self, request, *args, **kwargs):
        """
        Update cart item quantity.
        For guest users: Updates session cart
        For authenticated users: Updates CartItem in database
        """
        user = request.user if request.user.is_authenticated else None
        user_id = request.data.get('user_id')
        cart_item_id = self.kwargs.get('id')
        quantity = request.data.get('quantity') or request.data.get('qty')
        
        # Get user if provided
        if not user and user_id and user_id != "undefined" and user_id != "null":
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                user = None
        
        # GUEST USER: Update session cart
        if not user:
            guest_cart = request.session.get('guest_cart', {})
            
            # Find item in session (cart_item_id is negative for guest items)
            # We need to find by food_item_id
            item_found = False
            for item_key, item_data in guest_cart.items():
                food_item = FoodItem.objects.filter(id=item_data['food_item_id']).first()
                if food_item and abs(cart_item_id) == food_item.id:
                    # Update quantity
                    if quantity:
                        new_quantity = int(quantity)
                        if new_quantity == 0:
                            # Allow 0 in session (no model constraint)
                            # Frontend will show delete icon
                            guest_cart[item_key]['quantity'] = 0
                        elif new_quantity < 0:
                            # Remove item if quantity is negative
                            del guest_cart[item_key]
                        else:
                            guest_cart[item_key]['quantity'] = new_quantity
                    else:
                        # Increment by 1 if no quantity specified
                        guest_cart[item_key]['quantity'] += 1
                    item_found = True
                    break
            
            if not item_found:
                return Response(
                    {"error": "Cart item not found in guest cart"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            request.session['guest_cart'] = guest_cart
            request.session.modified = True
            
            return Response({
                "message": "Cart item quantity updated",
                "cart_item_id": cart_item_id,
                "quantity": guest_cart.get(item_key, {}).get('quantity', 0)
            }, status=status.HTTP_200_OK)
        
        # AUTHENTICATED USER: Update CartItem in database
        try:
            cart_item = CartItem.objects.get(id=cart_item_id, user=user)
        except CartItem.DoesNotExist:
            return Response(
                {"error": "Cart item not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Update quantity
        if quantity:
            new_quantity = int(quantity)
            if new_quantity == 0:
                # Quantity is 0 - keep at 1 in DB (model constraint) but return 0 for frontend
                # Frontend will show delete icon
                cart_item.quantity = 1  # Keep at 1 to satisfy model validator
                cart_item.save()
                return Response({
                    "message": "Cart item quantity is 0 (ready for deletion)",
                    "cart_item_id": cart_item_id,
                    "quantity": 0,  # Return 0 to frontend
                    "should_show_delete": True
                }, status=status.HTTP_200_OK)
            elif new_quantity < 1:
                # Negative or invalid - delete item
                cart_item.delete()
                return Response({
                    "message": "Cart item deleted (quantity was invalid)",
                    "cart_item_id": cart_item_id
                }, status=status.HTTP_200_OK)
            else:
                cart_item.quantity = new_quantity
        else:
            # Increment by 1 if no quantity specified
            cart_item.quantity += 1
        
        cart_item.save()
        
        return Response({
            "message": "Cart item quantity updated",
            "cart_item_id": cart_item_id,
            "quantity": cart_item.quantity
        }, status=status.HTTP_200_OK)


class CartItemDeleteAPIView(generics.GenericAPIView):
    """
    Delete a cart item (works for both authenticated and guest users).
    Endpoint: DELETE /api/v1/cart-delete/<cart_id>/<cart_item_id>/
    Endpoint: DELETE /api/v1/cart-delete/<cart_id>/<cart_item_id>/<user_id>/ (optional)
    """
    serializer_class = CartItemSerializer
    permission_classes = [AllowAny]
    queryset = CartItem.objects.all()
    
    def delete(self, request, *args, **kwargs):
        """
        Handle DELETE request for both authenticated and guest users.
        """
        cart_id = self.kwargs.get('cart_id')
        cart_item_id = self.kwargs.get('cart_item_id')
        user_id = self.kwargs.get('user_id')
        user = request.user if request.user.is_authenticated else None
        
        if not cart_item_id:
            return Response(
                {"error": "cart_item_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get user if provided
        if not user and user_id and user_id != "undefined" and user_id != "null":
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                user = None
        
        # GUEST USER: Delete from session
        if not user:
            guest_cart = request.session.get('guest_cart', {})
            item_found = False
            item_key_to_delete = None
            
            # For guest items, cart_item_id is negative (e.g., -123) where 123 is food_item.id
            # CartListView returns: 'id': -food_item.id
            # So we need to match: abs(cart_item_id) == food_item_id
            try:
                cart_item_id_int = int(cart_item_id)
                cart_item_id_abs = abs(cart_item_id_int)
            except (ValueError, TypeError):
                return Response(
                    {"error": "Invalid cart_item_id format"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            for item_key, item_data in list(guest_cart.items()):
                food_item_id = item_data.get('food_item_id')
                
                # Match by food_item_id
                # Frontend sends negative ID (e.g., -123), we match with food_item_id (123)
                if food_item_id and cart_item_id_abs == food_item_id:
                    item_key_to_delete = item_key
                    item_found = True
                    break
            
            if not item_found:
                return Response(
                    {
                        "error": "Cart item not found in guest cart",
                        "detail": f"Could not find item with cart_item_id={cart_item_id} (looking for food_item_id={cart_item_id_abs})"
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Delete the item from session
            del guest_cart[item_key_to_delete]
            request.session['guest_cart'] = guest_cart
            request.session.modified = True
            
            return Response({
                "message": "Cart item deleted successfully",
                "cart_item_id": cart_item_id
            }, status=status.HTTP_200_OK)
        
        # AUTHENTICATED USER: Delete from database
        try:
            instance = CartItem.objects.get(id=cart_item_id, user=user)
        except CartItem.DoesNotExist:
            return Response(
                {"error": "Cart item not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        item_name = instance.food_item.name if instance.food_item else "item"
        cart_id = instance.cart.cart_id if instance.cart else cart_id
        
        # Delete the CartItem
        instance.delete()
        
        return Response(
            {
                "message": f"Cart item '{item_name}' deleted successfully",
                "cart_id": cart_id,
                "cart_item_id": cart_item_id
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
        
        return Response(data, status=status.HTTP_200_OK)

    def calculate_delivery_fee(self, cart_item):
        """
        Calculate delivery fee for a cart item.
        Always uses SiteSettings.
        """
        site_settings = SiteSettings.get_settings()
        return site_settings.delivery_fee

    def calculate_service_fee(self, cart_item):
        """
        Calculate service fee for a cart item.
        Always uses SiteSettings.
        """
        site_settings = SiteSettings.get_settings()
        return site_settings.service_fee

    def calculate_sub_total(self, cart_item):
        # Implement your service fee calculation logic here for a single cart item
        # Example: Calculate based on service type, cart total, etc.
        return cart_item.sub_total

    def calculate_total(self, cart_item):
        # Implement your total calculation logic here for a single cart item
        # Example: Sum of sub_total, shipping, tax, and service_fee
        return cart_item.total
    
class GetCartIDAPIView(generics.RetrieveAPIView):
    """
    Endpoint to get or create the cart_id for a user.
    """
    permission_classes = [AllowAny]
    serializer_class = CartSerializer

    def get(self, request, user_id=None, *args, **kwargs):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        # Get existing cart or create a new one
        cart, created = Cart.objects.get_or_create(user=user)
        
        return Response({"cart_id": cart.cart_id}, status=status.HTTP_200_OK)

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
    permission_classes = (AllowAny,)

    def create(self, request, *args, **kwargs):
        payload = request.data

        # Get cart_id and user_id from URL parameters
        cart_id = self.kwargs.get('cart_id')
        user_id = self.kwargs.get('user_id')
        
        # Get order information from request body
        delivery_address = payload.get('delivery_address')
        customer_name = payload.get('customer_name', '')
        room_address = payload.get('room_address', '')
        delivery_time = payload.get('delivery_time', '')
        delivery_batch = payload.get('delivery_batch', '')
        
        # Validate required fields
        if not delivery_address:
            return Response(
                {"error": "delivery_address is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate delivery_batch if provided
        if delivery_batch and delivery_batch not in ['1pm', '6pm']:
            return Response(
                {"error": "delivery_batch must be either '1pm' or '6pm'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not cart_id:
            return Response(
                {"error": "cart_id is required in URL"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get user
        if user_id and user_id != 0:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                user = None
        else:
            user = request.user if request.user.is_authenticated else None

        # Get cart items - use CartItem instead of Cart
        try:
            cart = Cart.objects.get(cart_id=cart_id, user=user) if user else Cart.objects.get(cart_id=cart_id)
            cart_items = CartItem.objects.filter(cart=cart)
        except Cart.DoesNotExist:
            return Response(
                {"error": "Cart not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not cart_items.exists():
            return Response(
                {"error": "Cart is empty"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get site settings for default fees
        site_settings = SiteSettings.get_settings()
        
        total_sub_total = Decimal(0.0)

        with transaction.atomic():

            order = Order.objects.create(
                buyer=user,
                payment_status="Processing",
                delivery_address=delivery_address,
                customer_name=customer_name,
                room_address=room_address,
                delivery_time=delivery_time,
                delivery_batch=delivery_batch,
            )

            # Get delivery_fee and service_fee from SiteSettings (always use site settings)
            delivery_fee = site_settings.delivery_fee
            service_fee = site_settings.service_fee
            
            for cart_item in cart_items:
                # Calculate subtotal for this item
                item_subtotal = cart_item.subtotal  # Uses the property from CartItem model
                
                OrderItem.objects.create(
                    order=order,
                    food_item=cart_item.food_item,
                    quantity=cart_item.quantity,
                    price=cart_item.price,  # Uses the property from CartItem model
                    sub_total=item_subtotal,
                    service_fee=Decimal(0),  # Service fee is per order, not per item
                    total=item_subtotal,  # Item total is just subtotal
                    vendor=cart_item.vendor
                )

                total_sub_total += item_subtotal

                # Set vendor on order if not already set
                if cart_item.vendor and not order.vendor:
                    order.vendor = cart_item.vendor

                

            order.sub_total = total_sub_total
            order.delivery_fee = Decimal(str(delivery_fee))
            order.service_fee = service_fee
            order.total = total_sub_total + service_fee + Decimal(str(delivery_fee))
            order.total_amount = order.total

            
            order.save()

        return Response( {"message": "Order Created Successfully", 'order_oid':order.oid}, status=status.HTTP_201_CREATED)

class CheckoutView(generics.RetrieveAPIView):
    """
    Retrieve order details for checkout summary.
    Endpoint: GET /api/v1/checkout/{order_oid}/
    Returns order details with items and totals for checkout confirmation.
    """
    serializer_class = OrderSerializer
    lookup_field = 'order_oid'  
    permission_classes = [AllowAny]

    def get_object(self):
        order_oid = self.kwargs.get('order_oid')
        if not order_oid:
            raise NotFound("Order OID is required")
        
        try:
            order = Order.objects.select_related('buyer', 'vendor').prefetch_related('items__food_item', 'items__vendor').get(oid=order_oid)
            return order
        except Order.DoesNotExist:
            raise NotFound(f"Order with OID '{order_oid}' not found")

# class CheckoutView(generics.ListAPIView):
#     """
#     Retrieve order details for checkout summary.
#     Endpoint: GET /api/v1/checkout/{user_id}/ or GET /api/v1/checkout/{user_id}/{order_id}/
#     Returns order details with items and totals for checkout confirmation.
    
#     Authentication:
#     - Option 1: Provide JWT token in Authorization header (recommended)
#     - Option 2: Provide user_id in URL (less secure)
    
#     If order_id is provided, returns that specific order.
#     If only user_id is provided, returns the latest order for that user.
#     """
#     serializer_class = OrderSerializer
#     permission_classes = [AllowAny]  # Allow both authenticated and unauthenticated
    
#     def get_queryset(self):
#         """Get orders based on user_id from URL or authenticated user."""
#         user_id = self.kwargs.get('user_id')
#         order_id = self.kwargs.get('order_id')
        
#         # Determine user
#         user = None
#         if self.request.user.is_authenticated:
#             user = self.request.user
#             # If user_id in URL, validate it matches authenticated user
#             if user_id and user.id != int(user_id):
#                 return Order.objects.none()  # Return empty queryset if mismatch
#         elif user_id:
#             try:
#                 user = User.objects.get(id=user_id)
#             except User.DoesNotExist:
#                 return Order.objects.none()
#         else:
#             return Order.objects.none()
        
#         # Filter orders by user
#         queryset = Order.objects.filter(user=user).order_by('-created_at')
        
#         # If order_id is provided, filter to that specific order
#         if order_id:
#             queryset = queryset.filter(id=order_id)
        
#         return queryset
    
#     def list(self, request, *args, **kwargs):
#         """List orders or retrieve specific order with checkout summary."""
#         queryset = self.get_queryset()
        
#         if not queryset.exists():
#             raise NotFound({
#                 "error": "No orders found",
#                 "message": "No orders found for the specified user."
#             })
        
#         # Get the first order (latest if multiple, or specific if order_id provided)
#         order = queryset.first()
        
#         # Calculate totals from order items
#         order_items = order.items.all()
#         items_data = []
#         calculated_subtotal = Decimal('0.00')
        
#         for item in order_items:
#             item_subtotal = Decimal(str(item.price)) * Decimal(item.quantity)
#             calculated_subtotal += item_subtotal
#             items_data.append({
#                 'food_item': item.food_item.name,
#                 'food_item_id': item.food_item.item_id,
#                 'quantity': item.quantity,
#                 'price': str(item.price),
#                 'subtotal': str(item_subtotal),
#             })
        
#         # Get delivery and service fees (if stored separately, otherwise calculate)
#         # For now, using order total_amount - calculated_subtotal as fees
#         fees = order.total_amount - calculated_subtotal
        
#         # Get unique vendors from order items
#         vendors_set = set()
#         for item in order_items:
#             if item.vendor:
#                 vendors_set.add(item.vendor.name)
        
#         checkout_summary = {
#             'order_id': order.id,
#             'order_pin': order.order_pin,
#             'primary_vendor': order.vendor.name if order.vendor else None,
#             'vendors': list(vendors_set),  # List of all vendors in this order
#             'status': order.status,
#             'payment_status': order.payment_status,
#             'delivery_address': order.delivery_address,
#             'items': items_data,
#             'summary': {
#                 'subtotal': str(calculated_subtotal),
#                 'fees': str(fees),
#                 'total_amount': str(order.total_amount),
#             },
#             'created_at': order.created_at,
#         }
        
#         return Response(checkout_summary, status=status.HTTP_200_OK)
        
            
      
    
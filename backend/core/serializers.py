from rest_framework import serializers
from decimal import Decimal
from core.models import Vendor, FoodItem, Category, Cart, CartItem, Order, OrderItem, DeliveryBatch, Hostel, Room
from userauths.serializers import UserSerializer


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ['id', 'number']

class HostelSerializer(serializers.ModelSerializer):
    rooms = RoomSerializer(many=True, read_only=True)
    
    class Meta:
        model = Hostel
        fields = ['id', 'name', 'slug', 'rooms']


class DeliveryBatchSerializer(serializers.ModelSerializer):
    formatted_end_time = serializers.SerializerMethodField()

    class Meta:
        model = DeliveryBatch
        fields = ['id', 'name', 'start_time', 'cutoff_time', 'is_active', 'formatted_end_time']

    def get_formatted_end_time(self, obj):
        if obj.cutoff_time:
            return obj.cutoff_time.strftime("%I:%M %p").lstrip('0')
        return None


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class FoodItemSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    vendor_slug = serializers.CharField(source='vendor.slug', read_only=True)
    
    class Meta:
        model = FoodItem
        fields = ['id', 'vendor', 'vendor_name', 'vendor_slug', 'name', 'slug', 'description', 
                  'price', 'image', 'is_available', 'stock_qty', 'item_id', 'created_at', 'updated_at']
        read_only_fields = ['id', 'slug', 'item_id', 'created_at', 'updated_at']


class CartSerializer(serializers.ModelSerializer):
    food_item = FoodItemSerializer(read_only=True)
    
    class Meta:
        model = Cart
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super(CartSerializer, self).__init__(*args, **kwargs)
        # Customize serialization depth based on the request method.
        request = self.context.get('request')
        if request and request.method == 'POST':
            # When creating a new cart order item, set serialization depth to 0.
            self.Meta.depth = 0
        else:
            # For other methods, set serialization depth to 3.
            self.Meta.depth = 3



class CartItemSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()  # <-- explicitly include property
    subtotal = serializers.SerializerMethodField()
    sub_total = serializers.SerializerMethodField()  # Alias for frontend compatibility
    qty = serializers.IntegerField(source='quantity', read_only=True)  # Alias for frontend compatibility
    food_item_name = serializers.CharField(source='food_item.name', read_only=True)
    cart_id = serializers.CharField(source='cart.cart_id', read_only=True)  # Include cart_id for delete operations

    class Meta:
        model = CartItem
        fields = [
            'id', 'cart', 'cart_id', 'user', 'vendor',  # Added cart_id
            'food_item', 'food_item_name',
            'quantity', 'qty',  # Both quantity and qty for compatibility
            'price', 'subtotal', 'sub_total',  # Both subtotal and sub_total for compatibility
            'created_at', 'updated_at'
        ]
        depth = 1

    def get_price(self, obj):
        return str(obj.price)  # This calls the @property on the model

    def get_subtotal(self, obj):
        return str(obj.subtotal)

    def get_sub_total(self, obj):
        # Alias for frontend compatibility
        return str(obj.subtotal)

 
class OrderItemSerializer(serializers.ModelSerializer):
    # food_item = FoodItemSerializer(read_only=True)
    
    class Meta:
        model = OrderItem
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super(OrderItemSerializer, self).__init__(*args, **kwargs)
        # Customize serialization depth based on the request method.
        request = self.context.get('request')
        if request and request.method == 'POST':
            # When creating a new cart order item, set serialization depth to 0.
            self.Meta.depth = 0
        else:
            # For other methods, set serialization depth to 3.
            self.Meta.depth = 3


class OrderSerializer(serializers.ModelSerializer):
    order_item = OrderItemSerializer(many=True, read_only=True, source='items')
    
    class Meta:
        model = Order
        fields = [
            'id', 'oid', 'buyer', 'vendor', 'order_item', 'customer_name', 
            'hostel', 'room_address', 'delivery_batch', 'delivery_time',
            'status', 'payment_status', 'payment_id', 'order_pin', 'approved',
            'sub_total', 'delivery_fee', 'service_fee', 'total_pack_fee', 'total', 'total_amount',
            'created_at', 'updated_at', 'date'
        ]


    def __init__(self, *args, **kwargs):
        super(OrderSerializer, self).__init__(*args, **kwargs)
        # Customize serialization depth based on the request method.
        request = self.context.get('request')
        if request and request.method == 'POST':
            # When creating a new cart order, set serialization depth to 0.
            self.Meta.depth = 0
        else:
            # For other methods, set serialization depth to 3.
            self.Meta.depth = 3
# Nested serializers for detailed views

class VendorSerializer(serializers.ModelSerializer):
    # Serialize related CartOrderItem models
    user = UserSerializer(read_only=True)

    class Meta:
        model = Vendor
        fields = ['id', 'user', 'name', 'slug', 'description', 'address', 'logo', 'pack_fee', 'is_active', 'created_at']


    def __init__(self, *args, **kwargs):
        super(VendorSerializer, self).__init__(*args, **kwargs)
        # Customize serialization depth based on the request method.
        request = self.context.get('request')
        if request and request.method == 'POST':
            # When creating a new cart order, set serialization depth to 0.
            self.Meta.depth = 0
        else:
            # For other methods, set serialization depth to 3.
            self.Meta.depth = 3

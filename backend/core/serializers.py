from rest_framework import serializers
from decimal import Decimal
from core.models import Vendor, FoodItem, Category, Cart, CartItem, Order, OrderItem
from userauths.serializers import UserSerializer

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'slug', 'created_at']
        read_only_fields = ['id', 'slug', 'created_at']

class VendorSerializer(serializers.ModelSerializer):
    food_items_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Vendor
        fields = ['id', 'name', 'slug', 'description', 'address', 'logo', 'is_active', 'food_items_count', 'created_at']
        read_only_fields = ['id', 'slug', 'food_items_count', 'created_at']


class FoodItemSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    vendor_slug = serializers.CharField(source='vendor.slug', read_only=True)
    
    class Meta:
        model = FoodItem
        fields = ['id', 'vendor', 'vendor_name', 'vendor_slug', 'name', 'slug', 'description', 
                  'price', 'image', 'is_available', 'stock_qty', 'item_id', 'created_at', 'updated_at']
        read_only_fields = ['id', 'slug', 'item_id', 'created_at', 'updated_at']


class CartItemSerializer(serializers.ModelSerializer):
    food_item = FoodItemSerializer(read_only=True)
    food_item_id = serializers.IntegerField(write_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = CartItem
        fields = ['id', 'cart', 'food_item', 'food_item_id', 'quantity', 'subtotal', 'price', 
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'subtotal', 'price', 'created_at', 'updated_at']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    item_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total_amount', 'item_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'total_amount', 'item_count', 'created_at', 'updated_at']


class OrderItemSerializer(serializers.ModelSerializer):
    food_item = FoodItemSerializer(read_only=True)
    food_item_id = serializers.IntegerField(write_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'food_item', 'food_item_id', 'quantity', 'price', 'subtotal']
        read_only_fields = ['id', 'subtotal']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)
    vendor = VendorSerializer(read_only=True, allow_null=True)
    vendor_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    vendors = serializers.SerializerMethodField()  # List of all vendors in this order
    
    class Meta:
        model = Order
        fields = ['id', 'user', 'vendor', 'vendor_id', 'vendors', 'total_amount', 'status', 'delivery_address',
                  'delivery_batch', 'payment_status', 'payment_id', 'items', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'vendors']
    
    def get_vendors(self, obj):
        """Return list of unique vendors from order items."""
        vendors = set()
        for item in obj.items.all():
            if item.vendor:
                vendors.add(item.vendor.id)
        # Return vendor details
        from core.models import Vendor
        vendor_objs = Vendor.objects.filter(id__in=vendors)
        return VendorSerializer(vendor_objs, many=True).data


# class PaymentSerializer(serializers.ModelSerializer):
#     order = OrderSerializer(read_only=True)
#     order_id = serializers.IntegerField(write_only=True)
    
#     class Meta:
#         model = Payment
#         fields = ['id', 'order', 'order_id', 'amount', 'method', 'status', 'transaction_id',
#                   'created_at', 'updated_at']
#         read_only_fields = ['id', 'created_at', 'updated_at']


# Nested serializers for detailed views
class VendorDetailSerializer(VendorSerializer):
    """Vendor serializer with nested food items."""
    food_items = FoodItemSerializer(many=True, read_only=True)
    
    class Meta(VendorSerializer.Meta):
        fields = VendorSerializer.Meta.fields + ['food_items']


# class OrderDetailSerializer(OrderSerializer):
#     """Order serializer with nested payment information."""
#     payment = PaymentSerializer(read_only=True)
    
#     class Meta(OrderSerializer.Meta):
#         fields = OrderSerializer.Meta.fields + ['payment']

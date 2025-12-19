from django.contrib import admin

from core.models import Category, FoodItem, Cart, CartItem, Vendor, Order, OrderItem

# Register your models here.
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'slug']
    search_fields = ['name', 'description']
    list_filter = ['created_at']
    list_per_page = 10
    ordering = ['-created_at']
    readonly_fields = ['slug', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        (None, {'fields': ('name', 'description')}),
        ('Dates', {'fields': ('created_at',)}),
    )

class VendorAdmin(admin.ModelAdmin):
    actions = None
    list_display = ['name', 'slug', 'is_active', 'created_at']
    search_fields = ['name', 'slug', 'description', 'address']
    list_filter = ['is_active', 'created_at']
    list_per_page = 10
    ordering = ['name']
    readonly_fields = ['created_at']
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        (None, {'fields': ('name', 'slug', 'description', 'address', 'logo', 'is_active')}),
        ('Dates', {'fields': ('created_at',)}),
    )

class FoodItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'vendor', 'description', 'price', 'created_at', 'updated_at', 'item_id']
    search_fields = ['name', 'description', 'vendor__name']
    list_filter = ['vendor', 'created_at', 'updated_at']
    list_per_page = 10
    ordering = ['-created_at']
    readonly_fields = ['item_id', 'created_at', 'updated_at']
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        (None, {'fields': ('vendor', 'name', 'slug', 'description', 'price', 'image', 'is_available', 'item_id')}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
    )
class CartItemInline(admin.TabularInline):
    """Inline admin for CartItems within Cart admin."""
    model = CartItem
    extra = 0
    fields = ['food_item', 'vendor', 'quantity', 'subtotal_display', 'created_at']
    readonly_fields = ['subtotal_display', 'created_at']
    exclude = ['user']  # User will be set automatically from Cart
    
    def subtotal_display(self, obj):
        """Display calculated subtotal."""
        if obj.pk:
            return obj.subtotal
        return '-'
    subtotal_display.short_description = 'Subtotal'


class CartAdmin(admin.ModelAdmin):
    actions = None
    list_display = ['cart_id', 'user', 'food_item', 'qty', 'sub_total', 'delivery_fee', 'service_fee', 'total_amount', 'created_at']
    search_fields = ['cart_id', 'user__email', 'user__username', 'food_item__name']
    list_filter = ['created_at', 'updated_at']
    list_per_page = 10
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'sub_total', 'delivery_fee', 'service_fee', 'total_amount']
    inlines = [CartItemInline]
    fieldsets = (
        (None, {'fields': ('cart_id', 'user', 'food_item', 'qty')}),
        ('Fees & Totals', {'fields': ('sub_total', 'delivery_fee', 'service_fee', 'total_amount')}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
    )
    
    def save_formset(self, request, form, formset, change):
        """Override to automatically set user and vendor on CartItem instances."""
        instances = formset.save(commit=False)
        cart = form.instance
        
        # Set user and vendor on all CartItem instances
        for instance in instances:
            if isinstance(instance, CartItem):
                instance.user = cart.user
                # Set vendor from food_item's vendor if not already set
                if instance.food_item and not instance.vendor:
                    instance.vendor = instance.food_item.vendor
                instance.save()
        
        # Delete instances marked for deletion
        for obj in formset.deleted_objects:
            obj.delete()
        
        # Save any remaining instances
        formset.save_m2m()

class OrderItemInline(admin.TabularInline):
    """Inline admin for OrderItems within Order admin."""
    model = OrderItem
    extra = 0
    readonly_fields = ['subtotal_display']
    fields = ['food_item', 'vendor', 'quantity', 'price', 'subtotal_display']
    
    def subtotal_display(self, obj):
        """Display calculated subtotal."""
        if obj.pk:
            return obj.subtotal
        return '-'
    subtotal_display.short_description = 'Subtotal'


class OrderAdmin(admin.ModelAdmin):
    actions = None
    list_display = ['id', 'order_pin', 'user', 'vendor', 'total_amount', 'status', 'payment_status', 'approved', 'date', 'created_at']
    list_editable = ['approved', 'payment_status', 'status']  # Allow inline editing
    search_fields = ['id', 'order_pin', 'user__email', 'user__username', 'vendor__name', 'payment_id', 'delivery_address']
    list_filter = ['status', 'payment_status', 'approved', 'date', 'created_at', 'vendor']
    list_per_page = 10
    ordering = ['-created_at']
    readonly_fields = ['order_pin', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    
    fieldsets = (
        (None, {'fields': ('user', 'vendor', 'order_pin')}),  # vendor is now nullable for multi-vendor orders
        ('Order Details', {'fields': ('status', 'total_amount', 'delivery_address', 'delivery_batch')}),
        ('Payment', {'fields': ('payment_status', 'payment_id', 'approved')}),
        ('Dates', {'fields': ('date', 'created_at', 'updated_at')}),
    )
    
    def get_list_display(self, request):
        """Customize list display based on user permissions."""
        display = ['id', 'order_pin', 'user', 'vendor', 'total_amount', 'status', 'payment_status', 'approved', 'date', 'created_at']
        return display


class OrderItemAdmin(admin.ModelAdmin):
    actions = None
    list_display = ['id', 'order', 'food_item', 'vendor', 'quantity', 'price', 'subtotal_display', 'order_user']
    search_fields = ['order__id', 'order__order_pin', 'food_item__name', 'vendor__name', 'order__user__email']
    list_filter = ['vendor', 'order__status', 'order__created_at']
    list_per_page = 10
    ordering = ['order__id', 'food_item__name']
    readonly_fields = ['subtotal_display']
    
    fieldsets = (
        (None, {'fields': ('order', 'food_item', 'vendor', 'quantity', 'price')}),
        ('Totals', {'fields': ('subtotal_display',)}),
    )
    
    def subtotal_display(self, obj):
        """Display calculated subtotal."""
        if obj.pk:
            return obj.subtotal
        return '-'
    subtotal_display.short_description = 'Subtotal'
    
    def order_user(self, obj):
        """Display order user."""
        return obj.order.user.email if obj.order and obj.order.user else '-'
    order_user.short_description = 'Order User'


admin.site.register(FoodItem, FoodItemAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Vendor, VendorAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
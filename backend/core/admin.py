from django.contrib import admin

from core.models import Category, FoodItem, Cart, Vendor, Order, OrderItem, SiteSettings, Hostel, DeliveryBatch

from import_export.admin import ImportExportModelAdmin



class OrderItemsInlineAdmin(admin.TabularInline):
    model = OrderItem

class FoodItemAdmin(ImportExportModelAdmin):
    # inlines = [ProductImagesAdmin, SpecificationAdmin, ColorAdmin, SizeAdmin]
    search_fields = ['name', 'price', 'slug']
    list_filter = [ 'vendor']
    list_editable = ['price']
    list_display = [ 'name',  'price','stock_qty', 'vendor']
    # actions = [make_published, make_in_review, make_featured]
    list_display_links = ['name']
    list_per_page = 100
    prepopulated_fields = {"slug": ("name", )}
    # form = ProductAdminForm

class OrderAdmin(ImportExportModelAdmin):
    inlines = [OrderItemsInlineAdmin]
    search_fields = ['oid', 'customer_name', 'room_address', 'hostel']
    list_editable = ['payment_status']
    list_filter = ['payment_status', 'status']
    list_display = ['oid', 'customer_name', 'room_address', 'hostel', 'delivery_batch', 'payment_status', 'sub_total', 'service_fee', 'total', 'date']
    list_filter = ['payment_status', 'status', 'delivery_batch']

    ordering = ['hostel']  # Orders alphabetically by hostel

class CartAdmin(ImportExportModelAdmin):
    list_display = ['food_item', 'cart_id', 'qty', 'price', 'sub_total' ,'service_fee', 'total', 'date']


class OrderItemsAdmin(ImportExportModelAdmin):
    # list_filter = ['delivery_couriers', 'applied_coupon']
    list_editable = ['date']
    list_display = ['order_id', 'vendor', 'food_item' ,'quantity', 'price', 'sub_total', 'service_fee', 'total' , 'date']


class SiteSettingsAdmin(admin.ModelAdmin):
    """
    Admin interface for Site Settings (singleton model).
    Only one instance can exist.
    """
    def has_add_permission(self, request):
        # Only allow one instance
        try:
            return not SiteSettings.objects.exists()
        except:
            # If table doesn't exist yet (during migrations), allow add
            return True
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of the only instance
        return False
    
    list_display = ['delivery_fee', 'service_fee', 'updated_at']
    fields = ['delivery_fee', 'service_fee']
    readonly_fields = ['created_at', 'updated_at']
    
    def save_model(self, request, obj, form, change):
        """
        Override save to ensure singleton pattern.
        """
        obj.pk = 1
        super().save_model(request, obj, form, change)


class HostelAdmin(ImportExportModelAdmin):
    list_display = ['name', 'rooms', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {"slug": ("name", )}


class DeliveryBatchAdmin(ImportExportModelAdmin):
    list_display = ['name', 'cutoff_time', 'is_active']
    list_editable = ['is_active']
    search_fields = ['name']




# class OrderItemsAdmin(ImportExportModelAdmin):
    # list_filter = ['delivery_couriers', 'applied_coupon']
    # list_editable = ['date']
    # list_display = ['order_id', 'vendor', 'product' ,'qty', 'price', 'sub_total', 'service_fee', 'total' , 'date']


# admin.site.register(OrderItem, OrderItemsAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(OrderItem, OrderItemsAdmin)
admin.site.register(Vendor)
admin.site.register(FoodItem, FoodItemAdmin)
admin.site.register(SiteSettings, SiteSettingsAdmin)
admin.site.register(Hostel, HostelAdmin)
admin.site.register(DeliveryBatch, DeliveryBatchAdmin)
admin.site.register(Category)

# class OrderItemAdmin(ImportExportModelAdmin):
#     # list_filter = ['delivery_couriers', 'applied_coupon']
#     list_editable = ['date']
#     list_display = ['order_id', 'vendor', 'product' ,'qty', 'price', 'sub_total', 'shipping_amount' , 'service_fee', 'tax_fee', 'total' , 'delivery_couriers', 'applied_coupon', 'date']


# admin.site.register(OrderItem, OrderItemAdmin)
# # Register your models here.
# class CategoryAdmin(ImportExportModelAdmin):
#     list_editable = [ 'active']
#     list_display = ['title',  'active']

    

# class VendorAdmin(admin.ModelAdmin):
#     actions = None
#     list_display = ['name', 'slug', 'is_active', 'created_at']
#     search_fields = ['name', 'slug', 'description', 'address']
#     list_filter = ['is_active', 'created_at']
#     list_per_page = 10
#     ordering = ['name']
#     readonly_fields = ['created_at']
#     prepopulated_fields = {'slug': ('name',)}
#     fieldsets = (
#         (None, {'fields': ('name', 'slug', 'description', 'address', 'logo', 'is_active')}),
#         ('Dates', {'fields': ('created_at',)}),
#     )

# class FoodItemAdmin(admin.ModelAdmin):
#     list_display = ['name', 'vendor', 'description', 'price', 'created_at', 'updated_at', 'item_id']
#     search_fields = ['name', 'description', 'vendor__name']
#     list_filter = ['vendor', 'created_at', 'updated_at']
#     list_per_page = 100
#     ordering = ['-created_at']
#     readonly_fields = ['item_id', 'created_at', 'updated_at']
#     prepopulated_fields = {'slug': ('name',)}
#     fieldsets = (
#         (None, {'fields': ('vendor', 'name', 'slug', 'description', 'price', 'image', 'is_available', 'item_id')}),
#         ('Dates', {'fields': ('created_at', 'updated_at')}),
#     )

# class OrderItemInline(admin.TabularInline):
#     """Inline admin for OrderItems within Order admin."""
#     # list_filter = ['delivery_couriers', 'applied_coupon']
#     list_editable = ['date']
#     list_display = ['order_id', 'vendor', 'product' ,'qty', 'price', 'sub_total', 'service_fee', 'total' , 'date']


# class OrderAdmin(admin.ModelAdmin):
#     inlines = [OrderItemInline]
#     search_fields = ['oid', 'full_name', 'email', 'mobile']
#     list_editable = ['order_status', 'payment_status']
#     list_filter = ['payment_status', 'order_status']
#     list_display = ['oid', 'payment_status', 'order_status', 'sub_total', 'shipping_amount', 'tax_fee', 'service_fee' ,'total', 'saved' ,'date']


# class OrderItemAdmin(admin.ModelAdmin):
#     list_editable = ['date']
#     list_display = ['order_id', 'vendor', 'product' ,'qty', 'price', 'sub_total', 'service_fee', 'total' , 'date']


# admin.site.register(FoodItem, FoodItemAdmin)
# admin.site.register(Category, CategoryAdmin)
# admin.site.register(Vendor, VendorAdmin)
# # admin.site.register(Cart, CartAdmin)
# admin.site.register(Order, OrderAdmin)
# admin.site.register(OrderItem, OrderItemAdmin)
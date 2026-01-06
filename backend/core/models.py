from decimal import Decimal
from uuid import uuid4
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify
from django.utils.safestring import mark_safe
from userauths.models import User
from shortuuid.django_fields import ShortUUIDField
from django.utils import timezone
from datetime import time
# Create your models here.
class Vendor(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='vendor', help_text="User account associated with this vendor")
    name = models.CharField(max_length=200, unique=True, help_text="Vendor/restaurant name")
    slug = models.SlugField(max_length=200, unique=True, blank=True, help_text="URL-friendly identifier")
    description = models.TextField(help_text="Vendor description")
    address = models.TextField(help_text="Vendor physical address", blank=True, null=True)
    logo = models.FileField(upload_to='vendor_logos/', blank=True, null=True, help_text="Vendor logo image")
    is_active = models.BooleanField(default=True, help_text="Whether the vendor is currently active")
    pack_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Packaging fee per order from this vendor")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Vendor"
        verbose_name_plural = "Vendors"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def __str__(self):
        vendor_id = self.id
        return f"Vendor #{vendor_id} - {self.name}"
    
    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not provided."""
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            # Ensure slug is unique
            while Vendor.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    @property
    def food_items_count(self):
        """Return count of food items for this vendor."""
        
        return self.food_items.count()
    
class FoodItem(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='food_items', help_text="Vendor that offers this food item")
    name = models.CharField(max_length=200, help_text="Food item name")
    slug = models.SlugField(max_length=200, unique=True, blank=True, help_text="URL-friendly identifier")
    stock_qty = models.PositiveIntegerField(default=1, blank=True, null=True)
    description = models.TextField(help_text="Food item description")
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Food item price")
    image = models.FileField(upload_to='food_images/', blank=True, null=True, help_text="Food item image")
    is_available = models.BooleanField(default=True, help_text="Whether the food item is currently available")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    item_id = ShortUUIDField(unique=True, length=10, max_length=20, alphabet="abcdefghijklmnopqrstuvxyz")
    orders = models.PositiveIntegerField(default=0, null=True, blank=True)
    
    
    class Meta:
        verbose_name = "Food Item"
        verbose_name_plural = "Food Items"
        ordering = ['vendor', 'name']
        unique_together = ['vendor', 'name']  # Same food item name per vendor
    
    def __str__(self):
        return f"{self.name} - {self.vendor.name}"
    
    def save(self, *args, **kwargs):
        """Auto-generate item_id and slug if not provided."""
        # Auto-generate slug from name if not provided
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            # Ensure slug is unique (even though name is unique per vendor, slug is globally unique)
            while FoodItem.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        # Auto-generate item_id if not provided
        if not self.item_id:
            vendor_slug = self.vendor.slug if self.vendor and self.vendor.slug else 'item'
            name_slug = slugify(self.name) if self.name else 'food'
            # Generate unique item_id: vendor-slug-name-slug-uuid8
            item_id = f"{vendor_slug}-{name_slug}-{uuid4().hex[:8]}"
            # Ensure item_id is unique (very unlikely collision, but check anyway)
            while FoodItem.objects.filter(item_id=item_id).exclude(pk=self.pk).exists():
                item_id = f"{vendor_slug}-{name_slug}-{uuid4().hex[:8]}"
            self.item_id = item_id
        
        super().save(*args, **kwargs)
           
class Category(models.Model):
    """
    Food item categories (e.g., Pizza, Pasta, Desserts).
    """
    name = models.CharField(max_length=100, unique=True, help_text="Category name")
    description = models.TextField(blank=True, help_text="Category description")
    created_at = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(unique=True, blank=True)
    
    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not provided."""
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            # Ensure slug is unique
            while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
class Cart(models.Model):
    """
    Shopping cart for users.
    Each user has one active cart.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart', help_text="Cart owner")
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE, related_name='carts', help_text="Food item in cart", null=True, blank=True)
    qty = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)], help_text="Quantity of this item")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sub_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    cart_id = models.CharField(max_length=100, unique=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    price = models.DecimalField(decimal_places=2, max_digits=12, default=0.00, null=True, blank=True)

    class Meta:
        verbose_name = "Cart"
        verbose_name_plural = "Carts"
    
    # def __str__(self):
    #     return f'{self.cart_id} - {self.food_item.name}'

    def save(self, *args, **kwargs):
        """Auto-generate a unique cart_id if missing."""
        if not self.cart_id:
            cart_id = uuid4().hex[:12]
            # Ensure cart_id is unique (very unlikely collision, but check anyway)
            while Cart.objects.filter(cart_id=cart_id).exclude(pk=self.pk).exists():
                cart_id = uuid4().hex[:12]
            self.cart_id = cart_id
        super().save(*args, **kwargs)
    
    
    @property
    def calculated_total(self):
        """Calculate total amount for all items in cart."""
        return self.sub_total + self.delivery_fee + self.service_fee
    
    @property
    def item_count(self):
        """Return total number of items in cart."""
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    """
    Individual items in a shopping cart.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items', help_text="Cart item user")
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='cart_items', help_text="Cart item vendor")
    
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items', help_text="Parent cart")
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE, related_name='cart_items', help_text="Food item in cart", null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)], help_text="Quantity of this item")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Cart Item"
        verbose_name_plural = "Cart Items"
        unique_together = ['cart', 'food_item']  # One cart item entry per food item per cart
    
    def __str__(self):
        return f"{self.quantity}x {self.food_item.name} in {self.cart.user.username}'s cart"
    
    @property
    def subtotal(self):
        """Calculate subtotal for this cart item."""
        return self.food_item.price * self.quantity
    
    @property
    def price(self):
        """Return price per unit (for API consistency)."""
        return self.food_item.price

class Hostel(models.Model):
    """
    Hostel model representing a hostel.
    """
    name = models.CharField(max_length=100, unique=True, help_text="Hostel name")
    slug = models.SlugField(max_length=100, unique=True, blank=True, help_text="Hostel slug")
    # rooms = models.IntegerField(default=100, help_text="Total number of rooms")
    description = models.TextField(default='Unknown', help_text="Hostel description")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Hostel"
        verbose_name_plural = "Hostels"
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not provided."""
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            # Ensure slug is unique
            while Hostel.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

class Room(models.Model):
    hostel = models.ForeignKey(
        Hostel,
        on_delete=models.CASCADE,
        related_name="rooms"
    )
    number = models.CharField(
        max_length=10,
        help_text="Room number e.g 1, 2, 3, 4"
    )

    class Meta:
        unique_together = ("hostel", "number")
        ordering = ["number"]

    def __str__(self):
        return f"{self.hostel.name} - Room {self.number}"

        
class Rider(models.Model):
    """
    Rider model representing a delivery person.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='rider_profile', help_text="User account for this rider")
    hostels = models.ManyToManyField(Hostel, related_name='riders', blank=True, help_text="Hostels this rider delivers to")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Rider"
        verbose_name_plural = "Riders"

    def __str__(self):
        return f"Rider: {self.user.username}"
 
class DeliveryBatch(models.Model):
    name = models.CharField(max_length=50, unique=True)
    start_time = models.TimeField(default="08:00")
    cutoff_time = models.TimeField(default="18:00")

    is_active = models.BooleanField(default=True)

    def is_open_now(self):
        """Returns True if batch is open for ordering now. Handles midnight wrap-around."""
        if not self.is_active:
            return False
            
        now = timezone.localtime().time()
        
        if self.start_time <= self.cutoff_time:
            # Normal case (e.g., 8am to 6pm)
            return self.start_time <= now < self.cutoff_time
        else:
            # Midnight wrap-around (e.g., 8pm to 3am)
            return now >= self.start_time or now < self.cutoff_time

    def __str__(self):
        return self.name


# class DeliveryBatch(models.Model):
#     """
#     Delivery batches with cutoff times.
#     """
#     name = models.CharField(max_length=50, help_text="Batch name (e.g., '1pm Delivery')")
#     cutoff_time = models.TimeField(help_text="Time after which this batch is unavailable")
#     is_active = models.BooleanField(default=True)
    
#     def __str__(self):
#         return f"{self.name} (Cutoff: {self.cutoff_time})"


class Order(models.Model):
    """
    Order model representing a customer order.
    """
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Processing', 'Processing'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('Processing', 'Processing'),
        ('Paid', 'Paid'),
        ('Failed', 'Failed'),
    ]
    
    buyer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="buyer", blank=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='orders', blank=True, null=True, help_text="Primary vendor (nullable for multi-vendor orders)")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Total order amount")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending', help_text="Order status")
    sub_total = models.DecimalField(default=0.00, max_digits=12, decimal_places=2)
    delivery_fee = models.DecimalField(default=0.00, max_digits=12, decimal_places=2, help_text="Delivery fee from SiteSettings")
    service_fee = models.DecimalField(default=0.00, max_digits=12, decimal_places=2, help_text="Service fee from SiteSettings")
    total_pack_fee = models.DecimalField(default=0.00, max_digits=12, decimal_places=2, help_text="Total packaging fees for all vendors in this order")
    total = models.DecimalField(default=0.00, max_digits=12, decimal_places=2)

    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name='orders', blank=True, null=True, help_text="Hostel associated with this order")
    customer_name = models.CharField(max_length=200, blank=True, help_text="Customer name for the order")
    room_address = models.CharField(max_length=200, blank=True, help_text="Room number or room address")
    delivery_time = models.CharField(max_length=100, blank=True, help_text="Preferred delivery time")
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Pending', help_text="Payment status")
    payment_id = models.CharField(max_length=200, blank=True, help_text="Stripe transaction ID or payment reference")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    date = models.DateField(auto_now_add=True)
    delivery_batch = models.ForeignKey(DeliveryBatch, on_delete=models.SET_NULL, null=True, blank=True, help_text="Delivery batch")
    order_pin = models.IntegerField(blank=True, null=True, help_text="Order pin (4 digits)", unique=True)
    approved = models.BooleanField(default=False, help_text="Whether the order has been approved")
    oid = ShortUUIDField(length=10, max_length=25, alphabet="abcdefghijklmnopqrstuvxyz")

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.id} - {self.buyer.username if self.buyer else 'No buyer'} - {self.vendor.name if self.vendor else 'No vendor'}"
    
    def get_order_items(self):
        return OrderItem.objects.filter(order=self)
    
    def save(self, *args, **kwargs):
        """Auto-generate a unique 4-digit order_pin if not provided."""
        import random
        
        if not self.order_pin:
            # Generate a 4-digit pin (1000-9999)
            max_attempts = 100  # Prevent infinite loop
            attempts = 0
            
            while attempts < max_attempts:
                pin = random.randint(1000, 9999)
                # Check if pin is unique
                if not Order.objects.filter(order_pin=pin).exclude(pk=self.pk).exists():
                    self.order_pin = pin
                    break
                attempts += 1
            
            # If we couldn't find a unique pin after max attempts, raise an error
            if attempts >= max_attempts:
                raise ValueError("Unable to generate a unique 4-digit order pin. Please try again.")
        
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    """
    Individual items in an order.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', help_text="Parent order")
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='order_items', help_text="Order vendor")
    food_item = models.ForeignKey(FoodItem, on_delete=models.PROTECT, related_name='order_items', help_text="Food item in order")
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)], help_text="Quantity ordered")
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], help_text="Price at time of order")
    sub_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Total of Product price * Product Qty")
    service_fee = models.DecimalField(default=0.00, max_digits=12, decimal_places=2, help_text="Estimated Service Fee = service_fee * total (paid by buyer to platform)")
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Grand Total of all amount listed above")
    date = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"
    
    def order_img(self):
        """Return HTML img tag for food item image (for admin display)."""
        try:
            if self.food_item and self.food_item.image:
                return mark_safe(f'<img src="{self.food_item.image.url}" width="50" height="50" style="object-fit:cover; border-radius: 6px;" />')
        except (AttributeError, ValueError):
            pass
        return "-"
   
    # Method to return a formatted order ID
    def order_id(self):
        """Return a formatted order ID string."""
        try:
            if self.order and hasattr(self.order, 'oid'):
                return f"Order ID #{self.order.oid}"
            elif self.order:
                return f"Order ID #{self.order.id}"
        except (AttributeError, TypeError):
            pass
        return "Order ID #Unknown"

    def __str__(self):
        """Return string representation of order item."""
        try:
            food_name = self.food_item.name if self.food_item else "Unknown Item"
            order_id = self.order.id if self.order else "Unknown"
            return f"{self.quantity}x {food_name} in Order #{order_id}"
        except (AttributeError, TypeError):
            return f"OrderItem #{self.id}"
    
    @property
    def vendor_name(self):
        """Return the vendor name or 'Vendor' if not found."""
        return self.vendor.name if self.vendor else "Vendor"

    @property
    def subtotal(self):

        """Calculate subtotal for this order item."""
        return self.price * self.quantity

class SiteSettings(models.Model):
    """
    Site-wide settings that can be configured by admin.
    This is a singleton model - only one instance should exist.
    """
    delivery_fee = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=500.00,
        help_text="Default delivery fee in Naira (e.g., 500.00)"
    )
    service_fee = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=100.00,
        help_text="Default service fee in Naira (e.g., 100.00)"
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"
    
    def __str__(self):
        return f"Site Settings (Delivery: ₦{self.delivery_fee}, Service: ₦{self.service_fee})"
    
    def save(self, *args, **kwargs):
        """
        Ensure only one instance exists (singleton pattern).
        """
        self.pk = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """
        Get or create the singleton settings instance.
        """
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


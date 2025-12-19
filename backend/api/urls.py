from django.urls import path
from userauths import views as userauths_views
from core import views as core_views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('user/token/', userauths_views.MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('user/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('user/register/', userauths_views.RegisterView.as_view(), name='register'),
    
    # Store API Endpoints
    path('category/', core_views.CategoryListView.as_view(), name='category'),
    path('food-items/', core_views.FoodItemListView.as_view(), name='food-items'),
    path('food-item/<str:item_id>/', core_views.FoodItemDetailView.as_view(), name='food-item-detail'),
    path('cart-view/', core_views.CartAPIView.as_view(), name='cart-view'),
    # path('cart-list/<str:cart_id>/', core_views.CartItemListAPIView.as_view(), name='cart-list'),
    # path('cart-list/<str:cart_id>/<int:user_id>/', core_views.CartListView.as_view(), name='cart-list-with-user'),
    path('cart-detail/<str:cart_id>/', core_views.CartDetailView.as_view(), name='cart-detail'),
    path('cart-detail/<str:cart_id>/<int:user_id>/', core_views.CartDetailView.as_view(), name='cart-detail'),
    path('cart-delete/<str:cart_id>/<str:item_id>/', core_views.CartItemDeleteAPIView.as_view(), name='cart-delete'),
    path('cart-delete/<str:cart_id>/<str:item_id>/<int:user_id>/', core_views.CartItemDeleteAPIView.as_view(), name='cart-delete'),
    path('create-order/<str:cart_id>/<int:user_id>/', core_views.CreateOrderAPIView.as_view(), name='create-order-with-user'),
    path('checkout/<int:user_id>/', core_views.CheckoutView.as_view(), name='checkout'),
    path('checkout/<int:user_id>/<int:order_id>/', core_views.CheckoutView.as_view(), name='checkout-order'),
    
    path('vendor-list/', core_views.VendorListView.as_view(), name='vendor-list'),
    path('vendor-detail/<int:vendor_id>/', core_views.VendorDetailView.as_view(), name='vendor-detail'),
    # path('checkout/<order_oid>/', core_views.CheckoutView.as_view(), name='checkout'),

]
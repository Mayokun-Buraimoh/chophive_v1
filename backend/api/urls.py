from django.urls import path
from userauths import views as userauths_views
from core import views as core_views
from rest_framework_simplejwt.views import TokenRefreshView
from customer import views as customer_views

urlpatterns = [
    path('user/token/', userauths_views.MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('user/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('user/register/', userauths_views.RegisterView.as_view(), name='register'),
    path('user/google-signin/', userauths_views.GoogleSignInView.as_view(), name='google-signin'),
    path('user/profile/<user_id>/', userauths_views.ProfileView.as_view(), name='user_profile'),
    path('user/password-reset/<email>/', userauths_views.PasswordEmailVerify.as_view(), name='password_reset'),
    path('user/password-change/', userauths_views.PasswordChangeView.as_view(), name='password_reset'),
    path("verify-email/", userauths_views.VerifyEmailView.as_view()),
     
    # Store API Endpoints
    path('category/', core_views.CategoryListView.as_view(), name='category'),
    path('food-items/', core_views.FoodItemListView.as_view(), name='food-items'),
    path('food-item/<str:item_id>/', core_views.FoodItemDetailView.as_view(), name='food-item-detail'),
    path('delivery-batches/', core_views.DeliveryBatchListView.as_view(), name='delivery-batches'),
    path('cart-view/', core_views.CartAPIView.as_view(), name='cart-view'),
    # path('cart-list/', core_views.CartListView.as_view(), name='cart-list'),
    # path('cart-list/<str:cart_id>/', core_views.CartListView.as_view(), name='cart-list'),
    path('cart-list/<str:cart_id>/<int:user_id>/', core_views.CartListView.as_view(), name='cart-list-with-user'),
    
    # path('cart-list/<str:cart_id>/', core_views.CartItemListAPIView.as_view(), name='cart-list'),
    # path('cart-list/<str:cart_id>/<int:user_id>/', core_views.CartListView.as_view(), name='cart-list-with-user'),
    path('cart-detail/<str:cart_id>/', core_views.CartDetailView.as_view(), name='cart-detail'),
    path('cart-detail/<str:cart_id>/<int:user_id>/', core_views.CartDetailView.as_view(), name='cart-detail'),
    path('cart-item-update/<int:id>/', core_views.CartItemUpdateAPIView.as_view(), name='cart-item-update'),
    path('cart/delete/<str:cart_id>/', core_views.CartDeleteAPIView.as_view(), name='cart-delete'),
    path('cart-delete/<str:cart_id>/<int:cart_item_id>/', core_views.CartItemDeleteAPIView.as_view(), name='cart-delete'),
    path('cart-delete/<str:cart_id>/<int:cart_item_id>/<int:user_id>/', core_views.CartItemDeleteAPIView.as_view(), name='cart-delete-with-user'),
    path('get-cart_id/<int:user_id>/', core_views.GetCartIDAPIView.as_view(), name='get-cart-id'),
    path('create-order/<str:cart_id>/<int:user_id>/', core_views.CreateOrderAPIView.as_view(), name='create-order'),
    path('checkout/<order_oid>/', core_views.CheckoutView.as_view(), name='checkout'),

    path('vendor-list/', core_views.VendorListView.as_view(), name='vendor-list'),
    path('vendor-detail/<int:vendor_id>/', core_views.VendorDetailView.as_view(), name='vendor-detail'),
    # path('checkout/<order_oid>/', core_views.CheckoutView.as_view(), name='checkout'),
    
    # Customer API Endpoints
    path('customer/orders/<user_id>/', customer_views.OrdersAPIView.as_view(), name='customer-orders'),
    path('customer/order/detail/<user_id>/<order_oid>/', customer_views.OrdersDetailAPIView.as_view(), name='customer-order-detail'),
]
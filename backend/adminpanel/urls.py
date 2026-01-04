"""
URL configuration for adminpanel app
"""
from django.urls import path
from .views import dashboard, rider, vendors, profile

app_name = 'adminpanel'

urlpatterns = [
    # Root Redirect
    path('', dashboard.login_view, name='index'),

    # Login
    path('login/', dashboard.login_view, name='login'),
    
    # Admin Dashboard
    path('dashboard/', dashboard.AdminDashboardView.as_view(), name='admin_dashboard'),
    
    # Vendor Manager Dashboard
    path('vendor-manager/', vendors.VendorDashboardView.as_view(), name='vendor_dashboard'),
    path('vendor-manager/update-order/<int:order_id>/', vendors.update_order_status, name='update_order_status'),
    
    # Rider Dashboard
    path('rider-dashboard/', rider.RiderDashboardView.as_view(), name='rider_dashboard'),
    path('rider-dashboard/update-delivery/<int:order_id>/', rider.update_delivery_status, name='update_delivery_status'),
    
    # Vendors Management
    path('vendors/', vendors.VendorsListView.as_view(), name='vendors_list'),
    path('vendors/toggle/<int:vendor_id>/', vendors.toggle_vendor_status, name='toggle_vendor_status'),
    
    # Profile
    path('profile/', profile.ProfileView.as_view(), name='profile'),
    path('profile/change-password/', profile.ChangePasswordView.as_view(), name='change_password'),
    
    # Logout
    path('logout/', dashboard.logout_view, name='logout'),
]


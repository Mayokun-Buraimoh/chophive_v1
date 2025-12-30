
from django.shortcuts import render
from django.http import JsonResponse
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

# Restframework
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken

# Others
import json
import random

# Serializers
from userauths.serializers import MyTokenObtainPairSerializer, ProfileSerializer, RegisterSerializer, UserSerializer


# Models
from userauths.models import Profile, User
from core.views import transfer_guest_cart_to_user



# from django.shortcuts import render

# from rest_framework_simplejwt.views import TokenObtainPairView
# from rest_framework import generics
# from rest_framework.permissions import AllowAny
# from userauths.models import User,Profile
# from userauths.serializers import MyTokenObtainPairSerializer, RegisterSerializer, UserSerializer, ProfileSerializer
# import random
# import shortuuid
# from rest_framework.response import Response
# from rest_framework import status


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        """
        Override post to transfer guest cart after successful login.
        """
        response = super().post(request, *args, **kwargs)
        
        # If login successful (status 200), transfer guest cart
        if response.status_code == status.HTTP_200_OK:
            # Get user from response or request
            user_data = response.data
            # Extract user email from token or get user from request
            try:
                # Get user from email in request
                email = request.data.get('email')
                if email:
                    user = User.objects.get(email=email)
                    # Transfer guest cart to database
                    cart_id = transfer_guest_cart_to_user(request, user)
                    if cart_id:
                        # Add cart_id to response
                        response.data['cart_id'] = cart_id
            except (User.DoesNotExist, AttributeError):
                pass  # User not found or already logged in
        
        return response
    
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        """
        Create user account and transfer guest cart to database.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Transfer guest cart to database if exists
        cart_id = None
        try:
            # Check if session is available and has guest cart
            if hasattr(request, 'session'):
                # Ensure session is saved/loaded
                if not request.session.session_key:
                    request.session.save()
                
                print(f"DEBUG REGISTER: Session key: {request.session.session_key}")
                print(f"DEBUG REGISTER: Session exists: {request.session.exists(request.session.session_key) if request.session.session_key else False}")
                
                guest_cart = request.session.get('guest_cart', {})
                print(f"DEBUG REGISTER: Guest cart from session: {guest_cart}")
                print(f"DEBUG REGISTER: Guest cart type: {type(guest_cart)}, length: {len(guest_cart) if isinstance(guest_cart, dict) else 'N/A'}")
                
                if guest_cart and isinstance(guest_cart, dict) and len(guest_cart) > 0:
                    print(f"Transferring guest cart with {len(guest_cart)} items for user {user.id}")
                    cart_id = transfer_guest_cart_to_user(request, user)
                    print(f"Cart transfer completed. Cart ID: {cart_id}")
                else:
                    print("No guest cart found in session or cart is empty")
            else:
                print("Session not available in request")
        except Exception as e:
            print(f"Error transferring guest cart: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # Generate tokens for the new user
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        
        return Response({
            "message": "User registered successfully",
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username
            },
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token)
            },
            "cart_id": cart_id  # Return cart_id if cart was created
        }, status=status.HTTP_201_CREATED)

class ProfileView(generics.RetrieveAPIView):
    permission_classes = (AllowAny,)
    serializer_class = ProfileSerializer

    def get_object(self):
        user_id = self.kwargs['user_id']

        user = User.objects.get(id=user_id)
        profile = Profile.objects.get(user=user)
        return profile
    
def generate_numeric_otp(length=7):
        # Generate a random 7-digit OTP
        otp = ''.join([str(random.randint(0, 9)) for _ in range(length)])
        return otp
        
class PasswordEmailVerify(generics.RetrieveAPIView):
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer
    
    def get_object(self):
        email = self.kwargs['email']
        user = User.objects.get(email=email)
        
        if user:
            user.otp = generate_numeric_otp()
            uidb64 = user.pk
            
             # Generate a token and include it in the reset link sent via email
            refresh = RefreshToken.for_user(user)
            reset_token = str(refresh.access_token)

            # Store the reset_token in the user model for later verification
            user.reset_token = reset_token
            user.save()

            link = f"http://localhost:5173/create-new-password?otp={user.otp}&uidb64={uidb64}&reset_token={reset_token}"
            
            merge_data = {
                'link': link, 
                'username': user.username, 
            }
            subject = f"Password Reset Request"
            text_body = render_to_string("email/password_reset.txt", merge_data)
            html_body = render_to_string("email/password_reset.html", merge_data)
            
            msg = EmailMultiAlternatives(
                subject=subject, from_email=settings.FROM_EMAIL,
                to=[user.email], body=text_body
            )
            msg.attach_alternative(html_body, "text/html")
            msg.send()
        return user
    

class PasswordChangeView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer
    
    def create(self, request, *args, **kwargs):
        payload = request.data
        
        otp = payload['otp']
        uidb64 = payload['uidb64']
        reset_token = payload['reset_token']
        password = payload['password']

        print("otp ======", otp)
        print("uidb64 ======", uidb64)
        print("reset_token ======", reset_token)
        print("password ======", password)

        user = User.objects.get(id=uidb64, otp=otp)
        if user:
            user.set_password(password)
            user.otp = ""
            user.reset_token = ""
            user.save()

            
            return Response( {"message": "Password Changed Successfully"}, status=status.HTTP_201_CREATED)
        else:
            return Response( {"message": "An Error Occured"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


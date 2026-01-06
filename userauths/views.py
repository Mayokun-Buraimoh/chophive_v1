
from django.shortcuts import render
from django.http import JsonResponse
from django.core.mail import EmailMultiAlternatives
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework.exceptions import NotFound
from django.shortcuts import get_object_or_404
import jwt
# Restframework
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from sib_api_v3_sdk import ApiClient, Configuration, TransactionalEmailsApi, SendSmtpEmail

# Others

import json
import random


# Serializers
from userauths.serializers import MyTokenObtainPairSerializer, ProfileSerializer, RegisterSerializer, UserSerializer

User = get_user_model()

# Models
from userauths.models import Profile, User



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
    
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def get_serializer_context(self):
        return {"request": self.request}

class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        token = request.query_params.get("token")

        if not token:
            return Response({"error": "Token missing"}, status=400)

        try:
            access_token = AccessToken(token)
            user_id = access_token["user_id"]

            user = User.objects.get(id=user_id)
            user.is_active = True
            user.is_email_verified = True
            user.save()

            return Response({"message": "Email verified successfully"}, status=200)

        except Exception:
            return Response({"error": "Invalid or expired token"}, status=400)

class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        user_id = self.kwargs['user_id']
        return get_object_or_404(Profile, user__id=user_id)


# class ProfileView(generics.CrreRetrieveAPIView):
#     permission_classes = (AllowAny,)
#     serializer_class = ProfileSerializer

#     def get_object(self):
#         user_id = self.kwargs['user_id']

#         user = User.objects.get(id=user_id)
#         profile = Profile.objects.get(user=user)
#         return profile
    
def generate_numeric_otp(length=7):
        # Generate a random 7-digit OTP
        otp = ''.join([str(random.randint(0, 9)) for _ in range(length)])
        return otp

class PasswordEmailVerify(generics.RetrieveAPIView):
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer

    def get_object(self):
        email = self.kwargs.get("email")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise NotFound("User with this email does not exist")

        # 1️⃣ Generate OTP
        user.otp = generate_numeric_otp()

        # 2️⃣ Encode user ID properly
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

        # 3️⃣ Generate short-lived JWT reset token
        refresh = RefreshToken.for_user(user)
        reset_token = str(refresh.access_token)

        # 4️⃣ Save OTP + reset token
        user.reset_token = reset_token
        user.save()

        # 5️⃣ Build reset link
        link = (
            f"http://localhost:5173/create-new-password"
            f"?otp={user.otp}&uidb64={uidb64}&reset_token={reset_token}"
        )

        # 6️⃣ Email context
        context = {
            "link": link,
            "username": user.username,
        }

        subject = "Password Reset Request"
        html_body = render_to_string("email/password_reset.html", context)

        # 7️⃣ Configure Brevo SDK correctly (no 'with')
        configuration = Configuration()
        configuration.api_key["api-key"] = settings.BREVO_API_KEY

        api_client = ApiClient(configuration)
        email_api = TransactionalEmailsApi(api_client)

        send_email = SendSmtpEmail(
            sender={"name": "ChopHive", "email": "no-reply@chophive.com"},
            to=[{"email": user.email, "name": user.username}],
            subject=subject,
            html_content=html_body,
        )

        try:
            response = email_api.send_transac_email(send_email)
            print("Brevo sent:", response)
        except Exception as e:
            print("Brevo error:", e)

        return user
        
        # msg = EmailMultiAlternatives(
        #     subject=subject,
        #     from_email=settings.FROM_EMAIL,
        #     to=[user.email],
        # )
        # msg.attach_alternative(html_body, "text/html")
        # msg.send()

        

# class PasswordEmailVerify(generics.RetrieveAPIView):
#     permission_classes = (AllowAny,)
#     serializer_class = UserSerializer
    
#     def get_object(self):
#         email = self.kwargs['email']
#         user = User.objects.get(email=email)
        
#         if user:
#             user.otp = generate_numeric_otp()
#             uidb64 = user.pk
            
#              # Generate a token and include it in the reset link sent via email
#             refresh = RefreshToken.for_user(user)
#             reset_token = str(refresh.access_token)

#             # Store the reset_token in the user model for later verification
#             user.reset_token = reset_token
#             user.save()

#             link = f"http://localhost:5173/create-new-password?otp={user.otp}&uidb64={uidb64}&reset_token={reset_token}"
            
#             merge_data = {
#                 'link': link, 
#                 'username': user.username, 
#             }
#             subject = f"Password Reset Request"
#             # text_body = render_to_string("email/password_reset.txt", merge_data)
#             html_body = render_to_string("email/password_reset.html", merge_data)
            
#             msg = EmailMultiAlternatives(
#                 subject=subject, from_email=settings.FROM_EMAIL,
#                 to=[user.email], body=html_body
#             )
#             # msg.attach_alternative(html_body, "text/html")
#             msg.send()
#         return user
    
class PasswordChangeView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        payload = request.data

        otp = payload.get('otp')
        uidb64 = payload.get('uidb64')
        reset_token = payload.get('reset_token')
        password = payload.get('password')

        if not all([otp, uidb64, reset_token, password]):
            return Response(
                {"message": "All fields are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ Decode uidb64 → integer user ID
        try:
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(
                id=user_id,
                otp=otp,
                reset_token=reset_token
            )
        except (User.DoesNotExist, ValueError, TypeError):
            return Response(
                {"message": "Invalid reset link"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ Set new password
        user.set_password(password)

        # ✅ Invalidate OTP & token
        user.otp = None
        user.reset_token = None
        user.save()

        return Response(
            {"message": "Password changed successfully"},
            status=status.HTTP_200_OK
        )

# class PasswordChangeView(generics.CreateAPIView):
#     permission_classes = (AllowAny,)
#     serializer_class = UserSerializer
    
#     def create(self, request, *args, **kwargs):
#         payload = request.data
        
#         otp = payload['otp']
#         uidb64 = payload['uidb64']
#         reset_token = payload['reset_token']
#         password = payload['password']

#         print("otp ======", otp)
#         print("uidb64 ======", uidb64)
#         print("reset_token ======", reset_token)
#         print("password ======", password)

#         user = User.objects.get(id=uidb64, otp=otp)
#         if user:
#             user.set_password(password)
#             user.otp = ""
#             user.reset_token = ""
#             user.save()

            
#             return Response( {"message": "Password Changed Successfully"}, status=status.HTTP_201_CREATED)
#         else:
#             return Response( {"message": "An Error Occured"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GoogleSignInView(generics.GenericAPIView):
    """
    View to handle Google OAuth sign-in.
    Receives a Google credential token from the frontend,
    verifies it, creates or gets the user, and returns JWT tokens.
    """
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        credential = request.data.get('credential')
        
        if not credential:
            return Response(
                {"error": "Credential token is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Decode the Google JWT token (without verification for now)
            # In production, you should verify the token with Google's public keys
            decoded_token = jwt.decode(credential, options={"verify_signature": False})
            
            # Extract user information from the token
            email = decoded_token.get('email')
            name = decoded_token.get('name', '')
            given_name = decoded_token.get('given_name', '')
            family_name = decoded_token.get('family_name', '')
            picture = decoded_token.get('picture', '')
            
            if not email:
                return Response(
                    {"error": "Email not found in Google token"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Generate username from email or name
            username = email.split('@')[0] if email else given_name.lower().replace(' ', '') if given_name else 'user'
            
            # Get or create user
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': username,
                    'first_name': given_name,
                    'last_name': family_name,
                }
            )
            
            # If user already exists but name fields are empty, update them
            if not created:
                if not user.first_name and given_name:
                    user.first_name = given_name
                if not user.last_name and family_name:
                    user.last_name = family_name
                user.save()
            
            # Update profile if picture is available
            if hasattr(user, 'profile') and picture:
                profile = user.profile
                # You can store the picture URL or download it
                # For now, we'll just ensure the profile exists
                if not profile.username:
                    profile.username = username
                    profile.save()
            
            # Transfer guest cart to user if it exists
            # transfer_guest_cart_to_user(request, user)
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            
            return Response({
                "access": access_token,
                "refresh": refresh_token,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                }
            }, status=status.HTTP_200_OK)
            
        except jwt.DecodeError:
            return Response(
                {"error": "Invalid token format"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            print(f"Google Sign-In error: {str(e)}")
            return Response(
                {"error": f"An error occurred during Google sign-in: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


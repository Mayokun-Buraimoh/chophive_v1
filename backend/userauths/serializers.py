from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from userauths.models import Profile, User
from django.conf import settings
from django.urls import reverse
from django.core.mail import EmailMultiAlternatives
from rest_framework_simplejwt.tokens import RefreshToken
from sib_api_v3_sdk import ApiClient, TransactionalEmailsApi
from sib_api_v3_sdk.configuration import Configuration
from sib_api_v3_sdk.models import SendSmtpEmail
from django.template.loader import render_to_string

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['username'] = user.username
        return token

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'password2']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError("Passwords do not match")
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")

        user = User.objects.create(
            email=validated_data['email'],
            username=validated_data['username'],
            is_active=False,               # 👈 IMPORTANT
            is_email_verified=False,
        )
        user.set_password(validated_data['password'])
        user.save()

        # 🔐 Generate verification token
        token = RefreshToken.for_user(user).access_token

        verify_url = f"http://localhost:5173/verify-email?token={token}"

        # 📧 Render HTML email
        html_body = render_to_string(
            "email/verify_email.html",
            {
                "username": user.username,
                "verify_url": verify_url,
            }
        )

        # 5️⃣ Configure Brevo API
        configuration = Configuration()
        configuration.api_key["api-key"] = settings.BREVO_API_KEY
        api_client = ApiClient(configuration)
        email_api = TransactionalEmailsApi(api_client)

        # 6️⃣ Build Brevo email
        send_email = SendSmtpEmail(
            sender={"name": "ChopHive", "email": "no-reply@chophive.com"},  # ✅ must be verified in Brevo
            to=[{"email": user.email, "name": user.username}],
            subject="Verify your ChopHive account",
            html_content=html_body,
        )

        # 7️⃣ Send email
        try:
            response = email_api.send_transac_email(send_email)
            print("Brevo email sent:", response)
        except Exception as e:
            print("Brevo error:", e)

        return user

        # subject = "Verify your ChopHive account"

        # msg = EmailMultiAlternatives(
        #     subject=subject,
        #     from_email=settings.DEFAULT_FROM_EMAIL,
        #     to=[user.email],
        # )
        # msg.attach_alternative(html_body, "text/html")
        # msg.send()

        # return user


# class RegisterSerializer(serializers.ModelSerializer):
#     password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
#     password2 = serializers.CharField(write_only=True, required=True)
    
#     class Meta:
#         model = User
#         fields = ['email', 'username', 'password', 'password2']
        
#     def validate(self, attrs):
#         if attrs['password'] != attrs['password2']:
#             raise serializers.ValidationError({"password": "Password fields didn't match."})
#         return attrs
    
#     def create(self, validated_data):
#         user = User.objects.create(
#             email=validated_data['email'],
#             username=validated_data['username'],
#         )
#         user.set_password(validated_data['password'])
#         user.save()
#         return user

class UserSerializer(serializers.ModelSerializer): 
    class Meta:
        model = User
        fields = "__all__"
        
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = '__all__'
        
    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['user'] = UserSerializer(instance.user).data
        return response

class ProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = Profile
        fields = '__all__'

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['user'] = UserSerializer(instance.user).data
        return response
    
class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

from datetime import timedelta
from venv import logger
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.generics import RetrieveUpdateAPIView, CreateAPIView, GenericAPIView, UpdateAPIView
from .models import User
from Apps.Trading.models import Wallet
from django.contrib.auth.models import Group, Permission
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone

from .serializer import (
    EmailSerializer,
    GroupSerializer,
    PermissionSerializer,
    UserSerializer,
    UserRegisterSerializer,
    UserTokenObtainPairSerializer,
    ResetPasswordSerializer,
    ChangePasswordSerializer,
)

from rest_framework.response import Response
from django.core.mail import send_mail
import uuid
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework.serializers import ValidationError
from django.contrib.auth import logout as django_logout
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.db import transaction
from Common.Bast_Get_data.GetModel import Base_GetModel
from .permission import (UserPermission, PermissionPermission, GroupPermission)


class UserRegisterCreateAPIview(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]

    def post(self,request, *args, **kwargs ):
        # Wallet_Accout = self.request.data.get("Wallet_Accout")
        serializer= self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                self.perform_create(serializer)
                instance = serializer.instance
                
                Wallet.objects.create(
                    currency="USDT",
                    demo_balance=1000,   
                    real_balance=0, 
                    reserved=0,
                    admin_wallet=False,
                    user_id=instance
                )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class UserViewsets(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [UserPermission]

    # def list(self, request, *args, **kwargs):
    #     # Retrieve all users
    #     users = self.queryset.all()
    #     serialized_users = []

    #     for user in users:
    #         # Create a dictionary with user data
    #         wallet_data = WalletSerializer(user.wallet_id).data if user.wallet_id else None
    #         user_data = {
    #             "id": user.id,
    #             "last_login": user.last_login,  # Last login timestamp
    #             "is_superuser": user.is_superuser,  # Superuser flag
    #             "is_staff": user.is_staff,  # Staff status
    #             "is_active": user.is_active,  # Active status
    #             "date_joined": user.date_joined,  # Account creation timestamp
    #             "is_deleted": user.is_deleted,  # Custom field for soft delete
    #             "deleted_at": user.deleted_at,  # Timestamp for soft delete
    #             "username": user.username,  # Username
    #             "email": user.email,  # Email address
    #             "password": user.password,  # Password (hashed)
    #             "created_at": user.created_at,  # Creation timestamp
    #             "updated_at": user.updated_at,  # Last update timestamp
    #             "avatar": user.avatar.url if user.avatar else None,  # Avatar URL
    #             "groups": [group.name for group in user.groups.all()],  # User groups
    #             "user_permissions": [perm.codename for perm in user.user_permissions.all()],  # User permissions
    #             "wallet_id": wallet_data,  # Nested Wallet data (if available)
    #         }
    #         serialized_users.append(user_data)

    #     return Response({"users": serialized_users}, status=status.HTTP_200_OK)
    
    # def retrieve(self, request, *args, **kwargs):

    #     try:
    #         user = self.queryset.get(pk=kwargs['pk'])
    #     except User.DoesNotExist:
    #         return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    #     wallet_data = WalletSerializer(user.wallet_id).data if user.wallet_id else None
    #     user_data = {
    #         "id": user.id,
    #         "last_login": user.last_login,  # Last login timestamp
    #         "is_superuser": user.is_superuser,  # Superuser flag
    #         "is_staff": user.is_staff,  # Staff status
    #         "is_active": user.is_active,  # Active status
    #         "date_joined": user.date_joined,  # Account creation timestamp
    #         "is_deleted": user.is_deleted,  # Custom field for soft delete
    #         "deleted_at": user.deleted_at,  # Timestamp for soft delete
    #         "username": user.username,  # Username
    #         "email": user.email,  # Email address
    #         "password": user.password,  # Password (hashed)
    #         "created_at": user.created_at,  # Creation timestamp
    #         "updated_at": user.updated_at,  # Last update timestamp
    #         "avatar": user.avatar.url if user.avatar else None,  # Avatar URL
    #         "groups": [group.name for group in user.groups.all()],  # User groups
    #         "user_permissions": [perm.codename for perm in user.user_permissions.all()],  # User permissions
    #         "wallet_id": wallet_data,  # Nested Wallet data (if available)
    #     }

    #     return Response({"user": user_data}, status=status.HTTP_200_OK)


class GroupViewSet(ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [GroupPermission]


class PermissionViewSet(ModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [PermissionPermission]


class User_Me(RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated,]

    def get_object(self):
        return self.request.user
    
    
class VerifyEmailAPIView(APIView):
    
    permission_classes = [AllowAny,]
    authentication_classes = []
    def get(self, request, *args, **kwargs):
        uid = request.query_params.get('uid')
        token = request.query_params.get('token')
        # print("Decoded UID:", uid)
        if uid is None or token is None:
            return Response({'error': 'Missing uid or token'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            # print("Decoded UID:", uid)
            uid = force_str(urlsafe_base64_decode(uid))
            # print("Decoded UID:", uid)
            user = User.objects.get(pk=uid)
            if user.is_verify == True:
                return Response({'detail': 'Email is already verified.'}, status=status.HTTP_200_OK)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        print("Verify target user:", user)
        # token = default_token_generator.check_token(user)
        print("Is token valid?", token)
        
        if user is not None:
            is_valid_token = default_token_generator.check_token(user, token)
            print("Is token valid?", is_valid_token)

            if is_valid_token == True:
                user.is_verify = True
                user.save()
                return Response({'detail': 'Email successfully verified'}, status=status.HTTP_200_OK)
            else:
                return Response({'detail': 'Invalid verification link'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'Invalid verification link'}, status=status.HTTP_400_BAD_REQUEST)
        

class ResendVerificationEmailAPIView(APIView):
    serializer_class = EmailSerializer
    permission_classes = [AllowAny]
    def dispatch(self, request, *args, **kwargs):
        print(">>> DISPATCH CALLED")  # 👈 ถ้าไม่แสดง แปลว่า permission reject ก่อน
        return super().dispatch(request, *args, **kwargs)
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)
            print("Resend target user:", user)
            if user.is_verify == True:
                return Response({'message': 'Email is already verified.'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                subject = f'Verify Your Email Address - {uuid.uuid4().hex[:6]}'
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                print(f"Generated Token: {token}")
                verify_url = f"{settings.FRONTEND_VERIFY_URL}?uid={uid}&token={token}"

                context = {
                    'user': user,
                    'verify_url': verify_url,
                }
                html_content = render_to_string('verification_email.html', context)
                text_content = f'Hi {user.username},\n\nPlease verify your email address by clicking the following link:\n\n{verify_url}'

                msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [user.email])
                msg.attach_alternative(html_content, "text/html")
                print("Sending email to:", user.email)
                sent_count = msg.send()
                print("Email sent count:", sent_count)
                return Response({'message': 'Verification email resent successfully.'}, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(f'Error sending email: {e}')
                print(f'Error sending email: {e}')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(TokenObtainPairView):
    
    serializer_class = UserTokenObtainPairSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.user
            response = super().post(request, *args, **kwargs)
            response.data.update({
                "user_id": user.id,
                "email": user.email,
                "username": user.username,
                "is_superuser": user.is_superuser,
                "role": user.groups.first().name if user.groups.exists() else None,
                "is_verify": user.is_verify,
                "is_2fa_enabled": user.is_2fa_enabled
            })
        else:
            print("Serializer errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return response


class ChangePasswordAPIview(APIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [AllowAny, UserPermission]
    
    def patch(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            user = request.user
            serializer.update(user, serializer.validated_data)
            return Response({"status": "password set ... "}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class Send_Email_Rest_Password(APIView):
    
    serializer_class = EmailSerializer
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)

            # Generate token and reset link
            encoded_pk = urlsafe_base64_encode(force_bytes(user.id))
            token = default_token_generator.make_token(user)
            reset_url = reverse("api:reset-password", kwargs={"encoded_pk": encoded_pk, "token": token})
            reset_link = f"{settings.FRONTEND_RESET_PASSWORD_URL}{reset_url}"
            subject = 'Password Reset Request'
            message = f'Hi {user.username},\n\nPlease click the link below to reset your password:\n\n{reset_link}'
            
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

            return Response({"message": "Password reset email sent."}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordAPIView(APIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = [AllowAny]
    def patch(self, request, encoded_pk, token):
        user_id = force_str(urlsafe_base64_decode(encoded_pk))
        user = User.objects.get(pk=user_id)
        
        if default_token_generator.check_token(user, token):
            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid():
                user.set_password(serializer.validated_data['password'])
                user.save()
                return Response({"message": "Password reset complete"}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"error": "Invalid token or user"}, status=status.HTTP_400_BAD_REQUEST)
    
    # def post(self, request, *args, **kwargs):
    #     serializer = ResetPasswordSerializer(data=request.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response({"message": "Password reset successful."}, status=status.HTTP_200_OK)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

import pyotp
import qrcode
import base64
from io import BytesIO
from django.core.files.base import ContentFile
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from django_otp.plugins.otp_totp.models import TOTPDevice


class GenerateOTPView(APIView):

    def post(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "กรุณาเข้าสู่ระบบก่อน"}, status=401)

        # ตรวจสอบว่า TOTPDevice ถูกสร้างเมื่อไหร่และยังไม่เกินระยะเวลาที่กำหนด
        totp_device, created = TOTPDevice.objects.get_or_create(user=user, name="default")
        if not created and totp_device.created_at < timezone.now() - timedelta(minutes=30):
            totp_device.delete()  # ลบเก่าแล้วสร้างใหม่
            totp_device = TOTPDevice.objects.create(user=user, name="default")

        # แปลง bin_key เป็น base32 string (ถ้ามันไม่ใช่แล้ว)
        secret = base64.b32encode(totp_device.bin_key).decode('utf-8')  # แปลงให้เป็น base32 string

        # ใช้คีย์ที่แปลงแล้ว
        totp = pyotp.TOTP(secret)  # ใช้ base32 string เป็นคีย์
        otp = totp.now()  # สร้าง OTP 6 หลัก

        # สร้าง OTP URL
        otp_url = totp.provisioning_uri(name=user.username, issuer_name="MyApp")

        # สร้าง QR Code
        qr_code_img = qrcode.make(otp_url)
        qr_code_buffer = BytesIO()
        qr_code_img.save(qr_code_buffer)
        qr_code_buffer.seek(0)
        qr_code_file = ContentFile(qr_code_buffer.read())

        # แปลง QR code เป็น Base64 string
        qr_code_base64 = base64.b64encode(qr_code_file.read()).decode('utf-8')  # แปลงเป็น Base64

        # ส่ง OTP 6 หลัก และ QR code เป็น Base64
        return Response({
            "otp": otp,
            "otp_url": otp_url,
            "qr_code": qr_code_base64
        }, status=201)


class ValidateOTPView(APIView):
    # permission_classes = [IsAuthenticated]

    def post(self, request):
        otp = request.data.get("otp")
        user = request.user

        try:
            totp_device = TOTPDevice.objects.get(user=user , name="default")
            if totp_device.verify_token(otp):
                # OTP ถูกต้อง
                user.is_2fa_enabled = True
                user.save()
                return Response({"detail": "เปิดใช้งาน 2FA สำเร็จ"}, status=200)
            else:
                return Response({"detail": "OTP ไม่ถูกต้อง"}, status=400)
        except TOTPDevice.DoesNotExist:
            return Response({"detail": "ไม่พบ TOTP Device"}, status=404)
        
    
import jwt

class ValidateOTP_UserLoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    def post(self, request):
        
        otp = request.data.get("code")
        token = request.data.get("twoFALoginToken")
        email = request.data.get("email")
        if not token or not otp:
            return Response({"detail": "Missing token or OTP"}, status=400)

        try:
            # Decode JWT Token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            print("Token Expiration:", payload.get("exp"))
            if not user_id:
                return Response({"detail": "Invalid token"}, status=400)
            email_user = payload.get("email")
            if email_user != email:
                return Response({"detail": "Invalid token"}, status=400)

            user = User.objects.get(id=user_id)
            try:
                totp_device = TOTPDevice.objects.get(user=user, name="default")
                if totp_device.verify_token(otp):

                    return Response({"detail": "2FA verification successful", "token": token }, status=200)
                else:
                    return Response({"detail": "OTP ไม่ถูกต้อง"}, status=400)
            except TOTPDevice.DoesNotExist:
                return Response({"detail": "ไม่พบ TOTP Device"}, status=404)

        except jwt.ExpiredSignatureError:
            return Response({"detail": "Token expired"}, status=401)
        except jwt.InvalidTokenError:
            return Response({"detail": "Invalid token"}, status=401)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=404)


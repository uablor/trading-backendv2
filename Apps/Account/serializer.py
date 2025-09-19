from rest_framework.serializers import ModelSerializer
from .models import (User)
from Apps.Trading.models import Wallet
from django.contrib.auth.models import (Group, Permission)
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from django_otp.plugins.otp_totp.models import TOTPDevice

class UserRegisterSerializer(ModelSerializer):
    password = serializers.CharField(
        required=True, 
        write_only=True, 
        validators=[validate_password]
        )
    password2 = serializers.CharField(required=True, write_only=True)
    username = serializers.CharField(required=True)
    email = serializers.EmailField(
        required=True, validators=[UniqueValidator(queryset=User.objects.all())]
    )
    class Meta:
        model = User
        fields = ["email", "password", "password2","username"]
        
    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )

        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        validated_data['is_verify'] = False
        validated_data["is_active"] = True
        user = User.objects.create_user(
            email=validated_data["email"],
            username=validated_data["username"],
            password=validated_data["password"]  # จะถูก hash โดยอัตโนมัติ
        )
        return user


class UserSerializer(ModelSerializer):
    
    class Meta:
        fields = "__all__"
        model = User
        extra_kwargs = {
            "last_login": {"required": False},
            "date_joined": {"required": False},
            "created_at": {"required": False},
            "updated_at": {"required": False},
            "updated_at": {"required": False},
            "password": {"write_only": True},
        }

    def validate_password(self, value):

        validate_password(value)
        return value

    def create(self, validated_data):
        validated_data["password"] = make_password(validated_data["password"])

        validated_data['is_verify'] = False
        validated_data["is_active"] = True

        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop("password", None)
        return super().update(instance, validated_data)

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")
        if self.instance:
            fields.pop("password")

        if request.method in ["POST", "PUT", "PATCH"]:
            user = request.user
            if (
                not user.is_superuser
                and not user.groups.filter(permissions__codename=" ").exists()
                ):
                fields.pop("is_staff")
                fields.pop("is_superuser")
                fields.pop("groups")
                fields.pop("user_permissions")
        return fields
     
        
class GroupSerializer(ModelSerializer):
    class Meta:
        fields = "__all__"
        model = Group
   
        
class PermissionSerializer(ModelSerializer):
    class Meta:
        fields = "__all__"
        model = Permission
        

class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    class Meta:
        fields = "email"
    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email address is not associated with any account.")
        return value


class UserTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token["user_id"] = user.id
        token["email"] = user.email
        token["role"] = user.groups.first().name if user.groups.exists() else "user"
        token["username"] = user.username
        token["is_verify"] =  user.is_verify
        token["is_2fa_enabled"] = user.is_2fa_enabled

        return token

    def validate(self, attrs):

        user = authenticate(username=attrs['email'], password=attrs['password'])
        if user is None:
            raise serializers.ValidationError('Invalid email or password.')
        
        # ตรวจสอบการยืนยันบัญชีผู้ใช้
        if not user.is_verify:
            raise AuthenticationFailed('Account is not verified.')
        
        # data = super().validate(attrs)
        # user = self.user

        # if user.is_2fa_enabled:
        #     otp = self.context['request'].data.get('otp')
        #     totp_device = TOTPDevice.objects.filter(user=user, name="default").first()
        #     if not totp_device or not totp_device.verify_token(otp):
        #         raise serializers.ValidationError({"otp": "OTP ไม่ถูกต้องหรือไม่ได้ระบุ"})


        return super().validate(attrs)


class ChangePasswordSerializer(serializers.Serializer):
    password = serializers.CharField(required= True, write_only = True)
    new_password = serializers.CharField(required= True, write_only = True, validators=[validate_password])
    new_password2 = serializers.CharField(required= True, write_only = True)
    class Meta:
        model = User
        fields = ['password','new_password','new_password2']

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.check_password(attrs['password']):
            raise serializers.ValidationError({"password": "Current password is incorrect."})
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password2": "New password fields didn't match."})
        return attrs

    def update(self, instance, validated_data):
        instance.set_password(validated_data['new_password'])
        instance.save()
        return instance


class ResetPasswordSerializer(serializers.Serializer):
    
    password = serializers.CharField(write_only=True, required = True, validators = [validate_password])
    confirm_password = serializers.CharField(write_only=True, required = True)
        
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        data.pop('confirm_password')
        make_password(data['password'])
        return data
        
        
    #     try:
    #         # Decode user ID
    #         user_id = force_str(urlsafe_base64_decode(data['uidb64']))
    #         user = User.objects.get(pk=user_id)
    #     except (TypeError, ValueError, OverflowError, User.DoesNotExist):
    #         raise serializers.ValidationError("Invalid UID")

    #     # Verify the token
    #     if not default_token_generator.check_token(user, data['token']):
    #         raise serializers.ValidationError("Invalid token")

    #     # Check if passwords match
    #     if data['password'] != data['confirm_password']:
    #         raise serializers.ValidationError("Passwords do not match.")

    #     # Hash the password before returning
    #     data['password'] = make_password(data['password'])
    #     data.pop('confirm_password')

    #     # Add the user to the data to update the password later
    #     data['user'] = user
        
    #     return data
    
    # def save(self, **kwargs):
    #     validated_data = self.validated_data
    #     user = validated_data['user']
    #     user.password = validated_data['password']
    #     user.save()


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    class Meta:
        fields = "email"
    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email address is not associated with any account.")
        return value


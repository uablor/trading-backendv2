from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext as _
from Common.validator.validators import validate_image_extension,validate_max_file_size
from .utils import profile_image_storage
# from Apps.Trading.models import Wallet
from Common.models.base_models import Base_model
from django.db import transaction

class UserManager(BaseUserManager):
    def create_user(
        self, email,username=None , password=None, **extra_fields
    ):
        if not email:
            raise ValueError(_("The Email field must be set"))
        if not username:
            raise ValueError(_("The username field must be set"))
        email = self.normalize_email(email)
        user = self.model(
            email=email, username=username, **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    @transaction.atomic
    def create_superuser(
        self, email, username=None, password=None, **extra_fields
    ):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_verify", True)
        
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        user =  self.create_user(email, username, password, **extra_fields)
        # Wallet.objects.create(
        #     currency="USDT",
        #     balance=0,
        #     reserved=0,
        #     admin_wallet=True,  # Set to True for superuser
        #     user_id=user
        # )
        return user


class User(AbstractUser, Base_model):
    first_name = None
    last_name = None
    username = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_verify = models.BooleanField(default=False)
    is_2fa_enabled = models.BooleanField(default=False)
    avatar = models.FileField(
        upload_to=profile_image_storage,
        validators=[validate_image_extension, validate_max_file_size],
        blank=True,
        null=True,
    )
    object = UserManager()
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]
    def __str__(self):
        return self.username

class Wallet(Base_model):

    demo_balance = models.IntegerField( default=1000)
    currency = models.CharField(max_length=50, blank=False, null=False)
    real_balance = models.IntegerField(blank=False, null=False)
    last_updated = models.DateTimeField(auto_now=True)  # auto_now=True will update this field to the current time whenever the model is saved
    reserved = models.IntegerField(blank=False, null=False)
    admin_wallet = models.BooleanField(default=False)
    user_id = models.ForeignKey(User,on_delete=models.CASCADE, null=True )

    def __str__(self):
        return f"Wallet {self.id} - {self.currency}"

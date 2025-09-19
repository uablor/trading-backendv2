from django.db.models.signals import post_save , pre_save, pre_delete
from django.dispatch import receiver
import logging
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
# from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from .models import User, Wallet
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from django.core.files import File
import uuid
from rest_framework.serializers import ValidationError

from PIL import Image
from io import BytesIO

logger = logging.getLogger(__name__)

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Wallet

@receiver(post_save, sender=User)
def send_verification_email(sender, instance, created, **kwargs):
    if created:
        if instance.is_verify == True:
            return
        try:
            subject = f'Verify Your Email Address - {uuid.uuid4().hex[:6]}'
            uid = urlsafe_base64_encode(force_bytes(instance.pk))
            token = default_token_generator.make_token(instance)
            verify_url = f"{settings.FRONTEND_VERIFY_URL}?uid={uid}&token={token}"
            
            context = {
                'user': instance,
                'verify_url': verify_url,
            }
            
            html_content = render_to_string('verification_email.html', context)
            text_content = f'Hi {instance.username},\n\nPlease verify your email address by clicking the following link:\n\n{verify_url}'

            msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [instance.email])
            msg.attach_alternative(html_content, "text/html")
            msg.send()

        except Exception as e:
            logger.error(f'Error sending email: {e}')
   

@receiver(pre_save, sender=User)
def handle_avatar_update(sender, instance, **kwargs):
    print('Triggerd user...handle_avatar_update')
    if instance.deleted_at is not None:
        # User is being soft deleted, do not process the avatar
        return

    avatar_changed = False
    if instance.pk:
        try:
            old_instance = sender.objects.only('avatar').get(pk=instance.pk)
            avatar_changed = old_instance.avatar != instance.avatar
            if avatar_changed and old_instance.avatar:
                # Delete the old avatar
                old_instance.avatar.delete(save=False)
        except sender.DoesNotExist:
            pass  # Old instance does not exist, this must be a new instance
    else:
        avatar_changed = bool(instance.avatar)  # New instance with an avatar

    if avatar_changed and instance.avatar:
        compress_avatar(instance)


def compress_avatar(instance):
    try:
        with Image.open(instance.avatar) as im:
            img_format = im.format
            if img_format not in ['JPEG', 'PNG']:
                raise Exception(f'Unsupported image format: {img_format}')

            # Save the compressed image to BytesIO object
            im.thumbnail((400, 400))
            im_io = BytesIO()
            save_params = {'JPEG': ('JPEG', {'quality': 70}), 'PNG': ('PNG', {'optimize': True})}
            save_format, save_kwargs = save_params[img_format]
            im.save(im_io, save_format, **save_kwargs)

            # Create a django-friendly File object
            new_image = File(im_io, name=instance.avatar.name)

            # Assign the compressed image back to the instance's avatar attribute
            instance.avatar = new_image
    except Exception as e:
        raise ValidationError(f'Error compressing the image. {str(e)}')


@receiver(pre_delete, sender=User)
def delete_user_avatar_on_delete(sender, instance, **kwargs):
    print('Triggered user....delete_user_avatar_on_delete')
    # User is being hard deleted, delete the avatar
    if instance.avatar:
        instance.avatar.delete(save=False)


@receiver(post_save, sender=User)
def create_wallet_for_user(sender, instance, created, **kwargs):
    
    admin_wallet = True if instance.is_superuser else False
    
    if created:
        # Create a new wallet for the user when the user is created
        Wallet.objects.create(
            currency="USDT",
            real_balance=0,
            reserved=0,
            admin_wallet=admin_wallet,
            user_id=instance
        )
        

@receiver(post_save, sender=Wallet)
def send_wallet_update(sender, instance, created, **kwargs):
    # print(f"Wallet updated: {instance.real_balance}, {instance.demo_balance}")
    channel_layer = get_channel_layer()
    # ส่งข้อมูลการอัปเดตไปยังทุกคนในกลุ่ม 'wallet_update'
    # print('have change the wallet')
    
    # ใช้ async_to_sync เพื่อเรียกใช้ group_send
    async_to_sync(channel_layer.group_send)(
        "wallet_update",  # กลุ่ม
        {
            "type": "send_wallet_update",
            "wallet": {
                "real_balance": instance.real_balance,
                "demo_balance": instance.demo_balance,
            }
        }
    )
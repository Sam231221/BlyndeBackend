from django.conf import settings
from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail

from django.contrib.auth import get_user_model

User = get_user_model()

import imagekitio
from .models import Genre, Review


@receiver(post_save, sender=Review)
def update_product_rating(sender, instance, **kwargs):
    instance.product.update_review_count()
    instance.product.update_rating()


@receiver(pre_delete, sender=Genre)
def delete_imagekit_file(sender, instance, **kwargs):
    if instance.image_file_id:
        imagekit = imagekitio.ImageKit(
            private_key=settings.IMAGEKIT["PRIVATE_KEY"],
            public_key=settings.IMAGEKIT["PUBLIC_KEY"],
            url_endpoint=settings.IMAGEKIT["URL_ENDPOINT"],
        )
        try:
            imagekit.delete_file(file_id=instance.image_file_id)
        except Exception as e:
            pass


@receiver(post_save, sender=User)
def send_email_verification(sender, instance, created, **kwargs):
    if created and not instance.email_verified:
        uidb64 = urlsafe_base64_encode(force_bytes(instance.pk))
        token = default_token_generator.make_token(instance)
        verification_link = (
            f"https://blynde.up.railway.app/api/users/verify-email/{uidb64}/{token}/"
        )
        subject = "Email Verification for Your Account"
        message = f"Please click the link below to verify your email address:\n\n{verification_link}"
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [instance.email]
        print("Verification Link:", verification_link)
        send_mail(subject, message, from_email, recipient_list)


@receiver(post_save, sender=User)
def send_welcome_email(sender, instance, created, **kwargs):
    if created and instance.email_verified:
        subject = "Welcome to Our Website"
        message = f"Hello {instance.email},\n\nWelcome to our website! Thank you for joining us."
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [instance.email]
        send_mail(subject, message, from_email, recipient_list)


def updateUser(sender, instance, **kwargs):
    user = instance
    if user.email != "":
        user.username = user.email


pre_save.connect(updateUser, sender=User)

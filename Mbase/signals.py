from django.db.models.signals import pre_save, post_save


from django.core.mail import EmailMultiAlternatives
from django.dispatch import receiver
from django.template.loader import render_to_string

from django.urls import reverse

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail

from django.conf import settings

from django.contrib.auth import get_user_model

User = get_user_model()


# Signal for Welcome & Email Verification
@receiver(post_save, sender=User)
def send_email_verification(sender, instance, created, **kwargs):
    if created and not instance.email_verified:
        uidb64 = urlsafe_base64_encode(force_bytes(instance.pk))
        token = default_token_generator.make_token(instance)
        verification_link = (
            f"http://127.0.0.1:8000/api/users/verify-email/{uidb64}/{token}/"
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


# Every time email is updated, update username with that email.
def updateUser(sender, instance, **kwargs):
    user = instance
    if user.email != "":
        user.username = user.email


pre_save.connect(updateUser, sender=User)

import logging
from django.conf import settings
from django.db.models.signals import pre_save, post_delete, post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth import get_user_model
import imagekitio
from .models import Genre, Review

User = get_user_model()
logger = logging.getLogger(__name__)


@receiver([post_save, post_delete], sender=Review)
def update_product_rating(sender, instance, **kwargs):
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
def send_welcome_email(sender, instance, created, **kwargs):
    if created and instance.email_verified:
        try:
            subject = "Greetings"
            heading = "Welcome to Our Website"
            message = f"Hello {instance.email},\n\nWelcome to our website! Thank you for joining us."
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [instance.email]
            html_content = render_to_string(
                "email/template1.html",
                {
                    "subject": subject,
                    "heading": heading,
                    "recipient_name": instance.first_name,
                    "message_content": message,
                    "sender_name": from_email,
                },
            )
            text_content = render_to_string(
                "email/template1.txt",
                {
                    "subject": subject,
                    "heading": heading,
                    "recipient_name": instance.first_name,
                    "message_content": message,
                    "sender_name": from_email,
                },
            )
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=f"<{settings.EMAIL_HOST_USER}>",
                to=recipient_list,
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)
            logger.info(f"Welcome email sent to {instance.email}")
        except Exception as e:
            logger.error(f"Failed to send welcome email to {instance.email}: {str(e)}")


def updateUser(sender, instance, **kwargs):
    user = instance
    if user.email != "":
        user.username = user.email


pre_save.connect(updateUser, sender=User)


@receiver(post_save, sender=User)
def send_email_verification(sender, instance, created, **kwargs):
    if created and not instance.email_verified:
        try:
            uidb64 = urlsafe_base64_encode(force_bytes(instance.pk))
            token = default_token_generator.make_token(instance)

            verification_link = (
                f"{settings.DJANGO_BASE_URL}/api/users/verify-email/{uidb64}/{token}/"
            )
            subject = "Email Verification for Your Account"
            heading = "Welcome to Our Store."
            message = f"Please click the link below to verify your email address:\n\n"
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [instance.email]

            text_content = render_to_string(
                "email/template1.txt",
                {
                    "subject": subject,
                    "heading": heading,
                    "recipient_name": instance.first_name,
                    "message_content": message,
                    "cta_button": True,
                    "cta_url": verification_link,
                    "cta_text": "Verify Email",
                    "sender_name": from_email,
                },
            )
            html_content = render_to_string(
                "email/template1.html",
                {
                    "subject": subject,
                    "heading": heading,
                    "recipient_name": instance.first_name,
                    "message_content": message,
                    "cta_button": True,
                    "cta_url": verification_link,
                    "cta_text": "Verify Email",
                    "sender_name": from_email,
                },
            )

            # Create email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=f"<{settings.EMAIL_HOST_USER}>",
                to=recipient_list,
            )
            email.attach_alternative(html_content, "text/html")

            # Send email
            email.send(fail_silently=False)
            logger.info(f"Verification email sent to {instance.email}")

        except Exception as e:
            logger.error(
                f"Failed to send verification email to {instance.email}: {str(e)}"
            )

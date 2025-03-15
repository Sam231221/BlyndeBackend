import logging
import re
from datetime import timedelta

from django.db.utils import IntegrityError
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.core.exceptions import ObjectDoesNotExist
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.exceptions import TokenError

from Mbase.serializers import (
    UserSerializerWithToken,
)

User = get_user_model()
logger = logging.getLogger(__name__)


@api_view(["POST"])
def register_user(request):
    data = request.data

    required_fields = [
        "username",
        "firstName",
        "lastName",
        "email",
        "password",
        "confirmPassword",
        "agreeToTerms",
    ]
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return Response(
            {
                "errors": {
                    field: f"{field.capitalize()} is required"
                    for field in missing_fields
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not data.get("agreeToTerms"):
        return Response(
            {"errors": {"agreeToTerms": "You must agree to the terms and conditions"}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if len(data["password"]) < 8:
        return Response(
            {"errors": {"password": "Password must be at least 8 characters long"}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if data["password"] != data["confirmPassword"]:
        return Response(
            {"errors": {"confirmPassword": "Passwords do not match"}},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:

        if User.objects.filter(email=data["email"]).exists():
            return Response(
                {"errors": {"general": "User with this email already exists"}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.create_user(
            username=data["username"],
            first_name=data["firstName"],
            last_name=data["lastName"],
            email=data["email"].lower(),
            password=data["password"],
            agreed_to_terms=True,
        )

        serializer = UserSerializerWithToken(user, many=False)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    except IntegrityError:
        return Response(
            {"errors": {"general": "User with this email already exists"}},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return Response(
            {
                "errors": {
                    "general": str(e),
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def login_user(request):
    email = request.data["email"]
    password = request.data["password"]
    remember_me = request.data.get("rememberMe")
    required_fields = [
        "email",
        "password",
    ]
    missing_fields = [field for field in required_fields if not request.data.get(field)]

    if missing_fields:
        return Response(
            {
                "errors": {
                    field: f"{field.capitalize()} is required"
                    for field in missing_fields
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    else:
        user = authenticate(request, username=email, password=password)

        if user:
            if not user.email_verified:
                return Response(
                    {"errors": {"general": "User account is not verified yet."}},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            refresh = RefreshToken.for_user(user)
            if remember_me:

                refresh.set_exp(lifetime=timedelta(days=3))
            return Response(
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "profile_pic_url": user.profile_pic_url,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "refresh_token": str(refresh),
                    "email_verified": user.email_verified,
                    "access_token": str(refresh.access_token),
                },
                status=status.HTTP_200_OK,
            )

        else:
            return Response(
                {"errors": {"general": "Invalid Credentials Provided."}},
                status=status.HTTP_401_UNAUTHORIZED,
            )


@api_view(["POST"])
def logout_user(request):
    refresh_token = request.data.get("refresh")

    if not refresh_token:
        return Response(
            {"error": "Refresh token is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response(status=status.HTTP_204_NO_CONTENT)

    except TokenError as e:
        logger.error(f"TokenError: {e}")
        return Response(
            {"error": "Invalid or expired refresh token"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        logger.exception(f"Unexpected logout error: {e}")
        return Response(
            {"error": "An unexpected error occurred"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def refresh_token_view(request):
    refresh_token = request.data.get("refresh")

    if not refresh_token:
        return Response(
            {"error": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        refresh = RefreshToken(refresh_token)
        if hasattr(refresh, "blacklist"):
            refresh.blacklist()

        user_id = refresh.payload.get("user_id")
        if not user_id:
            return Response(
                {"error": "Invalid token: user ID missing"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )
        new_refresh = RefreshToken.for_user(user)

        return Response(
            {
                "access": str(new_refresh.access_token),
                "refresh": str(new_refresh),
            },
            status=status.HTTP_200_OK,
        )

    except Exception:
        return Response(
            {"error": "Invalid or expired refresh token"},
            status=status.HTTP_401_UNAUTHORIZED,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def request_password_reset(request):
    email = request.data.get("email")
    if not email:
        return Response(
            {"errors": {"email": "Email is required"}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = User.objects.filter(email=email).first()

    if not user:
        logger.warning(f"Password reset requested for non-existent email: {email}")
        return Response(
            {"errors": {"general": "User with this email does not exist"}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_link = f"{settings.FRONTEND_BASE_URL}/request-reset-password/confirm?token={uid}-{token}"

        subject = "Password Reset Request"
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [user.email]

        context = {
            "subject": subject,
            "heading": "Password Reset Request",
            "recipient_name": user.first_name,
            "message_content": "We have received a request to reset your password. "
            "Please click on the link below to reset your password. "
            "If you didn’t request this, you can ignore this email.",
            "cta_button": True,
            "cta_url": reset_link,
            "cta_text": "Reset Password",
            "sender_name": from_email,
        }

        html_content = render_to_string("email/template1.html", context)
        text_content = (
            f"Hello {user.first_name},\n\n"
            f"We have received a request to reset your password. "
            f"Click the link below to reset your password:\n\n"
            f"{reset_link}\n\n"
            f"If you didn’t request this, you can ignore this email."
        )

        # Send email
        email_message = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=recipient_list,
        )
        email_message.attach_alternative(html_content, "text/html")
        email_message.send(fail_silently=False)

        logger.info("Password reset email sent successfully to %s", user.email)

    except Exception as e:
        logger.error(f"Error sending password reset email: {e}")
        return Response(
            {"errors": {"general": "An error occurred. Please try again later."}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(
        {"detail": "A reset link has been sent to your email."},
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
def confirm_password_reset(request):
    token_data = request.data.get("token")
    new_password = request.data.get("new_password")
    confirm_password = request.data.get("confirm_password")

    if not token_data or not new_password or not confirm_password:
        return Response(
            {"error": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST
        )

    match = re.match(r"([^.-]+)-(.+)", token_data)
    if not match:
        return Response(
            {"error": "Invalid token format"}, status=status.HTTP_400_BAD_REQUEST
        )

    uid, token = match.groups()

    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)
    except (User.DoesNotExist, ValueError, TypeError):
        return Response(
            {"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST
        )

    if not default_token_generator.check_token(user, token):
        return Response(
            {"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST
        )

    if new_password != confirm_password:
        return Response(
            {"error": "Passwords do not match"}, status=status.HTTP_400_BAD_REQUEST
        )

    if len(new_password) < 8:
        return Response(
            {"error": "Password must be at least 8 characters long"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user.set_password(new_password)
    user.save()

    return Response(
        {"detail": "Password successfully reset"}, status=status.HTTP_200_OK
    )


@api_view(["GET"])
def verify_user_email(request, uidb64, token):
    try:

        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)

        if default_token_generator.check_token(user, token):
            if user.email_verified:
                return Response(
                    {"message": "Email already verified."},
                    status=status.HTTP_200_OK,
                )

            user.email_verified = True
            user.save()

            return Response(
                {"message": "Email verified successfully!"},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"error": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        return Response(
            {"error": "Invalid verification link."},
            status=status.HTTP_400_BAD_REQUEST,
        )

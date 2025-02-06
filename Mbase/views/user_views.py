from django.contrib.auth.hashers import make_password
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail

from django.conf import settings
from datetime import timedelta
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
import re
from django.utils.encoding import force_bytes, force_str
from django.db.utils import IntegrityError
from django.contrib.auth import authenticate
from django.contrib.auth import update_session_auth_hash

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from django.contrib.auth import get_user_model
from Mbase.serializers import (
    PasswordChangeSerializer,
    UserSerializer,
    UserCreateSerializer,
    UserSerializerWithToken,
)

User = get_user_model()


FRONTEND_URL = "http://localhost:5173/request-reset-password/confirm?token="


# 1. Request Password Reset
@api_view(["POST"])
@permission_classes([AllowAny])
def request_password_reset(request):
    email = request.data.get("email")
    if not email:
        return Response(
            {"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    user = User.objects.filter(email=email).first()
    if user:
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_link = f"{FRONTEND_URL}{uid}-{token}"

        # Send email with reset link
        send_mail(
            "Password Reset Request",
            f"Click the link below to reset your password:\n\n{reset_link}",
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

    return Response(
        {"detail": "If the email exists, a reset link has been sent."},
        status=status.HTTP_200_OK,
    )


# 2. Confirm Password Reset
@api_view(["POST"])
def confirm_password_reset(request):
    token_data = request.data.get("token")
    new_password = request.data.get("new_password")
    confirm_password = request.data.get("confirm_password")
    print(token_data, new_password, confirm_password)
    if not token_data or not new_password or not confirm_password:
        return Response(
            {"error": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST
        )

    # Extract UID and token
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

    # Validate token
    if not default_token_generator.check_token(user, token):
        return Response(
            {"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST
        )

    # Password validation
    if new_password != confirm_password:
        return Response(
            {"error": "Passwords do not match"}, status=status.HTTP_400_BAD_REQUEST
        )

    if len(new_password) < 8:
        return Response(
            {"error": "Password must be at least 8 characters long"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Save new password
    user.set_password(new_password)
    user.save()

    return Response(
        {"detail": "Password successfully reset"}, status=status.HTTP_200_OK
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def loginUser(request):
    username = request.data["email"]
    password = request.data["password"]
    remember_me = request.data.get("rememberMe")
    required_fields = [
        "email",
        "password",
    ]
    missing_fields = [field for field in required_fields if not request.data.get(field)]

    if missing_fields:
        return Response(
            {"errors": {field: f"{field} is required" for field in missing_fields}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    else:
        user = authenticate(request, username=username, password=password)

        if user:
            if not user.email_verified:  # Check if the user is active
                return Response(
                    {"errors": {"general": "User account is verified yet."}},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            refresh = RefreshToken.for_user(user)
            if remember_me:
                # Set longer expiry time for refresh token
                refresh.set_exp(lifetime=timedelta(days=3))
            return Response(
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "profile_pic": user.profile_pic,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "refresh": str(refresh),
                    "email_verified": user.email_verified,
                    # access
                    "token": str(refresh.access_token),
                },
                status=status.HTTP_200_OK,
            )

        else:  # Authentication failed
            return Response(
                {"errors": {"general": "Invalid credentials"}},
                status=status.HTTP_401_UNAUTHORIZED,
            )


@api_view(["POST"])
def registerUser(request):
    data = request.data

    # Validate Emtyness
    required_fields = [
        "username",
        "firstName",
        "lastName",
        "email",
        "password",
        "confirmPassword",
        "agreeToTerms",
    ]
    # Validate required fields
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return Response(
            {"errors": {field: f"{field} is required" for field in missing_fields}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validate agreeToTerms
    if not data.get("agreeToTerms"):
        return Response(
            {"errors": {"agreeToTerms": "You must agree to the terms and conditions"}},
            status=status.HTTP_400_BAD_REQUEST,
        )
    # Validate password length
    if len(data["password"]) < 8:
        return Response(
            {"errors": {"password": "Password must be at least 8 characters long"}},
            status=status.HTTP_400_BAD_REQUEST,
        )
        # Validate password match
    if data["password"] != data["confirmPassword"]:
        return Response(
            {"errors": {"confirmPassword": "Passwords do not match"}},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        # Check if email already exists
        if User.objects.filter(email=data["email"]).exists():
            return Response(
                {"detail": "User with this email already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Create user
        user = User(
            username=data["username"],
            first_name=data["firstName"],
            last_name=data["lastName"],
            email=data["email"],
        )
        user.set_password(data["password"])  # Proper way to hash password
        user.agreed_to_terms = True
        user.save()
        # Serialize user data with token
        serializer = UserSerializerWithToken(user, many=False)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    except IntegrityError:
        return Response(
            {"errors": {"email": "User with this email already exists"}},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return Response(
            {
                "errors": {
                    "server": "An error occurred while creating the user",
                    "detail": str(e),
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
def verify_email(request, uidb64, token):
    try:
        # Decode the user ID
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)

        # Verify the token
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


# Change Password
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    if request.method == "POST":
        serializer = PasswordChangeSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if user.check_password(serializer.data.get("old_password")):
                user.set_password(serializer.data.get("new_password"))
                user.save()
                update_session_auth_hash(
                    request, user
                )  # To update session after password change
                return Response(
                    {"message": "Password changed successfully."},
                    status=status.HTTP_200_OK,
                )
            return Response(
                {"error": "Incorrect old password."}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT"])
@permission_classes([IsAuthenticated])
def getUserProfile(request):
    user = request.user
    if request.method == "GET":
        # Get user profile data USING UserSerializer NO NEED TO USE UserSerializerWithToken
        serializer = UserSerializer(user, many=False)
        return Response(serializer.data)
    elif request.method == "PUT":
        # Update user profile data
        data = request.data
        # UserSerializerWithToken is used so only authenticated and owner can update it.
        serializer = UserSerializerWithToken(user, many=False)
        user.first_name = data["name"]
        user.username = data["email"]
        user.email = data["email"]
        user.save()
        # returning user details with token
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def listUsers(request):
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAdminUser, IsAuthenticated])
def createUser(request):
    serializer = UserCreateSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def getUserDetails(request, pk):
    user = User.objects.get(id=pk)
    serializer = UserSerializer(user, many=False)
    return Response(serializer.data)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def updateUser(request, pk):
    user = User.objects.get(id=pk)

    data = request.data

    user.first_name = data["first_name"]
    user.last_name = data["last_name"]
    user.username = data["username"]
    user.username = data["email"]
    user.email = data["email"]
    user.profile_pic = data["profile_pic"]

    user.save()

    serializer = UserSerializer(user, many=False)

    return Response(serializer.data)


@api_view(["DELETE"])
@permission_classes([IsAdminUser])
def deleteUser(request, pk):
    userForDeletion = User.objects.get(id=pk)
    userForDeletion.delete()
    return Response("User was deleted", status=status.HTTP_200_OK)

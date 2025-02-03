from django.contrib.auth.hashers import make_password
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from Mbase.serializers import (
    PasswordChangeSerializer,
    UserSerializer,
    UserCreateSerializer,
    UserSerializerWithToken,
)

from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from django.contrib.auth import update_session_auth_hash
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from django.contrib.auth import get_user_model

User = get_user_model()
# from django.contrib.auth.tokens import default_token_generator
# from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode


# def generate_email_verification_token(user):
#     uid = urlsafe_base64_encode(str(user.pk).encode())
#     token = default_token_generator.make_token(user)
#     return uid, token


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    # this function returns actual response to frontend.
    """
    refresh and access are returned under hood(Hover the pointer over TokenObtainPairSerializer and click on it for more details. )
        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)
    """

    def validate(self, attrs):
        data = super().validate(attrs)
        serializer = UserSerializerWithToken(self.user).data

        """
        serializer: {'id': 1, '_id': 1, 'username': 'Sam', 'email': 'samirshahi9882@gmail.com', 'name': 'samirshahi9882@gmail.com', 'isAdmin': True, 
        'token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjY0Nzg0MDEyLCJpYXQiOjE2NjIxOTIwMTIsImp0aSI6IjFhYzRhNjFjYTgwMzQwNGE4ZmUwNDIzZTM4YTEyNDY1IiwidXNlcl9pZCI6MX0.dnV2PalNENdhO8Iw3_RE2A4Ipq4gTRBELzfyXNuRMf8'}    
            
            """

        for key, value in serializer.items():
            data[key] = value
        return data


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


@api_view(["POST"])
def registerUser(request):
    data = request.data

    # Validate Emtyness
    required_fields = ["name", "email", "password"]
    for field in required_fields:
        if field not in data or not data[field]:
            return Response(
                {"detail": f"{field} is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
    # Validate Password Length
    if len(data["password"]) < 8:
        return Response(
            {"detail": "Password must be at least 8 characters long"},
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
        user = User.objects.create(
            first_name=data["name"],
            username=data["email"],  # Username is set to email for simplicity
            email=data["email"],
            password=make_password(data["password"]),  # Hash the password
        )

        # Serialize user data with token
        serializer = UserSerializerWithToken(user, many=False)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response(
            {"detail": "An error occurred while creating the user", "error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator


User = get_user_model()


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


# Login with Email OTP
class LoginWithOTP(APIView):
    def post(self, request):
        email = request.data.get("email", "")
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "User with this email does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

        otp = generate_otp()
        user.otp = otp
        user.save()

        send_otp_email(email, otp)

        return Response(
            {"message": "OTP has been sent to your email."}, status=status.HTTP_200_OK
        )


class ValidateOTP(APIView):
    def post(self, request):
        email = request.data.get("email", "")
        otp = request.data.get("otp", "")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "User with this email does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.otp == otp:
            user.otp = None
            user.save()

            # Authenticate the user and create or get an authentication token
            token, _ = Token.objects.get_or_create(user=user)

            return Response({"token": token.key}, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST
            )


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

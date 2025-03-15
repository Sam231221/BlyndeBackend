import logging
import base64
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions

from Mbase.serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserSerializerWithToken,
    WishlistSerializer,
    WishlistCreateSerializer,
    OrderSerializer,
)
from Mbase.mixins.imagekit import imagekit
from Mbase.models import Wishlist, Order

User = get_user_model()
logger = logging.getLogger(__name__)


@api_view(["GET", "PUT"])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    user = request.user

    if request.method == "GET":
        serializer = UserSerializer(user, many=False)
        return Response(serializer.data)

    elif request.method == "PUT":
        data = request.data
        user.first_name = data.get("first_name", user.first_name)
        user.last_name = data.get("last_name", user.last_name)
        user.email = data.get("email", user.email)
        avatar_file = request.FILES.get("avatar")

        if avatar_file:
            try:
                if user.profile_pic_id:
                    imagekit.delete_file(user.profile_pic_id)
                    upload_response = imagekit.upload_file(
                        file=base64.b64encode(avatar_file.read()).decode("utf-8"),
                        file_name=f"avataR-{avatar_file.name}",
                        options=UploadFileRequestOptions(
                            use_unique_file_name=False,
                            folder="/Blynde/Users/",
                        ),
                    )
                    user.profile_pic_id = upload_response.file_id
                    user.profile_pic_url = upload_response.url
                    user.save()
            except Exception as e:
                logger.error(f"Image upload failed: {str(e)}")
                return Response(
                    {
                        "errors": {
                            "general": "An error occurred while uploading the image"
                        }
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        serializer = UserSerializerWithToken(user, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def wishlist_items(request):
    if request.method == "GET":
        wishlist_items = Wishlist.objects.filter(user=request.user)
        serializer = WishlistSerializer(wishlist_items, many=True)
        return Response(
            {"count": wishlist_items.count(), "items": serializer.data},
            status=status.HTTP_200_OK,
        )

    elif request.method == "POST":
        productId = request.data.get("product")
        if not productId:
            return Response(
                {"errors": {"general": "Wishlist item not found."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            wishlist_item = Wishlist.objects.get(user=request.user, product=productId)
            wishlist_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Wishlist.DoesNotExist:
            serializer = WishlistCreateSerializer(
                data=request.data, context={"request": request}
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                {"errors": {"general": str(e)}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_all_orders(self, request, user_id):
    try:
        user = get_object_or_404(User, pk=user_id)
        orders = Order.objects.filter(user=user).order_by("-createdAt")
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_recent_orders(request, user_id):
    try:
        user = get_object_or_404(User, pk=user_id)

        recent_orders = Order.objects.filter(
            user=user, createdAt__gte=timezone.now() - timedelta(days=7)
        ).order_by("-createdAt")

        serializer = OrderSerializer(recent_orders, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def getUserDetails(request, pk):
    user = User.objects.get(id=pk)
    serializer = UserSerializer(user, many=False)
    return Response(serializer.data)

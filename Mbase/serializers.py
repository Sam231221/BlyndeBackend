from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

from rest_framework_simplejwt.tokens import RefreshToken
from .models import (
    Category,
    Genre,
    ImageAlbum,
    Product,
    Size,
    Order,
    OrderItem,
    ShippingAddress,
    Review,
    Color,
    DiscountOffers,
)


class ResetPasswordEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
            "username",
            "email",
            "password",
            "profile_pic",
        )  # Include all necessary fields
        extra_kwargs = {"password": {"write_only": True}}  # Make password write-only

    def create(self, validated_data):
        user = User.objects.create_user(
            **validated_data
        )  # Use create_user for proper password hashing
        return user


class UserSerializer(serializers.ModelSerializer):
    # custom fields to be serialized.
    name = serializers.SerializerMethodField(read_only=True)
    _id = serializers.SerializerMethodField(read_only=True)
    isAdmin = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        # serialize only this field.
        fields = [
            "id",
            "_id",
            "first_name",
            "last_name",
            "username",
            "profile_pic_url",
            "email",
            "name",
            "isAdmin",
        ]

    # obj is User Instance
    def get__id(self, obj):
        return obj.id

    def get_isAdmin(self, obj):
        return obj.is_staff

    def get_name(self, obj):
        name = obj.first_name
        if name == "":
            name = obj.email

        return name


class UserSerializerWithToken(UserSerializer):
    token = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "_id",
            "username",
            "first_name",
            "last_name",
            "email",
            "profile_pic_url",
            "token",
        ]

    # generates token for the user
    def get_token(self, obj):
        token = RefreshToken.for_user(obj)
        return str(token.access_token)


from rest_framework import serializers
from django.db.models import Count
from .models import Category


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ("_id", "name", "parent", "slug", "product_count")


class RecursiveCategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    product_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ["_id", "name", "slug", "children", "product_count"]

    def get_children(self, obj):
        if obj.children.exists():
            serializer = self.__class__(
                obj.children.all(), many=True, context=self.context
            )
            return serializer.data
        return []


class CategoryWithChildrenSerializer(serializers.ModelSerializer):
    children = RecursiveCategorySerializer(many=True, read_only=True)
    product_count = serializers.IntegerField()

    class Meta:
        model = Category
        fields = ["_id", "name", "slug", "children", "product_count"]


class ColorSerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Color
        fields = ("_id", "name", "hex_code", "product_count")

    def get_product_count(self, obj):
        return obj.product_set.count()


class SizeSerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Size
        fields = ("_id", "name", "description", "product_count")

    def get_product_count(self, obj):
        return obj.product_set.count()


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = "__all__"


class DiscountOffersSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscountOffers
        fields = "__all__"  # Include all fields


class ProductSerializer(serializers.ModelSerializer):
    reviews = serializers.SerializerMethodField(read_only=True)
    colors = ColorSerializer(many=True)
    categories = CategorySerializer(many=True)
    size = SizeSerializer(many=True)
    image_albums = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = "__all__"

    def get_reviews(self, obj):
        reviews = obj.reviews.all()
        serializer = ReviewSerializer(reviews, many=True)
        return serializer.data

    def get_image_albums(self, obj):
        image_albums = ImageAlbum.objects.filter(product=obj)
        return ImageAlbumSerializer(image_albums, many=True).data

    # def get_colors(self, obj):
    #     colors = obj.color_set.all()
    #     return ColorSerializer(colors, many=True).data


class ProductCreateUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = [
            "name",
            "thumbnail",
            "brand",
            "size",
            "colors",
            "categories",
            "description",
            "price",
            "countInStock",
            "badge",
        ]


class ImageAlbumSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageAlbum
        fields = "__all__"


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ["product", "user", "name", "createdAt", "rating", "comment"]


class ShippingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = "__all__"


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = "__all__"


class OrderSerializer(serializers.ModelSerializer):
    # custom ones
    orderItems = serializers.SerializerMethodField(read_only=True)
    shippingAddress = serializers.SerializerMethodField(read_only=True)
    user = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Order
        fields = "__all__"

    def get_orderItems(self, obj):
        items = obj.orderitem_set.all()
        serializer = OrderItemSerializer(items, many=True)
        return serializer.data

    def get_shippingAddress(self, obj):
        try:
            address = ShippingAddressSerializer(obj.shippingaddress, many=False).data
        except:
            address = False
        return address

    def get_user(self, obj):
        user = obj.user
        serializer = UserSerializer(user, many=False)
        return serializer.data

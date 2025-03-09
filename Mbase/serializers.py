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
    Wishlist,
    Discount,
)


class ResetPasswordEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


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
        )
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class UserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField(read_only=True)
    _id = serializers.SerializerMethodField(read_only=True)
    isAdmin = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
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

    def get_token(self, obj):
        token = RefreshToken.for_user(obj)
        return str(token.access_token)


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
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer):
    reviews = serializers.SerializerMethodField(read_only=True)
    reviews_count = serializers.SerializerMethodField(read_only=True)
    colors = ColorSerializer(many=True)
    categories = CategorySerializer(many=True)
    sizes = SizeSerializer(many=True)
    image_albums = serializers.SerializerMethodField()
    discounted_price = serializers.SerializerMethodField()
    discount_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = "__all__"

    def get_discounted_price(self, obj):
        discounted_price = obj.get_discounted_price()
        return discounted_price if discounted_price else None

    def get_discount_percentage(self, obj):
        discounted_percentage = obj.get_discount_percentage()
        return discounted_percentage if discounted_percentage else None

    def get_reviews(self, obj):
        reviews = obj.reviews.all()
        serializer = ReviewSerializer(reviews, many=True)
        return serializer.data

    def get_reviews_count(self, obj):
        return obj.reviews.count()

    def get_image_albums(self, obj):
        image_albums = ImageAlbum.objects.filter(product=obj)
        return ImageAlbumSerializer(image_albums, many=True).data


class ProductCreateUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = [
            "name",
            "thumbnail",
            "brand",
            "sizes",
            "colors",
            "categories",
            "description",
            "price",
            "countInStock",
            "badge",
        ]


class DiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount
        fields = [
            "id",
            "description",
            "discount_type",
            "amount",
            "is_global",
            "start_date",
            "end_date",
            "priority",
        ]


class ImageAlbumSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageAlbum
        fields = "__all__"


class WishlistSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Wishlist
        fields = ["id", "product", "added_at"]
        read_only_fields = ["id", "added_at"]


class WishlistCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wishlist
        fields = ["product"]

    def create(self, validated_data):
        user = self.context["request"].user
        product = validated_data["product"]
        try:
            wishlist_item = Wishlist.objects.create(user=user, product=product)
            return wishlist_item
        except Exception as e:
            raise serializers.ValidationError(
                {"detail": "This product is already in your wishlist."}
            )


class ReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(many=False)

    class Meta:
        model = Review
        fields = ["product", "user", "createdAt", "rating", "comment"]


class ShippingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = "__all__"


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = "__all__"


class OrderSerializer(serializers.ModelSerializer):
    orderItems = serializers.SerializerMethodField(read_only=True)
    shippingAddress = serializers.SerializerMethodField(read_only=True)
    user = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Order
        fields = "__all__"

    def get_orderItems(self, obj):
        items = obj.order_items.all()
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

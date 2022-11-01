from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Category, Genre, ImageAlbum, Product, Order, OrderItem, ShippingAddress, Review


class UserSerializer(serializers.ModelSerializer):
    #custom fields to be serialized.
    name = serializers.SerializerMethodField(read_only=True)
    _id = serializers.SerializerMethodField(read_only=True)
    isAdmin = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        #serialize only this field.
        fields = ['id', '_id', 'username', 'email', 'name', 'isAdmin']

    #obj is User Instance
    def get__id(self, obj):
        return obj.id

    def get_isAdmin(self, obj):
        return obj.is_staff

    def get_name(self, obj):
        name = obj.first_name
        if name == '':
            name = obj.email

        return name


class UserSerializerWithToken(UserSerializer):
    token = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ['id', '_id', 'username', 'email', 'name', 'isAdmin', 'token']

    def get_token(self, obj):
        token = RefreshToken.for_user(obj)
        return str(token.access_token)

'''
print('serializer:', serializer)
UserSerializerWithToken(<User: samirshahi9882@gmail.com>):
    id = IntegerField(label='ID', read_only=True)
    _id = SerializerMethodField(read_only=True)
    username = CharField(help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, validators=[<django.contrib.auth.validators.UnicodeUsernameValidator object>, <UniqueValidator(queryset=User.objects.all())>])
    email = EmailField(allow_blank=True, label='Email address', max_length=254, required=False)
    name = SerializerMethodField(read_only=True)
    isAdmin = SerializerMethodField(read_only=True)
    token = SerializerMethodField(read_only=True)
    
print('serialized data:', serializer.data)
serialized data: {
      'id': 3,
      '_id': 3, 
      'username': 'saara2@gmail.com', 
      'email': 'saara2@gmail.com', 
      'name': 'Saara', 
      'isAdmin': False, 
      'token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjY0Nzg1NDYyLCJpYXQiOjE2NjIxOTM0NjIsImp0aSI6ImIxNzE1YzB
      hM2E1MzQ3ZTFhMTdlYmM4NjM5MzdhMzg1IiwidXNlcl9pZCI6M30.v7WcrI_vMmkWYV-NPDs_0GxZr7bM8E36w_5mHlcfTRI'
    }    
'''

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields ="__all__"

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = "__al__"


class ProductSerializer(serializers.ModelSerializer):
    reviews = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Product
        fields = '__all__'

    def get_reviews(self, obj):
        reviews = obj.review_set.all()
        serializer = ReviewSerializer(reviews, many=True)
        return serializer.data

class ImageAlbumSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageAlbum
        fields = "__all__"


class ShippingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = '__all__'


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    #custom ones
    orderItems = serializers.SerializerMethodField(read_only=True)
    shippingAddress = serializers.SerializerMethodField(read_only=True)
    user = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Order
        fields = '__all__'

    def get_orderItems(self, obj):
        items = obj.orderitem_set.all()
        serializer = OrderItemSerializer(items, many=True)
        return serializer.data

    def get_shippingAddress(self, obj):
        try:
            address = ShippingAddressSerializer(
                obj.shippingaddress, many=False).data
        except:
            address = False
        return address

    def get_user(self, obj):
        user = obj.user
        serializer = UserSerializer(user, many=False)
        return serializer.data

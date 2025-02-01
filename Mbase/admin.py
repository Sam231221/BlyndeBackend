from django.contrib import admin
from .models import (
    Category,
    Size,
    Color,
    ImageAlbum,
    Genre,
    Product,
    Order,
    OrderItem,
    Review,
    ShippingAddress,
    DiscountOffers,
)


admin.site.register(
    (Category, DiscountOffers, Size, Color, Genre, Order, OrderItem, ShippingAddress)
)


# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model

User = get_user_model()


class UserAdmin(UserAdmin):
    model = User
    list_display = ["username", "email", "email_verified", "is_staff", "is_active"]
    list_filter = ["is_staff", "is_active", "email_verified"]
    search_fields = ["email", "username"]


admin.site.register(User, UserAdmin)


class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "comment",
        "product",
        "user",
        "rating",
    )
    list_filter = ("rating",)
    search_fields = ("product__name", "user__username")


admin.site.register(Review, ReviewAdmin)


class ImageAlbumAdmin(admin.TabularInline):
    model = ImageAlbum


class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "image",
        "name",
        "price",
        "badge",
        "discount_percentage",
        "is_featured",
        "rating",
        "countInStock",
    ]
    list_editable = ["price"]
    inlines = [ImageAlbumAdmin]
    extra = 5


admin.site.register(Product, ProductAdmin)

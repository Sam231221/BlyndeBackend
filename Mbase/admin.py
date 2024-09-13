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
    (Category, DiscountOffers,Size, Color, Genre, Order, OrderItem, Review, ShippingAddress)
)


class ImageAlbumAdmin(admin.TabularInline):
    model = ImageAlbum


class ProductAdmin(admin.ModelAdmin):
    list_display = ["image", "name","price", "is_featured", "rating", "countInStock"]
    list_editable = ["price"]
    inlines = [ImageAlbumAdmin]
    extra = 5


admin.site.register(Product, ProductAdmin)

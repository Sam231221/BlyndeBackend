from django.contrib import admin
from .models import (
    Category,
    Color,
    ImageAlbum,
    Genre,
    Product,
    Order,
    OrderItem,
    Review,
    ShippingAddress,
)

admin.site.register((Category, Color, Genre, Order, OrderItem, Review, ShippingAddress))


class ImageAlbumAdmin(admin.TabularInline):
    model = ImageAlbum


class ProductAdmin(admin.ModelAdmin):
    list_display = ["image", "name", "price", "is_featured", "rating", "countInStock"]
    list_editable = ["price"]
    inlines = [ImageAlbumAdmin]
    extra = 5


admin.site.register(Product, ProductAdmin)

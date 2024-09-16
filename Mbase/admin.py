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
    (Category, DiscountOffers,Size, Color, Genre, Order, OrderItem, ShippingAddress)
)


class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating',)
    list_filter = ('rating', )
    search_fields = ('product__name', 'user__username')

admin.site.register(Review, ReviewAdmin)    
class ImageAlbumAdmin(admin.TabularInline):
    model = ImageAlbum


class ProductAdmin(admin.ModelAdmin):
    list_display = ["image", "name","price", "badge","discount_percentage","is_featured", "rating", "countInStock"]
    list_editable = ["price"]
    inlines = [ImageAlbumAdmin]
    extra = 5


admin.site.register(Product, ProductAdmin)

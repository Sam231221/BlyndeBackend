from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model

User = get_user_model()
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
from .forms import GenreAdminForm, UserAdminForm
from .mixins.imagekit import ImageKitMixin

admin.site.register(
    (Category, DiscountOffers, Size, Color, Order, OrderItem, ShippingAddress)
)


class CustomUserAdmin(UserAdmin, ImageKitMixin):
    form = UserAdminForm
    list_display = (
        "email",
        "first_name",
        "last_name",
        "email_verified",
        "agreed_to_terms",
    )
    list_filter = ("email_verified", "agreed_to_terms")
    search_fields = ("username", "email")

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Personal Info",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "image_preview",
                    "image",
                    "remove_image",
                    "email",
                    "profile_pic_id",
                    "profile_pic_url",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important Dates", {"fields": ("last_login", "date_joined")}),
        ("Verification and Terms", {"fields": ("email_verified", "agreed_to_terms")}),
    )

    readonly_fields = ("image_preview",)

    def save_model(self, request, obj, form, change):
        if form.cleaned_data.get("remove_image"):
            if obj.profile_pic_id:
                self._delete_imagekit_file(obj.profile_pic_id)
                obj.profile_pic_id = ""
                obj.profile_pic_url = ""

        new_image = form.cleaned_data.get("image")
        if new_image:
            if change and obj.profile_pic_id:
                self._delete_imagekit_file(obj.profile_pic_id)

            upload_response = self._upload_to_imagekit(new_image, "/Blynde/Users/")
            obj.profile_pic_id = upload_response.file_id
            obj.profile_pic_url = upload_response.url

        super().save_model(request, obj, form, change)


admin.site.register(User, CustomUserAdmin)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin, ImageKitMixin):
    form = GenreAdminForm
    list_display = ("name", "image_preview")
    readonly_fields = ("image_preview", "image_url")
    fields = ("name", "image_preview", "image", "remove_image", "image_url")

    def save_model(self, request, obj, form, change):
        if form.cleaned_data.get("remove_image"):
            if obj.image_file_id:
                self._delete_imagekit_file(obj.image_file_id)
                obj.image_file_id = ""
                obj.image_url = ""

        new_image = form.cleaned_data.get("image")
        if new_image:
            if change and obj.image_file_id:
                self._delete_imagekit_file(obj.image_file_id)

            upload_response = self._upload_to_imagekit(new_image, "/Blynde/Products/")
            obj.image_file_id = upload_response.file_id
            obj.image_url = upload_response.url

        super().save_model(request, obj, form, change)


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

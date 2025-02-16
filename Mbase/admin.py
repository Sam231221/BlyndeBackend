from django.contrib import admin
from django.conf import settings
import imagekitio
import base64
from .forms import GenreAdminForm
from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions

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
    Genre,
)


admin.site.register(
    (Category, DiscountOffers, Size, Color, Order, OrderItem, ShippingAddress)
)

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model

User = get_user_model()


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    form = GenreAdminForm
    list_display = ("name", "image_preview")
    readonly_fields = ("image_preview", "image_url")
    fields = ("name", "image_preview", "image", "remove_image", "image_url")

    def save_model(self, request, obj, form, change):
        # Delete existing image if "remove_image" is checked
        if form.cleaned_data.get("remove_image"):
            if obj.image_file_id:
                self._delete_imagekit_file(obj.image_file_id)
                obj.image_file_id = ""
                obj.image_url = ""

        # Handle new image upload
        new_image = form.cleaned_data.get("image")
        if new_image:
            # Delete old image if it exists
            if change and obj.image_file_id:
                self._delete_imagekit_file(obj.image_file_id)

            # Upload new image to ImageKit
            upload_response = self._upload_to_imagekit(new_image)
            obj.image_file_id = upload_response.file_id
            obj.image_url = upload_response.url

        super().save_model(request, obj, form, change)

    def _upload_to_imagekit(self, image_file):
        imagekit = imagekitio.ImageKit(
            private_key=settings.IMAGEKIT["PRIVATE_KEY"],
            public_key=settings.IMAGEKIT["PUBLIC_KEY"],
            url_endpoint=settings.IMAGEKIT["URL_ENDPOINT"],
        )
        file_binary = image_file.read()
        # Encode the binary data to Base64
        file_base64 = base64.b64encode(file_binary).decode("utf-8")
        response = imagekit.upload_file(
            file=file_base64,
            file_name=image_file.name,
            options=UploadFileRequestOptions(
                use_unique_file_name=False,
                folder="/Blynde/Products/",
            ),
        )

        return response

    def _delete_imagekit_file(self, file_id):
        imagekit = imagekitio.ImageKit(
            private_key=settings.IMAGEKIT["PRIVATE_KEY"],
            public_key=settings.IMAGEKIT["PUBLIC_KEY"],
            url_endpoint=settings.IMAGEKIT["URL_ENDPOINT"],
        )
        try:
            imagekit.delete_file(file_id)
        except Exception as e:
            # Log errors here (e.g., using logging module)
            pass


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

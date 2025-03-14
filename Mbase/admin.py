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
    Wishlist,
    Discount,
    Coupon,
    ContentType,
)
from .forms import (
    GenreAdminForm,
    UserAdminForm,
    DiscountOfferAdminForm,
    ProductAdminForm,
    ImageAlbumAdminForm,
)
from .mixins.imagekit import ImageKitMixin

admin.site.register(
    (
        Category,
        ContentType,
        Wishlist,
        Size,
        Color,
        Order,
        OrderItem,
        ShippingAddress,
    )
)


@admin.register(User)
class BlyndeUserAdmin(UserAdmin, ImageKitMixin):
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


@admin.register(ImageAlbum)
class ImageAlbumAdmin(admin.ModelAdmin, ImageKitMixin):
    form = ImageAlbumAdminForm
    list_display = ("id", "image_preview", "product")
    readonly_fields = ("image_preview",)
    fields = ("image_preview", "image", "remove_image", "product")

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

            upload_response = self._upload_to_imagekit(
                new_image, f"/Blynde/Products/Pd-{obj.product._id}/ImageAlbums/"
            )
            obj.image_file_id = upload_response.file_id
            obj.image_url = upload_response.url

        super().save_model(request, obj, form, change)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin, ImageKitMixin):
    form = ProductAdminForm
    list_display = [
        "thumbnail_preview",
        "name",
        "price",
        "badge",
        "rating",
        "countInStock",
    ]
    # mark it to be shown properly in the admin panel, otherwise error
    readonly_fields = ("thumbnail_preview",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "thumbnail",
                    "thumbnail_preview",
                    "remove_thumbnail",
                )
            },
        ),
        (
            "Categorization",
            {
                "fields": (
                    "brand",
                    "categories",
                    "colors",
                    "sizes",
                    "badge",
                )
            },
        ),
        ("Pricing", {"fields": ("price", "countInStock")}),
        ("Other Details", {"fields": ("likes",)}),
    )
    list_editable = ["price"]

    def save_model(self, request, obj, form, change):
        if form.cleaned_data.get("remove_thumbnail"):
            if obj.thumbnail_file_id:
                self._delete_imagekit_file(obj.thumbnail_file_id)
                obj.thumbnail_file_id = ""
                obj.thumbnail_url = ""
        new_image = form.cleaned_data.get("thumbnail")
        if new_image:
            if change and obj.thumbnail_file_id:
                self._delete_imagekit_file(obj.thumbnail_file_id)
            upload_response = self._upload_to_imagekit(
                new_image, f"/Blynde/Products/Pd-{obj._id}/"
            )
            obj.thumbnail_file_id = upload_response.file_id
            obj.thumbnail_url = upload_response.url

        super().save_model(request, obj, form, change)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "comment",
        "product",
        "user",
        "rating",
    )
    list_filter = ("rating",)
    search_fields = ("product__name", "user__username")


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = (
        "discount_type",
        "object_id",
        "priority",
        "content_type",
        "is_global",
        "start_date",
        "end_date",
    )
    search_fields = ("discount_type", "start_date", "end_date")


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "discount",
        "max_uses",
        "is_active",
        "valid_from",
        "valid_to",
    )
    search_fields = ("code", "discount__discount_type", "valid_from", "valid_to")


@admin.register(DiscountOffers)
class DiscountOfferAdmin(admin.ModelAdmin, ImageKitMixin):
    form = DiscountOfferAdminForm
    list_display = ("name", "thumbnail_preview")
    readonly_fields = ("thumbnail_preview",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "thumbnail",
                    "thumbnail_preview",
                    "remove_thumbnail",
                    "description",
                )
            },
        ),
        (
            "Duration",
            {
                "fields": (
                    "start_date",
                    "end_date",
                )
            },
        ),
        ("Pricing", {"fields": ("price", "on_sale", "countInStock")}),
    )

    def save_model(self, request, obj, form, change):
        if form.cleaned_data.get("remove_thumbnail"):
            if obj.thumbnail_id:
                self._delete_imagekit_file(obj.thumbnail_id)
                obj.thumbnail_id = ""
                obj.thumbnail_url = ""

        new_image = form.cleaned_data.get("thumbnail")
        if new_image:
            if change and obj.thumbnail_id:
                self._delete_imagekit_file(obj.thumbnail_id)

            upload_response = self._upload_to_imagekit(
                new_image, "/Blynde/DiscountOffers/"
            )
            obj.thumbnail_id = upload_response.file_id
            obj.thumbnail_url = upload_response.url

        super().save_model(request, obj, form, change)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin, ImageKitMixin):
    form = GenreAdminForm
    list_display = ("name", "image_preview")
    readonly_fields = ("image_preview",)
    fields = ("name", "image_preview", "image", "remove_image")

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

            upload_response = self._upload_to_imagekit(new_image, "/Blynde/Genres/")
            obj.image_file_id = upload_response.file_id
            obj.image_url = upload_response.url

        super().save_model(request, obj, form, change)

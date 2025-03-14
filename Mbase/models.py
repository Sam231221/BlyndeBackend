import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
from django.utils.html import mark_safe
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from django.db.models import Q, F


class User(AbstractUser):
    profile_pic_id = models.CharField(null=True, max_length=255, blank=True)
    email_verified = models.BooleanField(default=False)
    profile_pic_url = models.URLField(null=True, blank=True)
    agreed_to_terms = models.BooleanField(default=False)

    def __str__(self):
        return str(self.username)

    def image_preview(self):
        if self.profile_pic_url:
            return mark_safe(
                f'<img style="object-fit:contain;" width="120" height="80" src="{self.profile_pic_url}" />'
            )
        return "No Image"


class Size(models.Model):
    _id = models.AutoField(primary_key=True, editable=False)
    name = models.CharField(max_length=50, unique=True, null=True)
    slug = models.SlugField(null=True, unique=True, editable=False)
    description = models.CharField(max_length=200, null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Size, self).save(*args, **kwargs)


class Color(models.Model):
    _id = models.AutoField(primary_key=True, editable=False)
    name = models.CharField(max_length=50, unique=True, null=True)
    slug = models.SlugField(null=True, unique=True, editable=False)
    hex_code = models.CharField(
        max_length=7, help_text="Hex color code, e.g., #FFFFFF for white"
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Color, self).save(*args, **kwargs)


class Category(models.Model):
    _id = models.AutoField(primary_key=True, editable=False)
    name = models.CharField(max_length=50, null=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )
    slug = models.SlugField(null=True, unique=True, blank=True)

    def __str__(self):
        if self.parent:
            return f"{self.name} -> {self.parent}"
        return str(self.name)

    def get_full_path(self):
        if self.parent:
            return f"{self.parent.get_full_path()} > {self.name}"
        return self.name

    def save(self, *args, **kwargs):
        if self.parent:

            self.slug = slugify(f"{self.name}-{self.parent.slug}")
        else:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"


class Genre(models.Model):
    _id = models.AutoField(primary_key=True, editable=False)
    image_file_id = models.CharField(null=True, max_length=255, blank=True)
    image_url = models.URLField(null=True, blank=True)
    name = models.CharField(max_length=50, unique=True, null=True)
    slug = models.SlugField(null=True, unique=True, editable=False)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return str(self.name)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Genre, self).save(*args, **kwargs)

    def image_preview(self):
        if self.image_url:
            return mark_safe(
                f'<img src="{self.image_url}" style="object-fit:contain;" width="120" height="80" />'
            )
        return "No Image"


class Product(models.Model):
    _id = models.AutoField(primary_key=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    slug = models.SlugField(max_length=255, blank=True)
    name = models.CharField(max_length=200, null=True)
    thumbnail_file_id = models.CharField(null=True, max_length=255, blank=True)
    thumbnail_url = models.URLField(null=True, blank=True)
    brand = models.CharField(max_length=200, null=True, blank=True)
    colors = models.ManyToManyField(Color)
    sizes = models.ManyToManyField(Size)
    categories = models.ManyToManyField(Category, related_name="categories")
    description = models.TextField(null=True, blank=True)
    rating = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, editable=False
    )
    price = models.DecimalField(
        max_digits=7,
        validators=[MinValueValidator(Decimal("0.01"))],
        decimal_places=2,
        null=True,
        blank=True,
    )
    countInStock = models.IntegerField(null=True, blank=True, default=0)
    createdAt = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, related_name="likes", blank=True)
    badge = models.CharField(
        max_length=20,
        choices=[
            ("Featured", "Featured"),
            ("Trending", "Trending"),
            ("Exclusive", "Exclusive"),
            ("Limited Edition", "Limited Edition"),
        ],
        null=True,
        blank=True,
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(Product, self).save(*args, **kwargs)

    def update_rating(self):
        avg_rating = self.reviews.aggregate(avg_rating=models.Avg("rating"))[
            "avg_rating"
        ]
        self.rating = avg_rating if avg_rating is not None else None
        self.save()

    def thumbnail_preview(self):
        if self.thumbnail_url:
            return mark_safe(
                f'<img style="object-fit:contain;"  width="120" height="80" src="{self.thumbnail_url}"/>'
            )
        return "No Image"

    def get_discounted_price(self, coupon_code=None):
        now = timezone.now()
        content_type_product = ContentType.objects.get_for_model(Product)
        content_type_category = ContentType.objects.get_for_model(Category)
        # Gather discounts from three sources:
        discounts = Discount.objects.filter(
            Q(
                content_type=content_type_product,
                object_id=self._id,
                start_date__lte=now,
                end_date__gte=now,
            )
            | Q(
                content_type=content_type_category,
                object_id__in=self.categories.values_list("_id", flat=True),
                start_date__lte=now,
                end_date__gte=now,
            )
            | Q(is_global=True, start_date__lte=now, end_date__gte=now)
        ).order_by("-priority")

        best_price = self.price

        for discount in discounts:
            if discount.discount_type == "percentage":

                if discount.amount < 5:
                    raise ValidationError("Percentage discount must be at least 5%.")
                computed_price = self.price * (1 - discount.amount / 100)
            else:
                computed_percentage = (discount.amount / self.price) * 100
                if computed_percentage < 5:
                    raise ValidationError(
                        "Fixed discount must be at least 5% of the product price."
                    )
                computed_price = self.price - discount.amount

            best_price = computed_price

            break

        if coupon_code:
            try:
                coupon = Coupon.objects.get(
                    code=coupon_code,
                    is_active=True,
                    valid_from__lte=now,
                    valid_to__gte=now,
                    used__lt=F("max_uses"),
                )
                if coupon.coupon_scope == "product":
                    coupon_discount = coupon.discount
                    if coupon_discount.discount_type == "percentage":
                        if coupon_discount.amount < 5:
                            raise ValidationError(
                                "Coupon percentage discount must be at least 5%."
                            )
                        best_price *= 1 - coupon_discount.amount / 100
                    else:
                        coupon_computed_percentage = (
                            coupon_discount.amount / self.price
                        ) * 100
                        if coupon_computed_percentage < 5:
                            raise ValidationError(
                                "Coupon fixed discount must be at least 5% of the product price."
                            )
                        best_price -= coupon_discount.amount
            except Coupon.DoesNotExist:
                pass

        return max(best_price, Decimal("0.00")).quantize(Decimal("0.01"))

    def get_discount_percentage(self, coupon_code=None):
        discounted_price = self.get_discounted_price(coupon_code=coupon_code)
        if self.price and self.price > discounted_price:
            discount = (self.price - discounted_price) / self.price * Decimal("100")
            return discount.quantize(Decimal("0.01"))
        return Decimal("0.00")

    @property
    def on_sale(self):
        return self.get_discount_percentage() > Decimal("0.00")

    def __str__(self):
        return f"{self.name}"


class Discount(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ("percentage", "Percentage"),
        ("fixed", "Fixed"),
    ]

    description = models.CharField(
        max_length=200, editable=False, null=True, blank=True
    )
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, null=True, blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES)
    amount = models.DecimalField(
        max_digits=5, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    priority = models.PositiveSmallIntegerField(default=0)
    is_global = models.BooleanField(default=False)

    class Meta:
        ordering = ["-priority"]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["start_date", "end_date"]),
        ]

    def generate_description(self):
        if self.is_global:
            target = "All Products"
        else:
            target = (
                str(self.content_object) if self.content_object else "Specific Product"
            )

        if self.discount_type == "fixed":
            discount_value = f"${self.amount}"
        else:
            discount_value = f"{self.amount}%"

        return f"{discount_value} discount on {target}"

    def save(self, *args, **kwargs):
        if not self.description:
            self.description = self.generate_description()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.description or self.generate_description()

    def clean(self):
        if self.is_global and (self.content_type or self.object_id):
            raise ValidationError(
                "Global discounts should not have a specific content_type or object_id set."
            )
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError("End date must be after start date")
        if self.discount_type == "percentage" and self.amount < 5:
            raise ValidationError("Percentage discount amount must be at least 5%.")


class Order(models.Model):
    _id = models.AutoField(primary_key=True, editable=False)
    order_number = models.CharField(
        max_length=20, unique=True, null=True, editable=False, db_index=True
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    paymentMethod = models.CharField(max_length=200, null=True, blank=True)
    itemsPrice = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, blank=True
    )
    taxPrice = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, blank=True
    )
    shippingPrice = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, blank=True
    )
    totalPrice = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ("Pending", "Pending"),
            ("Paid", "Paid"),
            ("Shipped", "Shipped"),
            ("Delivered", "Delivered"),
        ],
        default="Pending",
    )
    isPaid = models.BooleanField(default=False)
    paidAt = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    isDelivered = models.BooleanField(default=False)
    deliveredAt = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    createdAt = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    def generate_order_number(self):
        return f"ORD-{uuid.uuid4().hex[:10].upper()}"

    def __str__(self):
        return self.order_number


class OrderItem(models.Model):
    _id = models.AutoField(primary_key=True, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="order_items", null=True
    )
    name = models.CharField(max_length=200, null=True, blank=True)
    color = models.CharField(max_length=200, null=True, blank=True)
    size = models.CharField(max_length=200, null=True, blank=True)
    qty = models.IntegerField(null=True, blank=True, default=0)
    price = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    thumbnail = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return f"{self.name}, Color:{self.color}, Size:{self.size}, Qty:{self.qty} for order {self.order.order_number}"


class ShippingAddress(models.Model):
    _id = models.AutoField(primary_key=True, editable=False)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, null=True, blank=True)
    address = models.CharField(max_length=200, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    postalCode = models.CharField(max_length=200, null=True, blank=True)
    country = models.CharField(max_length=200, null=True, blank=True)
    shippingPrice = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, blank=True
    )

    def __str__(self):
        return f"{self.address}, {self.city}, {self.country} for order {self.order._id} by {self.order.user}"


class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True, null=True)
    discount = models.ForeignKey(Discount, on_delete=models.CASCADE, null=True)
    max_uses = models.PositiveIntegerField(default=1)
    used = models.PositiveIntegerField(default=0)
    valid_from = models.DateTimeField(null=True)
    valid_to = models.DateTimeField(null=True)
    is_active = models.BooleanField(default=True)
    COUPON_SCOPE_CHOICES = [
        ("product", "Product"),
        ("order", "Order"),
    ]
    coupon_scope = models.CharField(
        max_length=10, choices=COUPON_SCOPE_CHOICES, default="product"
    )

    def __str__(self):
        return f"{self.code}"

    def is_valid(self):
        now = timezone.now()
        return (
            self.is_active
            and self.used < self.max_uses
            and self.valid_from <= now <= self.valid_to
        )

    def use_coupon(self):
        if self.is_valid():
            self.used = F("used") + 1
            self.save(update_fields=["used"])
            return True
        return False


class FlashSale(models.Model):
    DISCOUNT_PERCENT = "percent"
    DISCOUNT_FIXED = "fixed"
    DISCOUNT_TYPES = (
        (DISCOUNT_PERCENT, "Percentage"),
        (DISCOUNT_FIXED, "Fixed Amount"),
    )

    name = models.CharField(max_length=255)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    products = models.ManyToManyField(Product, blank=True)
    max_usage = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["start_time", "end_time"]),
        ]

    def clean(self):
        if self.end_time <= self.start_time:
            raise ValidationError("End time must be after start time.")

        if self.discount_type == self.DISCOUNT_PERCENT and self.discount_value > 100:
            raise ValidationError("Percentage discount cannot exceed 100%.")

    @property
    def status(self):
        now = timezone.now()
        return "Active" if self.start_time <= now <= self.end_time else "Inactive"

    def __str__(self):
        return f"{self.name} ({self.status})"


class GiftCard(models.Model):
    code = models.CharField(max_length=50, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="gift_cards")
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def use(self, amount):
        if self.is_active and self.balance >= amount:
            self.balance -= amount
            self.save()
            return True
        return False


class ImageAlbum(models.Model):
    image_file_id = models.CharField(null=True, unique=True, max_length=255, blank=True)
    image_url = models.URLField(null=True, blank=True)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        help_text="Select the product you want to associate this image with.",
        null=True,
        verbose_name="Associated to",
    )

    def __str__(self):
        return f"{self.image_url}"

    def image_preview(self):
        if self.image_url:
            return mark_safe(f'<img src="{self.image_url}" width="80"/>')
        return "No Image"

    class Meta:
        ordering = ["-id"]


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")
        ordering = ["-added_at"]

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


class Review(models.Model):
    _id = models.AutoField(primary_key=True, editable=False)
    product = models.ForeignKey(
        Product, related_name="reviews", on_delete=models.SET_NULL, null=True
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    rating = models.DecimalField(max_digits=7, decimal_places=2, null=True)
    comment = models.TextField(null=True, blank=True)
    createdAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment on {self.user.first_name} {self.user.last_name}."


class DiscountOffers(models.Model):
    _id = models.AutoField(primary_key=True, editable=False)
    name = models.CharField(max_length=200, null=True, blank=True)
    thumbnail_id = models.CharField(null=True, max_length=255, blank=True)
    thumbnail_url = models.URLField(null=True, blank=True)
    price = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    on_sale = models.BooleanField(default=False)
    sale_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    countInStock = models.IntegerField(null=True, blank=True, default=0)
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)

    def __str__(self):
        return self.name

    def thumbnail_preview(self):
        if self.thumbnail_url:
            return mark_safe(
                f'<img src="{self.thumbnail_url}" style="object-fit:contain;" width="120" height="80" />'
            )
        return "No Image"

import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
from django.utils.html import mark_safe


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
            # Use parent's SLUG instead of NAME
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
    name = models.CharField(max_length=200, null=True, blank=True)
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
    review_count = models.PositiveIntegerField(default=0, editable=False)
    price = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    sale_price = models.DecimalField(
        max_digits=10, editable=False, decimal_places=2, null=True, blank=True
    )
    discount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    countInStock = models.IntegerField(null=True, blank=True, default=0)
    createdAt = models.DateTimeField(auto_now_add=True)

    likes = models.ManyToManyField(User, related_name="likes", default=None, blank=True)
    badge = models.CharField(
        max_length=20,
        choices=[
            ("Featured", "Featured"),
            ("Top Rated", "Top Rated"),
            ("In Sale", "In Sale"),
        ],
        null=True,
        blank=True,
    )

    def save(self, *args, **kwargs):
        if self.discount_percentage and not self.sale_price:
            self.sale_price = self.price - (
                self.price * (self.discount_percentage / 100)
            )
        super().save(*args, **kwargs)
        if not self.slug:
            self.slug = slugify(self.name)
        super(Product, self).save(*args, **kwargs)

    def update_review_count(self):
        self.review_count = self.reviews.count()
        self.save()

    def update_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            self.rating = reviews.aggregate(models.Avg("rating"))["rating__avg"]
        else:
            self.rating = None
        self.save()

    def thumbnail_preview(self):
        if self.thumbnail_url:
            return mark_safe(
                f'<img style="object-fit:contain;"  width="120" height="80" src="{self.thumbnail_url}"/>'
            )
        return "No Image"

    @property
    def effective_price(self):
        return self.sale_price if self.on_sale and self.sale_price else self.price

    def __str__(self):
        return f"{self.name}"


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


class Review(models.Model):
    _id = models.AutoField(primary_key=True, editable=False)
    product = models.ForeignKey(
        Product, related_name="reviews", on_delete=models.SET_NULL, null=True
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    rating = models.DecimalField(max_digits=7, decimal_places=2, null=True)
    comment = models.TextField(null=True, blank=True)
    createdAt = models.DateTimeField(auto_now_add=True)

    # def __str__(self):
    #     return f"Comment on {self.user.first_name} {self.user.last_name}."


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
        return str(self.name)


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


class Discount(models.Model):
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed"
    FREE_SHIPPING = "free_shipping"

    DISCOUNT_TYPES = [
        (PERCENTAGE, "Percentage"),
        (FIXED_AMOUNT, "Fixed Amount"),
        (FREE_SHIPPING, "Free Shipping"),
    ]

    name = models.CharField(max_length=255, unique=True)  # e.g., "Black Friday Sale"
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES)
    value = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Percentage or fixed discount value"
    )
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    applies_to_all_products = models.BooleanField(
        default=False
    )  # If True, applies to all products
    min_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Min order value required",
    )

    max_redemptions = models.PositiveIntegerField(
        null=True, blank=True, help_text="Max times this discount can be used"
    )
    current_redemptions = models.PositiveIntegerField(default=0)

    stackable = models.BooleanField(
        default=False, help_text="Can this discount be combined with others?"
    )
    priority = models.PositiveIntegerField(
        default=1, help_text="Higher priority discounts are applied first"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True  # This will be inherited by Coupons, Sales, and Vouchers

    def __str__(self):
        return f"{self.name} ({self.discount_type} - {self.value})"


class Coupon(Discount):
    code = models.CharField(
        max_length=50, unique=True, help_text="Enter coupon code (e.g., SAVE10)"
    )
    user = models.ManyToManyField(User, blank=True, related_name="coupons_used")
    one_time_use = models.BooleanField(
        default=False, help_text="Can be used only once per user"
    )

    def is_valid(self):
        return self.is_active and (
            self.max_redemptions is None
            or self.current_redemptions < self.max_redemptions
        )


class DiscountOffers(models.Model):
    _id = models.AutoField(primary_key=True, editable=False)
    name = models.CharField(max_length=200, null=True, blank=True)
    thumbnail = models.ImageField(null=True)
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

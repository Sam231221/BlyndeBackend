from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils.html import mark_safe
from django.db import models


class Size(models.Model):
    _id = models.AutoField(primary_key=True, editable=False)
    name = models.CharField(max_length=50, null=True)
    description = models.CharField(max_length=200, null=True)

    def __str__(self):
        return self.name


class Color(models.Model):
    _id = models.AutoField(primary_key=True, editable=False)
    name = models.CharField(max_length=50)
    hex_code = models.CharField(
        max_length=7, help_text="Hex color code, e.g., #FFFFFF for white"
    )

    def __str__(self):
        return self.name


class Category(models.Model):
    _id = models.AutoField(primary_key=True, editable=False)
    name = models.CharField(max_length=50, null=True)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children"
    )
    slug = models.SlugField(null=True, editable=False)

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
            self.slug = slugify(str(self.name) + "-" + str(self.parent))
        else:
            self.slug = slugify(str(self.name))
        super(Category, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"


class Genre(models.Model):
    _id = models.AutoField(primary_key=True, editable=False)
    name = models.CharField(max_length=50, null=True)
    slug = models.SlugField(null=True, editable=False)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return str(self.name)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Genre, self).save(*args, **kwargs)


class Product(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=200, null=True, blank=True)
    thumbnail = models.ImageField(null=True, blank=True, default="/placeholder.png")
    brand = models.CharField(max_length=200, null=True, blank=True)
    colors = models.ManyToManyField(Color)
    size = models.ManyToManyField(Size)
    categories = models.ManyToManyField(Category, related_name="products")
    description = models.TextField(null=True, blank=True)
    rating = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    review_count = models.PositiveIntegerField(default=0, editable=False)
    # Price Things#
    price = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    sale_price = models.DecimalField(
        max_digits=10, editable=False, decimal_places=2, null=True, blank=True
    )
    discount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    countInStock = models.IntegerField(null=True, blank=True, default=0)
    createdAt = models.DateTimeField(auto_now_add=True)
    _id = models.AutoField(primary_key=True, editable=False)
    is_featured = models.BooleanField(default=False)
    likes = models.ManyToManyField(User, related_name="likes", default=None, blank=True)
    badge = models.CharField(
        max_length=20,
        choices=[
            ("Featured", "Featured"),
            ("Top Rated", "Top Rated"),
            ("Sale", "Sale"),
        ],
        null=True,
        blank=True,
    )

    def update_review_count(self):
        self.review_count = self.reviews.count()
        self.save()

    def update_rating(self):
        # Calculate the average rating from related reviews
        reviews = self.reviews.all()
        if reviews.exists():
            self.rating = reviews.aggregate(models.Avg("rating"))["rating__avg"]
        else:
            self.rating = None
        self.save()

    def save(self, *args, **kwargs):
        # Automatically calculate sale_price based on discount_percentage
        if self.discount_percentage and not self.sale_price:
            self.sale_price = self.price - (
                self.price * (self.discount_percentage / 100)
            )
        super().save(*args, **kwargs)

    def image(self):
        return mark_safe(
            '<img style="object-fit:contain;" src="%s" width="50" height="50" />'
            % (self.thumbnail.url)
        )

    @property
    def effective_price(self):
        return self.sale_price if self.on_sale and self.sale_price else self.price

    def __str__(self):
        return f"{self.name}"


from django.db.models.signals import post_save
from django.dispatch import receiver


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

    # make correction
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)  # Make end_date nullable

    def __str__(self):
        return self.name


class ImageAlbum(models.Model):
    image = models.ImageField(null=True)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        help_text="Provide a url of image",
        null=True,
        verbose_name="images",
    )


class Review(models.Model):
    product = models.ForeignKey(
        Product, related_name="reviews", on_delete=models.SET_NULL, null=True
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=200, null=True, blank=True)
    rating = models.DecimalField(max_digits=7, decimal_places=2, null=True)
    comment = models.TextField(null=True, blank=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    _id = models.AutoField(primary_key=True, editable=False)

    def __str__(self):
        return f"Comment on {self.product.name} by {self.name}."


@receiver(post_save, sender=Review)
def update_product_rating(sender, instance, **kwargs):
    instance.product.update_review_count()
    instance.product.update_rating()


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    paymentMethod = models.CharField(max_length=200, null=True, blank=True)
    taxPrice = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, blank=True
    )
    shippingPrice = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, blank=True
    )
    totalPrice = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, blank=True
    )
    isPaid = models.BooleanField(default=False)
    paidAt = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    isDelivered = models.BooleanField(default=False)
    deliveredAt = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    _id = models.AutoField(primary_key=True, editable=False)

    def __str__(self):
        return str(self.createdAt)


class OrderItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=200, null=True, blank=True)
    color = models.CharField(max_length=200, null=True, blank=True)
    size = models.CharField(max_length=200, null=True, blank=True)
    qty = models.IntegerField(null=True, blank=True, default=0)
    price = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    thumbnail = models.CharField(max_length=200, null=True, blank=True)
    _id = models.AutoField(primary_key=True, editable=False)

    def __str__(self):
        return str(self.name)


class ShippingAddress(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, null=True, blank=True)
    address = models.CharField(max_length=200, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    postalCode = models.CharField(max_length=200, null=True, blank=True)
    country = models.CharField(max_length=200, null=True, blank=True)
    shippingPrice = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, blank=True
    )
    _id = models.AutoField(primary_key=True, editable=False)

    def __str__(self):
        return str(self.address)

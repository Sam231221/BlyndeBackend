from django_filters import rest_framework as filters
import django_filters
from .models import Product, Category, Color, Size


class ProductFilter(django_filters.FilterSet):
    categories = django_filters.ModelMultipleChoiceFilter(
        queryset=Category.objects.all(), field_name="categories"
    )
    colors = django_filters.ModelChoiceFilter(queryset=Color.objects.all())
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    sizes = django_filters.ModelMultipleChoiceFilter(
        queryset=Size.objects.all(), field_name="size"
    )

    class Meta:
        model = Product
        fields = ["categories", "colors", "min_price", "max_price", "sizes"]

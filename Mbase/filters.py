import django_filters
from .models import Product, Category


class ProductFilter(django_filters.FilterSet):
    categories = django_filters.CharFilter(
        method="filter_by_category_slug",
        label="Filter by category slugs (comma-separated)",
    )
    color = django_filters.CharFilter(field_name="colors__name", lookup_expr="iexact")
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    badge = django_filters.CharFilter(field_name="badge", lookup_expr="iexact")
    sizes = django_filters.CharFilter(
        method="filter_by_sizes_names", label="Filter by sizes names (comma-separated)"
    )
    rating = django_filters.NumberFilter(field_name="rating", lookup_expr="gte")

    class Meta:
        model = Product
        fields = ["categories", "badge", "colors", "min_price", "max_price", "sizes"]

    def filter_by_category_slug(self, queryset, name, value):
        slugs = [slug.strip() for slug in value.split(",")]
        categories = Category.objects.filter(slug__in=slugs)
        valid_slugs = set()

        for category in categories:
            valid_slugs.add(category.slug)
            valid_slugs.update(category.children.all().values_list("slug", flat=True))

        return queryset.filter(categories__slug__in=valid_slugs).distinct()

    def filter_by_sizes_names(self, queryset, name, value):
        sizes_names = [name.strip().lower() for name in value.split(",")]
        return queryset.filter(
            sizes__name__iregex=r"(" + "|".join(sizes_names) + ")"
        ).distinct()

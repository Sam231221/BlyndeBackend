from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from Mbase.models import (
    Product,
    Size,
    User,
    Review,
    Color,
    Category,
    ImageAlbum,
    DiscountOffers,
)
from Mbase.serializers import (
    CategorySerializer,
    SizeSerializer,
    DiscountOffersSerializer,
    ImageAlbumSerializer,
    ColorSerializer,
    ReviewSerializer,
    ProductSerializer,
    ProductCreateUpdateSerializer,
)
from Mbase.filters import ProductFilter
from Mbase.pagination import ProductPagination


class DiscountOffersView(APIView):
    def get(self, request, format=None):
        discounts = DiscountOffers.objects.all()
        serializer = DiscountOffersSerializer(discounts, many=True)
        return Response(serializer.data)


class DiscountOfferDeleteView(APIView):
    """
    API endpoint to delete a discount offer by ID.
    """

    def delete(self, request, pk):
        try:
            offer = get_object_or_404(DiscountOffers, pk=pk)
            offer.delete()
            return Response(
                {"detail": "Discount offer deleted Successfully!."},
                status=status.HTTP_200_OK,
            )
        except DiscountOffers.DoesNotExist:
            return JsonResponse(
                {"error": "Discount offer not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return JsonResponse(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CategoryListView(generics.ListAPIView):
    serializer_class = CategorySerializer

    def get_queryset(self):
        return Category.objects.all().exclude(name__icontains="deals")

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        for category in response.data:
            category_obj = Category.objects.filter(id=category["id"]).first()
            category["genres"] = list(category_obj.genre_set.values())
        return Response(response.data)


class ProductListView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = ProductFilter
    pagination_class = ProductPagination
    search_fields = ["name", "description"]


class SizeListView(APIView):
    def get(self, request):
        sizes = Size.objects.all()
        serializer = SizeSerializer(sizes, many=True)
        return Response(serializer.data)


class ColorListView(generics.ListAPIView):
    serializer_class = ColorSerializer
    queryset = Color.objects.all()


class ProductsView(generics.ListAPIView):
    serializer_class = ProductSerializer
    pagination_class = ProductPagination

    def get_queryset(self):
        query = self.request.query_params.get("keyword", "")
        return (
            Product.objects.filter(name__icontains=query)
            .order_by("-createdAt")
            .prefetch_related(
                "reviews", "colors", "categories", "size", "imagealbum_set"
            )
        )


class TopProductsView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        return (
            Product.objects.filter(rating__gte=5)
            .order_by("-rating")[:5]
            .prefetch_related(
                "reviews", "colors", "categories", "size", "imagealbum_set"
            )
        )


class DealProductsView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        category_obj = Category.objects.filter(name__icontains="deals").first()
        return Product.objects.filter(categories=category_obj)[:6].prefetch_related(
            "reviews", "colors", "categories", "size", "imagealbum_set"
        )


class RelatedProductsAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        product_id = self.kwargs["product_id"]
        product = Product.objects.get(_id=product_id)

        # Logic to determine related products (customize based on your needs)
        related_products = Product.objects.filter(
            # Consider these factors (modify based on your priorities):
            Q(categories__in=product.categories.all())
            | Q(colors__in=product.colors.all()),
            Q(brand=product.brand),
        ).exclude(_id=product_id)

        return related_products.distinct()


class RecentProductsView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        category_obj = Category.objects.filter(name__icontains="deals").first()
        return Product.objects.exclude(categories=category_obj).order_by("-createdAt")[
            :8
        ]

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        for product in response.data:
            product_obj = Product.objects.filter(_id=product["_id"]).first()
            imagealbum_objs = ImageAlbum.objects.filter(product=product_obj)
            product["images"] = ImageAlbumSerializer(imagealbum_objs, many=True).data
        return Response(response.data)


class FeaturedProductsView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        return Product.objects.filter(is_featured=True)[:8]

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        for product in response.data:
            product_obj = Product.objects.filter(_id=product["_id"]).first()
            product["images"] = list(product_obj.imagealbum_set.values())
        return Response(response.data)


class ProductDetailView(generics.RetrieveAPIView):
    serializer_class = ProductSerializer
    queryset = Product.objects.all()
    lookup_field = "pk"


# # Accepts POST method
class CreateProductView(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductCreateUpdateSerializer


# Accepts PUT, PATCH method
class UpdateProductView(generics.UpdateAPIView):
    serializer_class = ProductCreateUpdateSerializer
    permission_classes = [IsAdminUser]
    queryset = Product.objects.all()
    lookup_field = "pk"


# Accepts DELETE method
class DeleteProductView(generics.DestroyAPIView):
    permission_classes = [IsAdminUser]
    queryset = Product.objects.all()
    lookup_field = "pk"

    # default response is 204 content
    # so overriding delete() to show custom response
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"detail": f"Product has been deleted successfully!."},
            status=status.HTTP_200_OK,
        )


class ProductReviewListView(generics.ListAPIView):
    serializer_class = ReviewSerializer

    def get_queryset(self):
        product_id = self.kwargs.get("product_id")
        return Review.objects.filter(product___id=product_id)


class ReviewListCreateView(generics.ListCreateAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """
        Optionally, you can modify this method to customize how the review is fetched (e.g., using the review ID).
        """
        review = get_object_or_404(Review, pk=self.kwargs["pk"])
        return review

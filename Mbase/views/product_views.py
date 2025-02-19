from django.db.models import Q, Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
    IsAdminUser,
)
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.filters import SearchFilter, OrderingFilter


User = get_user_model()

from Mbase.models import (
    Product,
    Size,
    Review,
    Color,
    Category,
    ImageAlbum,
    DiscountOffers,
)
from Mbase.serializers import (
    CategoryWithChildrenSerializer,
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
    serializer_class = CategoryWithChildrenSerializer

    def get_queryset(self):
        return (
            Category.objects.annotate(product_count=Count("categories"))
            .exclude(name__icontains="deals")
            .exclude(name__icontains="packs")
        )


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
                "reviews", "colors", "categories", "sizes", "imagealbum_set"
            )
        )


class TopProductsView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        return (
            Product.objects.filter(rating__gte=5)
            .order_by("-rating")[:5]
            .prefetch_related(
                "reviews", "colors", "categories", "sizes", "imagealbum_set"
            )
        )


class DealProductsView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        category_obj = Category.objects.filter(name__icontains="deals").first()
        return Product.objects.filter(categories=category_obj)[:6].prefetch_related(
            "reviews", "colors", "categories", "sizes", "imagealbum_set"
        )


class RelatedProductsAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        product_slug = self.kwargs["product_slug"]
        product = Product.objects.get(slug=product_slug)
        related_products = Product.objects.filter(
            Q(categories__in=product.categories.all())
            | Q(colors__in=product.colors.all()),
            Q(brand=product.brand),
        ).exclude(slug=product_slug)

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


class ProductListView(generics.ListAPIView):
    queryset = Product.objects.prefetch_related(
        "colors",
        "sizes",
        "categories",
    )
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = ProductFilter
    pagination_class = ProductPagination
    search_fields = ["name", "description"]
    ordering_fields = ["price", "createdAt", "review_count"]


class ProductDetailView(generics.RetrieveAPIView):
    serializer_class = ProductSerializer
    queryset = Product.objects.all()
    lookup_field = "slug"


class CreateProductView(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductCreateUpdateSerializer


class UpdateProductView(generics.UpdateAPIView):
    serializer_class = ProductCreateUpdateSerializer
    permission_classes = [IsAdminUser]
    queryset = Product.objects.all()
    lookup_field = "slug"


class DeleteProductView(generics.DestroyAPIView):
    permission_classes = [IsAdminUser]
    queryset = Product.objects.all()
    lookup_field = "slug"
    """
    Default response is 204 content
    So overriding delete() to show custom response
    """

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
        product_slug = self.kwargs.get("product_slug")
        return Review.objects.filter(product__slug=product_slug)


class ReviewListCreateView(generics.ListCreateAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                product = serializer.validated_data.get("product")

                user = request.user
                review = Review.objects.create(
                    user=user,
                    product=product,
                    rating=serializer.validated_data.get("rating"),
                    comment=serializer.validated_data.get("comment"),
                )

                product.update_review_count()
                product.update_rating()

                return Response(
                    ReviewSerializer(review).data, status=status.HTTP_201_CREATED
                )

            except Exception as e:

                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        else:
            print(serializer.errors)  # Print serializer errors for debugging
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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

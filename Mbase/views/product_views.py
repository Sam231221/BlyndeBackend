from django.db.models import Q, Count
from django.http import JsonResponse

from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
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
from django.utils import timezone

User = get_user_model()

from Mbase.models import (
    Product,
    Size,
    Review,
    Color,
    Category,
    ImageAlbum,
    DiscountOffers,
    Discount,
    Coupon,
    Order,
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
    DiscountSerializer,
)
from Mbase.filters import ProductFilter
from Mbase.pagination import ProductPagination

from django.utils.timezone import now
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class ProductCouponAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request, product_slug):
        product = get_object_or_404(Product, slug=product_slug)
        coupon_code = request.data.get("coupon_code")
        try:
            coupon = Coupon.objects.get(code=coupon_code)
        except Coupon.DoesNotExist:
            return Response(
                {"error": "Invalid coupon   code"}, status=status.HTTP_400_BAD_REQUEST
            )
        now = timezone.now()
        if not (
            coupon.is_active
            and coupon.valid_from <= now <= coupon.valid_to
            and coupon.used < coupon.max_uses
        ):
            return Response(
                {"error": "Coupon expired or invalid"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if coupon.coupon_scope != "product":
            return Response(
                {"error": "Coupon not valid for products"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        discount = coupon.discount
        # Validate discount applicability
        applicable = False
        if discount.is_global:
            applicable = True
        else:
            model_class = discount.content_type.model_class()
            if model_class == Product:
                applicable = product._id == discount.object_id
            elif model_class == Category:
                applicable = product.categories.filter(_id=discount.object_id).exists()

        if not applicable:
            return Response(
                {"error": "Coupon not applicable to this product"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            discounted_price = product.get_discounted_price(coupon_code=coupon_code)
            discount_pct = product.get_discount_percentage(coupon_code=coupon_code)
            return Response(
                {
                    "discounted_price": discounted_price,
                    "discount_percentage": float(discount_pct),
                    "valid": True,
                }
            )
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class HighestPriorityDiscountAPIView(APIView):
    def get(self, request, *args, **kwargs):
        highest_discount = (
            Discount.objects.filter(start_date__lte=now(), end_date__gte=now())
            .order_by("-priority")
            .first()
        )

        if not highest_discount:
            return Response(
                {"errors": {"general": "No active discount found"}},
                status=status.HTTP_200_OK,
            )

        return Response(
            DiscountSerializer(highest_discount).data, status=status.HTTP_200_OK
        )


class DeleteHighestPriorityDiscountAPIView(APIView):
    def delete(self, request, *args, **kwargs):
        highest_discount = (
            Discount.objects.filter(start_date__lte=now(), end_date__gte=now())
            .order_by("-priority")
            .first()
        )

        if not highest_discount:
            return Response(
                {"message": "No active discount found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        highest_discount.delete()
        return Response(
            {"message": "Highest priority discount deleted successfully"},
            status=status.HTTP_200_OK,
        )


class DiscountOffersView(APIView):
    def get(self, request, format=None):
        discounts = DiscountOffers.objects.all()
        serializer = DiscountOffersSerializer(discounts, many=True)
        return Response(serializer.data)


class DiscountOfferDeleteView(APIView):

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
        return related_products.distinct()[:4]


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
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        review = get_object_or_404(Review, pk=self.kwargs["pk"])
        return review

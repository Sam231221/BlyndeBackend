from django.db.models import Q
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

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
from Mbase.serializers import ProductSerializer
from Mbase.serializers import (
    CategorySerializer,
    SizeSerializer,
    DiscountOffersSerializer,
    ImageAlbumSerializer,
    ColorSerializer,
    ReviewSerializer,
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
            return Response(status=status.HTTP_204_NO_CONTENT)
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


class ProductReviewListView(generics.ListAPIView):
    serializer_class = ReviewSerializer

    def get_queryset(self):
        product_id = self.kwargs.get("product_id")
        return Review.objects.filter(product___id=product_id)


class CreateReviewView(generics.CreateAPIView):
    serializer_class = ReviewSerializer

    def create(self, request, *args, **kwargs):
        data = request.data
        product = get_object_or_404(Product, _id=data["productId"])
        user_obj = User.objects.filter(first_name=data["user"]).first()

        review = Review.objects.create(
            product=product,
            user=user_obj,
            name=data["user"],
            rating=data["rating"],
            comment=data["comment"],
        )
        serializer = self.get_serializer(review)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# POST: Create Product (Admin Only)
class CreateProductView(generics.CreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(
            user=user,
            name="Sample Name",
            price=0,
            brand="Sample Brand",
            countInStock=0,
            description="",
        )


# PUT: Update Product (Admin Only)
class UpdateProductView(generics.UpdateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUser]
    queryset = Product.objects.all()
    lookup_field = "_id"

    def perform_update(self, serializer):
        data = self.request.data
        category = Category.objects.filter(name=data["category"]).first()
        serializer.save(
            name=data["name"],
            price=data["price"],
            brand=data["brand"],
            countInStock=data["countInStock"],
            category=category,
            description=data["description"],
        )


# DELETE: Delete Product (Admin Only)
class DeleteProductView(generics.DestroyAPIView):
    permission_classes = [IsAdminUser]
    queryset = Product.objects.all()
    lookup_field = "_id"


# POST: Upload Image
class UploadImageView(generics.GenericAPIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        product_id = data.get("product_id")
        product = get_object_or_404(Product, _id=product_id)

        product.image = request.FILES.get("image")
        product.save()
        return Response("Image was uploaded")

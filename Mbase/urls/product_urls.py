from django.urls import path
from Mbase.views import product_views as views

urlpatterns = [
    path("discountoffers/", views.DiscountOffersView.as_view(), name="discountoffers"),
    path(
        "discountoffers/<int:pk>/delete/",
        views.DiscountOfferDeleteView.as_view(),
        name="delete_discount_offer",
    ),
    path("sizes/", views.SizeListView.as_view(), name="sizes"),
    path("categories/", views.CategoryListView.as_view(), name="categories"),
    path("colors/", views.ColorListView.as_view(), name="colors"),
    # Product list types
    path("", views.ProductsView.as_view(), name="products"),
    path("all/", views.ProductListView.as_view(), name="all-products"),
    path("top/", views.TopProductsView.as_view(), name="top-products"),
    path("featured/", views.FeaturedProductsView.as_view(), name="featured-products"),
    path("recents/", views.RecentProductsView.as_view(), name="recent-products"),
    path("deals/", views.DealProductsView.as_view(), name="deal-products"),
    path(
        "<str:product_id>/related/",
        views.RelatedProductsAPIView.as_view(),
        name="related-products",
    ),
    # Reviewes
    path("reviews/", views.ReviewListCreateView.as_view(), name="review-list-create"),
    path(
        "<int:product_id>/reviews/",
        views.ProductReviewListView.as_view(),
        name="get_product_reviews",
    ),
    path(
        "reviews/<int:pk>/",
        views.ReviewDetailView.as_view(),
        name="review-detail",
    ),
    # CRUD
    path("create/", views.CreateProductView.as_view(), name="product-create"),
    path("<str:pk>/", views.ProductDetailView.as_view(), name="product-detail"),
    path("update/<str:pk>/", views.UpdateProductView.as_view(), name="product-update"),
    path("delete/<str:pk>/", views.DeleteProductView.as_view(), name="product-delete"),
]

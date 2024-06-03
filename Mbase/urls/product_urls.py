from django.urls import path
from Mbase.views import product_views as views

urlpatterns = [
    path("discountoffers/", views.DiscountOffersView.as_view(), name="discountoffers"),
    path(
        "discountoffers/<int:pk>/delete/",
        views.DiscountOfferDeleteView.as_view(),
        name="delete_discount_offer",
    ),
    path("categories/", views.getCategories, name="categories"),
    path("colors/", views.getAllColors, name="colors"),
    path("", views.getProducts, name="products"),
    path("all/", views.getAllProducts, name="all-products"),
    path("top/", views.getTopProducts, name="top-products"),
    path("featured/", views.getFeaturedProducts, name="featured-products"),
    path("recents/", views.getRecentProducts, name="recent-products"),
    path("deals/", views.getDealProducts, name="deal-products"),
    path("create/", views.createProduct, name="product-create"),
    path("upload/", views.uploadImage, name="image-upload"),
    path("<str:pk>/reviews/", views.createProductReview, name="create-review"),
    path("<str:pk>/", views.getProduct, name="product"),
    path("update/<str:pk>/", views.updateProduct, name="product-update"),
    path("delete/<str:pk>/", views.deleteProduct, name="product-delete"),
]

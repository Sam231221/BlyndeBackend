from django.urls import path
from Mbase.views import product_views as views

urlpatterns = [
    path('categories/', views.getCategories, name="categories"),

    path('', views.getProducts, name="products"),
    
    path('all/', views.getAllProducts , name="all-products"),

    #Filters
    path('top/', views.getTopProducts, name='top-products'),
    path('featured/', views.getFeaturedProducts, name="featured-products"),
    path('recents/', views.getRecentProducts, name="recent-products"),
    path('deals/', views.getDealProducts, name="deal-products"),

    path('create/', views.createProduct, name="product-create"),
    path('upload/', views.uploadImage, name="image-upload"),

    path('<str:pk>/reviews/', views.createProductReview, name="create-review"),

    path('<str:pk>/', views.getProduct, name="product"),

    path('update/<str:pk>/', views.updateProduct, name="product-update"),
    path('delete/<str:pk>/', views.deleteProduct, name="product-delete"),
]

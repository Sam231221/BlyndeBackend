from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("Mbase.urls.auth_urls")),
    path("api/users/", include("Mbase.urls.user_urls")),
    path("api/products/", include("Mbase.urls.product_urls")),
    path("api/orders/", include("Mbase.urls.order_urls")),
]


from django.conf import settings
from django.conf.urls.static import static

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

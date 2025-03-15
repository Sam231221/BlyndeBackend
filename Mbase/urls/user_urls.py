from django.urls import path
from Mbase.views import user_views as views


urlpatterns = [
    path("profile/", views.get_user_profile, name="users-profile"),
    path("wishlist/", views.wishlist_items, name="wishlist-list"),
    path("list/", views.listUsers, name="user-list"),
    path("create/", views.createUser, name="user-create"),
    path("update/<str:pk>/", views.updateUser, name="user-update"),
    path("delete/<str:pk>/", views.deleteUser, name="user-delete"),
    path(
        "<int:user_id>/orders/all/",
        views.get_user_all_orders,
        name="user_all_orders",
    ),
    path(
        "<int:user_id>/orders/recent/",
        views.get_user_recent_orders,
        name="user_recent_orders",
    ),
    # keep this at last since it can also match /api/users/list/, /api/users/create/ etc
    path("<str:first_name>/", views.getUserDetails, name="user-details"),
]

from django.urls import path
from Mbase.views import user_views as views


urlpatterns = [
    path("login/", views.login_user, name="user-login"),
    path("logout/", views.logout_user, name="user-logout"),
    path("api/token/refresh/", views.refresh_token_view, name="token_refresh"),
    path(
        "password-reset/confirm/",
        views.confirm_password_reset,
        name="password_reset_confirm",
    ),
    path(
        "password-reset-request/", views.request_password_reset, name="password_reset"
    ),
    path("register/", views.register_user, name="user-register"),
    path("profile/", views.get_user_profile, name="users-profile"),
    path("list/", views.listUsers, name="user-list"),
    path("create/", views.createUser, name="user-create"),
    path("update/<str:pk>/", views.updateUser, name="user-update"),
    path("delete/<str:pk>/", views.deleteUser, name="user-delete"),
    path(
        "verify-email/<uidb64>/<token>/",
        views.verify_user_email,
        name="verify_email",
    ),
    path("wishlist/", views.wishlist_items, name="wishlist-list"),
    # keep this at last since it can also match /api/users/list/, /api/users/create/ etc
    path("<str:first_name>/", views.getUserDetails, name="user-details"),
]

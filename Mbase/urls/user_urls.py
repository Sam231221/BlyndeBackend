from django.urls import path
from Mbase.views import user_views as views


urlpatterns = [
    path("login/", views.loginUser, name="user-token-obtain-pair"),
    path("logout/", views.logout, name="logout"),
    path("api/token/refresh/", views.refresh_token_view, name="token_refresh"),
    path(
        "password-reset/confirm/",
        views.confirm_password_reset,
        name="password_reset_confirm",
    ),
    path(
        "password-reset-request/", views.request_password_reset, name="password_reset"
    ),
    path("register/", views.registerUser, name="user-register"),
    path("profile/", views.getUserProfile, name="users-profile"),
    path("list/", views.listUsers, name="user-list"),
    path("create/", views.createUser, name="user-create"),
    path("update/<str:pk>/", views.updateUser, name="user-update"),
    path("delete/<str:pk>/", views.deleteUser, name="user-delete"),
    path(
        "verify-email/<uidb64>/<token>/",
        views.verify_email,
        name="verify_email",
    ),
    # keep this at last since it can also match /api/users/list/, /api/users/create/ etc
    path("<str:first_name>/", views.getUserDetails, name="user-details"),
]

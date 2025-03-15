from django.urls import path
from Mbase.views import auth_views as views


urlpatterns = [
    path("register/", views.register_user, name="user-register"),
    path("login/", views.login_user, name="user-login"),
    path("logout/", views.logout_user, name="user-logout"),
    path("token/refresh/", views.refresh_token_view, name="token_refresh"),
    path(
        "password-reset-request/", views.request_password_reset, name="password_reset"
    ),
    path(
        "password-reset/confirm/",
        views.confirm_password_reset,
        name="password_reset_confirm",
    ),
    path(
        "verify-email/<uidb64>/<token>/",
        views.verify_user_email,
        name="verify_email",
    ),
]

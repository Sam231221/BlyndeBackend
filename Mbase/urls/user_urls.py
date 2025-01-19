from django.urls import path
from Mbase.views import user_views as views


urlpatterns = [
    path(
        "login/", views.MyTokenObtainPairView.as_view(), name="user-token-obtain-pair"
    ),
    path("register/", views.registerUser, name="user-register"),
    path("profile/", views.getUserProfile, name="users-profile"),
    path("list/", views.listUsers, name="user-list"),
    path("<str:pk>/", views.getUserDetails, name="user-details"),
    path("update/<str:pk>/", views.updateUser, name="user-update"),
    path("delete/<str:pk>/", views.deleteUser, name="user-delete"),
]

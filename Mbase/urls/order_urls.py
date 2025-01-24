from django.urls import path
from Mbase.views import order_views as views


urlpatterns = [
    path("", views.GetOrdersView.as_view(), name="orders"),
    path("add/", views.AddOrderItemsView.as_view(), name="orders-add"),
    path("myorders/", views.GetMyOrdersView.as_view(), name="myorders"),
    path("<str:pk>/", views.GetOrderByIdView.as_view(), name="user-order"),
    path(
        "<str:pk>/deliver/",
        views.UpdateOrderToDeliveredView.as_view(),
        name="order-delivered",
    ),
    # after clicking paypal button
    path("<str:pk>/pay/", views.UpdateOrderToPaidView.as_view(), name="pay"),
]

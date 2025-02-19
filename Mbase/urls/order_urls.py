from django.urls import path
from Mbase.views import order_views as views

urlpatterns = [
    path("add/", views.AddOrderItemsView.as_view(), name="order-add"),
    path("myorders/", views.GetMyOrdersView.as_view(), name="get-my-orders"),
    path(
        "<str:order_number>/deliver/",
        views.UpdateOrderToDeliveredView.as_view(),
        name="order-deliver",
    ),
    path(
        "<str:order_number>/pay/",
        views.UpdateOrderToPaidView.as_view(),
        name="order-pay",
    ),
    path("list/", views.GetOrdersView.as_view(), name="order-list"),
    path(
        "<str:order_number>/",
        views.GetOrderByOrderNumberView.as_view(),
        name="get-order-by-number",
    ),
]

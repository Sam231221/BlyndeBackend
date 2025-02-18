from django.urls import path
from Mbase.views import order_views as views

urlpatterns = [
    path("add/", views.AddOrderItemsView.as_view(), name="order-add"),
    path("myorders/", views.GetMyOrdersView.as_view(), name="get-my-orders"),
    path(
        "<str:order_number>/",
        views.GetOrderByIdView.as_view(),
        name="get-order-by-number",
    ),
    path(
        "<str:pk>/deliver/",
        views.UpdateOrderToDeliveredView.as_view(),
        name="order-deliver",
    ),
    path("<str:pk>/pay/", views.UpdateOrderToPaidView.as_view(), name="order-pay"),
    path("", views.GetOrdersView.as_view(), name="order-list"),
]

from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from Mbase.models import Product, Order, OrderItem, ShippingAddress
from Mbase.serializers import OrderSerializer

from rest_framework.views import APIView
from rest_framework import status
from datetime import datetime
from django.utils import timezone


class GetOrdersView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        orders = Order.objects.order_by("-createdAt")
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)


class AddOrderItemsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        data = request.data
        orderItems = data.get("orderItems", [])
        if not orderItems:
            return Response(
                {"detail": "No Order Items"}, status=status.HTTP_400_BAD_REQUEST
            )

        # (1) Create order
        order = Order.objects.create(
            user=user,
            paymentMethod=data["paymentMethod"],
            taxPrice=data["taxPrice"],
            shippingPrice=data["shippingPrice"],
            totalPrice=data["totalPrice"],
        )

        # (2) Create shipping address
        ShippingAddress.objects.create(
            order=order,
            address=data["shippingAddress"]["address"],
            city=data["shippingAddress"]["city"],
            postalCode=data["shippingAddress"]["postalCode"],
            country=data["shippingAddress"]["country"],
        )

        # (3) Create order items and set order to orderItem relationship
        for item_data in orderItems:
            product = Product.objects.get(_id=item_data["productId"])
            order_item = OrderItem.objects.create(
                product=product,
                order=order,
                name=product.name,
                color=item_data["color"],
                size=item_data["size"],
                qty=int(item_data["quantity"]),
                price=item_data["price"],
                thumbnail=product.thumbnail.url,
            )
            product.countInStock -= order_item.qty
            product.save()

        serializer = OrderSerializer(order, many=False)
        return Response(serializer.data)


class GetOrderByIdView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        user = request.user
        try:
            order = Order.objects.get(_id=pk)
            if user.is_staff or order.user == user:
                serializer = OrderSerializer(order, many=False)
                return Response(serializer.data)
            else:
                return Response(
                    {"detail": "Not authorized to view this order"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Order.DoesNotExist:
            return Response(
                {"detail": "Order does not exist"}, status=status.HTTP_400_BAD_REQUEST
            )


class GetMyOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        orders = user.order_set.order_by("-_id")
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)


class UpdateOrderToPaidView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        try:
            order = Order.objects.get(_id=pk)
            order.isPaid = True
            order.paidAt = timezone.now()
            order.save()
            return Response(
                {"detail": f"Order was paid at {order.paidAt}"},
                status=status.HTTP_200_OK,
            )

        except Order.DoesNotExist:
            return Response(
                {"detail": "Order does not exist"}, status=status.HTTP_400_BAD_REQUEST
            )


class UpdateOrderToDeliveredView(APIView):
    permission_classes = [IsAdminUser]

    def put(self, request, pk):
        try:
            order = Order.objects.get(_id=pk)
            order.isDelivered = True
            order.deliveredAt = datetime.now()
            order.save()
            return Response(
                {"detail": "Order was delivered"}, status=status.HTTP_200_OK
            )
        except Order.DoesNotExist:
            return Response(
                {"detail": "Order does not exist"}, status=status.HTTP_400_BAD_REQUEST
            )

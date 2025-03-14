from django.db import transaction
from django.utils import timezone
from datetime import datetime
from decimal import Decimal
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from Mbase.models import Product, Order, OrderItem, ShippingAddress, Coupon
from Mbase.serializers import OrderSerializer
from Mbase.pagination import OrderPagination


class GetOrdersView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        orders = Order.objects.order_by("-createdAt")
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)


class GetOrderByOrderNumberView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_number):
        user = request.user
        try:
            order = Order.objects.get(order_number=order_number)
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


class GetUserOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        orders = user.order_set.order_by("-_id")

        ordering = request.GET.get("sortBy", None)
        sort_order = request.GET.get("sortOrder", "asc")

        if ordering:
            if sort_order == "desc":
                ordering = f"-{ordering}"
            orders = orders.order_by(ordering)
        paginator = OrderPagination()
        page = paginator.paginate_queryset(orders, request)

        serializer = OrderSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class OrderCouponAPIView(APIView):
    def post(self, request, order_id):
        coupon_code = request.data.get("coupon_code")
        if not coupon_code:
            return Response(
                {"error": "Coupon code is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order = get_object_or_404(Order, _id=order_id)

        try:
            coupon = Coupon.objects.get(code=coupon_code)
        except Coupon.DoesNotExist:
            return Response(
                {"error": "Invalid coupon code."}, status=status.HTTP_400_BAD_REQUEST
            )

        if coupon.coupon_scope != "order":
            return Response(
                {"error": "Coupon is not valid for order level."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not coupon.is_valid():
            return Response(
                {"error": "Coupon is not valid or has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not order.totalPrice:
            return Response(
                {"error": "Order total price is not set."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        original_total = order.totalPrice

        try:
            if coupon.discount.discount_type == "percentage":
                if coupon.discount.amount < 5:
                    raise ValidationError(
                        "Coupon percentage discount must be at least 5%."
                    )
                discounted_total = order.totalPrice * (1 - coupon.discount.amount / 100)
            else:  # fixed discount
                computed_percentage = (coupon.discount.amount / order.totalPrice) * 100
                if computed_percentage < 5:
                    raise ValidationError(
                        "Coupon fixed discount must be at least 5% of the order total."
                    )
                discounted_total = order.totalPrice - coupon.discount.amount

            discounted_total = max(discounted_total, Decimal("0.00")).quantize(
                Decimal("0.01")
            )
            order.totalPrice = discounted_total
            order.save(update_fields=["totalPrice"])
            coupon.use_coupon()
        except ValidationError as e:
            return Response({"error": e.message}, status=status.HTTP_400_BAD_REQUEST)

        data = {
            "order_id": order._id,
            "original_total": str(original_total),
            "discounted_total": str(discounted_total),
            "coupon_code": coupon_code,
        }
        return Response(data, status=status.HTTP_200_OK)


class AddOrderItemsView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
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
            itemsPrice=data["itemsPrice"],
        )
        ShippingAddress.objects.create(
            order=order,
            address=data["shippingAddress"]["address"],
            city=data["shippingAddress"]["city"],
            postalCode=data["shippingAddress"]["postalCode"],
            country=data["shippingAddress"]["country"],
        )
        for item in orderItems:
            try:
                product = Product.objects.get(_id=item["productId"])
            except Product.DoesNotExist:
                return Response(
                    {"detail": f"Product with id {item['productId']} not found."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # If the item contains an "items" key, iterate over each variant.
            if "variations" in item and isinstance(item["variations"], list):
                for variant in item["variations"]:
                    qty = int(variant.get("qty", 0))
                    if qty <= 0:
                        continue  # Skip variants with no quantity
                    OrderItem.objects.create(
                        product=product,
                        order=order,
                        name=product.name,
                        color=variant.get("color", ""),
                        size=variant.get("size", ""),
                        qty=qty,
                        price=item.get("price", product.price),
                        thumbnail=product.thumbnail_url,
                    )
                    product.countInStock -= qty
                    product.save()
            else:
                # Flat structure for a single variant order item.
                qty = int(item.get("qty", 0))
                if qty > 0:
                    OrderItem.objects.create(
                        product=product,
                        order=order,
                        name=product.name,
                        color=item.get("color", ""),
                        size=item.get("size", ""),
                        qty=qty,
                        price=item.get("price", product.price),
                        thumbnail=product.thumbnail_url,
                    )
                    product.countInStock -= qty
                    product.save()
        serializer = OrderSerializer(order, many=False)
        return Response(serializer.data)


def redeem_coupon(code):
    try:
        coupon = Coupon.objects.get(code=code, is_active=True)
        if coupon.used < coupon.max_uses:
            coupon.used += 1
            coupon.save()
            return True
    except Coupon.DoesNotExist:
        pass
    return False


class ApplyCouponView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, product_id, coupon_code):
        try:
            product = Product.objects.get(id=product_id)
            new_price = product.get_discounted_price(coupon_code=coupon_code)

            if redeem_coupon(coupon_code):
                return Response({"success": True, "new_price": str(new_price)})
            else:
                return Response(
                    {"success": False, "message": "Coupon is invalid or expired."}
                )
        except Product.DoesNotExist:
            return Response({"success": False, "message": "Product not found."})


class UpdateOrderToPaidView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, order_number):
        try:
            with transaction.atomic():
                order = Order.objects.select_for_update().get(order_number=order_number)

                if not order.isPaid:
                    order.status = "Paid"
                    order.isPaid = True
                    order.paidAt = timezone.now()
                    order.save()
                    return Response(
                        {"detail": f"Order was paid at {order.paidAt}"},
                        status=status.HTTP_200_OK,
                    )
                else:
                    return Response(
                        {"detail": "Order is already paid"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        except Order.DoesNotExist:
            return Response(
                {"detail": "Order does not exist"}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"detail": f"An error occurred: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UpdateOrderToDeliveredView(APIView):
    permission_classes = [IsAdminUser]

    def put(self, request, order_number):
        try:
            order = Order.objects.get(order_number=order_number)
            order.isDelivered = True
            order.deliveredAt = datetime.now()
            order.save()
            return Response(
                {
                    "detail": "Order was delivered",
                    "data": OrderSerializer(order, many=False).data,
                },
                status=status.HTTP_200_OK,
            )
        except Order.DoesNotExist:
            return Response(
                {"detail": "Order does not exist"}, status=status.HTTP_400_BAD_REQUEST
            )

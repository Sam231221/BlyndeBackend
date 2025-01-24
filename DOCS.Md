For adding order items
{
"orderItems": [
{
"productId": 1,
"quantity": 2,
"price": 50,
"color": "Red",
"size": "M"
},
{
"productId": 2,
"quantity": 1,
"price": 75,
"color": "Blue",
"size": "L"
}
],
"paymentMethod": "PayPal",
"taxPrice": 10,
"shippingPrice": 5,
"totalPrice": 140,
"shippingAddress": {
"address": "123 Main Street",
"city": "New York",
"postalCode": "10001",
"country": "USA"
}
}

# For Product image urls

from django.db import models
from django.core.validators import URLValidator

class MyModel(models.Model):
my_url = models.URLField(
validators=[URLValidator(schemes=['http', 'https'])],
max_length=200,
blank=True,
null=True,
)

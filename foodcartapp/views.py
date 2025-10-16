from django.db import transaction
from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from .models import Product, Order, OrderItem
from .serializers import OrderSerializer


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


@api_view(['POST'])
@transaction.atomic
def register_order(request: Request) -> Response:
    serializer = OrderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    order_data = serializer.validated_data
    order = Order.objects.create(
        firstname=order_data['firstname'],
        lastname=order_data['lastname'],
        phonenumber=order_data['phonenumber'],
        address=order_data['address'],
    )
    products = [
        OrderItem(
            order=order,
            product=product['product'],
            quantity=product['quantity'],
        )
        for product in order_data['products']
    ]
    OrderItem.objects.bulk_create(products)

    return Response({'success': request.data})

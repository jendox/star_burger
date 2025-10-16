from django.db import transaction
from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from .models import Product, Order, OrderItem


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
    try:
        order_data = request.data
        products = order_data['products']
        if products is None:
            raise ValueError('products: Это поле не может быть пустым.')
        if not isinstance(products, list):
            raise ValueError(f'products: Ожидался list со значениями, но был получен "{type(products).__name__}"')
        if not products:
            raise ValueError('products: Этот список не может быть пустым.')

        order = Order(
            first_name=order_data['firstname'],
            last_name=order_data['lastname'],
            phone_number=order_data['phonenumber'],
            address=order_data['address'],
        )
        order.save()

        for item in order_data['products']:
            product = Product.objects.available().get(pk=item['product'])
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item['quantity'],
            )
    except ValueError as e:
        return Response({'error': str(e)}, status=400)
    except KeyError as e:
        return Response({'error': f"{e.args[0]}: Обязательное поле."}, status=400)
    except Product.DoesNotExist as e:
        return Response({'error': f'Product not found: {e}'}, status=400)
    except Exception as e:
        return Response({'error': f'Unexpected error: {e}'}, status=500)
    return Response({'success': True})

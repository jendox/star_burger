import json

from django.core.handlers.wsgi import WSGIRequest
from django.db import transaction
from django.http import JsonResponse
from django.templatetags.static import static
from django.views.decorators.http import require_POST

from .models import Product, Order, OrderProductItem


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


@require_POST
@transaction.atomic
def register_order(request: WSGIRequest):
    try:
        order_data = json.loads(request.body.decode('utf-8'))
        order = Order(
            first_name=order_data['firstname'],
            last_name=order_data['lastname'],
            phone_number=order_data['phonenumber'],
            address=order_data['address'],
        )
        order.save()

        for item in order_data['products']:
            product = Product.objects.available().get(pk=item['product'])
            OrderProductItem.objects.create(
                order=order,
                product=product,
                quantity=item['quantity'],
            )
    except ValueError as e:
        JsonResponse({'error': f'Invalid json: {e}'}, status=400)
    except KeyError as e:
        JsonResponse({'error': f'Field is missing: {e}'}, status=400)
    except Product.DoesNotExist as e:
        JsonResponse({'error': f'Product not found: {e}'}, status=400)
    except Exception as e:
        JsonResponse({'error': 'Unexpected error'}, status=500)
    return JsonResponse({'success': True})

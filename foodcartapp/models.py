from collections import defaultdict
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum, F, QuerySet, Count
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderQuerySet(models.QuerySet):
    def total_cost(self) -> QuerySet:
        return self.annotate(
            total_cost=Sum(F('products__product__price') * F('products__quantity'))
        )

    def active(self) -> QuerySet:
        return self.exclude(status='delivered').total_cost()


class Order(models.Model):
    class OrderStatusChoices(models.TextChoices):
        ACCEPTED = 'accepted', 'Принят'
        CONFIRMED = 'confirmed', 'Подтвержден'
        PREPARING = 'preparing', 'Готовится'
        READY_FOR_PICKUP = 'ready_for_pickup', 'Готов к выдаче'
        IN_DELIVERY = 'in_delivery', 'В пути'
        DELIVERED = 'delivered', 'Доставлен'

    class PaymentMethodChoices(models.TextChoices):
        ONLINE = 'online', 'Оплата онлайн'
        CASH = 'cash', 'Наличными курьеру'
        CARD = 'card', 'Банковской картой курьеру'

    firstname = models.CharField(
        'Имя',
        max_length=32,
    )
    lastname = models.CharField(
        'Фамилия',
        max_length=64,
    )
    phonenumber = PhoneNumberField(
        'Мобильный номер',
    )
    address = models.CharField(
        'Адрес',
        max_length=200,
    )
    comment = models.TextField(
        'Комментарий',
        blank=True,
    )
    status = models.CharField(
        'Статус',
        max_length=16,
        choices=OrderStatusChoices,
        default=OrderStatusChoices.ACCEPTED,
        db_index=True,
    )
    payment_method = models.CharField(
        max_length=8,
        choices=PaymentMethodChoices,
        default=PaymentMethodChoices.CASH,
        db_index=True,
    )
    restaurant = models.ForeignKey(
        Restaurant,
        verbose_name='Ресторан, готовящий заказ',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='orders',
    )
    created_at = models.DateTimeField(
        'Зарегистрирован',
        default=timezone.now,
        db_index=True,
    )
    called_at = models.DateTimeField(
        'Подтвержден',
        null=True,
        blank=True,
        db_index=True,
    )
    delivered_at = models.DateTimeField(
        'Доставлен',
        null=True,
        blank=True,
        db_index=True,
    )

    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self) -> str:
        return f'{self.firstname} {self.lastname} {self.address}'

    @property
    def full_name(self) -> str:
        return f'{self.firstname} {self.lastname}'

    def get_available_restaurants(self):
        order_products_ids = self.products.values_list('product_id', flat=True)
        available_restaurants = Restaurant.objects.filter(
            menu_items__product_id__in=order_products_ids,
            menu_items__availability=True
        ).annotate(
            available_products_count=Count('menu_items__product', distinct=True)
        ).filter(
            available_products_count=len(order_products_ids)
        ).distinct()

        return available_restaurants

    @classmethod
    def active_orders_with_restaurants(cls):
        # Получаем заказы и позиции заказа (плоскими строками)
        order_rows = list(
            OrderItem.objects
            .exclude(order__status='delivered')
            .values(
                'order_id',
                'order__status',
                'order__payment_method',
                'order__firstname',
                'order__lastname',
                'order__phonenumber',
                'order__address',
                'order__comment',
                'order__created_at',
                'order__restaurant_id',
                'product_id',
                'price',
                'quantity',
            )
            .order_by('order_id')
        )
        # Получаем рестораны с доступными продуктами
        menu_rows = list(
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values('restaurant_id', 'product_id', 'restaurant__name')
            .distinct()
        )
        # Группируем рестораны по продуктам
        rest_products = defaultdict(set)
        rest_names = {}
        for r in menu_rows:
            rid = r['restaurant_id']
            rest_products[rid].add(r['product_id'])
            rest_names[rid] = r['restaurant__name']
        # Группируем строки заказа в заказы
        orders_map = {}
        for row in order_rows:
            oid = row['order_id']
            o = orders_map.get(oid)
            if not o:
                o = orders_map[oid] = {
                    'order_id': oid,
                    'status': Order.OrderStatusChoices(row['order__status']),
                    'payment_method': Order.PaymentMethodChoices(row['order__payment_method']),
                    'client': f"{row['order__firstname']} {row['order__lastname']}",
                    'phonenumber': row['order__phonenumber'],
                    'address': row['order__address'],
                    'comment': row['order__comment'],
                    'created_at': row['order__created_at'],
                    'restaurant_id': row['order__restaurant_id'],
                    'restaurants': [],
                    'products': set(),
                    'total_cost': Decimal('0.00'),
                }
            o['products'].add(row['product_id'])
            price = row['price'] if row['price'] is not None else Decimal('0.00')
            qty = row['quantity'] or 0
            o['total_cost'] += (price * qty)
        # Подбираем рестораны или подставляем выбранный
        for o in orders_map.values():
            chosen_id = o['restaurant_id']
            if chosen_id:  # выбран ресторан: показываем только его
                o['restaurants'] = [{
                    'id': chosen_id,
                    'name': rest_names.get(chosen_id, '—'),
                }]
            else:
                required = o['products']
                fits = []
                # Проверяем покрытие: ресторан подходит, если его товары >= товары заказа
                for rid, products in rest_products.items():
                    if required.issubset(products):
                        fits.append({'id': rid, 'name': rest_names.get(rid, '—')})
                o['restaurants'] = fits
            # Чтобы шаблон мог итерироваться
            o['products'] = list(o['products'])

            # Флаг для сортировки: без выбранного — сверху (False < True)
            o['has_restaurant'] = bool(chosen_id)
        # Итоговый отсортированный список
        orders_list = sorted(
            orders_map.values(),
            key=lambda x: (x['has_restaurant'], -x['created_at'].timestamp())
        )

        return orders_list


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        verbose_name='Заказ',
        on_delete=models.CASCADE,
        related_name='products',
    )
    product = models.ForeignKey(
        Product,
        verbose_name='Товар',
        on_delete=models.CASCADE,
        related_name='order_items',
    )
    quantity = models.PositiveIntegerField(
        'Количество',
        validators=[MinValueValidator(1)],
        default=1,
    )
    price = models.DecimalField(
        'Цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    class Meta:
        verbose_name = 'Элемент заказа'
        verbose_name_plural = 'Элементы заказа'
        unique_together = [
            ['order', 'product'],
        ]

    def __str__(self) -> str:
        return f'{self.product.name} - {self.order.full_name}'

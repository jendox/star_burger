import requests
from django.conf import settings
from django.db import models
from django.utils import timezone


class FetchCoordinatesError(RuntimeError):
    """Ошибка при получении координат из геокодера."""


class GeocodedAddress(models.Model):
    address = models.CharField(
        'Адрес',
        max_length=512,
    )
    norm_address = models.CharField(
        'Нормализованный адрес',
        max_length=512,
        unique=True,
        db_index=True,
    )
    lat = models.FloatField(
        'Широта',
        null=True,
        blank=True,
    )
    lon = models.FloatField(
        'Долгота',
        null=True,
        blank=True,
    )
    fetched_at = models.DateTimeField(
        'Время получения координат',
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Геокодированный адрес'
        verbose_name_plural = 'Геокодированные адреса'

    def __str__(self):
        return self.address

    @staticmethod
    def normalize(address: str | None) -> str:
        return (address or '').strip().lower()

    @classmethod
    def get_coordinates(cls, address: str) -> tuple[float, float] | None:
        try:
            norm_address = cls.normalize(address)
            if not norm_address:
                raise FetchCoordinatesError('Адрес - пустая строка.')
            geo_address = cls.objects.filter(norm_address=norm_address).first()
            if (
                geo_address is not None
                and geo_address.lat is not None
                and geo_address.lon is not None
            ):
                return geo_address.lat, geo_address.lon

            lat, lon = fetch_coordinates(address)
            now = timezone.now()
            cls.objects.create(
                address=address,
                norm_address=norm_address,
                lat=lat,
                lon=lon,
                fetched_at=now,
            )
            return lat, lon
        except FetchCoordinatesError:
            return None


def fetch_coordinates(address: str) -> tuple[float, float] | None:
    try:
        base_url = 'https://geocode-maps.yandex.ru/1.x'
        response = requests.get(base_url, params={
            'geocode': address,
            'apikey': settings.YANDEX_GEOCODER_API_KEY,
            'format': 'json',
        })
        response.raise_for_status()
        found_places = response.json()['response']['GeoObjectCollection']['featureMember']
        if not found_places:
            raise FetchCoordinatesError(f'Адрес {address} не найден.')
        most_relevant = found_places[0]
        lon, lat = most_relevant['GeoObject']['Point']['pos'].split(' ')
        return float(lat), float(lon)

    except requests.HTTPError as error:
        raise FetchCoordinatesError(f'Не удалось получить координаты: {str(error)}.') from error

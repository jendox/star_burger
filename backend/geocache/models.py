from django.db import models

from geocache.geocoder import fetch_coordinates, FetchCoordinatesError


class GeocodedAddress(models.Model):
    address = models.CharField(
        'Адрес',
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Геокодированный адрес'
        verbose_name_plural = 'Геокодированные адреса'

    def __str__(self):
        return self.address

    @classmethod
    def get_coordinates_batch(cls, addresses: set[str]) -> dict[str, tuple[float, float] | None]:
        if not addresses:
            return {}

        coordinates_map = {}
        existing_addresses = cls.objects.filter(address__in=addresses)

        for geo_address in existing_addresses:
            if geo_address.lat is None or geo_address.lon is None:
                coordinates_map[geo_address.address] = None
            else:
                coordinates_map[geo_address.address] = (geo_address.lat, geo_address.lon)

        missing_addresses = addresses - set(coordinates_map.keys())
        new_geo_addresses = []
        for address in missing_addresses:
            try:
                lat, lon = fetch_coordinates(address)
                new_geo_addresses.append(cls(address=address, lat=lat, lon=lon))
                if lat is None or lon is None:
                    raise FetchCoordinatesError('Не удалось вычислить координаты для данного адреса.')
                coordinates_map[address] = (lat, lon)
            except FetchCoordinatesError:
                coordinates_map[address] = None
        if new_geo_addresses:
            cls.objects.bulk_create(new_geo_addresses)
        return coordinates_map

    @classmethod
    def get_coordinates(cls, address: str) -> tuple[float, float] | None:
        try:
            if not address.strip():
                raise FetchCoordinatesError('Адрес - пустая строка.')
            geo_address = cls.objects.filter(address=address).first()
            if geo_address is None:
                lat, lon = fetch_coordinates(address)
                geo_address = cls.objects.create(address=address, lat=lat, lon=lon)
            if geo_address.lat is None or geo_address.lon is None:
                raise FetchCoordinatesError('Не удалось вычислить координаты для данного адреса.')
            return geo_address.lat, geo_address.lon
        except FetchCoordinatesError:
            return None

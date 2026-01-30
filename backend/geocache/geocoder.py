import requests
from django.conf import settings


class FetchCoordinatesError(RuntimeError):
    """Ошибка при получении координат из геокодера."""


def fetch_coordinates(address: str) -> tuple[float | None, float | None]:
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
            return None, None
        most_relevant = found_places[0]
        lon, lat = most_relevant['GeoObject']['Point']['pos'].split(' ')
        return float(lat), float(lon)
    except requests.HTTPError as error:
        raise FetchCoordinatesError(f'Не удалось получить координаты: {str(error)}.') from error

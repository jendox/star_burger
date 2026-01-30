from django.contrib import admin

from geocache.models import GeocodedAddress


@admin.register(GeocodedAddress)
class GeocodedAddressAdmin(admin.ModelAdmin):
    list_display = ('address', 'lat', 'lon', 'updated_at')
    search_fields = ('address',)

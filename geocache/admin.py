from django.contrib import admin

from geocache.models import GeocodedAddress


@admin.register(GeocodedAddress)
class GeocodedAddressAdmin(admin.ModelAdmin):
    list_display = ('address', 'lat', 'lon', 'fetched_at', 'updated_at')
    search_fields = ('address', 'norm_address')

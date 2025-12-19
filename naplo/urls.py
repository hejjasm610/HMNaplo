from django.urls import path
from .views import (
    naplo_bevitel,
    kategoria_treemap,
    api_kategoria_osszefoglalo,
    api_kategoria_bejegyzesek,
)

urlpatterns = [
    path("bevitel/", naplo_bevitel, name="naplo_bevitel"),
    path("bevitel/<int:pk>/", naplo_bevitel, name="naplo_bevitel_edit"),

    path("kategoria-treemap/", kategoria_treemap, name="kategoria_treemap"),

    path("api/kategoria-osszefoglalo/", api_kategoria_osszefoglalo, name="api_kategoria_osszefoglalo"),
    path("api/kategoria-bejegyzesek/", api_kategoria_bejegyzesek, name="api_kategoria_bejegyzesek"),
]

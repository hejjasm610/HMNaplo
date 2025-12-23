from django.urls import path
from .views import (
    naplo_bevitel,
    kategoria_treemap,
    api_kategoria_osszefoglalo,
    api_kategoria_bejegyzesek,
    api_utolso_bejegyzesek_kategoriara,
    dashboard_kereses,
    nap_attekintes,
)

urlpatterns = [
    path("bevitel/", naplo_bevitel, name="naplo_bevitel"),
    path("bevitel/<int:pk>/", naplo_bevitel, name="naplo_bevitel_edit"),

    path("kategoria-treemap/", kategoria_treemap, name="kategoria_treemap"),

    path("dashboard/", dashboard_kereses, name="dashboard"),
    path("nap/", nap_attekintes, name="nap_attekintes"),

    path("api/kategoria-osszefoglalo/", api_kategoria_osszefoglalo, name="api_kategoria_osszefoglalo"),
    path("api/kategoria-bejegyzesek/", api_kategoria_bejegyzesek, name="api_kategoria_bejegyzesek"),

    # új: kategória kiválasztás után modalhoz
    path(
        "api/utolso-bejegyzesek-kategoriara/",
        api_utolso_bejegyzesek_kategoriara,
        name="api_utolso_bejegyzesek_kategoriara",
    ),
]

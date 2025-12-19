from django.contrib import admin
from .models import NaploSor, Param

admin.site.register(Param)
@admin.register(NaploSor)
class NaploSorAdmin(admin.ModelAdmin):
    list_display = (
        "datum",
        "kezdet",
        "veg",
        "ido",
        "tevekenyseg",
        "ertek",
        "kategoria",
        "kapcsolodo",
        "szerep",
        "erzelem",
        "kapcsolodo_cel",
    )

    list_filter = ("datum", "kategoria", "erzelem")
    search_fields = ("tevekenyseg", "megjegyzes")
    ordering = ("-datum", "-kezdet")


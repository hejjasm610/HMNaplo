from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.utils import timezone

from .models import NaploSor
from .forms import NaploSorForm


def naplo_bevitel(request, pk=None):
    # ---- szerkesztési mód (ha van pk) ----
    obj = NaploSor.objects.filter(pk=pk).first() if pk else None

    # ---- segédfüggvény: éjfél átlépés ----
    def end_datetime(s):
        dt_start = datetime.combine(s.datum, s.kezdet)
        dt_end = datetime.combine(s.datum, s.veg)
        if dt_end < dt_start:
            dt_end += timedelta(days=1)
        return dt_end

    # ---- alap kezdő idő: utolsó sor végéről (csak új bevitelnél releváns) ----
    last = NaploSor.objects.order_by("-id").first()
    if last:
        last_end = end_datetime(last)
        initial_date = last_end.date()
        initial_start = last_end.time().replace(second=0, microsecond=0)
    else:
        now = timezone.localtime()
        initial_date = now.date()
        initial_start = now.time().replace(second=0, microsecond=0)

    dt0 = datetime.combine(initial_date, initial_start)
    initial_end = (dt0 + timedelta(minutes=30)).time()

    # ---- initial alap (csak új bevitelnél használjuk) ----
    initial = {
        "datum": initial_date,
        "kezdet": initial_start,
        "veg": initial_end,
    }

    # ---- kategória szerinti előtöltés (csak új bevitelnél) ----
    if not obj:
        category = request.GET.get("category_id")
        if category:
            last_cat = (
                NaploSor.objects
                .filter(kategoria=category)
                .order_by("-datum", "-kezdet", "-id")
                .first()
            )

            if last_cat:
                initial.update({
                    "kategoria": last_cat.kategoria,
                    "kapcsolodo": last_cat.kapcsolodo,
                    "szerep": last_cat.szerep,
                    "erzelem": last_cat.erzelem,
                    "kapcsolodo_cel": last_cat.kapcsolodo_cel,
                    "tevekenyseg": last_cat.tevekenyseg,
                })
            else:
                initial["kategoria"] = category

    # ---- POST / GET ----
    if request.method == "POST":
        form = NaploSorForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return redirect("naplo_bevitel")
    else:
        if obj:
            form = NaploSorForm(instance=obj)
        else:
            form = NaploSorForm(initial=initial)

    utolso_20 = NaploSor.objects.order_by("-id")[:20]

    return render(
        request,
        "naplo/naplo_bevitel.html",
        {
            "form": form,
            "utolso_20": utolso_20,
        }
    )

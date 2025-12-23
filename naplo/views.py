from datetime import datetime, timedelta

from django.db.models import Sum, Q, Avg
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.urls import reverse

from .models import NaploSor
from .forms import NaploSorForm


def format_minutes(total_minutes: int) -> str:
    """Perc -> 'X nap Y óra Z perc' (0 esetén is ad '0 perc'-et)."""
    try:
        m = int(total_minutes or 0)
    except (TypeError, ValueError):
        m = 0
    days = m // 1440
    hours = (m % 1440) // 60
    mins = m % 60

    parts = []
    if days:
        parts.append(f"{days} nap")
    if hours:
        parts.append(f"{hours} óra")
    if mins or not parts:
        parts.append(f"{mins} perc")
    return " ".join(parts)


def month_pill_style(month: int) -> str:
    """Hónap alapján erősen elkülönülő, világos háttérszínek a navigációs gombokhoz."""
    PALETTE = [
        ("#fee2e2", "#ef4444"),  # 1 light red
        ("#ffedd5", "#f97316"),  # 2 light orange
        ("#fef9c3", "#eab308"),  # 3 light yellow
        ("#dcfce7", "#22c55e"),  # 4 light green
        ("#d1fae5", "#10b981"),  # 5 light emerald
        ("#cffafe", "#06b6d4"),  # 6 light cyan
        ("#dbeafe", "#3b82f6"),  # 7 light blue
        ("#e0e7ff", "#6366f1"),  # 8 light indigo
        ("#f3e8ff", "#a855f7"),  # 9 light purple
        ("#fce7f3", "#ec4899"),  # 10 light pink
        ("#fae8ff", "#d946ef"),  # 11 light fuchsia
        ("#e5e7eb", "#111827"),  # 12 light gray (black border)
    ]
    try:
        m = int(month or 0)
    except (TypeError, ValueError):
        m = 0
    bg, border = PALETTE[(m - 1) % 12] if 1 <= m <= 12 else ("#e5e7eb", "#111827")
    return f"background: {bg}; border-color: {border}; color: #111;"


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


def kategoria_treemap(request):
    return render(request, "naplo/kategoria_treemap.html")


def api_kategoria_osszefoglalo(request):
    """
    GET:
      - start=YYYY-MM-DD
      - end=YYYY-MM-DD

    Válasz:
      {"items":[{"kategoria":"...", "minutes":123}, ...]}
    """
    start_s = request.GET.get("start")
    end_s = request.GET.get("end")

    start_d = parse_date(start_s) if start_s else None
    end_d = parse_date(end_s) if end_s else None

    if not start_d or not end_d:
        return JsonResponse({"error": "Kell start és end (YYYY-MM-DD)."}, status=400)

    qs = (
        NaploSor.objects
        .filter(datum__range=(start_d, end_d))
        .exclude(kategoria__iexact="Alvás")
        .values("kategoria")
        .annotate(total_ido=Sum("ido"))
        .order_by("-total_ido")
    )

    items = []
    for row in qs:
        dur = row["total_ido"]
        minutes = int(dur.total_seconds() // 60) if dur else 0
        items.append({
            "kategoria": row["kategoria"] or "",
            "minutes": minutes,
        })

    return JsonResponse({"items": items})


def api_kategoria_bejegyzesek(request):
    """
    GET:
      - start=YYYY-MM-DD
      - end=YYYY-MM-DD
      - kategoria=szoveg

    Válasz:
      {"entries":[{id, datum, kezdet, veg, minutes, tevekenyseg, megjegyzes}, ...]}
    """
    start_s = request.GET.get("start")
    end_s = request.GET.get("end")
    kategoria = (request.GET.get("kategoria") or "").strip()

    start_d = parse_date(start_s) if start_s else None
    end_d = parse_date(end_s) if end_s else None

    if not start_d or not end_d or not kategoria:
        return JsonResponse({"error": "Kell start, end és kategoria."}, status=400)

    qs = (
        NaploSor.objects
        .filter(datum__range=(start_d, end_d), kategoria=kategoria)
        .order_by("-datum", "-kezdet", "-id")   # legújabb felül
    )

    entries = []
    for s in qs:
        minutes = int(s.ido.total_seconds() // 60) if s.ido else 0
        entries.append({
            "id": s.id,
            "datum": s.datum.isoformat(),
            "kezdet": s.kezdet.strftime("%H:%M") if s.kezdet else "",
            "veg": s.veg.strftime("%H:%M") if s.veg else "",
            "minutes": minutes,
            "tevekenyseg": s.tevekenyseg,
            "megjegyzes": s.megjegyzes or "",
        })

    return JsonResponse({"entries": entries})


def api_utolso_bejegyzesek_kategoriara(request):
    """
    GET:
      - kategoria=szoveg
      - limit=20 (opcionális)

    Válasz:
      {"entries":[
        {id, datum, kezdet, veg, ertek, kapcsolodo, szerep, erzelem, kapcsolodo_cel, tevekenyseg, megjegyzes},
        ...
      ]}
    """
    kategoria = (request.GET.get("kategoria") or "").strip()
    limit_s = request.GET.get("limit") or "20"

    if not kategoria:
        return JsonResponse({"error": "Kell kategoria."}, status=400)

    try:
        limit = max(1, min(50, int(limit_s)))
    except ValueError:
        limit = 20

    qs = (
        NaploSor.objects
        .filter(kategoria=kategoria)
        .order_by("-datum", "-kezdet", "-id")[:limit]
    )

    entries = []
    for s in qs:
        entries.append({
            "id": s.id,
            "datum": s.datum.isoformat(),
            "kezdet": s.kezdet.strftime("%H:%M") if s.kezdet else "",
            "veg": s.veg.strftime("%H:%M") if s.veg else "",

            # a formhoz kellő mezők
            "ertek": s.ertek,
            "kapcsolodo": s.kapcsolodo or "",
            "szerep": s.szerep or "",
            "erzelem": s.erzelem or "",
            "kapcsolodo_cel": s.kapcsolodo_cel or "",
            "tevekenyseg": s.tevekenyseg or "",
            "megjegyzes": s.megjegyzes or "",
        })

    return JsonResponse({"entries": entries})


def dashboard_kereses(request):
    """
    Kérdésvezérelt dashboard (v1) – globális kereső a naplóban.

    GET paraméterek:
      - q: keresőkifejezés
      - start: YYYY-MM-DD (opcionális)
      - end: YYYY-MM-DD (opcionális)

    Találatok kattinthatók: a bevitel/szerkesztés oldalra visznek.
    """
    q = (request.GET.get("q") or "").strip()
    start_s = request.GET.get("start") or ""
    end_s = request.GET.get("end") or ""

    start_d = parse_date(start_s) if start_s else None
    end_d = parse_date(end_s) if end_s else None

    qs = NaploSor.objects.all()

    if start_d and end_d:
        qs = qs.filter(datum__range=(start_d, end_d))
    elif start_d:
        qs = qs.filter(datum__gte=start_d)
    elif end_d:
        qs = qs.filter(datum__lte=end_d)

    summary = {
        "count": 0,
        "total_minutes": 0,
        "total_human": format_minutes(0),
        "avg_ertek": None,
    }

    results = []
    day_groups = []
    day_nav = []

    if q:
        # szöveges keresés több mezőben egyszerre
        q_obj = (
            Q(tevekenyseg__icontains=q)
            | Q(megjegyzes__icontains=q)
            | Q(kategoria__icontains=q)
            | Q(kapcsolodo__icontains=q)
            | Q(szerep__icontains=q)
            | Q(erzelem__icontains=q)
            | Q(kapcsolodo_cel__icontains=q)
        )

        # ha a q tisztán szám, akkor Érték-re is szűrünk
        if q.isdigit():
            try:
                q_int = int(q)
                q_obj = q_obj | Q(ertek=q_int)
            except ValueError:
                pass

        qs2 = (
            qs.filter(q_obj)
            .order_by("-datum", "-kezdet", "-id")
        )

        # összegzés (percek + átlag Érték)
        agg = qs2.aggregate(
            total_ido=Sum("ido"),
            avg_ertek=Avg("ertek"),
        )
        total_minutes = int((agg["total_ido"].total_seconds() // 60)) if agg.get("total_ido") else 0
        avg_ertek = agg.get("avg_ertek")
        summary = {
            "count": qs2.count(),
            "total_minutes": total_minutes,
            "total_human": format_minutes(total_minutes),
            "avg_ertek": round(avg_ertek, 2) if avg_ertek is not None else None,
        }

        for s in qs2[:500]:  # v1: gyors, mégis bőséges
            minutes = int(s.ido.total_seconds() // 60) if s.ido else 0
            results.append({
                "id": s.id,
                "edit_url": reverse("naplo_bevitel_edit", args=[s.id]),
                "datum": s.datum,
                "kezdet": s.kezdet,
                "veg": s.veg,
                "minutes": minutes,
                "ertek": s.ertek,
                "kategoria": s.kategoria or "",
                "kapcsolodo": s.kapcsolodo or "",
                "szerep": s.szerep or "",
                "erzelem": s.erzelem or "",
                "kapcsolodo_cel": s.kapcsolodo_cel or "",
                "tevekenyseg": s.tevekenyseg or "",
                "megjegyzes": s.megjegyzes or "",
            })

        # Napi csoportosítás (ritmus / áttekintés)
        # A results már legújabb -> legrégebbi sorrendben van.
        by_day = {}
        for r in results:
            d = r["datum"]
            key = d.isoformat()
            if key not in by_day:
                by_day[key] = {
                    "date": d,
                    "anchor": f"d{d.strftime('%Y%m%d')}",
                    "items": [],
                    "total_minutes": 0,
                    "ertek_sum": 0,
                    "ertek_count": 0,
                }
            g = by_day[key]
            g["items"].append(r)
            g["total_minutes"] += int(r.get("minutes") or 0)
            if r.get("ertek") is not None:
                g["ertek_sum"] += int(r["ertek"])
                g["ertek_count"] += 1

        # by_day megőrzi a beszúrási sorrendet (Python 3.7+), ez a legújabb napok sorrendje.
        day_groups = []
        day_nav = []
        for g in by_day.values():
            avg = (g["ertek_sum"] / g["ertek_count"]) if g["ertek_count"] else None
            day_groups.append({
                "date": g["date"],
                "anchor": g["anchor"],
                "count": len(g["items"]),
                "total_minutes": g["total_minutes"],
                "total_human": format_minutes(g["total_minutes"]),
                "avg_ertek": round(avg, 2) if avg is not None else None,
                "items": g["items"],
            })
            day_nav.append({
                "anchor": g["anchor"],
                "date": g["date"],
            })

        # day_nav kiegészítése címkékkel
        for n in day_nav:
            d = n["date"]
            n["label"] = d.strftime("%m.%d")
            n["title"] = d.strftime("%Y.%m.%d")
            n["month"] = d.month
            n["style"] = month_pill_style(d.month)

    return render(
        request,
        "naplo/dashboard.html",
        {
            "q": q,
            "start": start_s,
            "end": end_s,
            "summary": summary,
            "results": results,
            "day_groups": day_groups,
            "day_nav": day_nav,
        }
    )


def nap_attekintes(request):
    """
    Napi összkép – válasz a kérdésre: 'hogyan telt egy bizonyos napom?'

    GET:
      - date=YYYY-MM-DD  (vagy datum=YYYY-MM-DD)

    Oldal:
      - idővonal (sorok időrendben)
      - napi összesítők
      - TOP kategóriák / TOP célok
    """
    date_s = (request.GET.get("date") or request.GET.get("datum") or "").strip()
    d = parse_date(date_s) if date_s else None

    if d is None:
        # alapértelmezés: legutóbbi bejegyzés napja, ha nincs, akkor a mai nap
        last = NaploSor.objects.order_by("-datum", "-kezdet", "-id").first()
        if last and last.datum:
            d = last.datum
        else:
            d = timezone.localdate()

    qs = NaploSor.objects.filter(datum=d).order_by("kezdet", "id")

    entries = []
    total_minutes = 0
    ertek_vals = []

    for s in qs:
        minutes = int(s.ido.total_seconds() // 60) if s.ido else 0
        total_minutes += minutes
        if s.ertek is not None:
            try:
                ertek_vals.append(int(s.ertek))
            except (TypeError, ValueError):
                pass

        entries.append({
            "id": s.id,
            "edit_url": reverse("naplo_bevitel_edit", args=[s.id]),
            "datum": s.datum,
            "kezdet": s.kezdet,
            "veg": s.veg,
            "minutes": minutes,
            "minutes_human": format_minutes(minutes),
            "ertek": s.ertek,
            "kategoria": s.kategoria or "",
            "kapcsolodo": s.kapcsolodo or "",
            "szerep": s.szerep or "",
            "erzelem": s.erzelem or "",
            "kapcsolodo_cel": s.kapcsolodo_cel or "",
            "tevekenyseg": s.tevekenyseg or "",
            "megjegyzes": s.megjegyzes or "",
        })

    avg_ertek = round(sum(ertek_vals) / len(ertek_vals), 2) if ertek_vals else None
    min_ertek = min(ertek_vals) if ertek_vals else None
    max_ertek = max(ertek_vals) if ertek_vals else None

    # TOP kategóriák (perc)
    cat_rows = (
        NaploSor.objects
        .filter(datum=d)
        .values("kategoria")
        .annotate(total_ido=Sum("ido"))
        .order_by("-total_ido", "kategoria")
    )

    top_kategoriak = []
    for r in cat_rows[:12]:
        dur = r.get("total_ido")
        m = int(dur.total_seconds() // 60) if dur else 0
        top_kategoriak.append({
            "kategoria": r.get("kategoria") or "",
            "minutes": m,
            "human": format_minutes(m),
        })

    # TOP célok (perc) – csak ha van szöveg
    cel_rows = (
        NaploSor.objects
        .filter(datum=d)
        .exclude(kapcsolodo_cel__isnull=True)
        .exclude(kapcsolodo_cel__exact="")
        .values("kapcsolodo_cel")
        .annotate(total_ido=Sum("ido"))
        .order_by("-total_ido", "kapcsolodo_cel")
    )

    top_celok = []
    for r in cel_rows[:12]:
        dur = r.get("total_ido")
        m = int(dur.total_seconds() // 60) if dur else 0
        top_celok.append({
            "cel": r.get("kapcsolodo_cel") or "",
            "minutes": m,
            "human": format_minutes(m),
        })

    return render(
        request,
        "naplo/nap_attekintes.html",
        {
            "date": d,
            "date_iso": d.isoformat(),
            "entries": entries,
            "total_minutes": total_minutes,
            "total_human": format_minutes(total_minutes),
            "avg_ertek": avg_ertek,
            "min_ertek": min_ertek,
            "max_ertek": max_ertek,
            "top_kategoriak": top_kategoriak,
            "top_celok": top_celok,
        }
    )

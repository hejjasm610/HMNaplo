import csv
import re
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from naplo.models import NaploSor


HUN_MONTHS = {
    "január": 1,
    "február": 2,
    "március": 3,
    "április": 4,
    "május": 5,
    "június": 6,
    "július": 7,
    "augusztus": 8,
    "szeptember": 9,
    "október": 10,
    "november": 11,
    "december": 12,
}


def parse_date_hu(s: str):
    """
    Várható: '2025. október 18., szombat'
    Elfogadja a vessző utáni résztől függetlenül.
    """
    s = (s or "").strip()
    if not s:
        raise ValueError("Üres dátum")

    s = s.split(",")[0].strip()  # '2025. október 18.'
    m = re.match(r"^\s*(\d{4})\.\s*([^\s]+)\s*(\d{1,2})\.\s*$", s)
    if not m:
        raise ValueError(f"Hibás dátum formátum: {s}")

    year = int(m.group(1))
    month_name = m.group(2).lower()
    day = int(m.group(3))

    if month_name not in HUN_MONTHS:
        raise ValueError(f"Ismeretlen hónapnév: {month_name}")

    return datetime(year, HUN_MONTHS[month_name], day).date()


def parse_time(s: str):
    """
    Várható: '09:20'
    Kezeli: '09_20', '09.20'
    """
    s = (s or "").strip()
    if not s:
        raise ValueError("Üres idő")

    s = s.replace("_", ":").replace(".", ":")
    return datetime.strptime(s, "%H:%M").time()


def parse_duration(s: str):
    """
    Várható: '0:30' vagy '2:05'
    Elfogadja: '00:30:00', valamint tiszta számot (percnek veszi).
    """
    s = (s or "").strip()
    if not s:
        raise ValueError("Üres időtartam")

    if s.count(":") == 2:
        h, m, sec = s.split(":")
        return timedelta(hours=int(h), minutes=int(m), seconds=int(sec))

    if s.count(":") == 1:
        h, m = s.split(":")
        return timedelta(hours=int(h), minutes=int(m))

    if s.isdigit():
        return timedelta(minutes=int(s))

    raise ValueError(f"Hibás időtartam: {s}")


class Command(BaseCommand):
    help = "HMNaplo CSV import (Excel export). Hibás idő/időtartam esetén sor átugrás."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str)

    def handle(self, *args, **opts):
        path = opts["csv_path"]

        created = 0
        skipped = 0
        line_no = 1  # header után az első adatsor lesz 2

        with open(path, newline="", encoding="utf-8-sig") as f:
            # Magyar Excel gyakran pontosvesszőt használ:
            reader = csv.DictReader(f, delimiter=";")
            if reader.fieldnames:
                reader.fieldnames = [h.strip() for h in reader.fieldnames]

            for row in reader:
                line_no += 1
                row = { (k.strip() if isinstance(k, str) else k): (v.strip() if isinstance(v, str) else v)
                        for k, v in row.items() }

                # üres sor átugrás
                if not any((v or "") for v in row.values()):
                    continue

                try:
                    datum = parse_date_hu(row.get("Dátum", ""))
                    kezdet = parse_time(row.get("Kezd", ""))
                    veg = parse_time(row.get("Vég", ""))
                    ido = parse_duration(row.get("Idő", ""))
                except Exception:
                    skipped += 1
                    continue

                try:
                    NaploSor.objects.create(
                        datum=datum,
                        kezdet=kezdet,
                        veg=veg,
                        ido=ido,
                        tevekenyseg=(row.get("Tevékenység", "") or ""),
                        ertek=int(row["Érték"]) if (row.get("Érték") or "").strip().isdigit() else None,
                        kategoria=(row.get("Kategória", "") or ""),
                        kapcsolodo=(row.get("Kapcsolódó", "") or ""),
                        szerep=(row.get("szerep", "") or ""),
                        erzelem=(row.get("Érzelem", "") or ""),
                        kapcsolodo_cel=(row.get("Kapcsolódó cél", "") or ""),
                        megjegyzes=(row.get("Megjegyzés", "") or ""),
                    )
                    created += 1
                except Exception:
                    skipped += 1
                    continue

        self.stdout.write(self.style.SUCCESS(f"Kész. Beírva: {created} sor. Átugorva: {skipped} sor."))


from django.core.management.base import BaseCommand
from naplo.models import NaploSor, Param


class Command(BaseCommand):
    help = "Param tábla feltöltése a NaploSor mezőkből (egyedi értékek)."

    def handle(self, *args, **options):
        mapping = {
            "kategoria": "kategoria",
            "kapcsolodo": "kapcsolodo",
            "szerep": "szerep",
            "erzelem": "erzelem",
            "kapcsolodo_cel": "cel",
        }

        created = 0
        seen = 0

        for field, tipus in mapping.items():
            values = (
                NaploSor.objects.exclude(**{f"{field}__isnull": True})
                .exclude(**{field: ""})
                .values_list(field, flat=True)
                .distinct()
            )

            for v in values:
                v = (v or "").strip()
                if not v:
                    continue
                seen += 1
                obj, was_created = Param.objects.get_or_create(tipus=tipus, nev=v)
                if was_created:
                    created += 1

        self.stdout.write(self.style.SUCCESS(f"Kész. Talált: {seen} | Új param: {created}"))

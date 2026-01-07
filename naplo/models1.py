from datetime import datetime, timedelta
from django.db import models


class Param(models.Model):
    TIPUSOK = [
        ("kategoria", "Kategória"),
        ("kapcsolodo", "Kapcsolódó"),
        ("szerep", "Szerep"),
        ("erzelem", "Érzelem"),
        ("cel", "Kapcsolódó cél"),
    ]

    tipus = models.CharField(max_length=20, choices=TIPUSOK)
    nev = models.CharField(max_length=200)

    class Meta:
        unique_together = ("tipus", "nev")
        ordering = ["tipus", "nev"]

    def __str__(self):
        return f"{self.get_tipus_display()}: {self.nev}"


class NaploSor(models.Model):
    datum = models.DateField()
    kezdet = models.TimeField(null=True, blank=True)
    veg = models.TimeField(null=True, blank=True)
    ido = models.DurationField()

    tevekenyseg = models.TextField()
    ertek = models.IntegerField(null=True, blank=True)

    kategoria = models.CharField(max_length=100, blank=True)
    kapcsolodo = models.CharField(max_length=100, blank=True)
    szerep = models.CharField(max_length=100, blank=True)
    erzelem = models.CharField(max_length=100, blank=True)
    kapcsolodo_cel = models.CharField(max_length=200, blank=True)

    # 6 program fókusz (P1–P6): több címke tárolása JSON listában (pl. ['P1_TUDAT','P3_EGESZSEG'])
    six_program_focus = models.JSONField(default=list, blank=True)

    letrehozva = models.DateTimeField(auto_now_add=True)
    megjegyzes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if self.datum and self.kezdet and self.veg:
            dt_start = datetime.combine(self.datum, self.kezdet)
            dt_end = datetime.combine(self.datum, self.veg)
            if dt_end < dt_start:
                dt_end += timedelta(days=1)
            self.ido = dt_end - dt_start
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["-datum", "-kezdet"]

    def __str__(self):
        return f"{self.datum} {self.kezdet}-{self.veg} | {self.tevekenyseg[:40]}"

from django import forms
from datetime import datetime, timedelta
from .models import NaploSor, Param


class NaploSorForm(forms.ModelForm):
    ertek = forms.IntegerField(required=False, initial=6)
    class Meta:
        model = NaploSor
        fields = [
            "datum", "kezdet", "veg",
            "tevekenyseg", "ertek",
            "kategoria", "kapcsolodo", "szerep", "erzelem",
            "kapcsolodo_cel", "megjegyzes",
        ]
        widgets = {
            "datum": forms.DateInput(attrs={"type": "date"}),
            "kezdet": forms.TimeInput(format="%H:%M", attrs={"type": "time", "step": 60}),
            "veg": forms.TimeInput(format="%H:%M", attrs={"type": "time", "step": 60}),
            "tevekenyseg": forms.Textarea(attrs={"rows": 2}),
            "megjegyzes": forms.Textarea(attrs={"rows": 2}),
            # "ido": forms.TextInput(attrs={"readonly": "readonly"}),  # a JS tölti, és szerver oldalon is számoljuk
        }
    """ def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ertek"].initial = 6
        self.fields["ertek"].widget.attrs["class"] = "short-number" """

    def clean(self):
        cleaned = super().clean()
        datum = cleaned.get("datum")
        kezdet = cleaned.get("kezdet")
        veg = cleaned.get("veg")

        # Idő automatikus számítás mentéskor is (JS mellett ez a biztonsági háló)
        if datum and kezdet and veg:
            dt_start = datetime.combine(datum, kezdet)
            dt_end = datetime.combine(datum, veg)
            if dt_end < dt_start:
                dt_end += timedelta(days=1)  # éjfél átlépés támogatás
            cleaned["ido"] = dt_end - dt_start

        return cleaned
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Érték mező: alapérték + megjelenés
        self.fields["ertek"].initial = 6
        self.fields["ertek"].widget.attrs["class"] = "short-number"

        def set_select(field_name: str, tipus: str):
            qs = Param.objects.filter(tipus=tipus).order_by("nev").values_list("nev", "nev")
            self.fields[field_name].widget = forms.Select(
                choices=[("", "— válassz —")] + list(qs)
            )

        set_select("kategoria", "kategoria")
        set_select("kapcsolodo", "kapcsolodo")
        set_select("szerep", "szerep")
        set_select("erzelem", "erzelem")
        set_select("kapcsolodo_cel", "cel")


    


from tinymce.widgets import TinyMCE
from django import forms
from datetime import datetime, timedelta
from .models import NaploSor, Param

# 6P – Dittrich: Változás 6 programja (rövid jelölések a UI-hoz)
SIX_PROGRAM_CHOICES = [
    ("P1_TUDAT", "Tudat"),
    ("P2_ERTEK", "Érték"),
    ("P3_EGESZSEG", "Egészség"),
    ("P4_KOZOSSEG", "Közösség"),
    ("P5_GAZDASAG", "Gazdaság"),
    ("P6_SPIRIT", "Spirit"),
]


class NaploSorForm(forms.ModelForm):
    ertek = forms.IntegerField(required=False, initial=6)
    six_program_focus = forms.MultipleChoiceField(
        required=False,
        choices=SIX_PROGRAM_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )
    class Meta:
        model = NaploSor
        fields = [
            "datum", "kezdet", "veg",
            "tevekenyseg", "ertek",
            "kategoria", "six_program_focus", "kapcsolodo", "szerep", "erzelem",
            "kapcsolodo_cel", "megjegyzes",
        ]
        widgets = {
            "datum": forms.DateInput(attrs={"type": "date"}),
            "kezdet": forms.TimeInput(format="%H:%M", attrs={"type": "time", "step": 60}),
            "veg": forms.TimeInput(format="%H:%M", attrs={"type": "time", "step": 60}),
            "tevekenyseg": forms.Textarea(attrs={"rows": 6}),
            "megjegyzes": forms.Textarea(attrs={"rows": 6}),
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

        # 6P fókusz: legfeljebb 2 jelölés (a bevitel gyors maradjon)
        sixp = cleaned.get("six_program_focus") or []
        if len(sixp) > 2:
            self.add_error("six_program_focus", "Legfeljebb 2 jelölést válassz.")
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


    

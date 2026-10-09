from django import forms
from shule_core.models import Student, SchoolClass
from .models import OffenseType, DisciplineIncident


TW = 'border border-gray-300 rounded px-3 py-2 text-sm w-full'


class OffenseTypeForm(forms.ModelForm):
    class Meta:
        model = OffenseType
        fields = ['name', 'points_deducted', 'description']
        labels = {
            'name': 'Jina la Kosa',
            'points_deducted': 'Alama Zitakazopunguzwa',
            'description': 'Maelezo (hiari)',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': TW, 'placeholder': 'Mfano: Kutoroka Shule'}),
            'points_deducted': forms.NumberInput(attrs={'class': TW, 'min': 1}),
            'description': forms.TextInput(attrs={'class': TW}),
        }


class DisciplineIncidentForm(forms.ModelForm):
    class Meta:
        model = DisciplineIncident
        fields = ['student', 'offense_type', 'academic_year', 'date_occurred', 'notes', 'evidence_file']
        labels = {
            'student': 'Mwanafunzi',
            'offense_type': 'Aina ya Kosa',
            'academic_year': 'Mwaka wa Masomo',
            'date_occurred': 'Tarehe ya Kosa',
            'notes': 'Maelezo',
            'evidence_file': 'Kiambatisho (hiari)',
        }
        widgets = {
            'student': forms.Select(attrs={'class': TW}),
            'offense_type': forms.Select(attrs={'class': TW}),
            'academic_year': forms.NumberInput(attrs={'class': TW}),
            'date_occurred': forms.DateInput(attrs={'class': TW, 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': TW, 'rows': 3}),
        }

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        if school:
            self.fields['student'].queryset = Student.objects.filter(school=school)
            self.fields['offense_type'].queryset = OffenseType.objects.filter(school=school)


class IncidentSpreadsheetFilterForm(forms.Form):
    """
    Kuchagua Darasa + Tarehe + Mwaka kabla ya kuonyesha jedwali la
    wanafunzi wote (spreadsheet ya makosa - safu ni Aina za Makosa,
    kiini ni tiki/checkbox).
    """
    school_class = forms.ModelChoiceField(
        queryset=SchoolClass.objects.none(),
        widget=forms.Select(attrs={'class': TW}),
        label='Darasa',
    )
    date_occurred = forms.DateField(
        widget=forms.DateInput(attrs={'class': TW, 'type': 'date'}),
        label='Tarehe',
    )
    academic_year = forms.IntegerField(
        min_value=2020, max_value=2100, initial=2026,
        widget=forms.NumberInput(attrs={'class': TW}),
        label='Mwaka wa Masomo',
    )

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        if school:
            self.fields['school_class'].queryset = SchoolClass.objects.filter(school=school)

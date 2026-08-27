from django import forms
from shule_core.models import Student
from .models import OffenseType, DisciplineIncident


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
            'name': forms.TextInput(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full', 'placeholder': 'Mfano: Kutoroka Shule'}),
            'points_deducted': forms.NumberInput(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full', 'min': 1}),
            'description': forms.TextInput(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full'}),
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
            'student': forms.Select(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full'}),
            'offense_type': forms.Select(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full'}),
            'academic_year': forms.NumberInput(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full'}),
            'date_occurred': forms.DateInput(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full', 'rows': 3}),
        }

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        if school:
            self.fields['student'].queryset = Student.objects.filter(school=school)
            self.fields['offense_type'].queryset = OffenseType.objects.filter(school=school)

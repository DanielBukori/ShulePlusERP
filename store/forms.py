from django import forms
from shule_core.models import SchoolClass, Student
from .models import ContributionRequirement, StudentContribution, StoreStock


class ContributionRequirementForm(forms.ModelForm):
    """
    Academic/Second Master anaweka kile kinachotakiwa kuletwa
    (mfano: Ream 1, Omo 2) kwa muhula fulani.
    """
    class Meta:
        model = ContributionRequirement
        fields = ['school_class', 'term', 'academic_year', 'item_name', 'quantity_required']
        labels = {
            'school_class': 'Darasa (acha wazi kama ni shule nzima)',
            'term': 'Muhula',
            'academic_year': 'Mwaka wa Masomo',
            'item_name': 'Jina la Kifaa',
            'quantity_required': 'Kiasi Kinachotakiwa',
        }
        widgets = {
            'school_class': forms.Select(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full'}),
            'term': forms.Select(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full'}),
            'academic_year': forms.NumberInput(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full'}),
            'item_name': forms.TextInput(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full', 'placeholder': 'Mfano: Ream, Omo, Mfagio'}),
            'quantity_required': forms.NumberInput(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full', 'min': 1}),
        }

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['school_class'].required = False
        if school:
            self.fields['school_class'].queryset = SchoolClass.objects.filter(school=school)


class StudentContributionForm(forms.ModelForm):
    """
    Store Keeper anarekodi mwanafunzi mmoja akileta kifaa fulani.
    """
    class Meta:
        model = StudentContribution
        fields = ['student', 'requirement', 'quantity_brought', 'notes']
        labels = {
            'student': 'Mwanafunzi',
            'requirement': 'Kifaa Kinachotakiwa',
            'quantity_brought': 'Kiasi Alicholeta',
            'notes': 'Maelezo (hiari)',
        }
        widgets = {
            'student': forms.Select(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full'}),
            'requirement': forms.Select(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full'}),
            'quantity_brought': forms.NumberInput(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full', 'min': 0}),
            'notes': forms.TextInput(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full'}),
        }

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        if school:
            self.fields['student'].queryset = Student.objects.filter(school=school)
            self.fields['requirement'].queryset = ContributionRequirement.objects.filter(school=school)


class StockAdjustmentForm(forms.Form):
    """
    Fomu rahisi ya Store Keeper kuongeza/kupunguza stock moja kwa moja
    (mfano: shule imetumia mifagio 3, au ununuzi mpya umefika).
    """
    REASON_CHOICES = [
        ('SCHOOL_USE', 'Matumizi ya Shule (punguza)'),
        ('PURCHASE', 'Ununuzi (ongeza)'),
        ('ADJUSTMENT', 'Marekebisho'),
    ]

    stock = forms.ModelChoiceField(
        queryset=StoreStock.objects.none(),
        widget=forms.Select(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full'}),
        label='Kifaa',
    )
    quantity = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full'}),
        label='Kiasi (tumia namba hasi kupunguza, mfano -3)',
    )
    reason = forms.ChoiceField(
        choices=REASON_CHOICES,
        widget=forms.Select(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full'}),
        label='Sababu',
    )
    notes = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'border border-gray-300 rounded px-3 py-2 text-sm w-full'}),
        label='Maelezo (hiari)',
    )

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        if school:
            self.fields['stock'].queryset = StoreStock.objects.filter(school=school)

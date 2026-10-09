from django import forms
from django.core.exceptions import ValidationError
from shule_core.models import SchoolClass, Student, Payment, CustomUser
from .models import FeeStructure, OtherCharge


TW = 'border border-gray-300 rounded px-3 py-2 text-sm w-full'


class FeeStructureForm(forms.ModelForm):
    class Meta:
        model = FeeStructure
        fields = ['school_class', 'academic_year', 'amount']
        labels = {'school_class': 'Darasa', 'academic_year': 'Mwaka wa Masomo', 'amount': 'Ada ya Mwaka (TZS)'}
        widgets = {
            'school_class': forms.Select(attrs={'class': TW}),
            'academic_year': forms.NumberInput(attrs={'class': TW}),
            'amount': forms.NumberInput(attrs={'class': TW}),
        }

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        if school:
            self.fields['school_class'].queryset = SchoolClass.objects.filter(school=school)


class OtherChargeForm(forms.ModelForm):
    """
    Kama muundaji ni Accountant, 'authorized_by' ni LAZIMA (Headmaster/
    Second Master aliyeidhinisha). Kama ni Headmaster/Second Master
    mwenyewe anayeunda, field hii haihitajiki (yeye mwenyewe ndiye mamlaka).
    """
    class Meta:
        model = OtherCharge
        fields = ['name', 'amount', 'school_class', 'academic_year', 'authorized_by']
        labels = {
            'name': 'Jina la Mchango (mfano: Mahafali)',
            'amount': 'Kiasi (TZS)',
            'school_class': 'Darasa (acha wazi kama ni shule nzima)',
            'academic_year': 'Mwaka wa Masomo',
            'authorized_by': 'Imeidhinishwa na (Mkuu/Second Master)',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': TW}),
            'amount': forms.NumberInput(attrs={'class': TW}),
            'school_class': forms.Select(attrs={'class': TW}),
            'academic_year': forms.NumberInput(attrs={'class': TW}),
            'authorized_by': forms.Select(attrs={'class': TW}),
        }

    def __init__(self, *args, school=None, creator_role=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.creator_role = creator_role
        self.fields['school_class'].required = False
        self.fields['authorized_by'].required = False
        if school:
            self.fields['school_class'].queryset = SchoolClass.objects.filter(school=school)
            self.fields['authorized_by'].queryset = CustomUser.objects.filter(
                school=school, role__in=['HEADMASTER', 'SECOND_MASTER']
            )

    def clean(self):
        cleaned = super().clean()
        if self.creator_role == 'ACCOUNTANT' and not cleaned.get('authorized_by'):
            self.add_error('authorized_by', 'Lazima uchague Mkuu/Second Master aliyeidhinisha mchango huu.')
        return cleaned


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['student', 'amount', 'date_paid', 'bank_name', 'receipt_number', 'receipt_file']
        labels = {
            'student': 'Mwanafunzi',
            'amount': 'Kiasi Kilicholipwa (TZS)',
            'date_paid': 'Tarehe ya Malipo',
            'bank_name': 'Benki',
            'receipt_number': 'Namba ya Risiti',
            'receipt_file': 'Risiti (picha/PDF)',
        }
        widgets = {
            'student': forms.Select(attrs={'class': TW}),
            'amount': forms.NumberInput(attrs={'class': TW}),
            'date_paid': forms.DateInput(attrs={'class': TW, 'type': 'date'}),
            'bank_name': forms.TextInput(attrs={'class': TW}),
            'receipt_number': forms.TextInput(attrs={'class': TW}),
        }

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        if school:
            self.fields['student'].queryset = Student.objects.filter(school=school)

    def clean_receipt_number(self):
        number = self.cleaned_data['receipt_number']
        if Payment.objects.filter(receipt_number=number).exists():
            raise ValidationError('Namba hii ya risiti tayari imetumika.')
        return number


class PaymentSpreadsheetFilterForm(forms.Form):
    """
    Kuchagua Darasa + Mwaka kabla ya kuonyesha jedwali la wanafunzi
    wote (spreadsheet ya malipo). Hakuna 'Muhula' kwa makusudi - ada
    (FeeStructure/StudentFeeAssessment) ni ya MWAKA MZIMA, siyo muhula.
    """
    school_class = forms.ModelChoiceField(
        queryset=SchoolClass.objects.none(),
        widget=forms.Select(attrs={'class': TW}),
        label='Darasa',
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
